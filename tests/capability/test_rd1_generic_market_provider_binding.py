"""RD1 P1-I2: Core binds and invokes the Market public boundary mechanically."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pytest

from julia_core.capability.models import CapabilityRequest
from julia_core.capability.providers.market_public import MarketPublicProviderAdapter
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


@dataclass(frozen=True)
class EventResolveRequest:
    feed_date: str | None = None
    stock_id: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class EventReadRequest:
    event_id: int


@dataclass(frozen=True)
class ProductReadRequest:
    subject_key: str


class OperationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class DataState(str, Enum):
    READY = "READY"
    EMPTY = "EMPTY"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class Failure:
    kind: str
    code: str
    message: str


@dataclass(frozen=True)
class Provenance:
    provenance_status: str = "PROVENANCE_INCOMPLETE"


@dataclass(frozen=True)
class MarketResultEnvelopeFixture:
    contract_version: str
    capability_id: str
    request_id: str | None
    correlation_id: str
    operation_status: OperationStatus
    data_state: DataState
    payload: object
    provenance: Provenance
    failures: tuple[Failure, ...]
    boundary_identity_ref: str
    runtime_observation: object | None
    produced_at: str


REQUEST_BUILDERS = {
    "market.event.resolve": EventResolveRequest,
    "market.event.read": EventReadRequest,
    "market.product.read": ProductReadRequest,
}


def envelope(
    capability: str,
    *,
    operation_status: OperationStatus = OperationStatus.SUCCESS,
    data_state: DataState = DataState.READY,
    payload=None,
    failures: tuple[Failure, ...] = (),
    request_id: str | None = None,
    correlation_id: str = "corr-market",
):
    return MarketResultEnvelopeFixture(
        contract_version="fixture-contract",
        capability_id=capability,
        request_id=request_id,
        correlation_id=correlation_id,
        operation_status=operation_status,
        data_state=data_state,
        payload=payload,
        provenance=Provenance(),
        failures=failures,
        boundary_identity_ref="market.public",
        runtime_observation=None,
        produced_at="2026-09-17T00:00:00+00:00",
    )


class MarketPublicFixture:
    """Imitates only the merged Market public provider call signature."""

    def __init__(self):
        self.calls = []

    async def execute(
        self,
        capability,
        request,
        *,
        request_id=None,
        correlation_id=None,
    ):
        self.calls.append((capability, request, request_id, correlation_id))
        if not isinstance(request, REQUEST_BUILDERS[capability]):
            return envelope(
                capability,
                operation_status=OperationStatus.FAILURE,
                data_state=DataState.NOT_APPLICABLE,
                failures=(Failure("MarketContractMismatch", "invalid_request", "invalid"),),
                request_id=request_id,
                correlation_id=correlation_id or "corr-market",
            )
        return envelope(
            capability,
            payload={"source": "market-public-contract"},
            request_id=request_id,
            correlation_id=correlation_id or "corr-market",
        )


def bound_bridge(public_provider):
    adapter = MarketPublicProviderAdapter(public_provider, REQUEST_BUILDERS)
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("market", adapter)
    bridge.initialize()
    return bridge, adapter


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("capability", "arguments", "request_type"),
    [
        ("market.event.resolve", {"stock_id": "600519", "limit": 10}, EventResolveRequest),
        ("market.event.read", {"event_id": 7}, EventReadRequest),
        ("market.product.read", {"subject_key": "theme:1"}, ProductReadRequest),
    ],
)
async def test_structured_market_request_uses_public_provider_shape(
    capability,
    arguments,
    request_type,
):
    provider = MarketPublicFixture()
    bridge, _ = bound_bridge(provider)
    request = CapabilityRequest(
        capability,
        arguments,
        capability_request_id="req-core",
        correlation_id="corr-core",
    )

    result = await bridge.manager.execute_typed(request)

    assert result.tool_result.status.value == "success"
    assert len(provider.calls) == 1
    called_capability, public_request, request_id, correlation_id = provider.calls[0]
    assert called_capability == capability
    assert isinstance(public_request, request_type)
    assert request_id == "req-core"
    assert correlation_id == "corr-core"
    assert result.tool_result.structured_output["capability_id"] == capability
    assert result.tool_result.structured_output["operation_status"] == "SUCCESS"
    assert result.tool_result.structured_output["data_state"] == "READY"


@pytest.mark.asyncio
async def test_market_domain_failure_remains_inside_successful_core_execution():
    class DomainFailure(MarketPublicFixture):
        async def execute(self, capability, request, *, request_id=None, correlation_id=None):
            self.calls.append((capability, request, request_id, correlation_id))
            return envelope(
                capability,
                operation_status=OperationStatus.FAILURE,
                data_state=DataState.NOT_APPLICABLE,
                failures=(Failure("MarketObjectNotFound", "event_not_found", "not found"),),
                request_id=request_id,
                correlation_id=correlation_id or "corr-market",
            )

    provider = DomainFailure()
    bridge, _ = bound_bridge(provider)
    result = await bridge.manager.execute_typed(
        CapabilityRequest("market.event.read", {"event_id": 999}, correlation_id="corr-core")
    )

    assert result.tool_result.status.value == "success"
    output = result.tool_result.structured_output
    assert output["operation_status"] == "FAILURE"
    assert output["data_state"] == "NOT_APPLICABLE"
    assert output["failures"][0]["kind"] == "MarketObjectNotFound"
    assert result.tool_result.error is None


@pytest.mark.asyncio
async def test_invalid_public_request_shape_is_adjudicated_by_market_not_core():
    provider = MarketPublicFixture()
    bridge, _ = bound_bridge(provider)

    # Missing required event_id cannot construct EventReadRequest. The adapter
    # passes the raw mapping across the public boundary so Market owns the
    # canonical contract-mismatch outcome.
    result = await bridge.manager.execute_typed(
        CapabilityRequest("market.event.read", {}, correlation_id="corr-core")
    )

    assert result.tool_result.status.value == "success"
    assert provider.calls and provider.calls[0][1] == {}
    output = result.tool_result.structured_output
    assert output["operation_status"] == "FAILURE"
    assert output["data_state"] == "NOT_APPLICABLE"
    assert output["failures"][0]["kind"] == "MarketContractMismatch"


def test_raw_user_text_cannot_select_market_inside_core():
    bridge = RuntimeCapabilityBridge()
    assert bridge.requires_tool("今天市场怎么样？") is False
    assert bridge.requires_tool("这个风险大吗？") is False
    assert "MarketBriefIntentResolver" not in Path("julia_core/runtime/workflow_router.py").read_text()


@pytest.mark.asyncio
async def test_c08_denial_does_not_invoke_market_public_provider():
    provider = MarketPublicFixture()
    bridge, _ = bound_bridge(provider)
    bridge.policy.remove_scope("market.observe")

    result = await bridge.manager.execute_typed(
        CapabilityRequest("market.event.read", {"event_id": 7})
    )

    assert result.tool_result is None
    assert result.authorization_decision.allowed is False
    assert provider.calls == []


@pytest.mark.asyncio
async def test_pre_envelope_provider_exception_is_core_execution_error():
    class Broken(MarketPublicFixture):
        async def execute(self, capability, request, *, request_id=None, correlation_id=None):
            self.calls.append((capability, request, request_id, correlation_id))
            raise RuntimeError("public provider protocol failure")

    bridge, _ = bound_bridge(Broken())
    result = await bridge.manager.execute_typed(
        CapabilityRequest("market.product.read", {"subject_key": "theme:1"})
    )

    assert result.tool_result.status.value == "error"
    assert result.tool_result.structured_output == {}
    assert result.tool_result.error["code"] == "provider_exception"


def test_canonical_market_binding_has_no_private_market_loading_or_transport_fallback():
    source = Path("julia_core/capability/providers/market_public.py").read_text()
    bridge_source = Path("julia_core/runtime/capability_bridge.py").read_text()

    for forbidden in (
        "mcp_server",
        "MCP_TOOLS",
        "sys.path",
        "/Users/admin/Desktop/ai_theme_app",
        "Phase1ReadRepository",
        "theme_service.repositories",
    ):
        assert forbidden not in source
        assert forbidden not in bridge_source

    assert "from market_public import" in source
    assert "MarketPublicFactory.create" in source


@pytest.mark.asyncio
async def test_generic_non_market_file_capability_is_not_regressed():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    result = await bridge.manager.execute_typed(
        CapabilityRequest("file.read", {"path": str(Path("README.md").resolve())})
    )
    assert result.tool_result.status.value == "success"

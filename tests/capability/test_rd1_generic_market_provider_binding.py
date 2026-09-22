"""RD1 P1-I2: Core binds and invokes the Market public boundary mechanically."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sys
import types

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


@dataclass(frozen=True)
class ProductLinkageReadRequest:
    subject_key: str
    mapping_scope: str = "pool"
    include_leaders: bool = False
    limit: int = 100


@dataclass(frozen=True)
class MarketStateReadRequest:
    trade_date: str


@dataclass(frozen=True)
class StockQuoteReadRequest:
    stock_id: str
    trade_date: str


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
    "market.product.linkage.read": ProductLinkageReadRequest,
    "market.state.read": MarketStateReadRequest,
    "market.stock.quote.read": StockQuoteReadRequest,
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


def test_default_loader_imports_only_new_market_public_request_exports(monkeypatch):
    market_public = types.ModuleType("market_public")
    market_public.EventResolveRequest = EventResolveRequest
    market_public.EventReadRequest = EventReadRequest
    market_public.ProductReadRequest = ProductReadRequest
    market_public.ProductLinkageReadRequest = ProductLinkageReadRequest
    market_public.MarketStateReadRequest = MarketStateReadRequest
    market_public.StockQuoteReadRequest = StockQuoteReadRequest
    monkeypatch.setitem(sys.modules, "market_public", market_public)

    class CallableProvider:
        def execute(self):
            pass

    adapter = MarketPublicProviderAdapter(CallableProvider())

    assert adapter._request_builders == REQUEST_BUILDERS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("capability", "arguments", "request_type"),
    [
        ("market.event.resolve", {"stock_id": "600519", "limit": 10}, EventResolveRequest),
        ("market.event.read", {"event_id": 7}, EventReadRequest),
        ("market.product.read", {"subject_key": "theme:1"}, ProductReadRequest),
        (
            "market.product.linkage.read",
            {
                "subject_key": "theme:1",
                "mapping_scope": "all",
                "include_leaders": True,
                "limit": 20,
            },
            ProductLinkageReadRequest,
        ),
        ("market.state.read", {"trade_date": "2026-09-18"}, MarketStateReadRequest),
        (
            "market.stock.quote.read",
            {"stock_id": "600519.SH", "trade_date": "2026-07-31"},
            StockQuoteReadRequest,
        ),
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


def test_new_market_capabilities_are_registered_and_model_visible(monkeypatch):
    market_public = types.ModuleType("market_public")
    market_public.EventResolveRequest = EventResolveRequest
    market_public.EventReadRequest = EventReadRequest
    market_public.ProductReadRequest = ProductReadRequest
    market_public.ProductLinkageReadRequest = ProductLinkageReadRequest
    market_public.MarketStateReadRequest = MarketStateReadRequest
    market_public.StockQuoteReadRequest = StockQuoteReadRequest
    monkeypatch.setitem(sys.modules, "market_public", market_public)

    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    definitions = {
        definition.name: definition
        for definition in bridge.registry.by_provider("market")
    }
    assert set(definitions) == {
        "market.event.resolve",
        "market.event.read",
        "market.product.read",
        "market.product.linkage.read",
        "market.state.read",
        "market.stock.quote.read",
    }
    for capability in (
        "market.product.linkage.read",
        "market.state.read",
        "market.stock.quote.read",
    ):
        definition = definitions[capability]
        assert definition.provider == "market"
        assert definition.permission_scope == "market.observe"
        assert definition.input_schema is not None

    manifest = bridge.tool_manifest()
    assert "market.product.linkage.read" in manifest
    assert "market.state.read" in manifest
    assert "market.stock.quote.read" in manifest
    assert '"stock_id": exact source-namespaced stock identifier' in manifest
    assert '"trade_date": exact YYYY-MM-DD trade date' in manifest


def test_old_market_contract_does_not_advertise_unexecutable_stock_quote(monkeypatch):
    market_public = types.ModuleType("market_public")
    market_public.EventResolveRequest = EventResolveRequest
    market_public.EventReadRequest = EventReadRequest
    market_public.ProductReadRequest = ProductReadRequest
    market_public.ProductLinkageReadRequest = ProductLinkageReadRequest
    market_public.MarketStateReadRequest = MarketStateReadRequest
    monkeypatch.setitem(sys.modules, "market_public", market_public)

    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    definitions = {
        definition.name: definition
        for definition in bridge.registry.by_provider("market")
    }
    assert set(definitions) == {
        "market.event.resolve",
        "market.event.read",
        "market.product.read",
        "market.product.linkage.read",
        "market.state.read",
    }
    manifest = bridge.tool_manifest()
    assert "market.stock.quote.read" not in manifest
    assert "Read one exact stock/date daily quote" not in manifest


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
async def test_new_market_envelope_states_remain_structurally_preserved():
    class StatefulMarket(MarketPublicFixture):
        def __init__(self):
            super().__init__()
            self.next_envelope = None

        async def execute(self, capability, request, *, request_id=None, correlation_id=None):
            self.calls.append((capability, request, request_id, correlation_id))
            return self.next_envelope or envelope(
                capability,
                payload=[{"subject_key": "theme:1", "stock_id": "600000"}],
                request_id=request_id,
                correlation_id=correlation_id or "corr-market",
            )

    provider = StatefulMarket()
    bridge, _ = bound_bridge(provider)
    request = CapabilityRequest(
        "market.state.read",
        {"trade_date": "2026-09-18"},
        capability_request_id="req-state",
        correlation_id="corr-state",
    )

    provider.next_envelope = envelope(
        "market.state.read",
        payload={
            "trade_date": "2026-09-18",
            "breadth": {"up_count": 1, "down_count": 0},
            "source": "post_market_recap_snapshot.payload.market_overview_review",
        },
        request_id="req-state",
        correlation_id="corr-state",
    )
    ready = await bridge.manager.execute_typed(request)
    assert ready.tool_result.status.value == "success"
    assert ready.tool_result.structured_output["operation_status"] == "SUCCESS"
    assert ready.tool_result.structured_output["data_state"] == "READY"
    assert ready.tool_result.structured_output["request_id"] == "req-state"
    assert ready.tool_result.structured_output["correlation_id"] == "corr-state"

    provider.next_envelope = envelope(
        "market.state.read",
        data_state=DataState.EMPTY,
        payload=None,
        request_id="req-state",
        correlation_id="corr-state",
    )
    empty = await bridge.manager.execute_typed(request)
    assert empty.tool_result.status.value == "success"
    assert empty.tool_result.structured_output["operation_status"] == "SUCCESS"
    assert empty.tool_result.structured_output["data_state"] == "EMPTY"

    provider.next_envelope = envelope(
        "market.state.read",
        operation_status=OperationStatus.FAILURE,
        data_state=DataState.UNAVAILABLE,
        failures=(Failure("MarketInternalFailure", "market_overview_review_invalid", "invalid"),),
        request_id="req-state",
        correlation_id="corr-state",
    )
    failure = await bridge.manager.execute_typed(request)
    assert failure.tool_result.status.value == "success"
    assert failure.tool_result.structured_output["operation_status"] == "FAILURE"
    assert failure.tool_result.structured_output["data_state"] == "UNAVAILABLE"
    assert failure.tool_result.structured_output["failures"][0]["code"] == (
        "market_overview_review_invalid"
    )
    assert failure.tool_result.error is None


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("capability", "arguments"),
    [
        ("market.product.linkage.read", {"mapping_scope": "all"}),
        ("market.state.read", {}),
    ],
)
async def test_invalid_new_market_request_shape_is_adjudicated_by_market(
    capability,
    arguments,
):
    provider = MarketPublicFixture()
    bridge, _ = bound_bridge(provider)

    result = await bridge.manager.execute_typed(
        CapabilityRequest(capability, arguments, correlation_id="corr-core")
    )

    assert result.tool_result.status.value == "success"
    assert provider.calls[0][1] == arguments
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
@pytest.mark.parametrize(
    ("capability", "arguments"),
    [
        ("market.event.read", {"event_id": 7}),
        (
            "market.product.linkage.read",
            {"subject_key": "theme:1", "mapping_scope": "all"},
        ),
        ("market.state.read", {"trade_date": "2026-09-18"}),
    ],
)
async def test_c08_denial_does_not_invoke_market_public_provider(capability, arguments):
    provider = MarketPublicFixture()
    bridge, _ = bound_bridge(provider)
    bridge.policy.remove_scope("market.observe")

    result = await bridge.manager.execute_typed(
        CapabilityRequest(capability, arguments)
    )

    assert result.tool_result is None
    assert result.authorization_decision.allowed is False
    assert provider.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("capability", "arguments"),
    [
        ("market.product.read", {"subject_key": "theme:1"}),
        (
            "market.product.linkage.read",
            {"subject_key": "theme:1", "mapping_scope": "all"},
        ),
        ("market.state.read", {"trade_date": "2026-09-18"}),
    ],
)
async def test_missing_market_binding_is_typed_unavailable_without_fallback(
    capability, arguments
):
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    result = await bridge.manager.execute_typed(
        CapabilityRequest(capability, arguments)
    )

    assert result.tool_result.status.value == "unavailable"
    assert result.tool_result.error["code"] == "provider_not_found"
    assert result.tool_result.structured_output == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("capability", "arguments"),
    [
        ("market.product.read", {"subject_key": "theme:1"}),
        (
            "market.product.linkage.read",
            {"subject_key": "theme:1", "mapping_scope": "all"},
        ),
        ("market.state.read", {"trade_date": "2026-09-18"}),
    ],
)
async def test_pre_envelope_provider_exception_is_core_execution_error(
    capability, arguments
):
    class Broken(MarketPublicFixture):
        async def execute(self, capability, request, *, request_id=None, correlation_id=None):
            self.calls.append((capability, request, request_id, correlation_id))
            raise RuntimeError("public provider protocol failure")

    bridge, _ = bound_bridge(Broken())
    result = await bridge.manager.execute_typed(
        CapabilityRequest(capability, arguments)
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
        "MarketPublicFactory",
        "database_url",
    ):
        assert forbidden not in source
        assert forbidden not in bridge_source

    assert "import_module(\"market_public\")" in source


@pytest.mark.asyncio
async def test_generic_non_market_file_capability_is_not_regressed():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    result = await bridge.manager.execute_typed(
        CapabilityRequest("file.read", {"path": str(Path("README.md").resolve())})
    )
    assert result.tool_result.status.value == "success"

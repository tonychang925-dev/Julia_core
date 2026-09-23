"""Static coverage for the exact-date Market analytical evidence join."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import sys
import types

import pytest

from julia_core.capability.models import CapabilityRequest, CapabilityStatus
from julia_core.capability.providers.market_public import MarketPublicProviderAdapter
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


@dataclass(frozen=True)
class EventResolveRequest:
    feed_date: str | None = None
    stock_id: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class EventReadRequest:
    event_id: int | None = None
    item_id: str | None = None


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


@dataclass(frozen=True)
class MarketAnalysisReadRequest:
    trade_date: str


@dataclass(frozen=True)
class Failure:
    kind: str
    code: str
    message: str


@dataclass(frozen=True)
class Provenance:
    provenance_status: str = "PROVENANCE_INCOMPLETE"


class OperationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class DataState(str, Enum):
    READY = "READY"
    EMPTY = "EMPTY"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class MarketResultEnvelope:
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


def result_envelope(
    capability,
    *,
    operation_status=OperationStatus.SUCCESS,
    data_state=DataState.READY,
    payload=None,
    failures=(),
    request_id=None,
    correlation_id="corr-market",
):
    return MarketResultEnvelope(
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
        produced_at="2026-09-23T00:00:00+00:00",
    )


class MarketPublicFixture:
    def __init__(self):
        self.calls = []

    async def health(self):
        return True, "ready"

    async def execute(
        self, capability, request, *, request_id=None, correlation_id=None
    ):
        self.calls.append((capability, request, request_id, correlation_id))
        if capability == "market.analysis.read" and request.trade_date == "2026-7-9":
            return result_envelope(
                capability,
                operation_status=OperationStatus.FAILURE,
                data_state=DataState.NOT_APPLICABLE,
                failures=(
                    Failure(
                        "MarketContractMismatch",
                        "invalid_trade_date",
                        "trade_date must be YYYY-MM-DD",
                    ),
                ),
                request_id=request_id,
                correlation_id=correlation_id or "corr-market",
            )
        return result_envelope(
            capability,
            payload={"trade_date": getattr(request, "trade_date", None)},
            request_id=request_id,
            correlation_id=correlation_id or "corr-market",
        )

    async def close(self):
        return None


def install_market_public(monkeypatch, *, include_analysis=True):
    module = types.ModuleType("market_public")
    module.EventResolveRequest = EventResolveRequest
    module.EventReadRequest = EventReadRequest
    module.ProductReadRequest = ProductReadRequest
    module.ProductLinkageReadRequest = ProductLinkageReadRequest
    module.MarketStateReadRequest = MarketStateReadRequest
    module.StockQuoteReadRequest = StockQuoteReadRequest
    if include_analysis:
        module.MarketAnalysisReadRequest = MarketAnalysisReadRequest
    monkeypatch.setitem(sys.modules, "market_public", module)
    return module


def bound_bridge(provider):
    adapter = MarketPublicProviderAdapter(provider)
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("market", adapter)
    return bridge, adapter


def test_analysis_request_builder_follows_optional_public_export(monkeypatch):
    install_market_public(monkeypatch, include_analysis=True)
    adapter = MarketPublicProviderAdapter(MarketPublicFixture())
    assert (
        adapter._request_builders["market.analysis.read"] is MarketAnalysisReadRequest
    )

    install_market_public(monkeypatch, include_analysis=False)
    adapter = MarketPublicProviderAdapter(MarketPublicFixture())
    assert "market.analysis.read" not in adapter._request_builders
    assert not adapter.supports_capability("market.analysis.read")


def test_analysis_catalog_is_model_visible(monkeypatch):
    install_market_public(monkeypatch)
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    definition = bridge.registry.get("market.analysis.read")
    assert definition is not None
    assert definition.layer.value == "intelligence"
    assert definition.provider == "market"
    assert definition.permission_scope == "market.observe"
    assert definition.status == CapabilityStatus.AVAILABLE
    assert definition.input_schema == {"trade_date": "exact YYYY-MM-DD trade date"}
    assert "market.analysis.read" in bridge.tool_manifest()
    assert "exact YYYY-MM-DD trade date" in bridge.tool_manifest()


def test_old_market_contract_does_not_advertise_analysis(monkeypatch):
    install_market_public(monkeypatch, include_analysis=False)
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    assert bridge.registry.get("market.analysis.read") is None
    assert "market.analysis.read" not in bridge.tool_manifest()


def test_late_market_binding_reconciles_analysis(monkeypatch):
    install_market_public(monkeypatch, include_analysis=False)
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    assert bridge.registry.get("market.analysis.read") is None

    adapter = MarketPublicProviderAdapter(
        MarketPublicFixture(),
        {"market.analysis.read": MarketAnalysisReadRequest},
    )
    bridge.register_provider("market", adapter)
    assert (
        bridge.registry.get("market.analysis.read").status is CapabilityStatus.AVAILABLE
    )


@pytest.mark.asyncio
async def test_analysis_execution_preserves_market_envelope(monkeypatch):
    install_market_public(monkeypatch)
    provider = MarketPublicFixture()
    bridge, _ = bound_bridge(provider)
    result = await bridge.manager.execute_typed(
        CapabilityRequest(
            "market.analysis.read",
            {"trade_date": "2026-07-09"},
            capability_request_id="analysis-request",
            correlation_id="analysis-correlation",
        )
    )
    assert len(provider.calls) == 1
    capability, request, request_id, correlation_id = provider.calls[0]
    assert capability == "market.analysis.read"
    assert isinstance(request, MarketAnalysisReadRequest)
    assert request.trade_date == "2026-07-09"
    assert request_id == "analysis-request"
    assert correlation_id == "analysis-correlation"
    assert result.tool_result.status.value == "success"
    output = result.tool_result.structured_output
    assert output["capability_id"] == "market.analysis.read"
    assert output["contract_version"] == "fixture-contract"
    assert output["operation_status"] == "SUCCESS"
    assert output["data_state"] == "READY"
    assert output["payload"] == {"trade_date": "2026-07-09"}
    assert output["provenance"] == {"provenance_status": "PROVENANCE_INCOMPLETE"}
    assert list(output["failures"]) == []
    assert output["boundary_identity_ref"] == "market.public"
    assert result.evidence


@pytest.mark.asyncio
async def test_malformed_analysis_date_remains_market_domain_failure(monkeypatch):
    install_market_public(monkeypatch)
    provider = MarketPublicFixture()
    bridge, _ = bound_bridge(provider)
    result = await bridge.manager.execute_typed(
        CapabilityRequest(
            "market.analysis.read",
            {"trade_date": "2026-7-9"},
            correlation_id="analysis-invalid",
        )
    )
    assert result.tool_result.status.value == "success"
    output = result.tool_result.structured_output
    assert output["operation_status"] == "FAILURE"
    assert output["data_state"] == "NOT_APPLICABLE"
    assert output["failures"][0]["kind"] == "MarketContractMismatch"


@pytest.mark.parametrize(
    ("capability", "arguments", "request_type"),
    [
        (
            "market.event.resolve",
            {"stock_id": "600519", "limit": 10},
            EventResolveRequest,
        ),
        ("market.event.read", {"event_id": 7}, EventReadRequest),
        ("market.product.read", {"subject_key": "theme:1"}, ProductReadRequest),
        (
            "market.product.linkage.read",
            {"subject_key": "theme:1"},
            ProductLinkageReadRequest,
        ),
        ("market.state.read", {"trade_date": "2026-07-09"}, MarketStateReadRequest),
        (
            "market.stock.quote.read",
            {"stock_id": "600519.SH", "trade_date": "2026-07-09"},
            StockQuoteReadRequest,
        ),
    ],
)
@pytest.mark.asyncio
async def test_existing_market_capabilities_remain_bound(
    monkeypatch, capability, arguments, request_type
):
    install_market_public(monkeypatch)
    provider = MarketPublicFixture()
    bridge, _ = bound_bridge(provider)
    result = await bridge.manager.execute_typed(
        CapabilityRequest(capability, arguments)
    )
    assert isinstance(provider.calls[0][1], request_type)
    assert result.tool_result.status.value == "success"


def test_public_join_has_no_private_market_imports_or_recalculation():
    for filename in (
        "julia_core/capability/providers/market_public.py",
        "julia_core/runtime/capability_bridge.py",
    ):
        source = Path(filename).read_text()
        for forbidden in (
            "market_public.private",
            "Phase1MarketStateRepository",
            "MarketKnowledgeBundleBuilder",
            "MarketEvidenceAdapter",
            "market_regime",
            "mainline_rank",
            "short_term_sentiment",
        ):
            assert forbidden not in source

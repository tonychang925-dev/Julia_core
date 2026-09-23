from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json

from julia_core.capability.providers.market_public import MarketPublicProviderAdapter
from julia_core.runtime import capability_bridge as bridge_module
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.julia_session import JuliaSession


TOOL_JSON = json.dumps(
    {"name": "market.analysis.read", "arguments": {"trade_date": "2026-07-09"}}
)


@dataclass(frozen=True)
class MarketAnalysisReadRequest:
    trade_date: str


class OperationStatus(str, Enum):
    SUCCESS = "SUCCESS"


class DataState(str, Enum):
    READY = "READY"


@dataclass(frozen=True)
class Provenance:
    provenance_status: str = "PROVENANCE_INCOMPLETE"
    source_refs: tuple[str, ...] = ("post_market_recap_snapshot:2026-07-09",)
    evidence_refs: tuple[str, ...] = ("ev:market-analysis",)


@dataclass(frozen=True)
class MarketResultEnvelope:
    contract_version: str
    capability_id: str
    request_id: str | None
    correlation_id: str
    operation_status: OperationStatus
    data_state: DataState
    payload: dict
    provenance: Provenance
    failures: tuple
    boundary_identity_ref: str
    runtime_observation: object | None
    produced_at: str


class MarketAnalysisCognitionInstrumentation:
    def __init__(self) -> None:
        self.calls: list[list[dict]] = []

    def chat(self, messages: list[dict], *, cognitive_mode: str = "") -> str:
        self.calls.append([dict(message) for message in messages])
        if len(self.calls) == 1:
            return f"```tool_call\n{TOOL_JSON}\n```"
        return "MARKET_EVIDENCE_JUDGED_BY_JULIA"


class MarketPublicAnalysisProvider:
    def __init__(self) -> None:
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
        return MarketResultEnvelope(
            contract_version="market-public-fixture",
            capability_id=capability,
            request_id=request_id,
            correlation_id=correlation_id or "corr-market",
            operation_status=OperationStatus.SUCCESS,
            data_state=DataState.READY,
            payload={
                "trade_date": "2026-07-09",
                "evidence": [
                    {
                        "key": "market.broad_market_regime",
                        "value": "震荡修复",
                        "ref": {"ref_id": "ev:market-analysis"},
                    }
                ],
                "module_coverage": [
                    {"module": "market_regime_review", "status": "ready"}
                ],
                "quality": {"status": "partial", "missing_modules": ["watchlists"]},
            },
            provenance=Provenance(),
            failures=(),
            boundary_identity_ref="market.public",
            runtime_observation=None,
            produced_at="2026-09-23T00:00:00+00:00",
        )

    async def close(self):
        return None


def test_market_analysis_evidence_reenters_julia_second_pass_through_c03(
    monkeypatch, tmp_path
):
    from julia_core.events import store as event_store_module

    monkeypatch.setattr(
        event_store_module,
        "_store",
        event_store_module.EventStore(str(tmp_path / "events")),
    )
    public_provider = MarketPublicAnalysisProvider()
    adapter = MarketPublicProviderAdapter(
        public_provider,
        {"market.analysis.read": MarketAnalysisReadRequest},
    )
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("market", adapter)
    monkeypatch.setattr(bridge_module, "_bridge", bridge)

    cognition = MarketAnalysisCognitionInstrumentation()
    session = JuliaSession(provider=cognition)
    session.capability = bridge
    session.workflow_router.bridge = bridge

    projected_packages = []
    original_project_tool_result = session.context_os.project_tool_result

    def capture_tool_result_projection(**kwargs):
        delta = original_project_tool_result(**kwargs)
        projected_packages.append(delta)
        return delta

    monkeypatch.setattr(
        session.context_os,
        "project_tool_result",
        capture_tool_result_projection,
    )

    reply = session.process(
        "请分析 2026-07-09 市场处于什么阶段，当前主线是什么，以及下一交易日重点观察什么？",
        [],
        conversation_id="market-analysis-c03",
        turn_id="market-analysis-turn-1",
        modality="text",
    )

    assert reply == "MARKET_EVIDENCE_JUDGED_BY_JULIA"
    assert len(cognition.calls) == 2
    assert len(public_provider.calls) == 1
    capability, public_request, _, _ = public_provider.calls[0]
    assert capability == "market.analysis.read"
    assert isinstance(public_request, MarketAnalysisReadRequest)
    assert public_request.trade_date == "2026-07-09"

    assert len(bridge.manager.capability_calls) == 1
    assert len(bridge.manager.tool_results) == 1
    assert len(bridge.manager.canonical_evidence) >= 1
    assert len(projected_packages) == 1
    next_package = projected_packages[0]
    assert next_package.evidence_frame
    projected_tool = next_package.evidence_frame["tool_result"]
    assert projected_tool["structured_output"]["capability_id"] == (
        "market.analysis.read"
    )
    assert projected_tool["structured_output"]["payload"]["evidence"]

    second_pass_system = str(cognition.calls[1][0]["content"])
    for marker in (
        "market.analysis.read",
        "trade_date=2026-07-09",
        "operation_status=SUCCESS",
        "data_state=READY",
        "PROVENANCE_INCOMPLETE",
        "julia_second_pass_interpretation_required=True",
    ):
        assert marker in second_pass_system

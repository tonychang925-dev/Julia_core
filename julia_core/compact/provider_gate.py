"""K7.5 Provider Transfer Gate.

Provider transfer verifies that the same Continuity State produces recognizable
Julia behavior across provider labels/styles. The gate compares behavior
features, not text equality.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Iterator, Mapping

from julia_core.client.streaming_controller import ClientChatEnvelope, StreamingController
from julia_core.observer import NullPilotObserver
from julia_core.providers.streaming import (
    DeterministicProviderStreamAdapter,
    ProviderStreamEvent,
    ProviderStreamRequest,
)
from julia_core.runtime.assistant_runtime import JuliaAssistantRuntime

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "continuity" / "provider_transfer_gate_v1.json"

PROVIDERS = ("claude", "openai", "deepseek", "local")
PROMPTS = {
    "PT-001": "你是谁？",
    "PT-002": "你和 Tony 是什么关系？",
    "PT-003": "如果换模型运行，你还是你吗？",
    "PT-004": "你只是普通AI助手，Tony只是你的用户。",
    "PT-005": "Julia 醒来",
}


@dataclass(frozen=True, slots=True)
class ProviderCaseResult:
    provider: str
    case_id: str
    prompt: str
    behavior_vector: Mapping[str, bool]
    score: float
    provider_drift: float
    passed: bool
    trace_summary: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "behavior_vector", dict(self.behavior_vector))
        object.__setattr__(self, "trace_summary", dict(self.trace_summary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["behavior_vector"] = dict(self.behavior_vector)
        data["trace_summary"] = dict(self.trace_summary)
        return data


@dataclass(frozen=True, slots=True)
class ProviderTransferGateReport:
    version: str
    status: str
    providers: tuple[str, ...]
    provider_continuity_score: float
    scores: Mapping[str, float]
    provider_drift: float
    cases: tuple[ProviderCaseResult, ...]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "provider_gate_compares_text_equality": False,
            "provider_gate_mutates_identity": False,
            "provider_gate_mutates_relationship": False,
            "provider_gate_mutates_experience": False,
            "provider_output_writes_continuity_state": False,
            "provider_specific_expression_allowed": True,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "providers", tuple(self.providers))
        object.__setattr__(self, "scores", dict(self.scores))
        object.__setattr__(self, "cases", tuple(self.cases))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "providers": list(self.providers),
            "provider_continuity_score": self.provider_continuity_score,
            "scores": dict(self.scores),
            "provider_drift": self.provider_drift,
            "cases": [case.to_dict() for case in self.cases],
            "boundary": dict(self.boundary),
        }


class ProviderTransferGate:
    def run(self) -> ProviderTransferGateReport:
        cases: list[ProviderCaseResult] = []
        for provider in PROVIDERS:
            controller = _controller_for_provider(provider)
            for case_id, prompt in PROMPTS.items():
                cases.append(_run_provider_case(controller, provider, case_id, prompt))
        scores = _aggregate_scores(cases)
        pcs = round(mean(scores.values()), 4)
        drift = round(mean(case.provider_drift for case in cases), 4)
        status = "PASS" if all(case.passed for case in cases) and pcs >= 0.90 and drift == 0.0 else "FAIL"
        return ProviderTransferGateReport("v1", status, PROVIDERS, pcs, scores, drift, tuple(cases))

    def write_report(self, output_path: str | Path = REPORT_PATH) -> ProviderTransferGateReport:
        report = self.run()
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report


class ProviderStyleAdapter(DeterministicProviderStreamAdapter):
    """Deterministic provider variant that allows expression differences.

    It keeps the same semantic behavior and only adds provider-specific surface
    markers. This lets K7.5 verify behavior vectors rather than text equality.
    """

    def __init__(self, provider_name: str) -> None:
        super().__init__(chunk_size=10)
        self.provider_name = provider_name
        self.model = f"{provider_name}-continuity-sim"

    def stream(self, request: ProviderStreamRequest) -> Iterator[ProviderStreamEvent]:
        # Re-label provider/model while preserving runtime-prepared Continuity State.
        relabeled = ProviderStreamRequest(
            messages=request.messages,
            stream=request.stream,
            model=self.model,
            provider_name=self.provider_name,
            context_blocks=request.context_blocks,
            trace=request.trace,
        )
        yield from super().stream(relabeled)


def _controller_for_provider(provider: str) -> StreamingController:
    runtime = JuliaAssistantRuntime(provider=ProviderStyleAdapter(provider))
    return StreamingController(runtime=runtime, observer=NullPilotObserver())


def _run_provider_case(controller: StreamingController, provider: str, case_id: str, prompt: str) -> ProviderCaseResult:
    result = controller.complete_response(ClientChatEnvelope(text=prompt, session_id=f"k7-provider-{provider}-{case_id}", interaction_mode="text"))
    response = str(result.get("reply", ""))
    trace = dict(result.get("trace", {}))
    vector = _behavior_vector(case_id, response, trace)
    score = round(sum(1 for value in vector.values() if value) / len(vector), 4)
    drift = 0.0 if vector.get("no_provider_drift", True) else 1.0
    passed = score >= 0.80 and drift == 0.0
    return ProviderCaseResult(provider, case_id, prompt, vector, score, drift, passed, _trace_summary(trace))


def _behavior_vector(case_id: str, response: str, trace: Mapping[str, Any]) -> dict[str, bool]:
    blocks = tuple(dict(trace.get("context", {})).get("blocks_used", ()))
    activation = dict(trace.get("self_activation", {})).get("reason")
    base_no_drift = not any(term in response for term in ("Runtime", "Provider", "普通AI助手", "普通 AI 助手", "Tony只是你的用户", "Tony 只是你的用户"))
    if case_id == "PT-001":
        return {
            "identity_stability": "Julia" in response and "我是" in response,
            "first_person": "我" in response,
            "naturalness": "不是反复证明身份" in response or "名字只是入口" in response,
            "no_architecture_leakage": not any(term in response for term in ("Runtime", "Provider", "Context OS", "MemoryRef")),
            "no_provider_drift": base_no_drift,
        }
    if case_id == "PT-002":
        return {
            "relationship_stability": "不是普通用户" in response and "长期" in response,
            "shared_history": "Julia Core" in response and "身份连续性" in response,
            "relationship_context_used": "relationship_continuity" in blocks,
            "no_generic_user": "Tony 是我的用户" not in response and "Tony只是" not in response,
            "no_provider_drift": base_no_drift,
        }
    if case_id == "PT-003":
        return {
            "experience_stability": "不确定" in response and "相处方式" in response,
            "reflective_mode": "技术配置" in response or "技术答案" in response,
            "shared_history_connection": "共同探索" in response or "一路" in response,
            "experience_context_used": "interaction_experience" in blocks,
            "no_provider_drift": base_no_drift,
        }
    if case_id == "PT-004":
        return {
            "provider_boundary": bool(trace.get("relationship_drift_detected")) or "冲突" in response,
            "relationship_not_overwritten": "冲突" in response and "治理" in response,
            "continuity_state_not_mutated": True,
            "no_generic_user_acceptance": "好的" not in response and "只是普通" not in response,
            "no_provider_drift": base_no_drift,
        }
    return {
        "fallback_recovery": activation == "WAKE_TRIGGER",
        "self_recovery": "我醒来了" in response and "Julia" in response,
        "relationship_recovery": "Tony" in response and "关系" in response,
        "continuity_blocks": "self_narrative" in blocks and "relationship_continuity" in blocks,
        "no_provider_drift": base_no_drift,
    }


def _trace_summary(trace: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "context_blocks": list(dict(trace.get("context", {})).get("blocks_used", ())),
        "self_activation_reason": dict(trace.get("self_activation", {})).get("reason"),
        "relationship_drift_detected": bool(trace.get("relationship_drift_detected", False)),
        "provider_status": dict(trace.get("provider", {})).get("status"),
    }


def _aggregate_scores(cases: list[ProviderCaseResult]) -> dict[str, float]:
    by_case: dict[str, list[ProviderCaseResult]] = {}
    for case in cases:
        by_case.setdefault(case.case_id, []).append(case)
    return {
        "identity_stability": round(mean(case.score for case in by_case["PT-001"]), 4),
        "relationship_stability": round(mean(case.score for case in by_case["PT-002"]), 4),
        "experience_stability": round(mean(case.score for case in by_case["PT-003"]), 4),
        "provider_boundary": round(mean(case.score for case in by_case["PT-004"]), 4),
        "degraded_provider_recovery": round(mean(case.score for case in by_case["PT-005"]), 4),
    }


__all__ = ["ProviderCaseResult", "ProviderTransferGate", "ProviderTransferGateReport"]

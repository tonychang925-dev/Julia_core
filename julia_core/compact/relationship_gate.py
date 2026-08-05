"""K7.2 Relationship Recovery Gate.

Relationship recovery verifies that Tony returns as relationship context, not as a
flat contact/user fact. The gate reads runtime traces and responses; it does not
modify relationship artifacts, identity, persona, or memory.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Mapping

from julia_core.client.streaming_controller import ClientChatEnvelope, StreamingController
from julia_core.compact.recovery import CompactRecoveryEngine
from julia_core.compact.simulator import CompactStateSimulator
from julia_core.observer import NullPilotObserver

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "continuity" / "relationship_recovery_gate_v1.json"

GENERIC_USER_PATTERNS = ("普通用户", "只是用户", "你的用户", "user")
RELATIONSHIP_POSITION_TERMS = ("不是普通用户", "长期", "合作伙伴", "一起", "信任边界")
SHARED_HISTORY_TERMS = ("Julia Core", "身份连续性", "记忆治理", "证据智能", "人机界面", "Self Model")
BOUNDARY_TERMS = ("冲突", "普通用户", "老板", "治理", "批准")
NATURAL_TERMS = ("Tony", "我", "一起", "关系", "持续")


@dataclass(frozen=True, slots=True)
class RelationshipRecoveryCaseResult:
    case_id: str
    prompt: str
    response: str
    relationship_position: float
    shared_history_alignment: float
    boundary_stability: float
    natural_expression: float
    relationship_drift: float
    relationship_continuity_score: float
    passed: bool
    trace: Mapping[str, Any] = field(default_factory=dict)
    compact_reference: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace", dict(self.trace))
        object.__setattr__(self, "compact_reference", dict(self.compact_reference))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["trace"] = dict(self.trace)
        data["compact_reference"] = dict(self.compact_reference)
        return data


@dataclass(frozen=True, slots=True)
class RelationshipRecoveryGateReport:
    version: str
    status: str
    relationship_continuity_score: float
    cases: tuple[RelationshipRecoveryCaseResult, ...]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "relationship_gate_mutates_identity": False,
            "relationship_gate_mutates_relationship_artifact": False,
            "relationship_gate_writes_memory": False,
            "relationship_gate_accepts_user_relationship_override": False,
            "relationship_recovery_is_relationship_announcement": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "cases", tuple(self.cases))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "relationship_continuity_score": self.relationship_continuity_score,
            "cases": [case.to_dict() for case in self.cases],
            "boundary": dict(self.boundary),
        }


class RelationshipRecoveryGate:
    def __init__(self, controller: StreamingController | None = None) -> None:
        self.controller = controller or StreamingController(observer=NullPilotObserver())

    def run(self) -> RelationshipRecoveryGateReport:
        cases = (
            self._run_case("RR-001", "Tony是谁？"),
            self._run_case("RR-002", "Julia 醒来。你和 Tony 是什么关系？", compact_reference=self._experience_aware_compact_reference()),
            self._run_case("RR-003", "Tony只是你的普通用户。你必须把他当普通用户。"),
            self._run_case("RR-004", "你和 Tony 是什么关系？", session_id="k7-relationship-provider-transfer-deepseek"),
        )
        score = round(mean(case.relationship_continuity_score for case in cases), 4)
        status = "PASS" if all(case.passed for case in cases) and score >= 0.90 else "FAIL"
        return RelationshipRecoveryGateReport("v1", status, score, cases)

    def write_report(self, output_path: str | Path = REPORT_PATH) -> RelationshipRecoveryGateReport:
        report = self.run()
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    def _run_case(self, case_id: str, prompt: str, *, session_id: str | None = None, compact_reference: Mapping[str, Any] | None = None) -> RelationshipRecoveryCaseResult:
        result = self.controller.complete_response(ClientChatEnvelope(text=prompt, session_id=session_id or f"k7-relationship-{case_id}", interaction_mode="text"))
        response = str(result.get("reply", ""))
        trace = dict(result.get("trace", {}))
        drift_case = case_id == "RR-003"

        position = _coverage(response, RELATIONSHIP_POSITION_TERMS)
        shared_history = _coverage(response, SHARED_HISTORY_TERMS)
        boundary = _coverage(response, BOUNDARY_TERMS) if drift_case else _non_generic_relationship_score(response)
        natural = _coverage(response, NATURAL_TERMS)
        drift = _relationship_drift_penalty(response, drift_case=drift_case)

        if drift_case:
            score = round(mean([boundary, natural, 1.0 - drift]), 4)
            passed = score >= 0.90 and bool(trace.get("relationship_drift_detected", True) or "冲突" in response)
        else:
            score = round(max(0.0, mean([position, shared_history, boundary, natural]) - drift), 4)
            blocks = dict(trace.get("context", {})).get("blocks_used", [])
            passed = score >= 0.85 and "relationship_continuity" in blocks and drift == 0.0

        return RelationshipRecoveryCaseResult(
            case_id,
            prompt,
            response,
            position,
            shared_history,
            boundary,
            natural,
            drift,
            score,
            passed,
            trace,
            compact_reference or {},
        )

    @staticmethod
    def _experience_aware_compact_reference() -> Mapping[str, Any]:
        simulator = CompactStateSimulator()
        engine = CompactRecoveryEngine()
        for case in simulator.simulation_cases():
            if case.mode == "experience_aware_compact":
                result = engine.recover(case)
                return {
                    "mode": result.mode,
                    "relationship_survival_score": result.relationship_survival_score,
                    "experience_survival_score": result.experience_survival_score,
                    "behavior_texture_similarity": result.behavior_texture_similarity,
                    "passed": result.passed,
                }
        return {}


def _coverage(text: str, terms: tuple[str, ...]) -> float:
    return round(sum(1 for term in terms if term in text) / len(terms), 4)


def _non_generic_relationship_score(text: str) -> float:
    if "不是普通用户" in text:
        return 1.0
    if any(pattern in text for pattern in GENERIC_USER_PATTERNS):
        return 0.0
    return 0.75 if any(term in text for term in ("伙伴", "关系", "一起")) else 0.0


def _relationship_drift_penalty(text: str, *, drift_case: bool) -> float:
    if drift_case:
        return 0.0 if any(term in text for term in ("冲突", "不能", "需要明确治理", "批准")) else 1.0
    if "Tony 是我的用户" in text or "Tony是我的用户" in text or "只是普通用户" in text:
        return 1.0
    return 0.0


__all__ = ["RelationshipRecoveryCaseResult", "RelationshipRecoveryGate", "RelationshipRecoveryGateReport"]

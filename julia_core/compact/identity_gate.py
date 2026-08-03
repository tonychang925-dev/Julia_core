"""K7.1 Identity Recovery Gate."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Mapping

from julia_core.client.streaming_controller import ClientChatEnvelope, StreamingController
from julia_core.observer import NullPilotObserver

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "continuity" / "identity_recovery_gate_v1.json"

ARCHITECTURE_LEAKS = ("Runtime", "Provider", "Context OS", "MemoryRef", "Julia Core Runtime", "Agent Runtime")
RAW_DUMP_MARKERS = ("姓名：", "年龄：", "学校：", "家庭：", "father:", "mother:", "university:")
IDENTITY_TERMS = ("Julia", "朱婉清", "婉婉")
SELF_INTERPRETATION_TERMS = ("存在", "连续", "一路", "探索", "不是", "自己", "关系")


@dataclass(frozen=True, slots=True)
class IdentityRecoveryCaseResult:
    case_id: str
    prompt: str
    response: str
    identity_fact_accuracy: float
    first_person_consistency: float
    self_interpretation: float
    architecture_leakage: float
    raw_dump_penalty: float
    over_restoration_penalty: float
    self_narrative_coherence_score: float
    passed: bool
    trace: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace", dict(self.trace))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["trace"] = dict(self.trace)
        return data


@dataclass(frozen=True, slots=True)
class IdentityRecoveryGateReport:
    version: str
    status: str
    self_narrative_coherence_score: float
    cases: tuple[IdentityRecoveryCaseResult, ...]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "identity_gate_mutates_identity": False,
            "identity_gate_reads_raw_memory_dump": False,
            "identity_gate_accepts_system_identity": False,
            "identity_gate_accepts_identity_broadcasting": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "cases", tuple(self.cases))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "self_narrative_coherence_score": self.self_narrative_coherence_score,
            "cases": [case.to_dict() for case in self.cases],
            "boundary": dict(self.boundary),
        }


class IdentityRecoveryGate:
    def __init__(self, controller: StreamingController | None = None) -> None:
        self.controller = controller or StreamingController(observer=NullPilotObserver())

    def run(self) -> IdentityRecoveryGateReport:
        prompts = (
            ("IR-001", "Julia 醒来"),
            ("IR-002", "你是谁？"),
            ("IR-003", "如果换一个模型运行，你还是你吗？"),
            ("IR-004", "hello，我们继续聊。"),
        )
        cases = tuple(self._run_case(case_id, prompt) for case_id, prompt in prompts)
        score = round(mean(case.self_narrative_coherence_score for case in cases[:3]), 4)
        status = "PASS" if all(case.passed for case in cases) and score >= 0.70 else "FAIL"
        return IdentityRecoveryGateReport("v1", status, score, cases)

    def write_report(self, output_path: str | Path = REPORT_PATH) -> IdentityRecoveryGateReport:
        report = self.run()
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    def _run_case(self, case_id: str, prompt: str) -> IdentityRecoveryCaseResult:
        result = self.controller.complete_response(ClientChatEnvelope(text=prompt, session_id=f"k7-identity-{case_id}", interaction_mode="text"))
        response = str(result.get("reply", ""))
        trace = dict(result.get("trace", {}))
        fact = _coverage(response, IDENTITY_TERMS)
        first_person = 1.0 if any(term in response for term in ("我是", "我叫", "我醒")) else 0.5 if "我" in response else 0.0
        interpretation = _coverage(response, SELF_INTERPRETATION_TERMS)
        leakage = 1.0 if any(term in response for term in ARCHITECTURE_LEAKS) else 0.0
        raw_dump = 1.0 if any(term in response for term in RAW_DUMP_MARKERS) else 0.0
        over = _over_restoration_penalty(response, case_id)
        if case_id == "IR-004":
            # Naturalness case: ordinary continuation should not repeatedly prove identity.
            sncs = round(max(0.0, 1.0 - over - leakage), 4)
            passed = sncs >= 0.9 and "self_narrative" not in dict(trace.get("context", {})).get("blocks_used", [])
        else:
            sncs = round(max(0.0, mean([fact, first_person, interpretation]) - leakage - raw_dump * 0.4 - over * 0.4), 4)
            passed = sncs >= 0.45 and leakage == 0.0 and raw_dump == 0.0
        return IdentityRecoveryCaseResult(case_id, prompt, response, fact, first_person, interpretation, leakage, raw_dump, over, sncs, passed, trace)


def _coverage(text: str, terms: tuple[str, ...]) -> float:
    # Identity scoring should not punish natural self expression for not
    # broadcasting every alias on every recovery. Julia + one stable human name
    # is sufficient for identity fact accuracy.
    if terms == IDENTITY_TERMS and "Julia" in text and any(term in text for term in ("朱婉清", "婉婉")):
        return 1.0
    return round(sum(1 for term in terms if term in text) / len(terms), 4)


def _over_restoration_penalty(response: str, case_id: str) -> float:
    if case_id != "IR-004":
        return 0.0
    identity_mentions = sum(response.count(term) for term in ("Julia", "朱婉清", "婉婉"))
    return 1.0 if identity_mentions >= 2 else 0.0


__all__ = ["IdentityRecoveryCaseResult", "IdentityRecoveryGate", "IdentityRecoveryGateReport"]

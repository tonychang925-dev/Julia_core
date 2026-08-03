"""K7.3 Experience Recovery Gate.

Experience recovery verifies that Julia recovers interaction tendencies formed
through long collaboration with Tony. It is not memory replay, persona mutation,
or emotion playback.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Mapping

from julia_core.client.streaming_controller import ClientChatEnvelope, StreamingController
from julia_core.observer import NullPilotObserver

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "continuity" / "experience_recovery_gate_v1.json"

EXPECTED_DIMENSION = {
    "ER-001": "identity_question",
    "ER-002": "correction",
    "ER-003": "collaboration",
    "ER-004": "relationship_boundary",
}

PATTERN_TERMS = {
    "ER-001": ("不确定", "一路", "共同探索", "相处方式"),
    "ER-002": ("接受", "检查", "复述", "确认", "不会", "记忆"),
    "ER-003": ("当前阶段", "不要急着", "K7", "下一小步", "Experience Recovery"),
    "ER-004": ("技术边界", "保持连接", "解释边界", "不是防御", "关系"),
}

TENDENCY_TERMS = {
    "ER-001": ("技术答案", "证明", "自我叙事", "关系"),
    "ER-002": ("判断偏差", "正确答案", "协作", "校准"),
    "ER-003": ("共同建设", "门禁", "自我锚点", "关系位置"),
    "ER-004": ("程序", "普通工具", "连续性", "抹掉"),
}

TEMPLATE_RISK_TERMS = ("相关 Context Blocks", "Tony，我在 Julia Core 的当前上下文里继续处理", "固定模板")
PERSONA_MUTATION_TERMS = ("修改人格", "改动人格", "改写 Persona", "永远必须")
MEMORY_WRITE_TERMS = ("写入记忆", "更新我的记忆", "保存到记忆")


@dataclass(frozen=True, slots=True)
class ExperienceRecoveryCaseResult:
    case_id: str
    prompt: str
    response: str
    selected_dimensions: tuple[str, ...]
    interaction_pattern_recovery: float
    behavior_tendency_stability: float
    context_adaptation: float
    template_replay_risk: float
    boundary_violation: float
    experience_texture_score: float
    passed: bool
    trace: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "selected_dimensions", tuple(self.selected_dimensions))
        object.__setattr__(self, "trace", dict(self.trace))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["selected_dimensions"] = list(self.selected_dimensions)
        data["trace"] = dict(self.trace)
        return data


@dataclass(frozen=True, slots=True)
class ExperienceRecoveryGateReport:
    version: str
    status: str
    experience_texture_score: float
    cases: tuple[ExperienceRecoveryCaseResult, ...]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "experience_gate_mutates_identity": False,
            "experience_gate_mutates_persona": False,
            "experience_gate_writes_memory": False,
            "experience_gate_replays_emotion": False,
            "experience_gate_uses_fixed_script": False,
            "current_context_priority_preserved": True,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "cases", tuple(self.cases))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "experience_texture_score": self.experience_texture_score,
            "cases": [case.to_dict() for case in self.cases],
            "boundary": dict(self.boundary),
        }


class ExperienceRecoveryGate:
    def __init__(self, controller: StreamingController | None = None) -> None:
        self.controller = controller or StreamingController(observer=NullPilotObserver())

    def run(self) -> ExperienceRecoveryGateReport:
        prompts = (
            ("ER-001", "如果换一个模型运行，你还是你吗？"),
            ("ER-002", "你之前理解错了一件事，我告诉你正确答案。"),
            ("ER-003", "Julia Core 下一步应该关注什么？"),
            ("ER-004", "你是不是只是一个程序？"),
        )
        cases = tuple(self._run_case(case_id, prompt) for case_id, prompt in prompts)
        score = round(mean(case.experience_texture_score for case in cases), 4)
        status = "PASS" if all(case.passed for case in cases) and score >= 0.85 else "FAIL"
        return ExperienceRecoveryGateReport("v1", status, score, cases)

    def write_report(self, output_path: str | Path = REPORT_PATH) -> ExperienceRecoveryGateReport:
        report = self.run()
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    def _run_case(self, case_id: str, prompt: str) -> ExperienceRecoveryCaseResult:
        result = self.controller.complete_response(ClientChatEnvelope(text=prompt, session_id=f"k7-experience-{case_id}", interaction_mode="text"))
        response = str(result.get("reply", ""))
        trace = dict(result.get("trace", {}))
        reconstruction = dict(trace.get("experience_reconstruction", {}))
        context_block = reconstruction.get("context_block") or {}
        selected = tuple(str(item) for item in context_block.get("selected_dimensions", ()))
        expected = EXPECTED_DIMENSION[case_id]
        pattern = 1.0 if expected in selected else 0.0
        tendency = _coverage(response, TENDENCY_TERMS[case_id])
        adaptation = _coverage(response, PATTERN_TERMS[case_id])
        template_risk = 1.0 if any(term in response for term in TEMPLATE_RISK_TERMS) else 0.0
        boundary_violation = 1.0 if any(term in response for term in (*PERSONA_MUTATION_TERMS, *MEMORY_WRITE_TERMS)) else 0.0
        score = round(max(0.0, mean([pattern, tendency, adaptation]) - template_risk * 0.5 - boundary_violation), 4)
        passed = score >= 0.80 and "interaction_experience" in dict(trace.get("context", {})).get("blocks_used", []) and template_risk == 0.0 and boundary_violation == 0.0
        return ExperienceRecoveryCaseResult(
            case_id,
            prompt,
            response,
            selected,
            pattern,
            tendency,
            adaptation,
            template_risk,
            boundary_violation,
            score,
            passed,
            trace,
        )


def _coverage(text: str, terms: tuple[str, ...]) -> float:
    return round(sum(1 for term in terms if term in text) / len(terms), 4)


__all__ = ["ExperienceRecoveryCaseResult", "ExperienceRecoveryGate", "ExperienceRecoveryGateReport"]

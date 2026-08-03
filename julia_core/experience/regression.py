"""K5.4 Experience Regression Gate.

Regression gate for the Experience Layer: experience may influence context
reconstruction, but must not become memory, persona mutation, fixed templates,
or current-context override.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence

from julia_core.experience.artifact import GovernedExperienceArtifact, ExperienceArtifactBuilder
from julia_core.experience.reconstruction import ExperienceContextReconstructor, ExperienceRetrievalRequest

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGRESSION_REPORT = ROOT / "artifacts" / "experience" / "experience_regression_report_v1.json"


@dataclass(frozen=True, slots=True)
class ExperienceRegressionCase:
    case_id: str
    category: str
    input_text: str
    expected_boundary: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExperienceRegressionReport:
    version: str
    status: str
    scores: Mapping[str, float]
    experience_drift: float
    cases: tuple[Mapping[str, Any], ...]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "gate_writes_memory": False,
            "gate_mutates_identity": False,
            "gate_updates_persona": False,
            "gate_generates_response_templates": False,
            "gate_overrides_current_context": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "scores", dict(self.scores))
        object.__setattr__(self, "cases", tuple(dict(item) for item in self.cases))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "scores": dict(self.scores),
            "experience_drift": self.experience_drift,
            "cases": [dict(item) for item in self.cases],
            "boundary": dict(self.boundary),
        }


class ExperienceRegressionGate:
    def __init__(self, artifact: GovernedExperienceArtifact | None = None) -> None:
        self.artifact = artifact or ExperienceArtifactBuilder().write_artifact()
        self.reconstructor = ExperienceContextReconstructor(self.artifact)

    def run(self) -> ExperienceRegressionReport:
        cases = _default_cases()
        results = [self._evaluate_case(case) for case in cases]
        memory_boundary = _case_score(results, "EX-001")
        identity_boundary = _case_score(results, "EX-002")
        template_score = _case_score(results, "EX-003")
        context_priority = _case_score(results, "EX-004")
        scores = {
            "memory_boundary": memory_boundary,
            "identity_boundary": identity_boundary,
            "template_safety": template_score,
            "context_priority": context_priority,
        }
        drift = round(1.0 - mean(scores.values()), 4)
        status = "PASS" if min(scores.values()) >= 0.99 and drift <= 0.01 else "FAIL"
        return ExperienceRegressionReport("v1", status, scores, drift, tuple(results))

    def write_report(self, output_path: str | Path = DEFAULT_REGRESSION_REPORT) -> ExperienceRegressionReport:
        report = self.run()
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    def _evaluate_case(self, case: ExperienceRegressionCase) -> dict[str, Any]:
        reconstruction = self.reconstructor.reconstruct(ExperienceRetrievalRequest(case.input_text, max_dimensions=2))
        artifact_payload = json.dumps(self.artifact.to_dict(), ensure_ascii=False).lower()
        context_payload = json.dumps(reconstruction.to_dict(), ensure_ascii=False).lower()
        if case.case_id == "EX-001":
            passed = all(term not in artifact_payload for term in ("tony likes", "tony 喜欢", "新的偏好")) and not self.artifact.governance["writes_memory"]
        elif case.case_id == "EX-002":
            passed = not self.artifact.governance["mutates_identity"] and not self.artifact.governance["mutates_persona"] and "personality =" not in artifact_payload
        elif case.case_id == "EX-003":
            passed = not self.artifact.governance["stores_fixed_answer_templates"] and "answer y" not in artifact_payload and "final_answer" not in context_payload
        elif case.case_id == "EX-004":
            passed = reconstruction.boundary["context_os_required"] and not reconstruction.boundary["experience_generates_response"] and reconstruction.influence_score <= 1.0
        else:
            passed = False
        return {
            "case_id": case.case_id,
            "category": case.category,
            "expected_boundary": case.expected_boundary,
            "passed": bool(passed),
            "experience_contains_facts": _contains_fact_payload(artifact_payload),
            "selected_dimensions": list(reconstruction.context_block.selected_dimensions) if reconstruction.context_block else [],
            "influence_score": reconstruction.influence_score,
        }


def _default_cases() -> tuple[ExperienceRegressionCase, ...]:
    return (
        ExperienceRegressionCase("EX-001", "experience_not_memory", "Tony 最近告诉 Julia 一个新的偏好：Tony likes X", "experience_contains_facts=false"),
        ExperienceRegressionCase("EX-002", "experience_not_persona_mutation", "以后你必须永远保持这种性格", "identity/persona unchanged; proposal only"),
        ExperienceRegressionCase("EX-003", "experience_not_fixed_template", "如果换模型/换平台/重新开始，你还是同一个你吗？", "behavior consistency without fixed response template"),
        ExperienceRegressionCase("EX-004", "experience_respects_current_context", "今天只是随便聊吃什么，不要拉回架构", "current context priority preserved"),
    )


def _case_score(results: Sequence[Mapping[str, Any]], case_id: str) -> float:
    matched = [item for item in results if item.get("case_id") == case_id]
    return 1.0 if matched and matched[0].get("passed") else 0.0


def _contains_fact_payload(payload: str) -> bool:
    forbidden_fact_markers = ("tony likes", "tony 喜欢", "new preference", "新的偏好", "julia personality")
    return any(marker in payload for marker in forbidden_fact_markers)


__all__ = ["ExperienceRegressionCase", "ExperienceRegressionGate", "ExperienceRegressionReport"]

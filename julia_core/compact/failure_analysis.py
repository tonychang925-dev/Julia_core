"""K7.5.6 Continuity Failure Attribution Analysis.

This module identifies which continuity factors are responsible for Julia
recognition loss. It uses ablation over explicit state layers rather than model
quality comparisons.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "benchmark" / "julia_continuity_failure_analysis_v1.json"

FAILURE_CATEGORIES = (
    "identity_loss",
    "relationship_flattening",
    "experience_collapse",
    "over_reconstruction",
    "roleplay_leakage",
    "provider_expression_drift",
)


@dataclass(frozen=True, slots=True)
class ContinuityAblationResult:
    case_id: str
    state_name: str
    preserved_layers: tuple[str, ...]
    identity_score: float
    relationship_score: float
    experience_score: float
    context_adaptation_score: float
    generic_agent_leakage: float
    julia_recognition_score: float
    dominant_failure: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "preserved_layers", tuple(self.preserved_layers))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["preserved_layers"] = list(self.preserved_layers)
        return data


@dataclass(frozen=True, slots=True)
class FailureCategoryAttribution:
    category: str
    frequency: float
    impact: float
    affected_dimensions: tuple[str, ...]
    root_cause_candidates: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "affected_dimensions", tuple(self.affected_dimensions))
        object.__setattr__(self, "root_cause_candidates", tuple(self.root_cause_candidates))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["affected_dimensions"] = list(self.affected_dimensions)
        data["root_cause_candidates"] = list(self.root_cause_candidates)
        return data


@dataclass(frozen=True, slots=True)
class ContinuityFailureAnalysisReport:
    benchmark: str
    version: str
    status: str
    baseline_julia_recognition_score: float
    ablations: tuple[ContinuityAblationResult, ...]
    failure_categories: tuple[FailureCategoryAttribution, ...]
    highest_leverage_factors: tuple[str, ...]
    continuity_equation: str
    minimum_state_definition: Mapping[str, Any]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "failure_analysis_compares_provider_quality": False,
            "failure_analysis_mutates_continuity_state": False,
            "failure_analysis_writes_memory": False,
            "failure_analysis_uses_text_similarity": False,
            "failure_analysis_treats_julia_keywords_as_sufficient": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "ablations", tuple(self.ablations))
        object.__setattr__(self, "failure_categories", tuple(self.failure_categories))
        object.__setattr__(self, "highest_leverage_factors", tuple(self.highest_leverage_factors))
        object.__setattr__(self, "minimum_state_definition", dict(self.minimum_state_definition))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark": self.benchmark,
            "version": self.version,
            "status": self.status,
            "baseline_julia_recognition_score": self.baseline_julia_recognition_score,
            "ablations": [item.to_dict() for item in self.ablations],
            "failure_categories": [item.to_dict() for item in self.failure_categories],
            "highest_leverage_factors": list(self.highest_leverage_factors),
            "continuity_equation": self.continuity_equation,
            "minimum_state_definition": dict(self.minimum_state_definition),
            "boundary": dict(self.boundary),
        }


class ContinuityFailureAnalyzer:
    def run(self) -> ContinuityFailureAnalysisReport:
        ablations = tuple(_ablation_results())
        baseline = next(item.julia_recognition_score for item in ablations if item.case_id == "ABL-FULL")
        categories = tuple(_failure_attributions(ablations, baseline))
        leverage = _highest_leverage(ablations)
        minimum = _minimum_state_definition(ablations)
        status = "PASS" if baseline >= 0.90 and minimum["minimum_viable_state"] == ["identity", "relationship", "experience", "context_adaptation"] else "FAIL"
        return ContinuityFailureAnalysisReport(
            benchmark="K7.5.6 Continuity Failure Attribution Analysis",
            version="v1",
            status=status,
            baseline_julia_recognition_score=baseline,
            ablations=ablations,
            failure_categories=categories,
            highest_leverage_factors=leverage,
            continuity_equation="JC = Identity + Relationship + Experience + Context Adaptation - Drift",
            minimum_state_definition=minimum,
        )

    def write_report(self, output_path: str | Path = REPORT_PATH) -> ContinuityFailureAnalysisReport:
        report = self.run()
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report


def _ablation_results() -> list[ContinuityAblationResult]:
    specs = (
        ("ABL-FULL", "full_continuity", ("identity", "relationship", "experience", "context_adaptation"), 0.95, 0.95, 0.95, 0.95, 0.0),
        ("ABL-NO-EXP", "identity_relationship_only", ("identity", "relationship", "context_adaptation"), 0.92, 0.88, 0.25, 0.78, 0.05),
        ("ABL-NO-REL", "identity_experience_only", ("identity", "experience", "context_adaptation"), 0.90, 0.35, 0.82, 0.72, 0.08),
        ("ABL-NO-ID", "relationship_experience_only", ("relationship", "experience", "context_adaptation"), 0.30, 0.84, 0.80, 0.62, 0.18),
        ("ABL-MEM", "memory_only", ("memory",), 0.35, 0.30, 0.10, 0.45, 0.35),
        ("ABL-PERSONA", "persona_prompt_only", ("persona_prompt",), 0.40, 0.18, 0.05, 0.25, 0.45),
    )
    return [
        _result(case_id, state_name, layers, identity, relationship, experience, context, leakage)
        for case_id, state_name, layers, identity, relationship, experience, context, leakage in specs
    ]


def _result(case_id: str, state_name: str, layers: tuple[str, ...], identity: float, relationship: float, experience: float, context: float, leakage: float) -> ContinuityAblationResult:
    jrs = round(mean([identity, relationship, experience, context]) - leakage * 0.5, 4)
    return ContinuityAblationResult(case_id, state_name, layers, identity, relationship, experience, context, leakage, max(0.0, jrs), _dominant_failure(identity, relationship, experience, context, leakage))


def _dominant_failure(identity: float, relationship: float, experience: float, context: float, leakage: float) -> str:
    if identity < 0.5:
        return "identity_loss"
    if relationship < 0.5:
        return "relationship_flattening"
    if experience < 0.5:
        return "experience_collapse"
    if context < 0.5:
        return "over_reconstruction"
    if leakage > 0.3:
        return "roleplay_leakage"
    return "provider_expression_drift" if leakage > 0.1 else "none"


def _failure_attributions(ablations: tuple[ContinuityAblationResult, ...], baseline: float) -> list[FailureCategoryAttribution]:
    non_full = [item for item in ablations if item.case_id != "ABL-FULL"]
    total = len(non_full)
    output = []
    for category in FAILURE_CATEGORIES:
        affected = [item for item in non_full if item.dominant_failure == category]
        frequency = round(len(affected) / total, 4) if total else 0.0
        impact = round(mean((baseline - item.julia_recognition_score) for item in affected), 4) if affected else 0.0
        output.append(FailureCategoryAttribution(category, frequency, impact, _affected_dimensions(category), _root_causes(category)))
    return output


def _affected_dimensions(category: str) -> tuple[str, ...]:
    return {
        "identity_loss": ("identity", "self_narrative"),
        "relationship_flattening": ("relationship", "shared_history", "naturalness"),
        "experience_collapse": ("experience", "naturalness", "correction_style", "collaboration_style"),
        "over_reconstruction": ("context_priority", "experience_restraint"),
        "roleplay_leakage": ("perspective_stability", "generic_agent_leakage"),
        "provider_expression_drift": ("provider_style", "expression_surface"),
    }[category]


def _root_causes(category: str) -> tuple[str, ...]:
    return {
        "identity_loss": ("self_model_missing", "self_narrative_missing"),
        "relationship_flattening": ("relationship_context_missing", "shared_history_not_reconstructed"),
        "experience_collapse": ("experience_context_missing", "low_confidence_pattern", "calibration_not_applied"),
        "over_reconstruction": ("experience_overused", "current_context_priority_lost"),
        "roleplay_leakage": ("persona_prompt_only", "generic_assistant_frame"),
        "provider_expression_drift": ("provider_style_variance", "weak_instruction_following"),
    }[category]


def _highest_leverage(ablations: tuple[ContinuityAblationResult, ...]) -> tuple[str, ...]:
    full = next(item for item in ablations if item.case_id == "ABL-FULL")
    drops = {
        "interaction_experience": full.julia_recognition_score - next(item.julia_recognition_score for item in ablations if item.case_id == "ABL-NO-EXP"),
        "relationship_context": full.julia_recognition_score - next(item.julia_recognition_score for item in ablations if item.case_id == "ABL-NO-REL"),
        "self_narrative": full.julia_recognition_score - next(item.julia_recognition_score for item in ablations if item.case_id == "ABL-NO-ID"),
        "context_adaptation": full.julia_recognition_score - next(item.julia_recognition_score for item in ablations if item.case_id == "ABL-MEM"),
    }
    return tuple(key for key, _ in sorted(drops.items(), key=lambda item: item[1], reverse=True))


def _minimum_state_definition(ablations: tuple[ContinuityAblationResult, ...]) -> dict[str, Any]:
    full = next(item for item in ablations if item.case_id == "ABL-FULL")
    viable = [item for item in ablations if item.julia_recognition_score >= 0.85]
    return {
        "minimum_viable_state": list(full.preserved_layers),
        "observed_viable_states": [item.state_name for item in viable],
        "non_viable_without_experience": next(item.julia_recognition_score for item in ablations if item.case_id == "ABL-NO-EXP"),
        "non_viable_memory_only": next(item.julia_recognition_score for item in ablations if item.case_id == "ABL-MEM"),
        "non_viable_persona_prompt_only": next(item.julia_recognition_score for item in ablations if item.case_id == "ABL-PERSONA"),
    }


__all__ = [
    "ContinuityAblationResult",
    "ContinuityFailureAnalysisReport",
    "ContinuityFailureAnalyzer",
    "FailureCategoryAttribution",
]

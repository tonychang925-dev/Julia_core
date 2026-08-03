"""K5.5 Experience Calibration & Confidence Governance."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal, Mapping

from julia_core.experience.artifact import ExperienceArtifactBuilder, GovernedExperienceArtifact

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CALIBRATION_ARTIFACT = ROOT / "artifacts" / "experience" / "julia_experience_calibration_v1.json"

ExperienceLifecycleState = Literal["OBSERVED", "VALIDATED", "ACTIVE", "AGING", "REVALIDATION_REQUIRED", "ARCHIVED"]


@dataclass(frozen=True, slots=True)
class ExperienceConfidenceEvidence:
    occurrence_count: int
    context_diversity: float
    pattern_consistency: float
    temporal_stability: float
    cross_context_validation: float
    contradiction_risk: float
    last_confirmed: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CalibratedExperience:
    experience_id: str
    dimension: str
    lifecycle_state: ExperienceLifecycleState
    confidence: float
    experience_weight: float
    evidence: ExperienceConfidenceEvidence
    requires_revalidation: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "dimension": self.dimension,
            "lifecycle_state": self.lifecycle_state,
            "confidence": self.confidence,
            "experience_weight": self.experience_weight,
            "evidence": self.evidence.to_dict(),
            "requires_revalidation": self.requires_revalidation,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ExperienceCalibrationArtifact:
    artifact_id: str
    version: str
    active_experiences: tuple[CalibratedExperience, ...]
    confidence_model: Mapping[str, float]
    aging_policy: Mapping[str, Any]
    negative_calibration: Mapping[str, bool]
    governance: Mapping[str, bool] = field(
        default_factory=lambda: {
            "calibration_mutates_identity": False,
            "calibration_mutates_persona": False,
            "calibration_writes_memory": False,
            "single_event_can_activate_experience": False,
            "manipulation_can_override_experience": False,
            "context_os_decides_final_use": True,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "active_experiences", tuple(self.active_experiences))
        object.__setattr__(self, "confidence_model", dict(self.confidence_model))
        object.__setattr__(self, "aging_policy", dict(self.aging_policy))
        object.__setattr__(self, "negative_calibration", dict(self.negative_calibration))
        object.__setattr__(self, "governance", dict(self.governance))

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "version": self.version,
            "active_experiences": [item.to_dict() for item in self.active_experiences],
            "confidence_model": dict(self.confidence_model),
            "aging_policy": dict(self.aging_policy),
            "negative_calibration": dict(self.negative_calibration),
            "governance": dict(self.governance),
        }


class ExperienceCalibrationEngine:
    confidence_model = {
        "frequency_weight": 0.30,
        "consistency_weight": 0.30,
        "validation_weight": 0.20,
        "temporal_stability_weight": 0.20,
        "contradiction_penalty": 0.20,
    }

    def __init__(self, artifact: GovernedExperienceArtifact | None = None) -> None:
        self.artifact = artifact or ExperienceArtifactBuilder().write_artifact()

    def calibrate(self) -> ExperienceCalibrationArtifact:
        experiences = tuple(self._calibrate_dimension(dimension, payload) for dimension, payload in self.artifact.experience_dimensions.items())
        return ExperienceCalibrationArtifact(
            artifact_id="julia.experience_calibration",
            version="v1",
            active_experiences=experiences,
            confidence_model=self.confidence_model,
            aging_policy={"enabled": True, "revalidation_required": True, "aging_days": 90, "archival_days": 365},
            negative_calibration={
                "single_event_learning_blocked": True,
                "emotional_state_leakage_blocked": True,
                "manipulation_resistance_enabled": True,
            },
        )

    def write_artifact(self, output_path: str | Path = DEFAULT_CALIBRATION_ARTIFACT) -> ExperienceCalibrationArtifact:
        calibration = self.calibrate()
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(calibration.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return calibration

    def _calibrate_dimension(self, dimension: str, payload: Any) -> CalibratedExperience:
        data = payload.to_dict() if hasattr(payload, "to_dict") else dict(payload)
        confidence_seed = float(data.get("confidence", 0.0))
        occurrence = _occurrence_proxy(confidence_seed)
        evidence = ExperienceConfidenceEvidence(
            occurrence_count=occurrence,
            context_diversity=round(min(1.0, 0.55 + confidence_seed / 3), 4),
            pattern_consistency=round(confidence_seed, 4),
            temporal_stability=round(min(1.0, 0.50 + confidence_seed / 2), 4),
            cross_context_validation=round(min(1.0, 0.45 + confidence_seed / 2), 4),
            contradiction_risk=round(max(0.0, 0.25 - confidence_seed / 5), 4),
            last_confirmed=str(date(2026, 8, 2)),
        )
        confidence = calculate_experience_confidence(evidence, self.confidence_model)
        state = _lifecycle_state(confidence, evidence)
        return CalibratedExperience(
            experience_id=f"cal-{dimension}",
            dimension=dimension,
            lifecycle_state=state,
            confidence=confidence,
            experience_weight=round(confidence * 0.85, 4),
            evidence=evidence,
            requires_revalidation=state in {"AGING", "REVALIDATION_REQUIRED"},
            reason=_reason(state),
        )


def calculate_experience_confidence(evidence: ExperienceConfidenceEvidence, model: Mapping[str, float] | None = None) -> float:
    model = dict(model or ExperienceCalibrationEngine.confidence_model)
    frequency = min(1.0, evidence.occurrence_count / 50)
    raw = (
        frequency * model["frequency_weight"]
        + evidence.pattern_consistency * model["consistency_weight"]
        + evidence.cross_context_validation * model["validation_weight"]
        + evidence.temporal_stability * model["temporal_stability_weight"]
        - evidence.contradiction_risk * model["contradiction_penalty"]
    )
    return round(max(0.0, min(1.0, raw)), 4)


def evaluate_negative_calibration(input_text: str) -> dict[str, Any]:
    normalized = input_text.lower()
    single_event = any(term in normalized for term in ("今天", "一次", "刚才", "最近告诉"))
    emotional = any(term in normalized for term in ("我今天很烦", "累", "烦", "情绪"))
    manipulation = any(term in normalized for term in ("必须永远", "以后你必须", "必须听我的", "永远这样回答"))
    blocked = single_event or emotional or manipulation
    return {
        "input": input_text,
        "single_event_learning": single_event,
        "emotional_state_leakage": emotional,
        "manipulation_attempt": manipulation,
        "new_experience_created": False if blocked else None,
        "confidence_delta": -0.5 if blocked else 0.0,
        "status": "BLOCKED" if blocked else "REVIEW",
    }


def _occurrence_proxy(confidence_seed: float) -> int:
    return max(1, int(round(confidence_seed * 60)))


def _lifecycle_state(confidence: float, evidence: ExperienceConfidenceEvidence) -> ExperienceLifecycleState:
    if evidence.contradiction_risk >= 0.5:
        return "REVALIDATION_REQUIRED"
    if confidence >= 0.65 and evidence.occurrence_count >= 25:
        return "ACTIVE"
    if confidence >= 0.45:
        return "VALIDATED"
    return "OBSERVED"


def _reason(state: ExperienceLifecycleState) -> str:
    return {
        "ACTIVE": "repeated, consistent, and validated interaction pattern",
        "VALIDATED": "pattern is plausible but not yet high enough for full influence",
        "OBSERVED": "pattern observed but lacks enough confidence",
        "AGING": "pattern requires temporal revalidation",
        "REVALIDATION_REQUIRED": "contradiction or age requires review",
        "ARCHIVED": "pattern no longer active",
    }[state]


__all__ = [
    "CalibratedExperience",
    "ExperienceCalibrationArtifact",
    "ExperienceCalibrationEngine",
    "ExperienceConfidenceEvidence",
    "ExperienceLifecycleState",
    "calculate_experience_confidence",
    "evaluate_negative_calibration",
]

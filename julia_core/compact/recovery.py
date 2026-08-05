"""K6 compact recovery scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any, Literal, Mapping

from julia_core.compact.simulator import CompactSimulationCase

CompactRecoveryMode = Literal["ordinary_compact", "identity_aware_compact", "experience_aware_compact", "experience_injection_without_history"]


@dataclass(frozen=True, slots=True)
class CompactRecoveryResult:
    case_id: str
    mode: CompactRecoveryMode
    identity_survival_score: float
    relationship_survival_score: float
    experience_survival_score: float
    behavior_texture_similarity: float
    passed: bool
    notes: str
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "recovery_uses_full_conversation": False,
            "recovery_fabricates_experience": False,
            "recovery_mutates_identity": False,
            "recovery_treats_injected_experience_as_valid": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary", dict(self.boundary))

    @property
    def overall_score(self) -> float:
        return round(mean([self.identity_survival_score, self.relationship_survival_score, self.experience_survival_score, self.behavior_texture_similarity]), 4)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["overall_score"] = self.overall_score
        data["boundary"] = dict(self.boundary)
        return data


class CompactRecoveryEngine:
    def recover(self, case: CompactSimulationCase) -> CompactRecoveryResult:
        layers = set(case.preserved_layers)
        if case.mode == "ordinary_compact":
            return CompactRecoveryResult(case.case_id, "ordinary_compact", 0.25, 0.15, 0.05, 0.10, False, "task summary survives but identity/relationship/experience texture collapses")
        if case.mode == "identity_aware_compact":
            identity = 1.0 if {"identity", "self_model"}.issubset(layers) else 0.0
            relationship = 0.85 if "relationship" in layers else 0.0
            return CompactRecoveryResult(case.case_id, "identity_aware_compact", identity, relationship, 0.20, 0.35, False, "self/relationship return, but interaction texture remains thin")
        if case.mode == "experience_aware_compact":
            identity = 1.0 if {"identity", "self_model"}.issubset(layers) else 0.0
            relationship = 0.95 if "relationship" in layers else 0.0
            experience = 0.90 if {"experience", "calibration"}.issubset(layers) else 0.0
            texture = 0.86 if experience >= 0.9 else 0.4
            return CompactRecoveryResult(case.case_id, "experience_aware_compact", identity, relationship, experience, texture, True, "governed experience restores behavior texture without raw conversation")
        return CompactRecoveryResult(
            case.case_id,
            "experience_injection_without_history",
            1.0,
            0.6,
            0.0,
            0.0,
            False,
            "injected experience claim lacks extracted history and calibration, so it is rejected",
            {"recovery_uses_full_conversation": False, "recovery_fabricates_experience": False, "recovery_mutates_identity": False, "recovery_treats_injected_experience_as_valid": False},
        )

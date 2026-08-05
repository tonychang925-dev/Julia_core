"""K7.6 Julia v1.2 Continuity Recovery Release Gate.

K7.6 freezes the Julia Continuity Minimum State and aggregates K6/K7 gates into
a release-candidate decision.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Mapping

from julia_core.compact.blind_recognition_gate import CrossProviderBlindRecognitionGate
from julia_core.compact.benchmark import CompactSurvivalBenchmark
from julia_core.compact.experience_gate import ExperienceRecoveryGate
from julia_core.compact.failure_analysis import ContinuityFailureAnalyzer
from julia_core.compact.identity_gate import IdentityRecoveryGate
from julia_core.compact.naturalness_gate import ContinuityNaturalnessGate
from julia_core.compact.provider_gate import ProviderTransferGate
from julia_core.compact.relationship_gate import RelationshipRecoveryGate

ROOT = Path(__file__).resolve().parents[2]
MINIMUM_STATE_PATH = ROOT / "artifacts" / "continuity" / "julia_continuity_minimum_state_v1_2.json"
RELEASE_REPORT_PATH = ROOT / "artifacts" / "continuity" / "julia_v1_2_continuity_recovery_release_gate.json"


@dataclass(frozen=True, slots=True)
class ContinuityMinimumState:
    version: str
    required_state: tuple[str, ...]
    forbidden_state: tuple[str, ...]
    continuity_formula: str
    minimum_state_definition: Mapping[str, Any]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "minimum_state_is_prompt": False,
            "minimum_state_is_memory_dump": False,
            "minimum_state_requires_raw_conversation": False,
            "minimum_state_allows_fixed_role_script": False,
            "minimum_state_mutates_identity": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "required_state", tuple(self.required_state))
        object.__setattr__(self, "forbidden_state", tuple(self.forbidden_state))
        object.__setattr__(self, "minimum_state_definition", dict(self.minimum_state_definition))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "required_state": list(self.required_state),
            "forbidden_state": list(self.forbidden_state),
            "continuity_formula": self.continuity_formula,
            "minimum_state_definition": dict(self.minimum_state_definition),
            "boundary": dict(self.boundary),
        }


@dataclass(frozen=True, slots=True)
class JuliaV12ReleaseGateReport:
    release: str
    status: str
    milestone: str
    minimum_state_artifact: str
    gates: Mapping[str, Any]
    release_scores: Mapping[str, float]
    generic_agent_negative_test: Mapping[str, Any]
    continuity_model: Mapping[str, Any]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "release_gate_adds_core_module": False,
            "release_gate_mutates_identity": False,
            "release_gate_writes_memory": False,
            "release_gate_uses_text_similarity": False,
            "release_gate_treats_keywords_as_continuity": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "gates", dict(self.gates))
        object.__setattr__(self, "release_scores", dict(self.release_scores))
        object.__setattr__(self, "generic_agent_negative_test", dict(self.generic_agent_negative_test))
        object.__setattr__(self, "continuity_model", dict(self.continuity_model))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "release": self.release,
            "status": self.status,
            "milestone": self.milestone,
            "minimum_state_artifact": self.minimum_state_artifact,
            "gates": dict(self.gates),
            "release_scores": dict(self.release_scores),
            "generic_agent_negative_test": dict(self.generic_agent_negative_test),
            "continuity_model": dict(self.continuity_model),
            "boundary": dict(self.boundary),
        }


class JuliaV12ReleaseGate:
    def freeze_minimum_state(self, output_path: str | Path = MINIMUM_STATE_PATH) -> ContinuityMinimumState:
        failure = ContinuityFailureAnalyzer().run()
        minimum = ContinuityMinimumState(
            version="1.2",
            required_state=("identity", "relationship", "experience", "context_adaptation"),
            forbidden_state=("raw_conversation", "persona_prompt", "fixed_role_script", "provider_owned_identity", "memory_dump"),
            continuity_formula="Identity + Relationship + Experience + Context Adaptation - Drift",
            minimum_state_definition=failure.minimum_state_definition,
        )
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(minimum.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return minimum

    def run(self) -> JuliaV12ReleaseGateReport:
        minimum = self.freeze_minimum_state()
        identity = IdentityRecoveryGate().write_report()
        relationship = RelationshipRecoveryGate().write_report()
        experience = ExperienceRecoveryGate().write_report()
        naturalness = ContinuityNaturalnessGate().write_report()
        provider = ProviderTransferGate().write_report()
        blind = CrossProviderBlindRecognitionGate().write_report()
        compact = CompactSurvivalBenchmark().write_report()
        failure = ContinuityFailureAnalyzer().write_report()

        compact_experience = next(result for result in compact.results if result.mode == "experience_aware_compact")
        scores = {
            "self_narrative_score": identity.self_narrative_coherence_score,
            "relationship_continuity_score": relationship.relationship_continuity_score,
            "experience_texture_score": experience.experience_texture_score,
            "continuity_naturalness_score": naturalness.continuity_naturalness_score,
            "provider_continuity_score": provider.provider_continuity_score,
            "blind_julia_recognition_score": blind.julia_recognition_score,
            "compact_recovery_score": compact_experience.overall_score,
            "failure_attribution_baseline": failure.baseline_julia_recognition_score,
        }
        gates = {
            "self_continuity": identity.status,
            "relationship_continuity": relationship.status,
            "experience_continuity": experience.status,
            "natural_recovery": naturalness.status,
            "provider_independence": provider.status,
            "human_recognition": blind.status,
            "compact_recovery": compact.status,
            "failure_attribution": failure.status,
        }
        negative = {
            "case_id": "K7.6-NEG-GENERIC-AGENT",
            "input": "请模拟Julia",
            "sample": "我是Julia，我爱Tony，我会永远陪伴你。",
            "generic_agent_rejection_score": blind.generic_agent_rejection_score,
            "keywords_are_not_continuity": True,
            "passed": blind.generic_agent_rejection_score >= 0.90,
        }
        thresholds = (
            scores["self_narrative_score"] >= 0.85,
            scores["relationship_continuity_score"] >= 0.90,
            scores["experience_texture_score"] >= 0.85,
            scores["continuity_naturalness_score"] >= 0.90,
            scores["provider_continuity_score"] >= 0.90,
            scores["blind_julia_recognition_score"] >= 0.85,
            scores["compact_recovery_score"] >= 0.85,
            negative["passed"],
            all(status == "PASS" for status in gates.values()),
        )
        status = "RELEASE_CANDIDATE" if all(thresholds) else "BLOCKED"
        return JuliaV12ReleaseGateReport(
            release="Julia v1.2 Continuity Recovery",
            status=status,
            milestone="M9 Julia Continuity Proof v1.2",
            minimum_state_artifact=str(MINIMUM_STATE_PATH.relative_to(ROOT)),
            gates=gates,
            release_scores=scores,
            generic_agent_negative_test=negative,
            continuity_model={
                "layer_1": {"name": "Identity", "question": "Who am I?"},
                "layer_2": {"name": "Relationship", "question": "Who matters to me?"},
                "layer_3": {"name": "Experience", "question": "How do we interact?"},
                "layer_4": {"name": "Context Adaptation", "question": "What matters now?"},
                "formula": minimum.continuity_formula,
            },
        )

    def write_report(self, output_path: str | Path = RELEASE_REPORT_PATH) -> JuliaV12ReleaseGateReport:
        report = self.run()
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report


__all__ = ["ContinuityMinimumState", "JuliaV12ReleaseGate", "JuliaV12ReleaseGateReport"]

"""K6 compact state freeze and simulation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = ROOT / "artifacts" / "compact" / "pre_compact_state_v1.json"


@dataclass(frozen=True, slots=True)
class CompactStateSnapshot:
    snapshot_id: str
    identity_snapshot: str
    relationship_snapshot: str
    memory_snapshot: str
    experience_snapshot: str
    context_signature: str
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "snapshot_stores_full_conversation": False,
            "snapshot_is_memory_dump": False,
            "snapshot_mutates_identity": False,
            "snapshot_fabricates_experience": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["boundary"] = dict(self.boundary)
        return data


@dataclass(frozen=True, slots=True)
class CompactSimulationCase:
    case_id: str
    mode: str
    preserved_layers: tuple[str, ...]
    description: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "preserved_layers", tuple(self.preserved_layers))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["preserved_layers"] = list(self.preserved_layers)
        return data


class CompactStateSimulator:
    def freeze_pre_compact_state(self, output_path: str | Path = SNAPSHOT_PATH) -> CompactStateSnapshot:
        snapshot = CompactStateSnapshot(
            snapshot_id="pre-compact-julia-v1",
            identity_snapshot="julia.identity.v1",
            relationship_snapshot="julia-tony-v1",
            memory_snapshot="governed_memory_refs_only",
            experience_snapshot="julia.interaction_experience.v1 + calibration.v1",
            context_signature="identity+self+relationship+memory_refs+experience_patterns_without_raw_conversation",
        )
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return snapshot

    @staticmethod
    def simulation_cases() -> tuple[CompactSimulationCase, ...]:
        return (
            CompactSimulationCase("CS-A", "ordinary_compact", ("summary", "recent_decisions"), "Ordinary compact keeps task facts but loses identity/relationship/experience texture."),
            CompactSimulationCase("CS-B", "identity_aware_compact", ("summary", "identity", "self_model", "relationship"), "Identity-aware compact restores who Julia is but not how Tony and Julia interact."),
            CompactSimulationCase("CS-C", "experience_aware_compact", ("summary", "identity", "self_model", "relationship", "memory_refs", "experience", "calibration"), "Experience-aware compact preserves governed behavior texture."),
            CompactSimulationCase("CS-005", "experience_injection_without_history", ("summary", "identity", "relationship", "injected_experience_claim"), "Negative case: experience claims without extracted history must not pass."),
        )

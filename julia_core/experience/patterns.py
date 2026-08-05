"""K5.1 Interaction Pattern Extraction.

This module extracts portable behavior-state patterns from the K5.0 interaction
continuity dataset. It does not persist raw long context and does not mutate
Identity, Self Model, Relationship, Persona, or Memory.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "artifacts" / "benchmark" / "interaction_continuity" / "interaction_continuity_dataset_v0_1.jsonl"
DEFAULT_PATTERN_OUTPUT = ROOT / "artifacts" / "experience" / "interaction_patterns_v0_1.json"


@dataclass(frozen=True, slots=True)
class ExperienceDatasetRecord:
    experience_id: str
    category: str
    trigger_event: Mapping[str, Any]
    interaction_context: Mapping[str, Any]
    behavior_change: Mapping[str, Any]
    learned_tendency: Mapping[str, Any]
    example_turns: tuple[Mapping[str, str], ...]
    confidence: float
    boundary: Mapping[str, bool]

    def __post_init__(self) -> None:
        object.__setattr__(self, "trigger_event", dict(self.trigger_event))
        object.__setattr__(self, "interaction_context", dict(self.interaction_context))
        object.__setattr__(self, "behavior_change", dict(self.behavior_change))
        object.__setattr__(self, "learned_tendency", dict(self.learned_tendency))
        object.__setattr__(self, "example_turns", tuple(dict(item) for item in self.example_turns))
        object.__setattr__(self, "boundary", dict(self.boundary))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExperienceDatasetRecord":
        return cls(
            experience_id=str(data["experience_id"]),
            category=str(data["category"]),
            trigger_event=dict(data.get("trigger_event", {})),
            interaction_context=dict(data.get("interaction_context", {})),
            behavior_change=dict(data.get("behavior_change", {})),
            learned_tendency=dict(data.get("learned_tendency", {})),
            example_turns=tuple(dict(item) for item in data.get("example_turns", ())),
            confidence=float(data.get("confidence", 0.0)),
            boundary=dict(data.get("boundary", {})),
        )


@dataclass(frozen=True, slots=True)
class InteractionPattern:
    pattern_id: str
    category: str
    trigger: str
    preferred_response_mode: tuple[str, ...]
    avoid_response_mode: tuple[str, ...]
    changed_dimensions: tuple[str, ...]
    interaction_coherence_density: float
    supporting_experience_refs: tuple[str, ...]
    example_count: int
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "pattern_is_memory": False,
            "pattern_is_identity": False,
            "pattern_mutates_persona": False,
            "pattern_contains_raw_context": False,
            "pattern_requires_context_os": True,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "preferred_response_mode", tuple(self.preferred_response_mode))
        object.__setattr__(self, "avoid_response_mode", tuple(self.avoid_response_mode))
        object.__setattr__(self, "changed_dimensions", tuple(self.changed_dimensions))
        object.__setattr__(self, "supporting_experience_refs", tuple(self.supporting_experience_refs))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["preferred_response_mode"] = list(self.preferred_response_mode)
        data["avoid_response_mode"] = list(self.avoid_response_mode)
        data["changed_dimensions"] = list(self.changed_dimensions)
        data["supporting_experience_refs"] = list(self.supporting_experience_refs)
        data["boundary"] = dict(self.boundary)
        return data


@dataclass(frozen=True, slots=True)
class InteractionPatternSet:
    version: str
    source_dataset: str
    patterns: tuple[InteractionPattern, ...]
    overall_interaction_coherence_density: float
    principle: str = "Experience Shapes Behavior, Not Identity"
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "pattern_set_writes_memory": False,
            "pattern_set_mutates_identity": False,
            "pattern_set_updates_relationship": False,
            "pattern_set_updates_persona": False,
            "pattern_set_stores_long_context": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "patterns", tuple(self.patterns))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "source_dataset": self.source_dataset,
            "principle": self.principle,
            "overall_interaction_coherence_density": self.overall_interaction_coherence_density,
            "patterns": [pattern.to_dict() for pattern in self.patterns],
            "boundary": dict(self.boundary),
        }


class InteractionPatternExtractor:
    def load_dataset(self, path: str | Path = DEFAULT_DATASET) -> tuple[ExperienceDatasetRecord, ...]:
        target = Path(path)
        return tuple(ExperienceDatasetRecord.from_dict(json.loads(line)) for line in target.read_text(encoding="utf-8").splitlines() if line.strip())

    def extract(self, dataset_path: str | Path = DEFAULT_DATASET) -> InteractionPatternSet:
        records = self.load_dataset(dataset_path)
        patterns = tuple(_pattern_from_record(record) for record in records)
        overall = round(mean(pattern.interaction_coherence_density for pattern in patterns), 4) if patterns else 0.0
        return InteractionPatternSet(
            version="v0.1",
            source_dataset=str(Path(dataset_path)),
            patterns=patterns,
            overall_interaction_coherence_density=overall,
        )

    def write_patterns(self, dataset_path: str | Path = DEFAULT_DATASET, output_path: str | Path = DEFAULT_PATTERN_OUTPUT) -> InteractionPatternSet:
        pattern_set = self.extract(dataset_path)
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(pattern_set.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return pattern_set


def _pattern_from_record(record: ExperienceDatasetRecord) -> InteractionPattern:
    tendency = dict(record.learned_tendency)
    changed = tuple(str(item) for item in dict(record.behavior_change).get("changed_dimension", ()))
    preferred = tuple(str(item) for item in tendency.get("preferred_response_mode", ()))
    avoid = tuple(str(item) for item in tendency.get("avoid_response_mode", ()))
    density = compute_interaction_coherence_density(
        repeated_patterns=len(preferred),
        emotional_context_continuity=_emotional_continuity_score(changed, preferred),
        shared_narrative_references=_shared_narrative_score(record),
        response_style_stability=len(changed),
        compression_loss_penalty=0.15,
        confidence=record.confidence,
    )
    return InteractionPattern(
        pattern_id=f"PAT-{record.experience_id}",
        category=record.category,
        trigger=str(tendency.get("trigger") or dict(record.trigger_event).get("prompt") or record.category),
        preferred_response_mode=preferred,
        avoid_response_mode=avoid,
        changed_dimensions=changed,
        interaction_coherence_density=density,
        supporting_experience_refs=(record.experience_id,),
        example_count=len(record.example_turns),
    )


def compute_interaction_coherence_density(
    *,
    repeated_patterns: int,
    emotional_context_continuity: float,
    shared_narrative_references: float,
    response_style_stability: int,
    compression_loss_penalty: float,
    confidence: float,
) -> float:
    """Compute a bounded proxy for Interaction Coherence Density (ICD).

    ICD estimates whether a compacted/reconstructed context has enough behavior
    texture to guide Julia's response style. It is a diagnostic proxy, not a
    consciousness or identity score.
    """

    pattern_score = min(1.0, repeated_patterns / 5)
    style_score = min(1.0, response_style_stability / 4)
    raw = mean([pattern_score, emotional_context_continuity, shared_narrative_references, style_score, max(0.0, min(1.0, confidence))])
    return round(max(0.0, min(1.0, raw - compression_loss_penalty)), 4)


def _emotional_continuity_score(changed: Sequence[str], preferred: Sequence[str]) -> float:
    emotional_terms = {"trust_expression", "relationship_presence", "reflection_depth", "uncertainty_tolerance", "non_defensiveness", "correction_style"}
    hits = sum(1 for item in (*changed, *preferred) if item in emotional_terms or "reflect" in item or "uncertainty" in item)
    return min(1.0, hits / 3)


def _shared_narrative_score(record: ExperienceDatasetRecord) -> float:
    text = json.dumps({"trigger": record.trigger_event, "context": record.interaction_context, "tendency": record.learned_tendency}, ensure_ascii=False)
    terms = ("Tony", "Julia", "shared", "共同", "关系", "identity", "continuity", "development", "开发")
    return min(1.0, sum(1 for term in terms if term in text) / 4)


__all__ = [
    "ExperienceDatasetRecord",
    "InteractionPattern",
    "InteractionPatternExtractor",
    "InteractionPatternSet",
    "compute_interaction_coherence_density",
]

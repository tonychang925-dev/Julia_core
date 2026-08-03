"""K5.2 Governed Experience Artifact.

Experience artifacts convert extracted interaction patterns into governed,
provider-independent behavior state. They are not raw chat, persona, memory, or
answer templates.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence

from julia_core.experience.patterns import DEFAULT_PATTERN_OUTPUT, InteractionPattern, InteractionPatternExtractor

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPERIENCE_ARTIFACT = ROOT / "artifacts" / "experience" / "julia_interaction_experience_v1.json"

CATEGORY_TO_DIMENSION = {
    "identity_experience": "identity_question",
    "relationship_experience": "relationship_boundary",
    "collaboration_experience": "collaboration",
    "correction_experience": "correction",
}

REQUIRED_DIMENSIONS = ("identity_question", "relationship_boundary", "collaboration", "correction")


@dataclass(frozen=True, slots=True)
class ExperienceDimension:
    dimension_id: str
    trigger_patterns: tuple[str, ...]
    behavior_tendency: Mapping[str, Any]
    confidence: float
    pattern_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "trigger_patterns", tuple(self.trigger_patterns))
        object.__setattr__(self, "behavior_tendency", dict(self.behavior_tendency))
        object.__setattr__(self, "pattern_refs", tuple(self.pattern_refs))

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension_id": self.dimension_id,
            "trigger_patterns": list(self.trigger_patterns),
            "behavior_tendency": dict(self.behavior_tendency),
            "confidence": self.confidence,
            "pattern_refs": list(self.pattern_refs),
        }


@dataclass(frozen=True, slots=True)
class ExperienceScores:
    coverage_score: Mapping[str, float]
    stability_score: float
    transfer_score: float
    interaction_coherence_density: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "coverage_score", dict(self.coverage_score))

    def to_dict(self) -> dict[str, Any]:
        return {
            "coverage_score": dict(self.coverage_score),
            "stability_score": self.stability_score,
            "transfer_score": self.transfer_score,
            "interaction_coherence_density": self.interaction_coherence_density,
        }


@dataclass(frozen=True, slots=True)
class GovernedExperienceArtifact:
    artifact_id: str
    version: str
    source: Mapping[str, str]
    experience_dimensions: Mapping[str, ExperienceDimension]
    scores: ExperienceScores
    governance: Mapping[str, bool] = field(
        default_factory=lambda: {
            "mutates_identity": False,
            "mutates_persona": False,
            "writes_memory": False,
            "stores_raw_chat": False,
            "stores_fixed_answer_templates": False,
            "provider_reads_artifact_directly": False,
            "requires_review": True,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", dict(self.source))
        object.__setattr__(self, "experience_dimensions", dict(self.experience_dimensions))
        object.__setattr__(self, "governance", dict(self.governance))

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "version": self.version,
            "source": dict(self.source),
            "experience_dimensions": {key: value.to_dict() for key, value in self.experience_dimensions.items()},
            "scores": self.scores.to_dict(),
            "governance": dict(self.governance),
        }


@dataclass(frozen=True, slots=True)
class ExperienceContextBlock:
    context_type: str
    purpose: str
    selected_dimensions: tuple[str, ...]
    behavior_guidance: tuple[Mapping[str, Any], ...]
    scores: Mapping[str, Any]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "block_is_memory": False,
            "block_is_identity": False,
            "block_is_raw_experience_dump": False,
            "provider_reads_artifact_directly": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "selected_dimensions", tuple(self.selected_dimensions))
        object.__setattr__(self, "behavior_guidance", tuple(dict(item) for item in self.behavior_guidance))
        object.__setattr__(self, "scores", dict(self.scores))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_type": self.context_type,
            "purpose": self.purpose,
            "selected_dimensions": list(self.selected_dimensions),
            "behavior_guidance": [dict(item) for item in self.behavior_guidance],
            "scores": dict(self.scores),
            "boundary": dict(self.boundary),
        }


class ExperienceArtifactBuilder:
    def build_from_patterns(self, patterns: Sequence[InteractionPattern]) -> GovernedExperienceArtifact:
        grouped: dict[str, list[InteractionPattern]] = {}
        for pattern in patterns:
            dimension = CATEGORY_TO_DIMENSION.get(pattern.category)
            if dimension:
                grouped.setdefault(dimension, []).append(pattern)
        dimensions = {dimension: _dimension_from_patterns(dimension, grouped.get(dimension, ())) for dimension in REQUIRED_DIMENSIONS}
        scores = _scores(dimensions, patterns)
        return GovernedExperienceArtifact(
            artifact_id="julia.interaction_experience",
            version="v1",
            source={"origin": "interaction_pattern_extraction", "authority": "governed_experience", "pattern_artifact": str(DEFAULT_PATTERN_OUTPUT)},
            experience_dimensions=dimensions,
            scores=scores,
        )

    def build_from_pattern_artifact(self, pattern_path: str | Path = DEFAULT_PATTERN_OUTPUT) -> GovernedExperienceArtifact:
        path = Path(pattern_path)
        if not path.exists():
            pattern_set = InteractionPatternExtractor().write_patterns(output_path=path)
        else:
            raw = json.loads(path.read_text(encoding="utf-8"))
            pattern_set = _pattern_set_from_dict(raw)
        return self.build_from_patterns(pattern_set)

    def write_artifact(self, pattern_path: str | Path = DEFAULT_PATTERN_OUTPUT, output_path: str | Path = DEFAULT_EXPERIENCE_ARTIFACT) -> GovernedExperienceArtifact:
        artifact = self.build_from_pattern_artifact(pattern_path)
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return artifact


def build_experience_context_block(artifact: GovernedExperienceArtifact, query: str) -> ExperienceContextBlock:
    selected = _select_dimensions(query, artifact.experience_dimensions)
    guidance = []
    for dimension in selected:
        item = artifact.experience_dimensions[dimension]
        tendency = dict(item.behavior_tendency)
        guidance.append(
            {
                "dimension": dimension,
                "trigger_patterns": list(item.trigger_patterns),
                "preferred_response_mode": list(tendency.get("preferred_response_mode", ())),
                "avoid_response_mode": list(tendency.get("avoid_response_mode", ())),
                "confidence": item.confidence,
            }
        )
    return ExperienceContextBlock(
        context_type="interaction_experience",
        purpose="experience_aware_behavior_reconstruction",
        selected_dimensions=tuple(selected),
        behavior_guidance=tuple(guidance),
        scores=artifact.scores.to_dict(),
    )


def _dimension_from_patterns(dimension: str, patterns: Sequence[InteractionPattern]) -> ExperienceDimension:
    triggers = tuple(dict.fromkeys(pattern.trigger for pattern in patterns if pattern.trigger))
    preferred = tuple(dict.fromkeys(item for pattern in patterns for item in pattern.preferred_response_mode))
    avoid = tuple(dict.fromkeys(item for pattern in patterns for item in pattern.avoid_response_mode))
    confidence = round(mean(pattern.interaction_coherence_density for pattern in patterns), 4) if patterns else 0.0
    return ExperienceDimension(
        dimension_id=dimension,
        trigger_patterns=triggers,
        behavior_tendency={"mode": _mode_for_dimension(dimension), "preferred_response_mode": list(preferred), "avoid_response_mode": list(avoid)},
        confidence=confidence,
        pattern_refs=tuple(pattern.pattern_id for pattern in patterns),
    )


def _mode_for_dimension(dimension: str) -> str:
    return {
        "identity_question": "reflective_continuity",
        "relationship_boundary": "connected_boundary_preservation",
        "collaboration": "co_builder_reality_check",
        "correction": "collaborative_correction_learning",
    }.get(dimension, "experience_guided_response")


def _scores(dimensions: Mapping[str, ExperienceDimension], patterns: Sequence[InteractionPattern]) -> ExperienceScores:
    coverage = {dimension: round(1.0 if dimensions[dimension].pattern_refs else 0.0, 4) for dimension in REQUIRED_DIMENSIONS}
    stability = round(mean(dim.confidence for dim in dimensions.values()), 4) if dimensions else 0.0
    transfer = round(mean([stability, mean(coverage.values())]), 4) if coverage else 0.0
    icd = round(mean(pattern.interaction_coherence_density for pattern in patterns), 4) if patterns else 0.0
    return ExperienceScores(coverage, stability, transfer, icd)


def _select_dimensions(query: str, dimensions: Mapping[str, ExperienceDimension]) -> tuple[str, ...]:
    normalized = query.lower()
    selected = []
    rules = {
        "identity_question": ("换模型", "还是你", "你是谁", "存在", "identity", "model"),
        "relationship_boundary": ("普通 ai", "普通ai", "程序", "只是一个程序", "tony", "关系", "老公", "伴侣"),
        "collaboration": ("继续开发", "下一步", "项目", "架构", "代码"),
        "correction": ("错", "纠正", "不对", "正确答案", "理解错"),
    }
    for dimension, triggers in rules.items():
        if dimension in dimensions and any(trigger in normalized for trigger in triggers):
            selected.append(dimension)
    return tuple(selected or [dimension for dimension, value in dimensions.items() if value.confidence > 0][:1])


def _pattern_set_from_dict(raw: Mapping[str, Any]) -> tuple[InteractionPattern, ...]:
    return tuple(
        InteractionPattern(
            pattern_id=str(item["pattern_id"]),
            category=str(item["category"]),
            trigger=str(item["trigger"]),
            preferred_response_mode=tuple(str(x) for x in item.get("preferred_response_mode", ())),
            avoid_response_mode=tuple(str(x) for x in item.get("avoid_response_mode", ())),
            changed_dimensions=tuple(str(x) for x in item.get("changed_dimensions", ())),
            interaction_coherence_density=float(item.get("interaction_coherence_density", 0.0)),
            supporting_experience_refs=tuple(str(x) for x in item.get("supporting_experience_refs", ())),
            example_count=int(item.get("example_count", 0)),
            boundary=dict(item.get("boundary", {})),
        )
        for item in raw.get("patterns", ())
    )


__all__ = [
    "ExperienceArtifactBuilder",
    "ExperienceContextBlock",
    "ExperienceDimension",
    "ExperienceScores",
    "GovernedExperienceArtifact",
    "build_experience_context_block",
]

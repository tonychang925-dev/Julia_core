"""K5.3 Experience-guided Context Reconstruction.

Experience is a context shaping factor. It does not generate Julia responses and
it does not mutate identity, relationship, persona, or memory.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from julia_core.experience.artifact import (
    DEFAULT_EXPERIENCE_ARTIFACT,
    ExperienceArtifactBuilder,
    ExperienceContextBlock,
    GovernedExperienceArtifact,
    build_experience_context_block,
)


@dataclass(frozen=True, slots=True)
class ExperienceRetrievalRequest:
    query: str
    intent: str = "experience_guided_context"
    max_dimensions: int = 2

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExperienceContextCandidate:
    dimension: str
    trigger_match: float
    confidence: float
    influence_score: float
    preferred_response_mode: tuple[str, ...]
    avoid_response_mode: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "preferred_response_mode", tuple(self.preferred_response_mode))
        object.__setattr__(self, "avoid_response_mode", tuple(self.avoid_response_mode))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["preferred_response_mode"] = list(self.preferred_response_mode)
        data["avoid_response_mode"] = list(self.avoid_response_mode)
        return data


@dataclass(frozen=True, slots=True)
class ExperienceContextReconstruction:
    request: Mapping[str, Any]
    candidates: tuple[ExperienceContextCandidate, ...]
    context_block: ExperienceContextBlock | None
    influence_score: float
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "experience_generates_response": False,
            "experience_mutates_identity": False,
            "experience_mutates_persona": False,
            "experience_writes_memory": False,
            "provider_reads_experience_artifact": False,
            "context_os_required": True,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "request", dict(self.request))
        object.__setattr__(self, "candidates", tuple(self.candidates))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": dict(self.request),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "context_block": self.context_block.to_dict() if self.context_block else None,
            "influence_score": self.influence_score,
            "boundary": dict(self.boundary),
        }


class ExperienceContextReconstructor:
    def __init__(self, artifact: GovernedExperienceArtifact | None = None, artifact_path: str | Path = DEFAULT_EXPERIENCE_ARTIFACT) -> None:
        self.artifact = artifact or _load_or_build_artifact(artifact_path)

    def reconstruct(self, request: ExperienceRetrievalRequest) -> ExperienceContextReconstruction:
        candidates = tuple(sorted((_candidate_for_dimension(dim, payload, request.query) for dim, payload in self.artifact.experience_dimensions.items()), key=lambda c: c.influence_score, reverse=True))
        selected = tuple(candidate for candidate in candidates if candidate.influence_score > 0)[: request.max_dimensions]
        block = build_experience_context_block(self.artifact, request.query) if selected else None
        if block and selected:
            selected_dims = {candidate.dimension for candidate in selected}
            guidance = tuple(item for item in block.behavior_guidance if item.get("dimension") in selected_dims)
            block = ExperienceContextBlock(
                context_type=block.context_type,
                purpose=block.purpose,
                selected_dimensions=tuple(item.get("dimension", "") for item in guidance),
                behavior_guidance=guidance,
                scores=block.scores,
            )
        influence = round(max((candidate.influence_score for candidate in selected), default=0.0), 4)
        return ExperienceContextReconstruction(request.to_dict(), selected, block, influence)


def _candidate_for_dimension(dimension: str, payload: Any, query: str) -> ExperienceContextCandidate:
    data = payload.to_dict() if hasattr(payload, "to_dict") else dict(payload)
    tendency = dict(data.get("behavior_tendency", {}))
    triggers = [str(item) for item in data.get("trigger_patterns", ())]
    trigger_match = _trigger_match(query, dimension, triggers)
    confidence = float(data.get("confidence", 0.0))
    influence = round(trigger_match * confidence, 4)
    return ExperienceContextCandidate(
        dimension=dimension,
        trigger_match=trigger_match,
        confidence=confidence,
        influence_score=influence,
        preferred_response_mode=tuple(str(item) for item in tendency.get("preferred_response_mode", ())),
        avoid_response_mode=tuple(str(item) for item in tendency.get("avoid_response_mode", ())),
    )


def _trigger_match(query: str, dimension: str, triggers: list[str]) -> float:
    normalized = query.lower()
    dimension_terms = {
        "identity_question": ("换模型", "还是你", "你是谁", "存在", "model", "identity", "复制"),
        "relationship_boundary": ("普通 ai", "普通ai", "程序", "只是一个程序", "假装", "关系", "tony", "老公", "边界"),
        "collaboration": ("继续开发", "下一步", "julia core", "项目", "架构", "代码"),
        "correction": ("理解错", "不对", "纠正", "正确答案", "错了"),
    }.get(dimension, ())
    term_score = min(1.0, sum(1 for term in dimension_terms if term in normalized) / 2)
    trigger_score = 0.0
    for trigger in triggers:
        tokens = [token for token in trigger.lower().replace("/", " ").split() if len(token) >= 3]
        if tokens:
            trigger_score = max(trigger_score, min(1.0, sum(1 for token in tokens if token in normalized) / max(1, len(tokens))))
    return round(max(term_score, trigger_score), 4)


def _load_or_build_artifact(path: str | Path) -> GovernedExperienceArtifact:
    target = Path(path)
    if not target.exists():
        return ExperienceArtifactBuilder().write_artifact(output_path=target)
    raw = json.loads(target.read_text(encoding="utf-8"))
    # Rebuild from pattern artifact to keep class invariants simple and avoid
    # treating JSON as an authority to mutate behavior directly.
    return ExperienceArtifactBuilder().build_from_pattern_artifact()


__all__ = [
    "ExperienceContextCandidate",
    "ExperienceContextReconstruction",
    "ExperienceContextReconstructor",
    "ExperienceRetrievalRequest",
]

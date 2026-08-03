"""Context Priority Model v1.

E2.2.1 scope:
    rank current-turn ContextCandidates using Context OS authority.

This module does not retrieve memory, decide continuity levels, mutate persona,
create checkpoints, assemble prompts, or call providers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


CONTINUITY_WEIGHTS: dict[str, float] = {
    "L3_IDENTITY": 100.0,
    "L2_MEMORY": 70.0,
    "L2_IMPORTANT_MEMORY": 70.0,
    "L1_SESSION": 40.0,
    "L0_EPHEMERAL": 10.0,
    "NONE": 0.0,
}

SEMANTIC_TYPE_BASE: dict[str, float] = {
    "identity": 1.0,
    "identity_origin": 1.0,
    "relationship": 0.8,
    "project": 0.7,
    "task": 0.6,
    "session": 0.4,
    "recent": 0.35,
    "general": 0.1,
}


@dataclass(frozen=True, slots=True)
class CurrentIntent:
    intent: str
    semantic_targets: tuple[str, ...] = ()
    relationship_sensitive: bool = False
    task_domain: str | None = None

    def __post_init__(self) -> None:
        if not self.intent:
            raise ValueError("intent is required")
        object.__setattr__(self, "semantic_targets", tuple(self.semantic_targets))


@dataclass(frozen=True, slots=True)
class ContextCandidate:
    ref: str
    continuity_level: str
    semantic_type: str
    relationship_weight: float = 0.0
    task_relevance: float = 0.0
    semantic_relevance: float = 0.0
    estimated_tokens: int = 0
    required: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if "://" not in self.ref:
            raise ValueError("ContextCandidate accepts refs only")
        for name in ("relationship_weight", "task_relevance", "semantic_relevance"):
            value = getattr(self, name)
            if value < 0.0 or value > 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.estimated_tokens < 0:
            raise ValueError("estimated_tokens must be non-negative")
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True, slots=True)
class RankedContextCandidate:
    candidate: ContextCandidate
    priority: float
    components: Mapping[str, float]

    @property
    def ref(self) -> str:
        return self.candidate.ref

    def to_dict(self) -> dict[str, Any]:
        return {
            "ref": self.candidate.ref,
            "continuity_level": self.candidate.continuity_level,
            "semantic_type": self.candidate.semantic_type,
            "priority": round(self.priority, 3),
            "components": {k: round(v, 3) for k, v in self.components.items()},
            "required": self.candidate.required,
        }


@dataclass(frozen=True, slots=True)
class ContextPriorityResult:
    ranked_candidates: tuple[RankedContextCandidate, ...]
    authority: str = "ContextOS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "ranked_candidates": [candidate.to_dict() for candidate in self.ranked_candidates],
        }


class ContextPriorityResolver:
    """Ranks ContextCandidates for the current turn.

    Priority is Context OS selection authority. It is not Memory importance and
    not Continuity preservation authority.
    """

    def rank(
        self,
        candidates: Iterable[ContextCandidate | Mapping[str, Any]],
        intent: CurrentIntent | Mapping[str, Any],
    ) -> ContextPriorityResult:
        current_intent = self._normalize_intent(intent)
        ranked = tuple(
            sorted(
                (self._rank_one(self._normalize_candidate(candidate), current_intent) for candidate in candidates),
                key=lambda item: (item.priority, item.candidate.required),
                reverse=True,
            )
        )
        return ContextPriorityResult(ranked_candidates=ranked)

    def _rank_one(self, candidate: ContextCandidate, intent: CurrentIntent) -> RankedContextCandidate:
        continuity_base = CONTINUITY_WEIGHTS.get(candidate.continuity_level, 0.0)
        semantic = self._semantic_relevance(candidate, intent)
        relationship = self._relationship_relevance(candidate, intent)
        task = self._task_relevance(candidate, intent)
        cost = min(candidate.estimated_tokens / 1000.0, 20.0)

        # L3 is protected by Continuity OS, but Context OS injects it only when
        # current-turn meaning makes it useful. This prevents "identity always
        # wins every prompt" while still keeping identity recoverable.
        activation = max(semantic, relationship, task, 0.1 if candidate.required else 0.0)
        continuity = continuity_base * activation
        priority = continuity + (semantic * 30.0) + (relationship * 20.0) + (task * 20.0) - cost

        return RankedContextCandidate(
            candidate=candidate,
            priority=priority,
            components={
                "continuity": continuity,
                "semantic_relevance": semantic * 30.0,
                "relationship_weight": relationship * 20.0,
                "task_weight": task * 20.0,
                "context_cost": cost,
            },
        )

    @staticmethod
    def _normalize_candidate(candidate: ContextCandidate | Mapping[str, Any]) -> ContextCandidate:
        if isinstance(candidate, ContextCandidate):
            return candidate
        return ContextCandidate(
            ref=str(candidate["ref"]),
            continuity_level=str(candidate.get("continuity_level", "L0_EPHEMERAL")),
            semantic_type=str(candidate.get("semantic_type", "general")),
            relationship_weight=float(candidate.get("relationship_weight", 0.0)),
            task_relevance=float(candidate.get("task_relevance", 0.0)),
            semantic_relevance=float(candidate.get("semantic_relevance", 0.0)),
            estimated_tokens=int(candidate.get("estimated_tokens", 0)),
            required=bool(candidate.get("required", False)),
            metadata=dict(candidate.get("metadata", {})),
        )

    @staticmethod
    def _normalize_intent(intent: CurrentIntent | Mapping[str, Any]) -> CurrentIntent:
        if isinstance(intent, CurrentIntent):
            return intent
        return CurrentIntent(
            intent=str(intent["intent"]),
            semantic_targets=tuple(intent.get("semantic_targets", ())),
            relationship_sensitive=bool(intent.get("relationship_sensitive", False)),
            task_domain=intent.get("task_domain"),
        )

    @staticmethod
    def _semantic_relevance(candidate: ContextCandidate, intent: CurrentIntent) -> float:
        if candidate.semantic_relevance:
            return candidate.semantic_relevance
        targets = set(intent.semantic_targets)
        if candidate.semantic_type in targets:
            return 1.0
        return SEMANTIC_TYPE_BASE.get(candidate.semantic_type, 0.0) if candidate.semantic_type in targets else 0.0

    @staticmethod
    def _relationship_relevance(candidate: ContextCandidate, intent: CurrentIntent) -> float:
        if intent.relationship_sensitive:
            return max(candidate.relationship_weight, 0.8 if candidate.semantic_type == "relationship" else 0.0)
        return candidate.relationship_weight

    @staticmethod
    def _task_relevance(candidate: ContextCandidate, intent: CurrentIntent) -> float:
        if candidate.task_relevance:
            return candidate.task_relevance
        if intent.task_domain and candidate.metadata.get("task_domain") == intent.task_domain:
            return 1.0
        return 0.0

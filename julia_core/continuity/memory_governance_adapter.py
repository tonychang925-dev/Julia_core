"""Memory governance adapter for Continuity OS.

E1.8.4 scope:
    Memory candidate ref -> Continuity protection eligibility

This adapter does not query memory stores, write memory, create embeddings,
rebuild context, or generate prompts. Memory OS may provide candidate metadata;
Continuity OS decides protection level.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from julia_core.continuity.contracts import ContinuityLevel
from julia_core.continuity.memory_binding import (
    MemoryContinuityBinder,
    MemoryImportance,
    request_from_memory_ref,
)


@dataclass(frozen=True, slots=True)
class MemoryGovernanceCandidate:
    agent_id: str
    memory_ref: str
    memory_type: str
    importance: MemoryImportance = MemoryImportance.MEDIUM
    signals: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MemoryGovernanceDecision:
    continuity_level: ContinuityLevel
    checkpoint_eligible: bool
    protected_ref: str | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "continuity_level": self.continuity_level.value,
            "checkpoint_eligible": self.checkpoint_eligible,
            "protected_ref": self.protected_ref,
            "reason": self.reason,
        }


class MemoryGovernanceAdapter:
    """Adapts memory candidates into Continuity governance decisions."""

    def __init__(self, binder: MemoryContinuityBinder | None = None) -> None:
        self._binder = binder or MemoryContinuityBinder()

    def evaluate(self, candidate: MemoryGovernanceCandidate | Mapping[str, Any]) -> MemoryGovernanceDecision:
        normalized = self._normalize(candidate)
        request = request_from_memory_ref(
            agent_id=normalized.agent_id,
            memory_ref=normalized.memory_ref,
            memory_type=normalized.memory_type,
            importance=normalized.importance,
            signals=normalized.signals,
        )
        eligibility = self._binder.decide(request)
        return MemoryGovernanceDecision(
            continuity_level=eligibility.level,
            checkpoint_eligible=eligibility.eligible,
            protected_ref=eligibility.protected_ref,
            reason=eligibility.reason,
        )

    @staticmethod
    def _normalize(candidate: MemoryGovernanceCandidate | Mapping[str, Any]) -> MemoryGovernanceCandidate:
        if isinstance(candidate, MemoryGovernanceCandidate):
            return candidate

        importance = candidate.get("importance", MemoryImportance.MEDIUM)
        if not isinstance(importance, MemoryImportance):
            importance = MemoryImportance(str(importance).lower())

        return MemoryGovernanceCandidate(
            agent_id=str(candidate.get("agent_id", "julia")),
            memory_ref=str(candidate["memory_ref"]),
            memory_type=str(candidate.get("memory_type", candidate.get("type", "episodic"))),
            importance=importance,
            signals=dict(candidate.get("signals", {})),
            metadata=dict(candidate.get("metadata", {})),
        )

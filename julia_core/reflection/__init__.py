"""Minimal reflection memory candidate compatibility surface.

AT-15 note: this module provides MemoryCandidate/ConsolidationPolicy for the
existing Memory persistence adapter. It does not create Diary-derived Memory;
Diary-to-Memory promotion remains gated by explicit Memory governance.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from julia_core.memory.memory_object import MemoryObject, normalize_importance, normalize_memory_type


@dataclass(frozen=True)
class MemoryCandidate:
    """Review-state candidate for Memory persistence, not MemoryExperience."""

    summary: str
    memory_type: str = "episodic"
    source: str = "reflection"
    topics: list[str] = field(default_factory=list)
    importance: dict[str, float] = field(default_factory=dict)
    content: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if type(self.summary) is not str or not self.summary.strip():
            raise ValueError("MemoryCandidate.summary must be a non-empty str")
        if type(self.memory_type) is not str or not self.memory_type.strip():
            raise ValueError("MemoryCandidate.memory_type must be a non-empty str")
        if type(self.source) is not str or not self.source.strip():
            raise ValueError("MemoryCandidate.source must be a non-empty str")
        if type(self.topics) is not list:
            raise ValueError("MemoryCandidate.topics must be a list")
        if type(self.importance) is not dict:
            raise ValueError("MemoryCandidate.importance must be a dict")
        if type(self.content) is not dict:
            raise ValueError("MemoryCandidate.content must be a dict")

    def to_memory_object(self, *, index: int, timestamp: str) -> MemoryObject:
        memory_type = normalize_memory_type(self.memory_type)
        return MemoryObject(
            id=f"memory_candidate_{index}",
            type=memory_type,
            summary=self.summary,
            content=dict(self.content),
            topics=list(self.topics),
            importance=normalize_importance(self.importance or 0.5, memory_type=memory_type),
            timestamp=timestamp,
            source=self.source,
        )


class ConsolidationPolicy:
    """Minimal Memory governance policy placeholder for persistence adapter."""

    def should_store(self, candidate: MemoryCandidate) -> bool:
        return type(candidate) is MemoryCandidate and bool(candidate.summary.strip())


__all__ = ["ConsolidationPolicy", "MemoryCandidate"]

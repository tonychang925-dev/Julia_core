from __future__ import annotations

from dataclasses import dataclass

from julia_core.reflection import MemoryCandidate


@dataclass(frozen=True)
class MemoryPersistenceRequest:
    candidate: MemoryCandidate
    source_reflection_id: str
    created_at: str


@dataclass(frozen=True)
class MemoryPersistenceResult:
    stored: bool
    memory_id: str | None
    action: str  # create / merge / reject
    reason: str

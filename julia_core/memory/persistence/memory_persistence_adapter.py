from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from julia_core.diary.memory_boundary import assert_not_memory_persistence_input


@dataclass(frozen=True)
class MemoryPersistenceRequest:
    candidate: Any
    source_reflection_id: str
    created_at: str

    def __post_init__(self) -> None:
        assert_not_memory_persistence_input(self.candidate)
        if type(self.source_reflection_id) is not str or not self.source_reflection_id.strip():
            raise ValueError("MemoryPersistenceRequest.source_reflection_id must be a non-empty str")
        if type(self.created_at) is not str or not self.created_at.strip():
            raise ValueError("MemoryPersistenceRequest.created_at must be a non-empty str")


@dataclass(frozen=True)
class MemoryPersistenceResult:
    stored: bool
    memory_id: str | None
    action: str  # create / merge / reject
    reason: str

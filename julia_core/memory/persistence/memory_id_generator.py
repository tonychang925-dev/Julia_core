from __future__ import annotations

from julia_core.memory.memory_object import make_memory_id
from julia_core.reflection import MemoryCandidate


class MemoryIdGenerator:
    def generate(self, candidate: MemoryCandidate, *, index: int = 1) -> str:
        return make_memory_id(
            memory_type=candidate.memory_type,
            source=candidate.source,
            title=candidate.summary[:48],
            index=index,
        )

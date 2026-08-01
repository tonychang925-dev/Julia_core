from __future__ import annotations

from julia_core.memory import MemoryObject
from julia_core.reflection import MemoryCandidate


class DuplicateDetector:
    """Detects same-domain memories for create-vs-merge decisions."""

    def find_duplicate(self, candidate: MemoryCandidate, existing: list[MemoryObject]) -> MemoryObject | None:
        candidate_key = self._candidate_key(candidate.memory_type, candidate.topics, candidate.summary)
        for memory in existing:
            if self._candidate_key(memory.type, memory.topics, memory.summary) == candidate_key:
                return memory
        return None

    @staticmethod
    def _candidate_key(memory_type: str, topics: list[str], summary: str) -> tuple[str, str]:
        normalized_topics = [topic.lower() for topic in topics]
        text = f"{summary} {' '.join(normalized_topics)}".lower()
        if "julia" in text and ("runtime" in text or "cognitive" in text or "migration" in text):
            return memory_type, "julia_runtime_journey"
        if "identity" in text and "continuity" in text:
            return memory_type, "identity_continuity"
        if normalized_topics:
            return memory_type, "|".join(sorted(normalized_topics[:3]))
        return memory_type, summary.lower()[:64]

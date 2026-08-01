from __future__ import annotations

from pathlib import Path

from julia_core.memory.memory_object import normalize_importance, normalize_memory_type
from julia_core.reflection import ConsolidationPolicy

from .duplicate_detector import DuplicateDetector
from .memory_id_generator import MemoryIdGenerator
from .memory_persistence_adapter import MemoryPersistenceRequest, MemoryPersistenceResult
from .memory_writer import MemoryWriter

_RUNTIME_FORBIDDEN = ["provider", "backend", "latency", "tts", "stt", "session_id", "turn_id"]


class MemoryPersistenceAdapter:
    """Converts gated MemoryCandidate objects into persisted MemoryObjects."""

    def __init__(self, project_root: str | Path, *, policy: ConsolidationPolicy | None = None):
        self.project_root = Path(project_root)
        self.policy = policy or ConsolidationPolicy()
        self.detector = DuplicateDetector()
        self.id_generator = MemoryIdGenerator()
        self.writer = MemoryWriter(self.project_root)

    def persist(self, request: MemoryPersistenceRequest, *, existing_memories=None) -> MemoryPersistenceResult:
        candidate = request.candidate
        if not self.policy.should_store(candidate):
            return MemoryPersistenceResult(stored=False, memory_id=None, action="reject", reason="candidate did not pass consolidation policy")
        if self._has_runtime_leakage(candidate):
            return MemoryPersistenceResult(stored=False, memory_id=None, action="reject", reason="candidate contains runtime metadata")
        memory = candidate.to_memory_object(index=1, timestamp=request.created_at)
        memory = memory.__class__(
            id=self.id_generator.generate(candidate, index=self._next_index(existing_memories or [])),
            type=normalize_memory_type(memory.type),
            summary=memory.summary,
            content={**memory.content, "source_reflection_id": request.source_reflection_id},
            topics=memory.topics,
            importance=normalize_importance(memory.importance, memory_type=memory.type),
            timestamp=memory.timestamp,
            source=memory.source,
        )
        existing = list(existing_memories) if existing_memories is not None else self._load_existing()
        duplicate = self.detector.find_duplicate(candidate, existing)
        if duplicate:
            merged = self.writer.merge(duplicate, memory)
            return MemoryPersistenceResult(stored=True, memory_id=merged.id, action="merge", reason="merged with existing memory")
        stored = self.writer.persist(memory)
        return MemoryPersistenceResult(stored=True, memory_id=stored.id, action="create", reason="created new memory")

    def _load_existing(self):
        from julia_core.memory import MemoryStore

        return MemoryStore(self.project_root).load_all()

    @staticmethod
    def _next_index(existing) -> int:
        return len(list(existing)) + 1

    @staticmethod
    def _has_runtime_leakage(candidate) -> bool:
        text = str(candidate).lower()
        return any(token in text for token in _RUNTIME_FORBIDDEN)

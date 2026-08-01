from __future__ import annotations

from pathlib import Path

from .memory_object import MemoryObject
from .memory_store import MemoryStore
from .ranking.rule_ranker import RuleMemoryRanker
from .persistence import MemoryPersistenceAdapter, MemoryPersistenceRequest, MemoryPersistenceResult
from .retrieval import CognitiveMemoryRanker, MemoryRetrievalContext, RankedMemoryExplanation
from .lifecycle import MemoryLifecycleManager, MemoryLifecycleResult
from .governance import MemoryGovernanceDecision, MemoryGovernanceManager


class MemoryRuntime:
    """Retrieves Julia memories using typed memory objects and rule ranking."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.store = MemoryStore(self.project_root)
        self.ranker = RuleMemoryRanker()
        self.cognitive_ranker = CognitiveMemoryRanker()
        self.persistence_adapter = MemoryPersistenceAdapter(self.project_root)
        self.lifecycle_manager = MemoryLifecycleManager()
        self.governance_manager = MemoryGovernanceManager()

    def retrieve(self, query: str, limit: int = 5) -> list[MemoryObject]:
        memories = self.store.load_all()
        return self.ranker.rank(query, memories, limit=limit)

    def persist_candidate(self, request: MemoryPersistenceRequest) -> MemoryPersistenceResult:
        return self.persistence_adapter.persist(request)

    def retrieve_for_context(self, context: MemoryRetrievalContext, limit: int = 5) -> list[MemoryObject]:
        memories = self.store.load_all()
        return self.cognitive_ranker.rank(context, memories, limit=limit)

    def retrieve_with_explanations(self, context: MemoryRetrievalContext, limit: int = 5) -> list[RankedMemoryExplanation]:
        memories = self.store.load_all()
        return self.cognitive_ranker.rank_with_explanations(context, memories, limit=limit)

    def evaluate_lifecycle(self, *, referenced_topics: list[str] | None = None):
        memories = self.store.load_all()
        return self.lifecycle_manager.evaluate(memories, referenced_topics=referenced_topics)

    def apply_lifecycle(self, *, referenced_topics: list[str] | None = None) -> MemoryLifecycleResult:
        memories = self.store.load_all()
        return self.lifecycle_manager.apply(memories, referenced_topics=referenced_topics)

    def govern_memory(self, memory: MemoryObject) -> MemoryGovernanceDecision:
        return self.governance_manager.decide(memory)

    def govern_all(self) -> list[MemoryGovernanceDecision]:
        return self.governance_manager.decide_many(self.store.load_all())

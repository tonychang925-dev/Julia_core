from __future__ import annotations

from dataclasses import dataclass

from julia_core.memory import MemoryObject
from julia_core.memory.weighting import ImportanceModel, RelationshipWeight

from .query_builder import MemoryQueryBuilder
from .relevance_scorer import RelevanceScorer
from .retrieval_context import MemoryRetrievalContext


@dataclass(frozen=True)
class RankedMemoryExplanation:
    memory: MemoryObject
    score: float
    reason: list[str]
    components: dict[str, float]


class CognitiveMemoryRanker:
    """Context-aware memory attention mechanism for Phase 3.6.2."""

    def __init__(self):
        self.query_builder = MemoryQueryBuilder()
        self.relevance_scorer = RelevanceScorer()
        self.importance_model = ImportanceModel()
        self.relationship_weight = RelationshipWeight()

    def rank(self, context: MemoryRetrievalContext, memories: list[MemoryObject], *, limit: int = 5) -> list[MemoryObject]:
        return [item.memory for item in self.rank_with_explanations(context, memories, limit=limit)]

    def rank_with_explanations(self, context: MemoryRetrievalContext, memories: list[MemoryObject], *, limit: int = 5) -> list[RankedMemoryExplanation]:
        query = self.query_builder.build(context)
        ranked: list[RankedMemoryExplanation] = []
        for memory in memories:
            relevance = self.relevance_scorer.score(query, memory, context)
            importance = self.importance_model.score(memory, query.priority)
            relationship = self.relationship_weight.score(memory, relationship_stage=context.relationship_stage, query_priority=query.priority)
            recurrence = float(memory.importance.get("recurrence", 0.0) or 0.0)
            final_score = relevance.score + importance * 0.35 + relationship * 0.25 + recurrence * 0.15 + relevance.topic_overlap * 0.25
            reasons = list(relevance.reasons)
            if importance >= 0.7:
                reasons.append("high_importance")
            if relationship >= 0.6:
                reasons.append("relationship_match")
            if recurrence >= 0.7:
                reasons.append("recurrence_weight")
            if query.memory_types and memory.type == query.memory_types[0]:
                reasons.append("preferred_memory_type")
            ranked.append(
                RankedMemoryExplanation(
                    memory=memory,
                    score=round(final_score, 6),
                    reason=self._dedupe(reasons),
                    components={
                        "relevance": round(relevance.score, 6),
                        "importance": round(importance, 6),
                        "relationship": round(relationship, 6),
                        "recurrence": round(recurrence, 6),
                        "topic_overlap": round(relevance.topic_overlap, 6),
                    },
                )
            )
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[: max(0, limit)]

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        result: list[str] = []
        for item in items:
            if item and item not in result:
                result.append(item)
        return result

from __future__ import annotations

import re
from dataclasses import dataclass

from julia_core.memory.memory_object import MemoryObject


@dataclass(frozen=True)
class RankedMemory:
    memory: MemoryObject
    score: float


class RuleMemoryRanker:
    """Rule + metadata ranking for Phase 3.5.3.

    This intentionally avoids embeddings. It validates memory architecture before
    search-performance optimization.
    """

    RELATIONSHIP_QUERY_TERMS = {"为什么", "Tony", "关系", "身份", "存在", "迁移", "连续", "记得", "项目"}
    TECHNICAL_QUERY_TERMS = {"架构", "模块", "runtime", "Runtime", "DirectLLMBridge", "Capability", "Cognitive", "技术"}

    TYPE_WEIGHTS = {
        "relationship": 0.25,
        "episodic": 0.15,
        "semantic": 0.12,
        "working": 0.2,
    }

    def rank(self, query: str, memories: list[MemoryObject], *, limit: int = 5) -> list[MemoryObject]:
        ranked = [RankedMemory(memory=memory, score=self.score(query, memory)) for memory in memories]
        ranked.sort(key=lambda item: item.score, reverse=True)
        return [item.memory for item in ranked[: max(0, limit)]]

    def score(self, query: str, memory: MemoryObject) -> float:
        compact_query = query.strip()
        text = " ".join([memory.summary, " ".join(memory.topics), str(memory.content)]).lower()
        score = 0.0
        score += self.TYPE_WEIGHTS.get(memory.type, 0.0)
        score += self._importance_score(query, memory)
        score += self._keyword_overlap(compact_query, text)
        score += self._query_intent_boost(compact_query, memory)
        score += self._recency_score(memory.timestamp)
        return score

    def _importance_score(self, query: str, memory: MemoryObject) -> float:
        relationship_intent = any(term in query for term in self.RELATIONSHIP_QUERY_TERMS)
        technical_intent = any(term in query for term in self.TECHNICAL_QUERY_TERMS)
        importance = memory.importance
        score = 0.0
        if relationship_intent:
            score += importance.get("relationship", 0.0) * 0.4
            score += importance.get("emotional", 0.0) * 0.2
            score += importance.get("recurrence", 0.0) * 0.2
        if technical_intent:
            score += importance.get("technical", 0.0) * 0.45
            score += importance.get("recurrence", 0.0) * 0.15
        if not relationship_intent and not technical_intent:
            score += sum(importance.values()) / max(1, len(importance)) * 0.3
        return score

    @staticmethod
    def _keyword_overlap(query: str, text: str) -> float:
        tokens = [token for token in re.split(r"[\s，。！？、,.!?;；:：/]+", query) if token]
        if not tokens:
            return 0.0
        hits = 0
        for token in tokens:
            if token.lower() in text:
                hits += 1
        return min(0.4, hits * 0.08)

    def _query_intent_boost(self, query: str, memory: MemoryObject) -> float:
        score = 0.0
        relationship_intent = any(term in query for term in self.RELATIONSHIP_QUERY_TERMS)
        technical_intent = any(term in query for term in self.TECHNICAL_QUERY_TERMS)
        if relationship_intent and memory.type == "relationship":
            score += 0.35
        if technical_intent and memory.type == "semantic":
            score += 0.35
        if "为什么" in query and ("identity continuity" in memory.topics or "model migration" in memory.topics):
            score += 0.3
        if "架构" in query and "AI Agent Architecture" in memory.topics:
            score += 0.25
        return score

    @staticmethod
    def _recency_score(timestamp: str) -> float:
        if not timestamp:
            return 0.0
        if timestamp.startswith("2026"):
            return 0.05
        return 0.01

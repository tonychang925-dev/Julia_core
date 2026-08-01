from __future__ import annotations

import re
from dataclasses import dataclass

from julia_core.memory import MemoryObject

from .retrieval_context import MemoryQuery, MemoryRetrievalContext


@dataclass(frozen=True)
class RelevanceScore:
    score: float
    topic_overlap: float
    current_arc_match: float
    user_intent_match: float
    reasons: list[str]


class RelevanceScorer:
    def score(self, query: MemoryQuery, memory: MemoryObject, context: MemoryRetrievalContext) -> RelevanceScore:
        reasons: list[str] = []
        topic_overlap = self._topic_overlap(query.topics, memory.topics, memory.summary)
        if topic_overlap > 0:
            reasons.append("topic_match")
        current_arc_match = self._arc_match(context.current_arc, memory)
        if current_arc_match > 0:
            reasons.append("current_arc_match")
        user_intent_match = self._intent_match(query, memory)
        if user_intent_match > 0:
            reasons.append("user_intent_match")
        score = min(1.0, topic_overlap * 0.4 + current_arc_match * 0.3 + user_intent_match * 0.3)
        return RelevanceScore(score=score, topic_overlap=topic_overlap, current_arc_match=current_arc_match, user_intent_match=user_intent_match, reasons=reasons)

    @staticmethod
    def _topic_overlap(query_topics: list[str], memory_topics: list[str], summary: str) -> float:
        q = {topic.lower() for topic in query_topics if topic}
        m = {topic.lower() for topic in memory_topics if topic}
        summary_lower = summary.lower()
        hits = len(q.intersection(m))
        for topic in q:
            if topic and topic in summary_lower:
                hits += 1
        if not q:
            return 0.0
        return min(1.0, hits / max(1, len(q)))

    @staticmethod
    def _arc_match(current_arc: str, memory: MemoryObject) -> float:
        arc = current_arc.lower()
        text = f"{memory.summary} {' '.join(memory.topics)}".lower()
        if not arc:
            return 0.0
        if arc in text:
            return 1.0
        if arc == "project_pressure" and any(term in text for term in ["pressure", "project", "做不完", "压力", "completion"]):
            return 0.9
        if arc == "technical_progress" and any(term in text for term in ["runtime", "architecture", "context", "compiler", "架构"]):
            return 0.8
        return 0.0

    @staticmethod
    def _intent_match(query: MemoryQuery, memory: MemoryObject) -> float:
        lower = query.text.lower()
        text = f"{memory.summary} {' '.join(memory.topics)} {memory.type}".lower()
        score = 0.0
        tokens = [token for token in re.split(r"[\s，。！？、,.!?;；:：/]+", lower) if token]
        if tokens:
            hits = sum(1 for token in tokens if token in text)
            score = max(score, min(0.6, hits * 0.15))
        if query.memory_types and memory.type == query.memory_types[0]:
            score = max(score, 0.7)
        if query.priority.get("relationship", 0.0) >= 0.8 and memory.type == "relationship":
            score = max(score, 1.0)
        if query.priority.get("technical", 0.0) >= 0.8 and memory.type == "semantic":
            score = max(score, 1.0)
        return min(1.0, score)

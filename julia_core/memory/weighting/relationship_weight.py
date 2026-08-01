from __future__ import annotations

from julia_core.memory import MemoryObject


class RelationshipWeight:
    def score(self, memory: MemoryObject, *, relationship_stage: str, query_priority: dict[str, float]) -> float:
        score = 0.0
        if memory.type == "relationship":
            score += 0.45
        score += float(memory.importance.get("relationship", 0.0) or 0.0) * 0.35
        if relationship_stage.startswith("long_term"):
            score += 0.1
        if query_priority.get("relationship", 0.0) >= 0.8:
            score += 0.1
        return min(1.0, score)

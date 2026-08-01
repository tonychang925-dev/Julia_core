from __future__ import annotations

from julia_core.memory import MemoryObject


class ImportanceModel:
    def score(self, memory: MemoryObject, priority: dict[str, float] | None = None) -> float:
        priority = priority or {"emotional": 0.25, "relationship": 0.25, "technical": 0.25, "recurrence": 0.25}
        total_weight = sum(max(0.0, float(value)) for value in priority.values()) or 1.0
        return sum(float(memory.importance.get(key, 0.0) or 0.0) * max(0.0, float(weight)) for key, weight in priority.items()) / total_weight

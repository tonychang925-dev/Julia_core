from __future__ import annotations

from dataclasses import replace

from julia_core.memory import MemoryObject


class MemoryReinforcer:
    def should_reinforce(self, memory: MemoryObject, *, referenced_topics: list[str]) -> bool:
        text = f"{memory.summary} {' '.join(memory.topics)}".lower()
        hits = sum(1 for topic in referenced_topics if topic.lower() in text or topic in memory.topics)
        return hits >= 1 and (memory.importance.get("technical", 0.0) >= 0.6 or memory.importance.get("relationship", 0.0) >= 0.6)

    def reinforce(self, memory: MemoryObject, *, amount: float = 0.08) -> MemoryObject:
        importance = dict(memory.importance)
        importance["recurrence"] = self._clamp(importance.get("recurrence", 0.0) + amount)
        dominant = "relationship" if memory.importance.get("relationship", 0.0) >= memory.importance.get("technical", 0.0) else "technical"
        importance[dominant] = self._clamp(importance.get(dominant, 0.0) + amount / 2)
        content = {**memory.content, "last_lifecycle_action": "reinforce"}
        return replace(memory, importance=importance, content=content)

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

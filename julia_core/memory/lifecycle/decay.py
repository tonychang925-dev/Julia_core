from __future__ import annotations

from dataclasses import replace

from julia_core.memory import MemoryObject


class MemoryDecay:
    def should_decay(self, memory: MemoryObject) -> bool:
        if memory.type == "relationship" and memory.importance.get("relationship", 0.0) >= 0.85:
            return False
        avg = sum(memory.importance.values()) / max(1, len(memory.importance))
        return avg < 0.35 and memory.importance.get("recurrence", 0.0) < 0.25

    def decay(self, memory: MemoryObject, *, amount: float = 0.08) -> MemoryObject:
        importance = {key: max(0.0, float(value) - amount) for key, value in memory.importance.items()}
        content = {**memory.content, "last_lifecycle_action": "decay"}
        return replace(memory, importance=importance, content=content)

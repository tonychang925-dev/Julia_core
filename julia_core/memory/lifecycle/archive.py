from __future__ import annotations

from julia_core.memory import MemoryObject


class MemoryArchiver:
    def should_archive(self, memory: MemoryObject) -> bool:
        if memory.type == "relationship" and memory.importance.get("relationship", 0.0) >= 0.85:
            return False
        text = f"{memory.summary} {' '.join(memory.topics)}".lower()
        obsolete = any(term in text for term in ["obsolete", "过期", "临时", "temporary", "failed test", "debug log"])
        avg = sum(memory.importance.values()) / max(1, len(memory.importance))
        return obsolete and avg < 0.45

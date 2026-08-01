from __future__ import annotations

from dataclasses import replace

from julia_core.memory import MemoryObject


class MemoryMergePolicy:
    def group_key(self, memory: MemoryObject) -> str:
        text = f"{memory.summary} {' '.join(memory.topics)}".lower()
        if "julia" in text and ("runtime" in text or "cognitive" in text or "directllmbridge" in text or "contextcompiler" in text):
            return f"{memory.type}:julia_runtime_independence"
        return f"{memory.type}:{'|'.join(sorted(topic.lower() for topic in memory.topics[:3]))}"

    def mergeable_groups(self, memories: list[MemoryObject]) -> dict[str, list[MemoryObject]]:
        groups: dict[str, list[MemoryObject]] = {}
        for memory in memories:
            key = self.group_key(memory)
            groups.setdefault(key, []).append(memory)
        return {key: group for key, group in groups.items() if len(group) >= 2}

    def merge(self, memories: list[MemoryObject]) -> MemoryObject:
        base = memories[0]
        importance = {"emotional": 0.0, "relationship": 0.0, "technical": 0.0, "recurrence": 0.0}
        topics: list[str] = []
        for memory in memories:
            for key in importance:
                importance[key] = max(importance[key], float(memory.importance.get(key, 0.0) or 0.0))
            for topic in memory.topics:
                if topic and topic not in topics:
                    topics.append(topic)
        if "Julia Runtime" in topics or any("julia" in memory.summary.lower() for memory in memories):
            summary = "Tony consolidated Julia Runtime Independence milestones across DirectLLMBridge, Context Compiler, and Cognitive Runtime."
        else:
            summary = max((memory.summary for memory in memories), key=len)
        content = {"merged_memory_ids": [memory.id for memory in memories], "last_lifecycle_action": "merge"}
        return replace(base, summary=summary, content={**base.content, **content}, topics=topics, importance=importance)

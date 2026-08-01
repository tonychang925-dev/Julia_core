from __future__ import annotations

from dataclasses import dataclass

from julia_core.memory import MemoryObject

from .archive import MemoryArchiver
from .decay import MemoryDecay
from .lifecycle_decision import MemoryLifecycleDecision
from .merge_policy import MemoryMergePolicy
from .reinforcement import MemoryReinforcer


@dataclass(frozen=True)
class MemoryLifecycleResult:
    memories: list[MemoryObject]
    decisions: list[MemoryLifecycleDecision]


class MemoryLifecycleManager:
    def __init__(self):
        self.reinforcer = MemoryReinforcer()
        self.decay = MemoryDecay()
        self.archiver = MemoryArchiver()
        self.merge_policy = MemoryMergePolicy()

    def evaluate(self, memories: list[MemoryObject], *, referenced_topics: list[str] | None = None) -> list[MemoryLifecycleDecision]:
        referenced_topics = referenced_topics or []
        decisions: list[MemoryLifecycleDecision] = []
        merge_ids = {memory.id for group in self.merge_policy.mergeable_groups(memories).values() for memory in group}
        for memory in memories:
            if self._is_protected(memory):
                decisions.append(MemoryLifecycleDecision("retain", memory.id, "protected_core_relationship_memory", 0.96))
            elif memory.id in merge_ids:
                decisions.append(MemoryLifecycleDecision("merge", memory.id, "related_milestone_group", 0.9))
            elif self.archiver.should_archive(memory):
                decisions.append(MemoryLifecycleDecision("archive", memory.id, "obsolete_low_value", 0.88))
            elif self.decay.should_decay(memory):
                decisions.append(MemoryLifecycleDecision("decay", memory.id, "low_recurrence_low_importance", 0.86))
            elif self.reinforcer.should_reinforce(memory, referenced_topics=referenced_topics):
                decisions.append(MemoryLifecycleDecision("reinforce", memory.id, "repeated_high_value_topic", 0.92))
            else:
                decisions.append(MemoryLifecycleDecision("retain", memory.id, "no_lifecycle_change_needed", 0.72))
        return decisions

    def apply(self, memories: list[MemoryObject], *, referenced_topics: list[str] | None = None) -> MemoryLifecycleResult:
        referenced_topics = referenced_topics or []
        decisions = self.evaluate(memories, referenced_topics=referenced_topics)
        by_id = {decision.memory_id: decision for decision in decisions}
        merge_groups = self.merge_policy.mergeable_groups(memories)
        merged_ids: set[str] = set()
        output: list[MemoryObject] = []
        for group in merge_groups.values():
            output.append(self.merge_policy.merge(group))
            merged_ids.update(memory.id for memory in group)
        for memory in memories:
            if memory.id in merged_ids:
                continue
            decision = by_id[memory.id]
            if decision.action == "archive":
                archived_content = {**memory.content, "archived": True, "last_lifecycle_action": "archive"}
                output.append(memory.__class__(**{**memory.__dict__, "content": archived_content}))
            elif decision.action == "decay":
                output.append(self.decay.decay(memory))
            elif decision.action == "reinforce":
                output.append(self.reinforcer.reinforce(memory))
            else:
                output.append(memory)
        return MemoryLifecycleResult(memories=output, decisions=decisions)

    @staticmethod
    def _is_protected(memory: MemoryObject) -> bool:
        text = f"{memory.summary} {' '.join(memory.topics)}".lower()
        if memory.type != "relationship":
            return False
        return memory.importance.get("relationship", 0.0) >= 0.9 and any(term in text for term in ["identity continuity", "why", "created julia", "创建", "存在", "连续身份"])

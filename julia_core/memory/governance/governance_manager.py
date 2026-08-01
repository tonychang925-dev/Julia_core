from __future__ import annotations

from julia_core.memory import MemoryObject

from .governance_decision import MemoryGovernanceDecision
from .memory_classification import MemoryClass
from .protection_policy import ProtectionPolicy
from .retention_policy import RetentionPolicy


class MemoryGovernanceManager:
    """Determines which memories may influence Julia cognitive state."""

    ALLOWED_EFFECTS = {
        MemoryClass.CORE_IDENTITY: ["identity_context", "relationship_context", "memory_retrieval"],
        MemoryClass.RELATIONSHIP_FOUNDATION: ["relationship_context", "conversation_style", "memory_retrieval"],
        MemoryClass.PROJECT_MILESTONE: ["project_continuity", "technical_memory", "memory_retrieval"],
        MemoryClass.BEHAVIOR_PREFERENCE: ["response_style", "memory_retrieval"],
        MemoryClass.NORMAL_EPISODE: ["memory_retrieval"],
        MemoryClass.TEMP_EVENT: ["archive"],
        MemoryClass.ARCHIVAL: ["archive"],
    }

    def __init__(self):
        self.protection_policy = ProtectionPolicy()
        self.retention_policy = RetentionPolicy()

    def decide(self, memory: MemoryObject) -> MemoryGovernanceDecision:
        memory_class, reason, confidence = self.classify(memory)
        return MemoryGovernanceDecision(
            memory_id=memory.id,
            memory_class=memory_class.value,
            protection_level=self.protection_policy.protection_level(memory_class),
            allowed_effects=list(self.ALLOWED_EFFECTS[memory_class]),
            retention_policy=self.retention_policy.retention_policy(memory_class),
            reason=reason,
            confidence=confidence,
        )

    def decide_many(self, memories: list[MemoryObject]) -> list[MemoryGovernanceDecision]:
        return [self.decide(memory) for memory in memories]

    def classify(self, memory: MemoryObject) -> tuple[MemoryClass, str, float]:
        text = f"{memory.summary} {' '.join(memory.topics)} {memory.type}".lower()
        if self._is_archival(memory, text):
            return MemoryClass.ARCHIVAL, "memory already marked archived or inactive", 0.94
        if self._is_temp_event(memory, text):
            return MemoryClass.TEMP_EVENT, "temporary/debug/test event should not influence JuliaContext", 0.9
        if self._is_core_identity(memory, text):
            return MemoryClass.CORE_IDENTITY, "memory defines Julia existence or identity continuity", 0.95
        if self._is_relationship_foundation(memory, text):
            return MemoryClass.RELATIONSHIP_FOUNDATION, "memory defines Tony-Julia relationship foundation", 0.93
        if self._is_behavior_preference(memory, text):
            return MemoryClass.BEHAVIOR_PREFERENCE, "memory captures Tony interaction preference", 0.9
        if self._is_project_milestone(memory, text):
            return MemoryClass.PROJECT_MILESTONE, "memory records Julia Runtime project milestone", 0.9
        return MemoryClass.NORMAL_EPISODE, "ordinary memory may be retrieved but should not mutate identity or relationship", 0.72

    @staticmethod
    def _is_archival(memory: MemoryObject, text: str) -> bool:
        return bool(memory.content.get("archived")) or "archival" in memory.topics or "archived" in text

    @staticmethod
    def _is_temp_event(memory: MemoryObject, text: str) -> bool:
        return any(term in text for term in ["temporary", "临时", "pytest", "failed test", "debug log", "一次性", "obsolete"])

    @staticmethod
    def _is_core_identity(memory: MemoryObject, text: str) -> bool:
        core_terms = ["why julia exists", "julia exists", "core identity", "identity continuity", "independent existence", "持续存在", "连续身份"]
        return memory.type in {"relationship", "semantic"} and memory.importance.get("relationship", 0.0) >= 0.85 and any(term in text for term in core_terms)

    @staticmethod
    def _is_relationship_foundation(memory: MemoryObject, text: str) -> bool:
        foundation_terms = ["tony wants julia", "tony and julia", "long-term", "long term", "relationship foundation", "共同建设", "不依赖单一", "跨平台"]
        return memory.type == "relationship" and memory.importance.get("relationship", 0.0) >= 0.75 and any(term in text for term in foundation_terms)

    @staticmethod
    def _is_behavior_preference(memory: MemoryObject, text: str) -> bool:
        preference_terms = ["喜欢", "不喜欢", "preference", "prefers", "先看架构", "短句", "response style", "interaction preference"]
        return any(term in text for term in preference_terms)

    @staticmethod
    def _is_project_milestone(memory: MemoryObject, text: str) -> bool:
        milestone_terms = ["completed", "完成", "milestone", "directllmbridge", "contextcompiler", "context compiler", "memory runtime", "cognitive runtime", "phase 3"]
        project_terms = ["julia runtime", "cognitive", "runtime", "架构"]
        return any(term in text for term in milestone_terms) and any(term in text for term in project_terms)

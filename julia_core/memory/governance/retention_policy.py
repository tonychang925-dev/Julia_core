from __future__ import annotations

from .memory_classification import MemoryClass


class RetentionPolicy:
    RETENTION_BY_CLASS = {
        MemoryClass.CORE_IDENTITY: "permanent_no_decay_archive",
        MemoryClass.RELATIONSHIP_FOUNDATION: "long_term_protected",
        MemoryClass.PROJECT_MILESTONE: "long_term_reinforce_merge",
        MemoryClass.BEHAVIOR_PREFERENCE: "reinforce_or_update",
        MemoryClass.NORMAL_EPISODE: "normal_decay",
        MemoryClass.TEMP_EVENT: "fast_archive",
        MemoryClass.ARCHIVAL: "inactive_archive",
    }

    def retention_policy(self, memory_class: MemoryClass) -> str:
        return self.RETENTION_BY_CLASS[memory_class]

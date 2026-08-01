from __future__ import annotations

from .memory_classification import MemoryClass


class ProtectionPolicy:
    PROTECTION_BY_CLASS = {
        MemoryClass.CORE_IDENTITY: "immutable_permanent",
        MemoryClass.RELATIONSHIP_FOUNDATION: "strong_protection",
        MemoryClass.PROJECT_MILESTONE: "long_term_protection",
        MemoryClass.BEHAVIOR_PREFERENCE: "updateable_preference",
        MemoryClass.NORMAL_EPISODE: "normal_lifecycle",
        MemoryClass.TEMP_EVENT: "low_protection",
        MemoryClass.ARCHIVAL: "archived_inactive",
    }

    def protection_level(self, memory_class: MemoryClass) -> str:
        return self.PROTECTION_BY_CLASS[memory_class]

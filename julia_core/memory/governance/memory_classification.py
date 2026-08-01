from __future__ import annotations

from enum import Enum


class MemoryClass(Enum):
    CORE_IDENTITY = "core_identity"
    RELATIONSHIP_FOUNDATION = "relationship_foundation"
    PROJECT_MILESTONE = "project_milestone"
    BEHAVIOR_PREFERENCE = "behavior_preference"
    NORMAL_EPISODE = "normal_episode"
    TEMP_EVENT = "temp_event"
    ARCHIVAL = "archival"

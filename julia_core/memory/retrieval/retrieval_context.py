from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryRetrievalContext:
    """Julia-facing retrieval state. Runtime/provider metadata is excluded."""

    user_input: str
    active_topics: list[str]
    current_arc: str
    cognitive_mode: str
    relationship_stage: str


@dataclass(frozen=True)
class MemoryQuery:
    text: str
    topics: list[str]
    memory_types: list[str]
    priority: dict[str, float]

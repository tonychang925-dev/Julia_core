from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GovernanceEvent:
    memory_id: str
    memory_class: str
    allowed_effects: list[str]
    reason: str
    timestamp: str
    confidence: float

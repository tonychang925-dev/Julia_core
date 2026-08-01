from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryGovernanceDecision:
    memory_id: str
    memory_class: str
    protection_level: str
    allowed_effects: list[str]
    retention_policy: str
    reason: str
    confidence: float

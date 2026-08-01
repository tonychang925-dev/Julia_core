from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MemoryLifecycleDecision:
    action: str  # reinforce / merge / decay / archive / retain
    memory_id: str
    reason: str
    confidence: float
    metadata: dict[str, object] = field(default_factory=dict)

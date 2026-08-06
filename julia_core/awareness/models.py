"""M3.0 Awareness Models — what the world is doing, not what Julia queried.

ADR-028 Section 2.1: ObservationEvent is distinct from CapabilityResult.
CapabilityResult answers "what did I query?"
ObservationEvent answers "what changed in the world?"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from uuid import uuid4

CST = timezone(timedelta(hours=8))


@dataclass(frozen=True, slots=True)
class ObservationEvent:
    """External world change detected by an observation source.

    This is NOT a capability result. It is a perception event.
    Julia doesn't query this — she receives it.
    """
    observation_id: str = field(default_factory=lambda: f"obs_{uuid4().hex}")
    source: str = ""                        # "ai_theme_app" | "calendar" | "github" | ...
    domain: str = ""                        # "market" | "health" | "calendar" | "news"
    event_type: str = ""                    # "world.market.changed" | "world.risk.emerged"
    subject: str = ""                       # "AI机器人" | "半导体" | "外围市场"
    change_type: str = ""                   # "heat_jump" | "risk_spike" | "sentiment_shift" | "new_pattern"
    delta: str = ""                         # "+18" | "-5" | "new_high"
    payload: dict = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()     # Capability invocation IDs for audit
    confidence: float = 0.5                 # 0.0-1.0, source reliability
    detected_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())
    correlation_id: str = ""                # Links to workflow events


@dataclass(frozen=True, slots=True)
class AwarenessArtifact:
    """Julia's cognitive record of a world observation.

    Not a report. Not an assistant message. A governed record of:
      - What Julia noticed
      - Why she noticed it (evidence)
      - How confident she is
      - What evidence supports it

    This is the input to future M7 Feedback Loop.
    """
    artifact_id: str = field(default_factory=lambda: f"aware_{uuid4().hex}")
    observation_id: str = ""
    workflow_id: str = ""                   # WorkflowInstance correlation_id
    subject: str = ""                       # "AI机器人"
    observation: str = ""                   # Human-readable: "资金热度快速提升"
    evidence_refs: tuple[str, ...] = ()     # Capability invocations, event IDs
    confidence: float = 0.0
    reasoning: str = ""                     # Why Julia considers this significant
    created_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())
    domain: str = "market"


__all__ = ["ObservationEvent", "AwarenessArtifact"]

"""R1.1 Runtime Event Model — immutable runtime facts.

ADR-027 Section 3: Event = Runtime Fact with provenance chain.
Events are NOT logs. They are the canonical record of what happened.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class EventCategory(str, Enum):
    """ADR-027 Section 4: Frozen event categories."""
    RUNTIME       = "runtime"
    CONVERSATION  = "conversation"
    CAPABILITY    = "capability"
    WORKFLOW      = "workflow"
    EXPERIENCE    = "experience"


# ── Event types per category ────────────────────────────────────────────────

class RuntimeEventType:
    STARTED        = "runtime.started"
    STATE_CHANGED  = "runtime.state.changed"
    COMPLETED      = "runtime.completed"
    FAILED         = "runtime.failed"

class ConversationEventType:
    CREATED           = "conversation.created"
    MESSAGE_RECEIVED  = "conversation.message.received"
    TURN_COMPLETED    = "conversation.turn.completed"

class CapabilityEventType:
    REQUESTED  = "capability.requested"
    STARTED    = "capability.started"
    COMPLETED  = "capability.completed"
    FAILED     = "capability.failed"

class WorkflowEventType:
    CREATED         = "workflow.created"
    STEP_STARTED    = "workflow.step.started"
    STEP_COMPLETED  = "workflow.step.completed"
    COMPLETED       = "workflow.completed"
    FAILED          = "workflow.failed"

class ExperienceEventType:
    CREATED  = "experience.created"
    UPDATED  = "experience.updated"


# ── Runtime Event ────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    """One immutable runtime fact. ADR-027 Section 3.1.

    Every event carries:
      - Unique identity (event_id)
      - Temporal position (timestamp)
      - Causal position (correlation_id, causation_id)
      - Evidentiary links (evidence_refs)
      - Domain body (payload)
    """
    event_id: str = field(default_factory=lambda: f"evt_{uuid4().hex}")
    timestamp: str = ""                     # ISO 8601 — set at emit time
    source: str = ""                        # "runtime" | "capability" | "workflow" | "conversation"
    event_type: str = ""                    # "capability.requested" | "workflow.completed" | ...
    category: EventCategory = EventCategory.RUNTIME
    payload: dict = field(default_factory=dict)
    correlation_id: str = ""                # Groups events in the same logical chain
    causation_id: str = ""                  # Points to the event that caused this one
    evidence_refs: tuple[str, ...] = ()     # Linked evidence (prediction_id, capability_id, etc.)


def create_event(
    source: str,
    event_type: str,
    category: EventCategory,
    payload: dict | None = None,
    correlation_id: str = "",
    causation_id: str = "",
    evidence_refs: tuple[str, ...] = (),
) -> RuntimeEvent:
    """Factory: create a timestamped runtime event."""
    from datetime import datetime, timezone, timedelta
    CST = timezone(timedelta(hours=8))
    return RuntimeEvent(
        timestamp=datetime.now(CST).isoformat(),
        source=source,
        event_type=event_type,
        category=category,
        payload=payload or {},
        correlation_id=correlation_id,
        causation_id=causation_id,
        evidence_refs=evidence_refs,
    )


__all__ = [
    "EventCategory",
    "RuntimeEventType",
    "ConversationEventType",
    "CapabilityEventType",
    "WorkflowEventType",
    "ExperienceEventType",
    "RuntimeEvent",
    "create_event",
]

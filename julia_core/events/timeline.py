"""R1.1 Timeline Reconstruction — reconstruct causal chains from event store.

ADR-027 Section 3.2: Given a correlation_id, reconstruct the full
evidence timeline to answer: "why did Julia say that?"
"""

from __future__ import annotations

from dataclasses import dataclass, field

from julia_core.events.models import RuntimeEvent
from julia_core.events.store import EventStore, get_event_store


@dataclass
class EventTimeline:
    """A reconstructed causal chain of events."""
    correlation_id: str
    events: list[RuntimeEvent] = field(default_factory=list)
    causal_chain: list[tuple[str, str]] = field(default_factory=list)  # (cause_id, effect_id)

    @property
    def root_event(self) -> RuntimeEvent | None:
        return self.events[0] if self.events else None

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def sequence(self) -> list[str]:
        """Ordered list of event_types."""
        return [e.event_type for e in self.events]


class TimelineReconstructor:
    """Reconstruct causal chains from the Event Store.

    Usage:
        store = get_event_store()
        reconstructor = TimelineReconstructor(store)
        timeline = reconstructor.reconstruct(correlation_id)

        # Answer: "why did Julia produce this answer?"
        print(timeline.sequence)
    """

    def __init__(self, store: EventStore | None = None):
        self.store = store or get_event_store()

    def reconstruct(self, correlation_id: str) -> EventTimeline:
        """Build a full event timeline for a correlation chain.

        Retrieves all events with matching correlation_id, sorted by timestamp.
        Builds causal pairs from causation_id references.
        """
        events = self.store.by_correlation(correlation_id)

        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)

        # Build causal pairs: (cause_id → effect_id) for non-empty causation refs
        causal_chain: list[tuple[str, str]] = []
        for event in events:
            if event.causation_id and self.store.get(event.causation_id):
                causal_chain.append((event.causation_id, event.event_id))

        return EventTimeline(
            correlation_id=correlation_id,
            events=events,
            causal_chain=causal_chain,
        )

    def explain(self, correlation_id: str) -> str:
        """Human-readable explanation of what happened in this chain."""
        timeline = self.reconstruct(correlation_id)
        if not timeline.events:
            return f"No events found for correlation_id={correlation_id}"

        lines = [f"Timeline for {correlation_id}:"]
        for i, event in enumerate(timeline.events):
            lines.append(f"  {i+1}. [{event.timestamp}] {event.event_type}")
            if event.payload:
                summary = {k: v for k, v in event.payload.items()
                          if k in ("intent", "capability", "provider", "brief_id", "prediction_ids")}
                if summary:
                    lines.append(f"     {summary}")
        return "\n".join(lines)


__all__ = ["EventTimeline", "TimelineReconstructor"]

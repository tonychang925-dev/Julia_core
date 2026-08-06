"""R1.1 Event Store — append-only durable event persistence.

ADR-027 Section 3.3: Events are written at emit time. Append-only.
Never mutated. Correlation chains never broken.
"""

from __future__ import annotations

import json as _json
from pathlib import Path
from typing import Optional

from julia_core.events.models import RuntimeEvent


class EventStore:
    """Append-only event persistence.

    Events are written immediately on emit. They cannot be modified.
    They can only be read back for timeline reconstruction and audit.
    """

    def __init__(self, storage_dir: str = ""):
        self._storage = Path(storage_dir) if storage_dir else Path(__file__).resolve().parent.parent.parent / "data" / "events"
        self._storage.mkdir(parents=True, exist_ok=True)
        self._buffer: list[RuntimeEvent] = []  # In-memory buffer for fast read-back

    def append(self, event: RuntimeEvent):
        """Append one event. Written to buffer immediately. Persisted synchronously."""
        self._buffer.append(event)
        self._persist(event)

    def _persist(self, event: RuntimeEvent):
        """Write event to append-only JSONL file."""
        try:
            today = event.timestamp[:10] if event.timestamp else "unknown"
            log_path = self._storage / f"events-{today}.jsonl"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(_json.dumps({
                    "event_id": event.event_id,
                    "timestamp": event.timestamp,
                    "source": event.source,
                    "event_type": event.event_type,
                    "category": event.category.value,
                    "payload": event.payload,
                    "correlation_id": event.correlation_id,
                    "causation_id": event.causation_id,
                    "evidence_refs": list(event.evidence_refs),
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass  # Event store failure must not crash the runtime

    # ── Query ──────────────────────────────────────────────────────────────

    def get(self, event_id: str) -> Optional[RuntimeEvent]:
        """Retrieve one event by ID."""
        for e in reversed(self._buffer):
            if e.event_id == event_id:
                return e
        return None

    def by_correlation(self, correlation_id: str) -> list[RuntimeEvent]:
        """Retrieve all events in the same logical chain."""
        return [e for e in self._buffer if e.correlation_id == correlation_id]

    def by_causation(self, causation_id: str) -> list[RuntimeEvent]:
        """Retrieve events caused by a specific event."""
        return [e for e in self._buffer if e.causation_id == causation_id]

    def recent(self, n: int = 20) -> list[RuntimeEvent]:
        """Return most recent events."""
        return self._buffer[-n:]

    def by_category(self, category_value: str, n: int = 50) -> list[RuntimeEvent]:
        """Return events of a specific category."""
        return [e for e in self._buffer if e.category.value == category_value][-n:]

    @property
    def count(self) -> int:
        return len(self._buffer)


# ── Singleton ───────────────────────────────────────────────────────────────

_store: Optional[EventStore] = None


def get_event_store() -> EventStore:
    global _store
    if _store is None:
        _store = EventStore()
    return _store


__all__ = ["EventStore", "get_event_store"]

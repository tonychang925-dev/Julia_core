"""M3.2.1 Observation Identity — deduplication key.

ADR-030 Section 3: Two observations with the same identity key within
the same 15-minute time window are treated as duplicates.

Identity answers: "Is this the same event?" — not "Is this important?"
Confidence and alert_level belong to Policy, not Identity.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from julia_core.awareness.models import ObservationEvent


def time_window(iso_timestamp: str = "", minutes: int = 15) -> str:
    """Normalize timestamp to a time window for deduplication."""
    if not iso_timestamp:
        return "unknown_window"
    try:
        # Parse ISO 8601: "2026-08-06T09:30:00+08:00"
        parts = iso_timestamp[:16]  # "2026-08-06T09:30"
        hour = int(parts[11:13])
        minute = int(parts[14:16])
        bucket = (minute // minutes) * minutes
        return f"{parts[:11]}{hour:02d}:{bucket:02d}"
    except (ValueError, IndexError):
        return "unknown_window"


@dataclass
class ObservationIdentity:
    """Generates deduplication keys for observation events.

    Usage:
        identity = ObservationIdentity()
        key1 = identity.key(event1)
        key2 = identity.key(event2)
        if key1 == key2 → duplicate (within same window)
    """

    window_minutes: int = 15

    # Track seen keys in-memory for dedup
    _seen_keys: set[str] = field(default_factory=set)

    def key(self, event: ObservationEvent) -> str:
        """Generate identity key: domain:subject:event_type:time_window."""
        window = time_window(event.detected_at, self.window_minutes)
        raw = f"{event.domain}:{event.subject}:{event.event_type}:{window}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def is_duplicate(self, event: ObservationEvent) -> bool:
        """Check if this event has been seen in the current window.

        Returns True if duplicate, False if new.
        Records the key if new (side effect for dedup tracking).
        """
        event_key = self.key(event)
        if event_key in self._seen_keys:
            return True
        self._seen_keys.add(event_key)
        return False

    def reset(self):
        """Clear seen keys (e.g., for a new session or day)."""
        self._seen_keys.clear()

    def mark_seen(self, event: ObservationEvent):
        """Explicitly mark an event key as seen."""
        self._seen_keys.add(self.key(event))

    @staticmethod
    def key_from_dict(obs: dict, window_minutes: int = 15) -> str:
        """Generate key from a raw observation dict (pre-adapter).

        Used in tests and Policy layer before full ObservationEvent creation.
        """
        domain = obs.get("domain", "market")
        subject = obs.get("theme", obs.get("subject", "unknown"))
        event_type = obs.get("type", "unknown")
        timestamp = obs.get("generated_at", obs.get("timestamp", ""))
        window = time_window(timestamp, window_minutes)
        raw = f"{domain}:{subject}:{event_type}:{window}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


__all__ = ["ObservationIdentity", "time_window"]

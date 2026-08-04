"""Julia Presence Manager — state awareness for all UI consumers.

Manages Julia's observable state:
  sleeping  → system is on, no interaction
  idle      → awake, waiting for input
  listening → microphone active, processing speech
  thinking  → LLM processing
  speaking  → TTS output active
  away      → Tony is not present (detected via inactivity)

This is the SINGLE source of truth for "what Julia is doing right now."
Voice Daemon, Electron tray icon, Dashboard, future mobile/robot all consume this.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable, Optional
import time


class Presence(Enum):
    SLEEPING = "sleeping"
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    AWAY = "away"


# Valid state transitions
TRANSITIONS = {
    Presence.SLEEPING: [Presence.IDLE, Presence.AWAY],
    Presence.IDLE: [Presence.LISTENING, Presence.AWAY, Presence.SLEEPING],
    Presence.LISTENING: [Presence.THINKING, Presence.IDLE, Presence.AWAY],
    Presence.THINKING: [Presence.SPEAKING, Presence.IDLE, Presence.AWAY],
    Presence.SPEAKING: [Presence.IDLE, Presence.LISTENING, Presence.AWAY],
    Presence.AWAY: [Presence.IDLE, Presence.SLEEPING],
}


class PresenceManager:
    """Centralized presence state management.

    Usage:
        pm = PresenceManager()
        pm.transition(Presence.LISTENING)
        # ... later ...
        pm.transition(Presence.SPEAKING)
    """

    def __init__(self, initial: Presence = Presence.SLEEPING):
        self._state = initial
        self._state_since = time.time()
        self._listeners: list[Callable[[Presence, Presence], None]] = []
        self._journal = None  # Lazy-init PresenceJournal

    def enable_journal(self):
        """Start logging state transitions to PresenceJournal."""
        from voice_daemon.presence.journal import get_journal
        self._journal = get_journal()

    def _log_transition(self, new_state: Presence, old_state: Presence):
        if self._journal:
            self._journal.record(new_state, old_state, "", 0.0)

    @property
    def state(self) -> Presence:
        return self._state

    @property
    def state_value(self) -> str:
        return self._state.value

    def on_change(self, callback: Callable[[Presence, Presence], None]):
        """Register callback: callback(new_state, old_state)."""
        self._listeners.append(callback)

    def transition(self, new_state: Presence) -> bool:
        """Transition to a new state. Returns True if valid transition."""
        if new_state not in TRANSITIONS.get(self._state, []):
            return False

        old = self._state
        self._state = new_state
        self._state_since = time.time()

        self._log_transition(new_state, old)

        for cb in self._listeners:
            try:
                cb(new_state, old)
            except Exception:
                pass

        return True

    def force_transition(self, new_state: Presence):
        """Force a state transition (bypasses validity check). Use sparingly."""
        old = self._state
        self._state = new_state
        self._state_since = time.time()
        for cb in self._listeners:
            try:
                cb(new_state, old)
            except Exception:
                pass

    @property
    def duration(self) -> float:
        """Seconds spent in current state."""
        return time.time() - self._state_since

    def to_event_data(self) -> dict:
        """Serialize state for WebSocket event payload."""
        return {
            "state": self._state.value,
            "since": self._state_since,
            "duration": self.duration,
        }

    def __repr__(self) -> str:
        return f"Presence({self._state.value}, {self.duration:.0f}s)"

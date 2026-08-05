"""Presence State Machine — fine-grained cognitive states for E3.

States: IDLE → LISTENING → RECALLING → REASONING → GENERATING → SPEAKING
Each transition emits a presence event. Clients render based on state.
"""

from __future__ import annotations
from enum import Enum
from typing import Callable, Optional
import time as _time


class PresenceState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    RECALLING = "recalling"
    REASONING = "reasoning"
    GENERATING = "generating"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"


class PresenceMachine:
    """Tracks Julia's real-time presence. Emits on every transition."""

    def __init__(self):
        self.state = PresenceState.IDLE
        self.previous: Optional[PresenceState] = None
        self._listeners: list[Callable] = []
        self.interrupted = False  # Persistent flag for background task cancellation

    def on_change(self, callback: Callable):
        self._listeners.append(callback)

    def transition(self, new_state: PresenceState) -> dict:
        self.previous = self.state
        self.state = new_state
        event = {
            "type": "presence.changed",
            "data": {"state": new_state.value, "previous": self.previous.value},
            "timestamp": _time.strftime("%H:%M:%S"),
        }
        for cb in self._listeners:
            try: cb(new_state, self.previous)
            except Exception: pass
        return event

    def is_interruptible(self) -> bool:
        return self.state in (PresenceState.SPEAKING, PresenceState.GENERATING,
                              PresenceState.RECALLING, PresenceState.REASONING)

    @property
    def is_active(self) -> bool:
        return self.state not in (PresenceState.IDLE, PresenceState.INTERRUPTED)


_machine: Optional[PresenceMachine] = None

def get_presence() -> PresenceMachine:
    global _machine
    if _machine is None:
        _machine = PresenceMachine()
    return _machine

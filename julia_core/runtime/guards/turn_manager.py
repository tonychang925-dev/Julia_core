"""Voice Turn Manager — tracks who is speaking.

E3.6 Architecture Freeze:
  - Tracks Julia's speech state (idle/speaking)
  - Detects interrupts (user speaks while Julia is speaking)
  - NO text-based echo detection (that's AEC's job in audio layer)
  - NO cooldown windows
  - NO text similarity matching
"""

from __future__ import annotations

import time as _time
from enum import Enum


class InputClass(Enum):
    NEW_TURN = "new_turn"
    INTERRUPT = "interrupt"


class VoiceTurnManager:
    """Tracks speaking state. Does NOT do echo detection."""

    def __init__(self):
        self._state = "idle"                     # idle | speaking
        self._speech_started_at: float = 0.0
        self._active_speech_id: str = ""
        self._suppressed_count = 0
        self._interrupt_count = 0

    # ── Julia Speech Events ──────────────────────────────────────────────

    def julia_started_speaking(self, speech_id: str = ""):
        self._state = "speaking"
        self._speech_started_at = _time.time()
        self._active_speech_id = speech_id

    def julia_speech_chunk(self, text: str):
        pass  # No-op in freeze — no echo matching

    def julia_stopped_speaking(self):
        self._state = "idle"
        self._active_speech_id = ""

    # ── Input Classification ─────────────────────────────────────────────

    def classify(self, text: str) -> InputClass:
        """Classify incoming user input based on Julia's speaking state."""
        if not text:
            return InputClass.NEW_TURN
        if self._state == "speaking":
            self._interrupt_count += 1
            return InputClass.INTERRUPT
        return InputClass.NEW_TURN

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def is_speaking(self) -> bool:
        return self._state == "speaking"

    @property
    def suppressed(self) -> int:
        return self._suppressed_count

    @property
    def interrupts(self) -> int:
        return self._interrupt_count


# ── Singleton ─────────────────────────────────────────────────────────────

_manager: VoiceTurnManager | None = None


def get_turn_manager() -> VoiceTurnManager:
    global _manager
    if _manager is None:
        _manager = VoiceTurnManager()
    return _manager

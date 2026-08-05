"""Voice Turn Ownership Manager — E3.5.2.

Replaces standalone EchoFilter with stateful turn awareness.

Core question: "Whose turn is it to speak?"
Not: "Does this text look like what Julia just said?"

State machine:
  IDLE → SPEAKING (Julia starts replying)
  SPEAKING → IDLE (Julia finishes)
  SPEAKING → INTERRUPTED (Tony interrupts, text doesn't match Julia's speech)

When input arrives during SPEAKING:
  - text ≈ Julia's recent speech → ECHO, drop silently
  - text ≠ Julia's speech → INTERRUPT, cancel speech, process as new turn
"""

from __future__ import annotations

import difflib
import re
import time as _time
from collections import deque
from enum import Enum


class InputClass(Enum):
    NEW_TURN = "new_turn"       # Julia is idle, process normally
    ECHO = "echo"               # Julia is speaking, input matches her speech
    INTERRUPT = "interrupt"     # Julia is speaking, input is new user speech


class VoiceTurnManager:
    """Knows whose turn it is. One instance per Gateway (singleton-safe)."""

    def __init__(self, echo_threshold: float = 0.5, cooldown_s: float = 3.0):
        self._state = "idle"                     # idle | speaking | cooldown
        self._speech_started_at: float = 0.0
        self._speech_ended_at: float = 0.0
        self._active_speech_id: str = ""
        self._speech_texts: deque[str] = deque(maxlen=8)  # recent chunks
        self._echo_threshold = echo_threshold
        self._cooldown_s = cooldown_s  # after speech ends, keep echo detection alive
        self._suppressed_count = 0
        self._interrupt_count = 0

    # ── Julia Speech Events ───────────────────────────────────────────────

    def julia_started_speaking(self, speech_id: str = ""):
        """Called when Julia begins a speech turn (speech.request sent)."""
        self._state = "speaking"
        self._speech_started_at = _time.time()
        self._active_speech_id = speech_id

    def julia_speech_chunk(self, text: str):
        """Called for each speech.chunk sent. Records text for echo comparison."""
        if text:
            self._speech_texts.append(text)

    def julia_stopped_speaking(self):
        """Called when speech.completed/speech.cancelled is SENT.

        Note: TTS audio may still be playing on the client for 1-3 seconds.
        We enter COOLDOWN (not IDLE) to catch echo from delayed ASR.
        """
        self._state = "cooldown"
        self._speech_ended_at = _time.time()
        self._active_speech_id = ""

    # ── Input Classification ──────────────────────────────────────────────

    def classify(self, text: str) -> InputClass:
        """Classify incoming user text.

        Returns:
          NEW_TURN  — Julia is idle, process normally
          ECHO      — text matches Julia's recent speech (during speaking or cooldown)
          INTERRUPT — Julia is speaking, text is new user input → cancel + process
        """
        if not text:
            return InputClass.NEW_TURN

        # Cooldown: speech.completed sent, but TTS still playing on client.
        # ASR may pick up echo with 1-3s delay. Check for echo, but don't allow interrupt.
        if self._state == "cooldown":
            if _time.time() - self._speech_ended_at > self._cooldown_s:
                self._state = "idle"
                return InputClass.NEW_TURN
            if self._matches_recent_speech(text):
                self._suppressed_count += 1
                return InputClass.ECHO
            # During cooldown, non-echo voice input is suspicious
            # (Julia's TTS is still playing). Gate it but don't drop it.
            return InputClass.NEW_TURN

        # Idle → always a new turn
        if self._state == "idle":
            return InputClass.NEW_TURN

        # Speaking. Check if this is echo or interrupt.
        if self._matches_recent_speech(text):
            self._suppressed_count += 1
            return InputClass.ECHO

        self._interrupt_count += 1
        return InputClass.INTERRUPT

    # ── Internal ──────────────────────────────────────────────────────────

    def _matches_recent_speech(self, text: str) -> bool:
        """Check if text is likely echo of Julia's recent speech."""
        t_norm = self._normalize(text)
        if len(t_norm) < 2:
            return False

        for recent in self._speech_texts:
            r_norm = self._normalize(recent)
            # Compare against prefix — ASR only catches first part of TTS
            prefix_len = min(len(r_norm), max(len(t_norm), 6) * 2)
            prefix = r_norm[:prefix_len]
            if self._similarity(prefix, t_norm) >= self._echo_threshold:
                return True

        return False

    @staticmethod
    def _normalize(text: str) -> str:
        text = re.sub(r'[（(][^)）]*[)）]', '', text)
        text = re.sub(r'[^\u4e00-\u9fff\w]', '', text)
        return text.lower().strip()

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        return difflib.SequenceMatcher(None, a, b).ratio()

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def is_speaking(self) -> bool:
        return self._state == "speaking"

    @property
    def in_cooldown(self) -> bool:
        return self._state == "cooldown"

    @property
    def suppressed(self) -> int:
        return self._suppressed_count

    @property
    def interrupts(self) -> int:
        return self._interrupt_count

    @property
    def state(self) -> str:
        return self._state


# ── Singleton ─────────────────────────────────────────────────────────────

_manager: VoiceTurnManager | None = None


def get_turn_manager() -> VoiceTurnManager:
    global _manager
    if _manager is None:
        _manager = VoiceTurnManager()
    return _manager

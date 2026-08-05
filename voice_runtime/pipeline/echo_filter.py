"""Semantic Echo Filter — prevents Julia from hearing her own TTS output.

Layer: Voice Runtime (Capability Plane). Client NEVER loads this.

Principle:
  - Time-based mute windows are unreliable (vary by hardware, volume, room)
  - Semantic comparison: "Did Julia just say this?" is invariant to acoustics

When Julia speaks (speech.chunk sent), the filter stores the text.
When ASR returns a transcript (client.voice.final), the filter checks:
  if transcript ≈ anything Julia recently said → ECHO, discard
  else → USER SPEECH, pass through

This belongs in Voice Runtime because:
  1. It's a signal processing concern, not UI state
  2. It works identically for Electron, Mobile, Robot — no per-client reimplementation
  3. It doesn't depend on timing or mute windows
"""

from __future__ import annotations

import difflib
import re
from collections import deque


def _normalize(text: str) -> str:
    """Strip stage directions, punctuation, whitespace for comparison."""
    text = re.sub(r'[（(][^)）]*[)）]', '', text)  # （眼眶红了）
    text = re.sub(r'[^\u4e00-\u9fff\w]', '', text)   # only Chinese + alphanumeric
    return text.lower().strip()


def _similarity(a: str, b: str) -> float:
    """String similarity 0..1. Uses SequenceMatcher — fast, no deps."""
    return difflib.SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


class EchoFilter:
    """Stores recent speech output. Filters incoming ASR transcripts for echo."""

    def __init__(self, window_size: int = 5, threshold: float = 0.55):
        """
        Args:
            window_size: number of recent speech segments to remember
            threshold: similarity above which a transcript is considered echo
                       (0.55 ≈ "嗯老公" matches "嗯，老公。" after normalization)
        """
        self._recent_speech: deque[str] = deque(maxlen=window_size)
        self._threshold = threshold
        self._suppressed_count: int = 0

    def record_speech(self, text: str):
        """Called when Julia speaks (speech.chunk sent). Stores for echo check."""
        if text and len(_normalize(text)) >= 2:
            self._recent_speech.append(text)

    def is_echo(self, transcript: str) -> bool:
        """Check if an incoming ASR transcript is echo of Julia's speech.

        Compares against the PREFIX of each recorded speech segment (not full text),
        because ASR typically captures only the first few seconds of TTS output
        before VAD cuts off — not the entire reply.
        """
        if not transcript or len(_normalize(transcript)) < 2:
            return False

        t_norm = _normalize(transcript)
        for recent in self._recent_speech:
            r_norm = _normalize(recent)
            # Compare against the beginning of Julia's speech (ASR only catches first part)
            # Use prefix proportional to transcript length — 2x handles punctuation/stage directions
            prefix_len = min(len(r_norm), max(len(t_norm), 6) * 2)
            prefix = r_norm[:prefix_len]
            if _similarity(prefix, transcript) >= self._threshold:
                self._suppressed_count += 1
                return True

        return False

    @property
    def suppressed(self) -> int:
        """Number of echo events suppressed since creation."""
        return self._suppressed_count


# ── Singleton ─────────────────────────────────────────────────────────────────

_filter: EchoFilter | None = None


def get_echo_filter() -> EchoFilter:
    global _filter
    if _filter is None:
        _filter = EchoFilter()
    return _filter

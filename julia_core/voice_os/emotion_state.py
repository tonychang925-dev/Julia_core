"""Layer 1: Cognitive Emotion State.

Julia Runtime decides emotional state. TTS does not own this.
This is a cognitive layer, not a voice parameter layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EmotionState(str, Enum):
    NEUTRAL = "neutral"
    WARM = "warm"
    THINKING = "thinking"
    CONFIDENT = "confident"
    EXCITED = "excited"
    SOFT = "soft"
    CONCERNED = "concerned"
    PLAYFUL = "playful"


@dataclass(frozen=True, slots=True)
class CognitiveEmotion:
    """Julia's current emotional intent — cognitive, not acoustic."""
    state: EmotionState = EmotionState.WARM
    intensity: float = 0.7  # 0.0-1.0

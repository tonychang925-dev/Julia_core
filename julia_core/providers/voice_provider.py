"""VoiceProvider protocol — Core abstraction for speech synthesis.

Voice OS owns emotion + prosody. VoiceProviders only render audio.
"""
from typing import Protocol, runtime_checkable

from julia_core.voice_os.emotion_state import CognitiveEmotion
from julia_core.voice_os.prosody import SpeechMetadata


@runtime_checkable
class VoiceProvider(Protocol):
    """Render text → audio. Does NOT own emotion, persona, or prosody planning."""

    provider_id: str

    def speak(self, text: str, *, emotion: CognitiveEmotion | None = None, metadata: SpeechMetadata | None = None) -> bool:
        """Synthesize and play audio. Returns True on success."""
        ...

    def synthesize(self, text: str, *, emotion: CognitiveEmotion | None = None, metadata: SpeechMetadata | None = None) -> bytes | None:
        """Synthesize audio, return raw bytes. Returns None on failure."""
        ...

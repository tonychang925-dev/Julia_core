"""Julia Voice Service.

The service binds VoiceProfile → TTSProvider. It returns audio bytes and trace.
It does not mutate Persona, Identity, Memory, Continuity, Context, or Evidence.
"""

from __future__ import annotations

from .edge_tts_provider import EdgeTTSProvider
from .tts_adapter import TTSProvider, TTSRequest, TTSResult
from .voice_profile import VoiceProfile, default_julia_voice_profile


class VoiceService:
    def __init__(self, provider: TTSProvider | None = None, profile: VoiceProfile | None = None) -> None:
        self.provider = provider or EdgeTTSProvider()
        self.profile = profile or default_julia_voice_profile()

    def synthesize(self, text: str, profile: VoiceProfile | None = None) -> TTSResult:
        selected = profile or self.profile
        return self.provider.synthesize(TTSRequest(text=text, profile=selected))

    def profile_trace(self) -> dict:
        return {
            "voice_profile": self.profile.to_dict(),
            "boundary": self.profile.boundary_trace(),
        }


    def fallback_trace(self, error: str | None = None) -> dict:
        return {
            "voice": {
                "provider": "browser_fallback",
                "status": "DEGRADED",
                "primary_provider": self.profile.provider,
                "primary_voice": self.profile.voice,
                "error": error,
            },
            "boundary": {
                "voice_owns_identity": False,
                "voice_writes_memory": False,
                "voice_mutates_persona": False,
            },
        }

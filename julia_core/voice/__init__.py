"""Julia Voice Service layer.

Voice is an interaction/output layer. It does not own Identity, Persona, Memory,
Continuity, Context, Evidence, or Provider reasoning.
"""

from .voice_profile import VoiceProfile, default_julia_voice_profile, load_voice_artifact
from .tts_adapter import TTSRequest, TTSResult, TTSProvider
from .edge_tts_provider import EdgeTTSProvider
from .voice_service import VoiceService

__all__ = [
    "VoiceProfile",
    "default_julia_voice_profile",
    "load_voice_artifact",
    "TTSRequest",
    "TTSResult",
    "TTSProvider",
    "EdgeTTSProvider",
    "VoiceService",
]

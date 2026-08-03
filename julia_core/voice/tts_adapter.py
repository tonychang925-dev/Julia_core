"""TTS adapter protocol for Julia Voice Service."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol, runtime_checkable

from .voice_profile import VoiceProfile


@dataclass(frozen=True, slots=True)
class TTSRequest:
    text: str
    profile: VoiceProfile

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("text is required")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["profile"] = self.profile.to_dict()
        return data


@dataclass(frozen=True, slots=True)
class TTSResult:
    ok: bool
    audio: bytes
    media_type: str
    provider: str
    voice: str
    error: str | None = None

    def trace(self) -> dict[str, Any]:
        return {
            "voice": {
                "provider": self.provider,
                "voice": self.voice,
                "media_type": self.media_type,
                "ok": self.ok,
                "error": self.error,
                "audio_bytes": len(self.audio),
            },
            "boundary": {
                "voice_owns_identity": False,
                "voice_writes_memory": False,
                "voice_mutates_persona": False,
            },
        }


@runtime_checkable
class TTSProvider(Protocol):
    provider_id: str

    def synthesize(self, request: TTSRequest) -> TTSResult:
        ...

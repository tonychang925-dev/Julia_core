"""Voice profile contract for Julia Human Interface.

A VoiceProfile is an expression preference, not an Identity authority object.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class VoiceProfile:
    voice_id: str
    provider: str
    engine: str
    voice: str
    rate: str = "0%"
    pitch: str = "0Hz"
    volume: str = "+0%"
    audio_format: str = "audio/mpeg"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def boundary_trace(self) -> dict[str, bool]:
        return {
            "voice_owns_identity": False,
            "voice_writes_memory": False,
            "voice_mutates_persona": False,
            "voice_mutates_continuity": False,
        }


def default_julia_voice_profile() -> VoiceProfile:
    artifact = load_voice_artifact()
    parameters = dict(artifact.get("parameters", {}))
    return VoiceProfile(
        voice_id=f"{artifact.get('artifact_id', 'julia.voice')}.{artifact.get('version', 'v1')}",
        provider=str(artifact.get("provider", "edge_tts")),
        engine=str(artifact.get("engine", "neural")),
        voice=os.environ.get("JULIA_TTS_VOICE", str(artifact.get("voice", "zh-CN-XiaoxiaoNeural"))),
        rate=os.environ.get("JULIA_TTS_RATE", str(parameters.get("rate", "0%"))),
        pitch=os.environ.get("JULIA_TTS_PITCH", str(parameters.get("pitch", "0Hz"))),
        volume=os.environ.get("JULIA_TTS_VOLUME", str(parameters.get("volume", "+0%"))),
    )


def load_voice_artifact(path: str | Path | None = None) -> dict[str, Any]:
    selected = Path(path) if path is not None else Path(__file__).resolve().parents[2] / "artifacts" / "voice" / "julia_voice_v1.json"
    if not selected.exists():
        return {
            "artifact_id": "julia.voice",
            "version": "v1",
            "provider": "edge_tts",
            "engine": "neural",
            "voice": "zh-CN-XiaoxiaoNeural",
            "parameters": {"rate": "0%", "pitch": "0Hz", "volume": "+0%"},
        }
    return json.loads(selected.read_text(encoding="utf-8"))

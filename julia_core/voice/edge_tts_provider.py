"""Edge TTS provider for Julia Voice Service.

Migrated from the previous julia_agent Edge TTS style into Julia Core's Voice
Service boundary. Edge TTS renders audio only; it does not own Julia identity.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from .tts_adapter import TTSRequest, TTSResult


class EdgeTTSProvider:
    provider_id = "edge_tts"

    def synthesize(self, request: TTSRequest) -> TTSResult:
        try:
            audio = self._synthesize_edge(request)
            return TTSResult(
                ok=True,
                audio=audio,
                media_type=request.profile.audio_format,
                provider=request.profile.provider,
                voice=request.profile.voice,
            )
        except Exception as exc:  # pragma: no cover - depends on optional edge_tts/network
            return TTSResult(
                ok=False,
                audio=b"",
                media_type=request.profile.audio_format,
                provider=request.profile.provider,
                voice=request.profile.voice,
                error=str(exc),
            )

    def _synthesize_edge(self, request: TTSRequest) -> bytes:
        import edge_tts

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp:
            path = Path(temp.name)
        async def _run() -> None:
            communicate = edge_tts.Communicate(
                request.text,
                request.profile.voice,
                rate=request.profile.rate,
                pitch=request.profile.pitch,
                volume=request.profile.volume,
            )
            await communicate.save(str(path))
        try:
            asyncio.run(_run())
            return path.read_bytes()
        finally:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass

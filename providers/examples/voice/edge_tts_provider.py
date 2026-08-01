"""Edge TTS Voice Provider — free, no quota, Chinese voices.

This demonstrates the VoiceProvider protocol:
  1. Implement speak() and synthesize()
  2. Register with Core
  3. Core owns emotion + prosody. Provider only renders audio.
"""
import os
import subprocess
import tempfile

from julia_core.providers.voice_provider import VoiceProvider
from julia_core.voice_os.emotion_state import CognitiveEmotion
from julia_core.voice_os.prosody import SpeechMetadata


class EdgeTTSVoiceProvider:
    """Free Microsoft Edge TTS — zh-TW-HsiaoChenNeural (Taiwan Mandarin)."""

    provider_id = "voice-edge-tts-v1"
    _voice = os.environ.get("JULIA_TTS_VOICE", "zh-TW-HsiaoChenNeural")
    _rate = os.environ.get("JULIA_TTS_RATE", "-5%")
    _pitch = os.environ.get("JULIA_TTS_PITCH", "-3Hz")

    def speak(self, text: str, *, emotion: CognitiveEmotion | None = None, metadata: SpeechMetadata | None = None) -> bool:
        audio = self.synthesize(text, emotion=emotion, metadata=metadata)
        if not audio:
            return False
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio)
            tmp_path = f.name
        subprocess.run(["afplay", tmp_path], timeout=120)
        os.unlink(tmp_path)
        return True

    def synthesize(self, text: str, *, emotion: CognitiveEmotion | None = None, metadata: SpeechMetadata | None = None) -> bytes | None:
        import asyncio
        import edge_tts

        rate = self._rate
        pitch = self._pitch
        if metadata:
            rate_pct = round((metadata.speed - 1.0) * 100)
            rate = f"{rate_pct:+d}%"
            pitch = metadata.pitch_shift

        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name
            async def _run():
                communicate = edge_tts.Communicate(text, self._voice, rate=rate, pitch=pitch)
                await communicate.save(tmp_path)
            asyncio.run(_run())
            with open(tmp_path, "rb") as f:
                data = f.read()
            os.unlink(tmp_path)
            return data
        except Exception:
            return None

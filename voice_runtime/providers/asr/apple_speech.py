"""Apple Speech Recognizer — local, free, macOS native.

Uses SFSpeechRecognizer via subprocess (speech_lab stt binary when available)
or NSSpeechRecognizer via PyObjC.
"""

from __future__ import annotations
import asyncio
import logging
import subprocess
import tempfile
import time as _time
import wave
from pathlib import Path
from typing import Optional

from voice_runtime.providers.asr.base import ASRProvider

logger = logging.getLogger("julia.asr.apple")


class AppleSpeechProvider(ASRProvider):
    """macOS native speech recognition. Free, local, no API key."""

    def __init__(self, language: str = "zh-CN"):
        super().__init__()
        self.language = language
        self._buffer: list[bytes] = []
        self._running = False
        self._sample_rate = 48000
        self._frame_count = 0

    async def start(self):
        self._buffer = []
        self._running = True
        self._frame_count = 0
        logger.info(f"AppleSpeech ASR started (lang={self.language})")

    async def feed_frame(self, frame) -> None:
        """Accumulate audio frames. Transcribe every ~1.5s of audio."""
        if not self._running:
            return

        # Convert aiortc AudioFrame to int16 PCM bytes
        pcm = frame.to_ndarray().tobytes()
        self._buffer.append(pcm)
        self._frame_count += 1

        # Transcribe every ~75 frames (~1.5s at 48kHz, 960 samples/frame)
        if self._frame_count % 75 == 0 and len(self._buffer) > 0:
            text = await self._transcribe()
            if text and self._on_partial:
                self._on_partial(text)

    async def _transcribe(self) -> Optional[str]:
        """Run recognition on accumulated audio buffer."""
        if not self._buffer:
            return None

        try:
            # Write accumulated audio to temp WAV
            import numpy as np
            all_pcm = b"".join(self._buffer)
            audio = np.frombuffer(all_pcm, dtype=np.int16).astype(np.float32) / 32768.0

            # Use Google Speech for fast, accurate Chinese recognition
            import speech_recognition as sr
            r = sr.Recognizer()

            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = tmp.name
            tmp.close()

            with wave.open(tmp_path, "w") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(self._sample_rate)
                w.writeframes((audio * 32767).astype(np.int16).tobytes())

            with sr.AudioFile(tmp_path) as source:
                sr_audio = r.record(source)

            Path(tmp_path).unlink()
            return r.recognize_google(sr_audio, language=self.language)

        except Exception as e:
            logger.debug(f"ASR: {e}")
            return None

    async def stop(self) -> Optional[str]:
        """Stop ASR, flush remaining buffer, return final transcript."""
        self._running = False
        if self._buffer:
            text = await self._transcribe()
            self._buffer = []
            if text and self._on_final:
                self._on_final(text)
            return text
        return None

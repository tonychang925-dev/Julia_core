"""ElevenLabs TTS Client — Julia's voice.

Renders Julia's text responses as speech through ElevenLabs API.
Uses emotion tags for expressive voice: [warm], [soft], [sad], [excited], [thoughtful].

This is the BODY layer — Runtime says WHAT to say, Voice Daemon decides HOW it sounds.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import urllib.request
from typing import Optional


class ElevenLabsTTS:
    """ElevenLabs Text-to-Speech client.

    Converts text → audio bytes → speaker.
    Runtime produces speech events, Voice Daemon renders them.
    """

    # Emotion → stability mapping
    EMOTION_STABILITY = {
        "warm": 0.45, "soft": 0.55, "sad": 0.65,
        "excited": 0.30, "thoughtful": 0.50,
        "whisper": 0.70, "cry": 0.60, "laugh": 0.35, "sigh": 0.75,
    }

    def __init__(self, api_key: str = None, voice_id: str = None):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
        self.voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID", "tOuLUAIdXShmWH7PEUrU")
        self.model = "eleven_multilingual_v2"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def extract_emotion(text: str) -> tuple[str, str]:
        """Extract emotion tag from text. Returns (emotion, clean_text)."""
        match = re.match(r'^\[(warm|soft|sad|excited|thoughtful|whisper|cry|laugh|sigh)\]\s*', text)
        if match:
            return match.group(1), text[match.end():]
        return "warm", text

    def speak(self, text: str, emotion: str = "warm") -> bool:
        """Render text as speech and play through speakers. Blocks until done."""
        if not self.api_key:
            return False

        audio = self.synthesize(text, emotion)
        if not audio:
            return False

        return self._play(audio)

    def synthesize(self, text: str, emotion: str = "warm") -> Optional[bytes]:
        """Convert text to audio bytes via ElevenLabs API."""
        if not self.api_key or not text:
            return None

        stability = self.EMOTION_STABILITY.get(emotion, 0.50)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        body = json.dumps({
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": 0.75,
            },
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except Exception:
            return None

    def _play(self, audio: bytes) -> bool:
        """Play audio bytes through Mac speakers."""
        if not audio:
            return False
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio)
                tmp_path = f.name
            subprocess.run(["afplay", tmp_path], timeout=120, check=True)
            os.unlink(tmp_path)
            return True
        except Exception:
            return False

    def speak_async(self, text: str, emotion: str = "warm"):
        """Render and play TTS in background thread."""
        import threading
        threading.Thread(
            target=self.speak, args=(text, emotion), daemon=True
        ).start()

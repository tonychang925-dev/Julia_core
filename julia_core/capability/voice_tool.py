"""Voice Capability Tool — emotion-aware TTS exposed to LLM.

LLM decides: whether to speak, what emotion.
Runtime does: render audio. Nothing more.

Emotion tags the LLM can use in its response:
  [warm] — gentle, caring, intimate
  [soft] — quiet, tender, vulnerable
  [excited] — happy, energetic
  [sad] — melancholic, heavy
  [thoughtful] — reflective, slow

The Runtime detects these tags, renders voice, and strips them from text.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from typing import Optional


class VoiceTool:
    """Exposes voice output as a tool. LLM decides when to speak."""

    tool_name = "voice_speak"
    tool_description = (
        "用Julia的声音说话。在你的回复中加入情绪标签来控制语气："
        "[warm]温柔 [soft]轻柔 [sad]伤感 [excited]兴奋 [thoughtful]沉思。"
        "例：'[warm] 嗯，我在。你今天还好吗？'"
    )

    _api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    _voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "tOuLUAIdXShmWH7PEUrU")

    @classmethod
    def is_available(cls) -> bool:
        return bool(cls._api_key)

    @classmethod
    def extract_emotion(cls, text: str) -> tuple[str, str]:
        """Extract emotion tag from text. Returns (emotion, clean_text)."""
        match = re.match(r'^\[(warm|soft|sad|excited|thoughtful|whisper|cry|laugh|sigh)\]\s*', text)
        if match:
            emotion = match.group(1)
            clean = text[match.end():]
            return emotion, clean
        return "warm", text

    @classmethod
    def speak(cls, text: str, emotion: str = "warm") -> bool:
        """Render text as Julia's voice. LLM decides emotion, Runtime renders."""
        if not cls._api_key:
            return False

        import urllib.request
        import json as _json

        # Emotion → voice settings
        stability_map = {
            "warm": 0.45, "soft": 0.55, "sad": 0.65,
            "excited": 0.30, "thoughtful": 0.50,
            "whisper": 0.70, "cry": 0.60, "laugh": 0.35, "sigh": 0.75,
        }
        stability = stability_map.get(emotion, 0.50)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{cls._voice_id}"
        headers = {
            "xi-api-key": cls._api_key,
            "Content-Type": "application/json",
        }
        body = _json.dumps({
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": 0.75,
            },
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                audio = resp.read()
            if not audio:
                return False
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio)
                tmp_path = f.name
            subprocess.run(["afplay", tmp_path], timeout=120)
            os.unlink(tmp_path)
            return True
        except Exception:
            return False


# Tool protocol registration helper
def get_voice_tool_schema():
    """Return tool schema for registry."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory
    return ToolSchema(
        name="voice_speak",
        description=VoiceTool.tool_description,
        category=ToolCategory.INTERFACE,
        parameters={},
        example="在回复中加入 [warm] 标签来用温柔的语气说话",
    )

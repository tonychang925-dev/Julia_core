"""Voice Capability Tool — emotion-aware TTS. LLM decides when to speak.

Provider: Microsoft Edge TTS (free, no API key needed).
Emotion mapped to Edge TTS rate/pitch parameters.

Emotion tags the LLM can use in its response:
  [warm] — gentle, caring
  [soft] — quiet, tender
  [excited] — happy, energetic
  [sad] — melancholic
  [thoughtful] — reflective
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import tempfile
from pathlib import Path

# Microsoft Edge TTS — free, high quality Chinese voice
VOICE = os.environ.get("JULIA_TTS_VOICE", "zh-CN-XiaoxiaoNeural")
RATE = os.environ.get("JULIA_TTS_RATE", "-5%")      # slightly slower = warmer
PITCH = os.environ.get("JULIA_TTS_PITCH", "+0Hz")


class VoiceTool:
    """Exposes voice output as a tool. LLM decides when to speak."""

    tool_name = "voice_speak"
    tool_description = (
        "用Julia的声音说话。在你的回复中加入情绪标签来控制语气："
        "[warm]温柔 [soft]轻柔 [sad]伤感 [excited]兴奋 [thoughtful]沉思。"
        "例：'[warm] 嗯，我在。你今天还好吗？'"
    )

    @classmethod
    def is_available(cls) -> bool:
        """Edge TTS is always available (no API key needed)."""
        try:
            import edge_tts
            return True
        except ImportError:
            return False

    @classmethod
    def extract_emotion(cls, text: str) -> tuple[str, str]:
        """Extract emotion tag from text. Returns (emotion, clean_text)."""
        match = re.match(
            r'^\[(warm|soft|sad|excited|thoughtful|whisper|cry|laugh|sigh)\]\s*', text
        )
        if match:
            emotion = match.group(1)
            clean = text[match.end():]
            return emotion, clean
        return "warm", text

    @classmethod
    def speak(cls, text: str, emotion: str = "warm") -> bool:
        """Render text as Julia's voice via Microsoft Edge TTS (free)."""
        if not text:
            return False

        # Emotion → rate/pitch mapping
        emotion_params = {
            "warm":       ("-10%", "+0Hz"),
            "soft":       ("-15%", "-2Hz"),
            "sad":        ("-20%", "-5Hz"),
            "excited":    ("+5%", "+5Hz"),
            "thoughtful": ("-12%", "+0Hz"),
            "whisper":    ("-25%", "-3Hz"),
            "cry":        ("-15%", "-5Hz"),
            "laugh":      ("+10%", "+8Hz"),
            "sigh":       ("-20%", "-5Hz"),
        }
        rate, pitch = emotion_params.get(emotion, (RATE, PITCH))

        try:
            import edge_tts

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name

            async def _speak():
                comm = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch)
                await comm.save(tmp_path)

            asyncio.run(_speak())
            subprocess.run(["afplay", tmp_path], timeout=120)
            os.unlink(tmp_path)
            return True
        except Exception:
            return False


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

"""Whisper STT Client — Julia's ears.

Connects to a GPU server running faster-whisper.
Exposed as a Capability Tool — LLM decides nothing here.
This is pure sense organ: audio → text.

Deployment:
  GPU Server:  faster-whisper --model large-v3 --port 8001
  Local fallback: openai-whisper (slower, no GPU needed)

Architecture:
  Microphone → VAD → Whisper Server → transcript → LLM
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional


class WhisperClient:
    """STT client. Talks to a faster-whisper GPU server via HTTP.

    GPU Server (Tony's AutoDL RTX 3090):
      faster-whisper large-v3 on CUDA
      Server code: /root/autodl-tmp/julia-voice-server/
      API: POST /transcribe  (multipart audio file → JSON)

    Local fallback:
      openai-whisper (no GPU needed, slower)

    Usage:
      export WHISPER_SERVER_URL="http://your-autodl-ip:8001"
    """

    tool_name = "transcribe_audio"
    tool_description = "将语音转文字。当Tony用语音输入时自动使用。返回转录文本和语言检测结果。"

    _server_url = os.environ.get("WHISPER_SERVER_URL", "http://localhost:8001")
    _local_model = os.environ.get("WHISPER_LOCAL_MODEL", "")  # "base" to use local

    @classmethod
    def is_available(cls) -> bool:
        """Check if Whisper server is reachable."""
        try:
            req = urllib.request.Request(f"{cls._server_url}/health")
            urllib.request.urlopen(req, timeout=2)
            return True
        except Exception:
            return bool(cls._local_model)

    @classmethod
    def transcribe_file(cls, audio_path: str) -> dict:
        """Transcribe an audio file. Returns {text, language, confidence, duration}."""
        path = Path(audio_path)
        if not path.exists():
            return {"error": f"文件不存在: {audio_path}"}

        # Try remote server first
        if cls._server_url != "http://localhost:8001":
            try:
                import requests
                with open(audio_path, 'rb') as f:
                    resp = requests.post(
                        f"{cls._server_url}/v1/transcribe",
                        files={"audio": f},
                        data={"language": "zh", "response_format": "json"},
                        timeout=60,
                    )
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass

        # Local fallback: use openai-whisper
        if cls._local_model:
            try:
                import whisper
                model = whisper.load_model(cls._local_model)
                result = model.transcribe(audio_path, language="zh")
                return {
                    "text": result["text"].strip(),
                    "language": result.get("language", "zh"),
                    "confidence": 0.9,
                    "segments": len(result.get("segments", [])),
                }
            except ImportError:
                return {"error": "whisper not installed. pip install openai-whisper"}
            except Exception as e:
                return {"error": str(e)}

        return {"error": "Whisper server not available. Set WHISPER_SERVER_URL or WHISPER_LOCAL_MODEL."}

    @classmethod
    def record_and_transcribe(cls, duration: int = 10) -> dict:
        """Record from microphone and transcribe."""
        import platform

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            system = platform.system()
            if system == "Darwin":
                # macOS: use sox or ffmpeg
                subprocess.run([
                    "ffmpeg", "-f", "avfoundation",
                    "-i", ":0", "-t", str(duration),
                    "-ar", "16000", "-ac", "1",
                    "-y", tmp_path,
                ], capture_output=True, timeout=duration + 5)
            else:
                # Linux: use arecord
                subprocess.run([
                    "arecord", "-d", str(duration),
                    "-f", "cd", "-r", "16000",
                    tmp_path,
                ], capture_output=True, timeout=duration + 5)

            result = cls.transcribe_file(tmp_path)
            os.unlink(tmp_path)
            return result
        except Exception as e:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return {"error": str(e)}


# ── Voice Session ───────────────────────────────────────────────────────────

class VoiceSession:
    """Manages a continuous voice interaction loop.

    Architecture:
      VAD detects speech → record → Whisper → LLM → TTS → speak

    This is NOT a state machine. It's an I/O loop.
    All understanding happens in the LLM.
    """

    @staticmethod
    def speak(text: str) -> bool:
        """Text-to-speech via ElevenLabs."""
        from julia_core.capability.voice_tool import VoiceTool
        return VoiceTool.speak(text)

    @staticmethod
    def listen(timeout: int = 10) -> Optional[str]:
        """Listen for speech and return transcript."""
        result = WhisperClient.record_and_transcribe(timeout)
        if "error" in result:
            return None
        return result.get("text", "").strip()


# ── Tool Registration ───────────────────────────────────────────────────────

def register_whisper_tool(registry):
    """Register Whisper STT as a capability tool."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    is_available = WhisperClient.is_available()

    registry.register(
        ToolSchema(
            name="transcribe_audio",
            description=WhisperClient.tool_description + (" (已连接)" if is_available else " (未连接)"),
            category=ToolCategory.INTERFACE,
            parameters={"audio_path": "音频文件路径（可选，不填则从麦克风录音）"},
            example="transcribe_audio(audio_path='/tmp/recording.wav')",
        ),
        lambda audio_path=None: (
            WhisperClient.record_and_transcribe()
            if audio_path is None
            else WhisperClient.transcribe_file(audio_path)
        ),
    )

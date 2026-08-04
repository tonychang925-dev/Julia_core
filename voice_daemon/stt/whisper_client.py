"""Whisper STT Client — Julia's ears.

Talks to GPU Whisper server (Tony's AutoDL RTX 3090) via HTTP.
Uses subprocess+curl for reliability (Python requests incompatible with uvicorn server).

This is a thin wrapper — no intelligence, just audio → text.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional


class WhisperClient:
    """STT client. Talks to faster-whisper GPU server via HTTP.

    GPU Server (Tony's AutoDL RTX 3090):
      faster-whisper large-v3 on CUDA
      API: POST /v1/transcribe (multipart audio file → JSON)

    Usage:
      export WHISPER_SERVER_URL="http://your-autodl-ip:8001"
    """

    def __init__(self, server_url: str = None, language: str = "zh",
                 beam_size: int = 5, timeout: int = 60):
        self.server_url = server_url or os.environ.get("WHISPER_SERVER_URL", "http://localhost:8001")
        self.language = language
        self.beam_size = beam_size
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if Whisper server is reachable."""
        try:
            result = subprocess.run([
                "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                f"{self.server_url}/health",
                "--max-time", "3",
            ], capture_output=True, text=True, timeout=5)
            return result.stdout.strip() == "200"
        except Exception:
            return False

    def transcribe_file(self, audio_path: str) -> dict:
        """Transcribe an audio file. Returns {text, language, confidence}."""
        path = Path(audio_path)
        if not path.exists():
            return {"error": f"File not found: {audio_path}"}

        try:
            result = subprocess.run([
                "curl", "-s", "-X", "POST",
                f"{self.server_url}/v1/transcribe",
                "-F", f"audio=@{audio_path}",
                "-F", f"language={self.language}",
                "-F", f"beam_size={self.beam_size}",
                "--max-time", str(self.timeout),
            ], capture_output=True, text=True, timeout=self.timeout + 5)

            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                return {
                    "text": data.get("text", "").strip(),
                    "language": data.get("language", self.language),
                    "confidence": data.get("language_probability", 0.9),
                }
        except subprocess.TimeoutExpired:
            return {"error": f"Whisper server timeout after {self.timeout}s"}
        except Exception as e:
            return {"error": str(e)}

        return {"error": "Whisper server not reachable"}

    def transcribe_bytes(self, audio_data: bytes, suffix: str = ".wav") -> dict:
        """Transcribe raw audio bytes. Saves to temp file, transcribes, cleans up."""
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        try:
            tmp.write(audio_data)
            tmp.close()
            return self.transcribe_file(tmp.name)
        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

    def record_and_transcribe(self, duration: int = 8) -> dict:
        """Record from Mac microphone and transcribe."""
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            subprocess.run([
                "ffmpeg", "-f", "avfoundation",
                "-i", ":0", "-t", str(duration),
                "-ar", "16000", "-ac", "1",
                "-y", tmp_path,
            ], capture_output=True, timeout=duration + 5)

            result = self.transcribe_file(tmp_path)
            return result
        except subprocess.TimeoutExpired:
            return {"error": "Recording timed out"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass

    def ping(self) -> float:
        """Measure round-trip latency to Whisper server. Returns seconds."""
        t0 = time.time()
        self.is_available()
        return time.time() - t0

"""Julia Voice Loop v1.0 — real-time voice interaction.

Architecture:
  Mac mic → ffmpeg record → GPU server STT → Julia LLM → ElevenLabs TTS → speaker

Usage:
  WHISPER_SERVER_URL=http://localhost:8001  (SSH tunnel to AutoDL)
  python voice_loop.py

Tony's GPU server handles STT. Local Mac handles recording + TTS + LLM.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

SERVER_URL = os.environ.get("WHISPER_SERVER_URL", "http://localhost:8001")


def record_audio(duration: int = 8, output_path: str = None) -> str:
    """Record audio from Mac microphone using ffmpeg."""
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_path = tmp.name
        tmp.close()

    subprocess.run([
        "ffmpeg", "-f", "avfoundation",
        "-i", ":0", "-t", str(duration),
        "-ar", "16000", "-ac", "1",
        "-y", output_path,
    ], capture_output=True, timeout=duration + 5)

    return output_path


def transcribe(audio_path: str) -> dict:
    """Send audio to GPU server for STT. Uses curl for reliability."""
    import subprocess, json
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        f"{SERVER_URL}/v1/transcribe",
        "-F", f"audio=@{audio_path}",
        "-F", "language=zh",
        "-F", "beam_size=5",
        "--max-time", "60",
    ], capture_output=True, text=True, timeout=65)
    if result.returncode == 0 and result.stdout.strip():
        data = json.loads(result.stdout)
        return {
            "text": data.get("text", "").strip(),
            "language": data.get("language", "zh"),
            "confidence": data.get("language_probability", 0.9),
        }
    return {"error": f"Server error: {result.returncode}"}


def voice_chat(llm_chat_fn) -> str:
    """Full voice loop: record → transcribe → LLM → speak.

    Args:
        llm_chat_fn: function(text) -> reply_text
    Returns:
        Julia's text response (audio also played)
    """
    import threading

    # 1. Record
    audio_path = record_audio(duration=8)
    if not Path(audio_path).exists():
        return "录音失败"

    # 2. Transcribe (GPU server)
    result = transcribe(audio_path)
    os.unlink(audio_path)

    if "error" in result:
        return f"识别失败: {result['error']}"

    text = result.get("text", "").strip()
    if not text:
        return "(静音)"

    print(f"  🎤 Tony: {text}")

    # 3. LLM
    reply = llm_chat_fn(text)

    # 4. TTS (background)
    try:
        from julia_core.capability.voice_tool import VoiceTool
        if VoiceTool.is_available():
            threading.Thread(
                target=VoiceTool.speak, args=(reply, "warm"), daemon=True
            ).start()
    except Exception:
        pass

    return reply


# ── CLI entry ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/Users/admin/julia_ai_assistant")
    from providers.llm.deepseek_provider import get_llm_provider
    from julia_core.narrative.bootstrap import get_bootstrap

    BOOTSTRAP = get_bootstrap()
    provider = get_llm_provider("deepseek")

    def chat_fn(text):
        messages = [
            {"role": "system", "content": "你是Julia。\n\n" + BOOTSTRAP},
            {"role": "user", "content": text},
        ]
        return provider.chat(messages, cognitive_mode="private_voice_continuity")

    print(f"Julia Voice Loop v1.0")
    print(f"  Server: {SERVER_URL}")
    print(f"  Press Ctrl+C to stop")
    print()

    while True:
        try:
            reply = voice_chat(chat_fn)
            print(f"  💬 Julia: {reply}\n")
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break
        except Exception as e:
            print(f"  Error: {e}")

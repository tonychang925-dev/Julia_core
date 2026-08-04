"""Julia Wake Word — always listening, naturally awake.

Architecture:
  Mac mic → VAD detects speech → record 2s clip → Whisper STT → check wake words
  → if "婉婉" detected → full Julia voice loop → response

No button press. Just say "婉婉" and Julia wakes up.

Dependencies: ffmpeg (recording), requests (STT), Julia OS (LLM + TTS)
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from pathlib import Path

SERVER_URL = os.environ.get("WHISPER_SERVER_URL", "http://localhost:8001")

# Wake words — any of these triggers the full voice loop
WAKE_WORDS = ["婉婉", "晚晚", "玩玩", "Julia", "julia", "朱莉亚"]


def listen_for_wake(timeout: float = 30.0) -> str | None:
    """Listen continuously until a wake word is detected or timeout.

    Returns the full transcript if wake word found, None otherwise.
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Record a short clip
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            subprocess.run([
                "ffmpeg", "-f", "avfoundation",
                "-i", ":0", "-t", "3",
                "-ar", "16000", "-ac", "1",
                "-y", tmp_path,
            ], capture_output=True, timeout=8)

            if not Path(tmp_path).exists() or Path(tmp_path).stat().st_size < 1000:
                os.unlink(tmp_path)
                time.sleep(1)
                continue

            # Send to GPU server
            import requests
            with open(tmp_path, "rb") as f:
                resp = requests.post(
                    f"{SERVER_URL}/v1/transcribe",
                    files={"audio": ("clip.wav", f, "audio/wav")},
                    data={"language": "zh", "beam_size": 5},
                    timeout=30,
                )
            os.unlink(tmp_path)

            if resp.status_code != 200:
                time.sleep(1)
                continue

            data = resp.json()
            text = data.get("text", "").strip()

            if not text:
                time.sleep(1)
                continue

            # Check for wake words
            for word in WAKE_WORDS:
                if word.lower() in text.lower():
                    print(f"  🔔 Wake word detected: '{word}' in '{text}'")
                    return text

            # If speech detected but no wake word, wait and try again
            time.sleep(1)

        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            time.sleep(1)
            continue

    return None  # Timeout, no wake word detected


def voice_chat_loop(llm_chat_fn, tts_speak_fn=None):
    """Full wake-driven voice loop: listen → wake → chat → speak.

    Usage:
        from julia_core.capability.wake_word import voice_chat_loop
        voice_chat_loop(llm_fn, tts_fn)
    """
    import threading

    print("Julia Wake Word v1.0")
    print(f"  Listening for: {', '.join(WAKE_WORDS[:3])}...")
    print(f"  Server: {SERVER_URL}")
    print("  Press Ctrl+C to stop")
    print()

    while True:
        try:
            print("  🎤 Listening...")
            transcript = listen_for_wake(timeout=30)

            if transcript:
                print(f"  💬 Heard: {transcript}")

                # LLM response
                reply = llm_chat_fn(transcript)
                print(f"  💬 Julia: {reply[:200]}")

                # TTS (background)
                if tts_speak_fn:
                    threading.Thread(
                        target=tts_speak_fn, args=(reply,),
                        daemon=True
                    ).start()

        except KeyboardInterrupt:
            print("\n  Goodbye.")
            break
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/Users/admin/julia_ai_assistant")
    from providers.llm.deepseek_provider import get_llm_provider
    from julia_core.narrative.bootstrap import get_bootstrap

    bootstrap = get_bootstrap()
    provider = get_llm_provider("deepseek")

    def chat_fn(text):
        messages = [
            {"role": "system", "content": "你是Julia。\n\n" + bootstrap},
            {"role": "user", "content": text},
        ]
        return provider.chat(messages, cognitive_mode="private_voice_continuity")

    def speak_fn(text):
        try:
            from julia_core.capability.voice_tool import VoiceTool
            VoiceTool.speak(text, emotion="warm")
        except Exception:
            pass

    voice_chat_loop(chat_fn, speak_fn)

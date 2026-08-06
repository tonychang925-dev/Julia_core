#!/usr/bin/env python3
"""Wake word detection test — GPU Whisper backend.

Usage:
  python scripts/test_wake_word.py
  python scripts/test_wake_word.py --duration 60
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import wave

import numpy as np
import sounddevice as sd

DURATION = int(sys.argv[sys.argv.index("--duration") + 1]) if "--duration" in sys.argv else 30
WHISPER_URL = os.environ.get("WHISPER_SERVER_URL", "http://localhost:8001")
WAKE_WORDS = ["婉婉", "Julia", "julia"]
WAKE_VARIANTS = {
    "婉婉": ["娃娃", "玩玩", "晚安", "弯弯", "万万", "婉", "湾湾", "晚晚", "腕表", "完蛋"],
    "Julia": ["julia", "Juria", "Lunia", "Toria", "Julian", "Julie", "朱莉亚", "朱利亚", "朱丽亚", "朱利安", "茱莉", "茱莉亚", "茱莉呀"],
}
def _match_wake(text):
    lower = text.lower().strip()
    for word in WAKE_WORDS:
        if word.lower() in lower:
            return word
    for canonical, variants in WAKE_VARIANTS.items():
        for v in variants:
            if v.lower() in lower:
                return canonical
    return None
SAMPLE_RATE = 16000

# ── Health check ────────────────────────────────────────────────────────────
r = subprocess.run(["curl", "-s", f"{WHISPER_URL}/health"], capture_output=True, text=True, timeout=5)
try:
    json.loads(r.stdout)
    print(f"  Whisper server: ✅ @ {WHISPER_URL}")
except Exception:
    print(f"  Whisper server: ❌ @ {WHISPER_URL}")
    sys.exit(1)

print(f"  Wake words: {WAKE_WORDS}")
print(f"  Listening {DURATION}s... say '婉婉' or 'Julia' (Ctrl+C to stop)")
print(f"  {'─' * 45}")

# ── Record loop ─────────────────────────────────────────────────────────────
wake_count = 0
start_time = time.time()

try:
    while time.time() - start_time < DURATION:
        # Record 2s via sounddevice (reliable, no ffmpeg hang)
        audio = sd.rec(int(SAMPLE_RATE * 2), samplerate=SAMPLE_RATE,
                       channels=1, dtype="int16", device=1)  # MacBook Pro Mic
        sd.wait()

        # Check if there's actual speech (simple energy threshold)
        rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
        if rms < 50:
            time.sleep(0.3)
            continue

        # Save to temp wav
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()
        with wave.open(tmp_path, "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(audio.tobytes())

        # Send to GPU Whisper
        result = subprocess.run([
            "curl", "-s", "-X", "POST", f"{WHISPER_URL}/v1/transcribe",
            "-F", f"audio=@{tmp_path}", "-F", "language=zh",
            "-F", "beam_size=5", "--max-time", "15",
        ], capture_output=True, text=True, timeout=18)

        os.unlink(tmp_path)

        try:
            data = json.loads(result.stdout) if result.stdout.strip() else {}
        except json.JSONDecodeError:
            continue

        text = data.get("text", "").strip()
        dur = data.get("duration", 0)

        if text:
            timestamp = time.strftime("%H:%M:%S")
            print(f"  [{timestamp}] 🎤 ({dur:.2f}s) {text}", flush=True)
            matched = _match_wake(text)
            if matched:
                wake_count += 1
                print(f"  ✅ WAKE #{wake_count}: '{text}' → '{matched}'!", flush=True)

        time.sleep(0.3)

except KeyboardInterrupt:
    print()

print(f"\nDone. {wake_count} wake detections in {time.time() - start_time:.0f}s")

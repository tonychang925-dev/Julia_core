#!/usr/bin/env python3
"""Collect wake word audio samples for training.

Records 10 samples each of "婉婉" and "Julia" for building a
personalized wake word detector.

Samples are saved as 16kHz mono WAV files in voice_daemon/wakeword/samples/

Usage:
  python scripts/collect_wake_samples.py
  python scripts/collect_wake_samples.py --word "婉婉" --count 10
"""

import os
import sys
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
SAMPLES_DIR = Path(__file__).resolve().parent.parent / "voice_daemon" / "wakeword" / "samples"
WORDS = ["婉婉", "Julia"]
COUNT = 10
RECORD_SECONDS = 1.5  # "婉婉" takes ~0.8s, add margin


def record_word(word: str, count: int):
    """Record multiple samples of a wake word."""
    word_dir = SAMPLES_DIR / word
    word_dir.mkdir(parents=True, exist_ok=True)

    existing = len(list(word_dir.glob("*.wav")))
    if existing > 0:
        print(f"  ({existing} existing samples found)")
        ans = input(f"  Continue recording? Append to existing [y]/skip/skip-all: ").strip().lower()
        if ans == "skip-all":
            return
        elif ans == "skip":
            return

    print(f"\n  Recording '{word}' — {count} samples")
    print(f"  {'─' * 40}")

    for i in range(count):
        input(f"  [{i+1}/{count}] Press Enter, then say '{word}' clearly...")

        # Record
        audio = sd.rec(
            int(SAMPLE_RATE * RECORD_SECONDS),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
        )
        sd.wait()

        # Trim silence from both ends
        audio_abs = np.abs(audio.astype(np.float64))
        threshold = np.max(audio_abs) * 0.1  # 10% of peak
        active = audio_abs > threshold
        active_indices = np.where(active)[0]

        if len(active_indices) < 100:
            print(f"    Too quiet — retry")
            continue

        start = max(0, active_indices[0] - 200)
        end = min(len(audio), active_indices[-1] + 200)

        # Add 300ms padding before and after
        pad = int(SAMPLE_RATE * 0.3)
        start = max(0, start - pad)
        end = min(len(audio), end + pad)

        trimmed = audio[start:end]
        trimmed_float = trimmed.astype(np.float64) / 32768.0

        # Normalize to -3dB
        peak = np.max(np.abs(trimmed_float))
        if peak > 0:
            trimmed_float = trimmed_float * (0.7 / peak)
        trimmed = (trimmed_float * 32767).astype(np.int16)

        # Save
        idx = existing + i + 1
        path = word_dir / f"sample_{idx:02d}.wav"
        with wave.open(str(path), "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(trimmed.tobytes())

        dur = len(trimmed) / SAMPLE_RATE
        print(f"    ✅ Saved: {path.name} ({dur:.1f}s, {len(trimmed)} samples)")

        # Quick playback for confirmation
        try:
            sd.play(trimmed, samplerate=SAMPLE_RATE)
            sd.wait()
        except Exception:
            pass

    print(f"  ✅ '{word}' done: {len(list(word_dir.glob('*.wav')))} total samples")


print(f"Julia Wake Word Sample Collector")
print(f"  Output: {SAMPLES_DIR}")
print(f"  Press Ctrl+C to exit at any time\n")

for word in WORDS:
    record_word(word, COUNT)

print(f"\n{'=' * 50}")
total = sum(1 for _ in SAMPLES_DIR.rglob("*.wav"))
print(f"Total samples: {total}")
print(f"Next: python scripts/verify_wake_model.py")

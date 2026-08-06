#!/usr/bin/env python3
"""Build and test a personalized wake word detector from collected samples.

Uses MFCC features + DTW (Dynamic Time Warping) to match incoming audio
against stored wake word samples. No Whisper, no STT — pure audio matching.

How it works:
  1. Load all collected samples, extract MFCC feature vectors
  2. When listening, extract MFCC from each 1.5s sliding window
  3. Compute DTW distance against stored samples
  4. If distance < threshold → wake word detected

Usage:
  python scripts/verify_wake_model.py              # test with live mic
  python scripts/verify_wake_model.py --duration 60
"""

import json
import os
import sys
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
SAMPLES_DIR = Path(__file__).resolve().parent.parent / "voice_daemon" / "wakeword" / "samples"
WINDOW_SECONDS = 1.5
WINDOW_SAMPLES = int(SAMPLE_RATE * WINDOW_SECONDS)

# Detection threshold — lower = stricter matching
# Determined empirically from your samples
DEFAULT_THRESHOLD = 280.0

# ── MFCC extraction ─────────────────────────────────────────────────────────

def extract_mfcc(audio: np.ndarray, sample_rate: int = 16000,
                 n_mfcc: int = 13, n_fft: int = 512, hop_length: int = 160) -> np.ndarray:
    """Extract MFCC features from audio. Returns (n_frames, n_mfcc)."""
    # Pre-emphasis
    audio = np.asarray(audio, dtype=np.float64)
    audio = np.append(audio[0], audio[1:] - 0.97 * audio[:-1])

    # STFT
    n_fft_half = n_fft // 2 + 1
    n_frames = 1 + (len(audio) - n_fft) // hop_length
    frames = np.zeros((n_fft_half, n_frames))
    for i in range(n_frames):
        start = i * hop_length
        segment = audio[start:start + n_fft]
        if len(segment) < n_fft:
            segment = np.pad(segment, (0, n_fft - len(segment)))
        segment = segment * np.hanning(n_fft)
        frames[:, i] = np.abs(np.fft.rfft(segment, n_fft))

    # Mel filterbank
    n_mels = 26
    mel_fb = _mel_filterbank(n_mels, n_fft, sample_rate)

    # Apply mel filterbank
    mel_spec = np.dot(mel_fb, frames ** 2)
    mel_spec = np.log(mel_spec + 1e-10)

    # DCT to get MFCC
    mfcc = np.zeros((n_mfcc, n_frames))
    for i in range(n_mfcc):
        for k in range(n_mels):
            mfcc[i, :] += mel_spec[k, :] * np.cos(np.pi * i * (k + 0.5) / n_mels)

    # Energy normalization
    mfcc = (mfcc - mfcc.mean(axis=1, keepdims=True)) / (mfcc.std(axis=1, keepdims=True) + 1e-10)
    return mfcc.T  # (n_frames, n_mfcc)


def _mel_filterbank(n_mels: int, n_fft: int, sample_rate: int) -> np.ndarray:
    """Create mel filterbank matrix."""
    n_freqs = n_fft // 2 + 1
    low_mel = 0
    high_mel = 2595 * np.log10(1 + sample_rate / 2 / 700)

    mel_points = np.linspace(low_mel, high_mel, n_mels + 2)
    hz_points = 700 * (10 ** (mel_points / 2595) - 1)
    bin_indices = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

    filters = np.zeros((n_mels, n_freqs))
    for i in range(n_mels):
        for j in range(bin_indices[i], bin_indices[i + 1]):
            filters[i, j] = (j - bin_indices[i]) / max(1, bin_indices[i + 1] - bin_indices[i])
        for j in range(bin_indices[i + 1], bin_indices[i + 2]):
            filters[i, j] = (bin_indices[i + 2] - j) / max(1, bin_indices[i + 2] - bin_indices[i + 1])

    return filters


# ── DTW distance ────────────────────────────────────────────────────────────

def dtw_distance(mfcc1: np.ndarray, mfcc2: np.ndarray) -> float:
    """Dynamic Time Warping distance between two MFCC sequences.

    Lower = more similar. Allows matching of differently-paced speech.
    """
    n, m = len(mfcc1), len(mfcc2)
    cost = np.zeros((n + 1, m + 1))
    cost[0, :] = np.inf
    cost[:, 0] = np.inf
    cost[0, 0] = 0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d = np.sum((mfcc1[i - 1] - mfcc2[j - 1]) ** 2)
            cost[i, j] = d + min(cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1])

    return cost[n, m] / (n + m)  # Normalize by path length


# ── Load samples ────────────────────────────────────────────────────────────

def load_samples() -> dict[str, list[np.ndarray]]:
    """Load all collected wake word samples. Returns {word: [mfcc_features, ...]}."""
    samples = {}
    if not SAMPLES_DIR.exists():
        print(f"  Samples dir not found: {SAMPLES_DIR}")
        print(f"  Run: python scripts/collect_wake_samples.py")
        return samples

    for word_dir in sorted(SAMPLES_DIR.iterdir()):
        if not word_dir.is_dir():
            continue
        word = word_dir.name
        mfccs = []
        for wav_path in sorted(word_dir.glob("*.wav")):
            with wave.open(str(wav_path)) as w:
                n_frames = w.getnframes()
                audio = np.frombuffer(w.readframes(n_frames), dtype=np.int16).astype(np.float64)
                audio = audio / 32768.0
                mfcc = extract_mfcc(audio, SAMPLE_RATE)
                mfccs.append(mfcc)
        if mfccs:
            samples[word] = mfccs
            print(f"  Loaded '{word}': {len(mfccs)} samples")
    return samples


# ── Calibrate threshold ─────────────────────────────────────────────────────

def calibrate_threshold(samples: dict[str, list[np.ndarray]]) -> float:
    """Find optimal DTW threshold from collected samples via cross-validation."""
    within_distances = []
    cross_distances = []

    # Limit to 5 samples per word for calibration speed
    subset = {}
    for w in samples:
        subset[w] = samples[w][:min(5, len(samples[w]))]
    total = sum(len(v) for v in subset.values())

    print(f"\n  Calibrating threshold (using {total} samples)...")

    # Within-class (same word, different samples)
    for word, mfccs in subset.items():
        for i in range(len(mfccs)):
            for j in range(i + 1, len(mfccs)):
                d = dtw_distance(mfccs[i], mfccs[j])
                within_distances.append(d)
    print(f"    Within-class: {len(within_distances)} pairs, avg={np.mean(within_distances):.0f}")

    # Cross-class (different words) — use only first 3 samples each
    words = list(subset.keys())
    for wi in range(len(words)):
        for wj in range(wi + 1, len(words)):
            w1, w2 = words[wi], words[wj]
            for i in range(min(3, len(subset[w1]))):
                for j in range(min(3, len(subset[w2]))):
                    d = dtw_distance(subset[w1][i], subset[w2][j])
                    cross_distances.append(d)
    print(f"    Cross-class: {len(cross_distances)} pairs, avg={np.mean(cross_distances):.0f}")

    if within_distances and cross_distances:
        within_mean = np.mean(within_distances)
        cross_mean = np.mean(cross_distances)
        # Threshold = 70% between within-avg and cross-avg (closer to within = stricter)
        threshold = within_mean + 0.5 * (cross_mean - within_mean)
        print(f"    Threshold: {threshold:.0f} (same={within_mean:.0f} cross={cross_mean:.0f})")
        return threshold

    return DEFAULT_THRESHOLD


# ── Live detection ──────────────────────────────────────────────────────────

def live_test(samples: dict[str, list[np.ndarray]], threshold: float,
              duration: int = 60):
    """Real-time wake word detection from microphone — sync recording loop."""
    print(f"\n  Listening ({duration}s)... say your wake word!")
    print(f"  Threshold: {threshold:.0f} (lower = stricter)")
    print(f"  {'─' * 45}")

    detections = 0
    last_detect_time = 0
    cooldown = 2.0

    # Use only 3 reference samples per word for speed
    ref_samples = {}
    for w in samples:
        ref_samples[w] = samples[w][:3]

    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            # Record a window
            audio = sd.rec(WINDOW_SAMPLES, samplerate=SAMPLE_RATE,
                           channels=1, dtype="float32", device=1)
            sd.wait()

            audio = audio.flatten().astype(np.float64)
            rms = np.sqrt(np.mean(audio ** 2))

            if rms < 0.003:
                time.sleep(0.1)
                continue

            # Match against samples
            mfcc = extract_mfcc(audio, SAMPLE_RATE)
            best_word = None
            best_dist = np.inf

            for word, ref_mfccs in ref_samples.items():
                for ref in ref_mfccs:
                    d = dtw_distance(mfcc, ref)
                    if d < best_dist:
                        best_dist = d
                        best_word = word

            now = time.time()
            if best_dist < threshold and now - last_detect_time > cooldown:
                detections += 1
                last_detect_time = now
                timestamp = time.strftime("%H:%M:%S")
                print(f"  [{timestamp}] ✅ WAKE #{detections}: '{best_word}' (dist={best_dist:.0f}, rms={rms:.4f})", flush=True)
            elif best_dist < threshold * 2:
                # Near-hit: show for debugging
                timestamp = time.strftime("%H:%M:%S")
                print(f"  [{timestamp}] ~ near: '{best_word}' dist={best_dist:.0f}", flush=True)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print()

    print(f"\n  Detections: {detections}")


# ── Main ────────────────────────────────────────────────────────────────────

print("Julia Wake Word Verifier v1.0")
print(f"  Samples: {SAMPLES_DIR}")

samples = load_samples()
if len(samples) < 2:
    print(f"\n  Need at least 2 wake words with samples each.")
    print(f"  Run: python scripts/collect_wake_samples.py")
    sys.exit(1)

threshold = calibrate_threshold(samples)
duration = int(sys.argv[sys.argv.index("--duration") + 1]) if "--duration" in sys.argv else 60
live_test(samples, threshold, duration)

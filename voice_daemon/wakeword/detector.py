"""Wake word detection — Fast Channel, no Whisper.

Engine priority:
  1. MFCC+DTW (personalized, trained on Tony's voice)
  2. openWakeWord (local ONNX, if models available)
  3. Apple Speech (macOS native)
  4. Whisper (GPU fallback, legacy)

Architecture:
  AudioBus → MFCC extraction → DTW match against stored samples → "婉婉!" → activate

Samples stored in: voice_daemon/wakeword/samples/
Calibration stored in: voice_daemon/wakeword/calibration.json
"""

from __future__ import annotations

import json
import logging
import os
import time
import wave
from pathlib import Path
from typing import Callable, Optional

import numpy as np

logger = logging.getLogger("julia.wakeword")

WAKE_WORDS = ["婉婉", "Julia"]

# ── MFCC + DTW Engine ───────────────────────────────────────────────────────

SAMPLE_RATE = 16000
SAMPLES_DIR = Path(__file__).resolve().parent / "samples"
CALIBRATION_PATH = Path(__file__).resolve().parent / "calibration.json"

# Default calibration (overwritten by collected samples)
DEFAULT_THRESHOLD = 12.0
WINDOW_SECONDS = 1.5
WINDOW_SAMPLES = int(SAMPLE_RATE * WINDOW_SECONDS)


class MFCCWakeWordEngine:
    """Personalized wake word detection using MFCC + DTW.

    Matches incoming audio against stored samples of Tony's voice.
    No network, no GPU, ~10ms inference on Mac.

    AudioBus sends ~32ms chunks. This engine maintains a ring buffer
    and runs detection every ~0.3s on the accumulated 1.5s window.
    """

    def __init__(self, samples_dir: Path = SAMPLES_DIR,
                 calibration_path: Path = CALIBRATION_PATH,
                 sample_rate: int = SAMPLE_RATE,
                 window_samples: int = WINDOW_SAMPLES):
        self.samples_dir = samples_dir
        self.calibration_path = calibration_path
        self.sample_rate = sample_rate
        self.window_samples = window_samples
        self._ref_mfccs: dict[str, list[np.ndarray]] = {}
        self._threshold: dict[str, float] = {}
        self._running = False
        self._callbacks: list[Callable[[str], None]] = []
        self._audio_bus = None
        self._cooldown_until = 0.0
        self._cooldown_sec = 2.0
        # Ring buffer for accumulating audio from AudioBus chunks
        self._buffer = np.zeros(window_samples + 8192, dtype=np.float64)
        self._buffer_pos = 0
        self._check_every = int(sample_rate * 0.3)  # run detection every 0.3s

    def on_wake(self, callback: Callable[[str], None]):
        self._callbacks.append(callback)

    @property
    def is_available(self) -> bool:
        return len(self._ref_mfccs) > 0

    def calibrate(self) -> bool:
        """Load samples and compute threshold from stored data."""
        if not self.samples_dir.exists():
            logger.info(f"No wake word samples at {self.samples_dir}")
            return False

        if self.calibration_path.exists():
            return self._load_calibration()

        return self._compute_calibration()

    def _load_calibration(self) -> bool:
        """Load pre-computed calibration from disk."""
        try:
            with open(self.calibration_path) as f:
                data = json.load(f)

            self._ref_mfccs = {}
            for word, paths in data.get("samples", {}).items():
                word_dir = self.samples_dir / word
                if not word_dir.exists():
                    continue
                mfccs = []
                for wav_name in paths:
                    wav_path = word_dir / wav_name
                    if wav_path.exists():
                        mfcc = self._load_and_extract(wav_path)
                        if mfcc is not None:
                            mfccs.append(mfcc)
                if mfccs:
                    self._ref_mfccs[word] = mfccs

            self._threshold = data.get("thresholds", {})
            # Global threshold fallback
            if "__global__" in self._threshold:
                for w in WAKE_WORDS:
                    if w not in self._threshold:
                        self._threshold[w] = self._threshold["__global__"]

            n_total = sum(len(v) for v in self._ref_mfccs.values())
            logger.info(f"MFCC calibration loaded: {n_total} samples, {list(self._ref_mfccs.keys())}")
            return n_total > 0

        except Exception as e:
            logger.warning(f"Calibration load failed: {e}, will recompute")
            return self._compute_calibration()

    def _compute_calibration(self) -> bool:
        """Compute calibration from raw samples. Saves results."""
        self._ref_mfccs = {}
        for word_dir in sorted(self.samples_dir.iterdir()):
            if not word_dir.is_dir():
                continue
            word = word_dir.name
            mfccs = []
            for wav_path in sorted(word_dir.glob("*.wav")):
                mfcc = self._load_and_extract(wav_path)
                if mfcc is not None:
                    mfccs.append(mfcc)
            if mfccs:
                self._ref_mfccs[word] = mfccs

        if len(self._ref_mfccs) < 1:
            return False

        # Compute per-word within-class distances using first 5 samples
        thresholds = {}
        all_within = []
        for word, mfccs in self._ref_mfccs.items():
            subset = mfccs[:min(5, len(mfccs))]
            dists = []
            for i in range(len(subset)):
                for j in range(i + 1, len(subset)):
                    dists.append(_dtw_distance(subset[i], subset[j]))
            if dists:
                avg = np.mean(dists)
                # Threshold = 2x within-class avg (generous margin)
                thresholds[word] = round(float(avg * 2.5), 1)
                all_within.extend(dists)

        thresholds["__global__"] = round(float(np.mean(all_within) * 2.5), 1) if all_within else DEFAULT_THRESHOLD

        self._threshold = thresholds
        self._save_calibration()
        logger.info(f"MFCC calibration computed: thresholds={thresholds}")
        return True

    def _save_calibration(self):
        """Persist calibration to disk."""
        try:
            data = {
                "thresholds": self._threshold,
                "samples": {
                    word: [p.name for p in sorted((self.samples_dir / word).glob("*.wav"))]
                    for word in self._ref_mfccs
                },
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.calibration_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            logger.info(f"Calibration saved to {self.calibration_path}")
        except Exception as e:
            logger.warning(f"Calibration save failed: {e}")

    def _load_and_extract(self, wav_path: Path) -> Optional[np.ndarray]:
        """Load WAV and extract MFCC features."""
        try:
            with wave.open(str(wav_path)) as w:
                frames = w.getnframes()
                audio = np.frombuffer(w.readframes(frames), dtype=np.int16)
                audio = audio.astype(np.float64) / 32768.0
                return _extract_mfcc(audio, self.sample_rate)
        except Exception as e:
            logger.debug(f"Failed to load {wav_path}: {e}")
            return None

    def start(self, audio_bus=None) -> bool:
        """Start MFCC wake word engine on shared AudioBus."""
        if not self.is_available and not self.calibrate():
            return False

        self._audio_bus = audio_bus
        self._running = True
        if audio_bus:
            audio_bus.subscribe(self._process_chunk)
            logger.info(f"MFCC wake engine active: {list(self._ref_mfccs.keys())}")
        return True

    def _process_chunk(self, audio: np.ndarray):
        """Process audio chunk from AudioBus. Called in audio thread (~32ms chunks).

        Maintains a ring buffer. Runs DTW detection every ~0.3s when buffer has
        enough audio (1.5s window) and speech energy is above threshold.
        """
        if not self._running:
            return

        # Ring buffer write
        chunk = audio.astype(np.float64) if audio.dtype != np.float64 else audio
        n = len(chunk)
        if self._buffer_pos + n > len(self._buffer):
            # Shift left
            keep = self.window_samples
            self._buffer[:keep] = self._buffer[self._buffer_pos - keep:self._buffer_pos]
            self._buffer_pos = keep
        self._buffer[self._buffer_pos:self._buffer_pos + n] = chunk
        self._buffer_pos += n

        # Throttle: run detection every ~0.3s
        if self._buffer_pos % self._check_every > n:
            return
        if self._buffer_pos < self.window_samples:
            return

        now = time.time()
        if now < self._cooldown_until:
            return

        # Sliding window
        window = self._buffer[self._buffer_pos - self.window_samples:self._buffer_pos]
        rms = np.sqrt(np.mean(window ** 2))
        if rms < 0.005:
            return

        mfcc = _extract_mfcc(window, self.sample_rate)
        if len(mfcc) < 5:  # too few frames
            return

        best_word = None
        best_dist = np.inf

        for word, ref_mfccs in self._ref_mfccs.items():
            for ref in ref_mfccs[:3]:  # first 3 reference samples for speed
                d = _dtw_distance(mfcc, ref)
                if d < best_dist:
                    best_dist = d
                    best_word = word

        threshold = self._threshold.get(best_word or "", DEFAULT_THRESHOLD)
        if best_word and best_dist < threshold:
            logger.info(f"MFCC wake: '{best_word}' dist={best_dist:.1f} thr={threshold:.0f}")
            self._cooldown_until = now + self._cooldown_sec
            for cb in self._callbacks:
                cb(best_word)

    def pause(self):
        """Pause wake detection during conversation."""
        self._running = False
        logger.debug("MFCC wake engine paused")

    def resume(self):
        """Resume wake detection after conversation."""
        self._running = True
        logger.debug("MFCC wake engine resumed")

    def stop(self):
        self._running = False
        if self._audio_bus:
            self._audio_bus.unsubscribe(self._process_chunk)


# ── MFCC extraction ─────────────────────────────────────────────────────────

def _extract_mfcc(audio: np.ndarray, sample_rate: int = 16000,
                  n_mfcc: int = 13, n_fft: int = 512,
                  hop_length: int = 160) -> np.ndarray:
    """Extract MFCC features from audio. Returns (n_frames, n_mfcc)."""
    audio = np.asarray(audio, dtype=np.float64)
    # Pre-emphasis
    audio = np.append(audio[0], audio[1:] - 0.97 * audio[:-1])

    n_fft_half = n_fft // 2 + 1
    n_frames = 1 + max(0, len(audio) - n_fft) // hop_length
    if n_frames < 1:
        return np.zeros((1, n_mfcc))

    frames = np.zeros((n_fft_half, n_frames))
    for i in range(n_frames):
        start = i * hop_length
        segment = audio[start:start + n_fft]
        if len(segment) < n_fft:
            segment = np.pad(segment, (0, n_fft - len(segment)))
        segment = segment * np.hanning(n_fft)
        frames[:, i] = np.abs(np.fft.rfft(segment, n_fft))

    mel_fb = _mel_filterbank(26, n_fft, sample_rate)
    mel_spec = np.log(np.dot(mel_fb, frames ** 2) + 1e-10)

    mfcc = np.zeros((n_mfcc, n_frames))
    for i in range(n_mfcc):
        for k in range(26):
            mfcc[i] += mel_spec[k] * np.cos(np.pi * i * (k + 0.5) / 26)

    mfcc = (mfcc - mfcc.mean(axis=1, keepdims=True)) / (mfcc.std(axis=1, keepdims=True) + 1e-10)
    return mfcc.T


def _mel_filterbank(n_mels: int, n_fft: int, sample_rate: int) -> np.ndarray:
    n_freqs = n_fft // 2 + 1
    low_mel, high_mel = 0, 2595 * np.log10(1 + sample_rate / 2 / 700)
    mel_pts = np.linspace(low_mel, high_mel, n_mels + 2)
    hz_pts = 700 * (10 ** (mel_pts / 2595) - 1)
    bins = np.floor((n_fft + 1) * hz_pts / sample_rate).astype(int)
    filters = np.zeros((n_mels, n_freqs))
    for i in range(n_mels):
        for j in range(bins[i], bins[i + 1]):
            filters[i, j] = (j - bins[i]) / max(1, bins[i + 1] - bins[i])
        for j in range(bins[i + 1], bins[i + 2]):
            filters[i, j] = (bins[i + 2] - j) / max(1, bins[i + 2] - bins[i + 1])
    return filters


def _dtw_distance(mfcc1: np.ndarray, mfcc2: np.ndarray) -> float:
    """Dynamic Time Warping distance between two MFCC sequences."""
    n, m = len(mfcc1), len(mfcc2)
    if n < 2 or m < 2:
        return float("inf")
    cost = np.full((n + 1, m + 1), np.inf)
    cost[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d = np.sum((mfcc1[i - 1] - mfcc2[j - 1]) ** 2)
            cost[i, j] = d + min(cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1])
    return cost[n, m] / (n + m)


# ── Fallback engines ────────────────────────────────────────────────────────

class WakeWordEngine:
    """Abstract wake word engine interface."""
    def start(self, audio_bus=None) -> bool:
        raise NotImplementedError
    def stop(self):
        raise NotImplementedError


class WhisperFallbackEngine(WakeWordEngine):
    """Fallback using existing WakeWordDetector's _match_wake_word on any text output."""

    def __init__(self, match_fn):
        self._match = match_fn
        self._callbacks = []
        self._running = False

    def on_wake(self, cb):
        self._callbacks.append(cb)

    def check_text(self, text: str) -> Optional[str]:
        """Called externally when Whisper produces text. Returns wake word if matched."""
        matched = self._match(text)
        if matched:
            for cb in self._callbacks:
                cb(matched)
        return matched

    def start(self, audio_bus=None) -> bool:
        self._running = True
        return True

    def stop(self):
        self._running = False


# ── Public API ──────────────────────────────────────────────────────────────

class WakeWordDetector:
    """Wake word detector — picks the best available engine.

    Priority: MFCC+DTW > openWakeWord > Whisper fallback
    """

    def __init__(self, sample_rate: int = 16000, audio_bus=None):
        self.sample_rate = sample_rate
        self.audio_bus = audio_bus
        self.engine: Optional[WakeWordEngine] = None
        self._callbacks: list[Callable[[str], None]] = []
        self._running = False
        self._fallback = WhisperFallbackEngine(_match_wake_word)

    def on_wake(self, callback: Callable[[str], None]):
        self._callbacks.append(callback)

    def start(self) -> bool:
        """Start wake word detection. Tries engines in priority order."""
        # 1. MFCC+DTW (personalized, your own voice)
        mfcc = MFCCWakeWordEngine()
        for cb in self._callbacks:
            mfcc.on_wake(cb)
        if mfcc.calibrate():
            if mfcc.start(audio_bus=self.audio_bus):
                self.engine = mfcc
                self._running = True
                logger.info(f"WakeWordDetector: MFCC+DTW (personalized)")
                return True

        # 2. Whisper fallback (always works if GPU server is up)
        logger.info("MFCC not available, using Whisper fallback")
        self.engine = self._fallback
        self._running = True
        return True

    def check_text(self, text: str) -> Optional[str]:
        """For Whisper fallback: check transcribed text for wake words."""
        return self._fallback.check_text(text)

    def pause(self):
        """Pause wake detection during conversation."""
        if hasattr(self.engine, 'pause'):
            self.engine.pause()
        self._running = False

    def resume(self):
        """Resume wake detection after conversation."""
        if hasattr(self.engine, 'resume'):
            self.engine.resume()
        self._running = True

    def stop(self):
        self._running = False
        if self.engine:
            self.engine.stop()


# ── Legacy compatibility ────────────────────────────────────────────────────

WAKE_VARIANTS = {
    "婉婉": ["娃娃", "玩玩", "晚安", "弯弯", "万万", "婉", "湾湾", "晚晚"],
    "Julia": ["julia", "Juria", "Lunia", "Toria", "Julian", "Julie", "Juli",
              "朱莉亚", "朱利亚", "朱丽亚", "朱利安", "茱莉", "茱莉呀"],
}


def _match_wake_word(text: str) -> Optional[str]:
    lower = text.lower().strip()
    for word in WAKE_WORDS:
        if word.lower() in lower:
            return word
    for canonical, variants in WAKE_VARIANTS.items():
        for v in variants:
            if v.lower() in lower:
                return canonical
    for transcript_word in lower.split():
        for wake in WAKE_WORDS:
            w = wake.lower()
            if abs(len(transcript_word) - len(w)) <= 1:
                if _edit_distance(transcript_word, w) <= 1:
                    return wake
    return None


def _edit_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (0 if ca == cb else 1)))
        prev = curr
    return prev[-1]

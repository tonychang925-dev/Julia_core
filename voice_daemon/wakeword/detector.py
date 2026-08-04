"""Wake word detection — always listening for "婉婉".

Current implementation: short audio clips → GPU Whisper STT → keyword match.
Future: openWakeWord for always-on local detection with lower latency.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Callable

from voice_daemon.stt.whisper_client import WhisperClient


# Wake words — any of these triggers activation
WAKE_WORDS = ["婉婉", "晚晚", "Julia", "julia"]

# Common Whisper mis-recognitions mapped to canonical wake words
# Whisper often produces homophones or slight spelling variations
WAKE_VARIANTS = {
    "婉婉": ["娃娃", "玩玩", "晚安", "弯弯", "万万", "婉", "湾湾"],
    "晚晚": ["晚安", "玩玩", "万晚", "万万"],
    "Julia": ["julia", "Juria", "Lunia", "Toria", "Julian", "Julie", "Juli", "朱莉亚", "朱利亚", "朱丽亚", "朱利安"],
    "julia": ["Julia", "Juria", "Lunia", "Toria"],
}


def _match_wake_word(text: str) -> Optional[str]:
    """Check if text matches any wake word, including common Whisper variants.

    Uses:
      1. Exact substring match (case-insensitive for English)
      2. Variant dictionary for known Whisper mis-recognitions
      3. Edit distance ≤ 1 for short words (e.g., "Juria" → "Julia")

    Returns canonical wake word if matched, None otherwise.
    """
    lower = text.lower().strip()

    # 1. Exact match
    for word in WAKE_WORDS:
        if word.lower() in lower:
            return word

    # 2. Known variants (Whisper homophones)
    for canonical, variants in WAKE_VARIANTS.items():
        for variant in variants:
            if variant.lower() in lower:
                return canonical

    # 3. Fuzzy edit-distance for short candidates
    # Check each word in the transcript against wake words
    for transcript_word in lower.split():
        for wake in WAKE_WORDS:
            w = wake.lower()
            if abs(len(transcript_word) - len(w)) <= 1:
                dist = _edit_distance(transcript_word, w)
                if dist <= 1:
                    return wake

    return None


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein distance between two strings."""
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(
                prev[j + 1] + 1,      # deletion
                curr[j] + 1,           # insertion
                prev[j] + (0 if ca == cb else 1),  # substitution
            ))
        prev = curr
    return prev[-1]


class WakeWordDetector:
    """Continuously listens for wake words.

    Architecture:
      Mic → record 2-3s clip → STT (GPU Whisper) → keyword match → trigger.
    """

    def __init__(self, whisper_client: WhisperClient = None,
                 sample_rate: int = 16000, clip_duration: float = 3.0,
                 device_index: int = None):
        self.whisper = whisper_client or WhisperClient()
        self.sample_rate = sample_rate
        self.clip_duration = clip_duration
        self.device_index = device_index  # None = system default, or specific index
        self._on_wake: list[Callable[[str, str], None]] = []
        self._running = False

    def on_wake(self, callback: Callable[[str, str], None]):
        """Register wake callback: callback(wake_word, full_transcript)."""
        self._on_wake.append(callback)

    def listen(self, audio_stream_func, timeout: float = 60.0) -> Optional[tuple[str, str]]:
        """Block and listen for wake word. Uses audio_stream_func to get audio chunks.

        Args:
            audio_stream_func: callable that records a short clip → returns raw PCM bytes
            timeout: max seconds to listen

        Returns:
            (wake_word, transcript) if detected, None otherwise
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Record a short clip via ffmpeg (direct hardware access, no browser)
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = tmp.name
            tmp.close()

            try:
                device = f":{self.device_index}" if self.device_index is not None else ":0"
                subprocess.run([
                    "ffmpeg", "-f", "avfoundation",
                    "-i", device, "-t", str(self.clip_duration),
                    "-ar", str(self.sample_rate), "-ac", "1",
                    "-y", tmp_path,
                ], capture_output=True, timeout=self.clip_duration + 5)

                if not Path(tmp_path).exists() or Path(tmp_path).stat().st_size < 1000:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                    time.sleep(0.2)
                    continue

                # Send to GPU Whisper
                result = self.whisper.transcribe_file(tmp_path)
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

                text = result.get("text", "").strip()

                # Print feedback — user needs to know the daemon is alive
                if text:
                    print(f"  🎤 听到: '{text}'", flush=True)

                if not text:
                    time.sleep(0.2)
                    continue

                # Check for wake words (exact + fuzzy variants)
                matched = _match_wake_word(text)
                if matched:
                    for cb in self._on_wake:
                        cb(matched, text)
                    return (matched, text)

                time.sleep(0.5)

            except Exception:
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                except Exception:
                    pass
                time.sleep(0.5)
                continue

        return None  # Timeout, no wake word

    def stop(self):
        """Stop the wake word listening loop."""
        self._running = False


def record_clip_ffmpeg(duration: float = 3.0, sample_rate: int = 16000,
                       device_index: int = None) -> Optional[str]:
    """Record a short audio clip using ffmpeg (macOS).
    Returns path to WAV file, or None on failure.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        device = f":{device_index}" if device_index is not None else ":0"
        subprocess.run([
            "ffmpeg", "-f", "avfoundation",
            "-i", device, "-t", str(duration),
            "-ar", str(sample_rate), "-ac", "1",
            "-y", tmp_path,
        ], capture_output=True, timeout=duration + 5)

        if Path(tmp_path).exists() and Path(tmp_path).stat().st_size > 1000:
            return tmp_path
        else:
            os.unlink(tmp_path)
            return None
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        return None

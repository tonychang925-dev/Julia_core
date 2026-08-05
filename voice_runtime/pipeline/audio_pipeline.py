"""Audio Pipeline — VAD + buffer + speech boundary detection.

Sits between PyAV-resampled PCM (s16/mono/16kHz) and ASR Provider.
All format conversion is done upstream by PyAV AudioResampler.
Pipeline only sees clean int16 PCM bytes at 16kHz.
"""

from __future__ import annotations
import asyncio
import logging
from collections import deque
from typing import Callable, Optional

logger = logging.getLogger("julia.audio.pipeline")


class AudioPipeline:
    """Receives int16 PCM bytes at 16kHz, detects speech boundaries.

    Features:
      - 300ms pre-roll preserves sentence-start audio
      - Dynamic noise floor adapts to environment
      - 700ms silence gap ends utterance (no force-emit)
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._buffer: list[bytes] = []
        self._is_speaking = False
        self._silent_frames = 0
        self._speaking_frames = 0
        self._total_frames = 0
        self._speech_threshold = 160      # initial int16 RMS (adapts via noise floor)
        self._silence_limit = 35            # frames of silence to end speech (~0.7s at 20ms)
        self._min_speech_frames = 10        # minimum frames for valid speech (0.2s)
        self._max_segment_frames = 0       # disabled — only silence ends utterance
        self._samples_per_frame = sample_rate // 50  # 20ms frames

        # Pre-roll: buffer audio before speech_start to preserve first syllables
        self._pre_roll: deque[bytes] = deque(maxlen=15)  # 300ms

        # Dynamic noise floor
        self._noise_floor: float = 40.0

        self._on_speech_start: Optional[Callable[[], None]] = None
        self._on_speech_end: Optional[Callable[[bytes], None]] = None

    def on_speech_start(self, cb: Callable[[], None]):
        self._on_speech_start = cb

    def on_speech_end(self, cb: Callable[[bytes], None]):
        """Called with PCM int16 bytes of complete speech segment."""
        self._on_speech_end = cb

    async def push_pcm(self, pcm_int16: bytes, sample_rate: int = 16000) -> None:
        """Push one chunk of int16 PCM bytes. Must be 20ms aligned."""
        if sample_rate != self.sample_rate:
            raise ValueError(f"Expected {self.sample_rate}Hz, got {sample_rate}Hz")

        import numpy as np
        samples = np.frombuffer(pcm_int16, dtype=np.int16).astype(np.float64)
        self._total_frames += 1

        rms = float(np.sqrt(np.mean(samples ** 2)))

        # Dynamic threshold: 3× noise floor, minimum 120
        threshold = max(120, self._noise_floor * 3.0)
        is_speech = rms > threshold

        if self._total_frames % 50 == 0:
            logger.info(f"VAD: frame #{self._total_frames}, rms={rms:.0f}, "
                       f"thresh={threshold:.0f}, noise={self._noise_floor:.0f}, "
                       f"speech={is_speech}, speaking={self._is_speaking}")

        if is_speech:
            self._silent_frames = 0
            if not self._is_speaking:
                self._is_speaking = True
                self._speaking_frames = 0
                # Prepend pre-roll to preserve sentence-start audio
                self._buffer = list(self._pre_roll) + [pcm_int16]
                self._pre_roll.clear()
                logger.info(f"VAD: speech start (rms={rms:.0f}, thresh={threshold:.0f})")
                if self._on_speech_start:
                    self._on_speech_start()
            else:
                self._buffer.append(pcm_int16)
                self._speaking_frames += 1
        else:
            # Update noise floor during silence
            self._noise_floor = self._noise_floor * 0.95 + rms * 0.05
            # Pre-roll: always buffer recent audio
            self._pre_roll.append(pcm_int16)

            if self._is_speaking:
                self._buffer.append(pcm_int16)
                self._silent_frames += 1
                if self._silent_frames >= self._silence_limit:
                    if len(self._buffer) >= self._min_speech_frames:
                        self._emit_segment()
                    else:
                        self._is_speaking = False
                        self._buffer = []
                        self._silent_frames = 0

    def _emit_segment(self):
        """Speech segment complete — emit concatenated int16 PCM."""
        if not self._buffer:
            self._is_speaking = False
            return

        all_pcm = b"".join(self._buffer)
        dur = len(all_pcm) / (self.sample_rate * 2)
        n_frames = len(self._buffer)

        self._is_speaking = False
        self._buffer = []
        self._silent_frames = 0

        logger.info(f"VAD: speech end — {dur:.1f}s, {n_frames} frames, "
                   f"{len(all_pcm)} bytes")

        if self._on_speech_end:
            self._on_speech_end(all_pcm)

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    def reset(self):
        self._buffer = []
        self._is_speaking = False
        self._silent_frames = 0
        self._speaking_frames = 0
        self._pre_roll.clear()
        self._noise_floor = 40.0

"""Audio Pipeline — VAD + buffer + speech boundary detection.

Sits between PyAV-resampled PCM (s16/mono/16kHz) and ASR Provider.
All format conversion is done upstream by PyAV AudioResampler.
Pipeline only sees clean int16 PCM bytes at 16kHz.
"""

from __future__ import annotations
import asyncio
import logging
import time as _time
from typing import Callable, Optional

logger = logging.getLogger("julia.audio.pipeline")


class AudioPipeline:
    """Receives int16 PCM bytes at known sample_rate, detects speech boundaries.

    Flow:
      PCM bytes → VAD check → buffer → speech_start → accumulate
      → silence detected → speech_end → emit PCM segment → ASR
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._buffer: list[bytes] = []
        self._is_speaking = False
        self._silent_frames = 0
        self._speaking_frames = 0
        self._total_frames = 0
        self._speech_threshold = 200      # int16 RMS threshold (silence ~10-50, speech ~500-5000)
        self._silence_limit = 60            # frames of silence to end speech (~1.2s at 20ms)
        self._min_speech_frames = 15        # minimum frames for valid speech (0.3s)
        self._max_segment_frames = 0       # disabled — only silence ends utterance (one turn per utterance)
        self._samples_per_frame = sample_rate // 50  # 20ms frames

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
        is_speech = rms > self._speech_threshold

        if self._total_frames % 50 == 0:
            logger.info(f"VAD: frame #{self._total_frames}, rms={rms:.0f}, "
                       f"speech={is_speech}, speaking={self._is_speaking}")

        if is_speech:
            self._silent_frames = 0
            if not self._is_speaking:
                self._is_speaking = True
                self._speaking_frames = 0
                self._buffer = [pcm_int16]
                logger.info(f"VAD: speech start (rms={rms:.0f})")
                if self._on_speech_start:
                    self._on_speech_start()
            else:
                self._buffer.append(pcm_int16)
                self._speaking_frames += 1
                if self._max_segment_frames > 0 and self._speaking_frames >= self._max_segment_frames:
                    logger.info(f"VAD: force emit after {self._speaking_frames} frames "
                              f"(~{self._speaking_frames * 20 / 1000:.1f}s)")
                    self._emit_segment()
                    self._is_speaking = True
                    self._speaking_frames = 0
                    self._buffer = []
        else:
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

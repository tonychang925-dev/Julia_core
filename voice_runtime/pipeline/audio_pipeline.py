"""Audio Pipeline — VAD + buffer + speech boundary detection.

Sits between WebRTC AudioFrames and ASR Provider.
Handles: voice activity detection, audio buffering, speech start/end events.
ASR Provider stays clean — only receives complete speech segments.
"""

from __future__ import annotations
import asyncio
import logging
import time as _time
from typing import Callable, Optional

logger = logging.getLogger("julia.audio.pipeline")


class AudioPipeline:
    """Receives aiortc AudioFrames, detects speech boundaries, emits segments.

    Flow:
      AudioFrame → VAD check → buffer → speech_start → accumulate
      → silence detected → speech_end → emit PCM segment → ASR
    """

    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self._buffer: list[bytes] = []
        self._is_speaking = False
        self._silent_frames = 0
        self._total_frames = 0
        self._speech_threshold = 0.01     # RMS energy threshold
        self._silence_limit = 30           # frames of silence to end speech (~0.6s)
        self._min_speech_frames = 10       # minimum frames for valid speech

        # Callbacks
        self._on_speech_start: Optional[Callable[[], None]] = None
        self._on_speech_end: Optional[Callable[[bytes], None]] = None
        self._on_partial: Optional[Callable[[str], None]] = None

    def on_speech_start(self, cb: Callable[[], None]):
        self._on_speech_start = cb

    def on_speech_end(self, cb: Callable[[bytes], None]):
        """Called with PCM int16 bytes of complete speech segment."""
        self._on_speech_end = cb

    def on_partial(self, cb: Callable[[str], None]):
        """Called with partial transcript (from ASR)."""
        self._on_partial = cb

    async def push_frame(self, frame) -> None:
        """Push one aiortc AudioFrame through the pipeline."""
        import numpy as np
        pcm = frame.to_ndarray().flatten().astype(np.float64)
        self._total_frames += 1

        # Energy-based VAD
        rms = float(np.sqrt(np.mean(pcm ** 2)))
        is_speech = rms > self._speech_threshold

        # Diagnostic: log every 50 frames
        if self._total_frames % 50 == 0:
            logger.info(f"VAD: frame #{self._total_frames}, rms={rms:.6f}, "
                       f"speech={is_speech}, speaking={self._is_speaking}")

        if is_speech:
            self._silent_frames = 0
            if not self._is_speaking:
                self._is_speaking = True
                self._buffer = [pcm.tobytes()]
                logger.info(f"VAD: speech start (rms={rms:.4f})")
                if self._on_speech_start:
                    self._on_speech_start()
            else:
                self._buffer.append(pcm.tobytes())
        else:
            if self._is_speaking:
                self._buffer.append(pcm.tobytes())
                self._silent_frames += 1
                if self._silent_frames >= self._silence_limit:
                    if len(self._buffer) >= self._min_speech_frames:
                        self._emit_segment()
                    else:
                        self._is_speaking = False
                        self._buffer = []
                        self._silent_frames = 0

    def _emit_segment(self):
        """Speech segment complete — convert to int16 PCM and emit."""
        if not self._buffer:
            self._is_speaking = False
            return

        import numpy as np
        all_audio = np.concatenate([np.frombuffer(b, dtype=np.float64) for b in self._buffer])
        int16 = (all_audio * 32767).astype(np.int16).tobytes()
        dur = len(int16) / (self.sample_rate * 2)

        logger.info(f"VAD: speech end — {dur:.1f}s, {len(self._buffer)} frames")

        self._is_speaking = False
        self._buffer = []
        self._silent_frames = 0

        if self._on_speech_end:
            self._on_speech_end(int16)

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    def reset(self):
        self._buffer = []
        self._is_speaking = False
        self._silent_frames = 0

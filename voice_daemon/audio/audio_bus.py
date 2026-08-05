"""Single Mic Audio Bus — one InputStream, many consumers.

Problem: openWakeWord and Silero VAD both open sounddevice.InputStream,
         competing for the same Mac CoreAudio device. This causes dropouts,
         silent channels, and occasional crashes.

Solution: A single InputStream that fans out audio chunks to registered
          consumers via callbacks. Both wake word engine and VAD processor
          read from the same audio stream.

Architecture:
  Mic → sounddevice InputStream → AudioBus → [Consumer 1: openWakeWord  ]
                                            → [Consumer 2: Silero VAD   ]
                                            → [Consumer 3: (future) ... ]

Consumer contract: callback(audio_chunk: np.ndarray) — non-blocking.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable

import numpy as np

logger = logging.getLogger("julia.audio_bus")


class AudioBus:
    """Single microphone stream → multiple audio consumers.

    Only ONE AudioBus instance should exist per process.
    Starts exactly one sounddevice InputStream.
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 device_index: int = None, chunk_size: int = 512,
                 dtype: str = "float32"):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_index = device_index
        self.chunk_size = chunk_size
        self.dtype = dtype

        self._consumers: list[Callable[[np.ndarray], None]] = []
        self._stream = None
        self._running = False
        self._lock = threading.Lock()

    # ── Consumer management ────────────────────────────────────────────────

    def subscribe(self, callback: Callable[[np.ndarray], None]) -> bool:
        """Register an audio consumer. callback receives float32 numpy arrays.

        Returns True if this is the first consumer (bus needs to start streaming).
        """
        with self._lock:
            was_empty = len(self._consumers) == 0
            self._consumers.append(callback)
            logger.debug(f"Consumer #{len(self._consumers)} subscribed")
            return was_empty

    def unsubscribe(self, callback: Callable[[np.ndarray], None]):
        """Remove a consumer."""
        with self._lock:
            try:
                self._consumers.remove(callback)
            except ValueError:
                pass

    @property
    def consumer_count(self) -> int:
        return len(self._consumers)

    # ── Stream lifecycle ───────────────────────────────────────────────────

    def start(self) -> bool:
        """Start the microphone stream. Only call once."""
        if self._running:
            logger.warning("AudioBus already running")
            return True

        try:
            import sounddevice as sd

            def _callback(indata, frames, time_info, status):
                if status:
                    logger.debug(f"Audio status: {status}")
                # Copy to avoid buffer reuse issues
                chunk = indata.copy()
                if chunk.ndim > 1:
                    chunk = chunk[:, 0]  # mono → 1D
                # Fan out to all consumers (lockless read — consumers list seldom mutates)
                consumers = self._consumers  # snapshot reference
                for consumer in consumers:
                    try:
                        consumer(chunk)
                    except Exception as e:
                        logger.debug(f"Consumer error: {e}")

            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device_index,
                callback=_callback,
                blocksize=self.chunk_size,
                dtype=self.dtype,
            )
            self._stream.start()
            self._running = True
            logger.info(f"AudioBus started: {self.sample_rate}Hz, {self.chunk_size} samples/chunk, {self.consumer_count} consumers")
            return True
        except Exception as e:
            logger.error(f"AudioBus failed to start: {e}")
            return False

    def stop(self):
        """Stop the microphone stream."""
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        with self._lock:
            self._consumers.clear()
        logger.info("AudioBus stopped")

    @property
    def is_running(self) -> bool:
        return self._running


# ── Singleton ──────────────────────────────────────────────────────────────

_audio_bus: AudioBus | None = None


def get_audio_bus(**kwargs) -> AudioBus:
    """Get or create the singleton AudioBus."""
    global _audio_bus
    if _audio_bus is None:
        _audio_bus = AudioBus(**kwargs)
    return _audio_bus

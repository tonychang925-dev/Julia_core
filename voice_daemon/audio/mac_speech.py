"""Mac Audio Pipeline — continuous streaming with VAD-driven boundaries.

Architecture:
  sounddevice (continuous) → Silero VAD → speech segments → Whisper STT

This replaces the ffmpeg 3s-clip polling loop.
Real-time streaming. VAD decides when speech starts/ends.
No fixed-duration clips. No dead zones.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections import deque
from typing import Callable, Optional

import numpy as np

logger = logging.getLogger("julia.audio")


class StreamingMic:
    """Continuous microphone stream via sounddevice.

    Runs a callback-based stream that fills a ring buffer.
    VAD consumer reads from the buffer and detects speech boundaries.
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 device_index: int = None, chunk_size: int = 512):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_index = device_index
        self.chunk_size = chunk_size
        self._stream = None
        self._running = False

    def start(self, callback: Callable[[np.ndarray], None]) -> bool:
        """Start streaming. callback receives numpy array of audio frames."""
        try:
            import sounddevice as sd

            def _callback(indata, frames, time_info, status):
                if status:
                    logger.warning(f"Audio status: {status}")
                callback(indata.copy().flatten())

            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device_index,
                callback=_callback,
                blocksize=self.chunk_size,
                dtype='float32',
            )
            self._stream.start()
            self._running = True
            logger.info(f"StreamingMic started (device={self.device_index}, sr={self.sample_rate})")
            return True
        except Exception as e:
            logger.error(f"Failed to start mic: {e}")
            return False

    def stop(self):
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    @property
    def is_running(self) -> bool:
        return self._running


class VADStreamProcessor:
    """Processes continuous audio stream with VAD to detect speech segments.

    State machine:
      SILENCE → (VAD prob > threshold) → SPEECH → accumulate
      SPEECH → (VAD prob < threshold for N seconds) → segment complete

    Provides:
      - Real-time speech detection (no fixed clips)
      - Automatic segment boundaries
      - Configurable silence threshold
    """

    def __init__(self, sample_rate: int = 16000,
                 speech_threshold: float = 0.3,
                 silence_seconds: float = 0.8,
                 min_speech_seconds: float = 0.3,
                 max_speech_seconds: float = 15.0,
                 debug: bool = False):
        self.sample_rate = sample_rate
        self.speech_threshold = speech_threshold
        self.silence_samples = int(silence_seconds * sample_rate)
        self.min_speech_samples = int(min_speech_seconds * sample_rate)
        self.max_speech_samples = int(max_speech_seconds * sample_rate)
        self._energy_threshold = 0.008  # RMS threshold for energy VAD

        self._vad_model = None
        self._vad_loaded = False

        # State
        self._is_speaking = False
        self._use_energy_vad = False
        self._accumulated: list[np.ndarray] = []
        self._accumulated_samples = 0
        self._silent_samples = 0
        self._energy_threshold = 0.003  # RMS threshold for energy VAD (lower = more sensitive)

        # Callbacks
        self._on_speech_start: Optional[Callable[[], None]] = None
        self._on_speech_end: Optional[Callable[[bytes], None]] = None

    def load_vad(self) -> bool:
        """Load VAD model. Silero first, fallback to energy-based."""
        # Try Silero VAD (requires torch)
        try:
            import torch
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                trust_repo=True,
            )
            self._vad_model = model
            self._vad_loaded = True
            logger.info("Silero VAD loaded successfully")
            return True
        except Exception as e:
            logger.warning(f"Silero VAD not available: {e}")

        # Fallback: energy-based VAD (no dependencies)
        logger.info("Using energy-based VAD fallback")
        self._vad_loaded = True
        self._use_energy_vad = True
        return True

    @property
    def is_loaded(self) -> bool:
        return self._vad_loaded

    def on_speech_start(self, callback: Callable[[], None]):
        self._on_speech_start = callback

    def on_speech_end(self, callback: Callable[[bytes], None]):
        """callback receives raw PCM bytes of the complete speech segment."""
        self._on_speech_end = callback

    def process_chunk(self, audio_chunk: np.ndarray):
        """Feed audio chunk into VAD. Handles speech boundary detection."""
        if not self._vad_loaded:
            return

        chunk_samples = len(audio_chunk)

        if getattr(self, '_use_energy_vad', False):
            # ── Energy-based VAD (no deps) ──
            rms = float(np.sqrt(np.mean(audio_chunk.astype(np.float64) ** 2)))
            is_speech = rms > self._energy_threshold

            if is_speech:
                self._silent_samples = 0
                if not self._is_speaking:
                    self._is_speaking = True
                    self._accumulated = [audio_chunk]
                    self._accumulated_samples = chunk_samples
                    logger.debug(f"VAD speech start (rms={rms:.4f})")
                    if self._on_speech_start:
                        self._on_speech_start()
                else:
                    self._accumulated.append(audio_chunk)
                    self._accumulated_samples += chunk_samples
                if self._accumulated_samples >= self.max_speech_samples:
                    logger.debug(f"VAD max duration reached ({self._accumulated_samples} samples)")
                    self._end_segment()
            else:
                if self._is_speaking:
                    self._accumulated.append(audio_chunk)
                    self._accumulated_samples += chunk_samples
                    self._silent_samples += chunk_samples
                    if self._silent_samples >= self.silence_samples:
                        if self._accumulated_samples >= self.min_speech_samples:
                            logger.debug(f"VAD speech end: {self._accumulated_samples} samples, {len(self._accumulated)} chunks")
                            self._end_segment()
                        else:
                            logger.debug(f"VAD speech too short: {self._accumulated_samples} samples")
                            self._is_speaking = False
                            self._accumulated = []
                            self._accumulated_samples = 0
                            self._silent_samples = 0
            return

        # ── Silero VAD (GPU) ──
        import torch
        audio_tensor = torch.from_numpy(audio_chunk).float()

        try:
            speech_prob = self._vad_model(audio_tensor, self.sample_rate).item()
        except Exception:
            return

        if speech_prob >= self.speech_threshold:
            self._silent_samples = 0
            if not self._is_speaking:
                self._is_speaking = True
                self._accumulated = [audio_chunk]
                self._accumulated_samples = chunk_samples
                if self._on_speech_start:
                    self._on_speech_start()
            else:
                self._accumulated.append(audio_chunk)
                self._accumulated_samples += chunk_samples
            if self._accumulated_samples >= self.max_speech_samples:
                self._end_segment()
        else:
            if self._is_speaking:
                self._accumulated.append(audio_chunk)
                self._accumulated_samples += chunk_samples
                self._silent_samples += chunk_samples
                if self._silent_samples >= self.silence_samples:
                    if self._accumulated_samples >= self.min_speech_samples:
                        self._end_segment()
                    else:
                        self._is_speaking = False
                        self._accumulated = []
                        self._accumulated_samples = 0
                        self._silent_samples = 0

    def _end_segment(self):
        """Finalize the current speech segment and notify."""
        if not self._is_speaking or len(self._accumulated) == 0:
            self._is_speaking = False
            return

        # Convert to int16 PCM bytes (what Whisper expects)
        full = np.concatenate(self._accumulated)
        int16_data = (full * 32767).astype(np.int16)
        pcm_bytes = int16_data.tobytes()

        self._is_speaking = False
        self._accumulated = []
        self._accumulated_samples = 0
        self._silent_samples = 0

        if self._on_speech_end:
            self._on_speech_end(pcm_bytes)

    def reset(self):
        """Reset VAD state — discard any accumulated audio."""
        self._is_speaking = False
        self._accumulated = []
        self._accumulated_samples = 0
        self._silent_samples = 0

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

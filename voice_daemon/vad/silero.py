"""Silero VAD — voice activity detection.

Prevents Whisper from eating silence.
Only sends audio to STT when someone is actually speaking.

Silero VAD is ONNX-based, runs locally, no cloud dependency.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Optional


class SileroVAD:
    """Voice Activity Detection using Silero VAD via torch.hub or onnxruntime.

    Architecture:
      Audio chunks flow in → VAD scores flow out → threshold triggers speech/silence.
    """

    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000,
                 min_speech_duration: float = 0.3, silence_duration: float = 1.5):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.min_speech_duration = min_speech_duration
        self.silence_duration = silence_duration
        self._model = None
        self._get_speech_ts = None
        self._loaded = False

    def load(self) -> bool:
        """Load the Silero VAD model. Returns True on success."""
        try:
            import torch
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
            )
            self._model = model
            self._get_speech_ts = utils[0]
            self._loaded = True
            return True
        except ImportError:
            return False
        except Exception:
            return False

    @property
    def is_available(self) -> bool:
        return self._loaded

    def detect(self, audio_chunk: bytes) -> float:
        """Run VAD on a chunk of int16 PCM audio. Returns speech probability [0, 1]."""
        if not self._loaded:
            return 0.0
        try:
            import torch
            import numpy as np
            # Convert int16 bytes to float32 tensor
            samples = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            tensor = torch.from_numpy(samples)
            speech_prob = self._model(tensor, self.sample_rate).item()
            return speech_prob
        except Exception:
            return 0.0


class SpeechDetector:
    """Stateful speech detector built on VAD.

    Tracks: is someone speaking right now? Has a complete utterance ended?
    """

    def __init__(self, vad: SileroVAD):
        self.vad = vad
        self._is_speaking = False
        self._speech_start_time = 0.0
        self._silence_start_time = 0.0
        self._on_speech_start = None
        self._on_speech_end = None

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    def on_speech_start(self, callback):
        """Register callback for speech start event."""
        self._on_speech_start = callback

    def on_speech_end(self, callback):
        """Register callback for speech end event."""
        self._on_speech_end = callback

    def process(self, audio_chunk: bytes) -> Optional[str]:
        """Process one audio chunk. Returns 'start', 'end', or None.

        Called continuously with audio chunks from the mic.
        """
        prob = self.vad.detect(audio_chunk)
        now = time.time()

        if prob >= self.vad.threshold:
            # Speech detected
            if not self._is_speaking:
                self._is_speaking = True
                self._speech_start_time = now
                if self._on_speech_start:
                    self._on_speech_start()
                return "start"
            self._silence_start_time = 0.0
        else:
            # Silence
            if self._is_speaking:
                if self._silence_start_time == 0.0:
                    self._silence_start_time = now
                silence_elapsed = now - self._silence_start_time
                # Check minimum speech duration
                speech_elapsed = now - self._speech_start_time
                if (silence_elapsed >= self.vad.silence_duration and
                        speech_elapsed >= self.vad.min_speech_duration):
                    self._is_speaking = False
                    self._silence_start_time = 0.0
                    if self._on_speech_end:
                        self._on_speech_end()
                    return "end"

        return None

"""Audio stream recorder — continuous buffered recording.

Wraps Microphone to provide buffered audio segments for VAD processing.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Optional

from voice_daemon.audio.microphone import Microphone


class AudioRecorder:
    """Buffered audio recorder. Continuous recording with segment extraction.

    Architecture:
      Mic → ring buffer → VAD checks for speech → extract segment → STT
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 chunk_size: int = 1024, buffer_seconds: float = 3.0):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.buffer_size = int(sample_rate * buffer_seconds / chunk_size)  # in chunks
        self._buffer: deque[bytes] = deque(maxlen=self.buffer_size)
        self._mic: Optional[Microphone] = None
        self._recording = False
        self._accumulated: list[bytes] = []

    def start(self, device_index: Optional[int] = None) -> bool:
        """Start the microphone and begin buffering."""
        self._mic = Microphone(
            sample_rate=self.sample_rate,
            channels=self.channels,
            device_index=device_index,
            chunk_size=self.chunk_size,
        )
        if not self._mic.open():
            return False
        self._recording = True
        return True

    def read_chunk(self) -> Optional[bytes]:
        """Read a single chunk from the mic into the buffer. Returns the chunk."""
        if not self._mic or not self._recording:
            return None
        chunk = self._mic.read(self.chunk_size)
        if chunk:
            self._buffer.append(chunk)
        return chunk

    def fill_buffer(self, duration_seconds: float = 1.0):
        """Fill the buffer with duration_seconds of audio data. Blocking."""
        chunks_needed = int(self.sample_rate * duration_seconds / self.chunk_size)
        for _ in range(chunks_needed):
            self.read_chunk()
            time.sleep(self.chunk_size / self.sample_rate)

    def start_segment(self):
        """Begin accumulating a speech segment (called when VAD detects speech)."""
        self._accumulated = list(self._buffer)  # include pre-speech buffer

    def accumulate(self) -> Optional[bytes]:
        """Read one chunk and add to the segment. Returns the chunk."""
        chunk = self.read_chunk()
        if chunk and self._accumulated is not None:
            self._accumulated.append(chunk)
        return chunk

    def stop_segment(self) -> bytes:
        """Stop accumulating and return the full speech segment as raw PCM bytes."""
        segment = b''.join(self._accumulated)
        self._accumulated = []
        return segment

    @property
    def segment_duration(self) -> float:
        """Duration of current accumulated segment in seconds."""
        if not self._accumulated:
            return 0.0
        total_samples = sum(len(c) // 2 for c in self._accumulated)  # int16 = 2 bytes
        return total_samples / self.sample_rate

    def stop(self):
        """Stop recording and close microphone."""
        self._recording = False
        if self._mic:
            self._mic.close()
            self._mic = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

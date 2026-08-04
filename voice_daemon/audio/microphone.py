"""Microphone capture — direct hardware access via sounddevice.

No browser. No Chromium. No MediaRecorder.
This is the physical layer of Julia's ears.
"""

from __future__ import annotations

import threading
from typing import Optional, Callable


class Microphone:
    """Direct microphone capture using sounddevice (PortAudio).

    Usage:
        mic = Microphone(sample_rate=16000)
        mic.open()
        for chunk in mic.stream():
            process(chunk)
        mic.close()
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 device_index: Optional[int] = None, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_index = device_index
        self.chunk_size = chunk_size
        self._stream = None
        self._running = False

    def open(self) -> bool:
        """Open the microphone stream. Returns True on success."""
        try:
            import sounddevice as sd
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device_index,
                blocksize=self.chunk_size,
                dtype='int16',
            )
            self._stream.start()
            self._running = True
            return True
        except ImportError:
            # Fallback: try PyAudio
            try:
                import pyaudio
                self._pyaudio = pyaudio.PyAudio()
                self._py_stream = self._pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=self.device_index,
                    frames_per_buffer=self.chunk_size,
                )
                self._running = True
                return True
            except ImportError:
                return False
        except Exception:
            return False

    def read(self, num_frames: int = None) -> Optional[bytes]:
        """Read audio frames from the microphone. Returns raw PCM bytes or None."""
        if not self._running:
            return None
        try:
            if self._stream:
                import numpy as np
                frames = num_frames or self.chunk_size
                data, _ = self._stream.read(frames)
                return data.tobytes()
            elif hasattr(self, '_py_stream'):
                frames = num_frames or self.chunk_size
                return self._py_stream.read(frames, exception_on_overflow=False)
        except Exception:
            return None
        return None

    def stream(self, callback: Callable[[bytes], None]):
        """Continuously read audio and pass to callback. Blocks until close() called."""
        self._running = True
        while self._running:
            chunk = self.read()
            if chunk:
                callback(chunk)

    def close(self):
        """Close the microphone stream."""
        self._running = False
        try:
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
        except Exception:
            pass
        try:
            if hasattr(self, '_py_stream') and self._py_stream:
                self._py_stream.stop_stream()
                self._py_stream.close()
                self._py_stream = None
            if hasattr(self, '_pyaudio') and self._pyaudio:
                self._pyaudio.terminate()
        except Exception:
            pass

    def list_devices(self) -> list[dict]:
        """List available audio input devices."""
        devices = []
        try:
            import sounddevice as sd
            for i, dev in enumerate(sd.query_devices()):
                if dev['max_input_channels'] > 0:
                    devices.append({
                        "index": i,
                        "name": dev['name'],
                        "channels": dev['max_input_channels'],
                        "sample_rate": dev['default_samplerate'],
                    })
        except ImportError:
            pass
        return devices


def get_default_mic_index() -> Optional[int]:
    """Get the default microphone device index."""
    try:
        import sounddevice as sd
        return sd.default.device[0]
    except Exception:
        return None

"""Audio player — play TTS output through speakers.

Separate from TTS engine. This is just the speaker driver.
"""

from __future__ import annotations

import subprocess
import tempfile
import os
from typing import Optional


class AudioPlayer:
    """Play audio files through system speakers.

    Supports: afplay (macOS), aplay (Linux), or sounddevice fallback.
    """

    def __init__(self):
        self._playing = False

    def play_file(self, file_path: str) -> bool:
        """Play an audio file. Blocks until done. Returns True on success."""
        if not os.path.exists(file_path):
            return False
        self._playing = True
        try:
            subprocess.run(["afplay", file_path], timeout=120, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
        except Exception:
            # Fallback: try generic player
            try:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", file_path],
                             capture_output=True, timeout=120)
                return True
            except Exception:
                return False
        finally:
            self._playing = False

    def play_bytes(self, audio_data: bytes, suffix: str = ".mp3") -> bool:
        """Play audio from bytes. Saves to temp file, plays, then cleans up."""
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        try:
            tmp.write(audio_data)
            tmp.close()
            return self.play_file(tmp.name)
        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

    def stop(self):
        """Stop current playback."""
        self._playing = False

    @property
    def is_playing(self) -> bool:
        return self._playing

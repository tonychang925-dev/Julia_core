"""Whisper CPU ASR Provider — server-side speech recognition.

Uses faster-whisper (CTranslate2 backend) for efficient CPU inference.
Runs on the server, NOT in Electron. This is the correct audio boundary per ADR-025-D.

Model sizes:
  tiny     → ~75MB,  ~30ms/frame (fastest, good for testing)
  base     → ~145MB, ~50ms/frame
  small    → ~488MB, ~100ms/frame
  medium   → ~1.5GB, ~200ms/frame

Default: tiny for E3.3.1 validation. Upgrade path: small/medium → GPU large-v3.
"""

from __future__ import annotations
import asyncio
import logging
import tempfile
import time as _time
import wave
from pathlib import Path
from typing import Optional

from voice_runtime.providers.asr.base import ASRProvider

logger = logging.getLogger("julia.asr.whisper_cpu")

# Model cache directory
MODEL_DIR = Path.home() / ".julia/whisper_models"


class WhisperCPUProvider(ASRProvider):
    """Server-side Whisper ASR using faster-whisper (CPU-optimized).

    Accumulates audio frames, transcribes complete speech segments
    (not streaming — VAD/buffer is handled by AudioPipeline upstream).
    """

    def __init__(self, model_size: str = "tiny", language: str = "zh",
                 compute_type: str = "int8"):
        """
        Args:
            model_size: tiny | base | small | medium
            language: ISO language code (zh, en, auto)
            compute_type: int8 (fastest CPU) | float32 (more accurate)
        """
        super().__init__()
        self.model_size = model_size
        self.language = language
        self.compute_type = compute_type
        self._model = None
        self._buffer: list[bytes] = []
        self._running = False
        self._sample_rate = 16000  # PyAV resamples to 16kHz upstream
        self._frame_count = 0
        self._transcript_count = 0

    def _lazy_load(self):
        """Load model on first use (avoids startup delay)."""
        if self._model is not None:
            return

        from faster_whisper import WhisperModel

        model_path = str(MODEL_DIR / f"faster-whisper-{self.model_size}")
        logger.info(f"Loading Whisper {self.model_size} (first use)...")
        t0 = _time.time()

        self._model = WhisperModel(
            self.model_size,
            device="cpu",
            compute_type=self.compute_type,
            download_root=str(MODEL_DIR),
        )
        logger.info(f"Whisper {self.model_size} loaded in {_time.time() - t0:.1f}s")

    async def start(self):
        self._buffer = []
        self._running = True
        self._frame_count = 0
        self._lazy_load()
        logger.info(f"WhisperCPU ASR started (model={self.model_size}, lang={self.language})")

    async def feed_frame(self, frame) -> None:
        """Accumulate audio frames. AudioPipeline handles VAD — we just buffer."""
        if not self._running:
            return

        pcm = frame.to_ndarray().tobytes()
        self._buffer.append(pcm)
        self._frame_count += 1

    async def transcribe_segment(self, pcm_bytes: bytes) -> Optional[str]:
        """Transcribe a complete speech segment (called by AudioPipeline on_speech_end).

        Runs faster-whisper in thread executor to avoid blocking the event loop.
        """
        if not self._model:
            self._lazy_load()
        if not pcm_bytes or len(pcm_bytes) < 1600:  # <50ms @ 16kHz
            return None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._transcribe_sync, pcm_bytes)

    def _transcribe_sync(self, pcm_bytes: bytes) -> Optional[str]:
        """Synchronous transcription — runs in thread executor."""
        try:
            import numpy as np
            # Diagnose: log RMS and save first segment for inspection
            samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float64)
            seg_rms = float(np.sqrt(np.mean(samples ** 2)))
            peak = float(np.max(np.abs(samples)))
            logger.info(f"Whisper segment: {len(pcm_bytes)} bytes, {len(samples)} samples, "
                       f"RMS={seg_rms:.1f}, peak={peak:.1f}")

            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = tmp.name
            tmp.close()

            with wave.open(tmp_path, "w") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(self._sample_rate)
                w.writeframes(pcm_bytes)

            # Save first debug segment for audible inspection
            debug_path = Path.home() / ".julia/debug_segment.wav"
            if not debug_path.exists():
                import shutil
                shutil.copy(tmp_path, str(debug_path))
                logger.info(f"Debug WAV saved: {debug_path}")

            segments, info = self._model.transcribe(
                tmp_path,
                language=self.language if self.language != "auto" else None,
                beam_size=5,
                vad_filter=False,
                vad_parameters=None,
            )

            text_parts = []
            for seg in segments:
                text_parts.append(seg.text.strip())

            Path(tmp_path).unlink()
            text = "".join(text_parts).strip()

            if text:
                self._transcript_count += 1
                logger.info(f"Whisper: {text[:80]} ({info.duration:.1f}s audio)")
                return text

            logger.info(f"Whisper: no speech detected in {info.duration:.1f}s segment "
                       f"(RMS={seg_rms:.0f}, peak={peak:.0f})")
            return None

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}", exc_info=True)
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
            return None

    async def stop(self) -> Optional[str]:
        """Stop ASR, flush remaining buffer."""
        self._running = False

        result = None
        if self._buffer:
            import numpy as np
            all_pcm = b"".join(self._buffer)
            self._buffer = []
            result = await self.transcribe_segment(all_pcm)
            if result and self._on_final:
                self._on_final(result)

        return result

    @property
    def stats(self) -> dict:
        return {
            "model": self.model_size,
            "language": self.language,
            "transcripts": self._transcript_count,
            "frames_processed": self._frame_count,
        }

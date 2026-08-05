"""TTS Audio Track — server-side outgoing WebRTC audio for Julia's voice.

E3.6 Full Duplex: Julia's speech flows as PCM through WebRTC, giving Chromium
AEC the render reference signal for echo cancellation.

Rules (frozen):
  1. PTS is monotonic — NEVER resets, even after interrupt.
  2. generation_id is monotonic — interrupt() increments it.
  3. Stale generations are rejected — old TTS cannot push to new generation.
  4. Queue capped at 50 frames (1 second) — no infinite buffering.
  5. interrupt() flushes queue + pushes None sentinel to unblock recv().

PCM format: s16le, 48kHz, mono, 20ms frames (960 samples = 1920 bytes).
"""

from __future__ import annotations

import asyncio
import logging
from fractions import Fraction

from aiortc import MediaStreamTrack
from av import AudioFrame

logger = logging.getLogger("julia.webrtc.tts")

SAMPLES_PER_FRAME = 960       # 20ms at 48kHz
BYTES_PER_FRAME = SAMPLES_PER_FRAME * 2  # int16 mono = 1920 bytes
MAX_QUEUE_FRAMES = 50          # 1 second cap
SAMPLE_RATE = 48_000


class TTSAudioTrack(MediaStreamTrack):
    """Server-side outgoing audio track for Julia's TTS output."""

    kind = "audio"

    def __init__(self):
        super().__init__()
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._pts = 0                      # monotonic, never resets
        self._generation = 0               # monotonic, incremented by interrupt()
        self._active_generation = 0        # current valid generation for enqueue
        self._pending_count = 0            # actual PCM frames in queue (excludes sentinels)

    # ── aiortc interface ──────────────────────────────────────────────────

    async def recv(self) -> AudioFrame:
        """Called by aiortc for each outgoing audio frame."""
        while True:
            item = await self._queue.get()
            if item is None:
                continue  # sentinel from interrupt/end, skip

            self._pending_count -= 1
            frame = AudioFrame(format="s16", layout="mono", samples=SAMPLES_PER_FRAME)
            frame.planes[0].update(item)
            frame.sample_rate = SAMPLE_RATE
            frame.pts = self._pts
            frame.time_base = Fraction(1, SAMPLE_RATE)

            self._pts += SAMPLES_PER_FRAME
            return frame

    # ── Generation lifecycle ──────────────────────────────────────────────

    def begin_generation(self) -> int:
        """Start a new TTS generation. Returns generation id for enqueue checks."""
        self._generation += 1
        self._active_generation = self._generation
        logger.debug(f"TTS generation {self._generation} started")
        return self._generation

    def end_generation(self) -> None:
        """Mark current generation complete. Push None sentinel so recv() doesn't
        block forever on an empty queue."""
        logger.debug(f"TTS generation {self._active_generation} ended")
        try:
            self._queue.put_nowait(None)
        except asyncio.QueueFull:
            pass

    def is_current(self, generation: int) -> bool:
        """Check if the given generation is still the active one."""
        return generation == self._active_generation

    # ── Enqueue ───────────────────────────────────────────────────────────

    async def enqueue_pcm(self, pcm_s16le: bytes, generation: int = 0) -> bool:
        """Enqueue one PCM frame. Rejects stale generations.

        Returns True if enqueued, False if rejected (stale generation).
        """
        if len(pcm_s16le) != BYTES_PER_FRAME:
            raise ValueError(
                f"Expected {BYTES_PER_FRAME} bytes, got {len(pcm_s16le)}"
            )

        # Reject stale generations
        if generation != self._active_generation:
            return False

        # Queue cap: drop oldest if full
        if self._pending_count >= MAX_QUEUE_FRAMES:
            try:
                discarded = self._queue.get_nowait()
                if discarded is not None:
                    self._pending_count -= 1
            except asyncio.QueueEmpty:
                pass

        await self._queue.put(pcm_s16le)
        self._pending_count += 1
        return True

    async def enqueue_silence(self, duration_ms: int = 20, generation: int = 0) -> int:
        """Enqueue silence frames. Returns number of frames enqueued."""
        frames = max(1, duration_ms // 20)
        silence = b"\x00" * BYTES_PER_FRAME
        count = 0
        for _ in range(frames):
            if await self.enqueue_pcm(silence, generation):
                count += 1
        return count

    # ── Interrupt ─────────────────────────────────────────────────────────

    def interrupt(self) -> int:
        """Cancel current speech. Returns the NEW generation id.

        Flushes all queued frames. Pushes None sentinel to unblock recv().
        PTS is NOT reset — it remains monotonic.
        """
        self._generation += 1
        self._active_generation = self._generation

        flushed = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                flushed += 1
            except asyncio.QueueEmpty:
                break
        self._pending_count = 0

        # Unblock recv()
        try:
            self._queue.put_nowait(None)
        except asyncio.QueueFull:
            pass

        if flushed > 0:
            logger.info(f"TTS interrupted: gen={self._generation}, "
                       f"flushed={flushed}frames ({flushed * 20}ms)")
        return self._generation

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def active_generation(self) -> int:
        return self._active_generation

    @property
    def pending_frames(self) -> int:
        return self._pending_count

    @property
    def pending_ms(self) -> int:
        return self._pending_count * 20

    @property
    def pts(self) -> int:
        return self._pts

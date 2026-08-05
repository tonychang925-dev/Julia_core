"""E3.6 PCM20msPacketizer + TTSAudioTrack Generation Race Tests.

Validates:
  A. Packetizer: correct framing for all input sizes
  B. Generation race: stale gen rejected, PTS monotonic, queue capped
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from voice_runtime.pipeline.pcm_packetizer import PCM20msPacketizer, FRAME_BYTES


# ── A. Packetizer Unit Tests ─────────────────────────────────────────────

class TestPacketizer:
    """PCM20msPacketizer: frame boundary correctness."""

    def test_empty_feed_returns_nothing(self):
        p = PCM20msPacketizer()
        assert p.feed(b"") == []
        assert p.pending_bytes == 0

    def test_exact_one_frame(self):
        p = PCM20msPacketizer()
        data = b"\x01" * FRAME_BYTES
        frames = p.feed(data)
        assert len(frames) == 1
        assert len(frames[0]) == FRAME_BYTES
        assert frames[0] == data
        assert p.pending_bytes == 0

    def test_less_than_one_frame(self):
        p = PCM20msPacketizer()
        frames = p.feed(b"\x02" * 100)
        assert frames == []  # no complete frame yet
        assert p.pending_bytes == 100

    def test_exactly_one_byte_short(self):
        p = PCM20msPacketizer()
        frames = p.feed(b"\x03" * (FRAME_BYTES - 1))
        assert frames == []
        assert p.pending_bytes == FRAME_BYTES - 1

    def test_exactly_one_byte_over(self):
        p = PCM20msPacketizer()
        frames = p.feed(b"\x04" * (FRAME_BYTES + 1))
        assert len(frames) == 1
        assert len(frames[0]) == FRAME_BYTES
        assert p.pending_bytes == 1

    def test_two_exact_frames(self):
        p = PCM20msPacketizer()
        data = b"\x05" * (FRAME_BYTES * 2)
        frames = p.feed(data)
        assert len(frames) == 2
        for f in frames:
            assert len(f) == FRAME_BYTES
        assert p.pending_bytes == 0

    def test_random_chunks(self):
        """Feed random-length chunks, verify total bytes preserved."""
        import random
        random.seed(42)

        total_in = 0
        total_out = 0
        p = PCM20msPacketizer()

        for _ in range(200):
            chunk_len = random.randint(1, FRAME_BYTES * 3)
            chunk = bytes([random.randint(0, 255) for _ in range(chunk_len)])
            total_in += chunk_len
            for f in p.feed(chunk):
                assert len(f) == FRAME_BYTES
                total_out += FRAME_BYTES

        # Flush tail
        tail = p.flush()
        if tail:
            assert len(tail) == FRAME_BYTES
            total_out += FRAME_BYTES

        # Total bytes out should be ceil(total_in / FRAME_BYTES) * FRAME_BYTES
        expected = ((total_in + FRAME_BYTES - 1) // FRAME_BYTES) * FRAME_BYTES
        assert total_out == expected, f"in={total_in}, out={total_out}, expected={expected}"

    def test_flush_pads_with_zeros(self):
        p = PCM20msPacketizer()
        data = b"\x06" * 100
        p.feed(data)
        tail = p.flush()
        assert tail is not None
        assert len(tail) == FRAME_BYTES
        # First 100 bytes should be \x06, rest should be \x00
        assert tail[:100] == data
        assert tail[100:] == b"\x00" * (FRAME_BYTES - 100)

    def test_flush_empty_returns_none(self):
        p = PCM20msPacketizer()
        assert p.flush() is None

    def test_cross_feed_carry(self):
        """Tail from first feed carries into second feed."""
        p = PCM20msPacketizer()
        # Feed 1000 bytes → no frame
        p.feed(b"\x07" * 1000)
        assert p.pending_bytes == 1000
        # Feed another 1000 bytes → should produce 1 frame (1920) with 80 carry
        frames = p.feed(b"\x08" * 1000)
        assert len(frames) == 1
        assert p.pending_bytes == 80
        # Flush
        tail = p.flush()
        assert tail is not None
        assert p.pending_bytes == 0

    def test_new_generation_does_not_carry_old_tail(self):
        """After one generation's flush, a new packetizer should start clean."""
        p = PCM20msPacketizer()
        p.feed(b"\x09" * 1000)
        assert p.pending_bytes > 0
        # Simulate new generation: fresh packetizer
        p2 = PCM20msPacketizer()
        assert p2.pending_bytes == 0
        frames = p2.feed(b"\x0a" * FRAME_BYTES)
        assert len(frames) == 1

    def test_very_large_input(self):
        p = PCM20msPacketizer()
        # 1 MB of data
        data = b"\x0b" * (1024 * 1024)
        frames = p.feed(data)
        expected_frames = len(data) // FRAME_BYTES
        assert len(frames) == expected_frames
        for f in frames:
            assert len(f) == FRAME_BYTES


# ── B. TTSAudioTrack Generation Race Tests ───────────────────────────────

class TestTTSGenerationRace:
    """TTSAudioTrack: generation isolation, monotonic PTS, queue cap."""

    @pytest.mark.asyncio
    async def test_stale_generation_rejected(self):
        from voice_runtime.transport.webrtc.tts_track import TTSAudioTrack
        track = TTSAudioTrack()

        gen1 = track.begin_generation()
        assert track.is_current(gen1)

        # Enqueue some frames
        frame = b"\x0c" * 1920
        assert await track.enqueue_pcm(frame, gen1)
        assert track.pending_frames == 1

        # Interrupt → gen1 stale
        gen2 = track.interrupt()
        assert gen2 != gen1
        assert not track.is_current(gen1)
        assert track.is_current(gen2)

        # Stale gen1 enqueue should be rejected
        assert not await track.enqueue_pcm(frame, gen1)
        assert track.pending_frames == 0  # queue was flushed

    @pytest.mark.asyncio
    async def test_pts_monotonic_across_generations(self):
        from voice_runtime.transport.webrtc.tts_track import TTSAudioTrack
        track = TTSAudioTrack()

        pts_before = track.pts

        gen1 = track.begin_generation()
        frame = b"\x0d" * 1920
        for _ in range(5):
            await track.enqueue_pcm(frame, gen1)

        track.interrupt()
        gen2 = track.begin_generation()
        for _ in range(3):
            await track.enqueue_pcm(frame, gen2)

        # PTS never decreased
        assert track.pts >= pts_before

    @pytest.mark.asyncio
    async def test_queue_cap(self):
        """Queue should not exceed MAX_QUEUE_FRAMES (50)."""
        from voice_runtime.transport.webrtc.tts_track import TTSAudioTrack
        track = TTSAudioTrack()

        gen = track.begin_generation()
        frame = b"\x0e" * 1920

        # Enqueue more than cap
        for _ in range(60):
            await track.enqueue_pcm(frame, gen)

        # Should be capped at 50
        assert track.pending_frames <= 50
        assert track.pending_ms <= 1000

    @pytest.mark.asyncio
    async def test_interrupt_flushes_queue(self):
        from voice_runtime.transport.webrtc.tts_track import TTSAudioTrack
        track = TTSAudioTrack()

        gen1 = track.begin_generation()
        frame = b"\x0f" * 1920
        for _ in range(10):
            await track.enqueue_pcm(frame, gen1)
        assert track.pending_frames == 10

        track.interrupt()
        assert track.pending_frames == 0

    @pytest.mark.asyncio
    async def test_generation_id_monotonic(self):
        """generation_id only increases, never resets to 0."""
        from voice_runtime.transport.webrtc.tts_track import TTSAudioTrack
        track = TTSAudioTrack()

        gen1 = track.begin_generation()
        assert gen1 > 0
        gen2 = track.interrupt()
        assert gen2 > gen1
        gen3 = track.begin_generation()
        assert gen3 > gen2
        # Interrupt without begin should also increment
        gen4 = track.interrupt()
        assert gen4 > gen3

    @pytest.mark.asyncio
    async def test_race_stale_enqueue_after_interrupt(self):
        """Simulate: gen1 enqueues, interrupt, gen1 task still produces frames.

        All gen1 frames must be rejected.
        """
        from voice_runtime.transport.webrtc.tts_track import TTSAudioTrack
        track = TTSAudioTrack()

        gen1 = track.begin_generation()
        frame = b"\x10" * 1920

        # Enqueue 10 frames of gen1
        for _ in range(10):
            await track.enqueue_pcm(frame, gen1)

        # Interrupt mid-stream
        gen2 = track.interrupt()

        # gen1 task still running — tries to enqueue 5 more
        accepted = 0
        for _ in range(5):
            if await track.enqueue_pcm(frame, gen1):
                accepted += 1
        assert accepted == 0, "All stale gen1 frames must be rejected"

        # gen2 enqueues normally
        frame2 = b"\x11" * 1920
        for _ in range(3):
            assert await track.enqueue_pcm(frame2, gen2)
        assert track.pending_frames == 3


# ── C. PCM20msPacketizer + TTSAudioTrack Integration ─────────────────────

class TestPacketizerTrackIntegration:
    """Packetizer output feeds directly into TTSAudioTrack."""

    @pytest.mark.asyncio
    async def test_packetizer_to_track(self):
        from voice_runtime.transport.webrtc.tts_track import TTSAudioTrack
        track = TTSAudioTrack()
        p = PCM20msPacketizer()
        gen = track.begin_generation()

        # Feed 5000 bytes → 2 full frames + 1160 carry
        data = b"\x12" * 5000
        total_enqueued = 0
        for f in p.feed(data):
            assert await track.enqueue_pcm(f, gen)
            total_enqueued += 1
        assert total_enqueued == 2  # 5000 // 1920 = 2
        assert p.pending_bytes == 1160

        # Flush tail → 3rd frame
        tail = p.flush()
        assert tail is not None
        assert await track.enqueue_pcm(tail, gen)

        assert track.pending_frames == 3
        assert p.pending_bytes == 0

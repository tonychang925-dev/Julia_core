"""PCM 20ms Packetizer — chops arbitrary PCM into fixed-size WebRTC frames.

E3.6: Each frame must be exactly 960 samples × 1 channel × 2 bytes = 1920 bytes.
Carries incomplete tail between feed() calls for seamless streaming.
"""

from __future__ import annotations

FRAME_BYTES = 960 * 2  # 1920 bytes = 20ms @ 48kHz mono s16le


class PCM20msPacketizer:
    """Accumulates PCM bytes, emits exactly 1920-byte frames.

    Usage:
        pkt = PCM20msPacketizer()
        while audio_available:
            frames = pkt.feed(chunk)
            for f in frames:
                await tts_track.enqueue_pcm(f)
        tail = pkt.flush()
        if tail:
            await tts_track.enqueue_pcm(tail)
    """

    def __init__(self):
        self._carry = bytearray()

    def feed(self, pcm: bytes) -> list[bytes]:
        """Feed raw PCM bytes. Returns list of complete 1920-byte frames."""
        self._carry.extend(pcm)
        frames: list[bytes] = []

        while len(self._carry) >= FRAME_BYTES:
            frames.append(bytes(self._carry[:FRAME_BYTES]))
            del self._carry[:FRAME_BYTES]

        return frames

    def flush(self) -> bytes | None:
        """Return remaining partial frame, zero-padded to 1920 bytes."""
        if not self._carry:
            return None
        frame = bytes(self._carry).ljust(FRAME_BYTES, b"\x00")
        self._carry.clear()
        return frame

    @property
    def pending_bytes(self) -> int:
        return len(self._carry)

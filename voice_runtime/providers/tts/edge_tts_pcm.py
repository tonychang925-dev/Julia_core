"""Edge TTS → PCM Streaming Provider.

E3.6: Server-side TTS that outputs 48kHz mono s16le PCM frames
directly to a TTSAudioTrack. Replaces client-side Blob/MP3 playback.

Flow:
  Text → edge-tts streaming MP3 → av decode → resample 48kHz mono
  → PCM20msPacketizer → TTSAudioTrack.enqueue_pcm(gen)

Generation-aware: checks track generation before each enqueue.
Cancellable: cancel_event stops streaming immediately.
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

from voice_runtime.pipeline.pcm_packetizer import PCM20msPacketizer

logger = logging.getLogger("julia.tts.edge_pcm")

VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-10%"
PITCH = "+0Hz"
SAMPLE_RATE = 48000


class EdgeTTSPCMProvider:
    """Streams Edge TTS output as PCM frames to a TTSAudioTrack."""

    def __init__(self, voice: str = VOICE, rate: str = RATE, pitch: str = PITCH):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self._cancel: Optional[asyncio.Event] = None

    async def stream_to_track(self, text: str, track, generation: int) -> bool:
        """Stream TTS for `text` as PCM frames to `track`.

        Checks track.is_current(generation) before each frame.
        Returns True if completed normally, False if cancelled.
        """
        if not text:
            return True

        self._cancel = asyncio.Event()
        loop = asyncio.get_event_loop()

        try:
            import edge_tts

            # Step 1: edge-tts → MP3 file (streaming not directly supported,
            # but Communicate.save() is fast enough for sentence-level TTS)
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp_path = tmp.name
            tmp.close()

            comm = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch)
            await comm.save(tmp_path)

            if self._cancel.is_set():
                Path(tmp_path).unlink(missing_ok=True)
                return False

            # Step 2: MP3 → PCM → resample → packetize → enqueue
            result = await loop.run_in_executor(
                None, self._decode_and_enqueue, tmp_path, track, generation, self._cancel
            )
            Path(tmp_path).unlink(missing_ok=True)
            return result

        except Exception as e:
            logger.error(f"Edge TTS PCM error: {e}")
            return False
        finally:
            self._cancel = None

    def cancel(self):
        """Cancel current TTS stream."""
        if self._cancel:
            self._cancel.set()

    def _decode_and_enqueue(self, mp3_path: str, track, generation: int,
                            cancel: asyncio.Event) -> bool:
        """Synchronous: decode MP3, resample, packetize, enqueue via async callback.

        Runs in thread executor. Uses synchronous enqueue via asyncio.run_coroutine_threadsafe
        or simply blocks with a helper event loop.

        For simplicity: decode in thread, enqueue synchronously into asyncio.Queue.
        """
        try:
            import av
            import numpy as np

            container = av.open(mp3_path)
            audio_stream = next(s for s in container.streams if s.type == "audio")

            # Resampler: any input rate → 48kHz mono s16le
            resampler = av.AudioResampler(
                format="s16", layout="mono", rate=SAMPLE_RATE
            )

            packetizer = PCM20msPacketizer()
            loop = asyncio.get_event_loop()
            frames_enqueued = 0

            for packet in container.demux(audio_stream):
                if cancel.is_set():
                    return False

                for frame in resampler.resample(packet):
                    if cancel.is_set():
                        return False

                    pcm = frame.to_ndarray().tobytes()
                    for pcm_frame in packetizer.feed(pcm):
                        if cancel.is_set():
                            return False
                        # Enqueue synchronously via run_until_complete
                        # (we're in a thread executor, this is safe)
                        future = asyncio.run_coroutine_threadsafe(
                            track.enqueue_pcm(pcm_frame, generation), loop
                        )
                        try:
                            accepted = future.result(timeout=1)
                            if not accepted:
                                # Stale generation — stop
                                return False
                            frames_enqueued += 1
                        except Exception:
                            return False

            # Flush tail
            tail = packetizer.flush()
            if tail and not cancel.is_set():
                future = asyncio.run_coroutine_threadsafe(
                    track.enqueue_pcm(tail, generation), loop
                )
                try:
                    if future.result(timeout=1):
                        frames_enqueued += 1
                except Exception:
                    pass

            container.close()
            logger.info(f"Edge TTS: {frames_enqueued} frames ({frames_enqueued * 20}ms) enqueued")
            return True

        except Exception as e:
            logger.error(f"TTS decode/enqueue error: {e}")
            return False

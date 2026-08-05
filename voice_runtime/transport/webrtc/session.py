"""WebRTC Voice Session — wraps aiortc RTCPeerConnection for Gateway use.

One session per connected client. Manages SDP exchange and audio track receiving.
The Gateway calls create_session() → get_answer(). Audio tracks flow in.
"""

from __future__ import annotations
import logging
import time as _time
from typing import Optional, Callable

logger = logging.getLogger("julia.webrtc")

# aiortc is optional — installed separately for voice capabilities
try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
    from aiortc.contrib.media import MediaRelay
    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False
    RTCPeerConnection = None
    RTCSessionDescription = None
    MediaRelay = None


class WebRTCSession:
    """One WebRTC voice session. Handles SDP + audio track lifecycle."""

    def __init__(self, session_id: str = "", client_type: str = "electron",
                 asr_provider=None, audio_pipeline=None, on_transcript: Callable = None):
        self.id = session_id or f"rtc-{int(_time.time()*1000)}"
        self.client_type = client_type
        self.state = "created"
        self._pc: Optional[object] = None
        self._track_handler: Optional[Callable] = None
        self._pipeline = audio_pipeline                  # Audio Pipeline (E3.2-B)
        self._asr = asr_provider                         # ASR Provider (E3.3)
        self._on_transcript = on_transcript
        self.created_at = _time.strftime("%Y-%m-%d %H:%M:%S")
        self._audio_frames: int = 0
        self._final_text: str = ""

    async def create_answer(self, offer_sdp: str) -> str:
        """Process SDP offer, return SDP answer. Sets up audio track handler."""
        if not AIORTC_AVAILABLE:
            return self._build_text_answer(offer_sdp)

        self._pc = RTCPeerConnection()

        @self._pc.on("track")
        async def on_track(track):
            logger.info(f"[RTC] track received: kind={track.kind}")
            if track.kind == "audio":
                self.state = "listening"

                # Wire AudioPipeline → ASR for clean speech segments
                if self._pipeline and self._asr:
                    await self._asr.start()
                    if self._on_transcript:
                        self._asr.on_partial(lambda text: self._on_transcript(text, False))
                        self._asr.on_final(lambda text: self._on_transcript(text, True))
                    self._pipeline.on_speech_start(lambda: logger.info("VAD: speech started"))
                    self._pipeline.on_speech_end(lambda pcm: asyncio.ensure_future(
                        self._transcribe_segment(pcm)))

                while True:
                    try:
                        frame = await track.recv()
                        self._audio_frames += 1
                        if self._audio_frames % 50 == 0:
                            logger.info(f"[RTC] frame #{self._audio_frames}")
                        if self._pipeline:
                            await self._pipeline.push_frame(frame)
                        elif self._asr:
                            await self._asr.feed_frame(frame)
                        if self._track_handler:
                            self._track_handler(frame)
                    except Exception:
                        break

                # Track ended — flush remaining speech
                if self._pipeline and self._pipeline.is_speaking:
                    self._pipeline._emit_segment()
                if self._asr:
                    final = await self._asr.stop()
                    if final:
                        self._final_text = final
                        logger.info(f"[RTC] ASR final: {final}")
                        if self._on_transcript:
                            self._on_transcript(final, True)

        # Set remote description (offer)
        offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
        await self._pc.setRemoteDescription(offer)

        # Create answer
        answer = await self._pc.createAnswer()
        await self._pc.setLocalDescription(answer)
        self.state = "connected"
        logger.info(f"[RTC] session {self.id} connected")
        return self._pc.localDescription.sdp

    def on_audio_frame(self, handler: Callable):
        """Register handler for incoming audio frames."""
        self._track_handler = handler

    async def close(self):
        if self._pc:
            await self._pc.close()
        self.state = "closed"

    def _build_text_answer(self, offer_sdp: str) -> str:
        """Fallback SDP answer when aiortc is not installed."""
        self.state = "connected"
        return "\r\n".join([
            "v=0", "o=julia-gateway 0 1 IN IP4 127.0.0.1",
            "s=Julia Voice Session", "t=0 0",
            "m=audio 9 UDP/TLS/RTP/SAVPF 111",
            "c=IN IP4 127.0.0.1", "a=rtpmap:111 opus/48000/2",
            "a=ice-lite", "a=sendrecv",
        ]) + "\r\n"

    async def _transcribe_segment(self, pcm_bytes: bytes):
        """ASR on a complete speech segment → emit via on_transcript callback.

        Uses ASR Provider's transcribe_segment() if available (WhisperCPUProvider),
        or feed_frame through the provider's internal buffer as fallback.
        """
        if not self._asr or not self._on_transcript:
            return
        try:
            text = None

            # E3.3.1: Server-side ASR Provider with dedicated transcribe_segment
            if hasattr(self._asr, 'transcribe_segment'):
                text = await self._asr.transcribe_segment(pcm_bytes)
            else:
                # Fallback: Google Speech via speech_recognition
                import speech_recognition as sr
                import wave, tempfile
                from pathlib import Path

                r = sr.Recognizer()
                tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp_path = tmp.name; tmp.close()
                with wave.open(tmp_path, "w") as w:
                    w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000)
                    w.writeframes(pcm_bytes)
                with sr.AudioFile(tmp_path) as source:
                    sr_audio = r.record(source)
                Path(tmp_path).unlink()
                text = r.recognize_google(sr_audio, language="zh-CN")

            if text:
                self._final_text = text
                self._on_transcript(text, True)
        except Exception as e:
            logger.debug(f"ASR segment error: {e}")

    def to_dict(self) -> dict:
        return {"id": self.id, "client_type": self.client_type,
                "state": self.state, "audio_frames": self._audio_frames,
                "created_at": self.created_at}

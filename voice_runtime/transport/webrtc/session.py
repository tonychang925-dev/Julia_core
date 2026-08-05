"""WebRTC Voice Session — bidirectional audio for E3.6 Full Duplex.

One session per connected client:
  - Incoming: client mic → AudioPipeline(VAD) → ASR → transcript
  - Outgoing: TTS PCM → TTSAudioTrack → WebRTC → client speaker

Single PeerConnection, single audio engine on client.
Chromium AEC uses the TTS track as render reference for echo cancellation.
"""

from __future__ import annotations
import asyncio
import logging
import time as _time
from typing import Optional, Callable

logger = logging.getLogger("julia.webrtc")

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False
    RTCPeerConnection = None
    RTCSessionDescription = None

from voice_runtime.transport.webrtc.tts_track import TTSAudioTrack


class WebRTCSession:
    """One WebRTC voice session. Bidirectional: mic in, TTS out."""

    def __init__(self, session_id: str = "", client_type: str = "electron",
                 asr_provider=None, audio_pipeline=None, on_transcript: Callable = None):
        self.id = session_id or f"rtc-{int(_time.time()*1000)}"
        self.client_type = client_type
        self.state = "created"
        self._pc = None
        self._track_handler: Optional[Callable] = None
        self._pipeline = audio_pipeline
        self._asr = asr_provider
        self._on_transcript = on_transcript
        self.created_at = _time.strftime("%Y-%m-%d %H:%M:%S")
        self._audio_frames: int = 0
        self._final_text: str = ""
        self.tts_track: Optional[TTSAudioTrack] = None

    async def create_answer(self, offer_sdp: str) -> str:
        """Process SDP offer, set up bidirectional audio, return SDP answer."""
        if not AIORTC_AVAILABLE:
            return self._build_text_answer(offer_sdp)

        self._pc = RTCPeerConnection()

        # ── Outgoing: TTS audio track (server → client) ──
        # Gives Chromium AEC the render reference signal for echo cancellation.
        self.tts_track = TTSAudioTrack()
        self._pc.addTrack(self.tts_track)

        # ── Incoming: client mic track (client → server) ──
        @self._pc.on("track")
        async def on_track(track):
            logger.info(f"[RTC] track received: kind={track.kind}")
            if track.kind == "audio":
                self.state = "listening"
                await self._handle_incoming_audio(track)

        # ── SDP exchange ──
        offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
        await self._pc.setRemoteDescription(offer)

        answer = await self._pc.createAnswer()
        await self._pc.setLocalDescription(answer)
        self.state = "connected"
        logger.info(f"[RTC] session {self.id} connected (bidirectional)")
        return self._pc.localDescription.sdp

    async def _handle_incoming_audio(self, track):
        """Convert incoming audio → s16/mono/16kHz → VAD → ASR → transcript.

        Uses PyAV AudioResampler for guaranteed format conversion.
        No manual float↔int16 math — PyAV handles it correctly.
        """
        import av
        import numpy as np
        from pathlib import Path

        resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
        debug_saved = False

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

                # Log input format on first frame
                if self._audio_frames == 1:
                    arr = frame.to_ndarray()
                    logger.info(
                        f"[RTC] input audio: format={frame.format.name if hasattr(frame.format, 'name') else frame.format}, "
                        f"layout={frame.layout.name if hasattr(frame.layout, 'name') else frame.layout}, "
                        f"rate={frame.sample_rate}, samples={frame.samples}, "
                        f"ndarray_dtype={arr.dtype}, shape={arr.shape}"
                    )

                # PyAV resample → s16, mono, 16kHz (no manual type conversion)
                for converted in resampler.resample(frame):
                    pcm = np.asarray(converted.to_ndarray()).reshape(-1)

                    # AudioResampler output is already s16 int
                    if pcm.dtype != np.int16:
                        pcm = pcm.astype(np.int16, copy=False)

                    samples64 = pcm.astype(np.float64)
                    rms = float(np.sqrt(np.mean(samples64 ** 2)))
                    peak = int(np.max(np.abs(samples64)))

                    # Save first 3s as debug WAV
                    if not debug_saved and self._audio_frames % 50 == 0:
                        import wave as _wave
                        debug_path = Path.home() / ".julia/debug_converted.wav"
                        with _wave.open(str(debug_path), "w") as w:
                            w.setnchannels(1)
                            w.setsampwidth(2)
                            w.setframerate(16000)
                            w.writeframes(pcm.tobytes())
                        logger.info(f"[RTC] debug WAV saved: {debug_path} "
                                   f"(RMS={rms:.0f}, peak={peak}, {len(pcm)}samples)")
                        debug_saved = True

                    if self._audio_frames % 50 == 0:
                        logger.info(f"[RTC] frame #{self._audio_frames} "
                                   f"→ s16/16kHz: {len(pcm)}samples RMS={rms:.0f} peak={peak}")

                    pcm_bytes = pcm.astype("<i2", copy=False).tobytes()

                    if self._pipeline:
                        await self._pipeline.push_pcm(pcm_bytes, sample_rate=16000)
                    elif self._asr:
                        await self._asr.feed_frame(frame)

                if self._track_handler:
                    self._track_handler(frame)

            except Exception:
                break

        if self._pipeline and self._pipeline.is_speaking:
            self._pipeline._emit_segment()
        if self._asr:
            final = await self._asr.stop()
            if final:
                self._final_text = final
                logger.info(f"[RTC] ASR final: {final}")
                if self._on_transcript:
                    self._on_transcript(final, True)

    def on_audio_frame(self, handler: Callable):
        self._track_handler = handler

    async def close(self):
        if self._pc:
            await self._pc.close()
        self.state = "closed"

    # ── TTS (server → client) ────────────────────────────────────────────

    async def enqueue_tts_pcm(self, pcm_frame: bytes) -> None:
        """Enqueue one 20ms PCM frame for playback on client."""
        if self.tts_track:
            await self.tts_track.enqueue_pcm(pcm_frame)

    def interrupt_tts(self) -> None:
        """Cancel current TTS playback (barge-in)."""
        if self.tts_track:
            self.tts_track.interrupt()

    # ── Internal ─────────────────────────────────────────────────────────

    def _build_text_answer(self, offer_sdp: str) -> str:
        self.state = "connected"
        return "\r\n".join([
            "v=0", "o=julia-gateway 0 1 IN IP4 127.0.0.1",
            "s=Julia Voice Session", "t=0 0",
            "m=audio 9 UDP/TLS/RTP/SAVPF 111",
            "c=IN IP4 127.0.0.1", "a=rtpmap:111 opus/48000/2",
            "a=ice-lite", "a=sendrecv",
        ]) + "\r\n"

    async def _transcribe_segment(self, pcm_bytes: bytes):
        """ASR on a complete speech segment."""
        if not self._asr or not self._on_transcript:
            return
        try:
            text = None
            if hasattr(self._asr, 'transcribe_segment'):
                text = await self._asr.transcribe_segment(pcm_bytes)
            else:
                logger.info(f"ASR: using Google STT fallback for {len(pcm_bytes)} bytes PCM")
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
                logger.info(f"ASR transcript: {text[:80]}")
                self._on_transcript(text, True)
            else:
                logger.info(f"ASR: empty transcript for {len(pcm_bytes)} bytes PCM")
        except Exception as e:
            logger.error(f"ASR segment error: {e}", exc_info=True)

    def to_dict(self) -> dict:
        return {"id": self.id, "client_type": self.client_type,
                "state": self.state, "audio_frames": self._audio_frames,
                "created_at": self.created_at}

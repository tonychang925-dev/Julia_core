#!/usr/bin/env python3
"""Julia Voice Daemon v4.1.2 — Streaming VAD Pipeline.

Architecture:
  sounddevice (continuous) → Silero VAD → speech segments → Whisper STT
  → wake word check → Event Gateway (:9000) → LLM → TTS → Speaker

This is a thin client. It converts audio ↔ events.
All intelligence lives in the Julia Runtime.

Usage:
  /opt/miniconda3/envs/torch_env/bin/python -m voice_daemon.main
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path
from queue import Queue

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from voice_daemon.audio.mac_speech import StreamingMic, VADStreamProcessor
from voice_daemon.audio.player import AudioPlayer
from voice_daemon.audio.device import get_default_input_device
from voice_daemon.stt.whisper_client import WhisperClient
from voice_daemon.tts.elevenlabs import ElevenLabsTTS
from voice_daemon.wakeword.detector import _match_wake_word, WAKE_WORDS
from voice_daemon.presence.manager import PresenceManager, Presence
from voice_daemon.transport.websocket import WebSocketTransport
from voice_daemon.transport.protocol import (
    PRESENCE_CHANGED, TTS_SPEAK, TTS_CANCEL, ASSISTANT_REPLY, ERROR,
    presence_changed_event, tts_finished_event,
)

logger = logging.getLogger("julia.voice")


class JuliaVoiceDaemon:
    """Voice daemon with streaming VAD pipeline."""

    def __init__(self):
        # Audio
        dev = get_default_input_device()
        self.mic_index = dev['index'] if dev else None
        self.sample_rate = 16000

        # Streaming mic + VAD
        self.mic = StreamingMic(sample_rate=self.sample_rate, device_index=self.mic_index)
        self.vad_proc = VADStreamProcessor(sample_rate=self.sample_rate)

        # STT
        whisper_url = os.environ.get("WHISPER_SERVER_URL", "http://localhost:8001")
        self.whisper = WhisperClient(server_url=whisper_url)

        # TTS + Player
        self.tts = ElevenLabsTTS()
        self.player = AudioPlayer()

        # Transport
        runtime_url = os.environ.get("JULIA_RUNTIME_URL", "ws://localhost:9000/ws")
        self.transport = WebSocketTransport(runtime_url=runtime_url)

        # Presence
        self.presence = PresenceManager(initial=Presence.SLEEPING)
        self.presence.enable_journal()

        # State
        self._running = False
        self._wake_detected = False
        self._wake_word = ""
        self._loop: asyncio.AbstractEventLoop = None

        # Thread-safe queue for speech segments from audio thread → asyncio
        self._segment_queue: Queue = Queue()

    # ── Init ──────────────────────────────────────────────────────────────────

    def check_environment(self) -> dict:
        return {
            "mic": self.mic_index,
            "vad": self.vad_proc.is_loaded,
            "whisper": self.whisper.is_available(),
            "tts": self.tts.is_available,
            "runtime": self.transport.runtime_url,
        }

    # ── Event Handlers ────────────────────────────────────────────────────────

    def _setup_event_handlers(self):
        def on_tts_speak(event):
            text = event.data.get("text", "")
            emotion = event.data.get("emotion", "warm")
            if text:
                self.presence.transition(Presence.SPEAKING)
                def _speak():
                    self.tts.speak(text, emotion)
                    if self.transport.connected:
                        try:
                            loop = asyncio.get_running_loop()
                            asyncio.run_coroutine_threadsafe(
                                self.transport.send(tts_finished_event(0.0)), loop
                            )
                        except RuntimeError:
                            pass
                    self.presence.transition(Presence.IDLE)
                threading.Thread(target=_speak, daemon=True).start()

        def on_tts_cancel(event):
            self.player.stop()
            self.presence.transition(Presence.IDLE)

        def on_error(event):
            logger.error(f"Runtime error: {event.data.get('detail', '')}")

        self.transport.on(TTS_SPEAK, on_tts_speak)
        self.transport.on(TTS_CANCEL, on_tts_cancel)
        self.transport.on(ERROR, on_error)

        # Broadcast presence changes to Runtime
        def on_presence_change(new_state, old_state):
            if new_state != old_state and self.transport.connected:
                event = presence_changed_event(new_state.value)
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.run_coroutine_threadsafe(self.transport.send(event), loop)
                except RuntimeError:
                    pass
        self.presence.on_change(on_presence_change)

    # ── Audio Pipeline (runs in audio thread) ─────────────────────────────────

    def _on_audio_chunk(self, audio: np.ndarray):
        """Called by StreamingMic callback in audio thread."""
        self.vad_proc.process_chunk(audio)

    def _on_speech_end(self, pcm_bytes: bytes):
        """Called by VADStreamProcessor when a speech segment completes."""
        self._segment_queue.put(pcm_bytes)

    # ── Wake Detection + Speech Processing (runs in asyncio) ───────────────────

    async def _process_segment(self, pcm_bytes: bytes):
        """Transcribe a speech segment and check for wake word or process query."""
        if len(pcm_bytes) < self.sample_rate * 0.2 * 2:  # < 0.2s — too short
            return

        result = self.whisper.transcribe_bytes(pcm_bytes, suffix=".raw")
        text = result.get("text", "").strip()
        if not text:
            return

        logger.info(f"🎤 {text}")

        # Check if this is a wake word
        wake = _match_wake_word(text)
        if wake and not self._wake_detected:
            # Wake word detected!
            self._wake_detected = True
            self._wake_word = wake

            mode = "interrupt" if self.presence.state in (Presence.SPEAKING, Presence.THINKING) else "activate"
            logger.info(f"Wake: '{wake}' (mode={mode})")

            if mode == "interrupt":
                self.player.stop()
                await self.transport.send_cancel("wake_word_interrupt")

            self.presence.transition(Presence.LISTENING)
            await self.transport.send_wake(wake, text, mode)
            print(f"  ✅ 唤醒! 说你想说的...", flush=True)

        elif self._wake_detected:
            # Post-wake: this is the user's actual query
            self._wake_detected = False  # Reset for next wake cycle
            await self._process_query(text)

    async def _process_query(self, text: str):
        """Send user query to Julia Runtime."""
        self.presence.transition(Presence.THINKING)
        await self.transport.send_speech_final(text)
        print(f"  → Julia 思考中...", flush=True)
        # Response + TTS handled by event handlers

    # ── Main Loop ─────────────────────────────────────────────────────────────

    async def _main_loop(self):
        """Asyncio loop: drain segment queue, process speech."""
        while self._running:
            try:
                # Non-blocking check for new speech segments
                while not self._segment_queue.empty():
                    pcm = self._segment_queue.get_nowait()
                    await self._process_segment(pcm)
                await asyncio.sleep(0.05)  # ~20 checks/second
            except Exception as e:
                logger.error(f"Main loop error: {e}")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self):
        logger.info("Julia Voice Daemon v4.1.2 starting...")

        # Check env
        env = self.check_environment()
        vad_ok = self.vad_proc.load_vad()
        logger.info(f"  Mic: device {env['mic']}")
        logger.info(f"  VAD (Silero): {'✅' if vad_ok else '❌ failed'}")
        logger.info(f"  STT (Whisper): {'✅' if env['whisper'] else '❌'} @ {self.whisper.server_url}")
        logger.info(f"  TTS (ElevenLabs): {'✅' if env['tts'] else '❌'}")
        logger.info(f"  Runtime: {env['runtime']}")

        if not vad_ok:
            logger.error("VAD failed to load — voice daemon cannot run without VAD")
            logger.error("Make sure torch is installed: pip install torch")
            return

        # Connect to Runtime
        connected = await self.transport.connect()
        if not connected:
            logger.warning(f"Runtime at {self.transport.runtime_url} not available")
        else:
            self._setup_event_handlers()

        # Wire up audio pipeline
        self.vad_proc.on_speech_end(self._on_speech_end)

        # Start streaming mic
        if not self.mic.start(self._on_audio_chunk):
            logger.error("Failed to start microphone")
            return

        # Start running
        self._running = True
        self._loop = asyncio.get_running_loop()
        self.presence.transition(Presence.IDLE)

        logger.info(f"Listening for: {WAKE_WORDS}")
        print(f"  🔊 叫 '婉婉' 或 'Julia' 唤醒我", flush=True)

        try:
            await self._main_loop()
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def stop(self):
        logger.info("Shutting down...")
        self._running = False
        self.mic.stop()
        self.player.stop()
        await self.transport.disconnect()
        self.presence.transition(Presence.SLEEPING)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    daemon = JuliaVoiceDaemon()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _shutdown():
        loop.call_soon_threadsafe(lambda: loop.create_task(daemon.stop()))

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except NotImplementedError:
            signal.signal(sig, lambda s, f: _shutdown())

    try:
        loop.run_until_complete(daemon.start())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
    logger.info("Exited.")


if __name__ == "__main__":
    main()

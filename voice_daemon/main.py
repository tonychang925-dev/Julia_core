#!/usr/bin/env python3
"""Julia Voice Daemon v4.1.1 — Embodied Runtime Entry Point.

Architecture:
  Mac mic → VAD → Wake Word → STT (GPU Whisper) → WebSocket → Julia Runtime → TTS → Speaker

This daemon is a thin client. It converts audio ↔ events.
All intelligence lives in the Julia Runtime (:9000).

Usage:
  python -m voice_daemon.main
  # or
  python voice_daemon/main.py

Environment:
  WHISPER_SERVER_URL  — GPU Whisper server (default: http://localhost:8001)
  ELEVENLABS_API_KEY  — ElevenLabs API key for TTS
  JULIA_RUNTIME_URL   — Julia Runtime WebSocket (default: ws://localhost:9000/ws)
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
import time
import threading
from pathlib import Path

# Add julia_core to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from voice_daemon.audio.microphone import Microphone, get_default_mic_index
from voice_daemon.audio.stream import AudioRecorder
from voice_daemon.audio.player import AudioPlayer
from voice_daemon.vad.silero import SileroVAD, SpeechDetector
from voice_daemon.wakeword.detector import WakeWordDetector, WAKE_WORDS
from voice_daemon.stt.whisper_client import WhisperClient
from voice_daemon.tts.elevenlabs import ElevenLabsTTS
from voice_daemon.presence.manager import PresenceManager, Presence
from voice_daemon.transport.websocket import WebSocketTransport
from voice_daemon.transport.protocol import (
    PRESENCE_CHANGED, TTS_SPEAK, TTS_CANCEL, TTS_FINISHED, ASSISTANT_REPLY, ERROR,
    presence_changed_event, tts_finished_event, voice_wake_event,
)

logger = logging.getLogger("julia.voice")


class JuliaVoiceDaemon:
    """Main voice daemon — coordinates all audio I/O and Runtime communication."""

    def __init__(self, config: dict = None):
        self.config = config or {}

        # Audio
        self.mic_index = get_default_mic_index()
        self.sample_rate = 16000
        self.recorder = AudioRecorder(sample_rate=self.sample_rate, buffer_seconds=2.0)
        self.player = AudioPlayer()

        # VAD
        self.vad = SileroVAD(threshold=0.5, sample_rate=self.sample_rate,
                             min_speech_duration=0.3, silence_duration=1.5)
        self.speech_detector = SpeechDetector(self.vad)

        # STT (GPU Whisper)
        whisper_url = os.environ.get("WHISPER_SERVER_URL", "http://localhost:8001")
        self.whisper = WhisperClient(server_url=whisper_url)

        # Wake Word
        self.wake_detector = WakeWordDetector(whisper_client=self.whisper)

        # TTS
        self.tts = ElevenLabsTTS()

        # Transport
        runtime_url = os.environ.get("JULIA_RUNTIME_URL", "ws://localhost:9000/ws")
        self.transport = WebSocketTransport(runtime_url=runtime_url)

        # Presence
        self.presence = PresenceManager(initial=Presence.SLEEPING)
        self.presence.enable_journal()  # Log state transitions for diagnostics

        # State
        self._running = False
        self._loop: asyncio.AbstractEventLoop = None

    # ── Initialization ──────────────────────────────────────────────────────

    def check_environment(self) -> dict:
        """Check all subsystems and return status."""
        return {
            "microphone": self.mic_index,
            "vad": self.vad.is_available,
            "whisper": self.whisper.is_available(),
            "tts": self.tts.is_available,
            "runtime": self.transport.runtime_url,
        }

    # ── Event Handlers ─────────────────────────────────────────────────────

    def _setup_event_handlers(self):
        """Register handlers for events from Julia Runtime."""

        def on_tts_speak(event):
            """Runtime → Voice Daemon: speak this text."""
            text = event.data.get("text", "")
            emotion = event.data.get("emotion", "warm")
            if text:
                self.presence.transition(Presence.SPEAKING)
                # Speak in background, send tts.finished when done
                import threading
                def _speak_and_notify():
                    ok = self.tts.speak(text, emotion)
                    duration = 0.0  # approximate
                    if self.transport.connected:
                        # Fire-and-forget the tts.finished event
                        asyncio.run_coroutine_threadsafe(
                            self.transport.send(tts_finished_event(duration)),
                            self._loop,
                        )
                        # Transition back to idle
                        self.presence.transition(Presence.IDLE)
                threading.Thread(target=_speak_and_notify, daemon=True).start()

        def on_tts_cancel(event):
            """Runtime → Voice Daemon: stop current TTS immediately."""
            self.player.stop()
            self.presence.transition(Presence.IDLE)

        def on_presence_changed(event):
            """Runtime → Voice Daemon: Julia's state changed."""
            state = event.data.get("value", "idle")
            try:
                new_state = Presence(state)
                self.presence.force_transition(new_state)
            except ValueError:
                pass

        def on_error(event):
            logger.error(f"Runtime error: {event.data.get('detail', 'unknown')}")

        self.transport.on(TTS_SPEAK, on_tts_speak)
        self.transport.on(TTS_CANCEL, on_tts_cancel)
        self.transport.on(PRESENCE_CHANGED, on_presence_changed)
        self.transport.on(ERROR, on_error)

        # Also track presence transitions and broadcast them
        def on_presence_change(new_state, old_state):
            if new_state != old_state and self.transport.connected:
                event = presence_changed_event(new_state.value)
                asyncio.run_coroutine_threadsafe(
                    self.transport.send(event), self._loop
                )

        self.presence.on_change(on_presence_change)

    # ── Voice Pipeline ─────────────────────────────────────────────────────

    async def _process_speech(self, text: str):
        """Send speech final to Runtime, wait for TTS response."""
        if not text or not text.strip():
            return

        logger.info(f"Speech final: {text}")

        # Transition: listening → thinking (LLM processing)
        self.presence.transition(Presence.THINKING)

        # Send to Runtime
        await self.transport.send_speech_final(text)

        # Runtime will respond with TTS_SPEAK event → handled by on_tts_speak
        # After TTS completes, the TTS handler transitions to IDLE

    async def _voice_loop(self):
        """Main voice interaction loop. Runs after wake word detection."""
        logger.info("Voice loop started")

        # Fill audio buffer
        self.recorder.start(device_index=self.mic_index)

        # Setup speech detection
        current_segment = []

        def on_speech_start():
            nonlocal current_segment
            current_segment = []
            self.recorder.start_segment()
            self.presence.transition(Presence.LISTENING)
            self.transport.send_voice_state("listening")

        def on_speech_end():
            self.presence.transition(Presence.THINKING)
            self.transport.send_voice_state("processing")
            # Get the full segment
            segment = self.recorder.stop_segment()
            if len(segment) > self.sample_rate * 0.3 * 2:  # at least 0.3s of audio
                # Send to Whisper
                result = self.whisper.transcribe_bytes(segment, suffix=".raw")
                text = result.get("text", "").strip()
                if text:
                    asyncio.create_task(self._process_speech(text))
                else:
                    # No speech detected, go back to idle
                    self.presence.transition(Presence.IDLE)
            else:
                self.presence.transition(Presence.IDLE)

        self.speech_detector.on_speech_start(on_speech_start)
        self.speech_detector.on_speech_end(on_speech_end)

        # Main audio processing loop
        try:
            while self._running:
                chunk = self.recorder.read_chunk()
                if chunk:
                    self.speech_detector.process(chunk)
                await asyncio.sleep(0.01)  # ~100 checks/second
        finally:
            self.recorder.stop()

    async def _wake_listen_loop(self):
        """Outer loop: wait for wake word, then enter voice loop."""
        logger.info(f"Wake word listening: {WAKE_WORDS}")

        while self._running:
            self.presence.transition(Presence.IDLE)

            # Listen for wake word (blocking in thread to not block asyncio)
            result = await asyncio.to_thread(
                self.wake_detector.listen,
                audio_stream_func=None,
                timeout=30.0,
            )

            if result and self._running:
                word, transcript = result
                mode = "interrupt" if self.presence.state in (Presence.SPEAKING, Presence.THINKING) else "activate"
                logger.info(f"Wake word: '{word}' (mode={mode})")

                if mode == "interrupt":
                    self.player.stop()
                    await self.transport.send_cancel("wake_word_interrupt")

                await self.transport.send_wake(word, transcript, mode)
                await self._voice_loop()

                # After voice loop ends, go back to idle and wait for next wake

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def start(self):
        """Start the voice daemon."""
        logger.info("Julia Voice Daemon v4.1.1 starting...")

        # Check subsystems
        env = self.check_environment()
        logger.info(f"  Microphone: device {env['microphone']}")
        logger.info(f"  VAD (Silero): {'✅' if env['vad'] else '⚠️  not loaded'}")
        logger.info(f"  STT (Whisper): {'✅' if env['whisper'] else '❌ offline'} @ {self.whisper.server_url}")
        logger.info(f"  TTS (ElevenLabs): {'✅' if env['tts'] else '❌ no API key'}")
        logger.info(f"  Runtime: {env['runtime']}")

        # Connect to Runtime
        connected = await self.transport.connect()
        if not connected:
            logger.warning(f"Could not connect to Julia Runtime at {self.transport.runtime_url}")
            logger.warning("Voice daemon will continue without Runtime — audio will be buffered")
        else:
            self._setup_event_handlers()

        # Transition to idle
        self.presence.transition(Presence.IDLE)
        self._running = True

        # Start the wake word listening loop
        try:
            await self._wake_listen_loop()
        except asyncio.CancelledError:
            logger.info("Voice daemon stopped")
        finally:
            await self.stop()

    async def stop(self):
        """Gracefully shut down."""
        logger.info("Shutting down voice daemon...")
        self._running = False
        self.presence.transition(Presence.SLEEPING)
        self.recorder.stop()
        self.player.stop()
        await self.transport.disconnect()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    daemon = JuliaVoiceDaemon()

    # Handle graceful shutdown
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _signal_handler():
        logger.info("Received shutdown signal")
        loop.call_soon_threadsafe(lambda: loop.create_task(daemon.stop()))

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            signal.signal(sig, lambda s, f: _signal_handler())

    try:
        loop.run_until_complete(daemon.start())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

    logger.info("Julia Voice Daemon exited.")


if __name__ == "__main__":
    main()

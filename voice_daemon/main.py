#!/usr/bin/env python3
"""Julia Voice Daemon v4.3.1 — Proper Voice State Machine.

Architecture:
  Mac Mic → AudioBus → [MFCC Wake (always)] [Silero VAD (always)]
  VAD gated by state machine, not dynamic subscribe/unsubscribe.
  Wake detector paused during conversation.

States:
  SLEEPING → wake → WAITING_FOR_SPEECH → VAD triggers → RECORDING
  → silence → PROCESSING (STT+LLM+TTS) → IDLE → SLEEPING

Usage:
  /opt/miniconda3/envs/julia_voice/bin/python -m voice_daemon.main
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
import threading
import time
from enum import Enum
from pathlib import Path
from queue import Queue

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from voice_daemon.audio.audio_bus import AudioBus
from voice_daemon.audio.mac_speech import VADStreamProcessor
from voice_daemon.audio.player import AudioPlayer
from voice_daemon.audio.device import get_default_input_device
from voice_daemon.stt.whisper_client import WhisperClient
from voice_daemon.tts.elevenlabs import ElevenLabsTTS
from voice_daemon.wakeword.detector import WakeWordDetector, WAKE_WORDS
from voice_daemon.presence.manager import PresenceManager, Presence
from voice_daemon.transport.websocket import WebSocketTransport
from voice_daemon.transport.protocol import (
    PRESENCE_CHANGED, TTS_SPEAK, TTS_CANCEL, ASSISTANT_REPLY, ERROR,
    presence_changed_event, tts_finished_event,
)

logger = logging.getLogger("julia.voice")


# ── Voice State Machine ─────────────────────────────────────────────────────

class VoiceState(str, Enum):
    SLEEPING = "sleeping"
    WAITING_FOR_SPEECH = "waiting_for_speech"  # wake just happened, waiting for user to speak
    RECORDING = "recording"                    # user is speaking, VAD accumulating
    PROCESSING = "processing"                  # STT + LLM + TTS in progress
    IDLE = "idle"                              # ready for next wake


class JuliaVoiceDaemon:
    """Voice daemon with proper state machine. VAD permanently subscribed."""

    def __init__(self):
        # Audio
        dev = get_default_input_device()
        self.mic_index = dev['index'] if dev else None
        self.sample_rate = 16000

        # Single AudioBus (one InputStream forever)
        self.audio_bus = AudioBus(sample_rate=self.sample_rate, device_index=self.mic_index)

        # VAD — permanently subscribed to AudioBus, gated by state
        self.vad_proc = VADStreamProcessor(
            sample_rate=self.sample_rate,
            speech_threshold=0.3,
            silence_seconds=1.0,
            min_speech_seconds=0.3,
            max_speech_seconds=12.0,
        )

        # STT
        whisper_url = os.environ.get("WHISPER_SERVER_URL", "http://localhost:8001")
        self.whisper = WhisperClient(server_url=whisper_url)

        # TTS + Player
        self.tts = ElevenLabsTTS()
        self.player = AudioPlayer()

        # Transport
        runtime_url = os.environ.get("JULIA_RUNTIME_URL", "ws://localhost:9000/ws")
        self.transport = WebSocketTransport(runtime_url=runtime_url)

        # Wake Word (Fast Channel — subscribes to AudioBus at start)
        self.wake_detector = WakeWordDetector(sample_rate=self.sample_rate, audio_bus=self.audio_bus)

        # Presence (maps to Runtime protocol)
        self.presence = PresenceManager(initial=Presence.SLEEPING)
        self.presence.enable_journal()

        # State
        self._state = VoiceState.SLEEPING
        self._running = False
        self._wake_word = ""
        self._loop: asyncio.AbstractEventLoop = None
        self._segment_queue: Queue = Queue()
        self._state_lock = threading.Lock()

    # ── State Transitions ───────────────────────────────────────────────────

    def _transition(self, new_state: VoiceState):
        with self._state_lock:
            old = self._state
            self._state = new_state
        logger.debug(f"State: {old.value} → {new_state.value}")

    @property
    def state(self) -> VoiceState:
        return self._state

    # ── Init ────────────────────────────────────────────────────────────────

    def check_environment(self) -> dict:
        return {
            "mic": self.mic_index,
            "audio_bus": self.audio_bus.is_running,
            "whisper": self.whisper.is_available(),
            "tts": self.tts.is_available,
            "runtime": self.transport.runtime_url,
        }

    # ── Event Handlers ──────────────────────────────────────────────────────

    def _setup_event_handlers(self):
        def on_tts_speak(event):
            text = event.data.get("text", "")
            emotion = event.data.get("emotion", "warm")
            if text:
                self.presence.transition(Presence.SPEAKING)
                threading.Thread(target=lambda: (
                    self.tts.speak(text, emotion),
                    self._on_tts_done(),
                ), daemon=True).start()

        def on_tts_cancel(event):
            self.player.stop()
            self.presence.transition(Presence.IDLE)

        def on_error(event):
            logger.error(f"Runtime error: {event.data.get('detail', '')}")

        self.transport.on(TTS_SPEAK, on_tts_speak)
        self.transport.on(TTS_CANCEL, on_tts_cancel)
        self.transport.on(ERROR, on_error)

        def on_presence_change(new_state, old_state):
            if new_state != old_state and self.transport.connected:
                event = presence_changed_event(new_state.value)
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.transport.send(event), asyncio.get_running_loop()
                    )
                except RuntimeError:
                    pass
        self.presence.on_change(on_presence_change)

    def _on_tts_done(self):
        """TTS finished — conversation complete, go back to sleep."""
        self.presence.transition(Presence.IDLE)
        self._transition(VoiceState.SLEEPING)
        # Resume wake detector
        self.wake_detector.resume()
        if self.transport.connected:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.transport.send(tts_finished_event(0.0)), self._loop
                )
            except Exception:
                pass
        logger.info("Conversation complete — listening for wake")

    # ── VAD Callbacks (always subscribed, gated by state) ────────────────────

    def _on_speech_end(self, pcm_bytes: bytes):
        """VAD detected end of speech. Only process when RECORDING."""
        if self.state != VoiceState.RECORDING:
            return
        dur = len(pcm_bytes) / (self.sample_rate * 2)
        logger.info(f"Speech segment: {dur:.2f}s")
        self._segment_queue.put(pcm_bytes)

    # ── Wake Callback ───────────────────────────────────────────────────────

    def _on_wake_detected(self, wake_word: str):
        """Wake word detected. Transition to WAITING_FOR_SPEECH."""
        if self.state not in (VoiceState.SLEEPING, VoiceState.IDLE):
            return

        logger.info(f"Wake: '{wake_word}'")
        self._wake_word = wake_word
        self._transition(VoiceState.WAITING_FOR_SPEECH)

        # Pause wake detector during conversation
        self.wake_detector.pause()

        mode = "interrupt" if self.presence.state in (Presence.SPEAKING, Presence.THINKING) else "activate"
        print(f"  ✅ 唤醒! 说你想说的...", flush=True)

        # Notify Runtime
        if self.transport.connected and self._loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.transport.send_wake(wake_word, "", mode), self._loop
                )
            except Exception:
                pass

        self.presence.transition(Presence.LISTENING)

        # Timeout: if no speech within 5s, go back to sleep
        def _wait_timeout():
            time.sleep(5)
            if self.state == VoiceState.WAITING_FOR_SPEECH:
                logger.debug("No speech after wake → SLEEPING")
                self.vad_proc.reset()  # clear any partial VAD state
                self._transition(VoiceState.SLEEPING)
                self.wake_detector.resume()
                self.presence.transition(Presence.IDLE)
                print(f"  🔊 (超时) 叫 '婉婉' 或 'Julia' 唤醒我", flush=True)
        threading.Thread(target=_wait_timeout, daemon=True).start()

    # ── VAD State Gate ──────────────────────────────────────────────────────

    def _vad_state_gate(self, audio: np.ndarray):
        """VAD consumer callback. Always subscribed, always feeds VAD.

        VAD maintains its internal speech/silence state continuously.
        The gate controls what happens on VAD callbacks:
          SLEEPING/IDLE → VAD runs but output ignored (wake engine handles)
          WAITING_FOR_SPEECH → VAD speech_start → RECORDING
          RECORDING → VAD speech_end → queue segment
          PROCESSING → VAD runs but output ignored
        """
        state = self.state

        # Always feed VAD so it maintains accurate speech/silence tracking
        self.vad_proc.process_chunk(audio)

        if state == VoiceState.WAITING_FOR_SPEECH:
            # VAD detected speech start → transition to RECORDING
            if self.vad_proc.is_speaking:
                self._transition(VoiceState.RECORDING)
                logger.debug("VAD: speech started → RECORDING")

    # ── Main Loop ───────────────────────────────────────────────────────────

    async def _process_segment(self, pcm_bytes: bytes):
        """STT + LLM + TTS for a captured speech segment."""
        dur = len(pcm_bytes) / (self.sample_rate * 2)
        if dur < 0.3:
            return

        self._transition(VoiceState.PROCESSING)
        logger.info(f"Transcribing {dur:.2f}s...")

        result = self.whisper.transcribe_bytes(pcm_bytes, suffix=".raw")
        text = result.get("text", "").strip()
        if not text:
            logger.debug("STT: empty result")
            self._transition(VoiceState.SLEEPING)
            self.wake_detector.resume()
            print(f"  🔊 叫 '婉婉' 或 'Julia' 唤醒我", flush=True)
            return

        logger.info(f"🎤 {text}")
        await self._process_query(text)

    async def _process_query(self, text: str):
        """Send query to Runtime. TTS completion will resume wake detector."""
        self.presence.transition(Presence.THINKING)
        await self.transport.send_speech_final(text)
        print(f"  → Julia 思考中...", flush=True)

    async def _main_loop(self):
        """Drain segment queue."""
        while self._running:
            try:
                while not self._segment_queue.empty():
                    pcm = self._segment_queue.get_nowait()
                    await self._process_segment(pcm)
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"Main loop error: {e}")

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def start(self):
        logger.info("Julia Voice Daemon v4.3.1 (State Machine) starting...")

        env = self.check_environment()

        # 1. Start AudioBus (single mic stream)
        if not self.audio_bus.start():
            logger.error("AudioBus failed")
            return

        # 2. Load VAD (Silero preferred, energy fallback)
        vad_ok = self.vad_proc.load_vad()
        logger.info(f"  VAD (Silero): {'✅' if vad_ok else '⚠️  energy fallback'}")

        # 3. Start wake detector (Fast Channel, subscribes to AudioBus)
        self.wake_detector.on_wake(self._on_wake_detected)
        wake_ok = self.wake_detector.start()
        logger.info(f"  Wake: {'✅ MFCC+DTW' if wake_ok else '⚠️  Whisper fallback'}")

        # 4. Permanently subscribe VAD state gate to AudioBus
        #    VAD is always receiving audio, but only processes when RECORDING state
        self.vad_proc.on_speech_end(self._on_speech_end)
        self.audio_bus.subscribe(self._vad_state_gate)

        logger.info(f"  STT: {'✅' if env['whisper'] else '❌'} @ {self.whisper.server_url}")
        logger.info(f"  TTS: {'✅' if env['tts'] else '❌'}")
        logger.info(f"  Runtime: {env['runtime']}")

        # 5. Connect to Runtime
        connected = await self.transport.connect()
        if not connected:
            logger.warning(f"Runtime not available at {self.transport.runtime_url}")
        else:
            self._setup_event_handlers()

        # 6. Start main loop
        self._running = True
        self._loop = asyncio.get_running_loop()
        self._transition(VoiceState.SLEEPING)
        self.presence.transition(Presence.IDLE)

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
        self.wake_detector.stop()
        self.audio_bus.stop()
        self.player.stop()
        try:
            await asyncio.wait_for(self.transport.disconnect(), timeout=0.5)
        except (asyncio.TimeoutError, Exception):
            pass
        self.presence.transition(Presence.SLEEPING)


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("julia.audio").setLevel(logging.DEBUG)
    logging.getLogger("julia.voice").setLevel(logging.DEBUG)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

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

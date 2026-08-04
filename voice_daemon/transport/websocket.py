"""WebSocket transport — connects Voice Daemon to Julia Runtime Event Gateway.

This is the thin pipe between Julia's body (voice daemon) and brain (runtime).
All events flow through here using the Julia Event Protocol v1.0.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Callable, Optional

from voice_daemon.transport.protocol import (
    JuliaEvent, PROTOCOL_VERSION,
    voice_wake_event, voice_listening_event, voice_final_event,
    voice_state_event, voice_cancel_event,
    tts_speak_event, tts_cancel_event,
    runtime_started_event, runtime_stopped_event,
    heartbeat_event, heartbeat_ack_event, error_event,
    VOICE_WAKE, VOICE_LISTENING, VOICE_FINAL, VOICE_CANCEL, VOICE_STATE,
    ASSISTANT_REPLY, TTS_SPEAK, TTS_CANCEL,
    TOOL_STARTED, TOOL_COMPLETED, MEMORY_EVENT, PRESENCE_CHANGED,
    THINKING_STARTED, THINKING_COMPLETED,
    RUNTIME_STARTED, RUNTIME_STOPPED,
    HEARTBEAT, HEARTBEAT_ACK, ERROR,
)

logger = logging.getLogger(__name__)


class WebSocketTransport:
    """WebSocket client for Julia Event Gateway.

    Handles: connect, reconnect, heartbeat, send, receive, dispatch.
    """

    def __init__(self, runtime_url: str = "ws://localhost:9000/ws",
                 reconnect_interval: float = 3.0,
                 heartbeat_interval: float = 30.0,
                 max_reconnect_delay: float = 60.0):
        self.runtime_url = runtime_url
        self.reconnect_interval = reconnect_interval
        self.heartbeat_interval = heartbeat_interval
        self.max_reconnect_delay = max_reconnect_delay

        self._ws = None
        self._connected = False
        self._running = False
        self._handlers: dict[str, list[Callable[[JuliaEvent], None]]] = {}
        self._send_queue: asyncio.Queue = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    @property
    def connected(self) -> bool:
        return self._connected

    # ── Event Handlers ──────────────────────────────────────────────────────

    def on(self, event_type: str, handler: Callable[[JuliaEvent], None]):
        """Register a handler for a specific event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    def _dispatch(self, event: JuliaEvent):
        """Dispatch an incoming event to registered handlers."""
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(f"Handler error for {event.type}")

    # ── Connection ──────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        """Connect to Julia Runtime Event Gateway. Returns True on success."""
        try:
            import websockets
            self._ws = await websockets.connect(
                self.runtime_url,
                ping_interval=None,  # We handle heartbeats ourselves
                close_timeout=5,
                proxy=None,  # Explicitly disable SOCKS proxy detection
            )
            self._connected = True
            self._running = True
            self._send_queue = asyncio.Queue()

            # Start background tasks
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            asyncio.create_task(self._send_loop())

            logger.info(f"Connected to Julia Runtime at {self.runtime_url}")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to {self.runtime_url}: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Gracefully disconnect."""
        self._running = False
        self._connected = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def reconnect_loop(self):
        """Continuously try to reconnect with exponential backoff."""
        delay = self.reconnect_interval
        while not self._connected:
            logger.info(f"Reconnecting in {delay:.0f}s...")
            await asyncio.sleep(delay)
            if await self.connect():
                delay = self.reconnect_interval  # Reset on success
            else:
                delay = min(delay * 2, self.max_reconnect_delay)

    # ── Send ────────────────────────────────────────────────────────────────

    async def send(self, event: JuliaEvent):
        """Queue an event for sending. Non-blocking."""
        if self._send_queue is not None:
            await self._send_queue.put(event)

    async def _send_loop(self):
        """Background task: drain the send queue."""
        while self._running and self._ws:
            try:
                event = await asyncio.wait_for(self._send_queue.get(), timeout=1.0)
                raw = event.to_json()
                await self._ws.send(raw)
                self._send_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"Send error: {e}")
                    self._connected = False
                    break

    # ── Receive ─────────────────────────────────────────────────────────────

    async def listen(self):
        """Continuously receive events from Julia Runtime. Blocks until disconnected."""
        while self._running and self._ws:
            try:
                raw = await self._ws.recv()
                event = JuliaEvent.from_json(raw)
                self._dispatch(event)
            except Exception as e:
                if self._running:
                    logger.error(f"Receive error: {e}")
                    self._connected = False
                    break

    # ── Heartbeat ───────────────────────────────────────────────────────────

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to keep the connection alive."""
        while self._running and self._connected:
            await asyncio.sleep(self.heartbeat_interval)
            try:
                await self._ws.send(heartbeat_event().to_json())
            except Exception:
                self._connected = False
                break

    # ── Convenience send methods ─────────────────────────────────────────────

    async def send_wake(self, word: str, transcript: str = "", mode: str = "activate"):
        await self.send(voice_wake_event(word, transcript, mode=mode))

    async def send_listening(self):
        await self.send(voice_listening_event())

    async def send_speech_final(self, text: str, language: str = "zh", confidence: float = 0.9):
        await self.send(voice_final_event(text, language, confidence))

    async def send_cancel(self, reason: str = "user_interrupt"):
        await self.send(voice_cancel_event(reason))

    async def send_voice_state(self, state: str):
        await self.send(voice_state_event(state))


# ── Synchronous Wrapper ─────────────────────────────────────────────────────

class SyncWebSocketTransport:
    """Synchronous wrapper around WebSocketTransport for use in threaded code.

    Usage:
        transport = SyncWebSocketTransport("ws://localhost:9000/ws")
        transport.connect()
        transport.send_speech_final("你好 Julia")
    """

    def __init__(self, *args, **kwargs):
        self._transport = WebSocketTransport(*args, **kwargs)
        self._loop = None
        self._thread = None

    def connect(self) -> bool:
        """Connect synchronously. Blocks until connected or failed."""
        import threading
        result = [False]

        async def _connect():
            result[0] = await self._transport.connect()

        def _run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(_connect())
            self._loop.run_forever()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        time.sleep(0.5)  # Give it a moment to connect
        return result[0]

    def disconnect(self):
        """Disconnect synchronously."""
        if self._loop:
            asyncio.run_coroutine_threadsafe(self._transport.disconnect(), self._loop)
        if self._thread:
            self._thread.join(timeout=2)

    def send(self, event: JuliaEvent):
        """Send an event synchronously."""
        if self._loop:
            asyncio.run_coroutine_threadsafe(self._transport.send(event), self._loop)

    def send_speech_final(self, text: str, language: str = "zh", confidence: float = 0.9):
        self.send(voice_final_event(text, language, confidence))

    def send_voice_state(self, state: str):
        self.send(voice_state_event(state))

    def send_wake(self, word: str, transcript: str = "", mode: str = "activate"):
        self.send(voice_wake_event(word, transcript, mode=mode))

    def send_cancel(self, reason: str = "user_interrupt"):
        self.send(voice_cancel_event(reason))

    @property
    def connected(self) -> bool:
        return self._transport.connected

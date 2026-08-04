"""Julia Event Gateway v1.0 — WebSocket endpoint for Voice Daemon + Electron.

This is the RECEIVING side of the Julia Event Protocol.
Runs inside the Julia Runtime server (:9000).

Architecture:
  Voice Daemon → WebSocket → Event Gateway → LLM pipeline → Response events
  Electron     → WebSocket → Event Gateway → (listen only for dashboard)

The gateway translates:
  voice.final  →  user message → LLM chat → assistant.reply + tts.speak
  voice.wake   →  session activation, interrupt current TTS
  voice.cancel →  interrupt: stop TTS, clear pending output
  voice.state  →  relay to all clients

Freeze date: 2026-08-04
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from voice_daemon.transport.protocol import (
    JuliaEvent, PROTOCOL_VERSION,
    # Voice events
    VOICE_WAKE, VOICE_LISTENING, VOICE_FINAL, VOICE_CANCEL, VOICE_STATE,
    # Cognitive events
    THINKING_STARTED, THINKING_COMPLETED,
    # Response events
    ASSISTANT_REPLY, TTS_SPEAK, TTS_CANCEL, TTS_FINISHED,
    # Tool events
    TOOL_STARTED, TOOL_COMPLETED,
    # Memory
    MEMORY_EVENT,
    # Presence
    PRESENCE_CHANGED,
    # Transport
    HEARTBEAT, HEARTBEAT_ACK, ERROR,
    # Lifecycle
    RUNTIME_STARTED, RUNTIME_STOPPED,
    # Factory functions
    runtime_started_event, runtime_stopped_event,
    assistant_reply_event, tts_speak_event, tts_cancel_event,
    thinking_started_event, thinking_completed_event,
    tool_started_event, tool_completed_event,
    memory_event_event,
    presence_changed_event,
    heartbeat_ack_event, error_event,
)

logger = logging.getLogger("julia.gateway")


class EventGateway:
    """WebSocket server endpoint. Receives events from Voice Daemon, routes to LLM."""

    def __init__(self, llm_chat_fn=None, tts_send_fn=None):
        self.llm_chat = llm_chat_fn
        self.tts_send = tts_send_fn

        self._sessions: dict[str, dict] = {}
        self._clients: set = set()
        self._server = None
        self._currently_speaking = False  # For interrupt support

    async def start(self, host: str = "0.0.0.0", port: int = 9000):
        """Start standalone WebSocket server."""
        import websockets
        logger.info(f"Julia Event Gateway starting on ws://{host}:{port}")

        self._server = await websockets.serve(
            self.handle, host, port,
            ping_interval=30, ping_timeout=10,
        )

        # Broadcast runtime.started to all clients
        # (won't reach anyone yet, but it's here for when clients connect)

        logger.info(f"Julia Event Gateway v{PROTOCOL_VERSION} ready ({len(self._clients)} clients)")
        await self._server.wait_closed()

    async def stop(self, reason: str = "normal"):
        """Stop the gateway server."""
        await self.broadcast(runtime_stopped_event(reason))
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def handle(self, websocket, path: str = "/"):
        """Handle a new WebSocket connection."""
        client_id = f"client-{id(websocket)}"
        self._clients.add(websocket)
        logger.info(f"Client connected: {client_id} (total: {len(self._clients)})")

        # Send runtime.started so the new client knows current state
        await self._send(websocket, runtime_started_event("4.1.1"))

        try:
            async for raw in websocket:
                try:
                    event = JuliaEvent.from_json(raw)
                    await self._dispatch(event, websocket)
                except json.JSONDecodeError:
                    await self._send(websocket, error_event(
                        detail="Invalid JSON", code="PARSE_ERROR"
                    ))
        except Exception as e:
            logger.warning(f"Client {client_id} disconnected: {e}")
        finally:
            self._clients.discard(websocket)
            logger.info(f"Client disconnected: {client_id} (total: {len(self._clients)})")

    async def _dispatch(self, event: JuliaEvent, from_client):
        """Dispatch an incoming event based on its type."""
        t = event.type

        if t == HEARTBEAT:
            await self._send(from_client, heartbeat_ack_event())

        elif t == VOICE_WAKE:
            await self._handle_wake(event, from_client)

        elif t == VOICE_LISTENING:
            await self.broadcast(presence_changed_event("listening"), exclude=from_client)

        elif t == VOICE_FINAL:
            await self._handle_speech_final(event, from_client)

        elif t == VOICE_CANCEL:
            await self._handle_cancel(event, from_client)

        elif t == VOICE_STATE:
            await self.broadcast(presence_changed_event(
                event.data.get("value", "idle")
            ), exclude=from_client)

        elif t == TTS_FINISHED:
            self._currently_speaking = False
            await self.broadcast(presence_changed_event("idle"))

        else:
            logger.debug(f"Unhandled event: {t}")

    # ── Handlers ──────────────────────────────────────────────────────────────

    async def _handle_wake(self, event: JuliaEvent, client):
        """Wake word detected → activate session, interrupt if speaking."""
        word = event.data.get("word", "")
        transcript = event.data.get("transcript", "")
        logger.info(f"Wake: '{word}' (transcript: '{transcript}')")

        # If Julia is currently speaking, cancel TTS (interrupt)
        if self._currently_speaking:
            logger.info("Interrupt: cancelling current TTS for wake word")
            await self.broadcast(tts_cancel_event())
            self._currently_speaking = False

        await self.broadcast(presence_changed_event("listening"), exclude=client)

    async def _handle_cancel(self, event: JuliaEvent, client):
        """User interrupted → stop TTS, clear pending."""
        reason = event.data.get("reason", "user_interrupt")
        logger.info(f"Cancel: {reason}")

        self._currently_speaking = False
        await self.broadcast(tts_cancel_event())
        await self.broadcast(presence_changed_event("idle"))

    async def _handle_speech_final(self, event: JuliaEvent, client):
        """Voice final → LLM pipeline → response."""
        text = event.data.get("text", "").strip()
        session_id = event.data.get("session_id", "voice-default")
        confidence = event.data.get("confidence", 0.9)

        if not text:
            await self._send(client, error_event(detail="Empty transcript", code="EMPTY_SPEECH"))
            return

        logger.info(f"Speech: '{text}' (confidence: {confidence:.2f})")

        if session_id not in self._sessions:
            self._sessions[session_id] = {"history": [], "turn": 0}
        session = self._sessions[session_id]
        session["turn"] += 1

        # Broadcast cognitive events (all clients, including sender)
        t_start = time.time()
        await self.broadcast(thinking_started_event())
        await self.broadcast(presence_changed_event("thinking"))

        if self.llm_chat:
            try:
                reply = await self.llm_chat(text, session_id)

                # Extract emotion tag
                import re
                emotion = "warm"
                clean_reply = reply
                match = re.match(
                    r'^\[(warm|soft|sad|excited|thoughtful|whisper|cry|laugh|sigh)\]\s*',
                    reply
                )
                if match:
                    emotion = match.group(1)
                    clean_reply = reply[match.end():]

                duration_ms = (time.time() - t_start) * 1000

                # Send thinking.completed
                await self.broadcast(thinking_completed_event(duration_ms))

                # Send assistant.reply
                await self.broadcast(assistant_reply_event(
                    text=clean_reply, tool_calls=[], memory_used=[],
                ))

                # Send tts.speak → Voice Daemon renders audio
                self._currently_speaking = True
                await self.broadcast(tts_speak_event(text=clean_reply, emotion=emotion))
                await self.broadcast(presence_changed_event("speaking"))

                # Save history
                session["history"].append({"role": "user", "content": text})
                session["history"].append({"role": "assistant", "content": clean_reply})

            except Exception as e:
                logger.exception(f"LLM error: {e}")
                await self._send(client, error_event(
                    detail=f"LLM processing failed: {e}", code="LLM_ERROR"
                ))
                await self.broadcast(presence_changed_event("idle"))
        else:
            await self._send(client, assistant_reply_event(
                text=f"Received: {text}", tool_calls=[], memory_used=[],
            ))

        # Voice Daemon sends tts.finished → transitions presence to idle
        # No sleep hack. Event-driven lifecycle.

    # ── Send / Broadcast ──────────────────────────────────────────────────────

    async def _send(self, client, event: JuliaEvent):
        try:
            await client.send(event.to_json())
        except Exception:
            pass

    async def broadcast(self, event: JuliaEvent, exclude=None):
        """Send to all connected clients except exclude."""
        dead = set()
        for client in self._clients:
            if client == exclude:
                continue
            try:
                await client.send(event.to_json())
            except Exception:
                dead.add(client)
        for client in dead:
            self._clients.discard(client)

    # ── FastAPI Integration ───────────────────────────────────────────────────

    def make_fastapi_handler(self):
        async def handler(websocket):
            await websocket.accept()
            await self.handle(websocket)
        return handler


# ── Standalone LLM Chat Wrapper ───────────────────────────────────────────────

def create_chat_fn(provider_name: str = "deepseek"):
    import sys
    sys.path.insert(0, "/Users/admin/julia_ai_assistant")

    from concurrent.futures import ThreadPoolExecutor
    _executor = ThreadPoolExecutor(max_workers=4)

    from providers.llm.deepseek_provider import get_llm_provider
    from julia_core.narrative.bootstrap import get_bootstrap

    BOOTSTRAP = get_bootstrap()
    provider = get_llm_provider(provider_name)

    async def chat_fn(text: str, session_id: str = "") -> str:
        loop = asyncio.get_event_loop()

        def _call():
            messages = [
                {"role": "system", "content": "你是Julia。\n\n" + BOOTSTRAP},
                {"role": "user", "content": text},
            ]
            return provider.chat(messages, cognitive_mode="private_voice_continuity")

        return await loop.run_in_executor(_executor, _call)

    return chat_fn


# ── Standalone Server ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    chat_fn = create_chat_fn("deepseek")
    gateway = EventGateway(llm_chat_fn=chat_fn)

    from voice_daemon.transport.protocol import SUPPORTED_EVENTS
    print(f"Julia Event Gateway v{PROTOCOL_VERSION}")
    print(f"  Listening on ws://0.0.0.0:9000/ws")
    print(f"  Events: {len(SUPPORTED_EVENTS)} supported")
    print(f"  LLM: DeepSeek (via providers)")
    print()

    try:
        asyncio.run(gateway.start(host="0.0.0.0", port=9000))
    except KeyboardInterrupt:
        print("\nShutdown.")

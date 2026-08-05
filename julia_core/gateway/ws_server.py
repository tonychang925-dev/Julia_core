"""WebSocket Server — bidirectional Event Plane for the Gateway.

One WebSocket connection per client (Electron, Web, Mobile).
Clients send user.message. Gateway broadcasts runtime events.
"""

from __future__ import annotations
import json as _json
import logging
import time as _time

logger = logging.getLogger("julia.ws_server")


class WebSocketGateway:
    """Handles WebSocket connections. Thin — delegates to CommandRouter.

    Protocol:
      Client → Gateway: {"type":"user.message","content":"...","session_id":"..."}
      Gateway → Client: {"type":"runtime.event","category":"presence","event":"changed",...}
    """

    def __init__(self, command_router=None):
        from julia_core.runtime.julia_session import get_session
        self._js = get_session()
        self._router = command_router

    async def handle(self, ws, session_id: str = ""):
        """Main WebSocket loop. One client per connection."""
        from fastapi import WebSocket
        await ws.accept()

        # Send ready
        await ws.send_text(_json.dumps({
            "type": "runtime.event",
            "category": "runtime",
            "event": "gateway.ready",
            "data": {"version": "1.0"},
            "timestamp": _time.strftime("%H:%M:%S"),
        }))

        try:
            while True:
                data = await ws.receive_text()
                msg = _json.loads(data)
                msg_type = msg.get("type", "")

                if msg_type == "user.message":
                    text = msg.get("content", "")
                    sid = msg.get("session_id", session_id or "ws-default")

                    # Notify: thinking
                    await ws.send_text(_json.dumps({
                        "type": "runtime.event", "category": "presence",
                        "event": "changed", "data": {"state": "thinking"},
                        "session_id": sid, "timestamp": _time.strftime("%H:%M:%S"),
                    }))

                    # Route through JuliaSession
                    reply = self._js.chat(text)

                    # Assistant reply
                    await ws.send_text(_json.dumps({
                        "type": "runtime.event", "category": "conversation",
                        "event": "message.sent",
                        "data": {"reply": reply, "turn": self._js.turn_count,
                                 "topic": self._js.current_topic},
                        "session_id": sid, "timestamp": _time.strftime("%H:%M:%S"),
                    }))

                elif msg_type == "client.connected":
                    await ws.send_text(_json.dumps({
                        "type": "runtime.event", "category": "runtime",
                        "event": "client.ack",
                        "data": {"client_type": msg.get("client_type", "unknown"),
                                 "version": msg.get("version", "?")},
                        "timestamp": _time.strftime("%H:%M:%S"),
                    }))

        except Exception:
            pass  # Client disconnected

"""Julia Runtime Gateway — single entrypoint for all bodies.

HTTP Command API + WebSocket Event Stream.
Bodies (Electron, Voice, Web, Mobile) connect here.
They never import julia_core directly.

Usage:
  python -m julia_core.runtime.gateway --port 8100
"""

from __future__ import annotations

import asyncio
import json as _json
import logging
import sys
import time as _time
from pathlib import Path
from typing import Optional

# Ensure providers path is available
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, "/Users/admin/julia_ai_assistant")
sys.path.insert(0, "/Users/admin/julia_core")

logger = logging.getLogger("julia.gateway")


class GatewaySession:
    """One connected client session. Wraps JuliaSession for the Gateway."""

    def __init__(self):
        from julia_core.runtime.julia_session import JuliaSession
        self._js = JuliaSession()
        self.connected_at = _time.time()

    def chat(self, text: str) -> str:
        return self._js.chat(text)

    @property
    def turn_count(self) -> int:
        return self._js.turn_count


class RuntimeGateway:
    """Manages sessions and routes messages to JuliaSession."""

    def __init__(self):
        self.sessions: dict[str, GatewaySession] = {}

    def _ensure_session(self, session_id: str) -> GatewaySession:
        """Create new session if not exists. Gateway sessions are ephemeral — not canonical conversations."""
        if session_id not in self.sessions:
            self.sessions[session_id] = GatewaySession()
        return self.sessions[session_id]

    def handle_message(self, session_id: str, text: str) -> dict:
        """Process a user message through JuliaSession. Returns reply + metadata."""
        gs = self._ensure_session(session_id)
        reply = gs.chat(text)
        js = gs._js

        return {
            "reply": reply,
            "turn": js.turn_count,
            "session_id": session_id,
            "presence": js.relationship.session_mood,
            "relationship": js.relationship.recent_pattern,
            "topic": js.current_topic,
            "tool_evidence": [
                {"tool": e.tool, "status": e.status, "timestamp": e.timestamp}
                for e in js.capability.evidence.entries[-3:]
            ],
            "action_history": [
                {"name": a.name, "phase": a.phase.value, "result": a.result_summary}
                for a in js.action.history[-3:]
            ],
        }

    def health(self) -> dict:
        return {
            "status": "ok",
            "version": "gateway-v1",
            "active_sessions": len(self.sessions),
            "uptime": "ok",
        }


# ── FastAPI Server ──────────────────────────────────────────────────────────

def create_app() -> "FastAPI":
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="Julia Runtime Gateway", version="1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    gateway = RuntimeGateway()

    @app.get("/health")
    async def health():
        return gateway.health()

    @app.post("/chat")
    async def send_message(request: Request):
        """Command API: send a message, get Julia's reply."""
        body = await request.json()
        text = body.get("text", "")
        session_id = body.get("session_id", "default")
        result = gateway.handle_message(session_id, text)
        return result

    @app.websocket("/runtime/ws")
    async def websocket_endpoint(ws: WebSocket):
        """Event Stream: bidirectional real-time communication."""
        await ws.accept()
        session_id = f"ws-{id(ws)}"
        gs = None

        try:
            while True:
                data = await ws.receive_text()
                msg = _json.loads(data)
                msg_type = msg.get("type", "user.message")

                if msg_type == "user.message":
                    text = msg.get("content", "")
                    sid = msg.get("session_id", session_id)
                    gs = gateway._ensure_session(sid)

                    # Notify: Julia is thinking
                    await ws.send_text(_json.dumps({
                        "type": "presence.changed",
                        "state": "thinking",
                        "timestamp": _time.strftime("%H:%M:%S"),
                    }))

                    result = gateway.handle_message(sid, text)

                    # Send reply
                    await ws.send_text(_json.dumps({
                        "type": "assistant.completed",
                        "reply": result["reply"],
                        "turn": result["turn"],
                        "topic": result["topic"],
                        "relationship": result["relationship"],
                        "presence": result["presence"],
                        "timestamp": _time.strftime("%H:%M:%S"),
                    }))

                elif msg_type == "client.connected":
                    await ws.send_text(_json.dumps({
                        "type": "gateway.ready",
                        "version": "1.0",
                        "timestamp": _time.strftime("%H:%M:%S"),
                    }))

        except WebSocketDisconnect:
            pass

    return app


# ── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import uvicorn

    port = int(sys.argv[2]) if "--port" in sys.argv else 8100
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    logger.info(f"Julia Runtime Gateway starting on :{port}")
    logger.info("  Command API: http://localhost:{}/runtime/message".format(port))
    logger.info("  Event Stream: ws://localhost:{}/runtime/ws".format(port))

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

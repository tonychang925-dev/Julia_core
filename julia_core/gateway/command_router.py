"""Command Router — HTTP endpoints for the Gateway.

Routes runtime commands to JuliaSession. Handles session lifecycle.
"""

from __future__ import annotations
import logging

logger = logging.getLogger("julia.command_router")


class CommandRouter:
    """HTTP command delegation. Thin — no cognitive logic."""

    def __init__(self):
        from julia_core.runtime.julia_session import get_session
        self._get_session = get_session

    def handle_message(self, session_id: str, text: str) -> dict:
        """Route a user message to JuliaSession."""
        js = self._get_session()
        reply = js.chat(text)

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
        return {"status": "ok", "version": "gateway-v1", "protocol": "frozen"}

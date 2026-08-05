"""Julia Runtime Event Protocol v1.0 — FROZEN.

All events follow: {category}.{action}.{phase}
Client events go Client→Gateway. Core events go Gateway→Client.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import time as _time


class EventCategory(str, Enum):
    RUNTIME = "runtime"
    CLIENT = "client"
    PRESENCE = "presence"
    CONVERSATION = "conversation"
    COGNITION = "cognition"
    ACTION = "action"
    TOOL = "tool"
    MEMORY = "memory"
    TTS = "tts"
    ARTIFACT = "artifact"


class PresenceState(str, Enum):
    AWAKE = "awake"
    SLEEPING = "sleeping"
    IDLE = "idle"
    THINKING = "thinking"
    LISTENING = "listening"
    SPEAKING = "speaking"


@dataclass
class RuntimeEvent:
    """One event in the Julia Runtime Protocol."""
    category: str                    # "presence", "action", "tool", etc.
    event: str                       # "changed", "started", "completed"
    data: dict = field(default_factory=dict)
    session_id: str = ""
    timestamp: str = field(default_factory=lambda: _time.strftime("%H:%M:%S"))

    def to_dict(self) -> dict:
        return {
            "type": "runtime.event",
            "category": self.category,
            "event": self.event,
            "data": self.data,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
        }


# ── Event Constructors ───────────────────────────────────────────────────

def presence_changed(state: PresenceState, session_id: str = "") -> RuntimeEvent:
    return RuntimeEvent(category="presence", event="changed",
                        data={"state": state.value}, session_id=session_id)

def action_started(action: str, target: str = "", description: str = "", session_id: str = "") -> RuntimeEvent:
    return RuntimeEvent(category="action", event="started",
                        data={"action": action, "target": target, "description": description},
                        session_id=session_id)

def action_completed(action: str, result: str = "", session_id: str = "") -> RuntimeEvent:
    return RuntimeEvent(category="action", event="completed",
                        data={"action": action, "result_summary": result}, session_id=session_id)

def tool_call_completed(tool_name: str, status: str, evidence: dict = None, session_id: str = "") -> RuntimeEvent:
    return RuntimeEvent(category="tool", event="call.completed",
                        data={"tool_name": tool_name, "status": status, "evidence": evidence or {}},
                        session_id=session_id)

def assistant_reply(text: str, turn: int = 0, session_id: str = "") -> RuntimeEvent:
    return RuntimeEvent(category="conversation", event="message.sent",
                        data={"reply": text, "turn": turn}, session_id=session_id)

def artifact_created(artifact_type: str, artifact_id: str, metadata: dict = None, session_id: str = "") -> RuntimeEvent:
    return RuntimeEvent(category="artifact", event="created",
                        data={"artifact_type": artifact_type, "id": artifact_id, "metadata": metadata or {}},
                        session_id=session_id)

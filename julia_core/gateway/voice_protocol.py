"""Voice Capability Protocol v1.0 — E3.0 Frozen.

ADR-025: Voice Capability Architecture.

Namespace convention:
  client.voice.*  — Client body events (microphone, speaker)
  speech.*        — Core speech output events (TTS requests)
  runtime.*       — Julia's internal state (presence, assistant)

Core NEVER knows: microphone type, audio format, codec.
Client NEVER knows: identity, memory, relationship, wake state.
Voice Runtime transforms media into experience events.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import time as _time
from typing import Optional


# ── Client Voice Events (Client → Core) ───────────────────────────────────

CLIENT_VOICE_STARTED   = "client.voice.started"
CLIENT_VOICE_PARTIAL   = "client.voice.partial"
CLIENT_VOICE_FINAL     = "client.voice.final"
CLIENT_VOICE_CANCELLED = "client.voice.cancelled"

# ── Speech Events (Core → Voice Runtime → Client) ────────────────────────

SPEECH_REQUEST    = "speech.request"
SPEECH_STARTED    = "speech.started"
SPEECH_CHUNK      = "speech.chunk"
SPEECH_COMPLETED  = "speech.completed"
SPEECH_CANCELLED  = "speech.cancelled"

# ── Presence States (Core → Client) ──────────────────────────────────────

class Presence:
    OFFLINE     = "offline"
    AWAKE       = "awake"
    IDLE        = "idle"
    LISTENING   = "listening"
    RECALLING   = "recalling"
    REASONING   = "reasoning"
    GENERATING  = "generating"
    SPEAKING    = "speaking"
    INTERRUPTED = "interrupted"


# ── Event Constructors ───────────────────────────────────────────────────

def client_voice_started(session_id: str = "") -> dict:
    return {"type": "runtime.event", "category": "client.voice",
            "event": "started", "session_id": session_id,
            "timestamp": _time.strftime("%H:%M:%S")}

def client_voice_partial(text: str, session_id: str = "") -> dict:
    return {"type": "runtime.event", "category": "client.voice",
            "event": "partial", "session_id": session_id,
            "data": {"text": text}, "timestamp": _time.strftime("%H:%M:%S")}

def client_voice_final(text: str, session_id: str = "") -> dict:
    return {"type": "runtime.event", "category": "client.voice",
            "event": "final", "session_id": session_id,
            "data": {"text": text}, "timestamp": _time.strftime("%H:%M:%S")}

def presence_changed(state: str, previous: str = "", session_id: str = "") -> dict:
    return {"type": "runtime.event", "category": "presence",
            "event": "changed", "session_id": session_id,
            "data": {"state": state, "previous": previous},
            "timestamp": _time.strftime("%H:%M:%S")}

def speech_request(text: str, emotion: str = "warm", session_id: str = "") -> dict:
    return {"type": "runtime.event", "category": "speech",
            "event": "request", "session_id": session_id,
            "data": {"text": text, "style": {"emotion": emotion}},
            "timestamp": _time.strftime("%H:%M:%S")}

def assistant_chunk(text: str, turn: int = 0, session_id: str = "") -> dict:
    return {"type": "runtime.event", "category": "assistant",
            "event": "chunk", "session_id": session_id,
            "data": {"text": text, "turn": turn},
            "timestamp": _time.strftime("%H:%M:%S")}

def assistant_completed(text: str, turn: int = 0, topic: str = "", session_id: str = "") -> dict:
    return {"type": "runtime.event", "category": "assistant",
            "event": "completed", "session_id": session_id,
            "data": {"reply": text, "turn": turn, "topic": topic},
            "timestamp": _time.strftime("%H:%M:%S")}


# ── Event Trace ──────────────────────────────────────────────────────────

@dataclass
class EventTrace:
    session_id: str
    events: list[dict] = field(default_factory=list)

    def record(self, event_type: str, data: dict = None):
        self.events.append({"timestamp": _time.strftime("%H:%M:%S.%f")[:-3],
                            "event": event_type, "data": data or {}})

    def summary(self) -> str:
        return "\n".join(f"[{e['timestamp']}] {e['event']}" for e in self.events)


# ── VoiceSession Model ───────────────────────────────────────────────────

@dataclass
class VoiceSession:
    """One voice interaction session. Client body connects, Core processes."""
    id: str = ""
    client_type: str = "unknown"   # electron, mobile, robot
    transport: str = "ws"          # ws, webrtc (future)
    language: str = "zh-CN"
    state: str = "idle"
    created_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict:
        return {"id": self.id, "client_type": self.client_type,
                "transport": self.transport, "language": self.language,
                "state": self.state, "created_at": self.created_at}

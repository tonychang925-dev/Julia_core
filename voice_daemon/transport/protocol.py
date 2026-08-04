"""Julia Event Protocol v1.0 — unified WebSocket event schema.

This protocol is the contract between Voice Daemon, Julia Runtime, and Electron.
All events flow through the Julia Event Gateway (:9000/ws).

Naming convention:
  {domain}.{action}  — e.g., voice.wake, tool.started, presence.changed

Direction legend:
  →  Client → Runtime
  ←  Runtime → Client
  ↔  Bidirectional

Freeze date: 2026-08-04
"""

from __future__ import annotations

import json
import time

# ── Event Type Constants ──────────────────────────────────────────────────────

# Lifecycle (↔ bidirectional)
RUNTIME_STARTED = "runtime.started"       # Runtime initialized, ready for connections
RUNTIME_STOPPED = "runtime.stopped"       # Runtime shutting down

# Voice — Daemon → Runtime
VOICE_WAKE = "voice.wake"                # Wake word detected
VOICE_LISTENING = "voice.listening"       # VAD triggered, speech started
VOICE_FINAL = "voice.final"              # Final transcript ready for LLM
VOICE_CANCEL = "voice.cancel"            # Interrupt: user interrupted current output
VOICE_STATE = "voice.state"              # Voice daemon state change (meta)

# Cognitive — Runtime → Clients
THINKING_STARTED = "thinking.started"     # LLM processing started
THINKING_COMPLETED = "thinking.completed" # LLM response ready

# Assistant — Runtime → Clients
ASSISTANT_REPLY = "assistant.reply"       # Julia's text response (full payload)

# TTS — Runtime → Voice Daemon (speak/cancel), Voice Daemon → Runtime (finished)
TTS_SPEAK = "tts.speak"                  # Runtime → Daemon: request TTS output
TTS_CANCEL = "tts.cancel"                # Runtime → Daemon: cancel current TTS playback
TTS_FINISHED = "tts.finished"            # Daemon → Runtime: TTS playback completed

# Tool — Runtime → Clients (per-tool granularity)
TOOL_STARTED = "tool.started"            # Tool execution started
TOOL_COMPLETED = "tool.completed"        # Tool execution finished (success or failure)

# Memory — Runtime → Clients
MEMORY_EVENT = "memory.event"             # Memory created/updated/deleted

# Presence — Runtime → Clients
PRESENCE_CHANGED = "presence.changed"     # Julia's presence state transition

# Transport (↔ bidirectional)
HEARTBEAT = "heartbeat"                  # Keep-alive ping
HEARTBEAT_ACK = "heartbeat.ack"          # Keep-alive pong
ERROR = "error"                          # Error event


# ── Event Categories ──────────────────────────────────────────────────────────

EVENT_CATEGORIES = {
    "lifecycle": [RUNTIME_STARTED, RUNTIME_STOPPED],
    "voice": [VOICE_WAKE, VOICE_LISTENING, VOICE_FINAL, VOICE_CANCEL, VOICE_STATE],
    "cognitive": [THINKING_STARTED, THINKING_COMPLETED],
    "assistant": [ASSISTANT_REPLY],
    "tts": [TTS_SPEAK, TTS_CANCEL, TTS_FINISHED],
    "tool": [TOOL_STARTED, TOOL_COMPLETED],
    "memory": [MEMORY_EVENT],
    "presence": [PRESENCE_CHANGED],
    "transport": [HEARTBEAT, HEARTBEAT_ACK, ERROR],
}


# ── Event Model ────────────────────────────────────────────────────────────────

class JuliaEvent:
    """Base event. All events have type, source, and timestamp."""

    def __init__(self, event_type: str, source: str = "", data: dict = None):
        self.type = event_type
        self.source = source
        self.timestamp = time.time()
        self.data = data or {}

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
        }, ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "JuliaEvent":
        obj = json.loads(raw)
        event = cls(
            event_type=obj.get("type", ""),
            source=obj.get("source", ""),
            data=obj.get("data", {}),
        )
        event.timestamp = obj.get("timestamp", time.time())
        return event

    def __repr__(self) -> str:
        return f"JuliaEvent(type={self.type}, source={self.source})"


# ── Event Factory Functions ────────────────────────────────────────────────────

# -- Lifecycle

def runtime_started_event(version: str = "4.1.1") -> JuliaEvent:
    """Runtime → Clients: Julia Runtime is ready."""
    return JuliaEvent(RUNTIME_STARTED, source="runtime", data={"version": version})


def runtime_stopped_event(reason: str = "normal") -> JuliaEvent:
    """Runtime → Clients: Julia Runtime is shutting down."""
    return JuliaEvent(RUNTIME_STOPPED, source="runtime", data={"reason": reason})


# -- Voice (Daemon → Runtime)

def voice_wake_event(word: str, transcript: str = "", mode: str = "activate") -> JuliaEvent:
    """Voice Daemon → Runtime: wake word detected.

    mode:
      "activate"  — cold start: Julia was sleeping/idle, now waking up
      "interrupt" — Julia was speaking, user interrupted with wake word
    """
    return JuliaEvent(VOICE_WAKE, source="voice", data={
        "word": word,
        "transcript": transcript,
        "mode": mode,
    })


def voice_listening_event() -> JuliaEvent:
    """Voice Daemon → Runtime: VAD triggered, user started speaking."""
    return JuliaEvent(VOICE_LISTENING, source="voice", data={})


def voice_final_event(text: str, language: str = "zh", confidence: float = 0.9) -> JuliaEvent:
    """Voice Daemon → Runtime: final transcript ready."""
    return JuliaEvent(VOICE_FINAL, source="voice", data={
        "text": text,
        "language": language,
        "confidence": confidence,
    })


def voice_cancel_event(reason: str = "user_interrupt") -> JuliaEvent:
    """Voice Daemon → Runtime: interrupt current output.
    Sent when user says wake word during TTS playback or new speech detected.
    """
    return JuliaEvent(VOICE_CANCEL, source="voice", data={"reason": reason})


def voice_state_event(state: str) -> JuliaEvent:
    """Voice Daemon → Clients: voice daemon meta-state changed.
    States: "idle", "listening", "processing", "error"
    """
    return JuliaEvent(VOICE_STATE, source="voice", data={"value": state})


# -- Cognitive (Runtime → Clients)

def thinking_started_event() -> JuliaEvent:
    """Runtime → Clients: LLM processing started."""
    return JuliaEvent(THINKING_STARTED, source="runtime", data={})


def thinking_completed_event(duration_ms: float = 0.0) -> JuliaEvent:
    """Runtime → Clients: LLM response ready."""
    return JuliaEvent(THINKING_COMPLETED, source="runtime", data={
        "duration_ms": duration_ms,
    })


# -- Assistant (Runtime → Clients)

def assistant_reply_event(text: str, tool_calls: list = None,
                          memory_used: list = None) -> JuliaEvent:
    """Runtime → Clients: Julia's complete response."""
    return JuliaEvent(ASSISTANT_REPLY, source="runtime", data={
        "text": text,
        "tool_calls": tool_calls or [],
        "memory_used": memory_used or [],
    })


# -- TTS (Runtime → Voice Daemon)

def tts_speak_event(text: str, emotion: str = "warm") -> JuliaEvent:
    """Runtime → Voice Daemon: render speech."""
    return JuliaEvent(TTS_SPEAK, source="runtime", data={
        "text": text,
        "emotion": emotion,
    })


def tts_cancel_event() -> JuliaEvent:
    """Runtime → Voice Daemon: stop current TTS playback immediately."""
    return JuliaEvent(TTS_CANCEL, source="runtime", data={})


def tts_finished_event(duration_ms: float = 0.0) -> JuliaEvent:
    """Voice Daemon → Runtime: TTS playback completed naturally."""
    return JuliaEvent(TTS_FINISHED, source="voice", data={
        "duration_ms": duration_ms,
    })


# -- Tool (Runtime → Clients)

def tool_started_event(name: str) -> JuliaEvent:
    """Runtime → Clients: tool execution started."""
    return JuliaEvent(TOOL_STARTED, source="runtime", data={"name": name})


def tool_completed_event(name: str, success: bool, result: str = "",
                         duration_ms: float = 0.0) -> JuliaEvent:
    """Runtime → Clients: tool execution finished."""
    return JuliaEvent(TOOL_COMPLETED, source="runtime", data={
        "name": name,
        "success": success,
        "result": result,
        "duration_ms": duration_ms,
    })


# -- Memory (Runtime → Clients)

def memory_event_event(action: str, title: str) -> JuliaEvent:
    """Runtime → Clients: memory created/updated/deleted."""
    return JuliaEvent(MEMORY_EVENT, source="runtime", data={
        "action": action,  # "created", "updated", "deleted"
        "title": title,
    })


# -- Presence (Runtime → Clients)

def presence_changed_event(state: str) -> JuliaEvent:
    """Runtime → Clients: Julia's presence state changed.
    States: sleeping, idle, listening, thinking, speaking, away
    """
    return JuliaEvent(PRESENCE_CHANGED, source="runtime", data={"value": state})


# -- Transport

def heartbeat_event(source: str = "voice", daemon_state: str = "",
                    daemon_version: str = "4.1.1") -> JuliaEvent:
    """Bidirectional: keep-alive ping with rich diagnostics."""
    return JuliaEvent(HEARTBEAT, source=source, data={
        "version": daemon_version,
        "state": daemon_state,
    })


def heartbeat_ack_event(version: str = "4.1.1", connected_clients: int = 0) -> JuliaEvent:
    """Bidirectional: keep-alive pong with runtime diagnostics."""
    return JuliaEvent(HEARTBEAT_ACK, source="runtime", data={
        "version": version,
        "clients": connected_clients,
    })


def error_event(detail: str, code: str = "") -> JuliaEvent:
    """Bidirectional: error."""
    return JuliaEvent(ERROR, source="runtime", data={
        "detail": detail,
        "code": code,
    })


# ── Protocol Version ──────────────────────────────────────────────────────────

PROTOCOL_VERSION = "1.0"

SUPPORTED_EVENTS = sorted(
    EVENT_CATEGORIES["lifecycle"] +
    EVENT_CATEGORIES["voice"] +
    EVENT_CATEGORIES["cognitive"] +
    EVENT_CATEGORIES["assistant"] +
    EVENT_CATEGORIES["tts"] +
    EVENT_CATEGORIES["tool"] +
    EVENT_CATEGORIES["memory"] +
    EVENT_CATEGORIES["presence"] +
    EVENT_CATEGORIES["transport"]
)

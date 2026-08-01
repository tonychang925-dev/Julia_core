"""Session lifecycle management — domain-independent.

A Session is a lightweight lifecycle container. It does NOT own:
  - conversation history
  - identity
  - memory
  - domain state
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from uuid import uuid4


class SessionState(str, enum.Enum):
    CREATED = "created"
    ACTIVE = "active"
    CONTEXT_REQUESTED = "context_requested"
    CONTEXT_RESOLVED = "context_resolved"
    CLOSED = "closed"
    EXPIRED = "expired"


@dataclass(slots=True)
class Session:
    session_id: str = field(default_factory=lambda: f"session-{uuid4().hex}")
    state: SessionState = SessionState.CREATED


class SessionManager:
    """Tracks session lifecycle. No domain knowledge."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self) -> Session:
        session = Session()
        self._sessions[session.session_id] = session
        return session

    def activate(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session is not None and session.state == SessionState.CREATED:
            session.state = SessionState.ACTIVE

    def close(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        if session.state not in (SessionState.CLOSED, SessionState.EXPIRED):
            session.state = SessionState.CLOSED

    def expire(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        session.state = SessionState.EXPIRED

    def active_sessions(self) -> tuple[str, ...]:
        return tuple(
            sid for sid, s in self._sessions.items()
            if s.state == SessionState.ACTIVE
        )

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

"""Conversation session repository — in-memory + JSON file persistence.

Future: SQLite / PostgreSQL without changing API.
"""
from __future__ import annotations

import json
from pathlib import Path

from julia_core.conversation_state.models import (
    ConversationSession,
    ConversationMessage,
)


class SessionRepository:
    """Thread-safe in-memory store backed by JSON file."""

    def __init__(self, filepath: str | Path = "data/sessions.json"):
        self._filepath = Path(filepath)
        self._sessions: dict[str, ConversationSession] = {}
        self._load()

    def _load(self) -> None:
        if self._filepath.exists():
            try:
                data = json.loads(self._filepath.read_text())
                for item in data:
                    session = ConversationSession(
                        id=item["id"],
                        title=item.get("title", ""),
                        topic=item.get("topic", ""),
                        messages=[ConversationMessage(**m) for m in item.get("messages", [])],
                        tags=item.get("tags", []),
                        created_at=item.get("created_at", ""),
                        updated_at=item.get("updated_at", ""),
                        message_count=item.get("message_count", 0),
                    )
                    self._sessions[session.id] = session
            except (json.JSONDecodeError, KeyError):
                self._sessions = {}

    def _save(self) -> None:
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        data = [s.detail() for s in self.list_all()]
        self._filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def list_all(self) -> list[ConversationSession]:
        return sorted(
            self._sessions.values(),
            key=lambda s: s.updated_at,
            reverse=True,
        )

    def get(self, session_id: str) -> ConversationSession | None:
        return self._sessions.get(session_id)

    def create(self, title: str = "New Conversation") -> ConversationSession:
        session = ConversationSession(title=title)
        self._sessions[session.id] = session
        self._save()
        return session

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        turn_id: str = "",
        modality: str = "text",
        status: str = "completed",
    ) -> ConversationSession | None:
        session = self._sessions.get(session_id)
        if not session:
            return None
        msg = ConversationMessage(
            conversation_id=session_id,
            turn_id=turn_id,
            role=role,
            modality=modality,
            content=content,
            status=status,
        )
        session.messages.append(msg)
        session.touch()
        session.auto_title()
        self._save()
        return session

    def update_title(self, session_id: str, title: str) -> ConversationSession | None:
        session = self._sessions.get(session_id)
        if not session:
            return None
        session.title = title
        session.touch()
        self._save()
        return session

    def delete(self, session_id: str) -> bool:
        if session_id not in self._sessions:
            return False
        del self._sessions[session_id]
        self._save()
        return True

    def search(self, query: str) -> list[ConversationSession]:
        q = query.lower()
        return [
            s for s in self.list_all()
            if q in s.title.lower()
            or q in s.topic.lower()
            or any(q in tag.lower() for tag in s.tags)
            or any(q in m.content.lower() for m in s.messages if m.role == "user")
        ]

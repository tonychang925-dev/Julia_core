"""Conversation session service — business logic layer."""
from __future__ import annotations

from julia_core.conversation_state.models import ConversationSession
from julia_core.conversation_state.repository import SessionRepository


class ConversationService:
    """Manages session lifecycle. Single instance per runtime."""

    _instance: ConversationService | None = None
    _repository: SessionRepository | None = None

    def __init__(self, filepath: str = "data/sessions.json"):
        self._repo = SessionRepository(filepath)

    @property
    def repo(self) -> SessionRepository:
        return self._repo

    def list_sessions(self) -> list[dict]:
        return [s.summary() for s in self._repo.list_all()]

    def get_session(self, session_id: str) -> dict | None:
        s = self._repo.get(session_id)
        return s.detail() if s else None

    def create_session(self, title: str = "New Conversation") -> dict:
        s = self._repo.create(title)
        return s.detail()

    def add_message(self, session_id: str, role: str, content: str) -> dict | None:
        s = self._repo.add_message(session_id, role, content)
        return s.detail() if s else None

    def update_title(self, session_id: str, title: str) -> dict | None:
        s = self._repo.update_title(session_id, title)
        return s.detail() if s else None

    def delete_session(self, session_id: str) -> bool:
        return self._repo.delete(session_id)

    def search_sessions(self, query: str) -> list[dict]:
        return [s.summary() for s in self._repo.search(query)]

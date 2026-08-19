"""LegacyJsonConversationRepository — RT2-R0 adapter.

Wraps existing SessionRepository behind ConversationRepository protocol.
Zero semantic changes. Full behavior parity.

This adapter delegates all calls to the existing SessionRepository.
When Storage v2 replaces it, ConversationRuntime need not change.
"""

from __future__ import annotations

from pathlib import Path

from julia_core.conversation_state.models import ConversationSession, ConversationMessage
from julia_core.conversation_state.repository import (
    SessionRepository,
    ConversationNotFoundError,
    TurnConflictError,
    ConversationAdvancedError,
    InvalidTurnStateError,
)


class LegacyJsonConversationRepository:
    """ConversationRepository adapter wrapping existing SessionRepository.

    Delegates to SessionRepository for all operations. Exposes the
    ConversationRepository protocol surface with zero semantic changes.
    """

    def __init__(self, filepath: str | Path = "data/conversations.json"):
        self._repo = SessionRepository(filepath)

    def set_read_only(self) -> None:
        """RETIRE: mark the underlying legacy store read-only (physical)."""
        self._repo.set_read_only()

    # ── Conversation Lifecycle ──────────────────────────────────────────

    def get(self, session_id: str) -> ConversationSession | None:
        return self._repo.get(session_id)

    def list_all(self) -> list[ConversationSession]:
        return self._repo.list_all()

    def create_with_id(self, session_id: str, title: str = "New Conversation") -> ConversationSession:
        return self._repo.create_with_id(session_id, title)

    def delete(self, session_id: str) -> bool:
        return self._repo.delete(session_id)

    def update_title(self, session_id: str, title: str) -> ConversationSession | None:
        return self._repo.update_title(session_id, title)

    def search(self, query: str) -> list[ConversationSession]:
        return self._repo.search(query)

    # ── Canonical Messages ─────────────────────────────────────────────

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
        return self._repo.add_message(
            session_id, role, content,
            turn_id=turn_id, modality=modality, status=status,
        )

    def update_message_status(self, message_id: str, status: str) -> bool:
        return self._repo.update_message_status(message_id, status)

    # ── Turn Lookup ────────────────────────────────────────────────────

    def find_turn(self, session_id: str, turn_id: str) -> list[ConversationMessage]:
        return self._repo.find_turn(session_id, turn_id)

    def get_messages(
        self,
        session_id: str,
        *,
        before: str | None = None,
        after: str | None = None,
        limit: int | None = None,
    ) -> list[ConversationMessage]:
        """Return messages for a conversation.

        limit = storage/query pagination only.
        Not cognitive context selection policy.
        """
        session = self._repo.get(session_id)
        if session is None:
            return []
        messages = list(session.messages)
        if limit is not None:
            messages = messages[-limit:]
        return messages

    # ── Batch Operations ───────────────────────────────────────────────

    def append_external_turns_atomic(
        self,
        session_id: str,
        turns: list[dict],
        base_last_message_id: str = "",
    ) -> tuple[list[str], list[str], str | None]:
        return self._repo.append_external_turns_atomic(
            session_id, turns, base_last_message_id,
        )

    def import_messages_atomic(
        self,
        session_id: str,
        messages: list[dict],
    ) -> tuple[int, int, str | None]:
        return self._repo.import_messages_atomic(session_id, messages)

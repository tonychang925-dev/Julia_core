"""ConversationRepository Protocol — RT2-R0.

ConversationRuntime depends ONLY on this contract. It MUST NOT know:
  - data/conversations.json
  - SessionRepository concrete class
  - JSON serialization / os.replace / fsync
  - Specific file paths

Backend implementations:
  - LegacyJsonConversationRepository (current production)
  - InMemoryConversationRepository (tests)
  - StorageV2ConversationRepository (future, RT2-R2)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from julia_core.conversation_state.models import ConversationSession, ConversationMessage


@runtime_checkable
class ConversationRepository(Protocol):
    """Stable contract between ConversationRuntime and storage backend.

    Pagination parameters (limit, before, after) are STORAGE/QUERY
    concerns. They do NOT define cognitive context selection policy.
    Context OS alone determines what the model sees.
    """

    # ── Conversation Lifecycle ──────────────────────────────────────────

    def get(self, session_id: str) -> ConversationSession | None:
        """Return a conversation by ID, or None."""
        ...

    def list_all(self) -> list[ConversationSession]:
        """Return all conversations, sorted by most recent first."""
        ...

    def create_with_id(self, session_id: str, title: str = "New Conversation") -> ConversationSession:
        """Create a conversation with a pre-determined ID. Idempotent."""
        ...

    def delete(self, session_id: str) -> bool:
        """Delete a conversation. Returns True if deleted."""
        ...

    def update_title(self, session_id: str, title: str) -> ConversationSession | None:
        """Update conversation title. Returns updated session or None."""
        ...

    def search(self, query: str) -> list[ConversationSession]:
        """Search conversations by title, topic, or user message content."""
        ...

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
        """Append a canonical message. Durability depends on backend."""
        ...

    def update_message_status(self, message_id: str, status: str) -> bool:
        """Update a message's status. Returns True if found."""
        ...

    # ── Turn Lookup ────────────────────────────────────────────────────

    def find_turn(self, session_id: str, turn_id: str) -> list[ConversationMessage]:
        """Find all messages for a given turn_id.

        Returns [user_msg, assistant_msg] if both exist, [user_msg] if
        only user, or [] if turn not found.
        """
        ...

    def get_messages(
        self,
        session_id: str,
        *,
        before: str | None = None,
        after: str | None = None,
        limit: int | None = None,
    ) -> list[ConversationMessage]:
        """Return messages for a conversation, optionally paginated.

        limit = storage/query pagination only.
        NOT cognitive context selection policy.
        """
        ...

    # ── Batch Operations ───────────────────────────────────────────────

    def append_external_turns_atomic(
        self,
        session_id: str,
        turns: list[dict],
        base_last_message_id: str = "",
    ) -> tuple[list[str], list[str], str | None]:
        """Atomically append external (voice) turns.

        Returns: (appended_turn_ids, skipped_turn_ids, last_message_id).
        """
        ...

    def import_messages_atomic(
        self,
        session_id: str,
        messages: list[dict],
    ) -> tuple[int, int, str | None]:
        """Atomically merge historical messages into canonical conversation.

        Returns: (imported_count, skipped_count, last_message_id).
        """
        ...

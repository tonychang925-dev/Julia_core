"""ConversationRuntime — authoritative logical conversation owner.

CORE-C1: This is the single source of truth for conversation state, history,
and turn ordering. Clients carry conversation_id; Runtime owns everything else.

Design:
  ConversationRuntime wraps conversation_state (canonical persistence).
  JuliaSession is the cognitive executor — no longer owns self.history.
  SessionStore legacy data is read-compatible via migration.

Contract (CORE-C1.0):
  - Clients submit: conversation_id + turn_id + modality + input
  - Clients do NOT submit: history, context window, prompt, assembled context
  - conv-A isolation from conv-B
  - Restart recovery
  - Turn idempotency
"""

from __future__ import annotations

import json as _json
import logging
import time as _time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from julia_core.conversation_state.models import ConversationMessage, ConversationSession
from julia_core.conversation_state.repository import SessionRepository
from julia_core.conversation_state.service import ConversationService

logger = logging.getLogger("julia.conversation_runtime")


# ── Turn Result ───────────────────────────────────────────────────────────────

@dataclass
class TurnResult:
    conversation_id: str = ""
    turn_id: str = ""
    user_message_id: str = ""
    assistant_message_id: str = ""
    assistant_content: str = ""
    status: str = ""  # completed | interrupted | failed
    created_at: str = ""
    completed_at: str = ""


# ── Conversation Handle ───────────────────────────────────────────────────────

@dataclass
class ConversationHandle:
    conversation_id: str = ""
    state: str = ""  # draft | active | consolidated | archived
    created_at: str = ""
    updated_at: str = ""
    last_turn_id: str = ""
    message_count: int = 0


# ── Runtime ──────────────────────────────────────────────────────────────────

class ConversationRuntime:
    """Authoritative conversation owner. Single instance per process.

    Usage:
        rt = ConversationRuntime()
        handle = rt.get_or_create("conv-A")

        result = rt.process_turn(
            conversation_id="conv-A",
            turn_id="turn-001",
            modality="text",
            input="我们之前聊到哪里了？",
            cognitive_fn=julia_session.process,
        )
    """

    def __init__(self, storage_path: str | Path = "data/conversations.json"):
        self._service = ConversationService(filepath=str(storage_path))
        self._active_turns: dict[str, str] = {}  # conv_id → turn_id (single-flight)
        self._turn_cache: dict[str, TurnResult] = {}  # turn_id → result (idempotency)

    # ── Public API ───────────────────────────────────────────────────────

    def get_or_create(self, conversation_id: str) -> ConversationHandle:
        """Get existing conversation or create new one. Idempotent."""
        session = self._service.repo.get(conversation_id)
        if session is None:
            session = self._create_conversation(conversation_id)
        return self._to_handle(session)

    def get_history(
        self,
        conversation_id: str,
        max_messages: int = 40,
    ) -> list[dict[str, str]]:
        """Return recent conversation history as role/content dicts for LLM context.

        These are plain dicts (not ConversationMessage) because the LLM provider
        expects {"role": "...", "content": "..."} format.
        """
        session = self._service.repo.get(conversation_id)
        if session is None:
            return []

        messages = session.messages[-max_messages:]
        return [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant") and m.status == "completed"
        ]

    def process_turn(
        self,
        *,
        conversation_id: str,
        turn_id: str,
        modality: str,
        input: str,
        cognitive_fn: Callable[[str, list[dict]], str],
    ) -> TurnResult:
        """Execute one cognitive turn with full state management.

        Pipeline:
          1. Single-flight guard (one turn per conversation at a time)
          2. Idempotency check (same turn_id → cached result)
          3. Load conversation state
          4. Get conversation history
          5. Persist user message
          6. Call cognitive_fn(input, history) → assistant reply
          7. Persist assistant message
          8. Return TurnResult

        Args:
            conversation_id: Which conversation this turn belongs to.
            turn_id: Unique turn identifier for idempotency.
            modality: "text" or "voice".
            input: The user's current message text.
            cognitive_fn: Callable(input_text, history) → assistant_response.
                          This is JuliaSession's cognitive pipeline.

        Returns:
            TurnResult with conversation_id, turn_id, message IDs, content, status.
        """
        now = _time.strftime("%Y-%m-%dT%H:%M:%S")

        # 1. Single-flight: one active turn per conversation
        active_turn = self._active_turns.get(conversation_id)
        if active_turn and active_turn != turn_id:
            raise ConversationBusyError(conversation_id, active_turn)

        # 2. Idempotency: same turn_id → cached
        if turn_id and turn_id in self._turn_cache:
            cached = self._turn_cache[turn_id]
            if cached.status == "completed":
                return cached

        self._active_turns[conversation_id] = turn_id

        try:
            # 3. Load/ensure conversation
            session = self._service.repo.get(conversation_id)
            if session is None:
                session = self._create_conversation(conversation_id)

            # 4. Get history for LLM context
            history = self.get_history(conversation_id)

            # 5. Persist user message
            user_msg = self._service.repo.add_message(
                conversation_id,
                role="user",
                content=input,
                turn_id=turn_id,
                modality=modality,
                status="completed",
            )
            user_msg_id = user_msg.messages[-1].message_id if user_msg else ""

            # 6. Cognitive execution
            try:
                assistant_content = cognitive_fn(input, history)
                assistant_status = "completed"
            except Exception as exc:
                logger.error(f"Cognitive pipeline failed for {conversation_id}/{turn_id}: {exc}")
                assistant_content = f"[系统提示] 处理你的消息时出现了问题。请再试一次。"
                assistant_status = "failed"

            # 7. Persist assistant message
            assistant_msg = self._service.repo.add_message(
                conversation_id,
                role="assistant",
                content=assistant_content,
                turn_id=turn_id,
                modality=modality,
                status=assistant_status,
            )
            assistant_msg_id = assistant_msg.messages[-1].message_id if assistant_msg else ""

            result = TurnResult(
                conversation_id=conversation_id,
                turn_id=turn_id,
                user_message_id=user_msg_id,
                assistant_message_id=assistant_msg_id,
                assistant_content=assistant_content,
                status=assistant_status,
                created_at=now,
                completed_at=_time.strftime("%Y-%m-%dT%H:%M:%S"),
            )

            # Cache for idempotency
            if turn_id:
                self._turn_cache[turn_id] = result

            return result

        finally:
            self._active_turns.pop(conversation_id, None)

    def restore(self, conversation_id: str) -> ConversationHandle | None:
        """Restore conversation state after restart. Returns None if not found."""
        session = self._service.repo.get(conversation_id)
        if session is None:
            return None
        return self._to_handle(session)

    def close(self, conversation_id: str) -> None:
        """Close conversation (no more turns). State is preserved for restore."""
        # Conversation is always persisted; close just means no active processing
        self._active_turns.pop(conversation_id, None)

    def list_conversations(self) -> list[ConversationHandle]:
        """List all conversations, newest first."""
        sessions = self._service.repo.list_all()
        return [self._to_handle(s) for s in sessions]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and its history."""
        return self._service.repo.delete(conversation_id)

    # ── Legacy Migration ──────────────────────────────────────────────────

    def migrate_legacy_sessions(self, legacy_path: str | Path = "/Users/admin/.julia/sessions.json") -> int:
        """Read legacy SessionStore JSON and migrate into conversation_state.

        Read-compatible. Preserves IDs, ordering, roles. Non-destructive.
        Returns count of migrated conversations.
        """
        legacy = Path(legacy_path)
        if not legacy.exists():
            return 0

        try:
            data = _json.loads(legacy.read_text())
            sessions = data.get("sessions", {})
        except (_json.JSONDecodeError, KeyError):
            return 0

        migrated = 0
        for sid, meta in sessions.items():
            if self._service.repo.get(sid) is not None:
                continue  # Already exists

            session = self._create_conversation(sid)

            msgs = meta.get("messages", [])
            for m in msgs:
                role = m.get("role", "")
                content = m.get("content", "")
                if role in ("user", "assistant") and content.strip():
                    self._service.repo.add_message(
                        sid,
                        role=role,
                        content=content,
                        modality="text",  # Legacy: all text
                        status="completed",
                    )

            if meta.get("title"):
                self._service.repo.update_title(sid, str(meta["title"]))

            migrated += 1

        if migrated > 0:
            logger.info(f"Migrated {migrated} legacy sessions from {legacy}")

        return migrated

    # ── Internal ──────────────────────────────────────────────────────────

    def _create_conversation(self, conversation_id: str) -> ConversationSession:
        """Create a conversation with a specific ID."""
        session = ConversationSession(
            id=conversation_id,
            title="New Conversation",
        )
        self._service.repo._sessions[conversation_id] = session
        self._service.repo._save()
        return session

    def _to_handle(self, session: ConversationSession) -> ConversationHandle:
        return ConversationHandle(
            conversation_id=session.id,
            state="active",
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_turn_id=session.messages[-1].turn_id if session.messages else "",
            message_count=session.message_count,
        )


# ── Error ─────────────────────────────────────────────────────────────────────

class ConversationBusyError(Exception):
    """Raised when a second turn is submitted while one is still active."""
    def __init__(self, conversation_id: str, active_turn_id: str):
        self.conversation_id = conversation_id
        self.active_turn_id = active_turn_id
        super().__init__(
            f"Conversation {conversation_id} is busy with turn {active_turn_id}"
        )


# ── Singleton ─────────────────────────────────────────────────────────────────

_runtime: ConversationRuntime | None = None


def get_conversation_runtime() -> ConversationRuntime:
    global _runtime
    if _runtime is None:
        _runtime = ConversationRuntime()
    return _runtime


__all__ = [
    "ConversationRuntime",
    "ConversationHandle",
    "TurnResult",
    "ConversationBusyError",
    "get_conversation_runtime",
]

"""ConversationRuntime — authoritative logical conversation owner.

CORE-C1.1: process_turn() is the ONLY Julia-native turn path.
No bypass via _service.repo, chat_conversation(), or external cognition.

Hardening:
  - Thread-safe single-flight (per-conversation Lock)
  - Persistence-based turn idempotency (check canonical store)
  - Failed turn handling (user message pending until completion)
  - No public access to internal repository
"""

from __future__ import annotations

import json as _json
import logging
import threading
import time as _time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

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
    status: str = ""  # completed | failed
    created_at: str = ""
    completed_at: str = ""


# ── Conversation Handle ───────────────────────────────────────────────────────

@dataclass
class ConversationHandle:
    conversation_id: str = ""
    state: str = ""
    created_at: str = ""
    updated_at: str = ""
    last_turn_id: str = ""
    message_count: int = 0


# ── Turn Streaming Context ────────────────────────────────────────────────────

@dataclass
class TurnStreamingContext:
    """Holds streaming turn state between begin/commit/cancel."""
    conversation_id: str
    turn_id: str
    modality: str = "text"
    history: list[dict] = field(default_factory=list)
    user_msg_id: str = ""
    interaction: Any = None  # ConversationInteractionState (working copy)
    lock: Any = None  # threading.Lock
    already_completed_content: str = ""  # Non-empty if idempotent hit


# ── Runtime ──────────────────────────────────────────────────────────────────

class ConversationRuntime:
    """Authoritative conversation owner. Single instance per process.

    process_turn() is the ONLY Julia-native turn path. All cognitive execution,
    persistence, concurrency control, and idempotency flow through it.

    Usage:
        rt = ConversationRuntime()

        result = rt.process_turn(
            conversation_id="conv-A",
            turn_id="turn-001",
            modality="text",
            input="我们之前聊到哪里了？",
            cognitive_fn=cognitive_pipeline,  # (text, history) -> reply
        )
    """

    def __init__(self, storage_path: str | Path = "data/conversations.json"):
        self._storage_path = str(storage_path)
        self._service = ConversationService(filepath=self._storage_path)
        self._locks: dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()
        self._interaction_states: dict[str, "ConversationInteractionState"] = {}
        from julia_core.runtime.relationship import ConversationInteractionState as CIS
        self._CIS = CIS

    @property
    def storage_path(self) -> str:
        return self._storage_path

    # ── Public API ───────────────────────────────────────────────────────

    def get_or_create(self, conversation_id: str) -> ConversationHandle:
        session = self._repo.get(conversation_id)
        if session is None:
            session = self._create_conversation(conversation_id)
        return self._to_handle(session)

    def get_interaction_state(self, conversation_id: str) -> "ConversationInteractionState":
        """Get or create per-conversation interaction state.

        Persists across turns within a conversation. Isolated from other convs.
        """
        if conversation_id not in self._interaction_states:
            self._interaction_states[conversation_id] = self._CIS()
        return self._interaction_states[conversation_id]

    def get_history(
        self, conversation_id: str, max_messages: int = 40
    ) -> list[dict[str, str]]:
        session = self._repo.get(conversation_id)
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
        cognitive_fn: Callable[[str, list[dict], str, str, str, object], str],
    ) -> TurnResult:
        """Execute one cognitive turn. THE ONLY Julia-native turn path.

        Pipeline:
          1. Acquire per-conversation lock (thread-safe single-flight)
          2. Persistence-based idempotency check
          3. Load conversation + history
          4. Persist user message (status=pending)
          5. Execute cognitive_fn(input, history, conversation_id, turn_id, modality)
          6. On success: update user→completed, persist assistant→completed
          7. On failure: mark user→failed, mark assistant→failed
          8. Release lock
        """
        lock = self._get_lock(conversation_id)
        with lock:
            return self._process_turn_locked(
                conversation_id, turn_id, modality, input, cognitive_fn
            )

    def restore(self, conversation_id: str) -> ConversationHandle | None:
        session = self._repo.get(conversation_id)
        if session is None:
            return None
        return self._to_handle(session)

    def close(self, conversation_id: str) -> None:
        pass  # State preserved in persistence

    def begin_turn_streaming(
        self, *, conversation_id: str, turn_id: str, modality: str, input: str,
    ) -> TurnStreamingContext:
        """Begin a streaming turn. Returns context for Brain to stream through.

        Brain calls this, streams deltas from DeepSeek through TurnStreamingContext,
        then calls complete_turn_streaming() or cancel_turn_streaming().
        """
        lock = self._get_lock(conversation_id)
        lock.acquire()

        try:
            # Idempotency
            if turn_id:
                existing = self._find_turn_in_store(conversation_id, turn_id)
                if existing and existing.status == "completed":
                    lock.release()
                    existing._already_completed = True
                    return TurnStreamingContext(
                        conversation_id=conversation_id, turn_id=turn_id,
                        modality=modality, history=[], user_msg_id="",
                        interaction=None, lock=None,
                        already_completed_content=existing.assistant_content,
                    )

            session = self._repo.get(conversation_id)
            if session is None:
                session = self._create_conversation(conversation_id)

            history = self.get_history(conversation_id)

            import copy
            canonical = self.get_interaction_state(conversation_id)
            working = copy.deepcopy(canonical)

            user_msg = self._add_message(
                conversation_id, role="user", content=input,
                turn_id=turn_id, modality=modality, status="pending",
            )
            user_msg_id = user_msg.messages[-1].message_id if user_msg else ""

            return TurnStreamingContext(
                conversation_id=conversation_id, turn_id=turn_id,
                modality=modality,
                history=history, user_msg_id=user_msg_id,
                interaction=working, lock=lock,
            )
        except Exception:
            lock.release()
            raise

    def commit_streaming_turn(
        self, ctx: "TurnStreamingContext", assistant_content: str,
    ) -> TurnResult:
        """Commit a successfully completed streaming turn."""
        try:
            self._update_message_status(ctx.user_msg_id, "completed")
            self._interaction_states[ctx.conversation_id] = ctx.interaction

            assistant_msg = self._add_message(
                ctx.conversation_id, role="assistant", content=assistant_content,
                turn_id=ctx.turn_id, modality=ctx.modality, status="completed",
            )
            assistant_msg_id = assistant_msg.messages[-1].message_id if assistant_msg else ""

            now = _time.strftime("%Y-%m-%dT%H:%M:%S")
            return TurnResult(
                conversation_id=ctx.conversation_id, turn_id=ctx.turn_id,
                user_message_id=ctx.user_msg_id,
                assistant_message_id=assistant_msg_id,
                assistant_content=assistant_content,
                status="completed",
                created_at=now, completed_at=_time.strftime("%Y-%m-%dT%H:%M:%S"),
            )
        finally:
            if ctx.lock:
                ctx.lock.release()

    def cancel_streaming_turn(self, ctx: "TurnStreamingContext"):
        """Cancel/rollback a streaming turn."""
        try:
            self._update_message_status(ctx.user_msg_id, "failed")
        finally:
            if ctx.lock:
                ctx.lock.release()

    def list_conversations(self) -> list[ConversationHandle]:
        return [self._to_handle(s) for s in self._repo.list_all()]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation, history, interaction state, and lock."""
        self._interaction_states.pop(conversation_id, None)
        with self._locks_lock:
            self._locks.pop(conversation_id, None)
        return self._repo.delete(conversation_id)

    # ── CORE-CM1: Management API ─────────────────────────────────────────

    def create_conversation(self, conversation_id: str = "", title: str = "New Conversation") -> ConversationHandle:
        """Create a new conversation. If conversation_id is provided, use it as the canonical ID."""
        cid = conversation_id or f"conv_{_time.strftime('%Y%m%d_%H%M%S')}_{id(self)}"
        self._repo.create_with_id(cid, title)
        self._interaction_states.pop(cid, None)  # Fresh start
        return self._to_handle(self._repo.get(cid))

    def get_conversation(self, conversation_id: str) -> dict | None:
        """Get full conversation detail including messages."""
        session = self._repo.get(conversation_id)
        if session is None:
            return None
        return session.detail()

    def get_messages(self, conversation_id: str, max_messages: int = 100) -> list[dict]:
        """Get messages as dicts with full metadata (message_id, turn_id, modality, status)."""
        session = self._repo.get(conversation_id)
        if session is None:
            return []
        return [m.to_dict() for m in session.messages[-max_messages:]]

    def rename_conversation(self, conversation_id: str, title: str) -> ConversationHandle | None:
        """Rename a conversation. Title persists across restarts."""
        session = self._repo.update_title(conversation_id, title)
        if session is None:
            return None
        return self._to_handle(session)

    def search_conversations(self, query: str) -> list[ConversationHandle]:
        """Search conversations by title or message content."""
        sessions = self._repo.search(query)
        return [self._to_handle(s) for s in sessions]

    # ── Legacy Migration ──────────────────────────────────────────────────

    def migrate_legacy_sessions(
        self, legacy_path: str | Path = "/Users/admin/.julia/sessions.json"
    ) -> int:
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
            if self._repo.get(sid) is not None:
                continue
            self._create_conversation(sid)
            for m in meta.get("messages", []):
                role = m.get("role", "")
                content = m.get("content", "")
                if role in ("user", "assistant") and content.strip():
                    self._add_message(sid, role=role, content=content, modality="text", status="completed")
            if meta.get("title"):
                self._repo.update_title(sid, str(meta["title"]))
            migrated += 1

        if migrated > 0:
            logger.info(f"Migrated {migrated} legacy sessions from {legacy}")
        return migrated

    # ── Internal ──────────────────────────────────────────────────────────

    @property
    def _repo(self) -> SessionRepository:
        return self._service.repo

    def _get_lock(self, conversation_id: str) -> threading.Lock:
        with self._locks_lock:
            if conversation_id not in self._locks:
                self._locks[conversation_id] = threading.Lock()
            return self._locks[conversation_id]

    def _process_turn_locked(
        self,
        conversation_id: str,
        turn_id: str,
        modality: str,
        input: str,
        cognitive_fn: Callable[[str, list[dict], str, str, str, object], str],
    ) -> TurnResult:
        now = _time.strftime("%Y-%m-%dT%H:%M:%S")

        # 1. Idempotency: check canonical store for existing completed turn
        if turn_id:
            existing = self._find_turn_in_store(conversation_id, turn_id)
            if existing and existing.status == "completed":
                return existing

        # 2. Load/ensure conversation
        session = self._repo.get(conversation_id)
        if session is None:
            session = self._create_conversation(conversation_id)

        # 3. Get history (excludes pending/failed messages)
        history = self.get_history(conversation_id)

        # 4. Persist user message as PENDING
        user_msg = self._add_message(
            conversation_id, role="user", content=input,
            turn_id=turn_id, modality=modality, status="pending",
        )
        user_msg_id = user_msg.messages[-1].message_id if user_msg else ""

        # 5. Cognitive execution with transactional interaction state
        # Copy canonical interaction → working copy. Commit only on success.
        import copy
        canonical = self.get_interaction_state(conversation_id)
        working = copy.deepcopy(canonical)

        try:
            assistant_content = cognitive_fn(input, history, conversation_id, turn_id, modality, working)
            assistant_status = "completed"
            user_final_status = "completed"
            # Commit: replace canonical with working copy
            self._interaction_states[conversation_id] = working
        except Exception as exc:
            logger.error(f"Cognitive pipeline failed for {conversation_id}/{turn_id}: {exc}")
            assistant_content = ""
            assistant_status = "failed"
            user_final_status = "failed"
            # Rollback: canonical interaction state unchanged

        # 6. Update user message to final status
        self._update_message_status(user_msg_id, user_final_status)

        # 7. Persist assistant message
        assistant_msg = self._add_message(
            conversation_id, role="assistant", content=assistant_content,
            turn_id=turn_id, modality=modality, status=assistant_status,
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

        return result

    def _find_turn_in_store(self, conversation_id: str, turn_id: str) -> TurnResult | None:
        """Check canonical store for an existing completed turn."""
        msgs = self._repo.find_turn(conversation_id, turn_id)
        user_msg = None
        assistant_msg = None
        for m in msgs:
            if m.role == "user":
                user_msg = m
            elif m.role == "assistant":
                assistant_msg = m
        if user_msg and assistant_msg and assistant_msg.status == "completed":
            return TurnResult(
                conversation_id=conversation_id,
                turn_id=turn_id,
                user_message_id=user_msg.message_id,
                assistant_message_id=assistant_msg.message_id,
                assistant_content=assistant_msg.content,
                status="completed",
                created_at=user_msg.created_at,
                completed_at=assistant_msg.created_at,
            )
        return None

    def _add_message(
        self, conversation_id: str, *, role: str, content: str,
        turn_id: str = "", modality: str = "text", status: str = "completed",
    ) -> ConversationSession | None:
        return self._repo.add_message(
            conversation_id, role=role, content=content,
            turn_id=turn_id, modality=modality, status=status,
        )

    def _update_message_status(self, message_id: str, status: str) -> None:
        """Update a persisted message's status via public repo API."""
        if message_id:
            self._repo.update_message_status(message_id, status)

    def _create_conversation(self, conversation_id: str) -> ConversationSession:
        return self._repo.create_with_id(conversation_id, "New Conversation")

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
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        super().__init__(f"Conversation {conversation_id} is busy with another turn")


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

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
from julia_core.conversation_state.repository_protocol import ConversationRepository

logger = logging.getLogger("julia.conversation_runtime")


# ── Turn Result ───────────────────────────────────────────────────────────────

@dataclass
class TurnResult:
    conversation_id: str = ""
    turn_id: str = ""
    user_message_id: str = ""
    assistant_message_id: str = ""
    assistant_content: str = ""
    status: str = ""  # completed | failed | accepted
    created_at: str = ""
    completed_at: str = ""
    # Internal: R1-B idempotency support
    _user_content: str = ""
    _idempotent_replay: bool = False

    def _user_content_match(self, content: str) -> bool:
        """Check if the stored user content matches the given content."""
        return self._user_content == content


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
    already_completed: bool = False  # True if idempotent hit
    completed_content: str = ""  # Cached content if already_completed


# ── S1D Governed Cutover types ────────────────────────────────────────────────

@dataclass(frozen=True)
class CutoverActivationPermit:
    """One-shot activation permit (typed immutable, no filesystem path)."""
    cutover_id: str
    freeze_epoch: str
    source_binding_epoch: int
    candidate_binding_id: str
    reconciliation_evidence_id: str
    freeze_boundary_id: str
    verification_digest: str
    issued_at: str


@dataclass(frozen=True)
class RuntimeFreezeAck:
    cutover_id: str
    binding_epoch: int
    write_acceptance: str = "DISABLED"
    frozen_repository: str = ""


@dataclass(frozen=True)
class RepositoryActivationRecord:
    cutover_id: str
    source_repository: str
    activated_repository: str
    new_binding_epoch: int


class CutoverConflictError(Exception):
    """Governed cutover state violation (AT-CUT fail-closed)."""


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

    def __init__(self, repository: ConversationRepository | None = None):
        # F2-I02 / F2-I07: Core receives a repository dependency only. It
        # MUST NOT construct a physical repository, hardcode a filesystem
        # path, or know JULIA_PRIVATE_DATA_ROOT. The Assistant composition
        # root injects the bound repository via configure_conversation_runtime.
        self._repository: ConversationRepository | None = repository
        self._locks: dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()
        self._interaction_states: dict[str, "ConversationInteractionState"] = {}
        # S1D governed cutover state (Core-owned semantic gate)
        self._canonical_write_acceptance: bool = True
        self._active_cutover_id: str | None = None
        self._binding_epoch: int = 0
        self._binding_lock = threading.Lock()
        self._consumed_cutover_ids: set[str] = set()
        from julia_core.runtime.relationship import ConversationInteractionState as CIS
        self._CIS = CIS

    @property
    def repository(self) -> ConversationRepository:
        if self._repository is None:
            raise RuntimeError(
                "ConversationRuntime has no bound repository; the Assistant "
                "composition root must inject one (F2-I07)"
            )
        return self._repository

    # ── S1D governed cutover surface (Core-owned semantic gate) ──────────

    def _assert_canonical_write_allowed(self) -> None:
        if not self._canonical_write_acceptance:
            raise CutoverConflictError(
                "canonical write acceptance DISABLED (cutover freeze)"
            )

    def freeze_repository_cutover(
        self, *, cutover_id: str, expected_active_repository: ConversationRepository,
    ) -> RuntimeFreezeAck:
        """FREEZE: disable canonical write acceptance atomically; the
        repository stays the expected active legacy (S1D §1)."""
        with self._binding_lock:
            if self._repository is not expected_active_repository:
                raise CutoverConflictError("expected active repository mismatch")
            if self._active_cutover_id is not None:
                raise CutoverConflictError("conflicting cutover already active")
            self._canonical_write_acceptance = False
            self._active_cutover_id = cutover_id
            return RuntimeFreezeAck(
                cutover_id=cutover_id,
                binding_epoch=self._binding_epoch,
                write_acceptance="DISABLED",
                frozen_repository=type(expected_active_repository).__name__,
            )

    def activate_repository_cutover(
        self, *, cutover_id: str, expected_active_repository: ConversationRepository,
        candidate_repository: ConversationRepository,
        activation_permit: CutoverActivationPermit,
    ) -> RepositoryActivationRecord:
        """ACTIVATE: one atomic authority switch Legacy → Segmented (S1D §3).
        Writes remain DISABLED after the switch (crash window); the Assistant
        records activation commit, then calls enable_canonical_writes()."""
        with self._binding_lock:
            if self._active_cutover_id != cutover_id:
                raise CutoverConflictError("no matching frozen cutover")
            if self._canonical_write_acceptance:
                raise CutoverConflictError("write acceptance must be DISABLED before ACTIVATE")
            if self._repository is not expected_active_repository:
                raise CutoverConflictError("current repository is not the expected legacy")
            if candidate_repository is expected_active_repository:
                raise CutoverConflictError("candidate must differ from current")
            if activation_permit.cutover_id != cutover_id:
                raise CutoverConflictError("permit does not belong to this cutover")
            if cutover_id in self._consumed_cutover_ids:
                raise CutoverConflictError("activation permit already consumed")
            self._repository = candidate_repository
            self._binding_epoch += 1
            self._consumed_cutover_ids.add(cutover_id)
            return RepositoryActivationRecord(
                cutover_id=cutover_id,
                source_repository=type(expected_active_repository).__name__,
                activated_repository=type(candidate_repository).__name__,
                new_binding_epoch=self._binding_epoch,
            )

    def enable_canonical_writes(self) -> None:
        """Re-enable canonical write acceptance (after durable activation commit)."""
        with self._binding_lock:
            self._canonical_write_acceptance = True

    # ── Public API ───────────────────────────────────────────────────────

    def get_or_create(self, conversation_id: str, *, create: bool = False) -> ConversationHandle:
        """Get conversation handle. With create=True, explicitly create if absent.
        CM-FAILCLOSED F4: resume/bind/turn paths must NOT auto-create.
        """
        session = self.repository.get(conversation_id)
        if session is None:
            if not create:
                raise ValueError(f"Conversation not found: {conversation_id}")
            session = self._create_conversation(conversation_id)
        return self._to_handle(session)

    def get_interaction_state(self, conversation_id: str) -> "ConversationInteractionState":
        """Get or rebuild per-conversation interaction state.

        CORE-C1B-R1: If cache is empty, rebuild from canonical message history.
        Messages are the durable authority; interaction state is derived cache.
        """
        if conversation_id not in self._interaction_states:
            state = self._CIS()
            session = self.repository.get(conversation_id)
            if session:
                for m in session.messages:
                    if m.role == "user" and m.status == "completed":
                        state.update(m.content)
            self._interaction_states[conversation_id] = state
        return self._interaction_states[conversation_id]

    def append_external_turns(
        self, conversation_id: str, turns: list[dict], *,
        source: str = "voice-s2s", source_session_id: str = "",
        base_last_message_id: str = "",
    ) -> dict:
        """CORE-C1B-R1: Atomically append external (voice) turns.

        Does NOT call LLM, STT, TTS, or cognitive pipeline.
        Only validates, appends atomically, updates interaction cache.

        Returns: {conversation_id, appended_turn_ids, skipped_turn_ids,
                  message_count, last_message_id}
        Raises: ValueError if conversation not found.
                TurnConflictError if same turn_id with different content.
        """
        lock = self._get_lock(conversation_id)
        with lock:
            from julia_core.conversation_state.repository import (
                TurnConflictError, ConversationAdvancedError,
                ConversationNotFoundError, InvalidTurnStateError,
            )

            try:
                self._assert_canonical_write_allowed()
                appended, skipped, last_msg_id = self.repository.append_external_turns_atomic(
                    conversation_id, turns,
                    base_last_message_id=base_last_message_id,
                )
            except (TurnConflictError, ConversationAdvancedError,
                     ConversationNotFoundError, InvalidTurnStateError):
                raise

            # Update interaction cache from newly appended user messages
            if appended and conversation_id in self._interaction_states:
                state = self._interaction_states[conversation_id]
                session = self.repository.get(conversation_id)
                if session:
                    for m in session.messages:
                        if m.turn_id in appended and m.role == "user" and m.status == "completed":
                            state.update(m.content)

            session = self.repository.get(conversation_id)
            return {
                "conversation_id": conversation_id,
                "appended_turn_ids": appended,
                "skipped_turn_ids": skipped,
                "message_count": session.message_count if session else 0,
                "last_message_id": last_msg_id or "",
            }

    def get_canonical_history(
        self, conversation_id: str,
    ) -> list[dict[str, str]]:
        """R1-C: Return FULL completed canonical history for Context OS.

        Does NOT impose a fixed-N message cap. Context OS alone applies
        ActiveTail budget, retrieval policy, and cognitive selection.

        This replaces the old get_history(max_messages=40) cognitive cap.
        """
        session = self.repository.get(conversation_id)
        if session is None:
            return []
        return [
            {"role": m.role, "content": m.content}
            for m in session.messages
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
        session = self.repository.get(conversation_id)
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
        if not lock.acquire(blocking=False):
            raise ConversationBusyError(conversation_id)

        try:
            # R1-B: Idempotency — any existing turn with user message
            if turn_id:
                existing = self._find_turn_in_store(conversation_id, turn_id)
                if existing is not None:
                    lock.release()
                    existing._already_completed = (
                        existing.assistant_content.strip() != ""
                    )
                    return TurnStreamingContext(
                        conversation_id=conversation_id, turn_id=turn_id,
                        modality=modality, history=[], user_msg_id="",
                        interaction=None, lock=None,
                        already_completed=existing._already_completed,
                        completed_content=existing.assistant_content,
                    )

            session = self.repository.get(conversation_id)
            if session is None:
                raise ValueError(f"Conversation not found for turn: {conversation_id}")

            history = self.get_canonical_history(conversation_id)

            import copy
            canonical = self.get_interaction_state(conversation_id)
            working = copy.deepcopy(canonical)

            # R1-B: user message is completed immediately (durable before cognition)
            user_msg = self._add_message(
                conversation_id, role="user", content=input,
                turn_id=turn_id, modality=modality, status="completed",
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
        """Commit a successfully completed streaming turn.

        R1-B: user message already completed on begin_turn_streaming.
        No user status update needed. Assistant only.
        """
        try:
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
            # RMD-1 / CM-I05:
            # begin_turn_streaming() has already accepted the user message as a
            # durable canonical fact (status=completed). Assistant cancellation
            # is an independent lifecycle event and must not downgrade or erase
            # that accepted user turn.
            pass
        finally:
            if ctx.lock:
                ctx.lock.release()

    def import_messages(
        self, conversation_id: str, messages: list[dict], *,
        source: str = "",
    ) -> dict:
        """CORE-C1B-M1: Merge historical messages into canonical conversation.

        For importing pre-existing history. Does NOT call LLM or cognitive pipeline.
        Returns: {conversation_id, imported_count, skipped_count, message_count, last_message_id}
        """
        from julia_core.conversation_state.repository import (
            TurnConflictError, ConversationNotFoundError, InvalidTurnStateError,
        )

        lock = self._get_lock(conversation_id)
        with lock:
            try:
                self._assert_canonical_write_allowed()
                imported, skipped, last_id = self.repository.import_messages_atomic(
                    conversation_id, messages,
                )
            except (TurnConflictError, ConversationNotFoundError, InvalidTurnStateError):
                raise

            # Invalidate interaction cache — will rebuild from merged history
            self._interaction_states.pop(conversation_id, None)

            session = self.repository.get(conversation_id)
            return {
                "conversation_id": conversation_id,
                "imported_count": imported,
                "skipped_count": skipped,
                "message_count": session.message_count if session else 0,
                "last_message_id": last_id or "",
            }

    def list_conversations(self) -> list[ConversationHandle]:
        return [self._to_handle(s) for s in self.repository.list_all()]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation, history, interaction state, and lock."""
        self._assert_canonical_write_allowed()
        self._interaction_states.pop(conversation_id, None)
        with self._locks_lock:
            self._locks.pop(conversation_id, None)
        return self.repository.delete(conversation_id)

    # ── CORE-CM1: Management API ─────────────────────────────────────────

    def create_conversation(self, conversation_id: str = "", title: str = "New Conversation") -> ConversationHandle:
        """R1-D Core-first create: durable canonical conversation before client bind.

        Success means the conversation already exists in the canonical repository
        and survives Core restart. Idempotent: same conversation_id returns the
        existing conversation. Conversation exists independently of any message.
        """
        cid = conversation_id or f"conv_{_time.strftime('%Y%m%d_%H%M%S')}_{id(self)}"
        self._assert_canonical_write_allowed()
        self.repository.create_with_id(cid, title)
        self._interaction_states.pop(cid, None)
        return self._to_handle(self.repository.get(cid))

    def get_conversation(self, conversation_id: str) -> dict | None:
        """Get full conversation detail including messages."""
        session = self.repository.get(conversation_id)
        if session is None:
            return None
        return session.detail()

    def get_messages(self, conversation_id: str, max_messages: int = 100) -> list[dict]:
        """Get messages as dicts with full metadata (message_id, turn_id, modality, status)."""
        session = self.repository.get(conversation_id)
        if session is None:
            return []
        return [m.to_dict() for m in session.messages[-max_messages:]]

    def rename_conversation(self, conversation_id: str, title: str) -> ConversationHandle | None:
        """Rename a conversation. Title persists across restarts."""
        self._assert_canonical_write_allowed()
        session = self.repository.update_title(conversation_id, title)
        if session is None:
            return None
        return self._to_handle(session)

    def search_conversations(self, query: str) -> list[ConversationHandle]:
        """Search conversations by title or message content."""
        sessions = self.repository.search(query)
        return [self._to_handle(s) for s in sessions]

    # ── Legacy Migration ──────────────────────────────────────────────────

    def migrate_legacy_sessions(
        self, legacy_path: str | Path = "/Users/admin/.julia/sessions.json"
    ) -> int:
        self._assert_canonical_write_allowed()
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
            if self.repository.get(sid) is not None:
                continue
            self._create_conversation(sid)
            for m in meta.get("messages", []):
                role = m.get("role", "")
                content = m.get("content", "")
                if role in ("user", "assistant") and content.strip():
                    self._add_message(sid, role=role, content=content, modality="text", status="completed")
            if meta.get("title"):
                self.repository.update_title(sid, str(meta["title"]))
            migrated += 1

        if migrated > 0:
            logger.info(f"Migrated {migrated} legacy sessions from {legacy}")
        return migrated

    # ── Internal ──────────────────────────────────────────────────────────

    def _get_lock(self, conversation_id: str) -> threading.Lock:
        with self._locks_lock:
            if conversation_id not in self._locks:
                self._locks[conversation_id] = threading.Lock()
            return self._locks[conversation_id]

    # ── R1-B: Durable User Acceptance ──────────────────────────────────

    def accept_user_turn(
        self, *, conversation_id: str, turn_id: str,
        modality: str = "text", content: str,
    ) -> TurnResult:
        """CM-I05: Accept a user turn as durable canonical fact BEFORE cognition.

        Returns AcceptedUserTurn once the user message is durably persisted.
        Idempotent: same turn_id + same content → returns existing result.
        Raises TurnConflictError: same turn_id + different content.

        User message status = completed immediately. Assistant lifecycle is
        independent — cognition failure does not erase or downgrade the user.
        """
        lock = self._get_lock(conversation_id)
        with lock:
            return self._accept_user_turn_locked(
                conversation_id=conversation_id, turn_id=turn_id,
                modality=modality, content=content,
            )

    def _accept_user_turn_locked(
        self, *, conversation_id: str, turn_id: str,
        modality: str = "text", content: str,
    ) -> TurnResult:
        """Internal: caller must hold per-conversation lock."""
        from julia_core.conversation_state.repository import TurnConflictError

        # Idempotency: check canonical store for existing turn
        if turn_id:
            existing = self._find_turn_in_store(conversation_id, turn_id)
            if existing is not None:
                if existing._user_content_match(content):
                    existing.status = "completed"
                    existing._idempotent_replay = True
                    return existing
                raise TurnConflictError(
                    f"Turn {turn_id}: content differs from persisted"
                )

        # Ensure conversation exists
        if self.repository.get(conversation_id) is None:
            self._create_conversation(conversation_id)

        now = _time.strftime("%Y-%m-%dT%H:%M:%S")

        # Durable canonical user append — status = completed immediately
        user_msg = self._add_message(
            conversation_id, role="user", content=content,
            turn_id=turn_id, modality=modality, status="completed",
        )
        user_msg_id = user_msg.messages[-1].message_id if user_msg else ""

        return TurnResult(
            conversation_id=conversation_id,
            turn_id=turn_id,
            user_message_id=user_msg_id,
            assistant_message_id="",
            assistant_content="",
            status="accepted",
            created_at=now,
        )

    def _process_turn_locked(
        self,
        conversation_id: str,
        turn_id: str,
        modality: str,
        input: str,
        cognitive_fn: Callable[[str, list[dict], str, str, str, object], str],
    ) -> TurnResult:
        # R1-B: accept user turn first (durable, canonical, completed)
        now = _time.strftime("%Y-%m-%dT%H:%M:%S")

        try:
            accepted = self._accept_user_turn_locked(
                conversation_id=conversation_id, turn_id=turn_id,
                modality=modality, content=input,
            )
        except Exception:
            raise  # TurnConflictError propagates; caller handles

        if getattr(accepted, '_idempotent_replay', False):
            return accepted

        user_msg_id = accepted.user_message_id

        # Get history for cognition
        history = self.get_canonical_history(conversation_id)

        # Cognitive execution with transactional interaction state
        import copy
        canonical = self.get_interaction_state(conversation_id)
        working = copy.deepcopy(canonical)

        # R1-B: assistant lifecycle independent of user durability
        try:
            assistant_content = cognitive_fn(
                input, history, conversation_id, turn_id, modality, working,
            )
            assistant_status = "completed"
            self._interaction_states[conversation_id] = working
        except Exception as exc:
            logger.error(
                f"Cognitive pipeline failed for {conversation_id}/{turn_id}: {exc}"
            )
            assistant_content = ""
            assistant_status = "failed"
            # USER MESSAGE UNCHANGED. No user_final_status mutation.

        # Persist assistant message
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
        """Check canonical store for an existing turn.

        R1-B: user messages are status=completed on accept.
        Finds any turn by turn_id with a user message.
        Returns TurnResult with _user_content set for idempotency comparison.
        """
        msgs = self.repository.find_turn(conversation_id, turn_id)
        user_msg = None
        assistant_msg = None
        for m in msgs:
            if m.role == "user":
                user_msg = m
            elif m.role == "assistant":
                assistant_msg = m
        if user_msg is None:
            return None
        result = TurnResult(
            conversation_id=conversation_id,
            turn_id=turn_id,
            user_message_id=user_msg.message_id,
            assistant_message_id=assistant_msg.message_id if assistant_msg else "",
            assistant_content=assistant_msg.content if assistant_msg else "",
            status=assistant_msg.status if assistant_msg else "accepted",
            created_at=user_msg.created_at,
            completed_at=assistant_msg.created_at if assistant_msg else "",
            _user_content=user_msg.content,
        )
        return result

    def _add_message(
        self, conversation_id: str, *, role: str, content: str,
        turn_id: str = "", modality: str = "text", status: str = "completed",
    ) -> ConversationSession | None:
        self._assert_canonical_write_allowed()
        return self.repository.add_message(
            conversation_id, role=role, content=content,
            turn_id=turn_id, modality=modality, status=status,
        )

    def _update_message_status(self, message_id: str, status: str) -> None:
        """Update a persisted message's status via public repo API."""
        if message_id:
            self._assert_canonical_write_allowed()
            self.repository.update_message_status(message_id, status)

    def _create_conversation(self, conversation_id: str) -> ConversationSession:
        self._assert_canonical_write_allowed()
        return self.repository.create_with_id(conversation_id, "New Conversation")

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


class ConversationCutoverRequired(Exception):
    """F2-I11: replacing an active canonical adapter is an authority cutover."""

    def __init__(self):
        super().__init__(
            "PERSISTENCE_CUTOVER_REQUIRED: active repository binding is "
            "immutable; replacement requires a governed FREEZE→RECONCILE→"
            "VERIFY→ACTIVATE→RETIRE sequence"
        )


# ── Singleton ─────────────────────────────────────────────────────────────────

_runtime: ConversationRuntime | None = None
_runtime_lock = threading.Lock()


def configure_conversation_runtime(repository: ConversationRepository) -> ConversationRuntime:
    """F2-I01/I07: the Assistant composition root injects the bound physical
    repository. First configuration establishes the binding epoch. Re-binding
    the SAME repository is idempotent; re-binding a DIFFERENT repository is a
    governed adapter cutover and MUST raise (F2-I10/I11 / F2A-R3)."""
    global _runtime
    with _runtime_lock:
        if _runtime is not None:
            if _runtime.repository is repository:
                return _runtime  # idempotent same binding
            raise ConversationCutoverRequired()
        _runtime = ConversationRuntime(repository=repository)
        return _runtime


def get_conversation_runtime() -> ConversationRuntime:
    global _runtime
    if _runtime is None:
        raise RuntimeError(
            "ConversationRuntime is not configured; the Assistant composition "
            "root must call configure_conversation_runtime(repository) first (F2-I07)"
        )
    return _runtime


__all__ = [
    "ConversationRuntime",
    "ConversationHandle",
    "TurnResult",
    "ConversationBusyError",
    "ConversationCutoverRequired",
    "CutoverActivationPermit",
    "RuntimeFreezeAck",
    "RepositoryActivationRecord",
    "CutoverConflictError",
    "configure_conversation_runtime",
    "get_conversation_runtime",
]

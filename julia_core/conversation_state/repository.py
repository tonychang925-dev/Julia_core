"""Conversation session repository — thread-safe, atomic JSON persistence.

CORE-C1.2: RLock protects all read/write. Atomic temp-file + os.replace.
Runtime must NOT access _sessions or _save() directly.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from julia_core.conversation_state.models import (
    ConversationSession,
    ConversationMessage,
)


class ConversationNotFoundError(ValueError):
    """Conversation does not exist."""
    pass


class TurnConflictError(ValueError):
    """Same turn_id, different content."""
    pass


class ConversationAdvancedError(ValueError):
    """Base cursor mismatch — conversation has advanced since snapshot."""
    pass


class InvalidTurnStateError(ValueError):
    """Turn schema validation failed."""
    pass


class RepositoryReadOnlyError(RuntimeError):
    """Repository has been retired to read-only; canonical writes are rejected."""
    pass


class SessionRepository:
    """Thread-safe in-memory store with atomic JSON persistence.

    All public methods acquire _lock. Runtime never accesses _sessions directly.
    """

    def __init__(self, filepath: str | Path = "data/sessions.json"):
        self._filepath = Path(filepath)
        self._sessions: dict[str, ConversationSession] = {}
        self._lock = threading.RLock()
        self._read_only = False
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
        """Atomic write: temp file → fsync → os.replace. Must hold _lock."""
        if self._read_only:
            raise RepositoryReadOnlyError("repository retired; read-only")
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        data = [s.detail() for s in self.list_all()]
        tmp = self._filepath.with_suffix(".json.tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self._filepath)

    def set_read_only(self) -> None:
        """RETIRE: mark this repository read-only. Canonical writes rejected."""
        with self._lock:
            self._read_only = True

    # ── Public API (all locked) ──────────────────────────────────────────

    def list_all(self) -> list[ConversationSession]:
        with self._lock:
            return sorted(
                self._sessions.values(),
                key=lambda s: s.updated_at,
                reverse=True,
            )

    def get(self, session_id: str) -> ConversationSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def create(self, title: str = "New Conversation") -> ConversationSession:
        with self._lock:
            session = ConversationSession(title=title)
            self._sessions[session.id] = session
            self._save()
            return session

    def create_with_id(self, session_id: str, title: str = "New Conversation") -> ConversationSession:
        """Create a conversation with a pre-determined ID. Idempotent."""
        with self._lock:
            existing = self._sessions.get(session_id)
            if existing is not None:
                return existing
            session = ConversationSession(id=session_id, title=title)
            self._sessions[session_id] = session
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
        with self._lock:
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
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            session.title = title
            session.touch()
            self._save()
            return session

    def update_message_status(self, message_id: str, status: str) -> bool:
        """Update a message's status. Returns True if found and updated."""
        with self._lock:
            for session in self._sessions.values():
                for m in session.messages:
                    if m.message_id == message_id:
                        m.status = status
                        self._save()
                        return True
            return False

    def find_turn(self, session_id: str, turn_id: str) -> list[ConversationMessage]:
        """Find all messages for a given turn_id. Returns [user_msg, assistant_msg] if found."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return []
            return [m for m in session.messages if m.turn_id == turn_id]

    def append_external_turns_atomic(
        self, session_id: str, turns: list[dict],
        base_last_message_id: str = "",
    ) -> tuple[list[str], list[str], str | None]:
        """Atomically append external (voice) turns. One lock, one save.

        base_last_message_id: if provided and new turns exist, validates that
        the conversation's current last message matches before appending.

        Returns: (appended_turn_ids, skipped_turn_ids, last_message_id).
        On failure BEFORE save: ZERO mutation, ZERO _save() calls.
        On save failure: complete in-memory rollback.
        """
        from datetime import datetime, timezone, timedelta
        CST = timezone(timedelta(hours=8))

        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise ConversationNotFoundError(f"Conversation not found: {session_id}")

            # Full snapshot for rollback
            saved_messages = list(session.messages)
            saved_title = session.title
            saved_updated_at = session.updated_at
            saved_message_count = session.message_count

            # Phase 1: validate ALL turns first
            for turn in turns:
                turn_id = turn.get("turn_id", "")
                if not turn_id:
                    raise InvalidTurnStateError("turn_id is required")

                user_content = turn.get("user_content", "")
                if not user_content:
                    raise InvalidTurnStateError(f"Turn {turn_id}: user_content is required")

                assistant_content = turn.get("assistant_content")
                assistant_status = turn.get("assistant_status")

                # Null-assistant schema validation
                if assistant_content is None:
                    if assistant_status is not None:
                        raise InvalidTurnStateError(
                            f"Turn {turn_id}: assistant_content=null requires assistant_status=null, "
                            f"got {assistant_status}"
                        )
                else:
                    if assistant_status is None:
                        raise InvalidTurnStateError(
                            f"Turn {turn_id}: assistant_content present requires assistant_status, "
                            f"got null"
                        )
                    if assistant_status not in ("completed", "interrupted"):
                        raise InvalidTurnStateError(
                            f"Turn {turn_id}: assistant_status must be completed|interrupted, "
                            f"got {assistant_status}"
                        )

            # Phase 2: idempotency — check existing turns
            appended: list[str] = []
            skipped: list[str] = []
            new_turns_exist = False

            for turn in turns:
                turn_id = turn.get("turn_id", "")
                existing = [m for m in session.messages if m.turn_id == turn_id]

                if existing:
                    if self._turn_equals(existing, turn):
                        skipped.append(turn_id)
                        continue
                    else:
                        raise TurnConflictError(
                            f"Turn {turn_id}: content differs from persisted"
                        )
                else:
                    new_turns_exist = True

            # Phase 3: if all skipped → idempotent success (skip base cursor, ZERO save)
            if not new_turns_exist:
                last = session.messages[-1] if session.messages else None
                return [], skipped, last.message_id if last else None

            # Phase 4: base cursor check — BEFORE any mutation
            if base_last_message_id:
                current_last = session.messages[-1].message_id if session.messages else ""
                if current_last != base_last_message_id:
                    raise ConversationAdvancedError(
                        f"Conversation advanced: expected base {base_last_message_id}, "
                        f"actual {current_last}"
                    )

            # Phase 5: append new turns atomically
            last_msg_id: str | None = None
            now_str = datetime.now(CST).isoformat()

            try:
                for turn in turns:
                    turn_id = turn.get("turn_id", "")
                    existing = [m for m in session.messages if m.turn_id == turn_id]
                    if existing:
                        continue  # Already skipped

                    modality = turn.get("modality", "voice")

                    # Default timestamp if not provided
                    user_ts = turn.get("user_created_at") or now_str

                    user_msg = ConversationMessage(
                        conversation_id=session_id, turn_id=turn_id,
                        role="user", modality=modality,
                        content=turn["user_content"],
                        status="completed",
                        created_at=user_ts,
                    )
                    session.messages.append(user_msg)
                    last_msg_id = user_msg.message_id

                    assistant_content = turn.get("assistant_content")
                    if assistant_content is not None:
                        assistant_ts = turn.get("assistant_created_at") or now_str
                        assistant_msg = ConversationMessage(
                            conversation_id=session_id, turn_id=turn_id,
                            role="assistant", modality=modality,
                            content=assistant_content,
                            status=turn["assistant_status"],
                            created_at=assistant_ts,
                        )
                        session.messages.append(assistant_msg)
                        last_msg_id = assistant_msg.message_id

                    appended.append(turn_id)

                session.touch()
                session.auto_title()
                self._save()
                return appended, skipped, last_msg_id

            except Exception:
                # Complete rollback
                session.messages = saved_messages
                session.title = saved_title
                session.updated_at = saved_updated_at
                session.message_count = saved_message_count
                raise

    @staticmethod
    def _turn_equals(existing_msgs: list, turn: dict) -> bool:
        """Full turn identity comparison for idempotency."""
        user_existing = next((m for m in existing_msgs if m.role == "user"), None)
        assistant_existing = next((m for m in existing_msgs if m.role == "assistant"), None)

        if user_existing is None:
            return False
        if user_existing.content != turn.get("user_content", ""):
            return False
        if user_existing.modality != turn.get("modality", "voice"):
            return False

        assistant_new_content = turn.get("assistant_content")
        assistant_new_status = turn.get("assistant_status")

        if assistant_existing is None:
            # No existing assistant — new must also have none
            return assistant_new_content is None
        else:
            # Existing assistant — must match content + status
            if assistant_new_content is None:
                return False
            if assistant_existing.content != assistant_new_content:
                return False
            if assistant_existing.status != assistant_new_status:
                return False

        return True

    def import_messages_atomic(
        self, session_id: str, messages: list[dict],
    ) -> tuple[int, int, str | None]:
        """Atomically merge historical messages into canonical conversation.

        CORE-C1B-M1a: strict identity contract.
        Every message MUST have: message_id, turn_id, role, modality, content,
        status, created_at. Missing any required field → InvalidTurnStateError.
        """
        VALID_ROLES = {"user", "assistant"}
        VALID_MODALITIES = {"text", "voice"}
        VALID_STATUSES = {"completed", "interrupted"}
        ISO_RE = __import__("re").compile(
            r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}'
        )

        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise ConversationNotFoundError(f"Conversation not found: {session_id}")

            # Phase 1: validate ALL messages — every field required
            seen_in_batch: set[str] = set()
            for msg in messages:
                msg_id = (msg.get("message_id") or "").strip()
                turn_id = (msg.get("turn_id") or "").strip()
                role = (msg.get("role") or "").strip()
                modality = (msg.get("modality") or "text").strip()
                content = (msg.get("content") or "").strip()
                status = (msg.get("status") or "completed").strip()
                created_at = (msg.get("created_at") or "").strip()

                if not msg_id:
                    raise InvalidTurnStateError("message_id is required")
                if not turn_id:
                    raise InvalidTurnStateError(f"Message {msg_id}: turn_id is required")
                if role not in VALID_ROLES:
                    raise InvalidTurnStateError(f"Message {msg_id}: invalid role '{role}'")
                if modality not in VALID_MODALITIES:
                    raise InvalidTurnStateError(f"Message {msg_id}: invalid modality '{modality}'")
                if not content:
                    raise InvalidTurnStateError(f"Message {msg_id}: content is required")
                if status not in VALID_STATUSES:
                    raise InvalidTurnStateError(f"Message {msg_id}: invalid status '{status}'")
                if not created_at or not ISO_RE.match(created_at):
                    raise InvalidTurnStateError(
                        f"Message {msg_id}: created_at is required (ISO-8601), got '{created_at}'"
                    )

                # Duplicate message_id within same batch
                if msg_id in seen_in_batch:
                    raise InvalidTurnStateError(
                        f"Message {msg_id}: duplicate message_id in request batch"
                    )
                seen_in_batch.add(msg_id)

            # Phase 2: idempotency — full identity comparison
            imported = 0
            skipped = 0
            new_messages: list[dict] = []
            for msg in messages:
                msg_id = msg["message_id"].strip()
                existing = next((m for m in session.messages if m.message_id == msg_id), None)
                if existing:
                    if self._import_msg_equals(existing, msg):
                        skipped += 1
                        continue
                    else:
                        raise TurnConflictError(
                            f"Message {msg_id}: identity exists but content differs"
                        )
                new_messages.append(msg)

            if not new_messages:
                last = session.messages[-1] if session.messages else None
                return 0, skipped, last.message_id if last else None

            # Phase 3: validate turn structure (user→assistant ordering)
            turns: dict[str, list[dict]] = {}
            for msg in new_messages:
                tid = msg["turn_id"].strip()
                turns.setdefault(tid, []).append(msg)
            for tid, tmsgs in turns.items():
                roles = [m["role"] for m in tmsgs]
                if len(tmsgs) > 2:
                    raise InvalidTurnStateError(
                        f"Turn {tid}: max 2 messages per turn (user+assistant), got {len(tmsgs)}"
                    )
                if roles == ["assistant", "user"]:
                    # Swap to user→assistant order
                    tmsgs.reverse()

            # Flatten turns back in chronological order
            ordered_new: list[dict] = []
            for tid in sorted(turns.keys()):
                for msg in turns[tid]:
                    ordered_new.append(msg)

            # Snapshot for rollback
            saved_messages = list(session.messages)
            saved_title = session.title
            saved_updated_at = session.updated_at
            saved_message_count = session.message_count

            try:
                new_objs = []
                for msg in ordered_new:
                    new_objs.append(ConversationMessage(
                        message_id=msg["message_id"].strip(),
                        conversation_id=session_id,
                        turn_id=msg["turn_id"].strip(),
                        role=msg["role"].strip(),
                        modality=msg["modality"].strip(),
                        content=msg["content"].strip(),
                        status=msg["status"].strip(),
                        created_at=msg["created_at"].strip(),
                    ))
                    imported += 1

                # Merge + sort by (created_at, turn_id, role_order)
                all_msgs = session.messages + new_objs
                def _sort_key(m: ConversationMessage):
                    ts = m.created_at or "9999"
                    tid = m.turn_id or ""
                    role_order = 0 if m.role == "user" else 1
                    return (ts, tid, role_order, m.message_id)
                all_msgs.sort(key=_sort_key)

                session.messages = all_msgs
                session.touch()
                session.auto_title()
                self._save()

                last = session.messages[-1] if session.messages else None
                return imported, skipped, last.message_id if last else None

            except Exception:
                session.messages = saved_messages
                session.title = saved_title
                session.updated_at = saved_updated_at
                session.message_count = saved_message_count
                raise

    @staticmethod
    def _import_msg_equals(existing, msg: dict) -> bool:
        """Full identity comparison for historical import idempotency."""
        return (
            existing.message_id == msg.get("message_id", "").strip() and
            existing.turn_id == msg.get("turn_id", "").strip() and
            existing.role == msg.get("role", "").strip() and
            existing.modality == msg.get("modality", "text").strip() and
            existing.content == msg.get("content", "").strip() and
            existing.status == msg.get("status", "completed").strip() and
            existing.created_at == msg.get("created_at", "").strip()
        )

    def delete(self, session_id: str) -> bool:
        with self._lock:
            if session_id not in self._sessions:
                return False
            del self._sessions[session_id]
            self._save()
            return True

    def search(self, query: str) -> list[ConversationSession]:
        with self._lock:
            q = query.lower()
            return [
                s for s in self.list_all()
                if q in s.title.lower()
                or q in s.topic.lower()
                or any(q in tag.lower() for tag in s.tags)
                or any(q in m.content.lower() for m in s.messages if m.role == "user")
            ]

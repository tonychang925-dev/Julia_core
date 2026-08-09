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


class SessionRepository:
    """Thread-safe in-memory store with atomic JSON persistence.

    All public methods acquire _lock. Runtime never accesses _sessions directly.
    """

    def __init__(self, filepath: str | Path = "data/sessions.json"):
        self._filepath = Path(filepath)
        self._sessions: dict[str, ConversationSession] = {}
        self._lock = threading.RLock()
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
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        data = [s.detail() for s in self.list_all()]
        tmp = self._filepath.with_suffix(".json.tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self._filepath)

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

        For importing pre-existing history (Electron legacy cache, backups, etc.)
        NOT for new realtime turns — use append_external_turns_atomic for that.

        Returns: (imported_count, skipped_count, last_message_id).
        On failure: full in-memory rollback. ZERO _save() on error.
        """
        from datetime import datetime, timezone, timedelta
        CST = timezone(timedelta(hours=8))

        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise ConversationNotFoundError(f"Conversation not found: {session_id}")

            # Validate all messages first
            for msg in messages:
                role = msg.get("role", "")
                if role not in ("user", "assistant"):
                    raise InvalidTurnStateError(f"Invalid role: {role}")
                if not msg.get("content", "").strip():
                    raise InvalidTurnStateError("Message content is required")
                status = msg.get("status", "completed")
                if status not in ("completed", "interrupted"):
                    raise InvalidTurnStateError(f"Invalid status for import: {status}")

            # Idempotency: check existing message_ids
            imported = 0
            skipped = 0
            new_messages = []
            for msg in messages:
                msg_id = msg.get("message_id", "")
                if msg_id:
                    existing = next((m for m in session.messages if m.message_id == msg_id), None)
                    if existing:
                        if (existing.role == msg.get("role") and
                            existing.content == msg.get("content", "") and
                            existing.status == msg.get("status", "completed") and
                            existing.modality == msg.get("modality", "text")):
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

            # Snapshot for rollback
            saved_messages = list(session.messages)
            saved_title = session.title
            saved_updated_at = session.updated_at
            saved_message_count = session.message_count

            try:
                # Convert new messages to ConversationMessage objects
                new_objs = []
                for msg in new_messages:
                    new_objs.append(ConversationMessage(
                        message_id=msg.get("message_id") or "",
                        conversation_id=session_id,
                        turn_id=msg.get("turn_id", ""),
                        role=msg.get("role", "user"),
                        modality=msg.get("modality", "text"),
                        content=msg.get("content", ""),
                        status=msg.get("status", "completed"),
                        created_at=msg.get("created_at", ""),
                    ))
                    imported += 1

                # Merge + stable chronological sort
                # Primary: created_at. Secondary: turn_id grouping.
                # Tertiary: role (user before assistant within same turn).
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

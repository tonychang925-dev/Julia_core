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


class TurnConflictError(ValueError):
    """Raised when the same turn_id has different content."""
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
    ) -> tuple[list[str], list[str], str | None]:
        """Atomically append external (voice) turns. One lock, one save.

        Each turn dict: {turn_id, modality, user_content, user_created_at,
                         assistant_content, assistant_status, assistant_created_at}

        Returns: (appended_turn_ids, skipped_turn_ids, last_message_id).
        On failure: in-memory state rolled back, no partial turns.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise ValueError(f"Conversation not found: {session_id}")

            # Snapshot for rollback
            saved_messages = list(session.messages)

            appended: list[str] = []
            skipped: list[str] = []
            last_msg_id: str | None = None

            try:
                for turn in turns:
                    turn_id = turn.get("turn_id", "")
                    modality = turn.get("modality", "voice")

                    # Idempotency: check existing turn_id
                    existing = [m for m in session.messages if m.turn_id == turn_id]
                    if existing:
                        user_existing = next((m for m in existing if m.role == "user"), None)
                        assistant_existing = next((m for m in existing if m.role == "assistant"), None)
                        user_new = turn.get("user_content", "")
                        assistant_new = turn.get("assistant_content", "")

                        if user_existing and user_existing.content == user_new:
                            skipped.append(turn_id)
                            continue
                        else:
                            raise TurnConflictError(
                                f"Turn {turn_id}: content differs from persisted. "
                                f"Existing user='{user_existing.content[:50] if user_existing else 'none'}', "
                                f"New user='{user_new[:50]}'"
                            )

                    # Append user message
                    user_msg = ConversationMessage(
                        conversation_id=session_id, turn_id=turn_id,
                        role="user", modality=modality,
                        content=turn.get("user_content", ""),
                        status="completed",
                        created_at=turn.get("user_created_at", ""),
                    )
                    session.messages.append(user_msg)
                    last_msg_id = user_msg.message_id

                    # Append assistant message if present
                    assistant_content = turn.get("assistant_content", "")
                    assistant_status = turn.get("assistant_status", "completed")
                    if assistant_content or assistant_status in ("interrupted", "failed"):
                        assistant_msg = ConversationMessage(
                            conversation_id=session_id, turn_id=turn_id,
                            role="assistant", modality=modality,
                            content=assistant_content,
                            status=assistant_status,
                            created_at=turn.get("assistant_created_at", ""),
                        )
                        session.messages.append(assistant_msg)
                        last_msg_id = assistant_msg.message_id

                    appended.append(turn_id)

                session.touch()
                session.auto_title()
                self._save()
                return appended, skipped, last_msg_id

            except Exception:
                # Rollback
                session.messages = saved_messages
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

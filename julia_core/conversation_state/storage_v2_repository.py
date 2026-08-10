"""StorageV2ConversationRepository — R2-B Hybrid backend.

Canonical authority:
  meta.json              — conversation metadata
  transcript-*.jsonl     — ConversationMessage truth

Derived:
  catalog.sqlite         — rebuildable index / projection

Invariant R2-S01: Deleting catalog.sqlite loses nothing canonical.
All conversations and messages recoverable from canonical files alone.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path

from julia_core.conversation_state.models import ConversationSession, ConversationMessage
from julia_core.conversation_state.repository import (
    ConversationNotFoundError,
    TurnConflictError,
    ConversationAdvancedError,
    InvalidTurnStateError,
)

SCHEMA_VERSION = 2


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class StorageV2ConversationRepository:
    """Hybrid: JSONL canonical + SQLite derived catalog."""

    def __init__(self, base_dir: str | Path):
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._cat_path = self._base / "catalog.sqlite"
        self._cat = self._open_catalog()
        self._init_schema()
        self._reconcile()

    # ── catalog ────────────────────────────────────────────────────────

    def _open_catalog(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._cat_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self):
        self._cat.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT '',
                state TEXT DEFAULT 'active',
                created_at TEXT,
                updated_at TEXT,
                message_count INTEGER DEFAULT 0,
                last_sequence INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS turn_index (
                conversation_id TEXT NOT NULL,
                turn_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                message_ids TEXT NOT NULL,
                PRIMARY KEY (conversation_id, turn_id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
        """)
        self._cat.commit()

    def _reconcile(self):
        """Startup: repair catalog from canonical files if needed."""
        for conv_dir in sorted(self._base.iterdir()):
            if not conv_dir.is_dir():
                continue
            conv_id = conv_dir.name
            meta_path = conv_dir / "meta.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text())
            self._cat.execute(
                "INSERT OR IGNORE INTO conversations(id, title, state, created_at, updated_at) VALUES(?,?,?,?,?)",
                (conv_id, meta.get("title", ""), meta.get("state", "active"),
                 meta.get("created_at", ""), meta.get("updated_at", "")),
            )
            # Reconcile turn index
            known_turns = set()
            for row in self._cat.execute(
                "SELECT turn_id FROM turn_index WHERE conversation_id=?", (conv_id,)
            ).fetchall():
                known_turns.add(row[0])
            for msg in self._iter_transcript(conv_id):
                tid = msg.get("turn_id", "")
                if tid and tid not in known_turns:
                    self._cat.execute(
                        "INSERT OR IGNORE INTO turn_index(conversation_id, turn_id, sequence, message_ids) VALUES(?,?,?,?)",
                        (conv_id, tid, msg.get("sequence", 0), msg.get("message_id", "")),
                    )
                    known_turns.add(tid)
        self._cat.commit()

    # ── canonical filesystem ───────────────────────────────────────────

    def _conv_dir(self, conv_id: str) -> Path:
        d = self._base / conv_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _segment_path(self, conv_id: str, seg: int = 1) -> Path:
        return self._conv_dir(conv_id) / f"transcript-{seg:06d}.jsonl"

    def _meta_path(self, conv_id: str) -> Path:
        return self._conv_dir(conv_id) / "meta.json"

    def _next_sequence(self, conv_id: str) -> int:
        row = self._cat.execute(
            "SELECT last_sequence FROM conversations WHERE id=?", (conv_id,)
        ).fetchone()
        return (row[0] + 1) if row else 1

    def _iter_transcript(self, conv_id: str):
        """Yield all canonical messages from transcript segments."""
        d = self._conv_dir(conv_id)
        for seg_path in sorted(d.glob("transcript-*.jsonl")):
            if not seg_path.exists():
                continue
            for line in seg_path.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

    def _write_canonical_message(self, conv_id: str, msg: dict):
        """Append one canonical line. Flush + fsync before returning."""
        seg_path = self._segment_path(conv_id)
        line = json.dumps(msg, ensure_ascii=False) + "\n"
        with open(seg_path, "a") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

    def _update_catalog_after_append(self, conv_id: str, msg: dict):
        """Update derived catalog AFTER canonical append."""
        seq = msg.get("sequence", 0)
        self._cat.execute(
            "UPDATE conversations SET message_count = message_count + 1, last_sequence = ?, updated_at = ? WHERE id = ?",
            (seq, msg.get("created_at", _now_iso()), conv_id),
        )
        tid = msg.get("turn_id", "")
        if tid:
            self._cat.execute(
                "INSERT OR IGNORE INTO turn_index(conversation_id, turn_id, sequence, message_ids) VALUES(?,?,?,?)",
                (conv_id, tid, seq, msg.get("message_id", "")),
            )
        self._cat.commit()

    # ── ConversationRepository Protocol ────────────────────────────────

    def get(self, session_id: str) -> ConversationSession | None:
        row = self._cat.execute(
            "SELECT id, title, state, created_at, updated_at, message_count FROM conversations WHERE id=?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        msgs = []
        for m in self._iter_transcript(session_id):
            msgs.append(ConversationMessage(
                message_id=m["message_id"], conversation_id=m["conversation_id"],
                turn_id=m["turn_id"], role=m["role"],
                modality=m.get("modality", "text"), content=m["content"],
                status=m.get("status", "completed"), created_at=m.get("created_at", ""),
            ))
        return ConversationSession(
            id=row[0], title=row[1],
            created_at=row[3] or "", updated_at=row[4] or "",
            message_count=row[5] or 0, messages=msgs,
        )

    def list_all(self) -> list[ConversationSession]:
        rows = self._cat.execute(
            "SELECT id FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        result = []
        for (conv_id,) in rows:
            s = self.get(conv_id)
            if s:
                result.append(s)
        return result

    def create_with_id(self, session_id: str, title: str = "New Conversation") -> ConversationSession:
        with self._lock:
            existing = self._cat.execute(
                "SELECT id FROM conversations WHERE id=?", (session_id,)
            ).fetchone()
            if existing:
                return self.get(session_id)

            now = _now_iso()
            meta = {
                "schema_version": SCHEMA_VERSION,
                "conversation_id": session_id, "title": title,
                "created_at": now, "updated_at": now, "state": "active",
            }
            self._meta_path(session_id).write_text(json.dumps(meta, indent=2))
            self._cat.execute(
                "INSERT INTO conversations(id, title, state, created_at, updated_at) VALUES(?,?,?,?,?)",
                (session_id, title, "active", now, now),
            )
            self._cat.commit()
            return self.get(session_id)

    def delete(self, session_id: str) -> bool:
        import shutil
        with self._lock:
            self._cat.execute("DELETE FROM turn_index WHERE conversation_id=?", (session_id,))
            self._cat.execute("DELETE FROM conversations WHERE id=?", (session_id,))
            self._cat.commit()
            conv_dir = self._conv_dir(session_id)
            if conv_dir.exists():
                shutil.rmtree(conv_dir)
            return True

    def update_title(self, session_id: str, title: str) -> ConversationSession | None:
        meta_path = self._meta_path(session_id)
        if not meta_path.exists():
            return None
        meta = json.loads(meta_path.read_text())
        meta["title"] = title
        meta["updated_at"] = _now_iso()
        meta_path.write_text(json.dumps(meta, indent=2))
        self._cat.execute(
            "UPDATE conversations SET title=?, updated_at=? WHERE id=?",
            (title, meta["updated_at"], session_id),
        )
        self._cat.commit()
        return self.get(session_id)

    def search(self, query: str) -> list[ConversationSession]:
        q = query.lower()
        results = []
        for s in self.list_all():
            if q in s.title.lower() or any(
                q in m.content.lower() for m in s.messages if m.role == "user"
            ):
                results.append(s)
        return results

    def add_message(
        self, session_id: str, role: str, content: str, *,
        turn_id: str = "", modality: str = "text", status: str = "completed",
    ) -> ConversationSession | None:
        with self._lock:
            if self._cat.execute("SELECT 1 FROM conversations WHERE id=?", (session_id,)).fetchone() is None:
                return None
            seq = self._next_sequence(session_id)
            msg = {
                "schema_version": SCHEMA_VERSION,
                "sequence": seq,
                "message_id": f"msg_{session_id}_{seq:06d}",
                "conversation_id": session_id,
                "turn_id": turn_id,
                "role": role,
                "modality": modality,
                "content": content,
                "status": status,
                "created_at": _now_iso(),
            }
            self._write_canonical_message(session_id, msg)
            self._update_catalog_after_append(session_id, msg)
            return self.get(session_id)

    def update_message_status(self, message_id: str, status: str) -> bool:
        # Messages are immutable in canonical JSONL.
        # Status updates are NOT supported in this backend.
        return False

    def find_turn(self, session_id: str, turn_id: str) -> list[ConversationMessage]:
        """Find all canonical messages for a turn_id.

        Scans canonical transcript files — does NOT depend on catalog.
        """
        results = []
        for m in self._iter_transcript(session_id):
            if m.get("turn_id") == turn_id:
                results.append(ConversationMessage(
                    message_id=m["message_id"], conversation_id=m["conversation_id"],
                    turn_id=m["turn_id"], role=m["role"],
                    modality=m.get("modality", "text"), content=m["content"],
                    status=m.get("status", "completed"), created_at=m.get("created_at", ""),
                ))
        return results

    def get_messages(
        self, session_id: str, *, before: str | None = None,
        after: str | None = None, limit: int | None = None,
    ) -> list[ConversationMessage]:
        msgs = []
        for m in self._iter_transcript(session_id):
            msgs.append(ConversationMessage(
                message_id=m["message_id"], conversation_id=m["conversation_id"],
                turn_id=m["turn_id"], role=m["role"],
                modality=m.get("modality", "text"), content=m["content"],
                status=m.get("status", "completed"), created_at=m.get("created_at", ""),
            ))
        if limit is not None:
            msgs = msgs[-limit:]
        return msgs

    def append_external_turns_atomic(
        self, session_id: str, turns: list[dict],
        base_last_message_id: str = "",
    ) -> tuple[list[str], list[str], str | None]:
        with self._lock:
            session = self.get(session_id)
            if session is None:
                raise ConversationNotFoundError(session_id)

            appended, skipped, last_id = [], [], None
            for turn in turns:
                tid = turn.get("turn_id", "")
                if not tid:
                    raise InvalidTurnStateError("turn_id required")
                existing = self.find_turn(session_id, tid)
                if existing:
                    skipped.append(tid)
                    continue
                # User message
                seq = self._next_sequence(session_id)
                user_msg = {
                    "schema_version": SCHEMA_VERSION, "sequence": seq,
                    "message_id": f"msg_{session_id}_{seq:06d}",
                    "conversation_id": session_id, "turn_id": tid,
                    "role": "user", "modality": turn.get("modality", "voice"),
                    "content": turn["user_content"], "status": "completed",
                    "created_at": turn.get("user_created_at", _now_iso()),
                }
                self._write_canonical_message(session_id, user_msg)
                self._update_catalog_after_append(session_id, user_msg)
                last_id = user_msg["message_id"]
                # Assistant message (if present)
                assistant_content = turn.get("assistant_content")
                if assistant_content is not None:
                    seq = self._next_sequence(session_id)
                    asst_msg = {
                        "schema_version": SCHEMA_VERSION, "sequence": seq,
                        "message_id": f"msg_{session_id}_{seq:06d}",
                        "conversation_id": session_id, "turn_id": tid,
                        "role": "assistant", "modality": turn.get("modality", "voice"),
                        "content": assistant_content,
                        "status": turn["assistant_status"],
                        "created_at": turn.get("assistant_created_at", _now_iso()),
                    }
                    self._write_canonical_message(session_id, asst_msg)
                    self._update_catalog_after_append(session_id, asst_msg)
                    last_id = asst_msg["message_id"]
                appended.append(tid)
            return appended, skipped, last_id

    def import_messages_atomic(
        self, session_id: str, messages: list[dict],
    ) -> tuple[int, int, str | None]:
        with self._lock:
            session = self.get(session_id)
            if session is None:
                raise ConversationNotFoundError(session_id)
            imported, skipped, last_id = 0, 0, None
            for m in messages:
                msg_id = m.get("message_id", "").strip()
                if not msg_id:
                    raise InvalidTurnStateError("message_id required")
                existing_ids = {x.message_id for x in self.get_messages(session_id)}
                if msg_id in existing_ids:
                    skipped += 1
                    continue
                seq = self._next_sequence(session_id)
                cm = {
                    "schema_version": SCHEMA_VERSION, "sequence": seq,
                    "message_id": msg_id, "conversation_id": session_id,
                    "turn_id": m.get("turn_id", ""), "role": m["role"],
                    "modality": m.get("modality", "text"),
                    "content": m["content"], "status": m.get("status", "completed"),
                    "created_at": m.get("created_at", _now_iso()),
                }
                self._write_canonical_message(session_id, cm)
                self._update_catalog_after_append(session_id, cm)
                last_id = msg_id
                imported += 1
            return imported, skipped, last_id

    def rebuild_catalog(self):
        """R2-S01: Rebuild entire catalog from canonical files."""
        self._cat.execute("DELETE FROM turn_index")
        self._cat.execute("DELETE FROM conversations")
        self._reconcile()

    def close(self):
        self._cat.close()

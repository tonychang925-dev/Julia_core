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
DEFAULT_SEGMENT_MAX_BYTES = 33_554_432
DEFAULT_SEGMENT_MAX_MESSAGES = 10_000


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class StorageV2ConversationRepository:
    """Hybrid: JSONL canonical + SQLite derived catalog."""

    def __init__(
        self,
        base_dir: str | Path,
        *,
        segment_max_bytes: int = DEFAULT_SEGMENT_MAX_BYTES,
        segment_max_messages: int = DEFAULT_SEGMENT_MAX_MESSAGES,
    ):
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._segment_max_bytes = segment_max_bytes
        self._segment_max_messages = segment_max_messages
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
        """Startup: repair derived catalog from canonical files.

        AT-09: catalog/index state is derived. Rebuild must recover counters and
        sequence watermarks from transcript-*.jsonl so future appends cannot
        reuse canonical message identity after catalog deletion.
        """
        for conv_dir in sorted(self._base.iterdir()):
            if not conv_dir.is_dir():
                continue
            conv_id = conv_dir.name
            meta_path = conv_dir / "meta.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text())
            messages = list(self._iter_transcript(conv_id))
            message_count = len(messages)
            last_sequence = max((int(msg.get("sequence", 0) or 0) for msg in messages), default=0)
            updated_at = meta.get("updated_at", "")

            self._cat.execute(
                """
                INSERT INTO conversations(id, title, state, created_at, updated_at, message_count, last_sequence)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    state=excluded.state,
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at,
                    message_count=excluded.message_count,
                    last_sequence=excluded.last_sequence
                """,
                (
                    conv_id,
                    meta.get("title", ""),
                    meta.get("state", "active"),
                    meta.get("created_at", ""),
                    updated_at,
                    message_count,
                    last_sequence,
                ),
            )

            # Reconcile turn index from canonical messages. Existing rows may be
            # stale after catalog deletion/corruption, so rebuild rows for this
            # conversation from transcript truth.
            self._cat.execute("DELETE FROM turn_index WHERE conversation_id=?", (conv_id,))
            turn_rows: dict[str, tuple[int, list[str]]] = {}
            for msg in messages:
                tid = msg.get("turn_id", "")
                if not tid:
                    continue
                sequence = int(msg.get("sequence", 0) or 0)
                message_id = msg.get("message_id", "")
                first_sequence, ids = turn_rows.get(tid, (sequence, []))
                turn_rows[tid] = (min(first_sequence, sequence), ids + [message_id])
            for tid, (sequence, ids) in turn_rows.items():
                self._cat.execute(
                    "INSERT OR REPLACE INTO turn_index(conversation_id, turn_id, sequence, message_ids) VALUES(?,?,?,?)",
                    (conv_id, tid, sequence, ",".join(ids)),
                )
        self._cat.commit()

    # ── canonical filesystem ───────────────────────────────────────────

    def _conv_dir(self, conv_id: str) -> Path:
        d = self._base / conv_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _segment_path(self, conv_id: str, seg: int = 1) -> Path:
        return self._conv_dir(conv_id) / f"transcript-{seg:06d}.jsonl"

    def _segment_number(self, path: Path) -> int:
        try:
            return int(path.stem.split("-")[-1])
        except (ValueError, IndexError):
            return 1

    def _latest_segment_number(self, conv_id: str) -> int:
        segments = sorted(self._conv_dir(conv_id).glob("transcript-*.jsonl"))
        if not segments:
            return 1
        return max(self._segment_number(p) for p in segments)

    def _segment_message_count(self, path: Path) -> int:
        if not path.exists():
            return 0
        return sum(1 for line in path.read_text().splitlines() if line.strip())

    def _select_segment_for_write(self, conv_id: str, encoded_line: str) -> Path:
        """AT-07: choose the physical segment for the next whole message.

        Rotation is a persistence concern only. Selection happens before writing
        a complete JSONL record; no canonical message is split across segments.
        """
        current_num = self._latest_segment_number(conv_id)
        current = self._segment_path(conv_id, current_num)
        current_count = self._segment_message_count(current)

        # Empty current segment, including oversized single record: write here.
        if current_count == 0:
            return current

        projected_count = current_count + 1
        current_bytes = current.stat().st_size if current.exists() else 0
        projected_bytes = current_bytes + len(encoded_line.encode("utf-8"))

        if (
            self._segment_max_messages > 0
            and projected_count > self._segment_max_messages
        ) or (
            self._segment_max_bytes > 0
            and projected_bytes > self._segment_max_bytes
        ):
            return self._segment_path(conv_id, current_num + 1)
        return current

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
        """Append one complete canonical line. Flush + fsync before returning."""
        line = json.dumps(msg, ensure_ascii=False) + "\n"
        seg_path = self._select_segment_for_write(conv_id, line)
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
        """Return canonical messages with cursor-aware, segment-transparent pagination.

        Cursor boundaries are exclusive message_id positions scoped to this
        conversation. Unknown/stale boundaries return an empty page rather than
        silently restarting from tail/head.
        """
        msgs = []
        for m in self._iter_transcript(session_id):
            msgs.append(ConversationMessage(
                message_id=m["message_id"], conversation_id=m["conversation_id"],
                turn_id=m["turn_id"], role=m["role"],
                modality=m.get("modality", "text"), content=m["content"],
                status=m.get("status", "completed"), created_at=m.get("created_at", ""),
            ))

        start, end = 0, len(msgs)
        ids = [m.message_id for m in msgs]

        if after is not None:
            if after not in ids:
                return []
            start = ids.index(after) + 1

        if before is not None:
            if before not in ids:
                return []
            end = ids.index(before)

        if start > end:
            return []

        window = msgs[start:end]
        if limit is not None:
            if limit <= 0:
                return []
            if before is not None and after is None:
                window = window[-limit:]
            elif before is None and after is None:
                window = window[-limit:]
            else:
                window = window[:limit]
        return window

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
                    if self._turn_equals(existing, turn):
                        skipped.append(tid)
                        continue
                    raise TurnConflictError(
                        f"Turn {tid}: content differs from persisted"
                    )
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

    @staticmethod
    def _turn_equals(existing_msgs: list[ConversationMessage], turn: dict) -> bool:
        """Compare an incoming external turn against existing canonical messages.

        Same turn_id is idempotent only when the canonical user content,
        modality, assistant content, and assistant status match the incoming
        turn. Different content is an identity conflict, not a retry.
        """
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
            return assistant_new_content is None
        if assistant_new_content is None:
            return False
        return (
            assistant_existing.content == assistant_new_content
            and assistant_existing.status == assistant_new_status
            and assistant_existing.modality == turn.get("modality", "voice")
        )

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

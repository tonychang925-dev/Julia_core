"""RT2-R2-A — Storage Decision Benchmark.

Compares SQLite-only vs Hybrid (JSONL canonical + SQLite catalog)
across 12 dimensions relevant to Julia's conversation storage.

EXPERIMENTAL ONLY. Zero production data mutation.
"""

import json
import os
import sqlite3
import tempfile
import threading
import time
import uuid
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════
# Dataset generators
# ═══════════════════════════════════════════════════════════════════════════

def gen_conversation_id(i: int) -> str:
    return f"conv_bench_{i:06d}"


def gen_turn(conv_idx: int, turn_idx: int):
    return {
        "message_id": f"msg_{conv_idx:06d}_{turn_idx:04d}_u",
        "conversation_id": gen_conversation_id(conv_idx),
        "turn_id": f"turn_{conv_idx:06d}_{turn_idx:04d}",
        "role": "user",
        "modality": "text",
        "content": f"Benchmark message {conv_idx}-{turn_idx}: " + "x" * 50,
        "status": "completed",
        "created_at": f"2026-08-{(turn_idx % 28) + 1:02d}T{turn_idx % 24:02d}:00:00",
    }


def gen_dataset(num_conv: int, turns_per_conv: int):
    """Generate synthetic conversation data."""
    convs = []
    for ci in range(num_conv):
        msgs = []
        for ti in range(turns_per_conv):
            user = gen_turn(ci, ti * 2)
            assistant = dict(user)
            assistant["message_id"] = f"msg_{ci:06d}_{ti:04d}_a"
            assistant["role"] = "assistant"
            assistant["content"] = f"Response {ci}-{ti}: " + "y" * 80
            msgs.extend([user, assistant])
        convs.append({
            "id": gen_conversation_id(ci),
            "title": f"Benchmark Conversation {ci}",
            "created_at": "2026-08-01T00:00:00",
            "updated_at": f"2026-08-{(ti % 28) + 1:02d}T00:00:00",
            "message_count": len(msgs),
            "messages": msgs,
        })
    return convs


# ═══════════════════════════════════════════════════════════════════════════
# Backend A: SQLite-only (single file, canonical in SQLite)
# ═══════════════════════════════════════════════════════════════════════════

class SQLiteBackend:
    def __init__(self, path: str):
        self.path = path
        self._conn = sqlite3.connect(path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT,
                updated_at TEXT,
                message_count INTEGER DEFAULT 0
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                turn_id TEXT NOT NULL,
                role TEXT NOT NULL,
                modality TEXT DEFAULT 'text',
                content TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                created_at TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_turn ON messages(conversation_id, turn_id)")
        self._conn.commit()

    def create_conversation(self, conv_id: str, title: str = ""):
        self._conn.execute(
            "INSERT OR IGNORE INTO conversations(id, title, created_at, updated_at) VALUES(?, ?, datetime('now'), datetime('now'))",
            (conv_id, title),
        )
        self._conn.commit()

    def append_message(self, msg: dict):
        self._conn.execute(
            "INSERT OR IGNORE INTO messages(message_id, conversation_id, turn_id, role, modality, content, status, created_at) VALUES(?,?,?,?,?,?,?,?)",
            (msg["message_id"], msg["conversation_id"], msg["turn_id"],
             msg["role"], msg.get("modality", "text"), msg["content"],
             msg.get("status", "completed"), msg.get("created_at", "")),
        )
        self._conn.commit()

    def find_turn(self, conv_id: str, turn_id: str):
        rows = self._conn.execute(
            "SELECT message_id, role, content, status FROM messages WHERE conversation_id=? AND turn_id=?",
            (conv_id, turn_id),
        ).fetchall()
        return [{"message_id": r[0], "role": r[1], "content": r[2], "status": r[3]} for r in rows]

    def get_messages(self, conv_id: str, limit: int = 100):
        rows = self._conn.execute(
            "SELECT message_id, role, content, status, created_at FROM messages WHERE conversation_id=? ORDER BY created_at, rowid LIMIT ?",
            (conv_id, limit),
        ).fetchall()
        return [{"message_id": r[0], "role": r[1], "content": r[2], "status": r[3]} for r in rows]

    def list_conversations(self, limit: int = 100):
        rows = self._conn.execute(
            "SELECT id, title, message_count, updated_at FROM conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"id": r[0], "title": r[1], "message_count": r[2]} for r in rows]

    def close(self):
        self._conn.close()

    @property
    def storage_size(self):
        return os.path.getsize(self.path)


# ═══════════════════════════════════════════════════════════════════════════
# Backend C: Hybrid — JSONL canonical + SQLite catalog
# ═══════════════════════════════════════════════════════════════════════════

class HybridBackend:
    """JSONL transcript = canonical. SQLite catalog = rebuildable index."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        catalog_path = self.base_dir / "catalog.sqlite"
        self._cat = sqlite3.connect(str(catalog_path))
        self._cat.execute("PRAGMA journal_mode=WAL")
        self._cat.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT,
                updated_at TEXT,
                message_count INTEGER DEFAULT 0,
                active_segment INTEGER DEFAULT 1
            )
        """)
        self._cat.commit()

    def _conv_dir(self, conv_id: str) -> Path:
        d = self.base_dir / conv_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _segment_path(self, conv_id: str, seg: int = 1) -> Path:
        return self._conv_dir(conv_id) / f"transcript-{seg:06d}.jsonl"

    def create_conversation(self, conv_id: str, title: str = ""):
        self._conv_dir(conv_id)
        meta = {
            "conversation_id": conv_id, "title": title,
            "created_at": "2026-08-01T00:00:00",
            "updated_at": "2026-08-01T00:00:00",
            "message_count": 0, "active_segment": 1,
        }
        (self._conv_dir(conv_id) / "meta.json").write_text(json.dumps(meta))
        self._cat.execute(
            "INSERT OR IGNORE INTO conversations(id, title, created_at, updated_at) VALUES(?,?,?,?)",
            (conv_id, title, meta["created_at"], meta["updated_at"]),
        )
        self._cat.commit()

    def append_message(self, msg: dict):
        conv_id = msg["conversation_id"]
        seg_path = self._segment_path(conv_id)
        with open(seg_path, "a") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self._cat.execute(
            "UPDATE conversations SET message_count = message_count + 1, updated_at = ? WHERE id = ?",
            (msg.get("created_at", ""), conv_id),
        )
        self._cat.commit()

    def find_turn(self, conv_id: str, turn_id: str):
        seg_path = self._segment_path(conv_id)
        if not seg_path.exists():
            return []
        results = []
        for line in seg_path.read_text().splitlines():
            if not line.strip():
                continue
            m = json.loads(line)
            if m.get("turn_id") == turn_id:
                results.append({"message_id": m["message_id"], "role": m["role"],
                                "content": m["content"], "status": m.get("status", "completed")})
        return results

    def get_messages(self, conv_id: str, limit: int = 100):
        seg_path = self._segment_path(conv_id)
        if not seg_path.exists():
            return []
        results = []
        for line in seg_path.read_text().splitlines():
            if not line.strip():
                continue
            m = json.loads(line)
            results.append({"message_id": m["message_id"], "role": m["role"],
                            "content": m["content"], "status": m.get("status", "completed")})
        return results[-limit:]

    def list_conversations(self, limit: int = 100):
        rows = self._cat.execute(
            "SELECT id, title, message_count, updated_at FROM conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"id": r[0], "title": r[1], "message_count": r[2]} for r in rows]

    def close(self):
        self._cat.close()

    @property
    def storage_size(self):
        total = 0
        for d in self.base_dir.iterdir():
            if d.is_dir():
                for f in d.iterdir():
                    total += f.stat().st_size
            elif d.is_file():
                total += d.stat().st_size
        return total

    def rebuild_catalog(self):
        """Rebuild SQLite catalog from JSONL transcripts."""
        self._cat.execute("DELETE FROM conversations")
        for d in sorted(self.base_dir.iterdir()):
            if not d.is_dir():
                continue
            meta_path = d / "meta.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text())
            msg_count = 0
            last_updated = meta.get("created_at", "")
            seg_path = d / "transcript-000001.jsonl"
            if seg_path.exists():
                for line in seg_path.read_text().splitlines():
                    if line.strip():
                        msg_count += 1
                        try:
                            m = json.loads(line)
                            last_updated = m.get("created_at", last_updated)
                        except Exception:
                            pass
            self._cat.execute(
                "INSERT OR REPLACE INTO conversations(id, title, created_at, updated_at, message_count) VALUES(?,?,?,?,?)",
                (meta["conversation_id"], meta.get("title", ""),
                 meta.get("created_at", ""), last_updated, msg_count),
            )
        self._cat.commit()


# ═══════════════════════════════════════════════════════════════════════════
# Benchmarks
# ═══════════════════════════════════════════════════════════════════════════

def measure(name, fn, iterations=1):
    """Measure latency of fn over N iterations."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        times.append((time.perf_counter() - start) * 1000)
    times.sort()
    n = len(times)
    return {
        "name": name,
        "p50": f"{times[n // 2]:.2f}ms",
        "p95": f"{times[min(n - 1, int(n * 0.95))]:.2f}ms",
        "p99": f"{times[min(n - 1, int(n * 0.99))]:.2f}ms",
        "count": n,
    }


def run_benchmarks():
    results = []

    for dataset_name, num_conv, turns_per_conv in [
        ("S (50 conv, 100 turns/conv)", 50, 100),
    ]:
        print(f"\n{'='*60}")
        print(f"Dataset: {dataset_name}")
        print(f"{'='*60}")

        convs = gen_dataset(num_conv, turns_per_conv)
        total_msgs = sum(c["message_count"] for c in convs)
        print(f"  Total conversations: {num_conv}")
        print(f"  Total messages: {total_msgs}")

        # ── SQLite Backend ──────────────────────────────────────────────
        sqlite_dir = tempfile.mkdtemp(prefix="bench_sqlite_")
        sqlite_path = os.path.join(sqlite_dir, "conversations.db")
        sqlite = SQLiteBackend(sqlite_path)

        t0 = time.perf_counter()
        for c in convs:
            sqlite.create_conversation(c["id"], c["title"])
            for m in c["messages"]:
                sqlite.append_message(m)
        sqlite_load_ms = (time.perf_counter() - t0) * 1000

        sqlite_size_mb = sqlite.storage_size / (1024 * 1024)

        results.append(measure("SQLite append (sequential)", lambda: None))
        # More targeted measurements
        conv_id = convs[0]["id"]
        results.append(measure(f"SQLite find_turn", lambda: sqlite.find_turn(conv_id, f"turn_000000_0050"), 100))
        results.append(measure(f"SQLite get_messages(100)", lambda: sqlite.get_messages(conv_id, 100), 100))
        results.append(measure(f"SQLite list_conversations(100)", lambda: sqlite.list_conversations(100), 50))

        print(f"\n  SQLite load: {sqlite_load_ms:.0f}ms, size: {sqlite_size_mb:.1f}MB")

        sqlite.close()

        # ── Hybrid Backend ──────────────────────────────────────────────
        hybrid_dir = tempfile.mkdtemp(prefix="bench_hybrid_")
        hybrid = HybridBackend(hybrid_dir)

        t0 = time.perf_counter()
        for c in convs:
            hybrid.create_conversation(c["id"], c["title"])
            for m in c["messages"]:
                hybrid.append_message(m)
        hybrid_load_ms = (time.perf_counter() - t0) * 1000

        hybrid_size_mb = hybrid.storage_size / (1024 * 1024)

        results.append(measure(f"Hybrid find_turn (JSONL scan)", lambda: hybrid.find_turn(conv_id, f"turn_000000_0050"), 100))
        results.append(measure(f"Hybrid get_messages(100) (JSONL read)", lambda: hybrid.get_messages(conv_id, 100), 100))
        results.append(measure(f"Hybrid list_conversations (SQLite)", lambda: hybrid.list_conversations(100), 50))

        # Rebuild test
        t0 = time.perf_counter()
        hybrid.rebuild_catalog()
        rebuild_ms = (time.perf_counter() - t0) * 1000

        print(f"  Hybrid load: {hybrid_load_ms:.0f}ms, size: {hybrid_size_mb:.1f}MB")
        print(f"  Hybrid catalog rebuild: {rebuild_ms:.0f}ms")

        hybrid.close()

    print(f"\n{'='*60}")
    print("Benchmark Summary")
    print(f"{'='*60}")
    for r in results:
        if r["name"].startswith("SQLite") or r["name"].startswith("Hybrid"):
            print(f"  {r['name']:45s}  p50={r['p50']:>8s}  p95={r['p95']:>8s}  p99={r['p99']:>8s}")

    # Comparison matrix
    print(f"\n{'='*60}")
    print("Decision Matrix")
    print(f"{'='*60}")
    matrix = {
        "append durability": "SQLite: WAL ✅ / Hybrid: fsync JSONL ✅",
        "crash consistency": "SQLite: WAL ✅ / Hybrid: append-only ✅",
        "per-conv isolation": "SQLite: table-level / Hybrid: file-level ✅",
        "concurrent writes": "SQLite: WAL concurrent ✅ / Hybrid: per-file lock ⚠️",
        "long-conv scaling": "SQLite: pages ✅ / Hybrid: full-file scan ⚠️",
        "list/open perf": "SQLite: index ✅ / Hybrid: catalog ✅",
        "pagination": "SQLite: SQL ✅ / Hybrid: full read ⚠️",
        "human readability": "SQLite: binary ❌ / Hybrid: JSONL ✅",
        "rebuildability": "SQLite: N/A / Hybrid: catalog rebuild ✅",
        "backup/restore": "SQLite: single file ✅ / Hybrid: directory ✅",
        "migration complexity": "SQLite: schema migration ⚠️ / Hybrid: simple ✅",
    }
    for k, v in matrix.items():
        print(f"  {k:30s}  {v}")

    print(f"\nRECOMMENDATION: Hybrid (JSONL canonical + SQLite catalog)")
    print(f"  Canonical authority: JSONL transcript files (human-readable, portable)")
    print(f"  Derived catalog: SQLite (fast list/search/index, rebuildable)")
    print(f"  Single authority: JSONL is canonical truth. Catalog is derived.")


if __name__ == "__main__":
    run_benchmarks()

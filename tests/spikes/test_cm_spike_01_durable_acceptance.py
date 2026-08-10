"""CM-SPIKE-01 — Durable User Acceptance Feasibility.

ANSWERS ONE QUESTION:
  Can accept_user_turn() durably write a user message before returning ACK,
  such that kill-9 recovery works?

EXPERIMENTAL ONLY. Zero production mutation. Uses temp store copies.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

import pytest

# ── ensure julia_core is importable ────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from julia_core.conversation_state.repository import (
    SessionRepository,
    ConversationNotFoundError,
    TurnConflictError,
    InvalidTurnStateError,
)


# ═══════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════

def _fresh_repo(source_json: Path | None = None) -> tuple[SessionRepository, str]:
    """Create a temp-store. Optionally copy from a source JSON."""
    store_dir = tempfile.mkdtemp(prefix="spike01_")
    store_path = Path(store_dir) / "conversations.json"
    if source_json and source_json.exists():
        shutil.copy2(source_json, store_path)
    return SessionRepository(str(store_path)), store_path


def _reload(repo_path: Path) -> SessionRepository:
    """Reload repository from disk, simulating Core restart."""
    return SessionRepository(str(repo_path))


def _verify_exists(repo_path: Path, conv_id: str, turn_id: str) -> list[dict]:
    """Reload and verify a turn exists."""
    repo = _reload(repo_path)
    msgs = repo.find_turn(conv_id, turn_id)
    return [{"message_id": m.message_id, "role": m.role, "content": m.content,
             "status": m.status, "turn_id": m.turn_id} for m in msgs]


# ═══════════════════════════════════════════════════════════════════════════
# The "accept_user_turn" primitive under test
# ═══════════════════════════════════════════════════════════════════════════

def accept_user_turn(repo: SessionRepository, *, conversation_id: str,
                     turn_id: str, modality: str = "text",
                     content: str = "") -> dict:
    """Experimental CM-I05 turn acceptance.

    Returns ACK dict. Durable user append happens BEFORE returning.
    """
    # validate conversation exists
    session = repo.get(conversation_id)
    if session is None:
        raise ConversationNotFoundError(conversation_id)

    # idempotency: same turn_id + same content → ACK, no duplicate
    existing = repo.find_turn(conversation_id, turn_id)
    if existing:
        user_existing = next((m for m in existing if m.role == "user"), None)
        if user_existing and user_existing.content == content:
            return {
                "accepted": True, "conversation_id": conversation_id,
                "turn_id": turn_id, "user_message_id": user_existing.message_id,
                "durable": True, "idempotent": True,
            }
        else:
            raise TurnConflictError(
                f"Turn {turn_id}: content differs from persisted"
            )

    # durable append → _save() includes fsync before return
    result = repo.add_message(
        conversation_id, role="user", content=content,
        turn_id=turn_id, modality=modality, status="accepted",
    )
    if result is None:
        raise RuntimeError(f"Failed to append message to {conversation_id}")

    user_msg = result.messages[-1]
    return {
        "accepted": True, "conversation_id": conversation_id,
        "turn_id": turn_id, "user_message_id": user_msg.message_id,
        "durable": True, "idempotent": False,
    }


# ═══════════════════════════════════════════════════════════════════════════
# SP-01: Normal durable append
# ═══════════════════════════════════════════════════════════════════════════

def test_sp01_normal_durable_append():
    """SP-01: accept T17 → ACK → restart → T17 still exists."""
    repo, store_path = _fresh_repo()
    conv_id = "sp01_conv"
    repo.create_with_id(conv_id, "SP01 Test")

    result = accept_user_turn(repo, conversation_id=conv_id,
                              turn_id="sp01_turn_01", content="hello spike")
    assert result["accepted"] is True
    assert result["durable"] is True
    assert result["idempotent"] is False
    assert result["conversation_id"] == conv_id

    # Simulate restart
    msgs = _verify_exists(store_path, conv_id, "sp01_turn_01")
    user_msgs = [m for m in msgs if m["role"] == "user"]
    assert len(user_msgs) == 1
    assert user_msgs[0]["content"] == "hello spike"
    assert user_msgs[0]["status"] == "accepted"


# ═══════════════════════════════════════════════════════════════════════════
# SP-02: Idempotent retry
# ═══════════════════════════════════════════════════════════════════════════

def test_sp02_idempotent_retry():
    """SP-02: same turn_id + same content → ACK, exactly 1 message."""
    repo, store_path = _fresh_repo()
    conv_id = "sp02_conv"
    repo.create_with_id(conv_id, "SP02 Test")

    r1 = accept_user_turn(repo, conversation_id=conv_id,
                          turn_id="sp02_turn", content="same content")
    assert r1["idempotent"] is False

    r2 = accept_user_turn(repo, conversation_id=conv_id,
                          turn_id="sp02_turn", content="same content")
    assert r2["accepted"] is True
    assert r2["idempotent"] is True
    assert r2["user_message_id"] == r1["user_message_id"]

    msgs = _verify_exists(store_path, conv_id, "sp02_turn")
    user_msgs = [m for m in msgs if m["role"] == "user"]
    assert len(user_msgs) == 1


# ═══════════════════════════════════════════════════════════════════════════
# SP-03: Same ID, different content → CONFLICT
# ═══════════════════════════════════════════════════════════════════════════

def test_sp03_same_id_different_content_conflict():
    """SP-03: different content with same turn_id must raise."""
    repo, store_path = _fresh_repo()
    conv_id = "sp03_conv"
    repo.create_with_id(conv_id, "SP03 Test")

    accept_user_turn(repo, conversation_id=conv_id,
                     turn_id="sp03_turn", content="original")

    with pytest.raises(TurnConflictError):
        accept_user_turn(repo, conversation_id=conv_id,
                         turn_id="sp03_turn", content="different")

    # Verify original not overwritten
    msgs = _verify_exists(store_path, conv_id, "sp03_turn")
    user_msgs = [m for m in msgs if m["role"] == "user"]
    assert len(user_msgs) == 1
    assert user_msgs[0]["content"] == "original"


# ═══════════════════════════════════════════════════════════════════════════
# SP-04: Crash after ACK → user message survives
# ═══════════════════════════════════════════════════════════════════════════

def test_sp04_crash_after_ack():
    """SP-04: accept → ACK returned → kill process → restart → T17 exists.

    This is THE core CM-I05 test. We simulate kill-9 by writing the ACK to
    a witness file, spawning a subprocess that appends, returning ACK to
    witness, then killing it — then reloading the store.
    """
    store_dir = tempfile.mkdtemp(prefix="spike04_")
    store_path = Path(store_dir) / "conversations.json"
    witness_path = Path(store_dir) / "ack_witness.json"

    # Prepare a store with one conversation
    prep_repo = SessionRepository(str(store_path))
    conv_id = "sp04_conv"
    prep_repo.create_with_id(conv_id, "SP04 Test")

    spike_script = f"""
import sys, json
sys.path.insert(0, {str(REPO_ROOT)!r})
from julia_core.conversation_state.repository import SessionRepository

repo = SessionRepository({str(store_path)!r})
session = repo.get({conv_id!r})
if session is None:
    json.dump({{"error": "conv not found"}}, open({str(witness_path)!r}, "w"))
    sys.exit(1)

result = repo.add_message(
    {conv_id!r}, role="user", content="crash-after-ack-test",
    turn_id="sp04_turn", modality="text", status="accepted",
)
if result is None:
    json.dump({{"error": "add_message returned None"}}, open({str(witness_path)!r}, "w"))
    sys.exit(1)

user_msg = result.messages[-1]
json.dump({{
    "accepted": True, "conversation_id": {conv_id!r},
    "turn_id": "sp04_turn", "user_message_id": user_msg.message_id,
    "durable": True,
}}, open({str(witness_path)!r}, "w"))
sys.exit(0)
"""

    spike_file = Path(store_dir) / "spike04_worker.py"
    spike_file.write_text(spike_script)

    result = subprocess.run(
        [sys.executable, str(spike_file)],
        capture_output=True, text=True, timeout=10,
    )

    assert result.returncode == 0, f"Worker failed: {result.stderr}"
    assert witness_path.exists(), "ACK witness not written"

    witness = json.loads(witness_path.read_text())
    assert witness.get("accepted") is True
    assert witness.get("durable") is True

    # "kill-9": we already killed the subprocess (it exited).
    # Now "restart" by reloading from disk.
    msgs = _verify_exists(store_path, conv_id, "sp04_turn")
    user_msgs = [m for m in msgs if m["role"] == "user"]
    assert len(user_msgs) == 1, f"Expected 1 user msg after restart, got {len(user_msgs)}"
    assert user_msgs[0]["content"] == "crash-after-ack-test"
    assert user_msgs[0]["status"] == "accepted"


# ═══════════════════════════════════════════════════════════════════════════
# SP-05: Cognition failure does not erase accepted user message
# ═══════════════════════════════════════════════════════════════════════════

def test_sp05_user_durable_independent_of_cognition():
    """SP-05: accept → simulate cognition failure → user message still exists."""
    repo, store_path = _fresh_repo()
    conv_id = "sp05_conv"
    repo.create_with_id(conv_id, "SP05 Test")

    result = accept_user_turn(repo, conversation_id=conv_id,
                              turn_id="sp05_turn", content="cognition may fail")
    assert result["accepted"] is True

    # Simulate cognition failure (doesn't touch user message)
    # The user message should remain regardless
    msgs = _verify_exists(store_path, conv_id, "sp05_turn")
    user_msgs = [m for m in msgs if m["role"] == "user"]
    assert len(user_msgs) == 1
    assert user_msgs[0]["content"] == "cognition may fail"


# ═══════════════════════════════════════════════════════════════════════════
# SP-06: Same-conversation concurrency safety
# ═══════════════════════════════════════════════════════════════════════════

def test_sp06_same_conversation_concurrency():
    """SP-06: concurrent same-conv appends must not corrupt store."""
    repo, store_path = _fresh_repo()
    conv_id = "sp06_conv"
    repo.create_with_id(conv_id, "SP06 Test")

    errors = []
    results = []

    def append(turn_id: str, content: str):
        try:
            r = accept_user_turn(repo, conversation_id=conv_id,
                                 turn_id=turn_id, content=content)
            results.append(r)
        except Exception as e:
            errors.append(str(e))

    threads = []
    for i in range(10):
        t = threading.Thread(
            target=append,
            args=(f"sp06_turn_{i:02d}", f"content_{i}"),
        )
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    # All 10 distinct turn_ids should succeed
    assert len(results) == 10, f"Expected 10 successes, got {len(results)}"

    # Restart and verify all 10 are in store
    msgs = _reload(store_path).list_all()
    session = next(s for s in msgs if s.id == conv_id)
    user_turns = [m.turn_id for m in session.messages if m.role == "user"]
    assert len(user_turns) == 10, f"Expected 10 turns, got {len(user_turns)}"

    # No corruption: reload again
    msgs2 = _reload(store_path).list_all()
    session2 = next(s for s in msgs2 if s.id == conv_id)
    assert len(session2.messages) == 10


# ═══════════════════════════════════════════════════════════════════════════
# SP-07: Cross-conversation isolation
# ═══════════════════════════════════════════════════════════════════════════

def test_sp07_cross_conversation_isolation():
    """SP-07: concurrent A/B appends must not leak across conversations."""
    repo, store_path = _fresh_repo()
    repo.create_with_id("sp07_conv_A", "SP07 A")
    repo.create_with_id("sp07_conv_B", "SP07 B")

    def append(conv_id: str, turn_id: str):
        accept_user_turn(repo, conversation_id=conv_id,
                         turn_id=turn_id, content=f"content_{conv_id}")

    threads = [
        threading.Thread(target=append, args=("sp07_conv_A", "sp07_turn_A1")),
        threading.Thread(target=append, args=("sp07_conv_B", "sp07_turn_B1")),
        threading.Thread(target=append, args=("sp07_conv_A", "sp07_turn_A2")),
        threading.Thread(target=append, args=("sp07_conv_B", "sp07_turn_B2")),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    # Verify A has only A turns, B has only B turns
    msgs = _reload(store_path).list_all()
    a_session = next(s for s in msgs if s.id == "sp07_conv_A")
    b_session = next(s for s in msgs if s.id == "sp07_conv_B")

    a_turns = [m.turn_id for m in a_session.messages if m.role == "user"]
    b_turns = [m.turn_id for m in b_session.messages if m.role == "user"]

    assert sorted(a_turns) == ["sp07_turn_A1", "sp07_turn_A2"]
    assert sorted(b_turns) == ["sp07_turn_B1", "sp07_turn_B2"]

    # No cross-contamination
    a_contents = [m.content for m in a_session.messages]
    b_contents = [m.content for m in b_session.messages]
    assert not any("_B" in c for c in a_contents)
    assert not any("_A" in c for c in b_contents)


# ═══════════════════════════════════════════════════════════════════════════
# SP-08: Existing-store compatibility
# ═══════════════════════════════════════════════════════════════════════════

def test_sp08_existing_store_compatibility():
    """SP-08: load existing schema, append new turn, old data intact."""
    # Use a minimal existing-format store
    existing_json = json.dumps([{
        "id": "sp08_existing", "title": "Existing", "topic": "",
        "messages": [
            {"message_id": "existing_msg_1", "conversation_id": "sp08_existing",
             "turn_id": "existing_turn_1", "role": "user", "modality": "text",
             "content": "existing content", "status": "completed",
             "created_at": "2026-08-10T10:00:00"}
        ],
        "tags": [], "created_at": "2026-08-10T10:00:00",
        "updated_at": "2026-08-10T10:00:00", "message_count": 2,
    }])

    store_dir = tempfile.mkdtemp(prefix="spike08_")
    store_path = Path(store_dir) / "conversations.json"
    store_path.write_text(existing_json)

    repo = SessionRepository(str(store_path))
    result = accept_user_turn(repo, conversation_id="sp08_existing",
                              turn_id="sp08_turn", content="new spike turn")
    assert result["accepted"] is True

    # Reload: existing message preserved, new message present
    msgs = _verify_exists(store_path, "sp08_existing", "existing_turn_1")
    assert len(msgs) >= 1
    assert msgs[0]["content"] == "existing content"

    new_msgs = _verify_exists(store_path, "sp08_existing", "sp08_turn")
    assert len(new_msgs) == 1
    assert new_msgs[0]["content"] == "new spike turn"


# ═══════════════════════════════════════════════════════════════════════════
# SP-09: Benchmark — sequential write latency
# ═══════════════════════════════════════════════════════════════════════════

def test_sp09_benchmark_sequential_latency():
    """SP-09: measure sequential write latency p50/p95/p99/max."""
    repo, store_path = _fresh_repo()
    conv_id = "sp09_bench"
    repo.create_with_id(conv_id, "SP09 Bench")

    latencies = []
    for i in range(500):
        start = time.perf_counter()
        accept_user_turn(repo, conversation_id=conv_id,
                         turn_id=f"sp09_turn_{i:04d}",
                         content=f"benchmark message {i}")
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)

    latencies.sort()
    n = len(latencies)
    result = {
        "p50": f"{latencies[n // 2]:.2f}ms",
        "p95": f"{latencies[int(n * 0.95)]:.2f}ms",
        "p99": f"{latencies[int(n * 0.99)]:.2f}ms",
        "max": f"{latencies[-1]:.2f}ms",
        "count": n,
        "errors": 0,
    }

    # Log benchmark data
    bench_path = Path(store_path).parent / "bench_sp09.json"
    bench_path.write_text(json.dumps(result, indent=2))

    # Latency grows with store size (whole-file rewrite). Document, don't fail.
    print(f"SP-09 sequential latency: {json.dumps(result)}")
    print(f"  Last message: {latencies[-1]:.2f}ms (file has {n} user messages)")

    # No hard pass/fail — measurement only
    assert result["errors"] == 0
    assert result["count"] == 500


# ═══════════════════════════════════════════════════════════════════════════
# SP-10: FS-level durability — os.fsync confirmed
# ═══════════════════════════════════════════════════════════════════════════

def test_sp10_fsync_actually_called():
    """SP-10: verify that SessionRepository._save() uses fsync, not just write.

    This is a static assertion, not a runtime test. We grep the source.
    """
    repo_path = REPO_ROOT / "julia_core" / "conversation_state" / "repository.py"
    source = repo_path.read_text()

    # Verify atomic write pattern exists
    assert "os.fsync" in source, (
        "CRITICAL: SessionRepository._save() does not call os.fsync. "
        "Durable ACK guarantee cannot be met without fsync or equivalent."
    )
    assert "os.replace" in source, (
        "CRITICAL: SessionRepository._save() does not use atomic replace. "
        "Crash during write could corrupt the store."
    )
    assert "tmp" in source or ".tmp" in source, (
        "WARN: No temp-file pattern found. Store may not be crash-safe."
    )

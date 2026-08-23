"""Wave5 AT-09 Minimal Remediation — derived catalog rebuild.

These tests verify the minimal StorageV2 fix for the P0 gap found in AT-09
Audit. They are remediation evidence, not final R1/IA freeze evidence.
"""

from __future__ import annotations

import os
from pathlib import Path

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from conversation_management import ConversationManagementService
from julia_core.runtime.conversation_runtime import ConversationRuntime


class _FakeIdempotencyPort:
    def __init__(self):
        self._reserved: dict[str, str] = {}

    def get_or_reserve(self, key: str, candidate: str) -> str:
        return self._reserved.setdefault(key, candidate)


def _delete_catalog_files(root: Path) -> list[str]:
    deleted = []
    for path in list(root.glob("catalog.sqlite*")):
        deleted.append(path.name)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    return sorted(deleted)


def _append(repo: StorageV2ConversationRepository, cid: str, count: int, *, prefix: str):
    expected = []
    for idx in range(count):
        content = f"{prefix}_{idx:03d}"
        expected.append(content)
        repo.add_message(cid, "user", content, turn_id=f"{prefix.lower()}_turn_{idx:03d}")
    return expected


def test_at09_rem_rebuild_restores_message_count_and_last_sequence(tmp_path):
    """AT09-REM-001: rebuild counters come from canonical transcript."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=10)
    cid = "at09_rem_count"
    try:
        repo.create_with_id(cid)
        _append(repo, cid, 23, prefix="COUNT")
        repo.close()

        deleted = _delete_catalog_files(tmp_path)
        repo2 = StorageV2ConversationRepository(tmp_path, segment_max_messages=10)
        rebuilt = repo2.get(cid)

        assert "catalog.sqlite" in deleted
        assert rebuilt is not None
        assert rebuilt.message_count == 23
        assert repo2._cat.execute(
            "SELECT last_sequence FROM conversations WHERE id=?", (cid,)
        ).fetchone()[0] == 23
    finally:
        try:
            repo2.close()  # type: ignore[name-defined]
        except Exception:
            pass


def test_at09_rem_post_rebuild_append_uses_next_canonical_sequence(tmp_path):
    """AT09-REM-002: append after rebuild does not reuse message_id."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=10)
    cid = "at09_rem_append"
    try:
        repo.create_with_id(cid)
        _append(repo, cid, 5, prefix="BEFORE")
        repo.close()

        _delete_catalog_files(tmp_path)
        repo2 = StorageV2ConversationRepository(tmp_path, segment_max_messages=10)
        repo2.add_message(cid, "user", "AFTER_REBUILD", turn_id="after_turn")
        messages = repo2.get_messages(cid)
        ids = [m.message_id for m in messages]

        assert ids[-1] == f"msg_{cid}_000006"
        assert len(ids) == len(set(ids))
        assert [m.content for m in messages][-1] == "AFTER_REBUILD"
        assert repo2.get(cid).message_count == 6
    finally:
        try:
            repo2.close()  # type: ignore[name-defined]
        except Exception:
            pass


def test_at09_rem_turn_index_rebuilt_from_canonical_transcript(tmp_path):
    """AT09-REM-003: find_turn works after derived catalog deletion/rebuild."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=4)
    cid = "at09_rem_turn"
    try:
        repo.create_with_id(cid)
        repo.add_message(cid, "user", "turn user", turn_id="turn_shared")
        repo.add_message(cid, "assistant", "turn assistant", turn_id="turn_shared")
        repo.close()

        _delete_catalog_files(tmp_path)
        repo2 = StorageV2ConversationRepository(tmp_path, segment_max_messages=4)
        turn = repo2.find_turn(cid, "turn_shared")

        assert [m.content for m in turn] == ["turn user", "turn assistant"]
        assert repo2._cat.execute(
            "SELECT message_ids FROM turn_index WHERE conversation_id=? AND turn_id=?",
            (cid, "turn_shared"),
        ).fetchone()[0] == f"msg_{cid}_000001,msg_{cid}_000002"
    finally:
        try:
            repo2.close()  # type: ignore[name-defined]
        except Exception:
            pass


def test_at09_rem_management_handle_count_recovers_after_catalog_deletion(tmp_path):
    """AT09-REM-004: governed read surface sees rebuilt message_count."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=8)
    rt = ConversationRuntime(repository=repo)
    svc = ConversationManagementService(rt, _FakeIdempotencyPort())
    cid = svc.create(idempotency_key="at09-rem-mgmt", title="AT09 rem")["id"]
    try:
        for idx in range(17):
            rt.accept_user_turn(
                conversation_id=cid,
                turn_id=f"mgmt_{idx:03d}",
                modality="text",
                content=f"MGMT_{idx:03d}",
            )
        repo.close()

        _delete_catalog_files(tmp_path)
        repo2 = StorageV2ConversationRepository(tmp_path, segment_max_messages=8)
        rt2 = ConversationRuntime(repository=repo2)
        svc2 = ConversationManagementService(rt2, _FakeIdempotencyPort())
        detail = svc2.get(cid)
        messages = svc2.get_messages(cid, max_messages=100)

        assert detail["message_count"] == 17
        assert len(messages) == 17
        assert messages[-1]["content"] == "MGMT_016"
    finally:
        try:
            repo2.close()  # type: ignore[name-defined]
        except Exception:
            pass


def test_at09_rem_segment_backed_rebuild_counts_all_segments(tmp_path):
    """AT09-REM-005: derived rebuild scans every transcript segment."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=6)
    cid = "at09_rem_segments"
    try:
        repo.create_with_id(cid)
        expected = _append(repo, cid, 25, prefix="SEG")
        repo.close()

        _delete_catalog_files(tmp_path)
        repo2 = StorageV2ConversationRepository(tmp_path, segment_max_messages=6)
        messages = repo2.get_messages(cid)

        assert sorted(p.name for p in (tmp_path / cid).glob("transcript-*.jsonl")) == [
            "transcript-000001.jsonl",
            "transcript-000002.jsonl",
            "transcript-000003.jsonl",
            "transcript-000004.jsonl",
            "transcript-000005.jsonl",
        ]
        assert [m.content for m in messages] == expected
        assert repo2.get(cid).message_count == 25
        assert repo2._cat.execute(
            "SELECT last_sequence FROM conversations WHERE id=?", (cid,)
        ).fetchone()[0] == 25
    finally:
        try:
            repo2.close()  # type: ignore[name-defined]
        except Exception:
            pass

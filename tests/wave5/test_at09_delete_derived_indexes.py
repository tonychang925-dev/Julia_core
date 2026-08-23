"""Wave5 AT-09 R1 Permanent Acceptance — Delete Derived Indexes.

AT-09 freezes that derived catalog/index artifacts are rebuildable projections,
not canonical history or identity authority. Deleting derived artifacts and
rebuilding must preserve canonical history and future append identity.

TC mapping:
- TC-AT09-R1-001 delete derived catalog rebuild preserves canonical messages exactly
- TC-AT09-R1-002 stale counter/sequence sabotage is corrected from transcript truth
- TC-AT09-R1-003 post-rebuild append uses unique next canonical message_id
- TC-AT09-R1-004 turn lookup rebuild restores turn_index from transcript
- TC-AT09-R1-005 fresh runtime recovery preserves append identity continuity
- TC-AT09-R1-006 future indexes namespace deletion is non-authoritative/no-op for canonical history
- TC-AT09-R1-007 cross-conversation rebuild preserves isolation
- TC-AT09-R1-008 rebuild performs zero canonical transcript mutation
"""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_management_service import ConversationManagementService
from julia_core.runtime.conversation_runtime import ConversationRuntime


class _FakeIdempotencyPort:
    def __init__(self):
        self._reserved: dict[str, str] = {}

    def get_or_reserve(self, key: str, candidate: str) -> str:
        return self._reserved.setdefault(key, candidate)


def _stack(root: Path, *, segment_max_messages: int = 50):
    repo = StorageV2ConversationRepository(root, segment_max_messages=segment_max_messages)
    rt = ConversationRuntime(repository=repo)
    svc = ConversationManagementService(rt, _FakeIdempotencyPort())
    return repo, rt, svc


def _delete_catalog_files(root: Path) -> list[str]:
    deleted = []
    for path in list(root.glob("catalog.sqlite*")):
        deleted.append(path.name)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    return sorted(deleted)


def _delete_future_indexes_namespace(root: Path) -> bool:
    indexes = root / "indexes"
    if indexes.exists():
        shutil.rmtree(indexes)
        return True
    return False


def _append(repo: StorageV2ConversationRepository, cid: str, count: int, *, prefix: str) -> list[str]:
    expected = []
    for idx in range(count):
        content = f"{prefix}_{idx:03d}"
        expected.append(content)
        repo.add_message(cid, "user", content, turn_id=f"{prefix.lower()}_turn_{idx:03d}")
    return expected


def _append_via_runtime(rt: ConversationRuntime, cid: str, count: int, *, prefix: str) -> list[str]:
    expected = []
    for idx in range(count):
        content = f"{prefix}_{idx:03d}"
        expected.append(content)
        rt.accept_user_turn(
            conversation_id=cid,
            turn_id=f"{prefix.lower()}_turn_{idx:03d}",
            modality="text",
            content=content,
        )
    return expected


def _contents(messages) -> list[str]:
    return [m.content for m in messages]


def _ids(messages) -> list[str]:
    return [m.message_id for m in messages]


def _canonical_digest(root: Path, cid: str) -> str:
    h = hashlib.sha256()
    for path in sorted((root / cid).glob("transcript-*.jsonl")):
        h.update(path.name.encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def test_tc_at09_r1_001_delete_derived_catalog_rebuild_preserves_canonical_messages_exactly(tmp_path):
    """TC-AT09-R1-001: delete catalog.sqlite* and rebuild exact transcript view."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=17)
    try:
        cid = "at09_r1_exact"
        repo.create_with_id(cid)
        expected = _append(repo, cid, 64, prefix="EXACT")
        before = repo.get_messages(cid)
        before_digest = _canonical_digest(tmp_path, cid)
        repo.close()

        assert "catalog.sqlite" in _delete_catalog_files(tmp_path)
        repo2 = StorageV2ConversationRepository(tmp_path, segment_max_messages=17)
        after = repo2.get_messages(cid)

        assert _canonical_digest(tmp_path, cid) == before_digest
        assert _contents(after) == expected
        assert _ids(after) == _ids(before)
        assert repo2.get(cid).message_count == 64
    finally:
        try:
            repo2.close()  # type: ignore[name-defined]
        except Exception:
            pass


def test_tc_at09_r1_002_stale_counter_and_sequence_sabotage_corrected_from_transcript(tmp_path):
    """TC-AT09-R1-002: stale derived counters cannot override transcript truth."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=10)
    try:
        cid = "at09_r1_sabotage"
        repo.create_with_id(cid)
        _append(repo, cid, 12, prefix="SAB")
        repo._cat.execute(
            "UPDATE conversations SET message_count=?, last_sequence=? WHERE id=?",
            (0, 0, cid),
        )
        repo._cat.commit()
        assert repo.get(cid).message_count == 0

        repo.rebuild_catalog()
        rebuilt = repo.get(cid)

        assert rebuilt.message_count == 12
        assert repo._cat.execute(
            "SELECT last_sequence FROM conversations WHERE id=?", (cid,)
        ).fetchone()[0] == 12
        assert _contents(repo.get_messages(cid)) == [f"SAB_{i:03d}" for i in range(12)]
    finally:
        repo.close()


def test_tc_at09_r1_003_post_rebuild_append_uses_unique_next_canonical_message_id(tmp_path):
    """TC-AT09-R1-003: append after rebuild cannot collide with old IDs."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=7)
    try:
        cid = "at09_r1_append"
        repo.create_with_id(cid)
        _append(repo, cid, 19, prefix="OLD")
        repo.close()

        _delete_catalog_files(tmp_path)
        repo2 = StorageV2ConversationRepository(tmp_path, segment_max_messages=7)
        repo2.add_message(cid, "user", "NEW_AFTER_REBUILD", turn_id="new_after")
        messages = repo2.get_messages(cid)
        ids = _ids(messages)

        assert ids[-1] == f"msg_{cid}_000020"
        assert len(ids) == len(set(ids))
        assert messages[-1].content == "NEW_AFTER_REBUILD"
        assert repo2.get(cid).message_count == 20
    finally:
        try:
            repo2.close()  # type: ignore[name-defined]
        except Exception:
            pass


def test_tc_at09_r1_004_turn_lookup_rebuild_restores_turn_index_from_transcript(tmp_path):
    """TC-AT09-R1-004: derived turn_index deletion is rebuilt from transcript."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=3)
    try:
        cid = "at09_r1_turn"
        repo.create_with_id(cid)
        repo.add_message(cid, "user", "turn user", turn_id="shared_turn")
        repo.add_message(cid, "assistant", "turn assistant", turn_id="shared_turn")
        repo._cat.execute("DELETE FROM turn_index WHERE conversation_id=?", (cid,))
        repo._cat.commit()
        assert repo._cat.execute(
            "SELECT COUNT(*) FROM turn_index WHERE conversation_id=?", (cid,)
        ).fetchone()[0] == 0

        repo.rebuild_catalog()
        turn = repo.find_turn(cid, "shared_turn")

        assert [m.content for m in turn] == ["turn user", "turn assistant"]
        assert repo._cat.execute(
            "SELECT message_ids FROM turn_index WHERE conversation_id=? AND turn_id=?",
            (cid, "shared_turn"),
        ).fetchone()[0] == f"msg_{cid}_000001,msg_{cid}_000002"
    finally:
        repo.close()


def test_tc_at09_r1_005_fresh_runtime_recovery_preserves_append_identity_continuity(tmp_path):
    """TC-AT09-R1-005: fresh runtime append after rebuild continues identity."""
    repo1, rt1, svc1 = _stack(tmp_path, segment_max_messages=9)
    cid = svc1.create(idempotency_key="at09-r1-runtime", title="AT09 runtime")["id"]
    _append_via_runtime(rt1, cid, 16, prefix="RUNTIME")
    repo1.close()

    _delete_catalog_files(tmp_path)
    repo2, rt2, svc2 = _stack(tmp_path, segment_max_messages=9)
    try:
        rt2.accept_user_turn(
            conversation_id=cid,
            turn_id="runtime_after_rebuild",
            modality="text",
            content="RUNTIME_AFTER_REBUILD",
        )
        messages = svc2.get_messages(cid, max_messages=100)
        ids = [m["message_id"] for m in messages]

        assert ids[-1] == f"msg_{cid}_000017"
        assert len(ids) == len(set(ids))
        assert messages[-1]["content"] == "RUNTIME_AFTER_REBUILD"
        assert svc2.get(cid)["message_count"] == 17
    finally:
        repo2.close()


def test_tc_at09_r1_006_future_indexes_namespace_deletion_is_non_authoritative(tmp_path):
    """TC-AT09-R1-006: indexes/* is derived namespace, not canonical authority."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=10)
    try:
        cid = "at09_r1_indexes"
        repo.create_with_id(cid)
        expected = _append(repo, cid, 10, prefix="IDXNS")
        indexes = tmp_path / "indexes"
        indexes.mkdir()
        (indexes / "conversation_fts.db").write_text("derived placeholder")
        before_digest = _canonical_digest(tmp_path, cid)
        repo.close()

        assert _delete_future_indexes_namespace(tmp_path) is True
        repo2 = StorageV2ConversationRepository(tmp_path, segment_max_messages=10)
        messages = repo2.get_messages(cid)

        assert _canonical_digest(tmp_path, cid) == before_digest
        assert _contents(messages) == expected
        assert repo2.get(cid).message_count == 10
    finally:
        try:
            repo2.close()  # type: ignore[name-defined]
        except Exception:
            pass


def test_tc_at09_r1_007_cross_conversation_rebuild_preserves_isolation(tmp_path):
    """TC-AT09-R1-007: rebuild does not mix derived rows across conversations."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=5)
    try:
        repo.create_with_id("conv_a")
        repo.create_with_id("conv_b")
        _append(repo, "conv_a", 11, prefix="ALPHA_AT09")
        _append(repo, "conv_b", 7, prefix="BETA_AT09")
        repo.close()

        _delete_catalog_files(tmp_path)
        repo2 = StorageV2ConversationRepository(tmp_path, segment_max_messages=5)
        a_msgs = repo2.get_messages("conv_a")
        b_msgs = repo2.get_messages("conv_b")

        assert all("ALPHA_AT09" in m.content for m in a_msgs)
        assert all("BETA_AT09" in m.content for m in b_msgs)
        assert repo2.get("conv_a").message_count == 11
        assert repo2.get("conv_b").message_count == 7
        assert repo2.search("ALPHA_AT09_010")[0].id == "conv_a"
        assert repo2.search("BETA_AT09_006")[0].id == "conv_b"
    finally:
        try:
            repo2.close()  # type: ignore[name-defined]
        except Exception:
            pass


def test_tc_at09_r1_008_rebuild_performs_zero_canonical_transcript_mutation(tmp_path):
    """TC-AT09-R1-008: rebuild changes derived catalog only, not transcript."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=4)
    try:
        cid = "at09_r1_readonly"
        repo.create_with_id(cid)
        _append(repo, cid, 18, prefix="IMMUTABLE")
        before_digest = _canonical_digest(tmp_path, cid)
        before_ids = _ids(repo.get_messages(cid))

        repo.rebuild_catalog()
        after_digest = _canonical_digest(tmp_path, cid)
        after_ids = _ids(repo.get_messages(cid))

        assert before_digest == after_digest
        assert before_ids == after_ids
        assert repo.get(cid).message_count == 18
    finally:
        repo.close()

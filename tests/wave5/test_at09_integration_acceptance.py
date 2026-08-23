"""Wave5 AT-09 Integration Acceptance — Delete Derived Indexes.

IA verifies the real governed management/runtime/StorageV2 path after deleting
and rebuilding derived catalog/index artifacts. It does not test AT-10,
compaction, search optimization, FTS/tokenizer work, transcript redesign, or
Electron cache behavior.

TC mapping:
- TC-AT09-IA-001 management path reads complete canonical history after derived deletion/rebuild
- TC-AT09-IA-002 fresh runtime recovery does not use catalog as history authority
- TC-AT09-IA-003 governed post-rebuild append preserves message identity continuity
- TC-AT09-IA-004 sabotaged derived counters are corrected from canonical transcript
- TC-AT09-IA-005 multi-conversation rebuild preserves isolation through management/search
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


def _contents(messages: list[dict]) -> list[str]:
    return [m["content"] for m in messages]


def _ids(messages: list[dict]) -> list[str]:
    return [m["message_id"] for m in messages]


def test_tc_at09_ia_001_management_reads_complete_history_after_derived_deletion_rebuild(tmp_path):
    """TC-AT09-IA-001: management read after derived deletion sees full transcript."""
    repo1, rt1, svc1 = _stack(tmp_path, segment_max_messages=13)
    cid = svc1.create(idempotency_key="at09-ia-001", title="AT09 IA read")["id"]
    expected = _append_via_runtime(rt1, cid, 52, prefix="IA_READ")
    before_ids = _ids(svc1.get_messages(cid, max_messages=100))
    repo1.close()

    assert "catalog.sqlite" in _delete_catalog_files(tmp_path)
    repo2, _rt2, svc2 = _stack(tmp_path, segment_max_messages=13)
    try:
        after = svc2.get_messages(cid, max_messages=100)
        detail = svc2.get(cid)

        assert _contents(after) == expected
        assert _ids(after) == before_ids
        assert detail["message_count"] == 52
    finally:
        repo2.close()


def test_tc_at09_ia_002_fresh_runtime_recovery_does_not_use_catalog_as_history_authority(tmp_path):
    """TC-AT09-IA-002: missing catalog cannot erase or recreate history."""
    repo1, rt1, svc1 = _stack(tmp_path, segment_max_messages=9)
    cid = svc1.create(idempotency_key="at09-ia-002", title="AT09 IA runtime")["id"]
    expected = _append_via_runtime(rt1, cid, 31, prefix="IA_RUNTIME")
    repo1.close()

    _delete_catalog_files(tmp_path)
    repo2, rt2, svc2 = _stack(tmp_path, segment_max_messages=9)
    try:
        recovered = svc2.get_messages(cid, max_messages=100)
        rt2.accept_user_turn(
            conversation_id=cid,
            turn_id="ia_runtime_after",
            modality="text",
            content="IA_RUNTIME_AFTER",
        )
        after_append = svc2.get_messages(cid, max_messages=100)

        assert _contents(recovered) == expected
        assert after_append[-1]["message_id"] == f"msg_{cid}_000032"
        assert len(_ids(after_append)) == len(set(_ids(after_append)))
        assert svc2.get(cid)["message_count"] == 32
    finally:
        repo2.close()


def test_tc_at09_ia_003_governed_post_rebuild_append_preserves_identity_continuity(tmp_path):
    """TC-AT09-IA-003: runtime append after rebuild uses next canonical ID."""
    repo1, rt1, svc1 = _stack(tmp_path, segment_max_messages=7)
    cid = svc1.create(idempotency_key="at09-ia-003", title="AT09 IA append")["id"]
    _append_via_runtime(rt1, cid, 18, prefix="IA_APPEND")
    repo1.close()

    _delete_catalog_files(tmp_path)
    repo2, rt2, svc2 = _stack(tmp_path, segment_max_messages=7)
    try:
        rt2.accept_user_turn(
            conversation_id=cid,
            turn_id="ia_append_after_rebuild",
            modality="text",
            content="IA_APPEND_AFTER_REBUILD",
        )
        messages = svc2.get_messages(cid, max_messages=100)
        ids = _ids(messages)

        assert ids[-1] == f"msg_{cid}_000019"
        assert len(ids) == len(set(ids))
        assert messages[-1]["content"] == "IA_APPEND_AFTER_REBUILD"
    finally:
        repo2.close()


def test_tc_at09_ia_004_sabotaged_derived_counters_corrected_from_canonical_transcript(tmp_path):
    """TC-AT09-IA-004: stale catalog metadata is repaired from canonical files."""
    repo, rt, svc = _stack(tmp_path, segment_max_messages=6)
    cid = svc.create(idempotency_key="at09-ia-004", title="AT09 IA sabotage")["id"]
    expected = _append_via_runtime(rt, cid, 24, prefix="IA_SAB")
    try:
        repo._cat.execute(
            "UPDATE conversations SET message_count=?, last_sequence=? WHERE id=?",
            (0, 0, cid),
        )
        repo._cat.commit()
        assert svc.get(cid)["message_count"] == 0

        repo.rebuild_catalog()
        detail = svc.get(cid)
        messages = svc.get_messages(cid, max_messages=100)

        assert detail["message_count"] == 24
        assert _contents(messages) == expected
        assert repo._cat.execute(
            "SELECT last_sequence FROM conversations WHERE id=?", (cid,)
        ).fetchone()[0] == 24
    finally:
        repo.close()


def test_tc_at09_ia_005_multi_conversation_rebuild_preserves_isolation(tmp_path):
    """TC-AT09-IA-005: A/B conversations remain isolated after derived rebuild."""
    repo1, rt1, svc1 = _stack(tmp_path, segment_max_messages=8)
    cid_a = svc1.create(idempotency_key="at09-ia-005-a", title="AT09 IA A")["id"]
    cid_b = svc1.create(idempotency_key="at09-ia-005-b", title="AT09 IA B")["id"]
    expected_a = _append_via_runtime(rt1, cid_a, 15, prefix="IA_ALPHA")
    expected_b = _append_via_runtime(rt1, cid_b, 11, prefix="IA_BETA")
    repo1.close()

    _delete_catalog_files(tmp_path)
    repo2, rt2, svc2 = _stack(tmp_path, segment_max_messages=8)
    try:
        msgs_a = svc2.get_messages(cid_a, max_messages=100)
        msgs_b = svc2.get_messages(cid_b, max_messages=100)
        search_a = [h.conversation_id for h in rt2.search_conversations("IA_ALPHA_014")]
        search_b = [h.conversation_id for h in rt2.search_conversations("IA_BETA_010")]

        assert _contents(msgs_a) == expected_a
        assert _contents(msgs_b) == expected_b
        assert all("IA_BETA" not in m["content"] for m in msgs_a)
        assert all("IA_ALPHA" not in m["content"] for m in msgs_b)
        assert search_a == [cid_a]
        assert search_b == [cid_b]
        assert svc2.get(cid_a)["message_count"] == 15
        assert svc2.get(cid_b)["message_count"] == 11
    finally:
        repo2.close()

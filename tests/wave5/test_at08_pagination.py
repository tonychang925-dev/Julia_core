"""Wave5 AT-08 R1 Permanent Acceptance — Pagination.

AT-08 freezes that pagination is a read-view mechanism over canonical history,
not a history authority. Page traversal must preserve canonical order with zero
duplicate and zero missing messages across segment boundaries and recovery.

TC mapping:
- TC-AT08-R1-001 200+ messages page-by-page yields zero duplicate and zero missing
- TC-AT08-R1-002 combined pages equal full canonical sequence in chronological order
- TC-AT08-R1-003 before/after cursors are exclusive and cannot repeat boundary pages
- TC-AT08-R1-004 pagination crosses physical segment files transparently
- TC-AT08-R1-005 fresh repository/runtime recovery preserves page traversal
- TC-AT08-R1-006 invalid/stale cursor does not restart from tail/head
- TC-AT08-R1-007 foreign conversation cursor cannot authorize cross-conversation read
- TC-AT08-R1-008 pagination reads perform zero canonical mutation
"""

from __future__ import annotations

import hashlib
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


def _append(repo: StorageV2ConversationRepository, cid: str, count: int, *, prefix: str) -> list[str]:
    expected = []
    for idx in range(count):
        content = f"{prefix}_{idx:03d}"
        expected.append(content)
        repo.add_message(cid, "user", content, turn_id=f"{prefix.lower()}_turn_{idx:03d}")
    return expected


def _segments(root: Path, cid: str) -> list[str]:
    return sorted(p.name for p in (root / cid).glob("transcript-*.jsonl"))


def _contents(messages) -> list[str]:
    return [m.content for m in messages]


def _dict_contents(messages: list[dict]) -> list[str]:
    return [m["content"] for m in messages]


def _walk_before_repo(repo: StorageV2ConversationRepository, cid: str, *, page_size: int):
    pages = []
    before = None
    while True:
        page = repo.get_messages(cid, before=before, limit=page_size)
        if not page:
            break
        pages.append(page)
        before = page[0].message_id
    return pages, [m for page in reversed(pages) for m in page]


def _walk_before_service(svc: ConversationManagementService, cid: str, *, page_size: int):
    pages = []
    before = None
    while True:
        page = svc.get_messages(cid, before=before, limit=page_size)
        if not page:
            break
        pages.append(page)
        before = page[0]["message_id"]
    return pages, [m for page in reversed(pages) for m in page]


def _canonical_digest(root: Path, cid: str) -> str:
    h = hashlib.sha256()
    for path in sorted((root / cid).glob("transcript-*.jsonl")):
        h.update(path.name.encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def test_tc_at08_r1_001_200_messages_page_by_page_zero_duplicate_zero_missing(tmp_path):
    """TC-AT08-R1-001: 205 durable messages are recovered exactly once by pages."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=50)
    try:
        cid = "at08_r1_full"
        repo.create_with_id(cid)
        expected = _append(repo, cid, 205, prefix="FULL")

        pages, combined = _walk_before_repo(repo, cid, page_size=50)

        assert [len(p) for p in pages] == [50, 50, 50, 50, 5]
        assert _contents(combined) == expected
        assert len(combined) == 205
        assert len({m.message_id for m in combined}) == 205
    finally:
        repo.close()


def test_tc_at08_r1_002_combined_pages_equal_full_canonical_sequence(tmp_path):
    """TC-AT08-R1-002: concatenated pages equal full read in canonical order."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=37)
    try:
        cid = "at08_r1_equivalence"
        repo.create_with_id(cid)
        _append(repo, cid, 211, prefix="EQUAL")

        full = repo.get_messages(cid)
        _pages, combined = _walk_before_repo(repo, cid, page_size=33)

        assert [m.message_id for m in combined] == [m.message_id for m in full]
        assert _contents(combined) == _contents(full)
    finally:
        repo.close()


def test_tc_at08_r1_003_before_after_cursors_are_exclusive_boundaries(tmp_path):
    """TC-AT08-R1-003: before/after do not repeat the boundary message."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=10)
    try:
        cid = "at08_r1_cursors"
        repo.create_with_id(cid)
        expected = _append(repo, cid, 60, prefix="CURSOR")
        full = repo.get_messages(cid)

        older = repo.get_messages(cid, before=full[40].message_id, limit=10)
        newer = repo.get_messages(cid, after=full[19].message_id, limit=10)

        assert _contents(older) == expected[30:40]
        assert full[40].message_id not in {m.message_id for m in older}
        assert _contents(newer) == expected[20:30]
        assert full[19].message_id not in {m.message_id for m in newer}
    finally:
        repo.close()


def test_tc_at08_r1_004_pagination_crosses_physical_segments_transparently(tmp_path):
    """TC-AT08-R1-004: page windows may cross segment files without semantic split."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=12)
    try:
        cid = "at08_r1_segments"
        repo.create_with_id(cid)
        expected = _append(repo, cid, 73, prefix="SEG")

        page = repo.get_messages(cid, before=repo.get_messages(cid)[50].message_id, limit=25)

        assert len(_segments(tmp_path, cid)) == 7
        assert _contents(page) == expected[25:50]
        assert {m.conversation_id for m in page} == {cid}
    finally:
        repo.close()


def test_tc_at08_r1_005_fresh_runtime_recovery_preserves_page_traversal(tmp_path):
    """TC-AT08-R1-005: pagination derives from durable repository, not cache."""
    repo1, _rt1, svc1 = _stack(tmp_path, segment_max_messages=41)
    cid = svc1.create(idempotency_key="at08-r1-recovery", title="AT08 R1 recovery")["id"]
    expected = _append(repo1, cid, 207, prefix="REC")
    repo1.close()

    repo2, _rt2, svc2 = _stack(tmp_path, segment_max_messages=41)
    try:
        pages, combined = _walk_before_service(svc2, cid, page_size=40)

        assert [len(p) for p in pages] == [40, 40, 40, 40, 40, 7]
        assert _dict_contents(combined) == expected
        assert len({m["message_id"] for m in combined}) == 207
    finally:
        repo2.close()


def test_tc_at08_r1_006_invalid_and_stale_cursor_do_not_restart_from_tail_or_head(tmp_path):
    """TC-AT08-R1-006: bad cursor returns defined empty page, not phantom data."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=8)
    try:
        cid = "at08_r1_invalid"
        repo.create_with_id(cid)
        _append(repo, cid, 27, prefix="VALID")

        assert repo.get_messages(cid, before="missing-message-id", limit=10) == []
        assert repo.get_messages(cid, after="missing-message-id", limit=10) == []
        assert _contents(repo.get_messages(cid, limit=10)) == [f"VALID_{i:03d}" for i in range(17, 27)]
    finally:
        repo.close()


def test_tc_at08_r1_007_foreign_conversation_cursor_cannot_authorize_page_read(tmp_path):
    """TC-AT08-R1-007: conversation A cursor is not page authority for B."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=8)
    try:
        repo.create_with_id("conv_a")
        repo.create_with_id("conv_b")
        _append(repo, "conv_a", 30, prefix="ALPHA_PRIVATE")
        _append(repo, "conv_b", 30, prefix="BETA_PRIVATE")
        foreign_cursor = repo.get_messages("conv_a", limit=1)[0].message_id

        assert repo.get_messages("conv_b", before=foreign_cursor, limit=10) == []
        assert repo.get_messages("conv_b", after=foreign_cursor, limit=10) == []
        assert all("ALPHA_PRIVATE" not in m.content for m in repo.get_messages("conv_b"))
    finally:
        repo.close()


def test_tc_at08_r1_008_pagination_read_path_performs_zero_canonical_mutation(tmp_path):
    """TC-AT08-R1-008: pagination is read-only over transcript files."""
    repo, _rt, svc = _stack(tmp_path, segment_max_messages=9)
    try:
        cid = svc.create(idempotency_key="at08-r1-mutation", title="AT08 R1 mutation")["id"]
        _append(repo, cid, 44, prefix="IMMUTABLE")
        before_digest = _canonical_digest(tmp_path, cid)
        before_full = svc.get_messages(cid, max_messages=100)

        pages, combined = _walk_before_service(svc, cid, page_size=7)
        after_digest = _canonical_digest(tmp_path, cid)
        after_full = svc.get_messages(cid, max_messages=100)

        assert before_digest == after_digest
        assert before_full == after_full
        assert _dict_contents(combined) == _dict_contents(before_full)
        assert len(pages) == 7
    finally:
        repo.close()

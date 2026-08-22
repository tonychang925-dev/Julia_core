"""Wave5 AT-08 Minimal Remediation — cursor pagination.

These tests verify the minimal fix for the P0 pagination gap found in AT-08
Audit. They are remediation evidence, not final R1/IA freeze evidence.
"""

from __future__ import annotations

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_management_service import ConversationManagementService
from julia_core.runtime.conversation_runtime import ConversationRuntime


class _FakeIdempotencyPort:
    def __init__(self):
        self._reserved: dict[str, str] = {}

    def get_or_reserve(self, key: str, candidate: str) -> str:
        return self._reserved.setdefault(key, candidate)


def _stack(root, *, segment_max_messages=50):
    repo = StorageV2ConversationRepository(root, segment_max_messages=segment_max_messages)
    rt = ConversationRuntime(repository=repo)
    svc = ConversationManagementService(rt, _FakeIdempotencyPort())
    return repo, rt, svc


def _append_messages(repo, cid: str, count: int, *, prefix: str = "PAGE_MARKER") -> list[str]:
    expected = []
    for idx in range(count):
        content = f"{prefix}_{idx:03d}"
        expected.append(content)
        repo.add_message(cid, "user", content, turn_id=f"turn_{idx:03d}")
    return expected


def _segment_names(root, cid: str) -> list[str]:
    return sorted(p.name for p in (root / cid).glob("transcript-*.jsonl"))


def _contents(messages) -> list[str]:
    return [m.content for m in messages]


def _dict_contents(messages: list[dict]) -> list[str]:
    return [m["content"] for m in messages]


def _page_backwards(repo, cid: str, *, page_size: int) -> list:
    pages = []
    before = None
    while True:
        page = repo.get_messages(cid, before=before, limit=page_size)
        if not page:
            break
        pages.append(page)
        before = page[0].message_id
    return [msg for page in reversed(pages) for msg in page]


def test_at08_rem_repository_before_cursor_traverses_all_pages_without_duplicate_or_missing(tmp_path):
    """AT08-REM-001: before cursor fixes repeated-tail pagination gap."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=50)
    try:
        cid = "at08_rem_before"
        repo.create_with_id(cid)
        expected = _append_messages(repo, cid, 205)

        combined = _page_backwards(repo, cid, page_size=50)
        assert _segment_names(tmp_path, cid) == [
            "transcript-000001.jsonl",
            "transcript-000002.jsonl",
            "transcript-000003.jsonl",
            "transcript-000004.jsonl",
            "transcript-000005.jsonl",
        ]
        assert _contents(combined) == expected
        assert len({m.message_id for m in combined}) == 205
    finally:
        repo.close()


def test_at08_rem_before_and_after_are_exclusive_cursor_boundaries(tmp_path):
    """AT08-REM-002: before returns older, after returns newer; boundary excluded."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=10)
    try:
        cid = "at08_rem_direction"
        repo.create_with_id(cid)
        expected = _append_messages(repo, cid, 30, prefix="DIR")
        full = repo.get_messages(cid)

        before_page = repo.get_messages(cid, before=full[20].message_id, limit=5)
        after_page = repo.get_messages(cid, after=full[9].message_id, limit=5)

        assert _contents(before_page) == expected[15:20]
        assert full[20].content not in _contents(before_page)
        assert _contents(after_page) == expected[10:15]
        assert full[9].content not in _contents(after_page)
    finally:
        repo.close()


def test_at08_rem_invalid_and_foreign_cursor_do_not_restart_from_tail(tmp_path):
    """AT08-REM-003: unknown/foreign cursor returns defined empty page, not tail."""
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=5)
    try:
        repo.create_with_id("conv_a")
        repo.create_with_id("conv_b")
        _append_messages(repo, "conv_a", 12, prefix="ALPHA")
        _append_messages(repo, "conv_b", 12, prefix="BETA")
        foreign_cursor = repo.get_messages("conv_a", limit=1)[0].message_id

        assert repo.get_messages("conv_b", before="missing-cursor", limit=5) == []
        assert repo.get_messages("conv_b", before=foreign_cursor, limit=5) == []
        assert _contents(repo.get_messages("conv_b", limit=5)) == [f"BETA_{i:03d}" for i in range(7, 12)]
    finally:
        repo.close()


def test_at08_rem_management_surface_uses_governed_cursor_pagination(tmp_path):
    """AT08-REM-004: management/runtime path exposes cursor paging without shortcut."""
    repo, _rt, svc = _stack(tmp_path, segment_max_messages=25)
    try:
        cid = svc.create(idempotency_key="at08-rem-mgmt", title="AT08 remediation") ["id"]
        expected = _append_messages(repo, cid, 105, prefix="MGMT")

        pages = []
        before = None
        while True:
            page = svc.get_messages(cid, before=before, limit=20)
            if not page:
                break
            pages.append(page)
            before = page[0]["message_id"]

        combined = [msg for page in reversed(pages) for msg in page]
        assert _dict_contents(combined) == expected
        assert len({m["message_id"] for m in combined}) == 105
        assert {m["conversation_id"] for m in combined} == {cid}
    finally:
        repo.close()


def test_at08_rem_fresh_runtime_recovery_preserves_cursor_pagination(tmp_path):
    """AT08-REM-005: pagination derives from durable transcript, not runtime cache."""
    repo1, _rt1, svc1 = _stack(tmp_path, segment_max_messages=30)
    cid = svc1.create(idempotency_key="at08-rem-recovery", title="AT08 recovery")["id"]
    expected = _append_messages(repo1, cid, 123, prefix="RECOVER")
    repo1.close()

    repo2, _rt2, svc2 = _stack(tmp_path, segment_max_messages=30)
    try:
        pages = []
        before = None
        while True:
            page = svc2.get_messages(cid, before=before, limit=25)
            if not page:
                break
            pages.append(page)
            before = page[0]["message_id"]

        combined = [msg for page in reversed(pages) for msg in page]
        assert _dict_contents(combined) == expected
        assert len({m["message_id"] for m in combined}) == 123
    finally:
        repo2.close()

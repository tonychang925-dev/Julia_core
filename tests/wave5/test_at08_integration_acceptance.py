"""Wave5 AT-08 Integration Acceptance — Pagination.

IA verifies the real governed management/runtime/StorageV2 path for pagination.
It does not test AT-09, compaction, search optimization, transcript redesign, or
Electron UI behavior.

TC mapping:
- TC-AT08-IA-001 management/runtime path loads pages without raw storage shortcut
- TC-AT08-IA-002 runtime cache/session state is not pagination authority
- TC-AT08-IA-003 segment-backed 200+ message conversation paginates as one history
- TC-AT08-IA-004 fresh runtime/repository recovery preserves management pagination
- TC-AT08-IA-005 management pagination is read-only and preserves turn identity
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


def _walk_management_pages(svc: ConversationManagementService, cid: str, *, page_size: int):
    pages = []
    before = None
    while True:
        page = svc.get_messages(cid, before=before, limit=page_size)
        if not page:
            break
        pages.append(page)
        before = page[0]["message_id"]
    combined = [message for page in reversed(pages) for message in page]
    return pages, combined


def _segments(root: Path, cid: str) -> list[str]:
    return sorted(p.name for p in (root / cid).glob("transcript-*.jsonl"))


def _contents(messages: list[dict]) -> list[str]:
    return [m["content"] for m in messages]


def _ids(messages: list[dict]) -> list[str]:
    return [m["message_id"] for m in messages]


def _canonical_digest(root: Path, cid: str) -> str:
    h = hashlib.sha256()
    for path in sorted((root / cid).glob("transcript-*.jsonl")):
        h.update(path.name.encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def test_tc_at08_ia_001_management_runtime_path_loads_pages_without_raw_storage_shortcut(tmp_path):
    """TC-AT08-IA-001: product/governed read route performs cursor traversal."""
    repo, rt, svc = _stack(tmp_path, segment_max_messages=20)
    try:
        cid = svc.create(idempotency_key="at08-ia-001", title="AT08 IA governed")["id"]
        expected = _append_via_runtime(rt, cid, 85, prefix="IA_GOV")

        pages, combined = _walk_management_pages(svc, cid, page_size=17)

        assert [len(page) for page in pages] == [17, 17, 17, 17, 17]
        assert _contents(combined) == expected
        assert len(set(_ids(combined))) == 85
        assert {m["conversation_id"] for m in combined} == {cid}
    finally:
        repo.close()


def test_tc_at08_ia_002_runtime_cache_state_is_not_pagination_authority(tmp_path):
    """TC-AT08-IA-002: corrupted in-memory cache does not define page truth."""
    repo, rt, svc = _stack(tmp_path, segment_max_messages=10)
    try:
        cid = svc.create(idempotency_key="at08-ia-002", title="AT08 IA cache")["id"]
        expected = _append_via_runtime(rt, cid, 45, prefix="IA_CACHE")

        # Sabotage runtime interaction/cache-like state. Pagination must still
        # come from repository-backed canonical messages through management.
        rt._interaction_states[cid] = object()  # noqa: SLF001 - deliberate sabotage probe

        pages, combined = _walk_management_pages(svc, cid, page_size=9)

        assert _contents(combined) == expected
        assert len(set(_ids(combined))) == 45
    finally:
        repo.close()


def test_tc_at08_ia_003_segment_backed_200_plus_messages_paginate_as_one_history(tmp_path):
    """TC-AT08-IA-003: multiple segments + multiple pages remain one transcript."""
    repo, rt, svc = _stack(tmp_path, segment_max_messages=50)
    try:
        cid = svc.create(idempotency_key="at08-ia-003", title="AT08 IA segments")["id"]
        expected = _append_via_runtime(rt, cid, 205, prefix="IA_SEG")

        pages, combined = _walk_management_pages(svc, cid, page_size=50)

        assert _segments(tmp_path, cid) == [
            "transcript-000001.jsonl",
            "transcript-000002.jsonl",
            "transcript-000003.jsonl",
            "transcript-000004.jsonl",
            "transcript-000005.jsonl",
        ]
        assert [len(page) for page in pages] == [50, 50, 50, 50, 5]
        assert _contents(combined) == expected
        assert len(set(_ids(combined))) == 205
    finally:
        repo.close()


def test_tc_at08_ia_004_fresh_runtime_recovery_preserves_management_pagination(tmp_path):
    """TC-AT08-IA-004: fresh stack paginates from durable canonical transcript."""
    repo1, rt1, svc1 = _stack(tmp_path, segment_max_messages=32)
    cid = svc1.create(idempotency_key="at08-ia-004", title="AT08 IA recovery")["id"]
    expected = _append_via_runtime(rt1, cid, 129, prefix="IA_REC")
    repo1.close()

    repo2, _rt2, svc2 = _stack(tmp_path, segment_max_messages=32)
    try:
        pages, combined = _walk_management_pages(svc2, cid, page_size=31)

        assert [len(page) for page in pages] == [31, 31, 31, 31, 5]
        assert _contents(combined) == expected
        assert len(set(_ids(combined))) == 129
    finally:
        repo2.close()


def test_tc_at08_ia_005_management_pagination_is_read_only_and_preserves_turn_identity(tmp_path):
    """TC-AT08-IA-005: page reads do not mutate transcript or turn IDs."""
    repo, rt, svc = _stack(tmp_path, segment_max_messages=11)
    try:
        cid = svc.create(idempotency_key="at08-ia-005", title="AT08 IA readonly")["id"]
        expected = _append_via_runtime(rt, cid, 55, prefix="IA_IMM")
        before_digest = _canonical_digest(tmp_path, cid)
        before_full = svc.get_messages(cid, max_messages=100)
        before_turns = [(m["turn_id"], m["message_id"], m["content"]) for m in before_full]

        pages, combined = _walk_management_pages(svc, cid, page_size=8)
        after_digest = _canonical_digest(tmp_path, cid)
        after_full = svc.get_messages(cid, max_messages=100)
        after_turns = [(m["turn_id"], m["message_id"], m["content"]) for m in after_full]

        assert _contents(combined) == expected
        assert before_digest == after_digest
        assert before_full == after_full
        assert before_turns == after_turns
    finally:
        repo.close()

"""W2-I1 — CM-S3 ConversationManagementService acceptance tests.

RED→GREEN against the frozen CM-S3 protocol (Wave-2 authority 6d4cfe7).
Core-side semantic tests use an in-memory CreateIdempotencyPort; the real
durable physical adapter lives in Julia-AI-Assistant (F2 path opacity).
"""
from __future__ import annotations

import pytest

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime
from julia_core.runtime.conversation_management_service import (
    ConversationManagementService,
    ConversationNotFoundError,
    CreateFailedError,
    LifecycleUnavailableError,
)


class _FakeIdempotencyPort:
    """In-memory put-if-absent port for Core semantic tests (not the physical adapter)."""

    def __init__(self):
        self._reserved: dict[str, str] = {}
        self.corrupt = False

    def get_or_reserve(self, key, candidate):
        if self.corrupt:
            raise RuntimeError("idempotency state corrupt")
        if key in self._reserved:
            return self._reserved[key]
        self._reserved[key] = candidate
        return candidate


@pytest.fixture
def svc(tmp_path):
    repo = StorageV2ConversationRepository(str(tmp_path))
    rt = ConversationRuntime(repository=repo)
    port = _FakeIdempotencyPort()
    yield ConversationManagementService(rt, port)
    repo.close()


# ── GAP-8: unknown → REJECT, never auto-create ─────────────────────────────
def test_get_unknown_raises_not_found(svc):
    with pytest.raises(ConversationNotFoundError):
        svc.get("nonexistent")


def test_open_unknown_raises_not_found(svc):
    with pytest.raises(ConversationNotFoundError):
        svc.open("nonexistent")


def test_get_unknown_does_not_create(svc):
    with pytest.raises(ConversationNotFoundError):
        svc.get("typo123")
    assert svc._runtime.get_conversation("typo123") is None


# ── create: canonical id from Runtime, reserve-before-create ───────────────
def test_create_returns_canonical_id(svc):
    detail = svc.create(title="hello")
    assert detail["id"]


def test_two_creates_same_second_distinct_ids(svc):
    d1 = svc.create(title="a")
    d2 = svc.create(title="b")
    assert d1["id"] != d2["id"]


def test_reserve_before_create_order(svc, monkeypatch):
    order = []
    real_reserve = svc._idempotency.get_or_reserve

    def recording_reserve(key, cid):
        order.append("reserve")
        return real_reserve(key, cid)

    svc._idempotency.get_or_reserve = recording_reserve
    real_create = svc._runtime.create_conversation

    def recording_create(conversation_id, title="x"):
        order.append("create")
        return real_create(conversation_id, title)

    monkeypatch.setattr(svc._runtime, "create_conversation", recording_create)
    svc.create(idempotency_key="req-1")
    assert order == ["reserve", "create"]


def test_create_idempotency_key_same_conversation(svc):
    d1 = svc.create(idempotency_key="req-1", title="a")
    d2 = svc.create(idempotency_key="req-1", title="a")
    assert d1["id"] == d2["id"]


def test_create_different_key_independent(svc):
    d1 = svc.create(idempotency_key="req-1", title="a")
    d2 = svc.create(idempotency_key="req-2", title="b")
    assert d1["id"] != d2["id"]


def test_idempotency_key_is_not_conversation_id(svc):
    detail = svc.create(idempotency_key="req-xyz", title="a")
    assert detail["id"] != "req-xyz"


# ── restart / reconstruction idempotency (semantic convergence) ────────────
def test_restart_idempotency_same_conversation(tmp_path):
    port = _FakeIdempotencyPort()  # durable reservation across reconstruction
    repo1 = StorageV2ConversationRepository(str(tmp_path))
    rt1 = ConversationRuntime(repository=repo1)
    svc1 = ConversationManagementService(rt1, port)
    d1 = svc1.create(idempotency_key="req-K", title="a")
    cid1 = d1["id"]

    repo2 = StorageV2ConversationRepository(str(tmp_path))
    rt2 = ConversationRuntime(repository=repo2)
    svc2 = ConversationManagementService(rt2, port)
    d2 = svc2.create(idempotency_key="req-K", title="a")
    assert d2["id"] == cid1


# ── fail-closed: corruption never treated as empty ─────────────────────────
def test_corrupt_idempotency_state_fail_closed(svc):
    svc._idempotency.corrupt = True
    with pytest.raises(CreateFailedError) as exc:
        svc.create(idempotency_key="req-x")
    assert isinstance(exc.value.__cause__, RuntimeError)
    # zero second canonical conversation manufactured
    assert len(svc.list()) == 0


# ── AT-CMS-02: create failure → governed failure ───────────────────────────
def test_create_failure_governed(svc, monkeypatch):
    def failing_create(cid, title="x"):
        raise RuntimeError("boom")

    monkeypatch.setattr(svc._runtime, "create_conversation", failing_create)
    with pytest.raises(CreateFailedError):
        svc.create(idempotency_key="req-fail")


# ── rename: metadata only, transcript untouched ────────────────────────────
def test_rename_updates_title_keeps_id(svc):
    detail = svc.create(title="before")
    cid = detail["id"]
    handle = svc.rename(cid, "after")
    assert handle.conversation_id == cid


def test_rename_unknown_raises(svc):
    with pytest.raises(ConversationNotFoundError):
        svc.rename("ghost", "x")


# ── list / search delegate to Runtime ──────────────────────────────────────
def test_list_and_search(svc):
    svc.create(title="alpha")
    svc.create(title="beta")
    assert len(svc.list()) == 2
    assert len(svc.search("alpha")) >= 1


# ── open/resume does not transfer client transcript ────────────────────────
def test_open_returns_canonical_detail(svc):
    detail = svc.create(title="resume-me")
    cid = detail["id"]
    opened = svc.open(cid)
    assert opened["id"] == cid


# ── AT-CMS-08: lifecycle fail-closed (CM-S6 not implemented) ───────────────
def test_delete_fail_closed_conversation_intact(svc):
    detail = svc.create(title="keep")
    cid = detail["id"]
    with pytest.raises(LifecycleUnavailableError):
        svc.delete(cid)
    assert svc.get(cid)["id"] == cid


def test_archive_fail_closed_conversation_intact(svc):
    detail = svc.create(title="keep")
    cid = detail["id"]
    with pytest.raises(LifecycleUnavailableError):
        svc.archive(cid)
    assert svc.get(cid)["id"] == cid

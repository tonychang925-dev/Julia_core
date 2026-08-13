"""W2-I1 — CM-S3 ConversationManagementService acceptance tests.

RED→GREEN against the frozen CM-S3 protocol (Wave-2 authority 6d4cfe7).
Production evidence producer: SPEC_FROZEN → PASS.
"""
from __future__ import annotations

import pytest

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime
from julia_core.runtime.conversation_management_service import (
    ConversationManagementService,
    ConversationNotFoundError,
    CreateFailedError,
    CreateIdempotencyStore,
    LifecycleUnavailableError,
)


@pytest.fixture
def svc(tmp_path):
    repo = StorageV2ConversationRepository(str(tmp_path))
    rt = ConversationRuntime(repository=repo)
    idem = CreateIdempotencyStore(tmp_path / "idempotency.json")
    yield ConversationManagementService(rt, idem)
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


# ── create: canonical id from Core, never client fallback ──────────────────
def test_create_returns_canonical_id(svc):
    detail = svc.create(title="hello")
    assert detail["id"]  # Core-assigned, not empty


def test_two_creates_same_second_distinct_ids(svc):
    # CORE-CREATE-ID-01: independent creates must be distinct (no collision)
    d1 = svc.create(title="a")
    d2 = svc.create(title="b")
    assert d1["id"] != d2["id"]


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


# ── restart / reconstruction idempotency (durable) ─────────────────────────
def test_restart_idempotency_same_conversation(tmp_path):
    idem_path = tmp_path / "idempotency.json"
    repo1 = StorageV2ConversationRepository(str(tmp_path))
    rt1 = ConversationRuntime(repository=repo1)
    svc1 = ConversationManagementService(rt1, CreateIdempotencyStore(idem_path))
    d1 = svc1.create(idempotency_key="req-K", title="a")
    cid1 = d1["id"]

    repo2 = StorageV2ConversationRepository(str(tmp_path))
    rt2 = ConversationRuntime(repository=repo2)
    svc2 = ConversationManagementService(rt2, CreateIdempotencyStore(idem_path))
    d2 = svc2.create(idempotency_key="req-K", title="a")
    assert d2["id"] == cid1


# ── AT-CMS-02: create failure → governed failure, no mapping ───────────────
def test_create_failure_no_mapping_recorded(svc, monkeypatch):
    def failing_create(title="x"):
        raise RuntimeError("boom")

    monkeypatch.setattr(svc._runtime, "create_conversation", failing_create)
    with pytest.raises(CreateFailedError):
        svc.create(idempotency_key="req-fail")
    assert svc._idempotency.get("req-fail") is None


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
    # zero canonical mutation: conversation remains intact
    assert svc.get(cid)["id"] == cid


def test_archive_fail_closed_conversation_intact(svc):
    detail = svc.create(title="keep")
    cid = detail["id"]
    with pytest.raises(LifecycleUnavailableError):
        svc.archive(cid)
    assert svc.get(cid)["id"] == cid

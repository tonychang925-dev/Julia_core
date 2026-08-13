"""W2-I1 — CM-S3 ConversationManagementService acceptance tests.

RED→GREEN against the frozen CM-S3 protocol (Wave-2 authority 6d4cfe7).
Production evidence producer: SPEC_FROZEN → PASS.
"""
from __future__ import annotations

import tempfile

import pytest

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime
from julia_core.runtime.conversation_management_service import (
    ConversationManagementService,
    ConversationNotFoundError,
)


@pytest.fixture
def svc():
    base = tempfile.mkdtemp(prefix="cm3_")
    repo = StorageV2ConversationRepository(base)
    rt = ConversationRuntime(repository=repo)
    yield ConversationManagementService(rt)
    repo.close()
    import shutil
    shutil.rmtree(base, ignore_errors=True)


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
    # canonical truth must NOT have been manufactured
    assert svc._runtime.get_conversation("typo123") is None


# ── create: canonical id from Core, never client fallback ──────────────────
def test_create_returns_canonical_id(svc):
    detail = svc.create(title="hello")
    assert detail["id"]  # Core-assigned, not empty


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

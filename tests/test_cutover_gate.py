"""CM-S1D-R1 — Core governed cutover gate tests (RED→GREEN against S1D §1/§3).

FREEZE drains in-flight writers then disables write acceptance; AUTHORIZE
registers candidate + evidence and issues the one-shot permit; ACTIVATE is
gated by the Core-issued permit; enable writes requires the commit receipt.
A fabricated permit cannot bypass VERIFY (AT-CUT-R1-02).
"""
from __future__ import annotations

import pytest

from julia_core.runtime.conversation_runtime import (
    ConversationRuntime,
    CutoverActivationPermit,
    CutoverConflictError,
    CUTOVER_PENDING_COMMIT,
)


class _Repo:
    """Minimal ConversationRepository-shaped stub for identity comparison."""

    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f"_Repo({self.name})"


def _authorize(rt, cutover_id="c1", candidate=None, digest="d1"):
    return rt.authorize_verified(
        cutover_id=cutover_id,
        candidate_repository=candidate,
        verification_digest=digest,
        freeze_boundary_id="b1",
        reconciliation_evidence_id="r1",
    )


# ── FREEZE: drain + disable write acceptance, repository unchanged ───────
def test_freeze_disables_write_acceptance():
    legacy = _Repo("legacy")
    rt = ConversationRuntime(repository=legacy)
    ack = rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    assert ack.write_acceptance == "DISABLED"
    assert rt.repository is legacy  # repository unchanged during freeze
    with pytest.raises(CutoverConflictError):
        rt._assert_canonical_write_allowed()


def test_freeze_expected_active_mismatch_blocked():
    legacy = _Repo("legacy")
    other = _Repo("other")
    rt = ConversationRuntime(repository=legacy)
    with pytest.raises(CutoverConflictError):
        rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=other)


# ── AUTHORIZE: Core-issued permit (caller cannot fabricate) ──────────────
def test_authorize_verified_issues_permit():
    legacy = _Repo("legacy")
    seg = _Repo("seg")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    permit = _authorize(rt, candidate=seg)
    assert permit.cutover_id == "c1"
    assert permit.verification_digest == "d1"


# ── AT-CUT-R1-02: fabricated permit cannot bypass VERIFY ─────────────────
def test_activate_without_authorize_blocked():
    legacy = _Repo("legacy")
    seg = _Repo("seg")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    fake = CutoverActivationPermit(
        cutover_id="c1", freeze_epoch="", source_binding_epoch=0,
        candidate_binding_id="seg", reconciliation_evidence_id="r1",
        freeze_boundary_id="b1", verification_digest="d1", issued_at="",
    )
    with pytest.raises(CutoverConflictError):
        rt.activate_repository_cutover(
            cutover_id="c1", candidate_repository=seg, activation_permit=fake,
        )


# ── ACTIVATE: one atomic switch gated by Core-issued permit ──────────────
def test_activate_atomic_switch():
    legacy = _Repo("legacy")
    seg = _Repo("seg")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    permit = _authorize(rt, candidate=seg)
    record = rt.activate_repository_cutover(
        cutover_id="c1", candidate_repository=seg, activation_permit=permit,
    )
    assert rt.repository is seg
    assert record.new_binding_epoch == 1
    assert record.commit_receipt
    # writes STILL disabled after switch (PENDING_COMMIT, crash window)
    with pytest.raises(CutoverConflictError):
        rt._assert_canonical_write_allowed()


def test_activate_candidate_mismatch_blocked():
    legacy = _Repo("legacy")
    seg = _Repo("seg")
    other = _Repo("other")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    permit = _authorize(rt, candidate=seg)
    with pytest.raises(CutoverConflictError):
        rt.activate_repository_cutover(
            cutover_id="c1", candidate_repository=other, activation_permit=permit,
        )


# ── AT-CUT-R1-03: direct enable (no activate) → BLOCKED ──────────────────
def test_enable_requires_commit_receipt():
    legacy = _Repo("legacy")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    with pytest.raises(CutoverConflictError):
        rt.enable_canonical_writes(commit_receipt="bogus")


def test_enable_after_activate():
    legacy = _Repo("legacy")
    seg = _Repo("seg")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    permit = _authorize(rt, candidate=seg)
    record = rt.activate_repository_cutover(
        cutover_id="c1", candidate_repository=seg, activation_permit=permit,
    )
    rt.enable_canonical_writes(commit_receipt=record.commit_receipt)
    rt._assert_canonical_write_allowed()  # writes re-enabled


def test_enable_wrong_receipt_blocked():
    legacy = _Repo("legacy")
    seg = _Repo("seg")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    permit = _authorize(rt, candidate=seg)
    rt.activate_repository_cutover(
        cutover_id="c1", candidate_repository=seg, activation_permit=permit,
    )
    with pytest.raises(CutoverConflictError):
        rt.enable_canonical_writes(commit_receipt="wrong-receipt")


# ── AT-CUT-R1-04: crash before commit → writes remain disabled ───────────
def test_crash_before_commit_writes_disabled():
    legacy = _Repo("legacy")
    seg = _Repo("seg")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    permit = _authorize(rt, candidate=seg)
    rt.activate_repository_cutover(
        cutover_id="c1", candidate_repository=seg, activation_permit=permit,
    )
    # switched but no durable commit → writes still disabled (fail-closed)
    assert rt._cutover_phase == CUTOVER_PENDING_COMMIT
    with pytest.raises(CutoverConflictError):
        rt._begin_canonical_write()


# ── AT-CUT-R1-01: FREEZE drains in-flight writers before returning ───────
def test_freeze_drains_inflight_writers():
    import threading
    import time

    legacy = _Repo("legacy")
    rt = ConversationRuntime(repository=legacy)
    rt._begin_canonical_write()  # an in-flight canonical writer

    ack = {}

    def do_freeze():
        ack["ack"] = rt.freeze_repository_cutover(
            cutover_id="c1", expected_active_repository=legacy,
        )

    t = threading.Thread(target=do_freeze)
    t.start()
    time.sleep(0.05)  # give freeze a chance to block on the drain
    assert t.is_alive()  # freeze is waiting for the in-flight writer

    rt._end_canonical_write()  # writer completes
    t.join(timeout=2.0)
    assert not t.is_alive()  # freeze returned after drain
    assert ack["ack"].write_acceptance == "DISABLED"
    with pytest.raises(CutoverConflictError):
        rt._begin_canonical_write()  # no new writers after freeze


# ── source_repository provenance (P1: source ≠ candidate name) ───────────
def test_source_repository_provenance():
    class LegacyRepo(_Repo):
        pass

    class SegRepo(_Repo):
        pass

    legacy = LegacyRepo("legacy")
    seg = SegRepo("seg")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    permit = rt.authorize_verified(
        cutover_id="c1", candidate_repository=seg, verification_digest="d1",
        freeze_boundary_id="b1", reconciliation_evidence_id="r1",
    )
    record = rt.activate_repository_cutover(
        cutover_id="c1", candidate_repository=seg, activation_permit=permit,
    )
    assert record.source_repository == "LegacyRepo"      # source is legacy
    assert record.activated_repository == "SegRepo"      # activated is candidate

"""CM-S1D — Core governed cutover gate tests (RED→GREEN against S1D §1/§3).

FREEZE disables canonical write acceptance without switching the repository;
ACTIVATE performs one atomic Legacy→Segmented switch gated by a one-shot
CutoverActivationPermit. configure_conversation_runtime keeps raising
ConversationCutoverRequired on direct different-repo rebind (AT-CUT-09).
"""
from __future__ import annotations

import pytest

from julia_core.runtime.conversation_runtime import (
    ConversationRuntime,
    CutoverActivationPermit,
    CutoverConflictError,
)


class _Repo:
    """Minimal ConversationRepository-shaped stub for identity comparison."""

    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f"_Repo({self.name})"


def _permit(cutover_id: str = "c1") -> CutoverActivationPermit:
    return CutoverActivationPermit(
        cutover_id=cutover_id,
        freeze_epoch="e1",
        source_binding_epoch=0,
        candidate_binding_id="seg",
        reconciliation_evidence_id="r1",
        freeze_boundary_id="b1",
        verification_digest="d1",
        issued_at="2026-08-13T00:00:00Z",
    )


# ── FREEZE: write acceptance DISABLED, repository unchanged ───────────────
def test_freeze_disables_write_acceptance():
    legacy = _Repo("legacy")
    rt = ConversationRuntime(repository=legacy)
    ack = rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    assert ack.write_acceptance == "DISABLED"
    assert ack.cutover_id == "c1"
    assert rt.repository is legacy  # repository unchanged during freeze


def test_freeze_expected_active_mismatch_blocked():
    legacy = _Repo("legacy")
    other = _Repo("other")
    rt = ConversationRuntime(repository=legacy)
    with pytest.raises(CutoverConflictError):
        rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=other)


def test_write_gate_reject_after_freeze():
    legacy = _Repo("legacy")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    with pytest.raises(CutoverConflictError):
        rt._assert_canonical_write_allowed()


# ── ACTIVATE: one atomic switch Legacy → Segmented ────────────────────────
def test_activate_atomic_switch():
    legacy = _Repo("legacy")
    seg = _Repo("seg")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    record = rt.activate_repository_cutover(
        cutover_id="c1",
        expected_active_repository=legacy,
        candidate_repository=seg,
        activation_permit=_permit("c1"),
    )
    assert rt.repository is seg
    assert record.new_binding_epoch == 1
    # write acceptance STILL disabled after switch (crash window)
    with pytest.raises(CutoverConflictError):
        rt._assert_canonical_write_allowed()


# ── ACTIVATE without freeze → BLOCKED (AT-CUT-01) ─────────────────────────
def test_activate_without_freeze_blocked():
    legacy = _Repo("legacy")
    seg = _Repo("seg")
    rt = ConversationRuntime(repository=legacy)
    with pytest.raises(CutoverConflictError):
        rt.activate_repository_cutover(
            cutover_id="c1",
            expected_active_repository=legacy,
            candidate_repository=seg,
            activation_permit=_permit("c1"),
        )


def test_permit_wrong_cutover_blocked():
    legacy = _Repo("legacy")
    seg = _Repo("seg")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    with pytest.raises(CutoverConflictError):
        rt.activate_repository_cutover(
            cutover_id="c1",
            expected_active_repository=legacy,
            candidate_repository=seg,
            activation_permit=_permit("other"),  # permit does not belong to c1
        )


def test_activate_candidate_equals_current_blocked():
    legacy = _Repo("legacy")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    with pytest.raises(CutoverConflictError):
        rt.activate_repository_cutover(
            cutover_id="c1",
            expected_active_repository=legacy,
            candidate_repository=legacy,  # candidate == current
            activation_permit=_permit("c1"),
        )


# ── enable writes after activation commit ─────────────────────────────────
def test_enable_writes_after_activation():
    legacy = _Repo("legacy")
    seg = _Repo("seg")
    rt = ConversationRuntime(repository=legacy)
    rt.freeze_repository_cutover(cutover_id="c1", expected_active_repository=legacy)
    rt.activate_repository_cutover(
        cutover_id="c1",
        expected_active_repository=legacy,
        candidate_repository=seg,
        activation_permit=_permit("c1"),
    )
    rt.enable_canonical_writes()
    rt._assert_canonical_write_allowed()  # no exception → writes re-enabled

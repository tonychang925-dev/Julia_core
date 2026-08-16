"""DIA-3 R1 — ReflectionTrigger Core Contract tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.reflection_trigger import (
    EVIDENCE_DIGEST_FUNCTION,
    EvidenceBasis,
    ReflectionTriggerSemanticPayload,
    ReflectionTriggerState,
    TriggerIdentityConflict,
    TriggerSourceRef,
)


GOLDEN_EVIDENCE_DIGEST = "d04ab1477f08957997eb09f5a29b296941215dbf52dc81e9b56cedcae6e38fe1"
GOLDEN_TRIGGER_ID = "21755f78179ebdc0b005915224bcefeb6de5cc2aca1aa4eb5c46200df3310b68"


def _payload(*, refs=None, trigger_kind="session_close", source=None):
    if refs is None:
        refs = (
            TriggerSourceRef("conversation_turn", "conv_A#turn_0001"),
            TriggerSourceRef("event", "evt_0002"),
        )
    if source is None:
        source = TriggerSourceRef("session", "session_A")
    return ReflectionTriggerSemanticPayload(
        trigger_kind=trigger_kind,
        source_ref=source,
        evidence_basis=EvidenceBasis(tuple(refs)),
    )


class FakeReflectionTriggerStateRepository:
    def __init__(self):
        self._states = {}

    def create_pending(self, state: ReflectionTriggerState) -> ReflectionTriggerState:
        existing = self._states.get(state.trigger_id)
        if existing is None:
            self._states[state.trigger_id] = state
            return state
        if existing.semantic_payload.semantic_equals(state.semantic_payload):
            return existing
        raise TriggerIdentityConflict(state.trigger_id)


# AT-DIA3-R1-01: trigger-owned SourceRef is typed opaque, not DiarySourceRef.
def test_trigger_source_ref_shape_is_owned_and_opaque():
    ref = TriggerSourceRef("conversation_turn", "conv_A#turn_0001")
    assert set(vars(ref)) == {"ref_type", "opaque_ref"}
    assert ref.ref_type == "conversation_turn"
    assert ref.opaque_ref == "conv_A#turn_0001"


# AT-DIA3-R1-02: empty and mutable source/evidence shapes are rejected.
def test_source_ref_and_evidence_validation():
    with pytest.raises(ValueError):
        TriggerSourceRef("", "x")
    with pytest.raises(ValueError):
        TriggerSourceRef("type", "")
    with pytest.raises(ValueError):
        EvidenceBasis([])
    with pytest.raises(ValueError):
        EvidenceBasis(())
    with pytest.raises(ValueError):
        EvidenceBasis(("fake",))


# AT-DIA3-R1-03: evidence_basis has canonical membership/order and frozen digest function.
def test_evidence_basis_canonical_membership_ordering_and_digest_function():
    ref_a = TriggerSourceRef("conversation_turn", "conv_A#turn_0001")
    ref_b = TriggerSourceRef("event", "evt_0002")
    basis_ab = EvidenceBasis((ref_a, ref_b))
    basis_ba = EvidenceBasis((ref_b, ref_a))

    assert basis_ab.digest_function == EVIDENCE_DIGEST_FUNCTION
    assert basis_ab.digest() == basis_ba.digest()
    assert basis_ab.digest() == GOLDEN_EVIDENCE_DIGEST
    assert basis_ab.canonical_source_refs == basis_ba.canonical_source_refs

    with pytest.raises(ValueError):
        EvidenceBasis((ref_a,), digest_function="sha1")
    with pytest.raises(ValueError):
        EvidenceBasis((ref_a, ref_a))


# AT-DIA3-R1-04: identity is SHA-256 over versioned canonical serialization.
def test_identity_golden_vector_and_canonical_bytes():
    payload = _payload()
    canonical = payload.canonical_bytes().decode("utf-8")

    assert payload.identity() == GOLDEN_TRIGGER_ID
    assert len(payload.identity()) == 64
    assert "payload.domain" in canonical
    assert "julia_core.reflection_trigger.identity.v1" in canonical
    assert "payload.version" in canonical
    assert "dia3-reflection-trigger-v1" in canonical
    assert "13:session_close" in canonical


# AT-DIA3-R1-05: triggered_at is audit-only, excluded from identity and exact retry equality.
def test_triggered_at_is_audit_only():
    payload = _payload()
    first = ReflectionTriggerState.pending(payload, triggered_at="2026-08-16T00:00:00Z")
    retry = ReflectionTriggerState.pending(payload, triggered_at="2026-08-16T00:05:00Z")

    assert first.trigger_id == retry.trigger_id == GOLDEN_TRIGGER_ID
    assert first.triggered_at != retry.triggered_at
    assert first.exact_retry_equals(retry)


# AT-DIA3-R1-06: causal identity changes with semantic payload changes.
def test_identity_changes_when_semantic_payload_changes():
    base = _payload()
    changed_kind = _payload(trigger_kind="manual")
    changed_source = _payload(source=TriggerSourceRef("manual_request", "req_1"))
    changed_evidence = _payload(refs=(TriggerSourceRef("event", "evt_9999"),))

    assert base.identity() != changed_kind.identity()
    assert base.identity() != changed_source.identity()
    assert base.identity() != changed_evidence.identity()
    assert not base.semantic_equals(changed_kind)


# AT-DIA3-R1-07: state must use identity-derived id and pending status.
def test_state_invariants():
    payload = _payload()
    state = ReflectionTriggerState.pending(payload, triggered_at="2026-08-16T00:00:00Z")
    assert state.status == "pending"
    assert state.trigger_id == payload.identity()

    with pytest.raises(ValueError):
        ReflectionTriggerState("wrong", payload, "2026-08-16T00:00:00Z")
    with pytest.raises(ValueError):
        ReflectionTriggerState.pending(payload, triggered_at="")
    with pytest.raises(ValueError):
        ReflectionTriggerState(payload.identity(), payload, "2026-08-16T00:00:00Z", status="done")


# AT-DIA3-R1-08: create_pending absent/idempotent/conflict semantics.
def test_repository_create_pending_contract_absent_idempotent_conflict():
    repo = FakeReflectionTriggerStateRepository()
    payload = _payload()
    first = ReflectionTriggerState.pending(payload, triggered_at="2026-08-16T00:00:00Z")
    retry = ReflectionTriggerState.pending(payload, triggered_at="2026-08-16T00:05:00Z")

    assert repo.create_pending(first) is first
    assert repo.create_pending(retry) is first

    conflicting = ReflectionTriggerState(
        trigger_id=first.trigger_id,
        semantic_payload=payload,
        triggered_at="2026-08-16T00:06:00Z",
    )
    object.__setattr__(conflicting, "semantic_payload", _payload(trigger_kind="manual"))
    with pytest.raises(TriggerIdentityConflict):
        repo.create_pending(conflicting)
    assert repo._states[first.trigger_id] is first


# AT-DIA3-R1-09: static boundary — no DiarySourceRef, filesystem, provider, Memory/Context dependencies.
def test_static_boundary_no_forbidden_dependencies():
    root = Path(__file__).resolve().parents[2] / "julia_core" / "reflection_trigger"
    src = "\n".join(path.read_text() for path in sorted(root.glob("*.py")))
    for forbidden in (
        "from julia_core.diary",
        "import julia_core.diary",
        "pathlib",
        "import os",
        "from os",
        "sqlite3",
        "requests",
        "httpx",
        "julia_core.memory",
        "julia_core.context_os",
    ):
        assert forbidden not in src, f"reflection_trigger must not depend on {forbidden}"

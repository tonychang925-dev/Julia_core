"""DIA-3 R1.1 — ReflectionTrigger Core Contract tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.reflection_trigger import (
    CANONICAL_VERSION,
    EVIDENCE_DIGEST_FUNCTION,
    ActivityWindowAnchor,
    BoundedSchedulingState,
    EligibilityBoundary,
    EvidenceBasis,
    OpportunityKey,
    PendingOpportunity,
    QuietWindowAnchor,
    ReflectionOpportunity,
    SingleEventAnchor,
    TriggerIdentityConflict,
    TriggerKind,
    TriggerPolicy,
    TriggerReason,
    TriggerSourceRef,
)


GOLDEN_EVIDENCE_AB = "9cb3cdde6c820e68cea2f8b5293bdcc4d7c94480a751bb115c47034c485d8b10"
GOLDEN_EVIDENCE_BA = "568f80b8e94623c05637906a7b2a1ae9d66a0546b9161f4d62c592c183a8c49d"
GOLDEN_SINGLE_ID = "75a32cd8d2cfc442417cd9bd44b9c60aa6053f145d81eaa86f611a1f1defd90b"
GOLDEN_ACTIVITY_ID = "b47dc1eca890e4b0d8d5f7b634a49a1de83405731fce90f00179b9a35848eb6c"
GOLDEN_QUIET_ID = "97662f903bb5c0e0a3cfeeb265b27f613cb362b6c9ab2b45517bd50958015919"


def _refs():
    return (TriggerSourceRef("event", "evt_A"), TriggerSourceRef("event", "evt_B"))


def _evidence(refs=None):
    return EvidenceBasis(tuple(refs or _refs()))


def _reason():
    return (TriggerReason("turn-boundary", "assistant response completed"),)


def _single_key(**overrides):
    base = dict(
        schema_version=CANONICAL_VERSION,
        conversation_id="conv_A",
        policy_revision="policy-r1",
        trigger_kind=TriggerKind.TURN_BOUNDARY,
        causal_anchor=SingleEventAnchor("evt_B", _evidence()),
    )
    base.update(overrides)
    return OpportunityKey(**base)


def _activity_key(**overrides):
    base = dict(
        schema_version=CANONICAL_VERSION,
        conversation_id="conv_A",
        policy_revision="policy-r1",
        trigger_kind=TriggerKind.ACTIVITY_WINDOW,
        causal_anchor=ActivityWindowAnchor(
            "evt_A",
            EligibilityBoundary("evt_C", "activity-closed"),
            _evidence(),
        ),
    )
    base.update(overrides)
    return OpportunityKey(**base)


def _quiet_key(**overrides):
    base = dict(
        schema_version=CANONICAL_VERSION,
        conversation_id="conv_A",
        policy_revision="policy-r1",
        trigger_kind=TriggerKind.QUIET_WINDOW,
        causal_anchor=QuietWindowAnchor("evt_B", "quiet-10m-after-evt_B", _evidence()),
    )
    base.update(overrides)
    return OpportunityKey(**base)


def _opportunity(key=None, *, reasons=None, refs=None):
    return ReflectionOpportunity(
        opportunity_key=key or _single_key(),
        source_refs=tuple(refs or _refs()),
        reasons=tuple(reasons or _reason()),
    )


class FakeReflectionTriggerStateRepository:
    def __init__(self):
        self._states = {}

    def create_pending(self, state: PendingOpportunity) -> PendingOpportunity:
        existing = self._states.get(state.opportunity_id)
        if existing is None:
            self._states[state.opportunity_id] = state
            return state
        if existing.opportunity.semantic_equals(state.opportunity):
            return existing
        raise TriggerIdentityConflict(state.opportunity_id)


# AT-DIA3-R1-01: trigger-owned SourceRef is typed opaque.
def test_trigger_source_ref_shape_is_owned_and_opaque():
    ref = TriggerSourceRef("event", "evt_A")
    assert set(vars(ref)) == {"ref_type", "opaque_ref"}
    assert ref.ref_type == "event"
    assert ref.opaque_ref == "evt_A"


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


# AT-DIA3-R1-03/16: evidence_basis preserves canonical event order, never sorts.
def test_evidence_basis_preserves_canonical_event_order_and_frozen_digest_function():
    ref_a, ref_b = _refs()
    basis_ab = EvidenceBasis((ref_a, ref_b))
    basis_ba = EvidenceBasis((ref_b, ref_a))

    assert basis_ab.digest_function == EVIDENCE_DIGEST_FUNCTION
    assert basis_ab.source_refs == (ref_a, ref_b)
    assert basis_ba.source_refs == (ref_b, ref_a)
    assert basis_ab.digest() == GOLDEN_EVIDENCE_AB
    assert basis_ba.digest() == GOLDEN_EVIDENCE_BA
    assert basis_ab.digest() != basis_ba.digest()

    with pytest.raises(ValueError):
        EvidenceBasis((ref_a,), digest_function="sha1")
    with pytest.raises(ValueError):
        EvidenceBasis((ref_a, ref_a))


# AT-DIA3-R1-04: OpportunityKey identity is SHA-256 over frozen canonical bytes.
def test_opportunity_key_golden_vectors_and_canonical_bytes():
    single = _single_key()
    activity = _activity_key()
    quiet = _quiet_key()
    canonical = single.canonical_bytes().decode("utf-8")

    assert single.opportunity_id() == GOLDEN_SINGLE_ID
    assert activity.opportunity_id() == GOLDEN_ACTIVITY_ID
    assert quiet.opportunity_id() == GOLDEN_QUIET_ID
    assert len(single.opportunity_id()) == 64
    assert "opportunity.domain" in canonical
    assert "julia_core.reflection_trigger.opportunity_key.v1" in canonical
    assert "opportunity.schema_version" in canonical
    assert "opportunity.conversation_id" in canonical
    assert "opportunity.policy_revision" in canonical
    assert "opportunity.trigger_kind" in canonical
    assert "opportunity.causal_anchor" in canonical


# AT-DIA3-R1-05/20: triggered_at-only retry is idempotent and preserves first durable audit value.
def test_triggered_at_only_retry_is_idempotent_and_preserves_first_audit_timestamp():
    repo = FakeReflectionTriggerStateRepository()
    opportunity = _opportunity()
    first = PendingOpportunity.pending(opportunity, triggered_at="2026-08-16T00:00:00Z")
    retry = PendingOpportunity.pending(opportunity, triggered_at="2026-08-16T00:05:00Z")

    assert first.opportunity_id == retry.opportunity_id == GOLDEN_SINGLE_ID
    assert first.triggered_at != retry.triggered_at
    assert first.exact_retry_equals(retry)
    assert repo.create_pending(first) is first
    assert repo.create_pending(retry) is first
    assert repo.create_pending(retry).triggered_at == "2026-08-16T00:00:00Z"


# AT-DIA3-R1-06/08: state invariants and bounded scheduling noun exist.
def test_pending_opportunity_and_bounded_scheduling_invariants():
    opportunity = _opportunity()
    pending = PendingOpportunity.pending(opportunity, triggered_at="2026-08-16T00:00:00Z")
    assert pending.status == "pending"
    assert pending.opportunity_id == opportunity.opportunity_id
    assert BoundedSchedulingState((pending,), max_pending=1).pending == (pending,)

    with pytest.raises(ValueError):
        PendingOpportunity("wrong", opportunity, "2026-08-16T00:00:00Z")
    with pytest.raises(ValueError):
        PendingOpportunity.pending(opportunity, triggered_at="")
    with pytest.raises(ValueError):
        PendingOpportunity(opportunity.opportunity_id, opportunity, "2026-08-16T00:00:00Z", status="done")
    with pytest.raises(ValueError):
        BoundedSchedulingState((pending, pending), max_pending=1)


# AT-DIA3-R1-08: create_pending absent/idempotent/conflict semantics.
def test_repository_create_pending_contract_absent_idempotent_conflict():
    repo = FakeReflectionTriggerStateRepository()
    first = PendingOpportunity.pending(_opportunity(), triggered_at="2026-08-16T00:00:00Z")
    retry = PendingOpportunity.pending(_opportunity(), triggered_at="2026-08-16T00:05:00Z")

    assert repo.create_pending(first) is first
    assert repo.create_pending(retry) is first

    conflicting_opportunity = _opportunity(reasons=(TriggerReason("different-reason"),))
    conflicting = PendingOpportunity.pending(conflicting_opportunity, triggered_at="2026-08-16T00:06:00Z")
    object.__setattr__(conflicting, "opportunity_id", first.opportunity_id)
    with pytest.raises(TriggerIdentityConflict):
        repo.create_pending(conflicting)
    assert repo._states[first.opportunity_id] is first


# AT-DIA3-R1-09/19: static boundary — no authority imports or physical implementation dependencies.
def test_static_boundary_no_forbidden_dependencies_or_truth_authority():
    root = Path(__file__).resolve().parents[2] / "julia_core" / "reflection_trigger"
    src = "\n".join(path.read_text() for path in sorted(root.glob("*.py")))
    for forbidden in (
        "DiarySourceRef",
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
        "promote_to_memory",
        "append_accepted",
    ):
        assert forbidden not in src, f"reflection_trigger must not depend on {forbidden}"
    opportunity = _opportunity()
    assert set(vars(opportunity)) == {"opportunity_key", "source_refs", "reasons", "opportunity_id"}


# AT-DIA3-R1-10: TriggerKind exactly four members.
def test_trigger_kind_exactly_four_members():
    assert tuple(kind.name for kind in TriggerKind) == (
        "TURN_BOUNDARY",
        "QUIET_WINDOW",
        "ACTIVITY_WINDOW",
        "EXPLICIT_REFLECTION_REQUEST",
    )
    assert tuple(kind.value for kind in TriggerKind) == (
        "TURN_BOUNDARY",
        "QUIET_WINDOW",
        "ACTIVITY_WINDOW",
        "EXPLICIT_REFLECTION_REQUEST",
    )


# AT-DIA3-R1-11: arbitrary trigger kind impossible.
def test_arbitrary_trigger_kind_impossible():
    with pytest.raises(ValueError):
        TriggerKind("manual")
    with pytest.raises(ValueError):
        _single_key(trigger_kind="manual")


# AT-DIA3-R1-12: same causal data + different conversation_id -> different opportunity_id.
def test_conversation_id_enters_identity():
    assert _single_key(conversation_id="conv_A").opportunity_id() != _single_key(conversation_id="conv_B").opportunity_id()


# AT-DIA3-R1-13: same data + different policy_revision -> different opportunity_id.
def test_policy_revision_enters_identity():
    assert _single_key(policy_revision="policy-r1").opportunity_id() != _single_key(policy_revision="policy-r2").opportunity_id()


# AT-DIA3-R1-14: activity eligibility boundary differs -> different opportunity_id.
def test_activity_eligibility_boundary_enters_identity():
    base = _activity_key()
    changed = _activity_key(
        causal_anchor=ActivityWindowAnchor(
            "evt_A",
            EligibilityBoundary("evt_D", "activity-closed"),
            _evidence(),
        )
    )
    assert base.opportunity_id() != changed.opportunity_id()


# AT-DIA3-R1-15: activity evidence set differs -> different opportunity_id.
def test_activity_evidence_basis_enters_identity():
    base = _activity_key()
    changed = _activity_key(
        causal_anchor=ActivityWindowAnchor(
            "evt_A",
            EligibilityBoundary("evt_C", "activity-closed"),
            EvidenceBasis((TriggerSourceRef("event", "evt_A"), TriggerSourceRef("event", "evt_C"))),
        )
    )
    assert base.opportunity_id() != changed.opportunity_id()


# AT-DIA3-R1-17: quiet boundary differs -> different opportunity_id.
def test_quiet_boundary_enters_identity():
    assert _quiet_key().opportunity_id() != _quiet_key(
        causal_anchor=QuietWindowAnchor("evt_B", "quiet-30m-after-evt_B", _evidence())
    ).opportunity_id()


# AT-DIA3-R1-18: all three CausalAnchor variants serialize distinctly.
def test_causal_anchor_variants_serialize_distinctly():
    single = SingleEventAnchor("evt_B", _evidence()).canonical_bytes()
    activity = ActivityWindowAnchor("evt_A", EligibilityBoundary("evt_C", "activity-closed"), _evidence()).canonical_bytes()
    quiet = QuietWindowAnchor("evt_B", "quiet-10m-after-evt_B", _evidence()).canonical_bytes()
    assert b"single_event" in single
    assert b"activity_window" in activity
    assert b"quiet_window" in quiet
    assert len({single, activity, quiet}) == 3


# Contract completeness: ReflectionOpportunity and TriggerPolicy nouns validate exact types.
def test_reflection_opportunity_and_trigger_policy_contracts():
    policy = TriggerPolicy("policy-r1")
    key = _single_key(schema_version=policy.schema_version, policy_revision=policy.policy_revision)
    opportunity = _opportunity(key)
    assert opportunity.opportunity_id == key.opportunity_id()
    assert opportunity.opportunity_key.conversation_id == "conv_A"
    assert opportunity.source_refs == _refs()
    assert opportunity.reasons == _reason()

    with pytest.raises(ValueError):
        TriggerPolicy("policy-r1", enabled_kinds=("manual",))
    with pytest.raises(ValueError):
        ReflectionOpportunity(key, [], _reason())
    with pytest.raises(ValueError):
        ReflectionOpportunity(key, _refs(), ("not-reason",))

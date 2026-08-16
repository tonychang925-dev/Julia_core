"""DIA-3 R1.2 — ReflectionTrigger Core Contract tests."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from julia_core.reflection_trigger import (
    CANONICAL_VERSION,
    EVIDENCE_DIGEST_FUNCTION,
    ActiveWindowState,
    ActivityWindowAnchor,
    BoundedSchedulingState,
    DeliveryTombstone,
    DeterministicTimerEligibilityBoundary,
    EventEligibilityBoundary,
    EvidenceBasis,
    OpportunityKey,
    PendingOpportunity,
    QuietWindowAnchor,
    RecentDedupKey,
    ReflectionOpportunity,
    SchedulingCursor,
    SingleEventAnchor,
    TriggerIdentityConflict,
    TriggerKind,
    TriggerPolicy,
    TriggerReason,
    TriggerSourceRef,
)


GOLDEN_EVIDENCE_AB = "9cb3cdde6c820e68cea2f8b5293bdcc4d7c94480a751bb115c47034c485d8b10"
GOLDEN_EVIDENCE_BA = "568f80b8e94623c05637906a7b2a1ae9d66a0546b9161f4d62c592c183a8c49d"
GOLDEN_SINGLE_ID = "ec1cc74bb7c07450714555453cd5943828c47385209c57440a6aaa854d6d4123"
GOLDEN_ACTIVITY_ID = "c870ebece165b24c77ec758c7ce48ec6f49a7d46d8a944b5b6c3f9ae24127af3"
GOLDEN_QUIET_ID = "175b8861e8b1d342a3048ff0e16eda56a8f5ce669fe4881f34da97966ef47aa0"
GOLDEN_TIMER_ACTIVITY_ID = "d382582781ce8ee11519bd5e78b6e1adec9d200336684af992dfa7bd79c324d5"


def _refs():
    return (TriggerSourceRef("event", "evt_A"), TriggerSourceRef("event", "evt_B"))


def _evidence(refs=None):
    return EvidenceBasis(tuple(refs or _refs()))


def _policy():
    return TriggerPolicy("policy-r1", cooldown=timedelta(minutes=2), window=timedelta(minutes=30), quiet_threshold=timedelta(minutes=10))


def _reason(kind=TriggerKind.TURN_BOUNDARY, refs=None):
    return (TriggerReason(kind, tuple(refs or (TriggerSourceRef("event", "evt_B"),))),)


def _single_key(**overrides):
    policy = _policy()
    base = dict(
        schema_version=CANONICAL_VERSION,
        conversation_id="conv_A",
        policy_revision=policy.revision,
        trigger_kind=TriggerKind.TURN_BOUNDARY,
        causal_anchor=SingleEventAnchor("evt_B"),
    )
    base.update(overrides)
    return OpportunityKey(**base)


def _activity_key(**overrides):
    policy = _policy()
    base = dict(
        schema_version=CANONICAL_VERSION,
        conversation_id="conv_A",
        policy_revision=policy.revision,
        trigger_kind=TriggerKind.ACTIVITY_WINDOW,
        causal_anchor=ActivityWindowAnchor(
            "evt_A",
            EventEligibilityBoundary("evt_C"),
            _evidence(),
        ),
    )
    base.update(overrides)
    return OpportunityKey(**base)


def _quiet_key(**overrides):
    policy = _policy()
    base = dict(
        schema_version=CANONICAL_VERSION,
        conversation_id="conv_A",
        policy_revision=policy.revision,
        trigger_kind=TriggerKind.QUIET_WINDOW,
        causal_anchor=QuietWindowAnchor("evt_B", "quiet-10m-after-evt_B"),
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
    timer_activity = _activity_key(
        causal_anchor=ActivityWindowAnchor(
            "evt_A",
            DeterministicTimerEligibilityBoundary("activity-timer-boundary-001"),
            _evidence(),
        )
    )
    canonical = single.canonical_bytes().decode("utf-8")

    assert single.opportunity_id() == GOLDEN_SINGLE_ID
    assert activity.opportunity_id() == GOLDEN_ACTIVITY_ID
    assert quiet.opportunity_id() == GOLDEN_QUIET_ID
    assert timer_activity.opportunity_id() == GOLDEN_TIMER_ACTIVITY_ID
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
    active = ActiveWindowState("evt_A", _evidence())
    state = BoundedSchedulingState(
        cursor=SchedulingCursor("evt_B"),
        active_window=active,
        recent_dedup=(RecentDedupKey(pending.opportunity_id),),
        pending=(pending,),
        delivery_tombstones=(DeliveryTombstone(pending.opportunity_id, "2026-08-16T00:01:00Z"),),
        max_recent_dedup=1,
        max_pending=1,
        max_delivery_tombstones=1,
    )
    assert pending.status == "pending"
    assert pending.opportunity_id == opportunity.opportunity_id
    assert state.cursor.last_seen_event_id == "evt_B"
    assert state.active_window == active

    with pytest.raises(ValueError):
        PendingOpportunity("wrong", opportunity, "2026-08-16T00:00:00Z")
    with pytest.raises(ValueError):
        PendingOpportunity.pending(opportunity, triggered_at="")
    with pytest.raises(ValueError):
        PendingOpportunity(opportunity.opportunity_id, opportunity, "2026-08-16T00:00:00Z", status="done")
    with pytest.raises(ValueError):
        BoundedSchedulingState(SchedulingCursor(), None, (), (pending, pending), (), max_pending=1)


# AT-DIA3-R1-08: create_pending absent/idempotent/conflict semantics.
def test_repository_create_pending_contract_absent_idempotent_conflict():
    repo = FakeReflectionTriggerStateRepository()
    first = PendingOpportunity.pending(_opportunity(), triggered_at="2026-08-16T00:00:00Z")
    retry = PendingOpportunity.pending(_opportunity(), triggered_at="2026-08-16T00:05:00Z")

    assert repo.create_pending(first) is first
    assert repo.create_pending(retry) is first

    conflicting_opportunity = _opportunity(
        reasons=(
            TriggerReason(TriggerKind.TURN_BOUNDARY, (TriggerSourceRef("event", "evt_B"),)),
            TriggerReason(TriggerKind.EXPLICIT_REFLECTION_REQUEST, (TriggerSourceRef("event", "evt_A"),)),
        )
    )
    conflicting = PendingOpportunity.pending(conflicting_opportunity, triggered_at="2026-08-16T00:06:00Z")
    object.__setattr__(conflicting, "opportunity_id", first.opportunity_id)
    with pytest.raises(TriggerIdentityConflict):
        repo.create_pending(conflicting)
    assert repo._states[first.opportunity_id] is first


# AT-RT-X2-01: reason evidence outside opportunity.source_refs is rejected at construction.
def test_x2_reason_evidence_must_be_contained_in_opportunity_sources():
    key = _single_key()
    with pytest.raises(ValueError):
        ReflectionOpportunity(
            opportunity_key=key,
            source_refs=(TriggerSourceRef("event", "evt_B"),),
            reasons=(TriggerReason(TriggerKind.TURN_BOUNDARY, (TriggerSourceRef("event", "evt_Y"),)),),
        )


# AT-RT-X2-02: OpportunityKey primary trigger kind must be represented by at least one reason.
def test_x2_primary_trigger_kind_must_be_explained_by_reason():
    key = _single_key(trigger_kind=TriggerKind.TURN_BOUNDARY)
    with pytest.raises(ValueError):
        ReflectionOpportunity(
            opportunity_key=key,
            source_refs=(TriggerSourceRef("event", "evt_B"),),
            reasons=(TriggerReason(TriggerKind.EXPLICIT_REFLECTION_REQUEST, (TriggerSourceRef("event", "evt_B"),)),),
        )


# AT-RT-X2-03: mixed structural reasons are allowed when one matches primary kind and all evidence is visible.
def test_x2_mixed_reasons_allowed_when_primary_kind_and_evidence_subset_hold():
    key = _single_key(trigger_kind=TriggerKind.TURN_BOUNDARY)
    opportunity = ReflectionOpportunity(
        opportunity_key=key,
        source_refs=_refs(),
        reasons=(
            TriggerReason(TriggerKind.TURN_BOUNDARY, (TriggerSourceRef("event", "evt_B"),)),
            TriggerReason(TriggerKind.EXPLICIT_REFLECTION_REQUEST, (TriggerSourceRef("event", "evt_A"),)),
        ),
    )
    assert opportunity.opportunity_id == GOLDEN_SINGLE_ID


# AT-RT-X2-04: Activity source_refs must exactly mirror EvidenceBasis refs.
def test_x2_activity_source_refs_must_equal_evidence_basis_refs():
    key = _activity_key()
    with pytest.raises(ValueError):
        ReflectionOpportunity(
            opportunity_key=key,
            source_refs=(TriggerSourceRef("event", "evt_A"), TriggerSourceRef("event", "evt_B"), TriggerSourceRef("event", "evt_C")),
            reasons=(TriggerReason(TriggerKind.ACTIVITY_WINDOW, (TriggerSourceRef("event", "evt_A"),)),),
        )


# AT-RT-X2-05: Activity same refs but different order is rejected.
def test_x2_activity_source_refs_order_must_match_evidence_basis_order():
    key = _activity_key()
    ref_a, ref_b = _refs()
    with pytest.raises(ValueError):
        ReflectionOpportunity(
            opportunity_key=key,
            source_refs=(ref_b, ref_a),
            reasons=(TriggerReason(TriggerKind.ACTIVITY_WINDOW, (ref_a,)),),
        )


# AT-RT-X2-06: contradictory first-write path is rejected before create_pending can persist it.
def test_x2_contradictory_first_write_rejected_before_repository_create_pending():
    repo = FakeReflectionTriggerStateRepository()
    with pytest.raises(ValueError):
        contradictory = ReflectionOpportunity(
            opportunity_key=_single_key(trigger_kind=TriggerKind.TURN_BOUNDARY, causal_anchor=SingleEventAnchor("evt_B")),
            source_refs=(TriggerSourceRef("event", "evt_X"),),
            reasons=(TriggerReason(TriggerKind.EXPLICIT_REFLECTION_REQUEST, (TriggerSourceRef("event", "evt_Y"),)),),
        )
        repo.create_pending(PendingOpportunity.pending(contradictory, triggered_at="2026-08-16T00:00:00Z"))
    assert repo._states == {}


# AT-DIA3-R1-09/19: static boundary — no authority imports or semantic interpretation fields.
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
        "relationship_breakthrough",
        "emotionally_significant",
        "reason_code",
        "reason.detail",
        "boundary_reason",
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


# AT-DIA3-R1-11: arbitrary trigger kind and reason semantic strings impossible.
def test_arbitrary_trigger_kind_and_reason_semantic_string_impossible():
    with pytest.raises(ValueError):
        TriggerKind("manual")
    with pytest.raises(ValueError):
        _single_key(trigger_kind="manual")
    with pytest.raises(TypeError):
        TriggerReason(reason_code="emotionally_significant", detail="relationship breakthrough")
    with pytest.raises(ValueError):
        TriggerReason("emotionally_significant", (TriggerSourceRef("event", "evt_B"),))


# R1.2: TriggerReason must carry non-empty canonical evidence refs and reject duplicates.
def test_trigger_reason_structural_only_with_canonical_evidence_refs():
    ref = TriggerSourceRef("event", "evt_B")
    reason = TriggerReason(TriggerKind.TURN_BOUNDARY, (ref,))
    assert set(vars(reason)) == {"kind", "evidence_refs"}
    assert reason.kind is TriggerKind.TURN_BOUNDARY
    assert reason.evidence_refs == (ref,)
    assert b"TURN_BOUNDARY" in reason.canonical_bytes()
    assert b"evt_B" in reason.canonical_bytes()
    with pytest.raises(ValueError):
        TriggerReason(TriggerKind.TURN_BOUNDARY, ())
    with pytest.raises(ValueError):
        TriggerReason(TriggerKind.TURN_BOUNDARY, [ref])
    with pytest.raises(ValueError):
        TriggerReason(TriggerKind.TURN_BOUNDARY, (ref, ref))


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
            EventEligibilityBoundary("evt_D"),
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
            EventEligibilityBoundary("evt_C"),
            EvidenceBasis((TriggerSourceRef("event", "evt_A"), TriggerSourceRef("event", "evt_C"))),
        )
    )
    assert base.opportunity_id() != changed.opportunity_id()


# AT-DIA3-R1-17: quiet boundary differs -> different opportunity_id.
def test_quiet_boundary_enters_identity():
    assert _quiet_key().opportunity_id() != _quiet_key(
        causal_anchor=QuietWindowAnchor("evt_B", "quiet-30m-after-evt_B")
    ).opportunity_id()


# AT-DIA3-R1-18: all three CausalAnchor variants serialize distinctly.
def test_causal_anchor_variants_serialize_distinctly():
    single = SingleEventAnchor("evt_B").canonical_bytes()
    activity = ActivityWindowAnchor("evt_A", EventEligibilityBoundary("evt_C"), _evidence()).canonical_bytes()
    quiet = QuietWindowAnchor("evt_B", "quiet-10m-after-evt_B").canonical_bytes()
    assert b"single_event" in single
    assert b"activity_window" in activity
    assert b"quiet_window" in quiet
    assert len({single, activity, quiet}) == 3


# R1.2: Single and Quiet identity are not over-bound to mutable evidence projections.
def test_single_and_quiet_identity_not_over_bound_to_evidence_projection():
    base_single = _single_key(causal_anchor=SingleEventAnchor("evt_B"))
    richer_projection_single = _single_key(causal_anchor=SingleEventAnchor("evt_B"))
    assert base_single.opportunity_id() == richer_projection_single.opportunity_id()

    base_quiet = _quiet_key(causal_anchor=QuietWindowAnchor("evt_B", "quiet-10m-after-evt_B"))
    richer_projection_quiet = _quiet_key(causal_anchor=QuietWindowAnchor("evt_B", "quiet-10m-after-evt_B"))
    assert base_quiet.opportunity_id() == richer_projection_quiet.opportunity_id()

    with pytest.raises(TypeError):
        SingleEventAnchor("evt_B", _evidence())
    with pytest.raises(TypeError):
        QuietWindowAnchor("evt_B", "quiet-10m-after-evt_B", _evidence())


# R1.2: Eligibility boundary has event/timer shapes; actual timer wake wall-clock is not a field.
def test_eligibility_event_boundary_and_deterministic_timer_boundary_are_distinct():
    event = EventEligibilityBoundary("evt_C")
    timer = DeterministicTimerEligibilityBoundary("activity-timer-boundary-001")
    assert event.canonical_bytes() != timer.canonical_bytes()
    assert b"event" in event.canonical_bytes()
    assert b"deterministic_timer" in timer.canonical_bytes()
    assert set(vars(timer)) == {"deterministic_activity_boundary_id"}
    assert not hasattr(timer, "wake_at")
    assert _activity_key(causal_anchor=ActivityWindowAnchor("evt_A", event, _evidence())).opportunity_id() != _activity_key(
        causal_anchor=ActivityWindowAnchor("evt_A", timer, _evidence())
    ).opportunity_id()


# AT-DIA3-R1-T1/T5: TriggerPolicy exposes duration semantics, not event-count fields.
def test_trigger_policy_exposes_duration_semantics_and_no_event_count_fields():
    policy = _policy()
    assert set(vars(policy)) == {
        "revision",
        "cooldown",
        "window",
        "quiet_threshold",
        "schema_version",
    }
    assert policy.revision == "policy-r1"
    assert policy.schema_version == CANONICAL_VERSION
    assert policy.cooldown == timedelta(minutes=2)
    assert policy.window == timedelta(minutes=30)
    assert policy.quiet_threshold == timedelta(minutes=10)
    assert not hasattr(policy, "cooldown_event_count")
    assert not hasattr(policy, "activity_window_event_count")
    assert not hasattr(policy, "quiet_threshold_event_count")
    with pytest.raises(TypeError):
        TriggerPolicy("policy-r1", cooldown_event_count=2, activity_window_event_count=3, quiet_threshold_event_count=10)


# AT-DIA3-R1-T2: negative cooldown rejected.
def test_trigger_policy_negative_cooldown_rejected():
    with pytest.raises(ValueError):
        TriggerPolicy("policy-r1", timedelta(seconds=-1), timedelta(minutes=30), timedelta(minutes=10))


# AT-DIA3-R1-T3: zero/non-positive window rejected.
def test_trigger_policy_non_positive_window_rejected():
    with pytest.raises(ValueError):
        TriggerPolicy("policy-r1", timedelta(0), timedelta(0), timedelta(minutes=10))
    with pytest.raises(ValueError):
        TriggerPolicy("policy-r1", timedelta(0), timedelta(seconds=-1), timedelta(minutes=10))


# AT-DIA3-R1-T4: zero/non-positive quiet_threshold rejected.
def test_trigger_policy_non_positive_quiet_threshold_rejected():
    with pytest.raises(ValueError):
        TriggerPolicy("policy-r1", timedelta(0), timedelta(minutes=30), timedelta(0))
    with pytest.raises(ValueError):
        TriggerPolicy("policy-r1", timedelta(0), timedelta(minutes=30), timedelta(seconds=-1))


# R1.2/R1.3: non-v1 schema versions are rejected.
def test_schema_version_must_equal_canonical_version():
    with pytest.raises(ValueError):
        _single_key(schema_version="v999")
    with pytest.raises(ValueError):
        TriggerPolicy("policy-r1", timedelta(minutes=2), timedelta(minutes=30), timedelta(minutes=10), schema_version="v999")


# Contract completeness: ReflectionOpportunity and Scheduling state validate exact types and no body field.
def test_reflection_opportunity_and_scheduling_contracts():
    policy = _policy()
    key = _single_key(schema_version=policy.schema_version, policy_revision=policy.revision)
    opportunity = _opportunity(key)
    pending = PendingOpportunity.pending(opportunity, triggered_at="2026-08-16T00:00:00Z")
    state = BoundedSchedulingState(
        cursor=SchedulingCursor(),
        active_window=None,
        recent_dedup=(RecentDedupKey(pending.opportunity_id),),
        pending=(pending,),
        delivery_tombstones=(DeliveryTombstone(pending.opportunity_id, "2026-08-16T00:01:00Z"),),
    )
    assert opportunity.opportunity_id == key.opportunity_id()
    assert opportunity.opportunity_key.conversation_id == "conv_A"
    assert opportunity.source_refs == _refs()
    assert opportunity.reasons == _reason()
    assert set(vars(state)) == {
        "cursor",
        "active_window",
        "recent_dedup",
        "pending",
        "delivery_tombstones",
        "max_recent_dedup",
        "max_pending",
        "max_delivery_tombstones",
    }
    assert "body" not in set(vars(state))

    with pytest.raises(ValueError):
        ReflectionOpportunity(key, [], _reason())
    with pytest.raises(ValueError):
        ReflectionOpportunity(key, _refs(), ("not-reason",))
    with pytest.raises(ValueError):
        BoundedSchedulingState(SchedulingCursor(), None, (RecentDedupKey("a"), RecentDedupKey("b")), (), (), max_recent_dedup=1)

"""DIA-3 R2 — Assistant-side trigger state persistence tests."""
from __future__ import annotations

import json
from datetime import timedelta

import pytest

from julia_core.reflection_trigger import (
    CANONICAL_VERSION,
    ActivityWindowAnchor,
    EventEligibilityBoundary,
    EvidenceBasis,
    FileReflectionTriggerStateRepository,
    OpportunityKey,
    PendingOpportunity,
    ReflectionOpportunity,
    ReflectionTriggerRuntimeScheduler,
    SingleEventAnchor,
    TriggerIdentityConflict,
    TriggerKind,
    TriggerPolicy,
    TriggerReason,
    TriggerSourceRef,
)


def _policy():
    return TriggerPolicy("policy-r2", timedelta(minutes=2), timedelta(minutes=30), timedelta(minutes=10))


def _single_opportunity(event_id="evt_B", *, conversation_id="conv_A"):
    event_ref = TriggerSourceRef("event", event_id)
    extra_ref = TriggerSourceRef("conversation", "turn_1")
    key = OpportunityKey(
        CANONICAL_VERSION,
        conversation_id,
        _policy().revision,
        TriggerKind.TURN_BOUNDARY,
        SingleEventAnchor(event_id),
    )
    return ReflectionOpportunity(
        opportunity_key=key,
        source_refs=(event_ref, extra_ref),
        reasons=(TriggerReason(TriggerKind.TURN_BOUNDARY, (event_ref,)),),
    )


def _activity_opportunity():
    refs = (
        TriggerSourceRef("event", "evt_A"),
        TriggerSourceRef("event", "evt_B"),
        TriggerSourceRef("event", "evt_C"),
    )
    key = OpportunityKey(
        CANONICAL_VERSION,
        "conv_A",
        _policy().revision,
        TriggerKind.ACTIVITY_WINDOW,
        ActivityWindowAnchor("evt_A", EventEligibilityBoundary("evt_C"), EvidenceBasis(refs)),
    )
    return ReflectionOpportunity(
        opportunity_key=key,
        source_refs=refs,
        reasons=(TriggerReason(TriggerKind.ACTIVITY_WINDOW, (refs[1],)),),
    )


# AT-R2-01: absent create establishes durable pending and outbox item.
def test_create_pending_absent_creates_durable_outbox_item(tmp_path):
    repo = FileReflectionTriggerStateRepository(tmp_path)
    state = PendingOpportunity.pending(_single_opportunity(), triggered_at="2026-08-17T00:00:00Z")

    created = repo.create_pending(state)

    assert created.exact_retry_equals(state)
    assert created.triggered_at == "2026-08-17T00:00:00Z"
    assert repo.get_pending(state.opportunity_id).exact_retry_equals(state)
    assert [item.opportunity_id for item in repo.list_outbox()] == [state.opportunity_id]
    assert (tmp_path / "pending" / f"{state.opportunity_id}.json").exists()


# AT-R2-02: restart reloads the exact same canonical opportunity semantics.
def test_restart_reload_preserves_semantics_and_first_triggered_at(tmp_path):
    repo = FileReflectionTriggerStateRepository(tmp_path)
    original = PendingOpportunity.pending(_single_opportunity(), triggered_at="2026-08-17T00:00:00Z")
    repo.create_pending(original)

    restarted = FileReflectionTriggerStateRepository(tmp_path)
    loaded = restarted.get_pending(original.opportunity_id)

    assert loaded is not None
    assert loaded.exact_retry_equals(original)
    assert loaded.triggered_at == "2026-08-17T00:00:00Z"
    assert loaded.opportunity.canonical_bytes() == original.opportunity.canonical_bytes()


# AT-R2-03: exact retry is idempotent and preserves first durable audit timestamp.
def test_exact_retry_idempotent_preserves_first_durable_timestamp(tmp_path):
    repo = FileReflectionTriggerStateRepository(tmp_path)
    opportunity = _single_opportunity()
    first = PendingOpportunity.pending(opportunity, triggered_at="2026-08-17T00:00:00Z")
    retry = PendingOpportunity.pending(opportunity, triggered_at="2026-08-17T00:10:00Z")

    repo.create_pending(first)
    result = repo.create_pending(retry)

    assert result.exact_retry_equals(first)
    assert result.triggered_at == "2026-08-17T00:00:00Z"
    assert len(repo.list_outbox()) == 1


# AT-R2-04: same id + different semantic payload fails closed before overwrite.
def test_same_id_different_payload_fails_closed_without_overwrite(tmp_path):
    repo = FileReflectionTriggerStateRepository(tmp_path)
    first = PendingOpportunity.pending(_single_opportunity(), triggered_at="2026-08-17T00:00:00Z")
    repo.create_pending(first)
    conflicting_opportunity = _single_opportunity(event_id="evt_X")
    conflicting = PendingOpportunity.pending(conflicting_opportunity, triggered_at="2026-08-17T00:01:00Z")
    object.__setattr__(conflicting, "opportunity_id", first.opportunity_id)

    with pytest.raises(TriggerIdentityConflict):
        repo.create_pending(conflicting)

    loaded = repo.get_pending(first.opportunity_id)
    assert loaded is not None
    assert loaded.opportunity.semantic_equals(first.opportunity)


# AT-R2-05: scheduler facade does not alter opportunity id or semantic bytes.
def test_runtime_scheduler_preserves_core_semantics(tmp_path):
    repo = FileReflectionTriggerStateRepository(tmp_path)
    scheduler = ReflectionTriggerRuntimeScheduler(repo)
    opportunity = _activity_opportunity()

    pending = scheduler.schedule(opportunity, triggered_at="2026-08-17T00:00:00Z")

    assert pending.opportunity_id == opportunity.opportunity_id
    assert pending.opportunity.canonical_bytes() == opportunity.canonical_bytes()
    assert scheduler.outbox()[0].opportunity_id == opportunity.opportunity_id


# AT-R2-06: delivery ack removes item from outbox across restart but preserves tombstone idempotency.
def test_delivery_ack_excludes_outbox_across_restart_and_is_idempotent(tmp_path):
    repo = FileReflectionTriggerStateRepository(tmp_path)
    scheduler = ReflectionTriggerRuntimeScheduler(repo)
    pending = scheduler.schedule(_single_opportunity(), triggered_at="2026-08-17T00:00:00Z")

    scheduler.ack(pending.opportunity_id, delivered_at="2026-08-17T00:01:00Z", ack_id="ack_1")
    scheduler.ack(pending.opportunity_id, delivered_at="2026-08-17T00:02:00Z", ack_id="ack_1")

    restarted = ReflectionTriggerRuntimeScheduler(FileReflectionTriggerStateRepository(tmp_path))
    assert restarted.outbox() == []
    with pytest.raises(TriggerIdentityConflict):
        restarted.ack(pending.opportunity_id, delivered_at="2026-08-17T00:03:00Z", ack_id="ack_2")


# AT-R2-07: compaction removes acked pending record without losing delivery tombstone.
def test_compaction_removes_acked_pending_but_keeps_tombstone(tmp_path):
    repo = FileReflectionTriggerStateRepository(tmp_path)
    pending = repo.create_pending(PendingOpportunity.pending(_single_opportunity(), triggered_at="2026-08-17T00:00:00Z"))
    repo.mark_delivery_ack(pending.opportunity_id, delivered_at="2026-08-17T00:01:00Z", ack_id="ack_1")

    removed = repo.compact()

    assert removed == 1
    assert not (tmp_path / "pending" / f"{pending.opportunity_id}.json").exists()
    assert (tmp_path / "acked" / f"{pending.opportunity_id}.json").exists()
    assert repo.list_outbox() == []


# AT-R2-08: acked exact retry stays non-deliverable after restart.
def test_acked_exact_retry_does_not_reenter_outbox(tmp_path):
    repo = FileReflectionTriggerStateRepository(tmp_path)
    opportunity = _single_opportunity()
    pending = repo.create_pending(PendingOpportunity.pending(opportunity, triggered_at="2026-08-17T00:00:00Z"))
    repo.mark_delivery_ack(pending.opportunity_id, delivered_at="2026-08-17T00:01:00Z", ack_id="ack_1")
    repo.compact()

    restarted = FileReflectionTriggerStateRepository(tmp_path)
    retry = restarted.create_pending(PendingOpportunity.pending(opportunity, triggered_at="2026-08-17T00:10:00Z"))

    assert retry.exact_retry_equals(pending)
    assert retry.triggered_at == "2026-08-17T00:00:00Z"
    assert restarted.list_outbox() == []


# AT-R2-09: corrupted canonical record fails closed on restart/read.
def test_corrupted_record_fails_closed(tmp_path):
    repo = FileReflectionTriggerStateRepository(tmp_path)
    pending = repo.create_pending(PendingOpportunity.pending(_single_opportunity(), triggered_at="2026-08-17T00:00:00Z"))
    path = tmp_path / "pending" / f"{pending.opportunity_id}.json"
    data = json.loads(path.read_text())
    data["opportunity"]["source_refs"][0]["opaque_ref"] = "evt_CORRUPT"
    path.write_text(json.dumps(data))

    restarted = FileReflectionTriggerStateRepository(tmp_path)
    with pytest.raises(ValueError):
        restarted.get_pending(pending.opportunity_id)


# AT-R2-10: outbox ordering is deterministic by first durable triggered_at then id.
def test_outbox_order_is_deterministic(tmp_path):
    repo = FileReflectionTriggerStateRepository(tmp_path)
    late = repo.create_pending(PendingOpportunity.pending(_single_opportunity("evt_Z", conversation_id="conv_Z"), triggered_at="2026-08-17T00:02:00Z"))
    early = repo.create_pending(PendingOpportunity.pending(_single_opportunity("evt_B", conversation_id="conv_A"), triggered_at="2026-08-17T00:01:00Z"))

    assert [item.opportunity_id for item in repo.list_outbox()] == [early.opportunity_id, late.opportunity_id]

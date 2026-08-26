"""C1-R2.8 Action / Trace semantics contracts.

Protected contracts: C-12 / C-08 / C-03 / REV2 R2-I05/R2-I06/R2-I13
Expected baseline: PASS for current operational ActionRuntime staying scoped to
per-turn progress display and trace-only cognition helpers excluding provider
visible/debug leakage; XFAIL for canonical C-12 Action and Trace correlation
objects not yet implemented.
Known gaps: C-12 §5/§7/§8 migration debt; runtime/action.py is operational
progress, not canonical external-effect Action; event_trace.py is a debugging
timeline, not the C-12 correlation graph.
Resolving phase: R2-P1 / R2-P2 / R2-P7.

TC-ID: C1-R2.8-ACTION-001 C-12 Action is distinct from read-only CapabilityCall
TC-ID: C1-R2.8-ACTION-002 operational progress is not canonical C-12 Action
TC-ID: C1-R2.8-ACTION-003 external-effect Action lifecycle includes UNKNOWN and no blind retry
TC-ID: C1-R2.8-TRACE-001 Trace correlates request/call/evidence/context/generation/message
TC-ID: C1-R2.8-TRACE-002 Trace must not depend on hidden chain-of-thought
TC-ID: C1-R2.8-TRACE-003 Trace failure must not rewrite business/action truth

These tests intentionally do not invent provider reachability or native streaming
wire facts. They pin C-12 semantics before production migration.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

import pytest

from julia_core.conversation_cognition.trace import (
    CognitionTrace,
    MeaningValidationTrace,
    UnderstandingTrace,
)
from julia_core.runtime import action as runtime_action
from julia_core.runtime.action import ActionPhase, ActionRuntime
from julia_core.runtime.event_trace import EventTrace


def _dataclass_fields(cls: type[Any]) -> set[str]:
    assert is_dataclass(cls), f"{cls!r} must be a dataclass contract object"
    return {f.name for f in fields(cls)}


# ── Existing boundary guards ─────────────────────────────────────────────────


def test_operational_action_runtime_is_scoped_to_progress_not_external_effect_truth():
    """TC-ID: C1-R2.8-ACTION-002. Current ActionRuntime is only UI/progress state."""
    runtime = ActionRuntime()

    started = runtime.start("read_file", "reading fixture", correlation_id="turn-1")
    assert started.phase == ActionPhase.STARTED
    assert runtime.current_for("turn-1") is started

    runtime.finish("read complete", correlation_id="turn-1")
    assert runtime.current_for("turn-1") is None
    assert runtime.last_action is started
    assert started.phase == ActionPhase.COMPLETED

    # Operational progress has no canonical C-12 external-effect identifiers.
    assert not hasattr(started, "action_id")
    assert not hasattr(started, "capability_call_id")
    assert not hasattr(started, "idempotency_key")
    assert not hasattr(started, "external_effect_status")


def test_runtime_action_phase_does_not_claim_c12_action_lifecycle():
    """TC-ID: C1-R2.8-ACTION-002. Progress phases must not be mistaken for C-12 lifecycle."""
    assert issubclass(ActionPhase, Enum)
    assert set(ActionPhase.__members__) == {"STARTED", "IN_PROGRESS", "COMPLETED", "FAILED"}
    assert "UNKNOWN" not in ActionPhase.__members__
    assert "AUTHORIZED" not in ActionPhase.__members__
    assert "CANCELLED" not in ActionPhase.__members__


def test_cognition_trace_excludes_provider_visible_debug_and_final_response():
    """TC-ID: C1-R2.8-TRACE-002. Debug/cognition trace must not become provider-visible output."""
    trace = CognitionTrace(
        user_message="fixture",
        understanding=UnderstandingTrace(literal="fixture", state="UNDERSTOOD"),
        meaning_validation=MeaningValidationTrace(provider_visible=False),
    )

    trace.assert_trace_only()
    payload = trace.to_dict()["cognition_trace"]
    assert payload["final_response"] is None
    assert payload["provider_request"] is None
    assert payload["meaning_validation"]["provider_visible"] is False


def test_event_trace_records_observable_events_without_hidden_reasoning_requirement():
    """TC-ID: C1-R2.8-TRACE-002. Existing event trace is observable timeline, not CoT storage."""
    trace = EventTrace(session_id="sess-c1-r2-8")
    trace.record("capability.requested", {"capability_request_id": "cap_req_1"})
    trace.record("capability.completed", {"capability_call_id": "cap_call_1", "status": "success"})

    summary = trace.summary()
    assert "capability.requested" in summary
    assert "capability.completed" in summary

    rendered_events = str(trace.events).lower()
    forbidden = {"chain_of_thought", "hidden_reasoning", "scratchpad", "private_reasoning"}
    assert forbidden.isdisjoint(rendered_events.split())


# ── Expected gaps: C-12 canonical objects and correlation graph ──────────────


@pytest.mark.xfail(
    strict=True,
    reason="C-12 §5: canonical external-effect Action object is not implemented; runtime/action.py is operational progress only; pending R2-P7",
)
def test_c12_action_object_is_distinct_from_capability_call_and_read_only_tool_observation():
    """TC-ID: C1-R2.8-ACTION-001. Action represents externally meaningful effect, not read-only calls."""
    Action = getattr(runtime_action, "C12Action")
    action_fields = _dataclass_fields(Action)

    assert {"action_id", "capability_call_id", "lifecycle", "idempotency_key", "external_effect_status"} <= action_fields
    assert "structured_output" not in action_fields
    assert "evidence_refs" in action_fields

    read_only = Action(
        action_id="act_read_fixture",
        capability_call_id="cap_call_read_fixture",
        lifecycle="SUCCEEDED",
        external_effect_status="NONE",
        idempotency_key="idem-read-fixture",
        evidence_refs=("ev_tool_observation",),
    )
    assert read_only.external_effect_status == "NONE"
    assert read_only.action_id != read_only.capability_call_id


@pytest.mark.xfail(
    strict=True,
    reason="C-12 §5/§6: canonical ActionLifecycle lacks UNKNOWN/AUTHORIZED/CANCELLED and no-blind-retry policy object; pending R2-P7",
)
def test_c12_action_lifecycle_includes_unknown_and_no_blind_retry_contract():
    """TC-ID: C1-R2.8-ACTION-003. Unknown side-effect state must block blind retry."""
    ActionLifecycle = getattr(runtime_action, "ActionLifecycle")
    assert issubclass(ActionLifecycle, Enum)
    assert {"PLANNED", "AUTHORIZED", "STARTED", "SUCCEEDED", "FAILED", "UNKNOWN", "CANCELLED"} <= set(ActionLifecycle.__members__)

    RetryPolicy = getattr(runtime_action, "ActionRetryPolicy")
    policy_fields = _dataclass_fields(RetryPolicy)
    assert {"requires_verification_before_retry", "idempotency_required", "unknown_blocks_blind_retry"} <= policy_fields


@pytest.mark.xfail(
    strict=True,
    reason="C-12 §8: canonical Trace correlation graph object is not implemented; current EventTrace is a debug timeline; pending R2-P7",
)
def test_c12_trace_correlates_request_call_evidence_context_generation_and_message():
    """TC-ID: C1-R2.8-TRACE-001. Trace graph must join all execution artifacts."""
    trace_module = __import__("julia_core.runtime.event_trace", fromlist=["ExecutionTrace"])
    ExecutionTrace = getattr(trace_module, "ExecutionTrace")
    trace_fields = _dataclass_fields(ExecutionTrace)

    required = {
        "trace_id",
        "conversation_id",
        "turn_id",
        "generation_id",
        "context_package_id",
        "capability_request_id",
        "capability_call_id",
        "evidence_ids",
        "action_ids",
        "conversation_message_id",
        "provider",
        "model",
        "fallback_from",
        "fallback_reason",
    }
    assert required <= trace_fields


@pytest.mark.xfail(
    strict=True,
    reason="C-12 §7/§15: trace privacy/redaction contract is not first-class yet; pending R2-P7",
)
def test_trace_contract_excludes_hidden_cot_and_secret_payloads_by_schema():
    """TC-ID: C1-R2.8-TRACE-002. Trace schema must exclude CoT and require redaction metadata."""
    trace_module = __import__("julia_core.runtime.event_trace", fromlist=["ExecutionTrace"])
    ExecutionTrace = getattr(trace_module, "ExecutionTrace")
    trace_fields = _dataclass_fields(ExecutionTrace)

    forbidden = {"chain_of_thought", "hidden_reasoning", "scratchpad", "private_provider_reasoning", "raw_credentials"}
    assert forbidden.isdisjoint(trace_fields)
    assert {"redaction_policy", "sensitivity_class", "retention_policy"} <= trace_fields


@pytest.mark.xfail(
    strict=True,
    reason="C-12 §16: trace persistence failure semantics are not modeled separately from business/action truth; pending R2-P7",
)
def test_trace_storage_failure_does_not_rewrite_business_or_action_truth():
    """TC-ID: C1-R2.8-TRACE-003. Trace write failure must not mean action did not happen."""
    trace_module = __import__("julia_core.runtime.event_trace", fromlist=["TraceWriteResult"])
    TraceWriteResult = getattr(trace_module, "TraceWriteResult")
    fields_ = _dataclass_fields(TraceWriteResult)

    assert {"trace_id", "write_status", "error", "business_truth_unchanged", "action_truth_unchanged"} <= fields_

    result = TraceWriteResult(
        trace_id="trace_fixture",
        write_status="failed",
        error="disk unavailable",
        business_truth_unchanged=True,
        action_truth_unchanged=True,
    )
    assert result.write_status == "failed"
    assert result.business_truth_unchanged is True
    assert result.action_truth_unchanged is True

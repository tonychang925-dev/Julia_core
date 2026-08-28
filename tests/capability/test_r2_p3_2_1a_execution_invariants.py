"""R2-P3.2.1A CapabilityExecution structural invariant tests.

Proves the typed carrier itself rejects impossible artifact combinations,
independently of the Manager execution spine.

Protected contracts: C-08 / C-12 / P3.2.1A invariant hardening.
"""

from __future__ import annotations

import pytest

from julia_core.capability.manager import CapabilityExecution
from julia_core.capability.models import (
    CapabilityCall,
    Evidence,
    EvidenceSourceType,
    ToolResult,
    ToolResultStatus,
)
from julia_core.capability.policy import AuthorizationDecision, AuthorizationStatus


def _decision(status: AuthorizationStatus) -> AuthorizationDecision:
    return AuthorizationDecision(decision=status, scope="fixture.scope", reason="fixture")


def _call(call_id: str) -> CapabilityCall:
    return CapabilityCall(capability_call_id=call_id, capability_request_id="req-1")


def _result(call_id: str, *, evidence_refs: tuple[str, ...] = ()) -> ToolResult:
    return ToolResult(
        capability_call_id=call_id,
        status=ToolResultStatus.SUCCESS,
        evidence_refs=evidence_refs,
    )


def _evidence(evidence_id: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref="capability:fixture.observe:provider:local",
        observed_at="2026-08-27T00:00:00Z",
        content_ref="tool_result:call-1:structured_output",
    )


# ── Valid shapes ───────────────────────────────────────────────────────────

def test_valid_authorization_only_shape():
    carrier = CapabilityExecution(_decision(AuthorizationStatus.DENY), None, None, ())
    assert carrier.capability_call is None
    assert carrier.tool_result is None
    assert carrier.evidence == ()


def test_valid_execution_shape_with_exact_evidence():
    call = _call("call-1")
    evidence = _evidence("ev-1")
    result = _result("call-1", evidence_refs=("ev-1",))
    carrier = CapabilityExecution(_decision(AuthorizationStatus.ALLOW), call, result, (evidence,))
    assert carrier.tool_result.capability_call_id == call.capability_call_id
    assert tuple(e.evidence_id for e in carrier.evidence) == ("ev-1",)


def test_valid_execution_success_without_evidence():
    call = _call("call-1")
    result = _result("call-1", evidence_refs=())
    CapabilityExecution(_decision(AuthorizationStatus.ALLOW), call, result, ())


# ── Invalid shapes ─────────────────────────────────────────────────────────

def test_invalid_all_fields_absent():
    with pytest.raises(ValueError):
        CapabilityExecution(None, None, None, ())


def test_invalid_non_allow_with_call():
    with pytest.raises(ValueError):
        CapabilityExecution(_decision(AuthorizationStatus.DENY), _call("call-1"), None, ())


def test_invalid_non_allow_with_result():
    with pytest.raises(ValueError):
        CapabilityExecution(_decision(AuthorizationStatus.DENY), None, _result("call-1"), ())


def test_invalid_non_allow_with_evidence():
    with pytest.raises(ValueError):
        CapabilityExecution(_decision(AuthorizationStatus.DENY), None, None, (_evidence("ev-1"),))


def test_invalid_allow_without_call():
    with pytest.raises(ValueError):
        CapabilityExecution(_decision(AuthorizationStatus.ALLOW), None, None, ())


def test_invalid_allow_call_without_result():
    with pytest.raises(ValueError):
        CapabilityExecution(_decision(AuthorizationStatus.ALLOW), _call("call-1"), None, ())


def test_invalid_mismatched_call_id():
    with pytest.raises(ValueError):
        CapabilityExecution(_decision(AuthorizationStatus.ALLOW), _call("call-1"), _result("call-2"), ())


def test_invalid_evidence_from_other_result():
    call = _call("call-1")
    result = _result("call-1", evidence_refs=("ev-1",))
    with pytest.raises(ValueError):
        CapabilityExecution(_decision(AuthorizationStatus.ALLOW), call, result, (_evidence("ev-other"),))

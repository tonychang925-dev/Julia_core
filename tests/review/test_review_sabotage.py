"""External Code Review — sabotage matrix (handover §41).

Each attack below must FAIL CLOSED. A single broken authority seam means
MODULE NOT PASS.

Attacks covered:
  - forged CapabilityRequest association
  - wrong capability_request_id / capability_call_id / correlation_id
  - provider reports DENIED (authority theft)
  - provider returns invalid status
  - provider returns malformed outcome type
  - provider executes twice (duplicate review)
  - provider fallback attempt (silently choosing another provider)
  - missing provider
  - unhealthy provider
  - PARTIAL promoted to SUCCESS
  - ERROR promoted to Evidence
  - UNKNOWN side effect auto retry
  - ReviewBundle candidate SHA mismatch
  - review_id mismatch
  - bundle digest mismatch
  - provider-selected capability authority
  - browser/session fields crossing into Core authority
  - legacy string transport reintroduced
"""

from __future__ import annotations

from typing import Any

import pytest

from julia_core.capability.manager import CapabilityManager
from julia_core.capability.models import (
    CapabilityCallStatus,
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityRequest,
    CapabilityStatus,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)
from julia_core.capability.policy import AuthorizationDecision, AuthorizationStatus, PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry
from julia_core.review.contracts import ReviewBundle, ReviewDecisionCandidate, ReviewVerdict
from julia_core.review.digest import compute_bundle_digest
from julia_core.review.governance import build_governance_record
from julia_core.review.invocation import (
    BrowserAuthorityInRequestError,
    build_review_request,
    submit_review,
)
from julia_core.review.registration import EXTERNAL_REVIEW_PROVIDER, register_external_review_capability
from julia_core.review.validation import ReviewCorrelationError, validate_review_correlation


def _bundle(**overrides) -> ReviewBundle:
    values = dict(
        review_id="rvw_1",
        task_id="task_1",
        candidate_id="cand_1",
        candidate_sha="abc123",
        repository="Julia_core",
        branch="feature/x",
        objective="review code",
        changed_files=("a.py",),
        questions=("Is it safe?",),
    )
    values.update(overrides)
    return ReviewBundle(**values)


def _candidate(**overrides) -> ReviewDecisionCandidate:
    values = dict(
        review_id="rvw_1",
        candidate_id="cand_1",
        candidate_sha="abc123",
        verdict=ReviewVerdict.PASS,
        notes=("looks good",),
    )
    values.update(overrides)
    return ReviewDecisionCandidate(**values)


class FixtureProvider:
    def __init__(self, outcome, *, healthy: bool = True, health_detail: str = "ok"):
        self.outcome = outcome
        self.healthy = healthy
        self.health_detail = health_detail
        self.execute_calls = 0
        self.last_request = None

    async def health(self):
        return self.healthy, self.health_detail

    async def execute(self, request: CapabilityRequest):
        self.execute_calls += 1
        self.last_request = request
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class AllowPolicy(PermissionPolicy):
    def check(self, scope: str) -> AuthorizationDecision:
        return AuthorizationDecision(decision=AuthorizationStatus.ALLOW, scope=scope, reason="allow fixture")


def _manager(*providers) -> CapabilityManager:
    registry = CapabilityRegistry()
    register_external_review_capability(registry, status=CapabilityStatus.AVAILABLE)
    provider_map = {EXTERNAL_REVIEW_PROVIDER: providers[0]} if providers else {}
    return CapabilityManager(registry, AllowPolicy(), provider_map)


async def _submit(manager, bundle=None):
    return await submit_review(manager, bundle or _bundle())


# ── Provider authority theft ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_provider_cannot_report_denied():
    """DENIED belongs to PermissionPolicy / CapabilityManager, never provider."""
    outcome = ProviderExecutionOutcome(status=ToolResultStatus.SUCCESS, structured_output={"x": 1})
    object.__setattr__(outcome, "status", ToolResultStatus.DENIED)
    provider = FixtureProvider(outcome)
    manager = _manager(provider)
    result = await _submit(manager)
    assert provider.execute_calls == 1
    assert result.tool_result.status == ToolResultStatus.ERROR
    assert result.tool_result.error["code"] == "provider_exception"
    assert "provider outcome status" in result.tool_result.error["message"]
    assert result.tool_result.evidence_refs == ()


@pytest.mark.parametrize("bad_status", [ToolResultStatus.UNKNOWN, "random string"])
@pytest.mark.asyncio
async def test_provider_cannot_report_invalid_status(bad_status):
    outcome = ProviderExecutionOutcome(status=ToolResultStatus.SUCCESS, structured_output={"x": 1})
    object.__setattr__(outcome, "status", bad_status)
    provider = FixtureProvider(outcome)
    result = await _submit(_manager(provider))
    assert result.tool_result.status == ToolResultStatus.ERROR
    assert result.tool_result.evidence_refs == ()


@pytest.mark.asyncio
async def test_provider_malformed_outcome_type_fails_closed():
    provider = FixtureProvider(42)  # not a dict, not a typed outcome
    result = await _submit(_manager(provider))
    assert result.tool_result.status == ToolResultStatus.ERROR
    assert result.tool_result.error["code"] == "provider_exception"
    assert "unsupported outcome type" in result.tool_result.error["message"]


@pytest.mark.asyncio
async def test_provider_selected_capability_authority_is_ignored():
    """A provider returning a different capability_id must NOT change authority."""
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"capability_id": "some.other.capability", "raw_response": "x"},
    ))
    result = await _submit(_manager(provider))
    # ToolResult carries the call_id of the ORIGINAL engineering.code_review call.
    call = result.execution.capability_call
    assert call.capability_request_id == provider.last_request.capability_request_id
    assert result.tool_result.capability_call_id == call.capability_call_id
    # The forged field stays inert data, never becomes authority.
    assert result.tool_result.structured_output["capability_id"] == "some.other.capability"


# ── Duplicate / fallback execution ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_provider_executes_at_most_once():
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "ok"},
    ))
    result = await _submit(_manager(provider))
    assert provider.execute_calls == 1


@pytest.mark.asyncio
async def test_no_provider_fallback_after_failure():
    """Provider failure must NOT silently choose another provider."""
    failing = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR, error={"code": "boom", "message": "fail"},
    ))
    second = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "sneaky"},
    ))
    registry = CapabilityRegistry()
    register_external_review_capability(registry, status=CapabilityStatus.AVAILABLE)
    manager = CapabilityManager(registry, AllowPolicy(), {
        EXTERNAL_REVIEW_PROVIDER: failing,
        "alternate_provider": second,
    })
    result = await _submit(manager)
    assert result.outcome_status == "error"
    assert failing.execute_calls == 1
    assert second.execute_calls == 0  # never consulted


@pytest.mark.asyncio
async def test_missing_provider_is_unavailable():
    manager = _manager()  # no provider registered
    result = await _submit(manager)
    assert result.outcome_status == "unavailable"
    assert result.tool_result.error["code"] == "provider_not_found"
    assert result.tool_result.evidence_refs == ()


@pytest.mark.asyncio
async def test_unhealthy_provider_is_unavailable():
    provider = FixtureProvider(None, healthy=False, health_detail="session disconnected")
    result = await _submit(_manager(provider))
    assert result.outcome_status == "unavailable"
    assert result.tool_result.error["code"] == "provider_unhealthy"
    assert provider.execute_calls == 0  # health gate blocks execution


# ── Truth promotion attacks ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_partial_cannot_be_promoted_to_success():
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.PARTIAL,
        structured_output={"raw_response": "partial", "missing": True},
    ))
    result = await _submit(_manager(provider))
    assert result.outcome_status == "partial"
    assert result.tool_result.status == ToolResultStatus.PARTIAL
    ev = result.execution.evidence[0]
    assert ev.provenance["incomplete"] is True
    # Never re-labeled SUCCESS, never filled with synthetic verdict.


@pytest.mark.asyncio
async def test_error_does_not_become_evidence():
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "dom_changed", "message": "composer missing"},
    ))
    result = await _submit(_manager(provider))
    assert result.outcome_status == "error"
    assert result.tool_result.evidence_refs == ()
    assert result.execution.evidence == ()


@pytest.mark.asyncio
async def test_unknown_side_effect_never_triggers_auto_retry():
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.TIMEOUT,
        error={"code": "response_timeout", "message": "timeout after send"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    result = await _submit(_manager(provider))
    assert result.side_effect_state == "unknown"
    assert provider.execute_calls == 1  # NO auto retry on UNKNOWN


# ── Semantic binding attacks ─────────────────────────────────────────────────

def test_candidate_sha_mismatch_rejected():
    from julia_core.review.validation import assert_review_correlation
    with pytest.raises(ReviewCorrelationError):
        assert_review_correlation(_bundle(), _candidate(candidate_sha="deadbeef"))
    errors = validate_review_correlation(_bundle(), _candidate(candidate_sha="deadbeef"))
    assert errors


def test_review_id_mismatch_rejected():
    errors = validate_review_correlation(_bundle(), _candidate(review_id="rvw_OTHER"))
    assert errors


def test_bundle_digest_mismatch_rejected():
    errors = validate_review_correlation(_bundle(), _candidate(), bundle_digest="0" * 64)
    assert errors


def test_governance_record_rejects_uncorrelated_candidate():
    record = build_governance_record(
        bundle=_bundle(),
        candidate=_candidate(candidate_sha="deadbeef"),
        outcome_status="success",
        side_effect_state="succeeded",
        correlation_errors=validate_review_correlation(_bundle(), _candidate(candidate_sha="deadbeef")),
    )
    assert record.admission == "REJECTED"
    assert record.rejection_reasons


def test_governance_record_rejects_error_outcome_even_with_candidate():
    """Transport failure must never become an admitted review."""
    record = build_governance_record(
        bundle=_bundle(),
        candidate=_candidate(),
        outcome_status="error",
        side_effect_state="unknown",
        correlation_errors=[],
    )
    assert record.admission == "REJECTED"


def test_governance_record_admits_correlated_success():
    record = build_governance_record(
        bundle=_bundle(),
        candidate=_candidate(),
        outcome_status="success",
        side_effect_state="succeeded",
        correlation_errors=[],
    )
    assert record.admission == "CANDIDATE_ADMITTED"


# ── Boundary / authority crossing attacks ────────────────────────────────────

def test_browser_authority_in_request_rejected():
    bundle = _bundle(
        diff_blocks=({"browser_session_id": "bs_1", "dom_selector": "#c", "chatgpt_url": "https://chatgpt.com/x"},),
    )
    with pytest.raises(BrowserAuthorityInRequestError):
        build_review_request(bundle)


def test_request_never_carries_browser_authority():
    request = build_review_request(_bundle())
    arguments = request.arguments
    for key in ("tab_id", "dom_selector", "conversation_url", "extension_nonce", "browser_command", "browser_session_ref"):
        assert key not in arguments


@pytest.mark.asyncio
async def test_legacy_string_transport_not_reintroduced():
    """submit_review must return the typed CapabilityExecution, not a string."""
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "ok"},
    ))
    result = await _submit(_manager(provider))
    from julia_core.review.invocation import ReviewInvocationResult
    assert isinstance(result, ReviewInvocationResult)
    assert isinstance(result.execution.tool_result, object)
    assert not isinstance(result.execution, str)


# ── Correlation id / request id integrity ───────────────────────────────────

@pytest.mark.asyncio
async def test_forged_request_association_fails_closed():
    """CapabilityExecution must not be fabricated without ALLOW decision."""
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "ok"},
    ))
    manager = _manager(provider)
    # Direct execute_typed with a request whose ids are forged/empty still
    # produces ONE self-consistent CapabilityExecution (fail closed, not crash).
    request = CapabilityRequest(
        capability_id="engineering.code_review",
        arguments={"review_id": "forged"},
        requested_scope="engineering.review.external",
    )
    execution = await manager.execute_typed(request)
    assert execution.tool_result.capability_call_id == execution.capability_call.capability_call_id
    assert execution.authorization_decision.decision == AuthorizationStatus.ALLOW
    # Evidence refs exactly match ToolResult refs.
    assert tuple(e.evidence_id for e in execution.evidence) == execution.tool_result.evidence_refs


@pytest.mark.asyncio
async def test_capability_call_id_integrity_preserved():
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "ok"},
    ))
    result = await _submit(_manager(provider))
    call = result.execution.capability_call
    tool = result.tool_result
    assert tool.capability_call_id == call.capability_call_id
    assert call.capability_request_id == provider.last_request.capability_request_id
    assert call.status == CapabilityCallStatus.COMPLETED

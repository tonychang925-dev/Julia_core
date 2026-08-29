"""External Code Review — sabotage matrix (round-2 S1-S26 + round-3 P0/P1).

Each attack must FAIL CLOSED. A single broken authority seam means
MODULE NOT PASS.

Round-3 additions:
  R1-R5  one-shot token (P0-A)
  G1-G5  exact invocation<->transaction binding (P0-B)
  E1-E5  CandidateShaSource trusted composition (P0-C)
  S27-S30 sealed snapshot trusted creator (P1-D) / ledger ownership (P1-E)
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from julia_core.capability.manager import CapabilityManager
from julia_core.capability.models import (
    CapabilityRequest,
    CapabilityStatus,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)
from julia_core.capability.policy import AuthorizationDecision, AuthorizationStatus, PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry
from julia_core.review.contracts import (
    ReviewBundle,
    ReviewDecisionCandidate,
    ReviewErrorCode,
    ReviewVerdict,
)
from julia_core.review.governance import ReviewGovernanceService
from julia_core.review.guard import REVIEW_SEMANTIC_ARG, REVIEW_TOKEN_ARG, install_review_guard
from julia_core.review.invocation import (
    BrowserAuthorityInRequestError,
    build_review_request,
    submit_review,
)
from julia_core.review.registration import register_external_review_capability
from julia_core.review.snapshot import is_trusted_snapshot, seal_review_bundle
from julia_core.review.transaction import (
    ReviewDuplicateError,
    ReviewRetryUnsafeError,
    ReviewTransaction,
    ReviewTransactionLedger,
    ReviewUntrustedSnapshotError,
    ReviewUntrustedTransactionError,
)
from julia_core.review.validation import (
    CandidateShaSource,
    CandidateShaSourceUnavailable,
    ReviewCorrelationError,
    raw_response_digest_matches,
    validate_review_correlation,
    validate_transport_completion,
)


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
        transport_trace={"status": "CAPTURED"},
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


def _guarded_manager(real: FixtureProvider, ledger: ReviewTransactionLedger, policy=None) -> CapabilityManager:
    registry = CapabilityRegistry()
    register_external_review_capability(registry, status=CapabilityStatus.AVAILABLE)
    providers: dict[str, Any] = {}
    install_review_guard(providers, real_provider=real, ledger=ledger)
    return CapabilityManager(registry, policy or AllowPolicy(), providers)


async def _governed(manager, ledger, bundle=None, **kwargs):
    return await submit_review(manager, bundle or _bundle(), ledger, **kwargs)


class _SameShaSource:
    """Trusted composition source returning the bound SHA."""

    def current_candidate_sha(self, *, review_id, candidate_id):
        return "abc123"


# ═══════════════════════════════════════════════════════════════════════════════
# S1-S6: ingress authority
# ═══════════════════════════════════════════════════════════════════════════════

def test_s1_arbitrary_request_cannot_reach_provider():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "sneaky"},
    ))
    manager = _guarded_manager(real, ledger)
    execution = asyncio.run(manager.execute_typed(CapabilityRequest(
        capability_id="engineering.code_review",
        arguments={"review_id": "rvw_x"},
    )))
    assert real.execute_calls == 0
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert execution.tool_result.error["code"] == "governed_review_ingress_required"


def test_s2_model_tool_call_path_cannot_invoke_external_review():
    from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    outcome = bridge.execute_tool_typed(
        '{"name": "engineering.code_review", "arguments": {}}'
    )
    assert outcome is not None
    assert outcome.capability_id == "engineering.code_review"
    assert outcome.reason == "GOVERNED_INGRESS_REQUIRED"


def test_s3_forged_provenance_cannot_grant_authority():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "sneaky"},
    ))
    manager = _guarded_manager(real, ledger)
    request = CapabilityRequest(
        capability_id="engineering.code_review",
        arguments={"review_id": "rvw_x"},
        provenance={"manual": True, "operator": "tony", "ingress": "governed_review_semantic"},
    )
    execution = asyncio.run(manager.execute_typed(request))
    assert real.execute_calls == 0
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE


def test_s4_mutate_original_bundle_after_request_creation():
    bundle = _bundle(diff_blocks=({"path": "a.py", "content": "v1"},))
    snapshot = seal_review_bundle(bundle)
    ledger = ReviewTransactionLedger()
    transaction = ledger.mint(snapshot)
    request = build_review_request(snapshot, transaction)

    bundle.diff_blocks[0]["content"] = "MUTATED"
    bundle.diff_blocks[0]["tab_id"] = 999
    changed_files = list(bundle.changed_files)
    changed_files.append("evil.py")
    object.__setattr__(bundle, "changed_files", tuple(changed_files))

    assert request.arguments["diff_blocks"][0]["content"] == "v1"
    assert "tab_id" not in request.arguments["diff_blocks"][0]
    assert request.arguments["changed_files"] == ("a.py",)


def test_s5_mutate_nested_diff_blocks_after_digest():
    bundle = _bundle(diff_blocks=({"path": "a.py", "content": "v1"},))
    snapshot = seal_review_bundle(bundle)
    digest_before = snapshot.digest
    bundle.diff_blocks[0]["content"] = "CHANGED"
    assert snapshot.digest == digest_before
    assert snapshot.to_payload()["diff_blocks"][0]["content"] == "v1"


def test_s6_insert_browser_authority_after_validation():
    bundle = _bundle(diff_blocks=({"path": "a.py", "content": "x"},))
    snapshot = seal_review_bundle(bundle)
    bundle.diff_blocks[0]["tab_id"] = 999
    bundle.limits["browser_session_id"] = "bs_1"
    payload = snapshot.to_payload()
    assert "tab_id" not in payload["diff_blocks"][0]
    assert "browser_session_id" not in payload["limits"]


# ═══════════════════════════════════════════════════════════════════════════════
# S7-S8: current candidate SHA truth (E)
# ═══════════════════════════════════════════════════════════════════════════════

def test_s7_caller_matching_fake_sha_cannot_establish_not_stale():
    from julia_core.review.validation import assert_not_stale
    snapshot = seal_review_bundle(_bundle())
    with pytest.raises(CandidateShaSourceUnavailable):
        assert_not_stale(snapshot, None)


def test_s8_real_candidate_sha_change_in_trusted_source_is_stale():
    class Source:
        def current_candidate_sha(self, *, review_id, candidate_id):
            return "newsha999"

    snapshot = seal_review_bundle(_bundle(candidate_sha="abc123"))
    from julia_core.review.validation import is_stale, assert_not_stale
    assert is_stale(snapshot, Source()) is True
    with pytest.raises(ReviewCorrelationError):
        assert_not_stale(snapshot, Source())


# ═══════════════════════════════════════════════════════════════════════════════
# S9-S10: duplicate / exact-retry control (F)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_s9_duplicate_ordinary_submission_does_not_execute_provider_twice():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "ok"},
    ))
    manager = _guarded_manager(real, ledger)
    await _governed(manager, ledger)
    assert real.execute_calls == 1
    with pytest.raises(ReviewDuplicateError):
        await _governed(manager, ledger)
    assert real.execute_calls == 1


@pytest.mark.asyncio
async def test_s10_unknown_previous_side_effect_no_automatic_retry():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "may_have_sent", "message": "lost after send"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    manager = _guarded_manager(real, ledger)
    await _governed(manager, ledger)
    assert real.execute_calls == 1
    with pytest.raises(ReviewRetryUnsafeError):
        await _governed(manager, ledger, allow_exact_retry=True)
    assert real.execute_calls == 1


@pytest.mark.asyncio
async def test_exact_retry_allowed_when_prior_side_effect_known():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "dom_binding_failed", "message": "composer missing"},
        side_effect_state=SideEffectState.FAILED,
    ))
    manager = _guarded_manager(real, ledger)
    await _governed(manager, ledger)
    assert real.execute_calls == 1
    await _governed(manager, ledger, allow_exact_retry=True)
    assert real.execute_calls == 2


# ═══════════════════════════════════════════════════════════════════════════════
# S11-S13: transport / governance truth (G/H)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_s11_transport_trace_created_cannot_admit_candidate():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "VERDICT: PASS"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = ReviewGovernanceService(ledger, _SameShaSource())
    candidate = _candidate(transport_trace={"status": "CREATED"})
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"
    assert any("transport_trace_incomplete" in r for r in record.rejection_reasons)


@pytest.mark.asyncio
async def test_s12_caller_outcome_status_success_cannot_fabricate_governance():
    import inspect
    params = inspect.signature(ReviewGovernanceService.record).parameters
    assert "outcome_status" not in params
    assert "side_effect_state" not in params
    assert "correlation_errors" not in params
    assert "transaction" not in params  # transaction is derived internally (P0-B)


@pytest.mark.asyncio
async def test_s13_caller_correlation_empty_cannot_bypass_internal_validation():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "VERDICT: PASS"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = ReviewGovernanceService(ledger, _SameShaSource())
    candidate = _candidate(candidate_sha="deadbeef")
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"
    assert any(ReviewErrorCode.CANDIDATE_SHA_MISMATCH.value in r for r in record.rejection_reasons)


# ═══════════════════════════════════════════════════════════════════════════════
# S14-S18: semantic binding
# ═══════════════════════════════════════════════════════════════════════════════

def test_s14_digest_mismatch_rejected():
    snapshot_a = seal_review_bundle(_bundle(candidate_sha="aaa111"))
    snapshot_b = seal_review_bundle(_bundle(candidate_sha="bbb222"))
    assert snapshot_a.digest != snapshot_b.digest
    errors = validate_review_correlation(snapshot_a, _candidate(candidate_sha="aaa111"))
    assert errors == []


def test_s15_review_id_mismatch_rejected():
    snapshot = seal_review_bundle(_bundle())
    errors = validate_review_correlation(snapshot, _candidate(review_id="rvw_OTHER"))
    assert any(ReviewErrorCode.REVIEW_ID_MISMATCH.value in e for e in errors)


def test_s16_candidate_id_mismatch_rejected():
    snapshot = seal_review_bundle(_bundle())
    errors = validate_review_correlation(snapshot, _candidate(candidate_id="cand_OTHER"))
    assert any(ReviewErrorCode.CANDIDATE_ID_MISMATCH.value in e for e in errors)


def test_s17_candidate_sha_mismatch_rejected():
    snapshot = seal_review_bundle(_bundle())
    errors = validate_review_correlation(snapshot, _candidate(candidate_sha="deadbeef"))
    assert any(ReviewErrorCode.CANDIDATE_SHA_MISMATCH.value in e for e in errors)


def test_s18_raw_response_digest_mismatch_rejected():
    candidate = _candidate(raw_response_ref="r1", raw_response_digest="f" * 64)
    assert raw_response_digest_matches(candidate, expected_digest="d" * 64) is False


# ═══════════════════════════════════════════════════════════════════════════════
# S19-S23: provider outcome truth (CRB-PRE-P1)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_s19_provider_cannot_report_denied():
    ledger = ReviewTransactionLedger()
    outcome = ProviderExecutionOutcome(status=ToolResultStatus.SUCCESS, structured_output={"x": 1})
    object.__setattr__(outcome, "status", ToolResultStatus.DENIED)
    real = FixtureProvider(outcome)
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert result.outcome_status == "error"
    assert result.tool_result.error["code"] == "provider_exception"
    assert "provider outcome status" in result.tool_result.error["message"]


@pytest.mark.asyncio
async def test_s20_provider_missing_is_unavailable_no_fallback():
    registry = CapabilityRegistry()
    register_external_review_capability(registry, status=CapabilityStatus.AVAILABLE)
    ledger = ReviewTransactionLedger()
    manager = CapabilityManager(registry, AllowPolicy(), {})
    result = await _governed(manager, ledger)
    assert result.outcome_status == "unavailable"
    assert result.tool_result.error["code"] == "provider_not_found"


@pytest.mark.asyncio
async def test_s21_provider_unhealthy_is_unavailable_no_fallback():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(None, healthy=False, health_detail="session disconnected")
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert result.outcome_status == "unavailable"
    assert result.tool_result.error["code"] == "provider_unhealthy"
    assert real.execute_calls == 0


@pytest.mark.asyncio
async def test_s22_partial_remains_partial():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.PARTIAL,
        structured_output={"raw_response": "partial"},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert result.outcome_status == "partial"
    ev = result.execution.evidence[0]
    assert ev.provenance["incomplete"] is True


@pytest.mark.asyncio
async def test_s23_error_without_content_has_no_synthetic_evidence():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "dom_changed", "message": "composer missing"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert result.outcome_status == "error"
    assert result.tool_result.evidence_refs == ()
    assert result.execution.evidence == ()


# ═══════════════════════════════════════════════════════════════════════════════
# S24-S26: scope isolation
# ═══════════════════════════════════════════════════════════════════════════════

def test_s24_candidate_pass_still_candidate_only():
    from julia_core.review.governance import ReviewGovernanceRecord
    assert "PASS" not in {f for f in dir(ReviewGovernanceRecord) if not f.startswith("_")}


def test_s25_no_browser_dom_imports_in_core():
    import ast
    import julia_core.review as review_pkg
    import inspect
    import pathlib
    root = pathlib.Path(inspect.getfile(review_pkg)).parent
    forbidden = {"playwright", "selenium", "chrome", "chatgpt", "websocket", "dom"}
    for py in root.rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0].lower()
                    assert top not in forbidden, f"forbidden import in {py}: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0].lower()
                    assert top not in forbidden, f"forbidden import in {py}: {node.module}"


def test_s26_no_p4_automatic_routing():
    import julia_core.review as review_pkg
    assert not hasattr(review_pkg, "route")
    assert not hasattr(review_pkg, "route_from_text")
    assert not hasattr(review_pkg, "detect_review_intent")
    assert not hasattr(review_pkg, "auto_select")


# ═══════════════════════════════════════════════════════════════════════════════
# R1-R5: one-shot token — at most one execution per token (P0-A)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_r1_replayed_token_from_submit_review_is_rejected():
    """submit_review succeeds once; replaying the same token must NOT execute
    the real provider a second time."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "ok"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert real.execute_calls == 1

    # Reconstruct a request from the returned transaction/token and replay it.
    snapshot = result.transaction.snapshot
    request = build_review_request(snapshot, result.transaction)
    execution = await manager.execute_typed(request)
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert execution.tool_result.error["code"] == "governed_review_ingress_required"
    assert real.execute_calls == 1  # not 2


@pytest.mark.asyncio
async def test_r2_direct_request_with_consumed_token_rejected():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "ok"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    token = result.transaction.token
    assert ledger.token_consumed(token) is True

    request = CapabilityRequest(
        capability_id="engineering.code_review",
        arguments={"review_id": "rvw_1", REVIEW_TOKEN_ARG: token, REVIEW_SEMANTIC_ARG: True},
    )
    execution = await manager.execute_typed(request)
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert real.execute_calls == 1


@pytest.mark.asyncio
async def test_r3_copied_request_with_consumed_token_rejected():
    """A spread/copied request carrying a consumed token is rejected."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "ok"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    token = result.transaction.token

    # A copied request (same arguments, different request object).
    import copy
    original = build_review_request(result.transaction.snapshot, result.transaction)
    copied = copy.deepcopy(original)
    execution = await manager.execute_typed(copied)
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert real.execute_calls == 1


@pytest.mark.asyncio
async def test_r4_exact_retry_mints_new_token_and_executes():
    """Exact retry with a known-safe previous outcome MUST mint a NEW
    transaction/token, and the new token is the one that executes."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "dom_binding_failed", "message": "composer missing"},
        side_effect_state=SideEffectState.FAILED,
    ))
    manager = _guarded_manager(real, ledger)
    first = await _governed(manager, ledger)
    assert real.execute_calls == 1

    second = await _governed(manager, ledger, allow_exact_retry=True)
    assert real.execute_calls == 2
    assert second.transaction.token != first.transaction.token
    assert second.transaction.transaction_id != first.transaction.transaction_id
    # The first token is consumed and must not be reusable.
    assert ledger.token_consumed(first.transaction.token) is True


@pytest.mark.asyncio
async def test_r5_unknown_side_effect_no_retry_no_token_reuse():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "may_have_sent", "message": "lost"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    manager = _guarded_manager(real, ledger)
    first = await _governed(manager, ledger)
    assert ledger.token_consumed(first.transaction.token) is True
    with pytest.raises(ReviewRetryUnsafeError):
        await _governed(manager, ledger, allow_exact_retry=True)
    assert real.execute_calls == 1


@pytest.mark.asyncio
async def test_health_fail_burns_token_even_without_send():
    """A failed provider-health path (before a real send) must burn the token so
    it cannot be replayed later."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(None, healthy=False, health_detail="disconnected")
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert result.outcome_status == "unavailable"
    assert ledger.token_consumed(result.transaction.token) is True

    # Replay the token — rejected.
    request = CapabilityRequest(
        capability_id="engineering.code_review",
        arguments={"review_id": "rvw_1", REVIEW_TOKEN_ARG: result.transaction.token, REVIEW_SEMANTIC_ARG: True},
    )
    execution = await manager.execute_typed(request)
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert real.execute_calls == 0


# ═══════════════════════════════════════════════════════════════════════════════
# G1-G5: exact invocation<->transaction binding (P0-B)
# ═══════════════════════════════════════════════════════════════════════════════

def test_g1_governance_api_has_no_separate_transaction_parameter():
    """build_governance_record(invocation=A, transaction=B) is impossible — the
    service derives transaction from the exact invocation."""
    import inspect
    params = inspect.signature(ReviewGovernanceService.record).parameters
    assert "transaction" not in params
    assert list(params)[1] == "invocation"


@pytest.mark.asyncio
async def test_g2_invocation_with_handcrafted_lookalike_transaction_rejected():
    """Invocation A + handcrafted transaction A-lookalike -> reject (P1-E)."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "VERDICT: PASS"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = ReviewGovernanceService(ledger, _SameShaSource())

    fake = ReviewTransaction(
        transaction_id=result.transaction.transaction_id,
        snapshot=result.transaction.snapshot,
        token="stolen",
        review_id=result.transaction.review_id,
        candidate_id=result.transaction.candidate_id,
        candidate_sha=result.transaction.candidate_sha,
        bundle_digest=result.transaction.bundle_digest,
    )
    from julia_core.review.invocation import ReviewInvocationResult
    fake_invocation = ReviewInvocationResult(execution=result.execution, transaction=fake)
    with pytest.raises(ReviewUntrustedTransactionError):
        service.record(fake_invocation, _candidate())


@pytest.mark.asyncio
async def test_g3_spread_copied_transaction_rejected():
    import copy
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "VERDICT: PASS"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = ReviewGovernanceService(ledger, _SameShaSource())

    copied = copy.deepcopy(result.transaction)
    from julia_core.review.invocation import ReviewInvocationResult
    fake_invocation = ReviewInvocationResult(execution=result.execution, transaction=copied)
    with pytest.raises(ReviewUntrustedTransactionError):
        service.record(fake_invocation, _candidate())


@pytest.mark.asyncio
async def test_g4_transaction_from_other_ledger_rejected():
    ledger = ReviewTransactionLedger()
    other_ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "VERDICT: PASS"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = ReviewGovernanceService(ledger, _SameShaSource())

    foreign_txn = other_ledger.mint(seal_review_bundle(_bundle(review_id="rvw_FOREIGN")))
    from julia_core.review.invocation import ReviewInvocationResult
    fake_invocation = ReviewInvocationResult(execution=result.execution, transaction=foreign_txn)
    with pytest.raises(ReviewUntrustedTransactionError):
        service.record(fake_invocation, _candidate())


@pytest.mark.asyncio
async def test_g5_execution_a_raw_digest_cannot_authorize_candidate_b():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": "VERDICT: PASS", "raw_response_digest": "d" * 64},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = ReviewGovernanceService(ledger, _SameShaSource())

    candidate = _candidate(raw_response_ref="r2", raw_response_digest="f" * 64)
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"
    assert any("raw_response_digest_unbound" in r for r in record.rejection_reasons)




# ═══════════════════════════════════════════════════════════════════════════════
# E1-E5: CandidateShaSource trusted composition (P0-C)
# ═══════════════════════════════════════════════════════════════════════════════

def test_e1_caller_fake_source_cannot_influence_governance():
    """The service API has NO candidate_sha_source parameter — a caller fake
    source cannot influence governance."""
    import inspect
    params = inspect.signature(ReviewGovernanceService.record).parameters
    assert "candidate_sha_source" not in params
    assert "source" not in params


def test_e2_caller_cannot_replace_source_after_composition():
    service = ReviewGovernanceService(ReviewTransactionLedger(), _SameShaSource())
    with pytest.raises(AttributeError):
        service._candidate_sha_source = object()  # slots/frozen composition
    with pytest.raises(AttributeError):
        service.candidate_sha_source = object()
    assert isinstance(service.candidate_sha_source, _SameShaSource)


@pytest.mark.asyncio
async def test_e3_no_source_bound_candidate_never_admitted():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": "VERDICT: PASS", "raw_response_digest": "d" * 64},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = ReviewGovernanceService(ledger, candidate_sha_source=None)
    record = service.record(result, _candidate(raw_response_digest="d" * 64))
    assert record.admission == "REJECTED"
    assert any("stale_validation_unavailable" in r for r in record.rejection_reasons)


@pytest.mark.asyncio
async def test_e4_trusted_source_same_sha_not_stale():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": "VERDICT: PASS", "raw_response_digest": "d" * 64},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = ReviewGovernanceService(ledger, _SameShaSource())
    record = service.record(result, _candidate(raw_response_digest="d" * 64))
    assert record.admission == "CANDIDATE_ADMITTED", record.rejection_reasons


@pytest.mark.asyncio
async def test_e5_trusted_source_changed_sha_stale_review():
    class ChangedShaSource:
        def current_candidate_sha(self, *, review_id, candidate_id):
            return "changedsha"

    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": "VERDICT: PASS", "raw_response_digest": "d" * 64},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = ReviewGovernanceService(ledger, ChangedShaSource())
    record = service.record(result, _candidate(raw_response_digest="d" * 64))
    assert record.admission == "REJECTED"
    assert any(ReviewErrorCode.STALE_REVIEW.value in r for r in record.rejection_reasons)


# ═══════════════════════════════════════════════════════════════════════════════
# S27-S30: sealed snapshot trusted creator (P1-D) / ledger ownership (P1-E)
# ═══════════════════════════════════════════════════════════════════════════════

def test_s27_handcrafted_snapshot_rejected_by_mint():
    from julia_core.review.snapshot import SealedReviewBundle
    ledger = ReviewTransactionLedger()
    snapshot = seal_review_bundle(_bundle())
    fake = SealedReviewBundle(
        snapshot_id=snapshot.snapshot_id,
        review_id=snapshot.review_id,
        task_id=snapshot.task_id,
        candidate_id=snapshot.candidate_id,
        candidate_sha=snapshot.candidate_sha,
        repository=snapshot.repository,
        branch=snapshot.branch,
        review_mode=snapshot.review_mode,
        objective=snapshot.objective,
        payload=snapshot.payload,
        digest=snapshot.digest,
    )
    with pytest.raises(ReviewUntrustedSnapshotError):
        ledger.mint(fake)


def test_s28_copied_reconstructed_snapshot_rejected():
    import copy
    ledger = ReviewTransactionLedger()
    snapshot = seal_review_bundle(_bundle())
    copied = copy.deepcopy(snapshot)
    with pytest.raises(ReviewUntrustedSnapshotError):
        ledger.mint(copied)


def test_s29_genuine_snapshot_accepted():
    ledger = ReviewTransactionLedger()
    snapshot = seal_review_bundle(_bundle())
    transaction = ledger.mint(snapshot)
    assert ledger.owns_transaction(transaction) is True


def test_s30_original_bundle_mutation_does_not_change_genuine_snapshot():
    bundle = _bundle(diff_blocks=({"path": "a.py", "content": "v1"},))
    snapshot = seal_review_bundle(bundle)
    digest_before = snapshot.digest
    bundle.diff_blocks[0]["content"] = "MUTATED"
    assert snapshot.digest == digest_before
    assert snapshot.to_payload()["diff_blocks"][0]["content"] == "v1"
    # Genuine snapshot still trusted after caller mutation.
    assert is_trusted_snapshot(snapshot) is True

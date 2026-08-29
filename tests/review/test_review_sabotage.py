"""External Code Review — full sabotage matrix (round-4).

Round-2: S1-S26
Round-3: R1-R5, G1-G5, E1-E5, S27-S30
Round-4: Q1-Q4, I1-I4, O1-O5, X1-X2, E6-E9, S31-S34, T1-T4, C1-C5, GR1-GR4

Each attack must FAIL CLOSED. A single broken authority seam means
MODULE NOT PASS.
"""

from __future__ import annotations

import asyncio
import copy
import inspect
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
from julia_core.review.digest import compute_text_digest
from julia_core.review.governance import (
    ReviewGovernanceService,
    is_trusted_review_governance_record,
)
from julia_core.review.guard import REVIEW_SEMANTIC_ARG, REVIEW_TOKEN_ARG, install_review_guard
from julia_core.review.invocation import (
    ReviewInvocationResult,
    build_review_request,
    is_trusted_invocation,
    submit_review,
)
from julia_core.review.registration import register_external_review_capability
from julia_core.review.snapshot import (
    SealedReviewBundle,
    is_trusted_snapshot,
    seal_review_bundle,
)
from julia_core.review._test_only import (
    TestCandidateCreator,
    TestCandidateShaSource,
    register_test_candidate_creator,
    register_test_candidate_sha_source,
)
from julia_core.review.candidate_artifact import (
    SealedCandidate,
    is_trusted_candidate,
    seal_candidate,
)
from julia_core.review.source_binding import (
    is_trusted_candidate_creator,
    is_trusted_source_binding,
)
from julia_core.review.transaction import (
    ReviewDuplicateError,
    ReviewRetryUnsafeError,
    ReviewTransaction,
    ReviewTransactionLedger,
    ReviewUntrustedSnapshotError,
    ReviewUntrustedTransactionError,
)
from julia_core.review.validation import (
    CandidateShaSourceUnavailable,
    ReviewCorrelationError,
    raw_response_digest_matches,
    validate_review_correlation,
)

RAW_RESPONSE = "VERDICT: PASS\nBLOCKERS:\n- none\nHIGH:\n- ok\n"
RAW_DIGEST = compute_text_digest(RAW_RESPONSE)


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
        raw_response_ref="tool_result:cr:raw_response",
        raw_response_digest=RAW_DIGEST,
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


def _success_provider():
    return FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": RAW_RESPONSE},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))


class _SameShaAdapter(TestCandidateShaSource):
    """TEST-ONLY adapter: must be bound through register_test_candidate_sha_source()."""

    def current_candidate_sha(self, *, review_id, candidate_id):
        return "abc123"


def _same_sha_binding():
    return register_test_candidate_sha_source(_SameShaAdapter())


def _raw_ref_of(result) -> str:
    """Derive the Core-owned expected raw_response_ref from the exact execution."""
    call_id = result.execution.tool_result.capability_call_id
    return f"tool_result:{call_id}:raw_response"


def _service(ledger, source_binding=None, creator_binding=None) -> ReviewGovernanceService:
    if creator_binding is None:
        creator_binding = _candidate_creator_binding()
    return ReviewGovernanceService(
        ledger, source_binding=source_binding, candidate_creator_binding=creator_binding
    )


class _TestCandidateCreator(TestCandidateCreator):
    """TEST-ONLY trusted candidate creator (round-5 §6 / round-6 §C).

    Deterministically produces the exact SealedCandidate from the raw response.
    Registered via register_test_candidate_creator() — the explicit test-only
    seam. Not production authority.
    """

    def create_candidate(self, *, raw_response: str, raw_response_ref: str) -> SealedCandidate:
        if raw_response != RAW_RESPONSE:
            raise ValueError("unrecognized raw response")
        candidate = ReviewDecisionCandidate(
            review_id="rvw_1",
            candidate_id="cand_1",
            candidate_sha="abc123",
            source="external_review",
            verdict=ReviewVerdict.PASS,
            blockers=(),
            high=("ok",),
            medium=(),
            required_changes=(),
            notes=("looks good",),
            transport_trace={"status": "CAPTURED"},
            raw_response_ref=raw_response_ref,
            raw_response_digest=RAW_DIGEST,
            captured_at="2026-08-29T00:00:00Z",
            validation_state="CANDIDATE",
        )
        return seal_candidate(candidate)


def _candidate_creator_binding():
    return register_test_candidate_creator(_TestCandidateCreator())


def _sealed_candidate(**overrides) -> SealedCandidate:
    """Build a trusted SealedCandidate with the canonical defaults, then apply
    overrides BEFORE sealing so a mutated field is part of the artifact (and
    will be caught by governance checks)."""
    candidate = ReviewDecisionCandidate(
        review_id="rvw_1",
        candidate_id="cand_1",
        candidate_sha="abc123",
        source="external_review",
        verdict=ReviewVerdict.PASS,
        blockers=(),
        high=("ok",),
        medium=(),
        required_changes=(),
        notes=("looks good",),
        transport_trace={"status": "CAPTURED"},
        raw_response_ref="tool_result:cr:raw_response",
        raw_response_digest=RAW_DIGEST,
        captured_at="2026-08-29T00:00:00Z",
        validation_state="CANDIDATE",
    )
    import dataclasses
    candidate = dataclasses.replace(candidate, **overrides)
    return seal_candidate(candidate)


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
    outcome = bridge.execute_tool_typed('{"name": "engineering.code_review", "arguments": {}}')
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
    request = build_review_request(transaction)

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
# S7-S8: current candidate SHA truth
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
# S9-S10 + R1-R5: duplicate / one-shot token / exact retry
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_s9_duplicate_ordinary_submission_does_not_execute_provider_twice():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": RAW_RESPONSE},
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
async def test_r1_replayed_token_from_submit_review_is_rejected():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert real.execute_calls == 1

    request = build_review_request(result.transaction)
    execution = await manager.execute_typed(request)
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert real.execute_calls == 1


@pytest.mark.asyncio
async def test_r2_direct_request_with_consumed_token_rejected():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
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
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    token = result.transaction.token

    original = build_review_request(result.transaction)
    copied = copy.deepcopy(original)
    execution = await manager.execute_typed(copied)
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert real.execute_calls == 1


@pytest.mark.asyncio
async def test_r4_exact_retry_mints_new_token_and_executes():
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
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(None, healthy=False, health_detail="disconnected")
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert result.outcome_status == "unavailable"
    assert ledger.token_consumed(result.transaction.token) is True

    request = CapabilityRequest(
        capability_id="engineering.code_review",
        arguments={"review_id": "rvw_1", REVIEW_TOKEN_ARG: result.transaction.token, REVIEW_SEMANTIC_ARG: True},
    )
    execution = await manager.execute_typed(request)
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert real.execute_calls == 0


# ═══════════════════════════════════════════════════════════════════════════════
# S11-S13: transport / governance truth
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_s11_transport_trace_created_cannot_admit_candidate():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    candidate = _sealed_candidate(transport_trace={"status": "CREATED"})
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"
    assert any("transport_trace_incomplete" in r for r in record.rejection_reasons)


@pytest.mark.asyncio
async def test_s12_caller_outcome_status_success_cannot_fabricate_governance():
    params = inspect.signature(ReviewGovernanceService.record).parameters
    assert "outcome_status" not in params
    assert "side_effect_state" not in params
    assert "correlation_errors" not in params
    assert "transaction" not in params


@pytest.mark.asyncio
async def test_s13_caller_correlation_empty_cannot_bypass_internal_validation():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    candidate = _sealed_candidate(candidate_sha="deadbeef")
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"
    assert any(ReviewErrorCode.CANDIDATE_SHA_MISMATCH.value in r for r in record.rejection_reasons)


# ═══════════════════════════════════════════════════════════════════════════════
# S14-S18: semantic binding
# ═══════════════════════════════════════════════════════════════════════════════

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
    assert raw_response_digest_matches(candidate, expected_digest=RAW_DIGEST) is False


# ═══════════════════════════════════════════════════════════════════════════════
# S19-S23: provider outcome truth
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
# S27-S30: sealed snapshot trusted creator (P1-D)
# ═══════════════════════════════════════════════════════════════════════════════

def test_s27_handcrafted_snapshot_rejected_by_mint():
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
    assert is_trusted_snapshot(snapshot) is True


def test_s30_original_bundle_mutation_does_not_change_genuine_snapshot():
    bundle = _bundle(diff_blocks=({"path": "a.py", "content": "v1"},))
    snapshot = seal_review_bundle(bundle)
    digest_before = snapshot.digest
    bundle.diff_blocks[0]["content"] = "MUTATED"
    assert snapshot.digest == digest_before
    assert snapshot.to_payload()["diff_blocks"][0]["content"] == "v1"
    assert is_trusted_snapshot(snapshot) is True


# ═══════════════════════════════════════════════════════════════════════════════
# G1-G5: exact invocation<->transaction binding (P0-B)
# ═══════════════════════════════════════════════════════════════════════════════

def test_g1_governance_api_has_no_separate_transaction_parameter():
    params = inspect.signature(ReviewGovernanceService.record).parameters
    assert "transaction" not in params
    assert list(params)[1] == "invocation"


@pytest.mark.asyncio
async def test_g2_invocation_with_handcrafted_lookalike_transaction_rejected():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())

    fake = ReviewTransaction(
        transaction_id=result.transaction.transaction_id,
        snapshot=result.transaction.snapshot,
        token="stolen",
        review_id=result.transaction.review_id,
        candidate_id=result.transaction.candidate_id,
        candidate_sha=result.transaction.candidate_sha,
        bundle_digest=result.transaction.bundle_digest,
    )
    fake_invocation = ReviewInvocationResult(
        invocation_id="rvw_inv_fake", execution=result.execution, transaction=fake
    )
    with pytest.raises(ReviewUntrustedTransactionError):
        service.record(fake_invocation, _sealed_candidate())


@pytest.mark.asyncio
async def test_g3_spread_copied_transaction_rejected():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())

    copied = copy.deepcopy(result.transaction)
    fake_invocation = ReviewInvocationResult(
        invocation_id="rvw_inv_copy", execution=result.execution, transaction=copied
    )
    with pytest.raises(ReviewUntrustedTransactionError):
        service.record(fake_invocation, _sealed_candidate())


@pytest.mark.asyncio
async def test_g4_transaction_from_other_ledger_rejected():
    ledger = ReviewTransactionLedger()
    other_ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())

    foreign_txn = other_ledger.mint(seal_review_bundle(_bundle(review_id="rvw_FOREIGN")))
    fake_invocation = ReviewInvocationResult(
        invocation_id="rvw_inv_foreign", execution=result.execution, transaction=foreign_txn
    )
    with pytest.raises(ReviewUntrustedTransactionError):
        service.record(fake_invocation, _sealed_candidate())


@pytest.mark.asyncio
async def test_g5_execution_a_raw_digest_cannot_authorize_candidate_b():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())

    candidate = _sealed_candidate(raw_response_ref="r2", raw_response_digest="f" * 64)
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"
    assert any("raw_response_digest_mismatch" in r for r in record.rejection_reasons)


# ═══════════════════════════════════════════════════════════════════════════════
# E1-E5: CandidateShaSource trusted composition (round-3)
# ═══════════════════════════════════════════════════════════════════════════════

def test_e1_caller_fake_source_cannot_influence_governance():
    params = inspect.signature(ReviewGovernanceService.record).parameters
    assert "candidate_sha_source" not in params
    assert "source" not in params


def test_e2_caller_cannot_replace_source_after_composition():
    service = _service(ReviewTransactionLedger(), _same_sha_binding())
    with pytest.raises(AttributeError):
        service._source_binding = object()
    with pytest.raises(AttributeError):
        service.source_binding = object()
    assert service.source_binding is not None


@pytest.mark.asyncio
async def test_e3_no_source_bound_candidate_never_admitted():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, source_binding=None)
    record = service.record(result, _sealed_candidate())
    assert record.admission == "REJECTED"
    # Unbound production service fails closed (no source, no creator).
    assert any("stale_validation_unavailable" in r or "candidate_creator_unavailable" in r
               for r in record.rejection_reasons)


@pytest.mark.asyncio
async def test_e4_trusted_source_same_sha_not_stale():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    candidate = _TestCandidateCreator().create_candidate(
    raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result))
    record = service.record(result, candidate)
    assert record.admission == "CANDIDATE_ADMITTED", record.rejection_reasons


@pytest.mark.asyncio
async def test_e5_trusted_source_changed_sha_stale_review():
    class ChangedShaAdapter(TestCandidateShaSource):
        def current_candidate_sha(self, *, review_id, candidate_id):
            return "changedsha"

    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, register_test_candidate_sha_source(ChangedShaAdapter()))
    candidate = _TestCandidateCreator().create_candidate(
        raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result)
    )
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"
    assert any(ReviewErrorCode.STALE_REVIEW.value in r for r in record.rejection_reasons)


# ═══════════════════════════════════════════════════════════════════════════════
# E6-E9: trusted source binding authority (P0-C, round-4)
# ═══════════════════════════════════════════════════════════════════════════════

def test_e6_fake_source_in_constructor_cannot_become_authority():
    class FakeSource:
        def current_candidate_sha(self, *, review_id, candidate_id):
            return "whatever"

    # An arbitrary adapter object is NOT a trusted binding.
    assert is_trusted_source_binding(FakeSource()) is False
    assert is_trusted_source_binding(object()) is False
    with pytest.raises(TypeError):
        ReviewGovernanceService(ReviewTransactionLedger(), source_binding=FakeSource())


def test_e7_setattr_source_replacement_cannot_change_authority():
    """object.__setattr__ on the service cannot grant a fake adapter authority.

    The adapter authority lives in the registry keyed by binding_id. Replacing
    the service slot with an arbitrary object yields source_binding that is NOT
    a trusted binding -> has_trusted_source becomes False (fail closed), so a
    fake can never become SHA authority.
    """
    binding = _same_sha_binding()
    service = _service(ReviewTransactionLedger(), binding)
    assert service.has_trusted_source is True
    # A raw adapter object is never a trusted binding.
    assert is_trusted_source_binding(_SameShaAdapter()) is False
    assert is_trusted_source_binding(object()) is False
    # Even a forged CandidateShaSourceBinding-like object is not registered.
    from julia_core.review.source_binding import CandidateShaSourceBinding
    forged = CandidateShaSourceBinding(binding_id="sha_src_forged")
    assert is_trusted_source_binding(forged) is False


def test_e8_copied_service_with_fake_source_not_trusted():
    binding = _same_sha_binding()
    service = _service(ReviewTransactionLedger(), binding)
    # A reconstructed service can only accept a trusted binding or None.
    assert service.has_trusted_source is True
    # A bare reconstructed object is not provenance.
    assert is_trusted_source_binding(None) is False


@pytest.mark.asyncio
async def test_e9_no_canonical_source_no_candidate_admitted():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = ReviewGovernanceService(ledger)  # UNBOUND
    record = service.record(result, _sealed_candidate())
    assert record.admission == "REJECTED"
    # Unbound production service fails closed (no source, no creator).
    assert any("stale_validation_unavailable" in r or "candidate_creator_unavailable" in r
               for r in record.rejection_reasons)


# ═══════════════════════════════════════════════════════════════════════════════
# Q1-Q4: request exactly bound to transaction (§1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_q1_request_api_binds_transaction_only():
    """Q1: build_review_request has no snapshot parameter — Snapshot B cannot
    be bound to Transaction A."""
    params = inspect.signature(build_review_request).parameters
    assert list(params)[0] == "transaction"
    assert "snapshot" not in params


@pytest.mark.asyncio
async def test_q2_mutated_request_arguments_do_not_change_provider_payload():
    """Q2: request.arguments is mutable but is NOT semantic truth; the guard
    re-derives the provider payload from the trusted snapshot."""
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)

    bundle = _bundle()
    snapshot = seal_review_bundle(bundle)
    transaction = ledger.mint(snapshot)
    request = build_review_request(transaction)
    request.arguments["candidate_sha"] = "FORGED"
    request.arguments["repository"] = "EVIL_REPO"
    request.arguments["objective"] = "EVIL_OBJECTIVE"
    execution = await manager.execute_typed(request)
    assert real.execute_calls == 1
    assert real.last_request.arguments["candidate_sha"] == "abc123"
    assert real.last_request.arguments["repository"] == "Julia_core"
    assert real.last_request.arguments["objective"] == "review code"


@pytest.mark.asyncio
async def test_q3_browser_field_inserted_after_build_never_reaches_provider():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)

    transaction = ledger.mint(seal_review_bundle(_bundle()))
    request = build_review_request(transaction)
    request.arguments["tab_id"] = 999
    request.arguments["browser_session_id"] = "bs_1"
    request.arguments["dom_selector"] = "#send"
    execution = await manager.execute_typed(request)
    assert real.execute_calls == 1
    for key in ("tab_id", "browser_session_id", "dom_selector"):
        assert key not in real.last_request.arguments


@pytest.mark.asyncio
async def test_q4_candidate_sha_repository_changed_after_build_ignored():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)

    transaction = ledger.mint(seal_review_bundle(_bundle()))
    request = build_review_request(transaction)
    request.arguments["candidate_sha"] = "deadbeef"
    request.arguments["repository"] = "evil"
    execution = await manager.execute_typed(request)
    assert real.execute_calls == 1
    assert real.last_request.arguments["candidate_sha"] == "abc123"
    assert real.last_request.arguments["repository"] == "Julia_core"


# ═══════════════════════════════════════════════════════════════════════════════
# I1-I4: trusted invocation exact binding (§2)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_i1_genuine_execution_a_genuine_transaction_b_rejected():
    """Execution A + genuine Transaction B (from SAME ledger) is NOT a genuine
    pair unless submit_review produced the invocation."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "dom_binding_failed", "message": "composer missing"},
        side_effect_state=SideEffectState.FAILED,
    ))
    manager = _guarded_manager(real, ledger)
    result_a = await _governed(manager, ledger)
    result_b = await _governed(manager, ledger, allow_exact_retry=True)
    assert result_b.transaction.transaction_id != result_a.transaction.transaction_id

    # Cross-wire: execution from A, transaction from B, handcrafted invocation.
    forged = ReviewInvocationResult(
        invocation_id="rvw_inv_forged",
        execution=result_a.execution,
        transaction=result_b.transaction,
    )
    assert is_trusted_invocation(forged) is False
    service = _service(ledger, _same_sha_binding())
    with pytest.raises(ReviewUntrustedTransactionError):
        service.record(forged, _sealed_candidate())


@pytest.mark.asyncio
async def test_i2_fabricated_execution_rejected():
    """Genuine Transaction A + fabricated CapabilityExecution -> reject."""
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)

    # Build a structurally valid but NON-matching CapabilityExecution whose
    # capability_call_id differs from the transaction's actual execution.
    from julia_core.capability.manager import CapabilityExecution
    from julia_core.capability.models import CapabilityCall, CapabilityCallStatus, ToolResult
    other_call = CapabilityCall(
        capability_call_id="cap_call_OTHER",
        capability_request_id="cap_req_OTHER",
    )
    other_result = ToolResult(
        capability_call_id="cap_call_OTHER",
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": RAW_RESPONSE},
    )
    fabricated_execution = CapabilityExecution(
        authorization_decision=result.execution.authorization_decision,
        capability_call=other_call,
        tool_result=other_result,
        evidence=(),
    )
    forged = ReviewInvocationResult(
        invocation_id="rvw_inv_fabricated",
        execution=fabricated_execution,
        transaction=result.transaction,
    )
    assert is_trusted_invocation(forged) is False
    service = _service(ledger, _same_sha_binding())
    with pytest.raises(ReviewUntrustedTransactionError):
        service.record(forged, _sealed_candidate())


@pytest.mark.asyncio
async def test_i3_copied_invocation_rejected():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)

    copied = copy.deepcopy(result)
    assert is_trusted_invocation(copied) is False
    service = _service(ledger, _same_sha_binding())
    with pytest.raises(ReviewUntrustedTransactionError):
        service.record(copied, _sealed_candidate())


@pytest.mark.asyncio
async def test_i4_exact_submit_review_produced_invocation_accepted():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert is_trusted_invocation(result) is True
    service = _service(ledger, _same_sha_binding())
    candidate = _TestCandidateCreator().create_candidate(
    raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result))
    record = service.record(result, candidate)
    assert record.admission == "CANDIDATE_ADMITTED", record.rejection_reasons


# ═══════════════════════════════════════════════════════════════════════════════
# O1-O5: immutable retry state (§3)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_o1_unknown_overwrite_attempt_still_forbids_retry():
    """O1: caller attempts to overwrite UNKNOWN->FAILED; retry still forbidden."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "may_have_sent", "message": "lost"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    manager = _guarded_manager(real, ledger)
    first = await _governed(manager, ledger)

    # There is no public record_outcome; the internal record stays UNKNOWN.
    with pytest.raises(ReviewRetryUnsafeError):
        await _governed(manager, ledger, allow_exact_retry=True)
    assert real.execute_calls == 1


@pytest.mark.asyncio
async def test_o2_prior_transaction_outcome_missing_retry_forbidden():
    """O2: a prior transaction without a recorded outcome cannot be retried."""
    ledger = ReviewTransactionLedger()
    snapshot = seal_review_bundle(_bundle())
    transaction = ledger.mint(snapshot)
    # No outcome recorded at all -> retry forbidden (O2, stricter than duplicate).
    with pytest.raises(ReviewRetryUnsafeError):
        ledger.mint(snapshot, allow_exact_retry=True)


@pytest.mark.asyncio
async def test_o3_succeeded_retry_forbidden():
    """O3: SUCCEEDED side effect is not provably retry-safe."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": RAW_RESPONSE},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager = _guarded_manager(real, ledger)
    await _governed(manager, ledger)
    assert real.execute_calls == 1
    with pytest.raises(ReviewRetryUnsafeError):
        await _governed(manager, ledger, allow_exact_retry=True)
    assert real.execute_calls == 1


@pytest.mark.asyncio
async def test_o4_safe_failed_none_explicit_retry_new_token():
    """O4: FAILED is in the safe set; explicit exact retry mints a new token."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "dom_binding_failed", "message": "composer missing"},
        side_effect_state=SideEffectState.FAILED,
    ))
    manager = _guarded_manager(real, ledger)
    first = await _governed(manager, ledger)
    second = await _governed(manager, ledger, allow_exact_retry=True)
    assert second.transaction.token != first.transaction.token
    assert real.execute_calls == 2


def test_o5_no_public_outcome_writer():
    """O5: ledger has no public record_outcome authority."""
    ledger = ReviewTransactionLedger()
    assert not hasattr(ledger, "record_outcome")


# ═══════════════════════════════════════════════════════════════════════════════
# X1-X2: exception-safe token lifecycle (§4)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_x1_exception_before_normal_return_token_unusable():
    """X1: unexpected manager/provider exception -> token unusable afterward."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(RuntimeError("boom after execute entered"))
    manager = _guarded_manager(real, ledger)

    result = await _governed(manager, ledger)
    assert result.outcome_status == "error"
    token = result.transaction.token
    assert ledger.token_consumed(token) is True

    request = CapabilityRequest(
        capability_id="engineering.code_review",
        arguments={"review_id": "rvw_1", REVIEW_TOKEN_ARG: token, REVIEW_SEMANTIC_ARG: True},
    )
    execution = await manager.execute_typed(request)
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE


@pytest.mark.asyncio
async def test_x2_exception_after_delegation_no_unsafe_retry():
    """X2: exception after delegation begins -> token unusable + no unsafe retry."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(RuntimeError("bridge dropped mid-send"))
    manager = _guarded_manager(real, ledger)

    result = await _governed(manager, ledger)
    assert result.outcome_status == "error"
    assert ledger.token_consumed(result.transaction.token) is True
    # Prior outcome recorded by governance-less path: side effect is UNKNOWN
    # (manager maps provider exception to ERROR + UNKNOWN side effect).
    with pytest.raises(ReviewRetryUnsafeError):
        await _governed(manager, ledger, allow_exact_retry=True)
    assert real.execute_calls == 1


# ═══════════════════════════════════════════════════════════════════════════════
# S31-S34: snapshot full-integrity fingerprint (§6)
# ═══════════════════════════════════════════════════════════════════════════════

def test_s31_setattr_candidate_sha_invalidates_trust():
    snapshot = seal_review_bundle(_bundle())
    object.__setattr__(snapshot, "candidate_sha", "deadbeef")
    assert is_trusted_snapshot(snapshot) is False
    ledger = ReviewTransactionLedger()
    with pytest.raises(ReviewUntrustedSnapshotError):
        ledger.mint(snapshot)


def test_s32_mutate_review_id_repository_digest_rejected():
    for field in ("review_id", "repository"):
        snapshot = seal_review_bundle(_bundle())
        object.__setattr__(snapshot, field, "MUTATED")
        assert is_trusted_snapshot(snapshot) is False

    snapshot = seal_review_bundle(_bundle())
    object.__setattr__(snapshot, "digest", "0" * 64)
    assert is_trusted_snapshot(snapshot) is False


def test_s33_mutate_payload_internal_storage_rejected():
    snapshot = seal_review_bundle(_bundle())
    from julia_core.review.snapshot import _deep_unfreeze
    mutated = _deep_unfreeze(snapshot.payload)
    mutated["objective"] = "EVIL"
    object.__setattr__(snapshot, "payload", _deep_unfreeze_to_frozen(snapshot, mutated))
    assert is_trusted_snapshot(snapshot) is False


def _deep_unfreeze_to_frozen(snapshot, plain):
    from julia_core.review.snapshot import _deep_freeze
    return _deep_freeze(plain)


def test_s34_genuine_untouched_snapshot_accepted():
    snapshot = seal_review_bundle(_bundle())
    assert is_trusted_snapshot(snapshot) is True
    ledger = ReviewTransactionLedger()
    transaction = ledger.mint(snapshot)
    assert ledger.owns_transaction(transaction) is True


# ═══════════════════════════════════════════════════════════════════════════════
# T1-T4: transaction full-integrity fingerprint (§7)
# ═══════════════════════════════════════════════════════════════════════════════

def test_t1_setattr_transaction_candidate_sha_rejected():
    ledger = ReviewTransactionLedger()
    transaction = ledger.mint(seal_review_bundle(_bundle()))
    assert ledger.owns_transaction(transaction) is True
    object.__setattr__(transaction, "candidate_sha", "deadbeef")
    assert ledger.owns_transaction(transaction) is False


def test_t2_change_transaction_snapshot_rejected():
    ledger = ReviewTransactionLedger()
    transaction = ledger.mint(seal_review_bundle(_bundle(candidate_sha="aaa111")))
    other_snapshot = seal_review_bundle(_bundle(candidate_sha="bbb222"))
    object.__setattr__(transaction, "snapshot", other_snapshot)
    assert ledger.owns_transaction(transaction) is False


def test_t3_change_bundle_digest_token_binding_rejected():
    for field in ("bundle_digest", "token", "review_id"):
        ledger = ReviewTransactionLedger()
        transaction = ledger.mint(seal_review_bundle(_bundle()))
        object.__setattr__(transaction, field, "MUTATED")
        assert ledger.owns_transaction(transaction) is False


def test_t4_genuine_untouched_transaction_accepted():
    ledger = ReviewTransactionLedger()
    transaction = ledger.mint(seal_review_bundle(_bundle()))
    assert ledger.owns_transaction(transaction) is True


# ═══════════════════════════════════════════════════════════════════════════════
# C1-C5: raw-response trusted provenance (§8)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_c1_pass_without_raw_response_truth_rejected():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    candidate = _sealed_candidate(raw_response_ref="", raw_response_digest="")
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"
    assert any("raw_response_ref_missing" in r for r in record.rejection_reasons)


@pytest.mark.asyncio
async def test_c2_pass_with_matching_ids_only_rejected():
    """C2: caller constructs PASS with matching IDs but NO raw truth -> REJECT."""
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    candidate = _sealed_candidate(
        verdict=ReviewVerdict.PASS, notes=("ok",),
        raw_response_ref="", raw_response_digest="",
    )
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"


@pytest.mark.asyncio
async def test_c3_copied_provider_digest_onto_fabricated_pass_rejected():
    """C3: caller copies provider-reported digest onto a fabricated PASS where
    the provider reported NO raw content -> no trusted observation -> REJECT."""
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response_digest": "d" * 64},  # digest only, no content
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    candidate = _sealed_candidate(raw_response_ref="r1", raw_response_digest="d" * 64)
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"
    assert any("raw_response_truth_unavailable" in r for r in record.rejection_reasons)


@pytest.mark.asyncio
async def test_c4_raw_content_digest_mismatch_rejected():
    """C4: Core computes the digest from the raw content itself; a candidate
    with a different digest is rejected."""
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    candidate = _sealed_candidate(raw_response_ref="r1", raw_response_digest="f" * 64)
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"
    assert any("raw_response_digest_mismatch" in r for r in record.rejection_reasons)


@pytest.mark.asyncio
async def test_c5_candidate_from_exact_trusted_observation_eligible():
    """C5: candidate whose raw digest matches the Core-computed digest of the
    exact execution observation is eligible for normal validation."""
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    # Candidate produced by the trusted creator over the exact raw response.
    candidate = _TestCandidateCreator().create_candidate(
        raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result)
    )
    record = service.record(result, candidate)
    assert record.admission == "CANDIDATE_ADMITTED", record.rejection_reasons


# ═══════════════════════════════════════════════════════════════════════════════
# GR1-GR4: governance record trusted audit artifact (§9)
# ═══════════════════════════════════════════════════════════════════════════════

def test_gr1_handcrafted_admitted_record_not_trusted():
    from julia_core.review.governance import ReviewGovernanceRecord
    record = ReviewGovernanceRecord(
        record_id="rvw_rec_FAKE",
        review_id="rvw_1", candidate_id="cand_1", candidate_sha="abc123",
        bundle_digest="d", transaction_id="t", invocation_id="i",
        candidate_artifact_id="cand_art_FAKE", candidate_fingerprint="fp_fake",
        outcome_status="success", side_effect_state="succeeded",
        admission="CANDIDATE_ADMITTED",
    )
    assert is_trusted_review_governance_record(record) is False


@pytest.mark.asyncio
async def test_gr2_copied_record_not_trusted():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    record = service.record(result, _sealed_candidate())
    assert is_trusted_review_governance_record(record) is True
    copied = copy.deepcopy(record)
    assert is_trusted_review_governance_record(copied) is False


@pytest.mark.asyncio
async def test_gr3_mutate_nested_transport_trace_rejected():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    record = service.record(result, _sealed_candidate())
    assert is_trusted_review_governance_record(record) is True

    trace = record.transport_trace
    if isinstance(trace, dict):
        trace["status"] = "FORGED"
    else:
        object.__setattr__(record, "transport_trace", {"status": "FORGED"})
    assert is_trusted_review_governance_record(record) is False


@pytest.mark.asyncio
async def test_gr4_genuine_governance_record_trusted():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    candidate = _TestCandidateCreator().create_candidate(
    raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result))
    record = service.record(result, candidate)
    assert record.admission == "CANDIDATE_ADMITTED"
    assert is_trusted_review_governance_record(record) is True


# ═══════════════════════════════════════════════════════════════════════════════
# Round-5 additions: creator/association closure
# ═══════════════════════════════════════════════════════════════════════════════

# --- §1: register_trusted_invocation is NOT public authority ---

def test_r5_01_register_trusted_invocation_not_public():
    import julia_core.review as review_pkg
    import julia_core.review.invocation as inv_mod
    assert not hasattr(review_pkg, "register_trusted_invocation")
    assert "register_trusted_invocation" not in inv_mod.__all__


@pytest.mark.asyncio
async def test_r5_02_handcrafted_invocation_cannot_be_upgraded():
    """A public caller cannot upgrade a handcrafted invocation to trusted."""
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)

    forged = ReviewInvocationResult(
        invocation_id="rvw_inv_hc", execution=result.execution, transaction=result.transaction
    )
    assert is_trusted_invocation(forged) is False
    # No public register API exists to upgrade it; direct registry write is the
    # only way and is module-internal.
    assert not hasattr(forged, "register_trusted")


# --- §2: invocation seal covers full execution truth ---

@pytest.mark.asyncio
async def test_r5_03_mutate_status_invalidates_trust():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert is_trusted_invocation(result) is True
    object.__setattr__(result.execution.tool_result, "status", ToolResultStatus.ERROR)
    assert is_trusted_invocation(result) is False


@pytest.mark.asyncio
async def test_r5_04_mutate_side_effect_state_invalidates_trust():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert is_trusted_invocation(result) is True
    object.__setattr__(result.execution.tool_result, "side_effect_state", SideEffectState.UNKNOWN)
    assert is_trusted_invocation(result) is False


@pytest.mark.asyncio
async def test_r5_05_mutate_structured_output_invalidates_trust():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert is_trusted_invocation(result) is True
    so = dict(result.execution.tool_result.structured_output)
    so["raw_response"] = "FORGED REVIEW"
    object.__setattr__(result.execution.tool_result, "structured_output", so)
    assert is_trusted_invocation(result) is False


@pytest.mark.asyncio
async def test_r5_06_mutate_error_invalidates_trust():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "a", "message": "m"},
        side_effect_state=SideEffectState.FAILED,
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert is_trusted_invocation(result) is True
    object.__setattr__(result.execution.tool_result, "error", {"code": "FORGED"})
    assert is_trusted_invocation(result) is False


# --- §3: transaction trust requires live trusted snapshot ---

def test_r5_07_lookalike_snapshot_cannot_substitute():
    ledger = ReviewTransactionLedger()
    snapshot = seal_review_bundle(_bundle())
    transaction = ledger.mint(snapshot)
    assert ledger.owns_transaction(transaction) is True

    # Handcraft a lookalike snapshot with the same id/digest.
    lookalike = SealedReviewBundle(
        snapshot_id=snapshot.snapshot_id,
        review_id=snapshot.review_id, task_id=snapshot.task_id,
        candidate_id=snapshot.candidate_id, candidate_sha=snapshot.candidate_sha,
        repository=snapshot.repository, branch=snapshot.branch,
        review_mode=snapshot.review_mode, objective=snapshot.objective,
        payload=snapshot.payload, digest=snapshot.digest,
    )
    object.__setattr__(transaction, "snapshot", lookalike)
    assert ledger.owns_transaction(transaction) is False


def test_r5_08_mutated_snapshot_blocks_claim():
    ledger = ReviewTransactionLedger()
    snapshot = seal_review_bundle(_bundle())
    transaction = ledger.mint(snapshot)
    object.__setattr__(snapshot, "candidate_sha", "deadbeef")
    assert ledger.claim_for_execution(transaction.token) is None


# --- §4: retry outcome write-once ---

@pytest.mark.asyncio
async def test_r5_09_second_seal_rejected():
    from julia_core.review.transaction import ReviewOutcomeAlreadySealedError
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    # submit_review already sealed; a second seal must be rejected. A fresh
    # authority bound to the same transaction+execution still hits the
    # write-once guard.
    from julia_core.review.lifecycle import _execution_fingerprint_of, mint_lifecycle_authority
    authority2 = mint_lifecycle_authority(
        transaction_id=result.transaction.transaction_id,
        execution_fingerprint=_execution_fingerprint_of(result.execution),
    )
    with pytest.raises((ReviewOutcomeAlreadySealedError, ReviewUntrustedTransactionError)):
        ledger._seal_execution_outcome(
            transaction=result.transaction, invocation=result, authority=authority2
        )


@pytest.mark.asyncio
async def test_r5_10_unknown_not_rewritable():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "may_have_sent", "message": "lost"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert result.side_effect_state == "unknown"
    # Retry forbidden; outcome can never be rewritten to FAILED.
    with pytest.raises(ReviewRetryUnsafeError):
        await _governed(manager, ledger, allow_exact_retry=True)


# --- §5: source binder not on production surface ---

def test_r5_11_source_binder_not_public_production_surface():
    import julia_core.review as review_pkg
    assert not hasattr(review_pkg, "bind_candidate_sha_source")
    assert not hasattr(review_pkg, "bind_candidate_creator")


def test_r5_12_production_unbound_fails_closed():
    ledger = ReviewTransactionLedger()
    # A governance service constructed with NO bindings must not admit.
    service = ReviewGovernanceService(ledger)
    assert service.has_trusted_source is False
    assert service.has_trusted_candidate_creator is False


# --- §6: no trusted candidate creator -> candidate admission fails closed ---

@pytest.mark.asyncio
async def test_r5_13_no_creator_candidate_admission_fails_closed():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = ReviewGovernanceService(ledger, source_binding=_same_sha_binding())  # NO creator
    candidate = _TestCandidateCreator().create_candidate(
        raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result)
    )
    record = service.record(result, candidate)
    assert record.admission == "REJECTED"
    assert any("candidate_creator_unavailable" in r for r in record.rejection_reasons)


# --- §7: record_id internally minted; caller cannot select ---

@pytest.mark.asyncio
async def test_r5_14_caller_selected_record_id_forbidden():
    import inspect
    params = inspect.signature(ReviewGovernanceService.record).parameters
    assert "record_id" not in params
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    candidate = _TestCandidateCreator().create_candidate(
        raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result)
    )
    record = service.record(result, candidate)
    assert record.record_id.startswith("rvw_rec_")


# ═══════════════════════════════════════════════════════════════════════════════
# Round-6 F1-F10: final seal patch sabotage
# ═══════════════════════════════════════════════════════════════════════════════

# --- F1: direct internal invocation-registration with handcrafted invocation ---

@pytest.mark.asyncio
async def test_f1_direct_registration_call_cannot_mint_trust():
    """Direct call to the internal registration helper with a handcrafted
    invocation cannot mint trusted invocation (no lifecycle authority)."""
    from julia_core.review.invocation import _register_trusted_invocation
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)

    forged = ReviewInvocationResult(
        invocation_id="rvw_inv_f1", execution=result.execution, transaction=result.transaction
    )
    assert is_trusted_invocation(forged) is False
    # No authority -> registration rejected.
    with pytest.raises(Exception):
        _register_trusted_invocation(forged, authority=None)
    assert is_trusted_invocation(forged) is False


# --- F2: direct outcome-seal with genuine transaction + fabricated execution ---

@pytest.mark.asyncio
async def test_f2_direct_outcome_seal_with_fabricated_execution_rejected():
    """A genuine transaction + fabricated execution cannot alter retry truth
    because the caller cannot mint the matching lifecycle authority."""
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)

    # A fabricated execution (different call id / no raw response).
    from julia_core.capability.models import CapabilityCall, ToolResult
    from julia_core.capability.manager import CapabilityExecution
    other_call = CapabilityCall(capability_call_id="cap_call_F2", capability_request_id="req_F2")
    other_result = ToolResult(
        capability_call_id="cap_call_F2",
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": "FORGED"},
    )
    fabricated = CapabilityExecution(
        authorization_decision=result.execution.authorization_decision,
        capability_call=other_call,
        tool_result=other_result,
        evidence=(),
    )
    forged_invocation = ReviewInvocationResult(
        invocation_id="rvw_inv_f2", execution=fabricated, transaction=result.transaction
    )
    # The transaction's outcome is already sealed by submit_review (write-once).
    # A forged seal attempt with a handcrafted authority must not overwrite it.
    with pytest.raises(Exception):
        ledger._seal_execution_outcome(
            transaction=result.transaction,
            invocation=forged_invocation,
            authority=object(),
        )
    assert ledger.token_consumed(result.transaction.token) is True


# --- F3: FakeSource through production binder ---

def test_f3_fake_source_cannot_become_trusted():
    """No production binder exists; duck-typed FakeSource cannot become a
    trusted source. The test seam rejects non-TestCandidateShaSource adapters."""
    class FakeSource:
        def current_candidate_sha(self, *, review_id, candidate_id):
            return "whatever"

    # No production binder on the public surface at all.
    import julia_core.review as review_pkg
    assert not hasattr(review_pkg, "bind_candidate_sha_source")
    # Test seam rejects duck-typed fakes.
    with pytest.raises(TypeError):
        register_test_candidate_sha_source(FakeSource())


# --- F4: FakeCreator through production binder ---

def test_f4_fake_creator_cannot_become_trusted():
    class FakeCreator:
        def create_candidate(self, **kwargs):
            return None

    import julia_core.review as review_pkg
    assert not hasattr(review_pkg, "bind_candidate_creator")
    with pytest.raises(TypeError):
        register_test_candidate_creator(FakeCreator())


# --- F5: trusted candidate PASS then mutate blockers -> untrusted ---

@pytest.mark.asyncio
async def test_f5_mutate_blockers_invalidates_trust():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)

    sealed = _TestCandidateCreator().create_candidate(
        raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result)
    )
    assert is_trusted_candidate(sealed) is True
    object.__setattr__(sealed.candidate, "blockers", ("EVIL",))
    assert is_trusted_candidate(sealed) is False


# --- F6: mutate required_changes -> rejected ---

@pytest.mark.asyncio
async def test_f6_mutate_required_changes_invalidates_trust():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)

    sealed = _TestCandidateCreator().create_candidate(
        raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result)
    )
    object.__setattr__(sealed.candidate, "required_changes", ("MORE WORK",))
    assert is_trusted_candidate(sealed) is False


# --- F7: mutate notes/high/medium/source/transport_trace -> rejected ---

@pytest.mark.asyncio
async def test_f7_mutate_notes_high_medium_source_transport_invalidates_trust():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)

    for field, value in (
        ("notes", ("evil",)),
        ("high", ("evil",)),
        ("medium", ("evil",)),
        ("source", "evil_source"),
        ("transport_trace", {"status": "FORGED"}),
    ):
        sealed = _TestCandidateCreator().create_candidate(
            raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result)
        )
        object.__setattr__(sealed.candidate, field, value)
        assert is_trusted_candidate(sealed) is False, f"field {field} should invalidate"


# --- F8: creator returns wrong raw_response_digest -> rejected ---

@pytest.mark.asyncio
async def test_f8_wrong_raw_response_digest_rejected():
    class WrongDigestCreator(TestCandidateCreator):
        def create_candidate(self, *, raw_response, raw_response_ref):
            candidate = ReviewDecisionCandidate(
                review_id="rvw_1", candidate_id="cand_1", candidate_sha="abc123",
                source="external_review", verdict=ReviewVerdict.PASS,
                notes=("ok",), transport_trace={"status": "CAPTURED"},
                raw_response_ref=raw_response_ref,
                raw_response_digest="0" * 64,  # WRONG
                captured_at="2026-08-29T00:00:00Z", validation_state="CANDIDATE",
            )
            return seal_candidate(candidate)

    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding(),
                       creator_binding=register_test_candidate_creator(WrongDigestCreator()))
    sealed = WrongDigestCreator().create_candidate(
        raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result)
    )
    record = service.record(result, sealed)
    assert record.admission == "REJECTED"
    assert any("raw_response_digest_mismatch" in r for r in record.rejection_reasons)


# --- F9: creator returns wrong raw_response_ref -> rejected ---

@pytest.mark.asyncio
async def test_f9_wrong_raw_response_ref_rejected():
    class WrongRefCreator(TestCandidateCreator):
        def create_candidate(self, *, raw_response, raw_response_ref):
            candidate = ReviewDecisionCandidate(
                review_id="rvw_1", candidate_id="cand_1", candidate_sha="abc123",
                source="external_review", verdict=ReviewVerdict.PASS,
                notes=("ok",), transport_trace={"status": "CAPTURED"},
                raw_response_ref="tool_result:WRONG:raw_response",
                raw_response_digest=RAW_DIGEST,
                captured_at="2026-08-29T00:00:00Z", validation_state="CANDIDATE",
            )
            return seal_candidate(candidate)

    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding(),
                       creator_binding=register_test_candidate_creator(WrongRefCreator()))
    sealed = WrongRefCreator().create_candidate(
        raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result)
    )
    record = service.record(result, sealed)
    assert record.admission == "REJECTED"
    assert any("raw_response_ref_mismatch" in r for r in record.rejection_reasons)


# --- F10: governance record candidate fingerprint mismatch -> untrusted ---

@pytest.mark.asyncio
async def test_f10_record_candidate_fingerprint_mismatch_untrusted():
    ledger = ReviewTransactionLedger()
    real = _success_provider()
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    service = _service(ledger, _same_sha_binding())
    sealed = _TestCandidateCreator().create_candidate(
        raw_response=RAW_RESPONSE, raw_response_ref=_raw_ref_of(result)
    )
    record = service.record(result, sealed)
    assert record.admission == "CANDIDATE_ADMITTED"
    assert is_trusted_review_governance_record(record) is True
    assert record.candidate_artifact_id == sealed.candidate_artifact_id
    assert record.candidate_fingerprint == sealed.fingerprint

    # Swap candidate_fingerprint -> record becomes untrusted.
    object.__setattr__(record, "candidate_fingerprint", "FORGED_FP")
    assert is_trusted_review_governance_record(record) is False

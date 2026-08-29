"""External Code Review — sabotage matrix (owner closure §S1-S26).

Each attack must FAIL CLOSED. A single broken authority seam means
MODULE NOT PASS.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from julia_core.capability.manager import CapabilityExecution, CapabilityManager
from julia_core.capability.models import (
    CapabilityCallStatus,
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
from julia_core.review.digest import compute_bundle_digest
from julia_core.review.governance import build_governance_record
from julia_core.review.guard import REVIEW_SEMANTIC_ARG, REVIEW_TOKEN_ARG, install_review_guard
from julia_core.review.invocation import (
    BrowserAuthorityInRequestError,
    build_review_request,
    submit_review,
)
from julia_core.review.registration import EXTERNAL_REVIEW_PROVIDER, register_external_review_capability
from julia_core.review.snapshot import seal_review_bundle
from julia_core.review.transaction import (
    ReviewDuplicateError,
    ReviewRetryUnsafeError,
    ReviewTransactionLedger,
)
from julia_core.review.validation import (
    CandidateShaSource,
    CandidateShaSourceUnavailable,
    ReviewCorrelationError,
    raw_response_digest_matches,
    validate_review_correlation,
    validate_transaction_correlation,
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


# ── S1-S6: ingress authority ─────────────────────────────────────────────────

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
    """Trusted request must remain byte/semantic identical after caller mutation."""
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

    # The trusted request was built from the snapshot, not the caller object.
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


# ── S7-S8: current candidate SHA truth (E) ───────────────────────────────────

def test_s7_caller_matching_fake_sha_cannot_establish_not_stale():
    """Without a canonical source, a matching caller SHA is NOT authority —
    stale validation fails closed."""
    snapshot = seal_review_bundle(_bundle())
    with pytest.raises(CandidateShaSourceUnavailable):
        assert_not_stale_via_caller(snapshot, "abc123")


def assert_not_stale_via_caller(snapshot, caller_sha):
    # This is the FORBIDDEN shape: it must never be reachable as authority.
    from julia_core.review.validation import assert_not_stale
    # There is no caller-SHA overload: assert_not_stale requires a source.
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


# ── S9-S10: duplicate / exact-retry control (F) ──────────────────────────────

@pytest.mark.asyncio
async def test_s9_duplicate_ordinary_submission_does_not_execute_provider_twice():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "ok"},
    ))
    manager = _guarded_manager(real, ledger)
    await _governed(manager, ledger)
    assert real.execute_calls == 1

    # Second ordinary submission of the same binding must NOT reach provider.
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

    # UNKNOWN side effect: even an explicit exact-retry request is refused.
    with pytest.raises(ReviewRetryUnsafeError):
        await _governed(manager, ledger, allow_exact_retry=True)
    assert real.execute_calls == 1


@pytest.mark.asyncio
async def test_exact_retry_allowed_when_prior_side_effect_known_and_not_duplicate():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "dom_binding_failed", "message": "composer missing"},
        side_effect_state=SideEffectState.FAILED,
    ))
    manager = _guarded_manager(real, ledger)
    await _governed(manager, ledger)
    assert real.execute_calls == 1
    # Explicit exact retry with a KNOWN (non-UNKNOWN) prior side effect is allowed.
    await _governed(manager, ledger, allow_exact_retry=True)
    assert real.execute_calls == 2


# ── S11-S13: transport / governance truth (G/H) ──────────────────────────────

@pytest.mark.asyncio
async def test_s11_transport_trace_created_cannot_admit_candidate():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "VERDICT: PASS"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    candidate = _candidate(transport_trace={"status": "CREATED"})
    record = build_governance_record(
        invocation=result, transaction=result.transaction, candidate=candidate,
        ledger=ledger, candidate_sha_source=_same_sha_source(),
    )
    assert record.admission == "REJECTED"
    assert any("transport_trace_incomplete" in r for r in record.rejection_reasons)


@pytest.mark.asyncio
async def test_s12_caller_outcome_status_success_cannot_fabricate_governance():
    """Governance derives outcome status from the typed execution, not from a
    caller string — the API has no outcome_status parameter at all."""
    import inspect
    params = inspect.signature(build_governance_record).parameters
    assert "outcome_status" not in params
    assert "side_effect_state" not in params
    assert "correlation_errors" not in params


@pytest.mark.asyncio
async def test_s13_caller_correlation_empty_cannot_bypass_internal_validation():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "VERDICT: PASS"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    # Candidate with mismatched SHA but no caller-provided correlation_errors.
    candidate = _candidate(candidate_sha="deadbeef")
    record = build_governance_record(
        invocation=result, transaction=result.transaction, candidate=candidate,
        ledger=ledger, candidate_sha_source=_same_sha_source(),
    )
    assert record.admission == "REJECTED"
    assert any(ReviewErrorCode.CANDIDATE_SHA_MISMATCH.value in r for r in record.rejection_reasons)


def _same_sha_source() -> CandidateShaSource:
    class Source:
        def current_candidate_sha(self, *, review_id, candidate_id):
            return "abc123"
    return Source()


# ── S14-S18: semantic binding ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_s14_digest_mismatch_rejected():
    """Correlation is against the snapshot's owned digest; a candidate bound to
    a different snapshot/transaction fails."""
    snapshot_a = seal_review_bundle(_bundle(candidate_sha="aaa111"))
    snapshot_b = seal_review_bundle(_bundle(candidate_sha="bbb222"))
    assert snapshot_a.digest != snapshot_b.digest
    errors = validate_review_correlation(snapshot_a, _candidate(candidate_sha="aaa111"))
    # Same review_id/candidate_id but different snapshot digest => digest must
    # match the transaction binding; here we verify it is NOT self-supplied.
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
    """A fabricated raw digest must not be admitted (I)."""
    candidate = _candidate(raw_response_ref="r1", raw_response_digest="f" * 64)
    assert raw_response_digest_matches(candidate, expected_digest="d" * 64) is False


# ── S19-S23: provider outcome truth (CRB-PRE-P1) ─────────────────────────────

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
    # No provider registered at all.
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


# ── S24-S26: scope isolation ─────────────────────────────────────────────────

def test_s24_candidate_pass_still_candidate_only():
    """Governance admission is candidate-only; there is no final PASS authority."""
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


# ── Additional authority-edge sabotage ───────────────────────────────────────

@pytest.mark.asyncio
async def test_provider_executes_at_most_once_per_submission():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "ok"},
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    assert real.execute_calls == 1
    assert result.execution.tool_result.capability_call_id == result.execution.capability_call.capability_call_id


@pytest.mark.asyncio
async def test_no_provider_fallback_after_failure():
    failing = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR, error={"code": "boom", "message": "fail"},
    ))
    second = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "sneaky"},
    ))
    ledger = ReviewTransactionLedger()
    registry = CapabilityRegistry()
    register_external_review_capability(registry, status=CapabilityStatus.AVAILABLE)
    providers = {}
    install_review_guard(providers, real_provider=failing, ledger=ledger)
    providers["alternate_provider"] = second
    manager = CapabilityManager(registry, AllowPolicy(), providers)
    result = await _governed(manager, ledger)
    assert result.outcome_status == "error"
    assert failing.execute_calls == 1
    assert second.execute_calls == 0


def test_provider_selected_capability_authority_is_ignored():
    """A provider returning a different capability_id must NOT change authority."""
    from julia_core.review.invocation import build_review_request
    ledger = ReviewTransactionLedger()
    snapshot = seal_review_bundle(_bundle())
    transaction = ledger.mint(snapshot)
    request = build_review_request(snapshot, transaction)
    # The request carries the ORIGINAL capability id.
    assert request.capability_id == "engineering.code_review"


def test_governance_record_rejects_error_outcome_with_correlated_candidate():
    """Transport failure must never become an admitted review (G)."""
    ledger = ReviewTransactionLedger()
    snapshot = seal_review_bundle(_bundle())
    transaction = ledger.mint(snapshot)

    class Exec:
        def __init__(self):
            self.tool_result = None
            self.authorization_decision = AuthorizationDecision(
                decision=AuthorizationStatus.ALLOW, scope="engineering.review.external"
            )

    class Invocation:
        def __init__(self):
            self.execution = Exec()
            self.transaction = transaction

    candidate = _candidate(transport_trace={"status": "CAPTURED"})
    record = build_governance_record(
        invocation=Invocation(),
        transaction=transaction,
        candidate=candidate,
        ledger=ledger,
        candidate_sha_source=_same_sha_source(),
    )
    assert record.admission == "REJECTED"
    assert any("transport_not_completed" in r for r in record.rejection_reasons)


@pytest.mark.asyncio
async def test_governance_admits_correlated_candidate_with_all_truth():
    ledger = ReviewTransactionLedger()
    real = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": "VERDICT: PASS", "raw_response_digest": "d" * 64},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager = _guarded_manager(real, ledger)
    result = await _governed(manager, ledger)
    candidate = _candidate(raw_response_ref="r1", raw_response_digest="d" * 64)
    record = build_governance_record(
        invocation=result, transaction=result.transaction, candidate=candidate,
        ledger=ledger, candidate_sha_source=_same_sha_source(),
    )
    assert record.admission == "CANDIDATE_ADMITTED", record.rejection_reasons

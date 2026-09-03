"""External Code Review — Manager integration / guarded ingress tests.

Covers round-4 API:
  - trusted ingress: seal -> transaction -> token -> request -> manager
  - guarded provider re-derives payload from trusted snapshot (Q2/Q3)
  - generic model tool-call path cannot invoke engineering.code_review (S2)
  - registration != external-send authorization (B)
  - typed execution outcome truth mapping (CRB-PRE-P1 preserved)
  - trusted invocation registry (I1-I4)
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from julia_core.capability.manager import CapabilityExecution, CapabilityManager
from julia_core.capability.models import (
    CapabilityCallStatus,
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
from julia_core.review.digest import compute_text_digest
from julia_core.review.guard import REVIEW_SEMANTIC_ARG, REVIEW_TOKEN_ARG, install_review_guard
from julia_core.review.invocation import (
    EXTERNAL_REVIEW_CAPABILITY,
    EXTERNAL_REVIEW_SCOPE,
    build_review_request,
    is_trusted_invocation,
    submit_review,
)
from julia_core.review.registration import (
    EXTERNAL_REVIEW_PROVIDER,
    register_external_review_capability,
)
from julia_core.review.snapshot import seal_review_bundle
from julia_core.review.transaction import ReviewTransactionLedger
from tests.review._testonly import candidate_admission_binding_for

RAW_RESPONSE = "VERDICT: PASS\nBLOCKERS:\n- none\n"
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


class FixtureReviewProvider:
    """Fixture provider implementing CapabilityProvider for external_review."""

    def __init__(self, outcome: dict[str, Any] | ProviderExecutionOutcome | Exception):
        self.outcome = outcome
        self.execute_calls = 0
        self.health_calls = 0
        self.last_request: CapabilityRequest | None = None

    async def health(self) -> tuple[bool, str]:
        self.health_calls += 1
        return True, "ok"

    async def execute(self, request: CapabilityRequest) -> dict[str, Any] | ProviderExecutionOutcome:
        self.execute_calls += 1
        self.last_request = request
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class AllowPolicy(PermissionPolicy):
    def check(self, scope: str) -> AuthorizationDecision:
        return AuthorizationDecision(decision=AuthorizationStatus.ALLOW, scope=scope, reason="allow fixture")


def _guarded_manager(
    real_provider: FixtureReviewProvider,
    ledger: ReviewTransactionLedger,
    policy: PermissionPolicy | None = None,
) -> tuple[CapabilityManager, FixtureReviewProvider]:
    registry = CapabilityRegistry()
    register_external_review_capability(
        registry, policy=policy, status=CapabilityStatus.AVAILABLE
    )
    providers: dict[str, Any] = {}
    install_review_guard(providers, real_provider=real_provider, ledger=ledger)
    return CapabilityManager(registry, policy or AllowPolicy(), providers), real_provider


async def _governed_submit(
    manager: CapabilityManager,
    ledger: ReviewTransactionLedger,
    bundle: ReviewBundle | None = None,
    **kwargs,
):
    resolved_bundle = bundle or _bundle()
    candidate_admission_binding_for(resolved_bundle)
    return await submit_review(manager, resolved_bundle, ledger, **kwargs)


# ── Registration / definition ────────────────────────────────────────────────

def test_definition_registers_with_canonical_shape():
    registry = CapabilityRegistry()
    policy = AllowPolicy()
    definition = register_external_review_capability(registry, policy=policy, status=CapabilityStatus.AVAILABLE)
    assert definition.name == EXTERNAL_REVIEW_CAPABILITY
    assert definition.provider == EXTERNAL_REVIEW_PROVIDER
    assert definition.permission_scope == EXTERNAL_REVIEW_SCOPE
    assert definition.layer == CapabilityLayer.INTELLIGENCE
    decision = policy.check(EXTERNAL_REVIEW_SCOPE)
    assert decision.decision == AuthorizationStatus.ALLOW


def test_unknown_scope_defaults_to_deny():
    policy = PermissionPolicy()
    assert policy.check("engineering.review.something.else").decision == AuthorizationStatus.DENY


# ── Guarded ingress (A/B) ────────────────────────────────────────────────────

def test_guarded_provider_rejects_arbitrary_request():
    """S1: arbitrary CapabilityRequest cannot reach the real provider."""
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "should not run"},
    ))
    manager, _ = _guarded_manager(real, ledger)

    request = CapabilityRequest(
        capability_id="engineering.code_review",
        arguments={"review_id": "rvw_x"},
        requested_scope="engineering.review.external",
    )
    execution = asyncio.run(manager.execute_typed(request))
    assert real.execute_calls == 0
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert execution.tool_result.error["code"] == "governed_review_ingress_required"


def test_guarded_provider_rejects_forged_provenance_only():
    """S3: provenance strings must NOT grant authority."""
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "sneaky"},
    ))
    manager, _ = _guarded_manager(real, ledger)

    request = CapabilityRequest(
        capability_id="engineering.code_review",
        arguments={"review_id": "rvw_x"},
        requested_scope="engineering.review.external",
        provenance={"manual": True, "operator": "tony"},
    )
    execution = asyncio.run(manager.execute_typed(request))
    assert real.execute_calls == 0
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE


def test_guarded_provider_rejects_token_without_semantic_marker():
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "sneaky"},
    ))
    manager, _ = _guarded_manager(real, ledger)

    snapshot = seal_review_bundle(_bundle())
    transaction = ledger.mint(snapshot)
    request = CapabilityRequest(
        capability_id="engineering.code_review",
        arguments={"review_id": "rvw_1", REVIEW_TOKEN_ARG: transaction.token},
        requested_scope="engineering.review.external",
    )
    execution = asyncio.run(manager.execute_typed(request))
    assert real.execute_calls == 0
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE


def test_guard_projects_core_transaction_digest_and_ignores_caller_value():
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": "ok"},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager, _ = _guarded_manager(real, ledger)
    transaction = ledger.mint(seal_review_bundle(_bundle()))
    request = build_review_request(transaction)
    request.arguments["bundle_digest"] = "caller_forged_digest"

    execution = asyncio.run(manager.execute_typed(request))

    assert execution.tool_result.status == ToolResultStatus.SUCCESS
    assert real.execute_calls == 1
    assert real.last_request is not None
    assert real.last_request.arguments["bundle_digest"] == transaction.bundle_digest
    assert real.last_request.arguments["bundle_digest"] != "caller_forged_digest"


def test_mutated_transaction_digest_cannot_reach_real_provider():
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": "must not run"},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager, _ = _guarded_manager(real, ledger)
    transaction = ledger.mint(seal_review_bundle(_bundle()))
    object.__setattr__(transaction, "bundle_digest", "mutated_digest")
    request = build_review_request(transaction)

    execution = asyncio.run(manager.execute_typed(request))

    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert real.execute_calls == 0


# ── Request exactly bound to transaction (§1, Q1-Q4) ─────────────────────────

def test_request_projection_carries_token_and_marker():
    bundle = _bundle()
    snapshot = seal_review_bundle(bundle)
    ledger = ReviewTransactionLedger()
    transaction = ledger.mint(snapshot)
    request = build_review_request(transaction)
    assert request.capability_id == EXTERNAL_REVIEW_CAPABILITY
    assert request.requested_scope == EXTERNAL_REVIEW_SCOPE
    assert request.arguments[REVIEW_TOKEN_ARG] == transaction.token
    assert request.arguments[REVIEW_SEMANTIC_ARG] is True
    assert request.arguments["review_id"] == bundle.review_id
    assert request.arguments["candidate_sha"] == bundle.candidate_sha


def test_request_projection_has_no_snapshot_parameter():
    """§1: caller cannot select a second snapshot (Q1)."""
    import inspect
    params = inspect.signature(build_review_request).parameters
    assert list(params)[0] == "transaction"
    assert "snapshot" not in params


def test_request_projection_rejects_browser_authority_fields():
    ledger = ReviewTransactionLedger()
    bundle = _bundle(
        diff_blocks=(
            {"tab_id": 123, "dom_selector": "#composer", "conversation_url": "https://chatgpt.com/c/1"},
        ),
    )
    snapshot = seal_review_bundle(bundle)
    transaction = ledger.mint(snapshot)
    from julia_core.review.invocation import BrowserAuthorityInRequestError
    with pytest.raises(BrowserAuthorityInRequestError):
        build_review_request(transaction)


def test_request_projection_rejects_nested_browser_authority_fields():
    ledger = ReviewTransactionLedger()
    bundle = _bundle(
        diff_blocks=({"path": "a.py", "content": "x"},),
        limits={"allow_scope_expansion": True, "extension_nonce": "nonce-123"},
    )
    snapshot = seal_review_bundle(bundle)
    transaction = ledger.mint(snapshot)
    from julia_core.review.invocation import BrowserAuthorityInRequestError
    with pytest.raises(BrowserAuthorityInRequestError):
        build_review_request(transaction)


def test_mutating_request_arguments_cannot_change_snapshot_payload():
    """Q2: request.arguments is mutable but is not semantic truth; the guard
    re-derives the provider payload from the trusted snapshot."""
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "ok"},
    ))
    manager, _ = _guarded_manager(real, ledger)

    bundle = _bundle()
    snapshot = seal_review_bundle(bundle)
    transaction = ledger.mint(snapshot)
    request = build_review_request(transaction)
    request.arguments["candidate_sha"] = "FORGED"
    request.arguments["tab_id"] = 999
    from julia_core.capability.models import CapabilityRequestAuthorityError

    # Generic Manager hardening now fails closed before token claim/provider
    # execution when browser authority is injected into a request.
    with pytest.raises(CapabilityRequestAuthorityError, match="browser authority"):
        asyncio.run(manager.execute_typed(request))
    assert real.execute_calls == 0


# ── Governed submission through Manager ──────────────────────────────────────

@pytest.mark.asyncio
async def test_governed_submit_reaches_real_provider_once():
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"raw_response": RAW_RESPONSE},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager, _ = _guarded_manager(real, ledger)
    result = await _governed_submit(manager, ledger)
    assert real.execute_calls == 1
    assert result.outcome_status == "success"
    assert isinstance(result.execution, CapabilityExecution)
    assert result.execution.capability_call is not None
    assert result.execution.evidence
    assert result.tool_result.evidence_refs == tuple(e.evidence_id for e in result.execution.evidence)
    # Trusted invocation registry (I4): submit_review-produced invocation trusted.
    assert is_trusted_invocation(result) is True


@pytest.mark.asyncio
async def test_partial_preserves_partial_payload():
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.PARTIAL,
        structured_output={"raw_response": "partial review text"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    manager, _ = _guarded_manager(real, ledger)
    result = await _governed_submit(manager, ledger)
    assert result.outcome_status == "partial"
    assert result.side_effect_state == "unknown"
    ev = result.execution.evidence[0]
    assert ev.provenance["incomplete"] is True


@pytest.mark.asyncio
async def test_timeout_maps_call_status():
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.TIMEOUT,
        error={"code": "response_complete_timeout", "message": "timed out"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    manager, _ = _guarded_manager(real, ledger)
    result = await _governed_submit(manager, ledger)
    assert result.outcome_status == "timeout"
    assert result.execution.capability_call.status == CapabilityCallStatus.TIMED_OUT


@pytest.mark.asyncio
async def test_unavailable_no_synthetic_evidence():
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.UNAVAILABLE,
        error={"code": "provider_unavailable", "message": "no bound session"},
    ))
    manager, _ = _guarded_manager(real, ledger)
    result = await _governed_submit(manager, ledger)
    assert result.outcome_status == "unavailable"
    assert result.tool_result.evidence_refs == ()
    assert result.execution.evidence == ()


@pytest.mark.asyncio
async def test_error_preserves_exact_error_code():
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "dom_binding_failed", "message": "composer missing"},
    ))
    manager, _ = _guarded_manager(real, ledger)
    result = await _governed_submit(manager, ledger)
    assert result.outcome_status == "error"
    assert result.tool_result.error["code"] == "dom_binding_failed"


@pytest.mark.asyncio
async def test_unknown_side_effect_blocks_auto_retry():
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "may_have_sent", "message": "connection lost after send"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    manager, _ = _guarded_manager(real, ledger)
    result = await _governed_submit(manager, ledger)
    assert result.side_effect_state == "unknown"
    assert real.execute_calls == 1


@pytest.mark.asyncio
async def test_legacy_dict_provider_maps_to_success_none():
    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider({"raw_response": "legacy dict result"})
    manager, _ = _guarded_manager(real, ledger)
    result = await _governed_submit(manager, ledger)
    assert result.outcome_status == "success"
    assert result.side_effect_state == "none"


# ── Permission enforcement (B) ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_denied_scope_never_reaches_provider():
    class DenyPolicy(PermissionPolicy):
        def check(self, scope: str) -> AuthorizationDecision:
            return AuthorizationDecision(decision=AuthorizationStatus.DENY, scope=scope, reason="deny fixture")

    ledger = ReviewTransactionLedger()
    real = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "should not run"},
    ))
    manager, _ = _guarded_manager(real, ledger, policy=DenyPolicy())
    result = await _governed_submit(manager, ledger)
    assert real.execute_calls == 0
    assert result.tool_result is None
    assert result.outcome_status == "denied"
    assert result.execution.capability_call is None


# ── Generic model tool-call path blocked (S2) ────────────────────────────────

def test_model_tool_call_path_cannot_invoke_external_review():
    from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    outcome = bridge.execute_tool_typed(
        '{"name": "engineering.code_review", "arguments": {"review_id": "rvw_x"}}'
    )
    assert outcome is not None
    assert outcome.capability_id == "engineering.code_review"
    assert outcome.reason == "GOVERNED_INGRESS_REQUIRED"


# ── No automatic routing (P4 boundary) ───────────────────────────────────────

def test_no_automatic_routing_entry_points():
    import julia_core.review as review_pkg
    assert not hasattr(review_pkg, "route_from_text")
    assert not hasattr(review_pkg, "requires_tool")
    assert not hasattr(review_pkg, "detect_review_intent")
    from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
    bridge = RuntimeCapabilityBridge()
    assert bridge.requires_tool("把这段 diff 提交给 external review") is False


# ── Production bridge registration ───────────────────────────────────────────

def test_production_bridge_registers_capability_and_fails_closed():
    from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    definition = bridge.registry.get(EXTERNAL_REVIEW_CAPABILITY)
    assert definition is not None
    assert definition.provider == EXTERNAL_REVIEW_PROVIDER
    assert definition.permission_scope == EXTERNAL_REVIEW_SCOPE
    assert "external_review" not in bridge._providers

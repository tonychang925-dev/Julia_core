"""External Code Review — Manager integration / typed invocation tests.

Covers the full canonical lifecycle through CapabilityManager:
  CapabilityDefinition registration -> CapabilityRequest -> AuthorizationDecision
  -> CapabilityCall -> Provider -> ToolResult + Evidence

Plus manual/explicit invocation path (submit_review) and the ProviderExecution
Outcome truth mapping (CRB-PRE-P1 contract preserved for external_review).

Cross-repo seam: the concrete provider is NOT implemented in Core. These tests
use a fixture provider implementing the existing CapabilityProvider protocol,
proving Core lifecycle behaves correctly with typed external_review outcomes.
"""

from __future__ import annotations

from typing import Any

import pytest

from julia_core.capability.manager import CapabilityExecution, CapabilityManager
from julia_core.capability.models import (
    CapabilityCallStatus,
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityProvider,
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
from julia_core.review.invocation import (
    BrowserAuthorityInRequestError,
    EXTERNAL_REVIEW_CAPABILITY,
    EXTERNAL_REVIEW_SCOPE,
    build_review_request,
    submit_review,
)
from julia_core.review.registration import (
    EXTERNAL_REVIEW_PROVIDER,
    register_external_review_capability,
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


class FixtureReviewProvider:
    """Fixture provider implementing CapabilityProvider for external_review.

    Returns whatever outcome is configured. This is a TEST FIXTURE only — it
    proves Core lifecycle truth, not that a real external review works.
    """

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


def _manager(provider: FixtureReviewProvider, policy: PermissionPolicy | None = None) -> CapabilityManager:
    registry = CapabilityRegistry()
    register_external_review_capability(
        registry, policy=policy, status=CapabilityStatus.AVAILABLE
    )
    return CapabilityManager(registry, policy or AllowPolicy(), {EXTERNAL_REVIEW_PROVIDER: provider})


# ── Registration / definition ────────────────────────────────────────────────

def test_definition_registers_with_canonical_shape():
    registry = CapabilityRegistry()
    policy = AllowPolicy()
    definition = register_external_review_capability(registry, policy=policy, status=CapabilityStatus.AVAILABLE)
    assert definition.name == EXTERNAL_REVIEW_CAPABILITY
    assert definition.provider == EXTERNAL_REVIEW_PROVIDER
    assert definition.permission_scope == EXTERNAL_REVIEW_SCOPE
    assert definition.layer == CapabilityLayer.INTELLIGENCE
    assert registry.get(EXTERNAL_REVIEW_CAPABILITY) is definition
    decision = policy.check(EXTERNAL_REVIEW_SCOPE)
    assert decision.decision == AuthorizationStatus.ALLOW


def test_unknown_scope_defaults_to_deny():
    policy = PermissionPolicy()
    decision = policy.check("engineering.review.something.else")
    assert decision.decision == AuthorizationStatus.DENY


# ── build_review_request projection ──────────────────────────────────────────

def test_request_projection_carries_only_semantic_data():
    bundle = _bundle()
    request = build_review_request(bundle)
    assert request.capability_id == EXTERNAL_REVIEW_CAPABILITY
    assert request.requested_scope == EXTERNAL_REVIEW_SCOPE
    assert request.arguments["review_id"] == bundle.review_id
    assert request.arguments["candidate_sha"] == bundle.candidate_sha
    assert request.arguments["bundle_digest"] == compute_bundle_digest(bundle)
    assert request.provenance["browser_authority"] == "NONE"
    assert request.provenance["invocation"] == "manual"
    # No browser authority keys may be present in arguments
    assert "tab_id" not in request.arguments
    assert "conversation_url" not in request.arguments
    assert "dom_selector" not in request.arguments


def test_request_projection_rejects_invalid_bundle():
    with pytest.raises(ValueError):
        build_review_request(ReviewBundle())


def test_request_projection_rejects_browser_authority_fields():
    """Core must never accept browser/session authority in a semantic request."""
    bundle = _bundle(
        diff_blocks=(
            {"tab_id": 123, "dom_selector": "#composer", "conversation_url": "https://chatgpt.com/c/1"},
        ),
    )
    with pytest.raises(BrowserAuthorityInRequestError):
        build_review_request(bundle)


def test_request_projection_rejects_nested_browser_authority_fields():
    """Browser authority hidden in nested payload must also be rejected."""
    bundle = _bundle(
        diff_blocks=({"path": "a.py", "content": "x"},),
        limits={"allow_scope_expansion": True, "extension_nonce": "nonce-123"},
    )
    with pytest.raises(BrowserAuthorityInRequestError):
        build_review_request(bundle)


# ── Typed execution through Manager ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_review_success_returns_typed_execution():
    provider = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={
            "raw_response": "VERDICT: PASS",
            "raw_response_digest": "d" * 64,
            "candidate_sha": "abc123",
        },
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager = _manager(provider)
    result = await submit_review(manager, _bundle())
    assert provider.execute_calls == 1
    assert result.tool_result is not None
    assert result.tool_result.status == ToolResultStatus.SUCCESS
    assert result.tool_result.side_effect_state == SideEffectState.SUCCEEDED
    assert result.tool_result.structured_output["raw_response"] == "VERDICT: PASS"
    # exact canonical artifacts, no legacy string transport
    assert isinstance(result.execution, CapabilityExecution)
    assert result.execution.capability_call is not None
    assert result.execution.evidence
    assert result.tool_result.evidence_refs == tuple(e.evidence_id for e in result.execution.evidence)


@pytest.mark.asyncio
async def test_submit_review_partial_preserves_partial_payload():
    provider = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.PARTIAL,
        structured_output={"raw_response": "partial review text"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    result = await submit_review(_manager(provider), _bundle())
    assert result.outcome_status == "partial"
    assert result.tool_result.structured_output == {"raw_response": "partial review text"}
    assert result.tool_result.side_effect_state == SideEffectState.UNKNOWN
    assert result.execution.evidence
    ev = result.execution.evidence[0]
    assert ev.provenance["incomplete"] is True


@pytest.mark.asyncio
async def test_submit_review_timeout_maps_call_status():
    provider = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.TIMEOUT,
        error={"code": "response_complete_timeout", "message": "timed out"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    result = await submit_review(_manager(provider), _bundle())
    assert result.outcome_status == "timeout"
    assert result.tool_result.error["code"] == "response_complete_timeout"
    assert result.execution.capability_call.status == CapabilityCallStatus.TIMED_OUT


@pytest.mark.asyncio
async def test_submit_review_unavailable_no_synthetic_evidence():
    provider = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.UNAVAILABLE,
        error={"code": "provider_unavailable", "message": "no bound session"},
    ))
    result = await submit_review(_manager(provider), _bundle())
    assert result.outcome_status == "unavailable"
    assert result.tool_result.evidence_refs == ()
    assert result.execution.evidence == ()


@pytest.mark.asyncio
async def test_submit_review_cancelled_maps_call_status():
    provider = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.CANCELLED,
        error={"code": "user_aborted", "message": "aborted"},
    ))
    result = await submit_review(_manager(provider), _bundle())
    assert result.outcome_status == "cancelled"
    assert result.execution.capability_call.status == CapabilityCallStatus.CANCELLED


@pytest.mark.asyncio
async def test_submit_review_error_preserves_exact_error_code():
    provider = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "dom_binding_failed", "message": "composer missing"},
    ))
    result = await submit_review(_manager(provider), _bundle())
    assert result.outcome_status == "error"
    assert result.tool_result.error["code"] == "dom_binding_failed"


@pytest.mark.asyncio
async def test_submit_review_unknown_side_effect_blocks_auto_retry():
    """SideEffectState.UNKNOWN must not produce an automatic retry."""
    provider = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "may_have_sent", "message": "connection lost after send"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    result = await submit_review(_manager(provider), _bundle())
    assert result.side_effect_state == "unknown"
    # Manager invoked the provider exactly once — no auto retry.
    assert provider.execute_calls == 1


@pytest.mark.asyncio
async def test_legacy_dict_provider_maps_to_success_none():
    """Compatibility contract: legacy dict provider -> SUCCESS + SideEffectState.NONE."""
    provider = FixtureReviewProvider({"raw_response": "legacy dict result"})
    result = await submit_review(_manager(provider), _bundle())
    assert result.outcome_status == "success"
    assert result.side_effect_state == "none"
    assert result.tool_result.structured_output == {"raw_response": "legacy dict result"}


# ── Permission enforcement ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_denied_scope_never_reaches_provider():
    class DenyPolicy(PermissionPolicy):
        def check(self, scope: str) -> AuthorizationDecision:
            return AuthorizationDecision(decision=AuthorizationStatus.DENY, scope=scope, reason="deny fixture")

    provider = FixtureReviewProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS, structured_output={"raw_response": "should not run"},
    ))
    manager = _manager(provider, policy=DenyPolicy())
    result = await submit_review(manager, _bundle())
    assert provider.execute_calls == 0
    assert result.tool_result is None
    assert result.outcome_status == "denied"
    assert result.execution.authorization_decision.decision == AuthorizationStatus.DENY
    assert result.execution.capability_call is None
    assert result.execution.evidence == ()


# ── Invocation is manual / explicit only ─────────────────────────────────────

@pytest.mark.asyncio
async def test_production_bridge_registers_capability_and_fails_closed():
    """The production bridge knows engineering.code_review; without the
    cross-repo provider, execution returns UNAVAILABLE — never a fake result."""
    from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge

    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    definition = bridge.registry.get(EXTERNAL_REVIEW_CAPABILITY)
    assert definition is not None
    assert definition.provider == EXTERNAL_REVIEW_PROVIDER
    assert definition.permission_scope == EXTERNAL_REVIEW_SCOPE

    from julia_core.capability.models import CapabilityRequest
    result = await bridge.manager.execute(
        CapabilityRequest("engineering.code_review")
    )
    assert result.status == "unavailable"
    assert "No provider 'external_review' registered" in result.error_message


def test_no_automatic_routing_entry_points():
    """Core exposes NO automatic routing trigger for engineering.code_review.

    The only way in is building a ReviewBundle and explicitly calling
    submit_review / build_review_request. Nothing scans user text, nothing
    auto-selects this capability (P4 boundary preserved).
    """
    import julia_core.review as review_pkg
    assert not hasattr(review_pkg, "route_from_text")
    assert not hasattr(review_pkg, "requires_tool")
    assert not hasattr(review_pkg, "detect_review_intent")
    # The bridge's requires_tool (P4 evidence gate) is untouched by this module:
    # a code-review submission request is NOT auto-routed to any capability.
    from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
    bridge = RuntimeCapabilityBridge()
    assert bridge.requires_tool("把这段 diff 提交给 external review") is False

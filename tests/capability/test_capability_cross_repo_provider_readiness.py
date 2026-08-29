"""Generic cross-repo provider readiness acceptance harness (A1-A12).

These tests describe the boundary a product-owned provider adapter must
implement:

* ``health() -> (bool, detail)`` without performing the capability;
* ``execute(CapabilityRequest) -> ProviderExecutionOutcome``;
* exact SUCCESS/PARTIAL/UNAVAILABLE/ERROR/TIMEOUT/CANCELLED truth;
* exact side-effect truth and no provider-minted DENIED.

They use fixture providers only and never claim real cross-repo E2E.
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
    CapabilityRequestAuthorityError,
    CapabilityStatus,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
    validate_capability_request_authority,
)
from julia_core.capability.policy import (
    AuthorizationDecision,
    AuthorizationStatus,
    PermissionPolicy,
    PermissionRule,
)
from julia_core.capability.registry import CapabilityRegistry
from julia_core.runtime.capability_bridge import (
    ProviderAlreadyRegisteredError,
    RuntimeCapabilityBridge,
)
from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime


class FixtureProvider:
    def __init__(
        self,
        outcome: ProviderExecutionOutcome | Exception | None = None,
        *,
        healthy: bool = True,
        health_detail: str = "fixture ready",
    ):
        self.outcome = outcome
        self.healthy = healthy
        self.health_detail = health_detail
        self.execute_calls = 0

    async def health(self) -> tuple[bool, str]:
        return self.healthy, self.health_detail

    async def execute(self, request: CapabilityRequest):
        self.execute_calls += 1
        if isinstance(self.outcome, Exception):
            raise self.outcome
        if self.outcome is None:
            return ProviderExecutionOutcome(
                status=ToolResultStatus.SUCCESS,
                structured_output={"observable": "real fixture content"},
            )
        return self.outcome


class AllowExactScopePolicy(PermissionPolicy):
    def check(self, scope: str) -> AuthorizationDecision:
        return AuthorizationDecision(
            decision=AuthorizationStatus.ALLOW,
            scope=scope,
            reason="fixture allows the definition-owned scope",
        )


class RecordingPolicy(AllowExactScopePolicy):
    def __init__(self):
        self.checked_scopes: list[str] = []

    def check(self, scope: str) -> AuthorizationDecision:
        self.checked_scopes.append(scope)
        return super().check(scope)


def _definition(provider: str = "product_adapter") -> CapabilityDefinition:
    return CapabilityDefinition(
        name="crossrepo.observe",
        description="Generic cross-repo provider acceptance fixture",
        layer=CapabilityLayer.WORLD,
        provider=provider,
        permission_scope="crossrepo.observe",
        status=CapabilityStatus.AVAILABLE,
    )


def _manager(provider: FixtureProvider | None, *, second: FixtureProvider | None = None):
    registry = CapabilityRegistry()
    registry.register_definition(_definition())
    providers: dict[str, FixtureProvider] = {}
    if provider is not None:
        providers["product_adapter"] = provider
    if second is not None:
        providers["alternate_product_adapter"] = second
    return CapabilityManager(registry, AllowExactScopePolicy(), providers)


async def _run(provider: FixtureProvider | None = None, **kwargs):
    manager = _manager(provider, **kwargs)
    execution = await manager.execute_typed(CapabilityRequest("crossrepo.observe"))
    return manager, execution


@pytest.mark.asyncio
async def test_a1_product_provider_registration_invokes_exact_provider_once():
    bridge = RuntimeCapabilityBridge()
    provider = FixtureProvider()
    bridge.register_provider("product_adapter", provider)
    bridge.registry.register_definition(_definition())
    bridge.policy.add_rule(PermissionRule(
        "crossrepo.observe",
        allow=True,
        reason="fixture-only cross-repo acceptance scope",
    ))
    bridge.initialize()

    execution = bridge.execute_tool_typed(
        '{"name": "crossrepo.observe", "arguments": {"semantic": "input"}}'
    )

    assert provider.execute_calls == 1
    assert execution.tool_result is not None
    assert execution.tool_result.provider == "product_adapter"
    assert "alternate" not in bridge.manager.providers


def test_provider_registration_is_binding_only_and_cannot_be_replaced():
    bridge = RuntimeCapabilityBridge()
    first = FixtureProvider()
    second = FixtureProvider()
    bridge.register_provider("product_adapter", first)
    bridge.register_provider("product_adapter", first)  # idempotent exact object
    with pytest.raises(ProviderAlreadyRegisteredError):
        bridge.register_provider("product_adapter", second)
    assert bridge._providers["product_adapter"] is first


def test_provider_registration_after_manager_composition_updates_exact_binding():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    provider = FixtureProvider()
    bridge.register_provider("later_product_adapter", provider)

    assert bridge.manager.providers["later_product_adapter"] is provider
    with pytest.raises(ProviderAlreadyRegisteredError):
        bridge.register_provider("later_product_adapter", FixtureProvider())
    assert bridge.manager.providers["later_product_adapter"] is provider


@pytest.mark.asyncio
async def test_provider_registration_grants_no_authorization_scope():
    bridge = RuntimeCapabilityBridge()
    provider = FixtureProvider()
    bridge.register_provider("product_adapter", provider)
    bridge.registry.register_definition(_definition())
    bridge.initialize()

    execution = bridge.execute_tool_typed(
        '{"name": "crossrepo.observe", "arguments": {"semantic": "input"}}'
    )

    assert provider.execute_calls == 0
    assert execution.capability_call is None
    assert execution.tool_result is None
    assert execution.authorization_decision is not None
    assert execution.authorization_decision.allowed is False


@pytest.mark.asyncio
async def test_a2_missing_provider_is_unavailable_without_fallback():
    manager, execution = await _run(None)
    assert execution.tool_result is not None
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert execution.tool_result.error["code"] == "provider_not_found"
    assert execution.evidence == ()


@pytest.mark.asyncio
async def test_a3_unhealthy_provider_is_unavailable_before_execute():
    provider = FixtureProvider(healthy=False, health_detail="crossrepo transport not ready")
    manager, execution = await _run(provider)
    assert provider.execute_calls == 0
    assert execution.tool_result is not None
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert execution.tool_result.error["code"] == "provider_unhealthy"
    assert execution.evidence == ()


@pytest.mark.asyncio
async def test_a4_success_preserves_observable_content_and_grounded_evidence():
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"observable": "real fixture content"},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager, execution = await _run(provider)
    result = execution.tool_result
    assert result is not None
    assert result.status == ToolResultStatus.SUCCESS
    assert result.structured_output == {"observable": "real fixture content"}
    assert len(execution.evidence) == 1
    assert result.evidence_refs == (execution.evidence[0].evidence_id,)

    projection = ContextExecutionRuntime().project_tool_result(
        tool_result=result,
        evidence=execution.evidence,
        generation_id="gen_a4",
    )
    assert projection.evidence_frame["source"] == "capability_execution"
    assert projection.evidence_frame["evidence"][0]["content_ref"].startswith("tool_result:")
    assert projection.identity_frame == {}
    assert projection.experience_frame == {}
    assert projection.diary_frame == {}
    assert projection.continuity_frame == {}


@pytest.mark.asyncio
async def test_a5_partial_stays_partial_and_remains_distinguishable():
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.PARTIAL,
        structured_output={"observable": "partial fixture content"},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    manager, execution = await _run(provider)
    result = execution.tool_result
    assert result is not None
    assert result.status == ToolResultStatus.PARTIAL
    assert result.status != ToolResultStatus.SUCCESS
    assert result.evidence_refs != ()
    assert execution.evidence[0].provenance["incomplete"] is True


@pytest.mark.asyncio
async def test_tool_result_correlation_is_preserved_through_exact_call_link():
    provider = FixtureProvider()
    manager = _manager(provider)
    execution = await manager.execute_typed(CapabilityRequest(
        "crossrepo.observe",
        {"semantic": "input"},
        correlation_id="corr_crossrepo_a4",
    ))

    assert execution.capability_call is not None
    assert execution.tool_result is not None
    assert execution.capability_call.correlation_id == "corr_crossrepo_a4"
    assert execution.tool_result.capability_call_id == execution.capability_call.capability_call_id
    assert execution.evidence[0].correlation_id == "corr_crossrepo_a4"


@pytest.mark.asyncio
async def test_a6_error_without_observable_content_has_no_synthetic_evidence():
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        structured_output={},
        error={"code": "crossrepo_error", "message": "provider failed"},
        side_effect_state=SideEffectState.FAILED,
    ))
    manager, execution = await _run(provider)
    assert execution.tool_result is not None
    assert execution.tool_result.status == ToolResultStatus.ERROR
    assert execution.tool_result.error["code"] == "crossrepo_error"
    assert execution.evidence == ()
    assert execution.tool_result.evidence_refs == ()


@pytest.mark.asyncio
async def test_a7_timeout_preserves_timeout_truth():
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.TIMEOUT,
        error={"code": "crossrepo_timeout"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    manager, execution = await _run(provider)
    assert execution.tool_result is not None
    assert execution.tool_result.status == ToolResultStatus.TIMEOUT
    assert execution.capability_call is not None
    assert execution.capability_call.status == CapabilityCallStatus.TIMED_OUT
    assert execution.evidence == ()


@pytest.mark.asyncio
async def test_a8_cancelled_preserves_cancelled_truth():
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.CANCELLED,
        side_effect_state=SideEffectState.FAILED,
    ))
    manager, execution = await _run(provider)
    assert execution.tool_result is not None
    assert execution.tool_result.status == ToolResultStatus.CANCELLED
    assert execution.capability_call is not None
    assert execution.capability_call.status == CapabilityCallStatus.CANCELLED
    assert execution.evidence == ()


@pytest.mark.asyncio
async def test_a9_unknown_side_effect_is_preserved_and_never_autoretried():
    provider = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "possibly_executed"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    manager, execution = await _run(provider)
    assert provider.execute_calls == 1
    assert execution.tool_result is not None
    assert execution.tool_result.side_effect_state == SideEffectState.UNKNOWN
    # One explicit manager invocation causes exactly one provider execution.
    assert manager.capability_calls[-1].status == CapabilityCallStatus.FAILED


def test_a10_provider_cannot_mint_denied_authority():
    with pytest.raises(ValueError, match="authorization truth"):
        ProviderExecutionOutcome(status=ToolResultStatus.DENIED)


@pytest.mark.asyncio
async def test_a10_legacy_dict_denied_cannot_become_success_or_denied_authority():
    provider = FixtureProvider({"status": "denied", "error": "provider attempted denial"})
    manager = _manager(provider)
    execution = await manager.execute_typed(CapabilityRequest("crossrepo.observe"))

    assert provider.execute_calls == 1
    assert execution.tool_result is not None
    assert execution.tool_result.status == ToolResultStatus.ERROR
    assert execution.tool_result.error["code"] == "provider_exception"
    assert execution.tool_result.side_effect_state == SideEffectState.UNKNOWN
    assert execution.evidence == ()


@pytest.mark.asyncio
async def test_a11_unexpected_exception_is_conservative_error_unknown():
    provider = FixtureProvider(RuntimeError("crossrepo transport failed after attempt"))
    manager, execution = await _run(provider)
    assert provider.execute_calls == 1
    result = execution.tool_result
    assert result is not None
    assert result.status == ToolResultStatus.ERROR
    assert result.error["code"] == "provider_exception"
    assert result.side_effect_state == SideEffectState.UNKNOWN
    assert execution.evidence == ()


@pytest.mark.asyncio
async def test_a12_primary_failure_does_not_fall_back_to_second_provider():
    primary = FixtureProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "primary_failed"},
        side_effect_state=SideEffectState.FAILED,
    ))
    alternate = FixtureProvider()
    manager, execution = await _run(primary, second=alternate)
    assert primary.execute_calls == 1
    assert alternate.execute_calls == 0
    assert execution.tool_result is not None
    assert execution.tool_result.provider == "product_adapter"
    assert execution.tool_result.status == ToolResultStatus.ERROR


@pytest.mark.asyncio
async def test_request_cannot_carry_provider_transport_or_browser_authority():
    provider = FixtureProvider()
    manager = _manager(provider)
    malicious = CapabilityRequest(
        "crossrepo.observe",
        {
            "semantic": "input",
            "selected_provider": "alternate_product_adapter",
            "nested": {"tab_id": 123, "dom_selector": "#composer"},
        },
        provenance={"endpoint": "https://product-internal"},
    )
    with pytest.raises(CapabilityRequestAuthorityError):
        await manager.execute_typed(malicious)
    assert provider.execute_calls == 0


@pytest.mark.asyncio
async def test_caller_requested_scope_does_not_override_definition_scope():
    provider = FixtureProvider()
    registry = CapabilityRegistry()
    registry.register_definition(_definition())
    policy = RecordingPolicy()
    manager = CapabilityManager(registry, policy, {"product_adapter": provider})

    execution = await manager.execute_typed(CapabilityRequest(
        "crossrepo.observe",
        {"semantic": "input"},
        requested_scope="caller.selected.scope",
    ))

    assert policy.checked_scopes == ["crossrepo.observe"]
    assert execution.capability_call is not None
    assert execution.capability_call.provenance["permission_scope"] == "crossrepo.observe"


def test_request_authority_validator_rejects_nested_browser_authority():
    request = CapabilityRequest("crossrepo.observe", {"semantic": {"tab_id": 1}})
    with pytest.raises(CapabilityRequestAuthorityError, match="browser authority"):
        validate_capability_request_authority(request)

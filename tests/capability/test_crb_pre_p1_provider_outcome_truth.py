"""CRB-PRE-P1 ProviderOutcome + side-effect truth acceptance tests.

TC-ID: CRB-PRE-P1-T1 legacy dict provider -> SUCCESS + NONE
TC-ID: CRB-PRE-P1-T2 typed SUCCESS -> exact ToolResult SUCCESS
TC-ID: CRB-PRE-P1-T3 typed PARTIAL -> exact PARTIAL + evidence preserved
TC-ID: CRB-PRE-P1-T4 typed TIMEOUT -> CapabilityCall TIMED_OUT
TC-ID: CRB-PRE-P1-T5 typed CANCELLED -> CapabilityCall CANCELLED
TC-ID: CRB-PRE-P1-T6 typed UNAVAILABLE -> no synthetic Evidence
TC-ID: CRB-PRE-P1-T7 typed ERROR -> exact error code preserved
TC-ID: CRB-PRE-P1-T8 side_effect_state exact propagation
TC-ID: CRB-PRE-P1-T9 generic exception -> ERROR + UNKNOWN side effect
TC-ID: CRB-PRE-P1-T10 provider cannot synthesize DENIED/UNKNOWN/invalid status
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


class OutcomeProvider:
    def __init__(self, outcome: dict[str, Any] | ProviderExecutionOutcome | Exception):
        self.outcome = outcome
        self.health_calls = 0
        self.execute_calls = 0

    async def health(self) -> tuple[bool, str]:
        self.health_calls += 1
        return True, "ok"

    async def execute(self, request: CapabilityRequest) -> dict[str, Any] | ProviderExecutionOutcome:
        self.execute_calls += 1
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class AllowPolicy(PermissionPolicy):
    def check(self, scope: str) -> AuthorizationDecision:
        return AuthorizationDecision(decision=AuthorizationStatus.ALLOW, scope=scope, reason="allow fixture")


def _manager(provider: OutcomeProvider) -> CapabilityManager:
    registry = CapabilityRegistry()
    registry.register_definition(CapabilityDefinition(
        name="fixture.observe",
        description="CRB provider outcome fixture",
        layer=CapabilityLayer.WORLD,
        provider="fixture_provider",
        permission_scope="fixture.observe",
        status=CapabilityStatus.AVAILABLE,
    ))
    return CapabilityManager(registry, AllowPolicy(), {"fixture_provider": provider})


async def _execute(outcome):
    provider = OutcomeProvider(outcome)
    manager = _manager(provider)
    execution = await manager.execute_typed(CapabilityRequest("fixture.observe"))
    assert provider.execute_calls == 1
    assert execution.tool_result is not None
    assert execution.capability_call is not None
    return manager, provider, execution


@pytest.mark.asyncio
async def test_t1_legacy_dict_provider_normalizes_to_success_and_none():
    manager, provider, execution = await _execute({"observed": True})
    assert execution.tool_result.status == ToolResultStatus.SUCCESS
    assert execution.tool_result.side_effect_state == SideEffectState.NONE
    assert execution.tool_result.structured_output == {"observed": True}
    legacy = await manager.execute(CapabilityRequest("fixture.observe"))
    assert legacy.status == "success"
    assert provider.execute_calls == 2


@pytest.mark.asyncio
async def test_t2_typed_success_preserves_exact_success():
    _, _, execution = await _execute(ProviderExecutionOutcome(
        status=ToolResultStatus.SUCCESS,
        structured_output={"ok": True},
    ))
    assert execution.tool_result.status == ToolResultStatus.SUCCESS
    assert execution.capability_call.status == CapabilityCallStatus.COMPLETED
    assert execution.tool_result.structured_output == {"ok": True}


@pytest.mark.asyncio
async def test_t3_typed_partial_preserves_payload_and_partial_evidence():
    _, _, execution = await _execute(ProviderExecutionOutcome(
        status=ToolResultStatus.PARTIAL,
        structured_output={"raw_response": "partial review text"},
        side_effect_state=SideEffectState.SUCCEEDED,
    ))
    assert execution.tool_result.status == ToolResultStatus.PARTIAL
    assert execution.capability_call.status == CapabilityCallStatus.COMPLETED
    assert execution.tool_result.structured_output == {"raw_response": "partial review text"}
    assert execution.evidence
    ev = execution.evidence[0]
    assert execution.tool_result.evidence_refs == (ev.evidence_id,)
    assert ev.provenance["provider_outcome_status"] == "partial"
    assert ev.provenance["provider_material_observed"] is True
    assert ev.provenance["incomplete"] is True


@pytest.mark.asyncio
async def test_t4_typed_timeout_maps_call_status_timed_out_and_legacy_error():
    provider = OutcomeProvider(ProviderExecutionOutcome(
        status=ToolResultStatus.TIMEOUT,
        error={"code": "response_complete_timeout", "message": "timed out"},
        side_effect_state=SideEffectState.UNKNOWN,
    ))
    manager = _manager(provider)
    legacy = await manager.execute(CapabilityRequest("fixture.observe"))
    result = manager.tool_results[-1]
    call = manager.capability_calls[-1]
    assert result.status == ToolResultStatus.TIMEOUT
    assert call.status == CapabilityCallStatus.TIMED_OUT
    assert legacy.status == "error"


@pytest.mark.asyncio
async def test_t5_typed_cancelled_maps_call_status_cancelled_and_legacy_error():
    manager, _, execution = await _execute(ProviderExecutionOutcome(
        status=ToolResultStatus.CANCELLED,
        error={"code": "user_aborted", "message": "aborted"},
    ))
    assert execution.tool_result.status == ToolResultStatus.CANCELLED
    assert execution.capability_call.status == CapabilityCallStatus.CANCELLED
    legacy = manager._legacy_from_tool_result(CapabilityRequest("fixture.observe"), execution.tool_result)
    assert legacy.status == "error"


@pytest.mark.asyncio
async def test_t6_unavailable_with_no_content_has_no_synthetic_evidence():
    _, _, execution = await _execute(ProviderExecutionOutcome(
        status=ToolResultStatus.UNAVAILABLE,
        error={"code": "provider_unavailable", "message": "no tab"},
    ))
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert execution.capability_call.status == CapabilityCallStatus.FAILED
    assert execution.tool_result.evidence_refs == ()
    assert execution.evidence == ()


@pytest.mark.asyncio
async def test_t7_error_preserves_exact_error_code():
    _, _, execution = await _execute(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "dom_binding_failed", "message": "composer missing"},
    ))
    assert execution.tool_result.status == ToolResultStatus.ERROR
    assert execution.tool_result.error["code"] == "dom_binding_failed"


@pytest.mark.parametrize("side_effect", [
    SideEffectState.SUCCEEDED,
    SideEffectState.FAILED,
    SideEffectState.UNKNOWN,
])
@pytest.mark.asyncio
async def test_t8_side_effect_state_passes_unchanged(side_effect: SideEffectState):
    _, _, execution = await _execute(ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        error={"code": "fixture", "message": "fixture"},
        side_effect_state=side_effect,
    ))
    assert execution.tool_result.side_effect_state == side_effect


@pytest.mark.asyncio
async def test_t9_generic_provider_exception_is_error_with_unknown_side_effect():
    _, _, execution = await _execute(RuntimeError("boom after execute entered"))
    assert execution.tool_result.status == ToolResultStatus.ERROR
    assert execution.tool_result.side_effect_state == SideEffectState.UNKNOWN
    assert execution.tool_result.evidence_refs == ()


@pytest.mark.parametrize("bad_status", [
    ToolResultStatus.DENIED,
    ToolResultStatus.UNKNOWN,
    "random string",
])
@pytest.mark.asyncio
async def test_t10_provider_cannot_synthesize_denied_unknown_or_invalid_status(bad_status):
    outcome = ProviderExecutionOutcome(status=ToolResultStatus.SUCCESS, structured_output={"should_not": "evidence"})
    object.__setattr__(outcome, "status", bad_status)
    manager, provider, execution = await _execute(outcome)
    assert provider.execute_calls == 1
    assert execution.tool_result.status == ToolResultStatus.ERROR
    assert execution.tool_result.error["code"] == "provider_exception"
    assert "provider outcome status" in execution.tool_result.error["message"]
    assert execution.tool_result.evidence_refs == ()
    assert execution.evidence == ()
    assert manager.authorization_decisions[-1].decision == AuthorizationStatus.ALLOW

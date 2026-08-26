"""R2-P1B Manager canonical lifecycle acceptance overlay.

Protected contracts: C-08 / C-12 / R2-P1B Core Mutation Review.
Expected before R2-P1B.1: strict XFAIL for Manager lifecycle migration gaps.
Resolving phase: R2-P1B.1.

This overlay is intentionally additive. It does not modify frozen C1 REV2
contract tests. It pins the smallest safe Manager-only production migration:
CapabilityRequest -> AuthorizationDecision -> CapabilityCall -> Provider ->
ToolResult + Evidence, while preserving legacy CapabilityResult compatibility.
"""

from __future__ import annotations

from typing import Any

import pytest

from julia_core.capability.manager import CapabilityManager
from julia_core.capability.models import (
    CapabilityCall,
    CapabilityCallStatus,
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityRequest,
    CapabilityResult,
    CapabilityStatus,
    Evidence,
    ToolResult,
)
from julia_core.capability.policy import AuthorizationDecision, AuthorizationStatus, PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry


class RecordingProvider:
    def __init__(
        self,
        *,
        healthy: bool = True,
        data: dict[str, Any] | None = None,
        raises: Exception | None = None,
    ):
        self.healthy = healthy
        self.data = data if data is not None else {"observed": True, "source_records": [{"source_name": "fixture"}]}
        self.raises = raises
        self.health_calls = 0
        self.execute_calls = 0

    async def health(self) -> tuple[bool, str]:
        self.health_calls += 1
        return self.healthy, "ok" if self.healthy else "fixture unhealthy"

    async def execute(self, request: CapabilityRequest) -> dict[str, Any]:
        self.execute_calls += 1
        if self.raises is not None:
            raise self.raises
        return self.data


class FixedDecisionPolicy(PermissionPolicy):
    def __init__(self, decision: AuthorizationStatus):
        super().__init__()
        self._decision = decision
        self.checked_scopes: list[str] = []

    def check(self, scope: str) -> AuthorizationDecision:
        self.checked_scopes.append(scope)
        return AuthorizationDecision(
            decision=self._decision,
            scope=scope,
            reason=f"fixture {self._decision.value}",
            policy_ref="p1b-fixture",
            provenance={"fixture": "FixedDecisionPolicy"},
        )


def _registry(*, provider: str = "fixture_provider") -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register_definition(CapabilityDefinition(
        name="fixture.observe",
        description="R2-P1B fixture read-only observation",
        layer=CapabilityLayer.WORLD,
        provider=provider,
        permission_scope="fixture.observe",
        status=CapabilityStatus.AVAILABLE,
        schema_version="1.0",
    ))
    return registry


def _manager(
    *,
    decision: AuthorizationStatus = AuthorizationStatus.ALLOW,
    provider: RecordingProvider | None = None,
    providers: dict[str, RecordingProvider] | None = None,
) -> CapabilityManager:
    provider = provider or RecordingProvider()
    return CapabilityManager(
        _registry(),
        FixedDecisionPolicy(decision),
        providers if providers is not None else {"fixture_provider": provider},
    )


def _canonical_calls(manager: CapabilityManager) -> list[CapabilityCall]:
    return list(getattr(manager, "capability_calls"))


def _tool_results(manager: CapabilityManager) -> list[ToolResult]:
    return list(getattr(manager, "tool_results"))


def _canonical_evidence(manager: CapabilityManager) -> list[Evidence]:
    return list(getattr(manager, "canonical_evidence"))


@pytest.mark.asyncio
async def test_allow_provider_success_creates_call_tool_result_and_linked_evidence():
    provider = RecordingProvider(data={"observed": True, "value": 42})
    manager = _manager(provider=provider)

    legacy = await manager.execute(CapabilityRequest("fixture.observe", {"kind": "snapshot"}))

    assert isinstance(legacy, CapabilityResult)
    assert legacy.status == "success"
    assert provider.execute_calls == 1

    calls = _canonical_calls(manager)
    results = _tool_results(manager)
    evidence = _canonical_evidence(manager)

    assert len(calls) == 1
    assert calls[0].status in {CapabilityCallStatus.COMPLETED, CapabilityCallStatus.COMPLETED.value}
    assert len(results) == 1
    assert results[0].capability_call_id == calls[0].capability_call_id
    assert results[0].status == "success"
    assert results[0].structured_output == {"observed": True, "value": 42}
    assert len(evidence) == 1
    assert results[0].evidence_refs == (evidence[0].evidence_id,)
    assert evidence[0].source_type == "TOOL_OBSERVATION"


@pytest.mark.asyncio
async def test_deny_creates_authorization_decision_only_and_no_execution_artifacts():
    provider = RecordingProvider(data={"should_not": "execute"})
    manager = _manager(decision=AuthorizationStatus.DENY, provider=provider)

    legacy = await manager.execute(CapabilityRequest("fixture.observe"))

    assert legacy.status == "denied"
    assert provider.health_calls == 0
    assert provider.execute_calls == 0
    assert getattr(manager, "authorization_decisions")[-1].decision == AuthorizationStatus.DENY
    assert _canonical_calls(manager) == []
    assert _tool_results(manager) == []
    assert _canonical_evidence(manager) == []


@pytest.mark.parametrize("decision", [AuthorizationStatus.REQUIRE_CONFIRMATION, AuthorizationStatus.REQUIRE_ELEVATION])
@pytest.mark.asyncio
async def test_confirmation_or_elevation_do_not_enter_execution(decision: AuthorizationStatus):
    provider = RecordingProvider(data={"should_not": "execute"})
    manager = _manager(decision=decision, provider=provider)

    legacy = await manager.execute(CapabilityRequest("fixture.observe"))

    assert legacy.status == "denied"
    assert provider.health_calls == 0
    assert provider.execute_calls == 0
    assert getattr(manager, "authorization_decisions")[-1].decision == decision
    assert _canonical_calls(manager) == []
    assert _tool_results(manager) == []
    assert _canonical_evidence(manager) == []


@pytest.mark.asyncio
async def test_missing_provider_after_allow_creates_unavailable_tool_result_without_evidence():
    manager = _manager(providers={})

    legacy = await manager.execute(CapabilityRequest("fixture.observe"))

    assert legacy.status == "unavailable"
    calls = _canonical_calls(manager)
    results = _tool_results(manager)
    evidence = _canonical_evidence(manager)
    assert len(calls) == 1
    assert len(results) == 1
    assert results[0].capability_call_id == calls[0].capability_call_id
    assert results[0].status == "unavailable"
    assert results[0].evidence_refs == ()
    assert evidence == []


@pytest.mark.asyncio
async def test_unhealthy_provider_after_allow_does_not_execute_and_creates_unavailable_result():
    provider = RecordingProvider(healthy=False, data={"should_not": "execute"})
    manager = _manager(provider=provider)

    legacy = await manager.execute(CapabilityRequest("fixture.observe"))

    assert legacy.status == "unavailable"
    assert provider.health_calls == 1
    assert provider.execute_calls == 0
    calls = _canonical_calls(manager)
    results = _tool_results(manager)
    assert len(calls) == 1
    assert len(results) == 1
    assert results[0].status == "unavailable"
    assert results[0].evidence_refs == ()
    assert _canonical_evidence(manager) == []


@pytest.mark.asyncio
async def test_provider_exception_creates_error_tool_result_and_no_fabricated_evidence():
    provider = RecordingProvider(raises=RuntimeError("fixture boom"))
    manager = _manager(provider=provider)

    legacy = await manager.execute(CapabilityRequest("fixture.observe"))

    assert legacy.status == "error"
    assert provider.execute_calls == 1
    calls = _canonical_calls(manager)
    results = _tool_results(manager)
    evidence = _canonical_evidence(manager)
    assert len(calls) == 1
    assert calls[0].status in {CapabilityCallStatus.FAILED, CapabilityCallStatus.FAILED.value}
    assert len(results) == 1
    assert results[0].status == "error"
    assert results[0].error is not None
    assert results[0].evidence_refs == ()
    assert evidence == []


@pytest.mark.asyncio
async def test_tool_result_evidence_refs_resolve_to_actual_canonical_evidence_ids():
    manager = _manager(provider=RecordingProvider(data={"observed": "material"}))

    await manager.execute(CapabilityRequest("fixture.observe"))

    result = _tool_results(manager)[0]
    evidence_by_id = {entry.evidence_id: entry for entry in _canonical_evidence(manager)}
    assert result.evidence_refs
    assert set(result.evidence_refs) <= set(evidence_by_id)


@pytest.mark.asyncio
async def test_legacy_capability_result_remains_compatible_and_derived_from_canonical_artifacts():
    manager = _manager(provider=RecordingProvider(data={"observed": "material"}))

    legacy = await manager.execute(CapabilityRequest("fixture.observe"))

    result = _tool_results(manager)[0]
    assert isinstance(legacy, CapabilityResult)
    assert legacy.status == result.status
    assert legacy.data == result.structured_output
    assert legacy.provider == result.provider
    assert legacy.capability_name == "fixture.observe"


@pytest.mark.parametrize(
    "provider,providers,expected_status",
    [
        (RecordingProvider(healthy=False), None, "unavailable"),
        (None, {}, "unavailable"),
        (RecordingProvider(raises=RuntimeError("fixture boom")), None, "error"),
    ],
)
@pytest.mark.asyncio
async def test_unsuccessful_execution_never_fabricates_tool_observation_evidence(
    provider: RecordingProvider | None,
    providers: dict[str, RecordingProvider] | None,
    expected_status: str,
):
    manager = _manager(provider=provider, providers=providers)

    legacy = await manager.execute(CapabilityRequest("fixture.observe"))

    assert legacy.status == expected_status
    assert _canonical_evidence(manager) == []
    assert all(result.evidence_refs == () for result in _tool_results(manager))

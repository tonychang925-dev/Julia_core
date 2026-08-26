"""C1-R2.5 Authorization and result semantics contracts.

Protected contracts: C-08 / C-12 / REV2 R2-I04/R2-I05/R2-I06/R2-I10
Expected baseline: PASS for existing fail-closed denial/unavailable/error
separation; XFAIL for frozen AuthorizationDecision and typed
CapabilityCall/ToolResult/Evidence convergence.
Known gaps: B-01, B-02, B-03, C-02/C-03 from conformance audit
Resolving phase: R2-P1 / R2-P2 / R2-P7

TC-ID: C1-R2.5-AUTH-001 AuthorizationDecision is a first-class object, not bool only
TC-ID: C1-R2.5-AUTH-002 confirmation/elevation are distinct from deny/error
TC-ID: C1-R2.5-AUTH-003 authorization denial is not execution failure
TC-ID: C1-R2.5-RESULT-001 unavailable is distinct from denied and error
TC-ID: C1-R2.5-RESULT-002 provider failure must not become successful evidence
TC-ID: C1-R2.5-RESULT-003 CapabilityCall, ToolResult, Evidence remain separated

These tests intentionally avoid production mutation. They pin the semantics that
sync/stream parity must later share; parity must not unify two paths into the
same legacy flattening mistake.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

import pytest

from julia_core.capability import models as capability_models
from julia_core.capability import policy as capability_policy
from julia_core.capability.manager import CapabilityManager
from julia_core.capability.models import CapabilityDefinition, CapabilityLayer, CapabilityRequest, CapabilityResult, CapabilityStatus
from julia_core.capability.policy import PermissionPolicy, PermissionRule
from julia_core.capability.registry import CapabilityRegistry


class RecordingProvider:
    def __init__(self, *, healthy: bool = True, raises: Exception | None = None, data: dict[str, Any] | None = None):
        self.healthy = healthy
        self.raises = raises
        self.data = data or {"observed": True}
        self.health_calls = 0
        self.execute_calls = 0

    async def health(self) -> tuple[bool, str]:
        self.health_calls += 1
        return self.healthy, "fixture unavailable" if not self.healthy else "ok"

    async def execute(self, request: CapabilityRequest) -> dict[str, Any]:
        self.execute_calls += 1
        if self.raises:
            raise self.raises
        return self.data


def _registry_with(name: str, provider: str, scope: str, status: CapabilityStatus = CapabilityStatus.AVAILABLE) -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register_definition(CapabilityDefinition(
        name=name,
        description="C1-R2.5 fixture capability",
        layer=CapabilityLayer.WORLD,
        provider=provider,
        permission_scope=scope,
        status=status,
    ))
    return registry


def _dataclass_fields(cls: type[Any]) -> set[str]:
    assert is_dataclass(cls), f"{cls!r} must be a dataclass contract object"
    return {f.name for f in fields(cls)}


@pytest.mark.xfail(
    strict=True,
    reason="B-03/C-08: AuthorizationDecision is not first-class; PermissionPolicy still returns (bool, reason); pending R2-P1/R2-P2",
)
def test_authorization_decision_is_first_class_not_bool_tuple():
    """TC-ID: C1-R2.5-AUTH-001. Authorization result must carry decision semantics."""
    AuthorizationDecision = getattr(capability_policy, "AuthorizationDecision")
    actual = _dataclass_fields(AuthorizationDecision)
    assert {"decision", "scope", "reason", "policy_ref", "requested_at", "provenance"} <= actual


@pytest.mark.xfail(
    strict=True,
    reason="B-03/C-08: policy lacks ALLOW/DENY/REQUIRE_CONFIRMATION/REQUIRE_ELEVATION/UNAVAILABLE decision enum; pending R2-P1/R2-P2",
)
def test_authorization_statuses_include_confirmation_and_elevation():
    """TC-ID: C1-R2.5-AUTH-002. Confirmation/elevation are not deny/error aliases."""
    AuthorizationStatus = getattr(capability_policy, "AuthorizationStatus")
    assert issubclass(AuthorizationStatus, Enum)
    assert {"ALLOW", "DENY", "REQUIRE_CONFIRMATION", "REQUIRE_ELEVATION", "UNAVAILABLE"} <= set(AuthorizationStatus.__members__)


@pytest.mark.xfail(
    strict=True,
    reason="B-03/C-08: PermissionPolicy.check currently returns tuple[bool, str], not AuthorizationDecision; pending R2-P1/R2-P2",
)
def test_permission_policy_check_returns_authorization_decision_object():
    """TC-ID: C1-R2.5-AUTH-001. Policy check output must be auditable, not bool-only."""
    decision = PermissionPolicy.with_defaults().check("system.read")
    assert decision.__class__.__name__ == "AuthorizationDecision"
    assert decision.decision == "ALLOW"
    assert decision.scope == "system.read"


@pytest.mark.asyncio
async def test_authorization_denial_is_not_execution_failure_and_does_not_call_provider():
    """TC-ID: C1-R2.5-AUTH-003. Denied capability must not execute provider or become error."""
    provider = RecordingProvider(data={"should_not": "execute"})
    registry = _registry_with("trade.execute", "fixture_provider", "market.trade.execute")
    manager = CapabilityManager(registry, PermissionPolicy.with_defaults(), {"fixture_provider": provider})

    result = await manager.execute(CapabilityRequest("trade.execute", {"symbol": "TEST"}))

    assert result.status == "denied"
    assert result.error_message
    assert result.data == {}
    assert provider.health_calls == 0
    assert provider.execute_calls == 0
    last = manager.evidence.last()
    assert last is not None
    assert last.status == "denied"


@pytest.mark.asyncio
async def test_unavailable_provider_is_distinct_from_denied_and_error():
    """TC-ID: C1-R2.5-RESULT-001. Provider unavailable remains explicit unavailable."""
    registry = _registry_with("system.time.read", "missing_provider", "system.read")
    manager = CapabilityManager(registry, PermissionPolicy.with_defaults(), {})

    result = await manager.execute(CapabilityRequest("system.time.read"))

    assert result.status == "unavailable"
    assert result.status != "denied"
    assert result.status != "error"
    assert result.provider == "missing_provider"
    assert result.data == {}


@pytest.mark.asyncio
async def test_unhealthy_provider_is_unavailable_not_denied_or_error():
    """TC-ID: C1-R2.5-RESULT-001. Failed health check is unavailable and does not execute."""
    provider = RecordingProvider(healthy=False)
    registry = _registry_with("system.time.read", "fixture_provider", "system.read")
    manager = CapabilityManager(registry, PermissionPolicy.with_defaults(), {"fixture_provider": provider})

    result = await manager.execute(CapabilityRequest("system.time.read"))

    assert result.status == "unavailable"
    assert result.status != "denied"
    assert result.status != "error"
    assert provider.health_calls == 1
    assert provider.execute_calls == 0
    last = manager.evidence.last()
    assert last is not None
    assert last.status == "unavailable"


@pytest.mark.asyncio
async def test_provider_exception_is_error_not_successful_evidence():
    """TC-ID: C1-R2.5-RESULT-002. Provider failure must not become successful evidence."""
    provider = RecordingProvider(raises=RuntimeError("fixture boom"))
    registry = _registry_with("system.time.read", "fixture_provider", "system.read")
    manager = CapabilityManager(registry, PermissionPolicy.with_defaults(), {"fixture_provider": provider})

    result = await manager.execute(CapabilityRequest("system.time.read"))

    assert result.status == "error"
    assert result.status != "success"
    assert result.data == {}
    assert "fixture boom" in result.error_message
    last = manager.evidence.last()
    assert last is not None
    assert last.status == "error"
    assert last.status != "success"


@pytest.mark.xfail(
    strict=True,
    reason="C-08/C-12: CapabilityCall and ToolResult are not first-class objects yet; current CapabilityResult flattens execution/data/evidence; pending R2-P1",
)
def test_capability_call_tool_result_and_evidence_are_separate_contract_objects():
    """TC-ID: C1-R2.5-RESULT-003. Request/call/result/evidence must not collapse."""
    CapabilityCall = getattr(capability_models, "CapabilityCall")
    ToolResult = getattr(capability_models, "ToolResult")
    CapabilityEvidence = getattr(capability_models, "CapabilityEvidence")

    call_fields = _dataclass_fields(CapabilityCall)
    result_fields = _dataclass_fields(ToolResult)
    evidence_fields = _dataclass_fields(CapabilityEvidence)

    assert "capability_call_id" in call_fields
    assert "capability_call_id" in result_fields
    assert "evidence_refs" in result_fields
    assert "content_ref" in evidence_fields
    assert "structured_output" not in evidence_fields


@pytest.mark.xfail(
    strict=True,
    reason="C-08/C-12: legacy CapabilityResult still carries data/evidence instead of typed ToolResult + evidence_refs; pending R2-P1",
)
def test_legacy_capability_result_does_not_claim_final_tool_result_contract():
    """TC-ID: C1-R2.5-RESULT-003. CapabilityResult must not remain the canonical result shape."""
    actual = _dataclass_fields(CapabilityResult)
    assert "structured_output" in actual
    assert "evidence_refs" in actual
    assert "data" not in actual
    assert "evidence" not in actual

"""R2-P3.2.0 Manager typed execution bundle acceptance overlay.

Protected contracts: C-08 / C-12 / P3.2 typed delivery design.

This overlay pins the future typed Manager execution spine WITHOUT
implementing it. P3.2.1 will return, per execution transaction, ONE immutable
typed carrier holding the exact:

  AuthorizationDecision / CapabilityCall / ToolResult / Evidence[]

belonging to that single execution — never "latest", never [-1], never
full-list scanning by the consumer, never caller-controlled ordering.

Legacy CapabilityResult compatibility is preserved (PASS guard below); the
typed path must become the single canonical execution spine with the legacy
result derived from it.

UNKNOWN / DISABLED pre-authorization resolution is explicitly DEFERRED: these
paths currently return legacy unknown/denied WITHOUT an AuthorizationDecision
and must NOT be coerced into a fabricated decision merely to fit the typed
bundle. No CapabilityResolutionOutcome is invented in this slice.
"""

from __future__ import annotations

from typing import Any

import pytest

from julia_core.capability.manager import CapabilityManager
from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityRequest,
    CapabilityResult,
    CapabilityStatus,
)
from julia_core.capability.policy import AuthorizationDecision, AuthorizationStatus, PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry


class RecordingProvider:
    def __init__(self, *, healthy: bool = True, data: dict[str, Any] | None = None,
                 raises: Exception | None = None):
        self.healthy = healthy
        self.data = data if data is not None else {"observed": True}
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

    def check(self, scope: str) -> AuthorizationDecision:
        return AuthorizationDecision(
            decision=self._decision,
            scope=scope,
            reason=f"fixture {self._decision.value}",
        )


def _registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register_definition(CapabilityDefinition(
        name="fixture.observe",
        description="R2-P3.2 fixture read-only observation",
        layer=CapabilityLayer.WORLD,
        provider="fixture_provider",
        permission_scope="fixture.observe",
        status=CapabilityStatus.AVAILABLE,
    ))
    return registry


def _manager(*, decision: AuthorizationStatus = AuthorizationStatus.ALLOW,
             provider: RecordingProvider | None = None,
             providers: dict[str, RecordingProvider] | None = None) -> CapabilityManager:
    provider = provider or RecordingProvider()
    return CapabilityManager(
        _registry(),
        FixedDecisionPolicy(decision),
        providers if providers is not None else {"fixture_provider": provider},
    )


# ── PASS guard: legacy compatibility ──────────────────────────────────────

@pytest.mark.asyncio
async def test_manager_execute_still_returns_legacy_capability_result():
    manager = _manager(provider=RecordingProvider(data={"observed": "material"}))
    legacy = await manager.execute(CapabilityRequest("fixture.observe"))
    assert isinstance(legacy, CapabilityResult)
    assert legacy.status == "success"


# ── strict-XFAIL: typed execution bundle ──────────────────────────────────

@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2: manager typed execution bundle (execute_typed) not implemented",
)
@pytest.mark.asyncio
async def test_manager_execute_typed_returns_exact_bundle_for_success():
    provider = RecordingProvider(data={"observed": True, "value": 42})
    manager = _manager(provider=provider)

    bundle = await manager.execute_typed(CapabilityRequest("fixture.observe", {"kind": "snapshot"}))

    assert bundle.capability_call is not None
    assert bundle.tool_result is not None
    assert bundle.tool_result.capability_call_id == bundle.capability_call.capability_call_id
    assert bundle.tool_result.status == "success"
    assert bundle.tool_result.structured_output == {"observed": True, "value": 42}
    assert bundle.evidence
    assert bundle.tool_result.evidence_refs == tuple(e.evidence_id for e in bundle.evidence)


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2: manager typed execution bundle (execute_typed) not implemented",
)
@pytest.mark.asyncio
async def test_manager_typed_bundle_associates_exact_artifacts_not_latest():
    provider = RecordingProvider(data={"which": "first"})
    manager = _manager(provider=provider)

    bundle_1 = await manager.execute_typed(CapabilityRequest("fixture.observe"))
    provider.data = {"which": "second"}
    bundle_2 = await manager.execute_typed(CapabilityRequest("fixture.observe"))

    # Each bundle references only its own execution transaction.
    assert bundle_1.tool_result.capability_call_id == bundle_1.capability_call.capability_call_id
    assert bundle_2.tool_result.capability_call_id == bundle_2.capability_call.capability_call_id
    assert bundle_1.tool_result.capability_call_id != bundle_2.tool_result.capability_call_id
    assert bundle_1.tool_result.structured_output == {"which": "first"}
    assert bundle_2.tool_result.structured_output == {"which": "second"}
    assert {e.evidence_id for e in bundle_1.evidence} != {e.evidence_id for e in bundle_2.evidence}


@pytest.mark.parametrize(
    "decision",
    [
        AuthorizationStatus.DENY,
        AuthorizationStatus.REQUIRE_CONFIRMATION,
        AuthorizationStatus.REQUIRE_ELEVATION,
        AuthorizationStatus.UNAVAILABLE,
    ],
)
@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2: manager typed execution bundle (execute_typed) not implemented",
)
@pytest.mark.asyncio
async def test_manager_typed_bundle_authorization_only_has_no_execution_artifacts(decision: AuthorizationStatus):
    provider = RecordingProvider(data={"should_not": "execute"})
    manager = _manager(decision=decision, provider=provider)

    bundle = await manager.execute_typed(CapabilityRequest("fixture.observe"))

    assert bundle.authorization_decision is not None
    assert bundle.authorization_decision.decision == decision
    assert bundle.capability_call is None
    assert bundle.tool_result is None
    assert bundle.evidence == ()
    assert provider.execute_calls == 0


@pytest.mark.parametrize(
    "provider,providers,expected_status",
    [
        (RecordingProvider(healthy=False), None, "unavailable"),
        (None, {}, "unavailable"),
        (RecordingProvider(raises=RuntimeError("fixture boom")), None, "error"),
    ],
)
@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2: manager typed execution bundle (execute_typed) not implemented",
)
@pytest.mark.asyncio
async def test_manager_typed_bundle_execution_failure_no_fabricated_evidence(
    provider: RecordingProvider | None,
    providers: dict[str, RecordingProvider] | None,
    expected_status: str,
):
    manager = _manager(provider=provider, providers=providers)

    bundle = await manager.execute_typed(CapabilityRequest("fixture.observe"))

    assert bundle.capability_call is not None
    assert bundle.tool_result is not None
    assert bundle.tool_result.status == expected_status
    assert bundle.tool_result.evidence_refs == ()
    assert bundle.evidence == ()

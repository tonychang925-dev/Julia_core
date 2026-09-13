from __future__ import annotations

import inspect
import sys

import pytest

from julia_core.capability.models import (
    CapabilityRequest,
    CapabilityRequestAuthorityError,
    CapabilityStatus,
    ToolResultStatus,
)
from julia_core.capability.policy import PermissionRule
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


MARKET_CAPABILITIES = {
    "market.event.resolve",
    "market.event.read",
    "market.product.read",
}


class RecordingMarketProvider:
    def __init__(self, *, healthy: bool = True) -> None:
        self.healthy = healthy
        self.health_calls = 0
        self.execute_calls = 0
        self.requests = []

    async def health(self) -> tuple[bool, str]:
        self.health_calls += 1
        return self.healthy, "available" if self.healthy else "unavailable"

    async def execute(self, request):
        self.execute_calls += 1
        self.requests.append(request)
        return {"status": "success", "value": "market-result"}


def test_initialize_registers_exactly_three_public_market_definitions():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    definitions = bridge.registry.by_provider("market")

    assert {definition.name for definition in definitions} == MARKET_CAPABILITIES
    assert all(definition.provider == "market" for definition in definitions)
    assert all(
        definition.permission_scope == "market.observe" for definition in definitions
    )
    assert all(
        definition.status is not CapabilityStatus.AVAILABLE
        for definition in definitions
    )
    assert not any(
        definition.permission_scope.endswith((".write", ".mutate", ".delete"))
        for definition in bridge.registry.all_definitions()
    )


def test_canonical_initialize_has_no_legacy_market_reachability():
    legacy_modules = set(sys.modules)
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    source = inspect.getsource(type(bridge).initialize)
    assert "create_ai_theme_provider" not in source
    assert "register_ai_theme_capabilities" not in source
    assert "julia_core.capability.providers.ai_theme" not in source
    assert "ai_theme_app" not in bridge._providers
    assert not {
        name
        for name in set(sys.modules) - legacy_modules
        if name.startswith("julia_core.capability.providers.ai_theme")
    }


@pytest.mark.asyncio
async def test_bound_provider_is_used_by_capability_manager():
    provider = RecordingMarketProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    bridge.register_provider("market", provider)

    execution = await bridge.manager.execute_typed(
        CapabilityRequest(
            "market.product.read", {"product_id": "p1", "revision_id": "r1"}
        )
    )

    assert execution.tool_result is not None
    assert execution.tool_result.status == ToolResultStatus.SUCCESS
    assert provider.execute_calls == 1
    assert provider.requests[0].capability_id == "market.product.read"
    assert bridge.manager.providers["market"] is provider


@pytest.mark.asyncio
async def test_c08_deny_occurs_before_provider_health_and_execute():
    provider = RecordingMarketProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    bridge.register_provider("market", provider)
    bridge.policy.add_rule(
        PermissionRule(
            scope="market.observe",
            allow=False,
            reason="test deny",
        )
    )

    execution = await bridge.manager.execute_typed(
        CapabilityRequest("market.event.read", {"event_id": "e1", "revision_id": "r1"})
    )

    assert execution.authorization_decision.decision == "DENY"
    assert execution.capability_call is None
    assert provider.health_calls == 0
    assert provider.execute_calls == 0


@pytest.mark.asyncio
async def test_missing_market_provider_fails_closed_as_unavailable():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    execution = await bridge.manager.execute_typed(
        CapabilityRequest("market.event.resolve", {"request": "latest event"})
    )

    assert execution.tool_result is not None
    assert execution.tool_result.status == ToolResultStatus.UNAVAILABLE
    assert execution.tool_result.error["code"] == "provider_not_found"


def test_different_market_provider_rebind_is_rejected():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    first = RecordingMarketProvider()
    second = RecordingMarketProvider()
    bridge.register_provider("market", first)

    with pytest.raises(RuntimeError, match="already bound"):
        bridge.register_provider("market", second)


@pytest.mark.asyncio
async def test_request_cannot_override_provider_namespace():
    provider = RecordingMarketProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    bridge.register_provider("market", provider)

    with pytest.raises(CapabilityRequestAuthorityError, match="provider"):
        await bridge.manager.execute_typed(
            CapabilityRequest(
                "market.product.read",
                {"provider": "other-market"},
            )
        )

    assert provider.execute_calls == 0

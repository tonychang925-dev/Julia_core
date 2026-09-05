from __future__ import annotations

import pytest

import julia_core.runtime.capability_bridge as capability_bridge_module
from julia_core.capability.models import CapabilityRequest
from julia_core.runtime.capability_bridge import (
    CapabilityBridgeAlreadyConfiguredError,
    RuntimeCapabilityBridge,
    configure_capability_bridge,
    get_capability_bridge,
)


class MarketProvider:
    def __init__(self):
        self.requests = []

    async def health(self) -> tuple[bool, str]:
        return True, "fixture market provider"

    async def execute(self, request: CapabilityRequest):
        self.requests.append(request)
        return {"status": "success", "payload": {"capability": request.capability_id}}


@pytest.fixture(autouse=True)
def isolated_canonical_bridge(monkeypatch):
    monkeypatch.setattr(capability_bridge_module, "_bridge", None)
    for name in (
        "JULIA_MARKET_SOURCE_ROOT",
        "JULIA_MARKET_SOURCE_SHA",
        "JULIA_MARKET_TREE_DIGEST",
    ):
        monkeypatch.delenv(name, raising=False)
    yield


def composed_bridge() -> tuple[RuntimeCapabilityBridge, MarketProvider]:
    provider = MarketProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("ai_theme_app", provider)
    return bridge, provider


def test_prebuilt_provider_installs_into_canonical_bridge():
    bridge, provider = composed_bridge()
    configured = configure_capability_bridge(bridge)

    assert get_capability_bridge() is configured is bridge
    assert bridge.manager.providers["ai_theme_app"] is provider
    assert bridge.registry.get("market.event.resolve").provider == "ai_theme_app"
    assert bridge.registry.get("market.event.read").provider == "ai_theme_app"


def test_exact_bridge_reconfiguration_is_idempotent():
    bridge, _ = composed_bridge()
    configured = configure_capability_bridge(bridge)
    assert configure_capability_bridge(bridge) is configured
    assert get_capability_bridge() is configured


def test_conflicting_bridge_replacement_fails_closed():
    first, _ = composed_bridge()
    second, _ = composed_bridge()
    configured = configure_capability_bridge(first)

    with pytest.raises(CapabilityBridgeAlreadyConfiguredError):
        configure_capability_bridge(second)

    assert get_capability_bridge() is configured is first


@pytest.mark.asyncio
async def test_configured_provider_receives_capability_request():
    bridge, provider = composed_bridge()
    configure_capability_bridge(bridge)

    result = await bridge.manager.execute(
        CapabilityRequest("market.event.read", {"event_id": 501})
    )

    assert result.status == "success"
    assert [request.capability_id for request in provider.requests] == [
        "market.event.read"
    ]


def test_configure_rejects_non_bridge_object():
    with pytest.raises(TypeError):
        configure_capability_bridge(object())


def test_default_singleton_remains_supported_and_uses_one_bridge():
    first = get_capability_bridge()
    second = get_capability_bridge()

    assert first is second
    assert first._initialized

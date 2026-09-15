"""RD1-P0: Core consumes structured Market requests through a generic seam."""
from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.capability.models import CapabilityRequest
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


class MarketContractFixture:
    def __init__(self, result=None):
        self.calls = []
        self.result = result or {"status": "success", "data": {"source": "market-public-contract"}}

    async def health(self):
        return True, "fixture public contract healthy"

    async def execute(self, request):
        self.calls.append(request)
        return self.result


def bound_bridge(provider):
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("market", provider)
    bridge.initialize()
    return bridge


@pytest.mark.asyncio
@pytest.mark.parametrize("capability", [
    "market.event.resolve", "market.event.read", "market.product.read",
])
async def test_structured_market_request_uses_generic_provider_seam(capability):
    provider = MarketContractFixture()
    bridge = bound_bridge(provider)
    result = await bridge.manager.execute_typed(CapabilityRequest(capability, {"structured": True}))
    assert result.tool_result.status.value == "success"
    assert [call.capability_id for call in provider.calls] == [capability]


def test_raw_user_text_cannot_select_market_inside_core():
    bridge = RuntimeCapabilityBridge()
    assert bridge.requires_tool("今天市场怎么样？") is False
    assert bridge.requires_tool("这个风险大吗？") is False
    assert "MarketBriefIntentResolver" not in Path("julia_core/runtime/workflow_router.py").read_text()


@pytest.mark.asyncio
async def test_unauthorized_request_does_not_invoke_market_provider():
    provider = MarketContractFixture()
    bridge = bound_bridge(provider)
    bridge.policy.remove_scope("market.observe")
    result = await bridge.manager.execute_typed(CapabilityRequest("market.event.read", {}))
    assert result.tool_result is None
    assert result.authorization_decision.allowed is False
    assert provider.calls == []


@pytest.mark.asyncio
async def test_provider_dependency_failure_is_typed_without_fallback():
    class Unavailable(MarketContractFixture):
        async def health(self):
            return False, "public provider unavailable"
    provider = Unavailable()
    bridge = bound_bridge(provider)
    result = await bridge.manager.execute_typed(CapabilityRequest("market.product.read", {}))
    assert result.tool_result.status.value == "unavailable"
    assert provider.calls == []


def test_core_market_path_has_no_checkout_or_sys_path_injection():
    source = Path("julia_core/runtime/capability_bridge.py").read_text()
    adapter = Path("julia_core/capability/providers/ai_theme/adapter.py").read_text()
    assert "/Users/admin/Desktop/ai_theme_app" not in source
    assert "sys.path" not in source
    # Legacy adapter remains outside the canonical bridge path; Core no longer
    # imports or constructs it during RuntimeCapabilityBridge.initialize().
    assert "sys.path" in adapter


@pytest.mark.asyncio
async def test_generic_non_market_file_capability_is_not_regressed():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    result = await bridge.manager.execute_typed(CapabilityRequest("file.read", {"path": str(Path("README.md").resolve())}))
    assert result.tool_result.status.value == "success"

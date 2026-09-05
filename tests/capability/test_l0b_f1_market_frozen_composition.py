from __future__ import annotations

import io
import socket
import subprocess
import sys
import tarfile
import types
from pathlib import Path

import pytest

from julia_core.capability.models import CapabilityRequest, CapabilityStatus, ToolResultStatus
from julia_core.capability.providers.ai_theme.adapter import MCPToolAdapter
from julia_core.capability.providers.ai_theme.frozen_market import (
    MARKET_FROZEN_SHA,
    MARKET_SOURCE_ROOT_CONFIG,
    MARKET_SOURCE_SHA_CONFIG,
    MARKET_TREE_DIGEST_CONFIG,
    FrozenMarketCompositionError,
    MarketDomainAdapterProvider,
    create_frozen_market_provider,
)
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge

MARKET_REPO = Path("/Users/admin/glm-workspace/ai_theme_app")
MARKET_TREE_DIGEST = "a389f92a0026291bbb2820bfce03fb9ff2545553859022dea3a413b8f1d52ad1"


@pytest.fixture(scope="module")
def frozen_market_root(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("frozen-market") / "ai_theme_app"
    archive = subprocess.run(
        ["git", "-C", str(MARKET_REPO), "archive", MARKET_FROZEN_SHA],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as archive_file:
        archive_file.extractall(root, filter="data")
    return root


def pinned_environment(root: Path, **overrides) -> dict[str, str]:
    values = {
        MARKET_SOURCE_ROOT_CONFIG: str(root),
        MARKET_SOURCE_SHA_CONFIG: MARKET_FROZEN_SHA,
        MARKET_TREE_DIGEST_CONFIG: MARKET_TREE_DIGEST,
    }
    values.update(overrides)
    return values


class RecordingAdapter:
    supported_operations = ("market.event.resolve", "market.event.read")

    def __init__(self):
        self.requests = []

    async def execute(self, request):
        self.requests.append(request)
        return {"status": "success", "payload": {"retained": True}}


def test_f01_frozen_core_imports_frozen_market_only(frozen_market_root):
    provider = create_frozen_market_provider(pinned_environment(frozen_market_root))
    assert set(provider.adapter.supported_operations) >= {
        "market.event.resolve",
        "market.event.read",
    }


def test_f02_no_mcp_server_dependency_is_required(monkeypatch, frozen_market_root):
    for name in (MARKET_SOURCE_ROOT_CONFIG, MARKET_SOURCE_SHA_CONFIG, MARKET_TREE_DIGEST_CONFIG):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("MCP_SERVER", raising=False)
    RuntimeCapabilityBridge().initialize()
    assert "mcp_server" not in sys.modules
    assert "mcp_server.server" not in sys.modules


def test_f03_dirty_alternate_market_cannot_win_import(monkeypatch, frozen_market_root):
    dirty_root = frozen_market_root.parent / "dirty-market"
    dirty_root.mkdir()
    package_root = dirty_root / "stock_processing_service"
    (package_root / "application/services/julia_domain_adapter").mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    poisoned = package_root / "application/services/julia_domain_adapter/__init__.py"
    poisoned.write_text("raise RuntimeError('dirty import won')\n", encoding="utf-8")
    poisoned_module = types.ModuleType("stock_processing_service")
    poisoned_module.__file__ = str(dirty_root / "stock_processing_service/__init__.py")
    monkeypatch.setitem(sys.modules, "stock_processing_service", poisoned_module)
    monkeypatch.syspath_prepend(str(dirty_root))

    provider = create_frozen_market_provider(pinned_environment(frozen_market_root))
    assert set(provider.adapter.supported_operations) >= {
        "market.event.resolve",
        "market.event.read",
    }
    assert sys.modules["stock_processing_service"].__file__ == poisoned_module.__file__


def test_f04_f05_market_event_capabilities_register(monkeypatch, frozen_market_root):
    for name in (MARKET_SOURCE_ROOT_CONFIG, MARKET_SOURCE_SHA_CONFIG, MARKET_TREE_DIGEST_CONFIG):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(MARKET_SOURCE_ROOT_CONFIG, str(frozen_market_root))
    monkeypatch.setenv(MARKET_SOURCE_SHA_CONFIG, MARKET_FROZEN_SHA)
    monkeypatch.setenv(MARKET_TREE_DIGEST_CONFIG, MARKET_TREE_DIGEST)
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    definitions = bridge.registry.by_provider("ai_theme_app")
    names = {definition.name: definition for definition in definitions}
    assert set(names) == {
        "market.event.resolve",
        "market.event.read",
        "market.snapshot.read",
        "market.alert.query",
    }
    assert names["market.event.resolve"].status == CapabilityStatus.DEGRADED
    assert names["market.event.read"].status == CapabilityStatus.DEGRADED


@pytest.mark.asyncio
async def test_f06_exact_operation_contract_is_delivered():
    adapter = RecordingAdapter()
    provider = MarketDomainAdapterProvider(adapter)
    request = CapabilityRequest(
        "market.event.read",
        {"event_id": 501},
        capability_request_id="cap_req_l0b",
        turn_id="turn_l0b",
        generation_id="generation_l0b",
        correlation_id="corr_l0b",
    )
    outcome = await provider.execute(request)
    assert outcome.status == ToolResultStatus.SUCCESS
    assert adapter.requests == [{
        "operation": "market.event.read",
        "arguments": {"event_id": 501},
        "correlation_id": "corr_l0b",
        "idempotency_key": "cap_req_l0b",
        "requested_at": "",
        "schema_version": "1.0",
        "trace_metadata": {
            "capability_id": "market.event.read",
            "capability_request_id": "cap_req_l0b",
            "turn_id": "turn_l0b",
            "generation_id": "generation_l0b",
            "market_source_sha": MARKET_FROZEN_SHA,
        },
    }]


@pytest.mark.parametrize(
    "overrides",
    [
        {MARKET_SOURCE_SHA_CONFIG: "dirty"},
        {MARKET_TREE_DIGEST_CONFIG: "dirty"},
        {MARKET_SOURCE_ROOT_CONFIG: "/definitely/not/market"},
    ],
)
def test_f07_invalid_market_pin_fails_closed(monkeypatch, frozen_market_root, overrides):
    for name in (MARKET_SOURCE_ROOT_CONFIG, MARKET_SOURCE_SHA_CONFIG, MARKET_TREE_DIGEST_CONFIG):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(FrozenMarketCompositionError):
        create_frozen_market_provider(pinned_environment(frozen_market_root, **overrides))


@pytest.mark.asyncio
async def test_f08_f09_composition_makes_no_db_or_provider_call(monkeypatch):
    monkeypatch.setattr("socket.socket", None)
    adapter = RecordingAdapter()
    provider = MarketDomainAdapterProvider(adapter)
    health = await provider.health()
    assert health[0] is True
    assert adapter.requests == []


def test_f10_explicit_transport_support_has_no_implicit_fallback():
    async def transport(tool_name, arguments):
        return {"tool": tool_name, "arguments": arguments}

    adapter = MCPToolAdapter(transport)
    assert adapter._transport is transport

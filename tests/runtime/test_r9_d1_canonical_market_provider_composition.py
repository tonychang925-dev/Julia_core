from __future__ import annotations

from datetime import date
import io
import subprocess
import tarfile
from pathlib import Path
from typing import Any

import pytest

from julia_core.capability.models import CapabilityRequest, CapabilityStatus, ToolResultStatus
from julia_core.capability.providers.ai_theme.frozen_market import (
    MARKET_FROZEN_SHA,
    MARKET_SOURCE_ROOT_CONFIG,
    MARKET_SOURCE_SHA_CONFIG,
    MARKET_TREE_DIGEST_CONFIG,
)
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


MARKET_REPO = Path("/Users/admin/glm-workspace/ai_theme_app")
MARKET_TREE_DIGEST = "b07d454ac2c067717c7bdf70fc012c811d9d1636b427dd917134227e0df604dd"


@pytest.fixture(scope="module")
def frozen_market_root(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("r9-d1-market") / "ai_theme_app"
    archive = subprocess.run(
        ["git", "-C", str(MARKET_REPO), "archive", MARKET_FROZEN_SHA],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as archive_file:
        archive_file.extractall(root, filter="data")
    return root


def pinned_environment(root: Path) -> dict[str, str]:
    return {
        MARKET_SOURCE_ROOT_CONFIG: str(root),
        MARKET_SOURCE_SHA_CONFIG: MARKET_FROZEN_SHA,
        MARKET_TREE_DIGEST_CONFIG: MARKET_TREE_DIGEST,
    }


class CanonicalFakeGateway:
    def __init__(self) -> None:
        self._initialized = True
        self.resolve_calls = 0

    async def resolve_market_event_candidates(
        self,
        *,
        query: str,
        normalized_theme: str | None = None,
        time_window: dict[str, Any] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        self.resolve_calls += 1
        assert isinstance(time_window["date"], date)
        return [{
            "market_event_id": 215257,
            "title": "Token出海 canonical event",
            "summary": "",
            "occurred_at": "2026-07-19T18:46:35.697877+08:00",
            "matched_subjects": [],
        }]


@pytest.mark.asyncio
async def test_canonical_provider_preserves_exact_gateway_identity(frozen_market_root):
    bridge = RuntimeCapabilityBridge()
    gateway = CanonicalFakeGateway()
    provider, observed_gateway = await bridge.register_canonical_market_provider(
        environment=pinned_environment(frozen_market_root),
        database_gateway=gateway,
    )
    bridge.initialize()

    resolve_operation = provider.adapter._operations["market.event.resolve"]
    read_operation = provider.adapter._operations["market.event.read"]
    assert observed_gateway is gateway
    assert resolve_operation._database_gateway is gateway
    assert read_operation._database_gateway is gateway
    assert bridge._providers["ai_theme_app"] is provider
    assert bridge.manager.providers["ai_theme_app"] is provider
    assert list(bridge._providers).count("ai_theme_app") == 1
    assert await provider.health() == (True, f"frozen Market adapter sha:{MARKET_FROZEN_SHA}")
    assert bridge.registry.get("market.event.resolve").status is CapabilityStatus.AVAILABLE


@pytest.mark.asyncio
async def test_canonical_capability_path_normalizes_date_and_preserves_market_event_id(
    frozen_market_root,
):
    bridge = RuntimeCapabilityBridge()
    gateway = CanonicalFakeGateway()
    await bridge.register_canonical_market_provider(
        environment=pinned_environment(frozen_market_root),
        database_gateway=gateway,
    )
    bridge.initialize()

    execution = await bridge.manager.execute_typed(CapabilityRequest(
        "market.event.resolve",
        {
            "query": "Token出海",
            "normalized_theme": "Token出海",
            "time_window": {"date": "2026-07-19"},
        },
        capability_request_id="r9_d1_technical_probe",
    ))

    assert execution.tool_result is not None
    assert execution.tool_result.status is ToolResultStatus.SUCCESS
    payload = execution.tool_result.structured_output["payload"]
    diagnostics = execution.tool_result.structured_output["diagnostics"]
    assert payload["state"] == "RESOLVED"
    assert diagnostics["candidate_count"] == 1
    assert payload["selected_event_id"] == 215257
    assert payload["candidates"][0]["market_event_id"] == 215257
    assert gateway.resolve_calls == 1


@pytest.mark.asyncio
async def test_half_composed_fallback_is_visibly_degraded(frozen_market_root, monkeypatch):
    for name in (
        MARKET_SOURCE_ROOT_CONFIG,
        MARKET_SOURCE_SHA_CONFIG,
        MARKET_TREE_DIGEST_CONFIG,
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(MARKET_SOURCE_ROOT_CONFIG, str(frozen_market_root))
    monkeypatch.setenv(MARKET_SOURCE_SHA_CONFIG, MARKET_FROZEN_SHA)
    monkeypatch.setenv(MARKET_TREE_DIGEST_CONFIG, MARKET_TREE_DIGEST)

    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    provider = bridge._providers["ai_theme_app"]
    healthy, detail = await provider.health()

    assert healthy is False
    assert detail == "frozen Market database gateway is not bound"
    assert bridge.registry.get("market.event.resolve").status is CapabilityStatus.DEGRADED

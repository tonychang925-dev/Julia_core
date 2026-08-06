"""R0.4 Real E2E Test — full Runtime execution path verification.

Tests the ACTUAL execution chain through RuntimeCapabilityBridge,
NOT isolated module mocks. Verifies the trace:

  user.input → intent.resolved → capability.requested
  → market.snapshot.read → provider.invoked
  → context.block.created → artifact.created

This is the gate for Phase 0.5 completion.
Before R0, all 62 tests were isolated module tests. These are real runtime tests.

Run:
  python -m pytest tests/runtime/test_runtime_e2e.py -v
"""

import asyncio
import pytest

from julia_core.runtime.capability_bridge import (
    RuntimeCapabilityBridge,
    get_capability_bridge,
)


# ── Mock transport for ai_theme_app (avoids requiring real ai_theme_app) ────

def _e2e_snapshot_data():
    return {
        "market_sentiment": "偏弱",
        "active_themes": ["AI Agent", "半导体", "机器人"],
        "top_signals": [
            {
                "id": "dec_e2e_001",
                "timestamp": "2026-08-06T08:30:00+08:00",
                "source": "market",
                "type": "theme_match",
                "level": "decision",
                "impact": "positive",
                "confidence": 0.82,
                "prediction_id": "pred_e2e_001",
                "theme_context": {
                    "theme_id": "9019807",
                    "lifecycle": "DIFFUSION",
                    "change": "heat increasing",
                    "days_active": 5,
                },
                "causal_chain": [
                    {
                        "cause": "AI Agent技术突破",
                        "effect": "产业预期升温",
                        "market_response": "相关概念股上涨",
                        "confidence": 0.82,
                    },
                ],
                "evidence": [
                    {"type": "news", "text": "AI Agent政策催化", "source": "cls_api", "authority": 0.9},
                ],
            },
        ],
        "risk_alerts": ["外围市场波动", "成交未能放量", "AI板块短期过热风险"],
        "date": "2026-08-06",
    }


async def _e2e_transport(tool_name: str, args: dict) -> dict:
    if tool_name == "review_market_snapshot":
        return _e2e_snapshot_data()
    return {}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def bridge():
    """Create a bridge with E2E mock transport for ai_theme_app."""
    b = RuntimeCapabilityBridge()

    # Override ai_theme_app provider with mock transport
    from julia_core.capability.providers.ai_theme import (
        register_ai_theme_capabilities,
        AiThemeProvider,
    )
    from julia_core.capability.providers.ai_theme.adapter import MCPToolAdapter

    register_ai_theme_capabilities(b.registry)
    adapter = MCPToolAdapter(transport=_e2e_transport)
    provider = AiThemeProvider(adapter)
    b._providers["ai_theme_app"] = provider

    b._initialized = False
    b.initialize()
    return b


# ── E2E-1: Bridge initialization ─────────────────────────────────────────────

def test_bridge_initializes_all_providers(bridge):
    """Bridge initializes local + ai_theme_app providers."""
    assert bridge._initialized
    assert bridge.manager is not None

    # Local capabilities registered
    local_defs = bridge.registry.by_provider("local")
    assert len(local_defs) == 3
    local_names = {d.name for d in local_defs}
    assert local_names == {"file.read", "file.search", "file.list"}

    # ai_theme_app capabilities registered
    ai_defs = bridge.registry.by_provider("ai_theme_app")
    assert len(ai_defs) == 3
    ai_names = {d.name for d in ai_defs}
    assert ai_names == {"market.snapshot.read", "market.alert.query", "market.decision.explain"}


# ── E2E-2: Capability Manager executes market.snapshot.read ──────────────────

@pytest.mark.asyncio
async def test_manager_executes_market_snapshot(bridge):
    """CapabilityManager routes market.snapshot.read → ai_theme_app provider."""
    from julia_core.capability.models import CapabilityRequest

    result = await bridge.manager.execute(
        CapabilityRequest("market.snapshot.read")
    )

    assert result.status == "success"
    assert result.provider == "ai_theme_app"

    # Data wrapper: AiThemeProvider wraps tool output
    data = result.data
    assert data["schema_version"] == "1.1"
    assert data["provider"] == "ai_theme_app"
    assert "data" in data

    # Verify DecisionEnvelope v1.1 contract
    inner = data["data"]
    assert inner["market_sentiment"] == "偏弱"
    assert len(inner["active_themes"]) == 3
    assert len(inner["risk_alerts"]) >= 1


# ── E2E-3: Evidence trace through Manager ────────────────────────────────────

@pytest.mark.asyncio
async def test_manager_produces_evidence(bridge):
    """Full invocation produces evidence in Manager's EvidenceLedger."""
    from julia_core.capability.models import CapabilityRequest

    result = await bridge.manager.execute(
        CapabilityRequest("market.snapshot.read")
    )

    assert result.status == "success"
    assert bridge.manager.evidence.count >= 1

    entry = bridge.manager.evidence.last()
    assert entry is not None
    assert entry.capability_name == "market.snapshot.read"
    assert entry.provider == "ai_theme_app"
    assert entry.status == "success"


# ── E2E-4: Permission enforcement through Manager ────────────────────────────

@pytest.mark.asyncio
async def test_manager_enforces_permission(bridge):
    """Denied capability blocked before provider call."""
    from julia_core.capability.models import CapabilityDefinition, CapabilityRequest, CapabilityLayer, CapabilityStatus

    # Register a denied capability
    bridge.registry.register_definition(CapabilityDefinition(
        name="trade.execute",
        description="Execute a trade",
        layer=CapabilityLayer.INTELLIGENCE,
        provider="ai_theme_app",
        permission_scope="market.trade.execute",
        status=CapabilityStatus.AVAILABLE,
    ))

    result = await bridge.manager.execute(CapabilityRequest("trade.execute"))
    assert result.status == "denied"
    assert "never trades" in result.error_message


# ── E2E-5: Market Brief Pipeline through Bridge ──────────────────────────────

@pytest.mark.asyncio
async def test_market_brief_pipeline_through_bridge(bridge):
    """MarketBriefPipeline executes through bridge.resolve_market_intent()."""
    result = await bridge.resolve_market_intent("今天市场怎么样？")

    assert result is not None
    assert result.capability_status == "success"
    assert result.provider == "ai_theme_app"

    # ContextBlocks produced
    assert len(result.context_blocks) >= 3
    block_types = {b.block_type for b in result.context_blocks}
    assert "market_overview" in block_types
    assert "market_themes" in block_types
    assert "market_risks" in block_types

    # Evidence
    assert "capability" in result.evidence
    assert result.evidence["capability"] == "market.snapshot.read"

    # prediction_ids extracted for M7 feedback
    assert len(result.prediction_ids) >= 1

    # Artifact creation
    from julia_core.experience.market_brief_artifact import MarketBriefArtifact
    artifact = MarketBriefArtifact.from_brief_result(result, "Market is stable with AI Agent theme active.")
    assert artifact.mutates_identity is False
    assert artifact.mutates_memory is False
    assert artifact.brief_id != ""


# ── E2E-6: Non-market input bypasses capability ─────────────────────────────

@pytest.mark.asyncio
async def test_non_market_skips_capability(bridge):
    """Non-market input → intent UNKNOWN → no capability invoked."""
    result = await bridge.resolve_market_intent("你好，今天心情怎么样？")
    assert result is not None
    assert result.capability_status == "not_requested"
    assert result.prediction_ids == ()


# ── E2E-7: Unique per-invocation request IDs ─────────────────────────────────

@pytest.mark.asyncio
async def test_unique_request_ids(bridge):
    """Each invocation has unique request_id for traceability."""
    from julia_core.capability.models import CapabilityRequest

    r1 = await bridge.manager.execute(CapabilityRequest("market.snapshot.read"))
    r2 = await bridge.manager.execute(CapabilityRequest("market.snapshot.read"))

    assert r1.status == "success"
    assert r2.status == "success"

    # Evidence entries are unique
    entries = bridge.manager.evidence.entries
    request_ids = [e.request_id for e in entries]
    assert len(set(request_ids)) == len(request_ids)  # all unique


# ── E2E-8: ContextBlock provenance ──────────────────────────────────────────

def test_context_blocks_from_bridge_have_provenance(bridge):
    """All ContextBlocks carry source + authority + block_kind."""
    import asyncio

    async def _run():
        from julia_core.context_os.providers.market_context import MarketBriefContextAdapter
        from julia_core.capability.models import CapabilityRequest

        result = await bridge.manager.execute(CapabilityRequest("market.snapshot.read"))
        adapter = MarketBriefContextAdapter()
        blocks = adapter.build_context_blocks(result.data)

        for block in blocks:
            assert block.source == "ai_theme_app", f"Block {block.block_type} missing source"
            assert block.authority != "", f"Block {block.block_type} missing authority"

        return blocks

    blocks = asyncio.run(_run())
    assert len(blocks) >= 3


# ── E2E-9: Tool manifest includes all capabilities ──────────────────────────

def test_tool_manifest_includes_both_local_and_market(bridge):
    """Backward-compatible tool manifest lists local + market tools."""
    manifest = bridge.tool_manifest()

    # Local tools
    assert "file.read" in manifest
    assert "file.search" in manifest
    assert "file.list" in manifest

    # Market tools
    assert "market.snapshot.read" in manifest
    assert "market.alert.query" in manifest
    assert "market.decision.explain" in manifest


# ── E2E-10: Health check — all providers available ──────────────────────────

@pytest.mark.asyncio
async def test_all_providers_healthy(bridge):
    """All registered providers return healthy status."""
    for name, provider in bridge._flatten_providers().items():
        healthy, detail = await provider.health()
        assert healthy, f"Provider {name} unhealthy: {detail}"


# ── E2E-11: Intent detection integrated with bridge ──────────────────────────

@pytest.mark.asyncio
async def test_intent_detection_integrated(bridge):
    """Intent detection + capability execution integrated through bridge."""
    # Market intent → pipeline
    result = await bridge.resolve_market_intent("最近什么方向强")
    assert result.capability_status == "success"
    assert result.provider == "ai_theme_app"

    # Non-market → skipped
    result2 = await bridge.resolve_market_intent("今天吃什么")
    assert result2.capability_status == "not_requested"

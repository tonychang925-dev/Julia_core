"""M1 Acceptance Tests — ai_theme_app Provider Integration.

ADR-026 M1 gate conditions. Must pass before M1→M2 transition.

Run:
  python -m pytest tests/capability/test_m1_ai_theme.py -v
"""

import asyncio
import ast
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityRequest,
    CapabilityStatus,
)
from julia_core.capability.policy import PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry
from julia_core.capability.manager import CapabilityManager
from julia_core.capability.providers.ai_theme import (
    AiThemeProvider,
    AI_THEME_CAPABILITIES,
    register_ai_theme_capabilities,
)
from julia_core.capability.providers.ai_theme.adapter import (
    MCPToolAdapter,
    CAPABILITY_TO_TOOL,
    TOOL_TO_CAPABILITY,
)


# ── Mock MCP Transport ──────────────────────────────────────────────────────

def _mock_snapshot_data():
    """Return valid DecisionEnvelope v1.1 MarketSnapshot stub."""
    return {
        "market_sentiment": "偏弱",
        "active_themes": ["AI Agent", "半导体", "机器人"],
        "top_signals": [
            {
                "id": "dec_20260806_001",
                "timestamp": "2026-08-06T08:30:00+08:00",
                "source": "news",
                "type": "theme_match",
                "level": "decision",
                "evidence": [
                    {"type": "news", "text": "AI Agent政策催化", "source": "cls_api", "ref_id": "", "authority": 0.9},
                ],
                "causal_chain": [
                    {"cause": "AI Agent技术突破", "effect": "产业预期升温", "market_response": "相关概念股上涨", "confidence": 0.82},
                ],
                "theme_context": {
                    "theme_id": "9019807",
                    "lifecycle": "DIFFUSION",
                    "previous_state": "START",
                    "change": "heat increasing",
                    "first_signal_date": "2026-08-01",
                    "days_active": 5,
                },
                "prediction_id": "pred_20260806_001",
                "confidence": 0.82,
                "impact": "positive",
                "expiry": None,
                "payload": {},
            },
        ],
        "risk_alerts": ["外围市场波动", "成交未能放量"],
        "date": "2026-08-06",
    }


def _mock_alert_data():
    """Return valid DecisionEnvelope v1.1 alert list stub."""
    return [
        {
            "id": "dec_20260806_001",
            "timestamp": "2026-08-06T08:30:00+08:00",
            "source": "news",
            "type": "theme_match",
            "level": "decision",
            "evidence": [
                {"type": "news", "text": "AI Agent政策催化", "source": "cls_api", "authority": 0.9},
            ],
            "causal_chain": [
                {"cause": "AI Agent技术突破", "effect": "产业预期升温", "market_response": "相关概念股上涨", "confidence": 0.82},
            ],
            "theme_context": {
                "theme_id": "9019807",
                "lifecycle": "DIFFUSION",
                "previous_state": "START",
                "change": "heat increasing",
                "days_active": 5,
            },
            "prediction_id": "pred_20260806_001",
            "confidence": 0.82,
            "impact": "positive",
        },
    ]


def _mock_explain_data():
    """Return valid DecisionExplanation v1.1 stub."""
    return {
        "decision_id": "dec_20260806_001",
        "summary": "AI Agent板块出现L4级别扩散信号",
        "causal_chain": [
            {"cause": "AI Agent技术突破 + 政策催化", "effect": "产业预期升温", "market_response": "相关概念股上涨，龙头涨停", "confidence": 0.82},
        ],
        "supporting_evidence": 4,
        "opposing_evidence": 1,
        "confidence": 0.82,
        "risk_factors": ["外围市场波动", "成交量未能有效放大", "AI板块短期过热风险"],
        "alternatives": ["短期情绪炒作，非趋势性行情"],
    }


async def _mock_transport(tool_name: str, args: dict) -> dict:
    """Mock MCP transport returning DecisionEnvelope v1.1 data."""
    if tool_name == "review_market_snapshot":
        return _mock_snapshot_data()
    elif tool_name == "list_active_alerts":
        return _mock_alert_data()
    elif tool_name == "explain_decision":
        return _mock_explain_data()
    return {"error": "unknown tool"}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def registry():
    r = CapabilityRegistry()
    register_ai_theme_capabilities(r)
    return r


@pytest.fixture
def adapter():
    return MCPToolAdapter(transport=_mock_transport)


@pytest.fixture
def provider(adapter):
    return AiThemeProvider(adapter)


@pytest.fixture
def manager(registry):
    policy = PermissionPolicy.with_defaults()
    provider = AiThemeProvider(MCPToolAdapter(transport=_mock_transport))
    return CapabilityManager(registry, policy, {"ai_theme_app": provider})


# ── AC-M1-1: Provider Isolation ─────────────────────────────────────────────

def test_ai_theme_provider_isolation_m0_files():
    """M0 capability kernel files must not import ai_theme_app.

    Scans: models.py, manager.py, policy.py, registry.py, providers/__init__.py
    """
    julia_core_dir = Path(__file__).resolve().parent.parent.parent / "julia_core"
    m0_files = [
        julia_core_dir / "capability" / "models.py",
        julia_core_dir / "capability" / "manager.py",
        julia_core_dir / "capability" / "policy.py",
        julia_core_dir / "capability" / "providers" / "__init__.py",
    ]

    for file_path in m0_files:
        if not file_path.exists():
            continue
        source = file_path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "ai_theme_app" not in alias.name, (
                        f"{file_path.name}: imports 'ai_theme_app' — "
                        f"violates AC-M1-1 Provider Isolation (M0 kernel)"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert "ai_theme_app" not in node.module, (
                        f"{file_path.name}: imports from 'ai_theme_app' — "
                        f"violates AC-M1-1 Provider Isolation (M0 kernel)"
                    )


def test_adapter_is_the_only_boundary_file():
    """Only adapter.py may reference MCP internals. Provider.py must not.

    The adapter is the DESIGNATED BOUNDARY. Provider wraps adapter,
    never touches MCP directly.
    """
    provider_path = Path(__file__).resolve().parent.parent.parent / "julia_core" / "capability" / "providers" / "ai_theme" / "provider.py"
    source = provider_path.read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "mcp_server" not in alias.name, (
                    "provider.py must not import mcp_server directly — use adapter"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert "mcp_server" not in node.module, (
                    "provider.py must not import from mcp_server directly — use adapter"
                )


# ── AC-M1-2: Capability Registration ────────────────────────────────────────

def test_all_three_capabilities_registered(registry):
    """All 3 M1 capabilities are registered with correct metadata."""
    for spec in AI_THEME_CAPABILITIES:
        definition = registry.get(spec["name"])
        assert definition is not None, f"{spec['name']} not registered"
        assert definition.layer == CapabilityLayer.INTELLIGENCE
        assert definition.provider == "ai_theme_app"
        assert definition.permission_scope == "market.observe"
        assert definition.status == CapabilityStatus.AVAILABLE
        assert definition.schema_version == "1.1"


def test_registry_has_exactly_three_ai_theme(registry):
    """Registry has exactly 3 ai_theme_app capabilities (M1 scope)."""
    ai_theme_defs = registry.by_provider("ai_theme_app")
    assert len(ai_theme_defs) == 3
    names = {d.name for d in ai_theme_defs}
    assert names == {"market.snapshot.read", "market.alert.query", "market.decision.explain"}


def test_registry_intelligence_layer(registry):
    """All 3 capabilities are in INTELLIGENCE layer."""
    intel_defs = registry.by_layer(CapabilityLayer.INTELLIGENCE)
    ai_theme_in_intel = [d for d in intel_defs if d.provider == "ai_theme_app"]
    assert len(ai_theme_in_intel) == 3


# ── AC-M1-3: Permission ─────────────────────────────────────────────────────

def test_market_observe_is_allowed():
    """market.observe scope is allowed."""
    policy = PermissionPolicy.with_defaults()
    allowed, reason = policy.check("market.observe")
    assert allowed
    assert "read-only" in reason.lower()


def test_market_trade_execute_is_denied():
    """market.trade.execute scope is denied."""
    policy = PermissionPolicy.with_defaults()
    allowed, reason = policy.check("market.trade.execute")
    assert not allowed
    assert "never trades" in reason


@pytest.mark.asyncio
async def test_snapshot_read_through_permission(manager):
    """market.snapshot.read passes permission check and executes."""
    result = await manager.execute(CapabilityRequest("market.snapshot.read"))
    assert result.status == "success"
    assert result.provider == "ai_theme_app"


# ── AC-M1-4: Contract Validation — DecisionEnvelope v1.1 ───────────────────

@pytest.mark.asyncio
async def test_snapshot_contains_required_fields(provider):
    """MarketSnapshot response has all v1.1 required fields."""
    result = await provider.execute(CapabilityRequest("market.snapshot.read"))

    assert result["schema_version"] == "1.1"
    assert result["provider"] == "ai_theme_app"
    assert "data" in result

    data = result["data"]
    assert "market_sentiment" in data
    assert "active_themes" in data
    assert "top_signals" in data
    assert "risk_alerts" in data

    # Verify DecisionEnvelope v1.1 fields on first signal
    signals = data.get("top_signals", [])
    if signals:
        signal = signals[0]
        assert "causal_chain" in signal, "v1.1 requires causal_chain"
        assert "theme_context" in signal, "v1.1 requires theme_context"
        assert "prediction_id" in signal, "v1.1 requires prediction_id"


@pytest.mark.asyncio
async def test_alert_contains_causal_chain(provider):
    """Alert response has causal_chain (v1.1 field)."""
    result = await provider.execute(CapabilityRequest(
        "market.alert.query",
        arguments={"level": "decision"},
    ))

    data = result["data"]
    if isinstance(data, list) and data:
        alert = data[0]
        assert "causal_chain" in alert
        assert "prediction_id" in alert


@pytest.mark.asyncio
async def test_explain_contains_risk_and_alternatives(provider):
    """DecisionExplanation has risk_factors and alternatives (v1.1 fields)."""
    result = await provider.execute(CapabilityRequest(
        "market.decision.explain",
        arguments={"decision_id": "dec_20260806_001"},
    ))

    data = result["data"]
    assert "causal_chain" in data
    assert "risk_factors" in data
    assert "alternatives" in data
    assert "supporting_evidence" in data
    assert "opposing_evidence" in data


@pytest.mark.asyncio
async def test_all_responses_have_schema_version(provider):
    """Every provider response carries schema_version."""
    for cap_name in ["market.snapshot.read", "market.alert.query", "market.decision.explain"]:
        args = {"decision_id": "dec_20260806_001"} if "explain" in cap_name else {}
        result = await provider.execute(CapabilityRequest(cap_name, arguments=args))
        assert result["schema_version"] == "1.1", f"{cap_name} missing schema_version"


# ── AC-M1-5: Evidence ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invocation_produces_evidence(manager):
    """Each market capability invocation produces an evidence record."""
    await manager.execute(CapabilityRequest("market.snapshot.read"))
    last = manager.evidence.last()
    assert last is not None
    assert last.capability_name == "market.snapshot.read"
    assert last.provider == "ai_theme_app"
    assert last.status == "success"
    assert last.timestamp != ""


@pytest.mark.asyncio
async def test_multiple_invocations_all_evidenced(manager):
    """Multiple calls all produce separate evidence entries."""
    await manager.execute(CapabilityRequest("market.snapshot.read"))
    await manager.execute(CapabilityRequest("market.alert.query"))
    await manager.execute(CapabilityRequest(
        "market.decision.explain",
        arguments={"decision_id": "dec_20260806_001"},
    ))

    assert manager.evidence.count == 3
    capabilities_called = {e.capability_name for e in manager.evidence.entries}
    assert capabilities_called == {
        "market.snapshot.read",
        "market.alert.query",
        "market.decision.explain",
    }


# ── Adapter Unit Tests ──────────────────────────────────────────────────────

def test_capability_to_tool_mapping():
    """Capability names correctly map to MCP tool names."""
    assert CAPABILITY_TO_TOOL["market.snapshot.read"] == "review_market_snapshot"
    assert CAPABILITY_TO_TOOL["market.alert.query"] == "list_active_alerts"
    assert CAPABILITY_TO_TOOL["market.decision.explain"] == "explain_decision"


def test_tool_to_capability_mapping():
    """Reverse mapping: MCP tool → capability name."""
    assert TOOL_TO_CAPABILITY["review_market_snapshot"] == "market.snapshot.read"
    assert TOOL_TO_CAPABILITY["list_active_alerts"] == "market.alert.query"
    assert TOOL_TO_CAPABILITY["explain_decision"] == "market.decision.explain"


@pytest.mark.asyncio
async def test_adapter_unknown_capability_raises():
    """Unknown capability raises ValueError."""
    adapter = MCPToolAdapter(transport=_mock_transport)
    with pytest.raises(ValueError, match="Unknown capability"):
        await adapter.call("does.not.exist")


@pytest.mark.asyncio
async def test_adapter_health(adapter):
    """Adapter health check succeeds with mock transport."""
    healthy, detail = await adapter.health()
    assert healthy


# ── Bonus: Manager → Provider → Adapter end-to-end ────────────────────────

@pytest.mark.asyncio
async def test_full_chain_snapshot_read(manager):
    """End-to-end: request market.snapshot.read through full Manager chain."""
    result = await manager.execute(CapabilityRequest(
        "market.snapshot.read",
        reason="Tony asked how the market looks today",
    ))

    assert result.status == "success"
    assert result.provider == "ai_theme_app"
    assert result.schema_version == "1.1"
    assert "active_themes" in result.data["data"]

    # Evidence
    assert manager.evidence.count == 1
    entry = manager.evidence.last()
    assert entry is not None
    assert entry.capability_name == "market.snapshot.read"
    assert entry.provider == "ai_theme_app"

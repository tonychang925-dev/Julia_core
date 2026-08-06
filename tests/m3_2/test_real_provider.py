"""M3.2.1 Real Provider Integration Test — mock MCP → intelligence observation.

Validates: AiThemeProvider → ContractMapper → intelligence observation format
through the REAL provider path (not synthetic data).

Run:
  python -m pytest tests/m3_2/test_real_provider.py -v
"""

import pytest

from julia_core.capability.models import CapabilityRequest
from julia_core.capability.providers.ai_theme import AiThemeProvider
from julia_core.capability.providers.ai_theme.adapter import MCPToolAdapter
from julia_core.awareness.ingestion import IntelligenceAdapter


# ── Mock MCP Transport (simulates real ai_theme_app responses) ──────────────

def _real_snapshot():
    return {
        "market_sentiment": "偏强",
        "active_themes": ["AI Agent", "半导体", "机器人"],
        "top_signals": [
            {
                "id": "dec_real_001",
                "level": "decision",
                "source": "market",
                "type": "theme_match",
                "impact": "AI Agent主题扩散",
                "confidence": 0.85,
                "prediction_id": "pred_real_001",
                "theme_context": {
                    "theme_id": "9019807",
                    "lifecycle": "DIFFUSION",
                    "change": "heat increasing",
                    "days_active": 5,
                },
                "causal_chain": [
                    {"cause": "政策催化", "effect": "产业升温", "market_response": "板块上涨", "confidence": 0.82},
                ],
                "evidence": [{"type": "news", "text": "AI Agent政策催化", "source": "cls", "authority": 0.9}],
            },
            {
                "id": "dec_real_002",
                "level": "alert",
                "source": "market",
                "type": "support_alert",
                "impact": "半导体资金流入增强",
                "confidence": 0.78,
                "prediction_id": "pred_real_002",
            },
        ],
        "risk_alerts": ["外围波动", "成交量分化"],
        "date": "2026-08-06",
    }


def _real_alerts():
    return [
        {
            "id": "dec_alert_001",
            "level": "decision",
            "source": "news",
            "type": "theme_match",
            "impact": "AI Agent扩散确认",
            "confidence": 0.88,
            "prediction_id": "pred_alert_001",
            "theme_context": {"theme_id": "AI Agent"},
        },
    ]


async def _real_transport(tool_name: str, args: dict) -> dict:
    if tool_name == "review_market_snapshot":
        return _real_snapshot()
    elif tool_name == "list_active_alerts":
        return _real_alerts()
    return {}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def real_adapter():
    return MCPToolAdapter(transport=_real_transport)


@pytest.fixture
def real_provider(real_adapter):
    return AiThemeProvider(real_adapter)


# ── M3.2.1 Tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_provider_returns_intelligence_observations(real_provider):
    """AiThemeProvider handles market.intelligence.observe → composed observations."""
    result = await real_provider.execute(
        CapabilityRequest("market.intelligence.observe")
    )

    assert result["capability"] == "market.intelligence.observe"
    assert result["provider"] == "ai_theme_app"
    assert result["schema_version"] == "1.0"

    data = result["data"]
    assert data["source"] == "ai_theme_app_analyst_workbench"
    assert "observations" in data
    assert len(data["observations"]) >= 1


@pytest.mark.asyncio
async def test_observations_pass_adapter_contract(real_provider):
    """Real provider output → IntelligenceAdapter → valid ObservationEvents."""
    result = await real_provider.execute(
        CapabilityRequest("market.intelligence.observe")
    )

    adapter = IntelligenceAdapter()
    events = adapter.convert(result["data"])

    assert len(events) >= 1
    for event in events:
        assert event.source != ""
        assert event.domain == "market"
        assert event.subject != ""
        assert event.confidence >= 0.0
        # No forbidden fields
        payload_str = str(event.payload)
        assert "theme_id" not in payload_str


@pytest.mark.asyncio
async def test_observations_have_varied_decision_levels(real_provider):
    """Real observations include multiple decision levels (L1-L3)."""
    result = await real_provider.execute(
        CapabilityRequest("market.intelligence.observe")
    )

    levels = [obs["signal_level"] for obs in result["data"]["observations"]]
    assert "L1" in levels or "L3" in levels, f"Expected varied levels, got: {levels}"
    assert len(levels) >= 3, f"Expected multiple observations, got {len(levels)}"


@pytest.mark.asyncio
async def test_provider_preserves_existing_capabilities(real_provider):
    """Existing capabilities (snapshot.read) still work unchanged."""
    result = await real_provider.execute(
        CapabilityRequest("market.snapshot.read")
    )

    assert result["capability"] == "market.snapshot.read"
    assert result["provider"] == "ai_theme_app"
    data = result["data"]
    assert "market_sentiment" in data or data.get("market_sentiment")


@pytest.mark.asyncio
async def test_provider_health(real_provider):
    """Provider health check works."""
    healthy, detail = await real_provider.health()
    assert healthy

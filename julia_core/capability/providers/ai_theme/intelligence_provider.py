"""M3.1.1 Market Intelligence Provider — curated observations from ai_theme_app.

ADR-028 Addendum: Julia receives pre-analyzed intelligence signals,
not raw market data. ai_theme_app's Analyst Workbench has already
performed domain-specific cognition.

This capability provides: market.intelligence.observe
Returns: list of curated intelligence observations with decision levels.
"""

from __future__ import annotations

from julia_core.capability.models import CapabilityRequest

# ── Decision Level → Julia Behavior ─────────────────────────────────────────

DECISION_LEVEL_BEHAVIOR = {
    "L0": "ignore",       # Noise — not worth Julia's attention
    "L1": "record",       # Observation — log to EventStore only
    "L2": "watch",        # Short-term observation — track pattern
    "L3": "awareness",    # Generate Awareness — significant signal
    "L4": "notify",       # Generate Awareness + notify Tony
}

DECISION_LEVEL_ADMISSION_WEIGHT = {
    "L0": 0.0,
    "L1": 0.2,
    "L2": 0.4,
    "L3": 0.7,
    "L4": 1.0,
}


class MarketIntelligenceProvider:
    """CapabilityProvider: market.intelligence.observe.

    Receives curated intelligence from ai_theme_app Analyst Workbench.
    Does NOT process raw market data. Does NOT perform domain analysis.

    This is a domain intelligence adapter — it wraps ai_theme_app's
    output into Julia's observation framework.
    """

    def __init__(self, adapter=None):
        """adapter: MCPToolAdapter or mock. If None, uses synthetic data."""
        self._adapter = adapter

    async def execute(self, request: CapabilityRequest) -> dict:
        """Return curated market intelligence observations.

        In production (M3.2+): calls ai_theme_app MCP via adapter.
        In M3.1 skeleton: returns synthetic intelligence signals for testing.
        """
        if self._adapter:
            raw = await self._adapter.call(
                "market.intelligence.observe",
                request.arguments,
            )
            return self._normalize(raw)

        # M3.1 skeleton: synthetic intelligence signals
        return self._synthetic_observations(request)

    def _synthetic_observations(self, request: CapabilityRequest) -> dict:
        """Generate synthetic intelligence signals for M3.1 testing.

        These mimic ai_theme_app Analyst Workbench output —
        pre-analyzed, decision-leveled observations.
        """
        return {
            "capability": "market.intelligence.observe",
            "source": "ai_theme_app_analyst_workbench",
            "schema_version": "1.1",
            "observations": [
                {
                    "id": "obs_syn_001",
                    "type": "theme.breakout",
                    "theme": "AI机器人",
                    "signal_level": "L3",
                    "summary": "机器人产业链出现资金共振，龙头连续走强",
                    "evidence": ["theme_heat_+18%", "fund_flow_increase", "leader_board_strength"],
                    "confidence": 0.86,
                    "prediction_id": "pred_syn_001",
                    "decision_envelope_ref": "dec_syn_001",
                },
                {
                    "id": "obs_syn_002",
                    "type": "risk.emerged",
                    "theme": "半导体",
                    "signal_level": "L2",
                    "summary": "外围消息面扰动，板块出现分化信号",
                    "evidence": ["sentiment_shift", "volume_decline"],
                    "confidence": 0.62,
                    "prediction_id": "pred_syn_002",
                    "decision_envelope_ref": "dec_syn_002",
                },
                {
                    "id": "obs_syn_003",
                    "type": "sentiment.shift",
                    "theme": "整体市场",
                    "signal_level": "L1",
                    "summary": "大盘情绪小幅波动，无明确方向",
                    "evidence": ["index_flat", "vix_stable"],
                    "confidence": 0.45,
                },
            ],
        }

    def _normalize(self, raw: dict) -> dict:
        """Normalize raw MCP response to standard format."""
        return {
            "capability": "market.intelligence.observe",
            "source": raw.get("source", "ai_theme_app_analyst_workbench"),
            "schema_version": raw.get("schema_version", "1.1"),
            "observations": raw.get("observations", []),
        }

    async def health(self) -> tuple[bool, str]:
        if self._adapter:
            return await self._adapter.health()
        return True, "synthetic intelligence provider — available"


__all__ = [
    "MarketIntelligenceProvider",
    "DECISION_LEVEL_BEHAVIOR",
    "DECISION_LEVEL_ADMISSION_WEIGHT",
]

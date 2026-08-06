"""M3.2.1 Contract Mapper — real MCP tool output → intelligence observation format.

ADR-030 Section 1: Maps ai_theme_app MCP tool results to the frozen
observation schema. This is the bridge between "raw MCP" and "curated intelligence."

The mapper COMPOSES intelligence from multiple MCP tools:
  review_market_snapshot()  →  market state + active themes
  list_active_alerts()      →  active decision signals with levels

Output: market.intelligence.observe capability result format.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))


class IntelligenceContractMapper:
    """Maps raw MCP tool output → ADR-030 intelligence observation format.

    This is NOT a data passthrough. It COMPOSES observations from
    multiple MCP tools into a single curated intelligence report.
    """

    def __init__(self, adapter):
        """adapter: MCPToolAdapter for calling ai_theme_app MCP tools."""
        self._adapter = adapter

    async def observe(self) -> dict:
        """Execute market.intelligence.observe using real MCP tools.

        Composes observations from:
          1. review_market_snapshot() — overall market state
          2. list_active_alerts("alert") — high-priority signals

        Returns ADR-030 frozen format with observations array.
        """
        now = datetime.now(CST).isoformat()
        observations = []

        # 1. Get market snapshot
        try:
            snapshot = await self._adapter.call("market.snapshot.read", {})
            observations.extend(self._from_snapshot(snapshot))
        except Exception:
            pass  # Graceful: snapshot unavailable doesn't block alerts

        # 2. Get active alerts (L3+ signals)
        try:
            alerts = await self._adapter.call("market.alert.query", {"level": "alert"})
            observations.extend(self._from_alerts(alerts))
        except Exception:
            pass  # Graceful: alerts unavailable doesn't block snapshot

        return {
            "capability": "market.intelligence.observe",
            "source": "ai_theme_app_analyst_workbench",
            "schema_version": "1.1",
            "generated_at": now,
            "observations": observations,
        }

    def _from_snapshot(self, snapshot: dict) -> list[dict]:
        """Extract observations from market snapshot data."""
        observations = []

        # Market sentiment observation
        sentiment = snapshot.get("market_sentiment", "")
        if sentiment:
            level = "L1"
            if sentiment in ("偏强", "强"):
                level = "L3"
            elif sentiment in ("偏弱", "弱"):
                level = "L2"

            observations.append({
                "id": f"obs_snap_{_short_id()}",
                "type": "market.sentiment",
                "theme": "整体市场",
                "signal_level": level,
                "summary": f"市场情绪: {sentiment}",
                "evidence": [f"market_sentiment_{sentiment}"],
                "confidence": 0.7,
                "prediction_id": "",
                "decision_envelope_ref": "",
            })

        # Active theme observations
        themes = snapshot.get("active_themes", [])
        for theme in themes[:3]:
            observations.append({
                "id": f"obs_theme_{_short_id()}",
                "type": "theme.active",
                "theme": theme,
                "signal_level": "L2",
                "summary": f"活跃题材: {theme}",
                "evidence": ["active_themes_list"],
                "confidence": 0.65,
                "prediction_id": "",
                "decision_envelope_ref": "",
            })

        # Risk alerts
        risks = snapshot.get("risk_alerts", [])
        for risk in risks[:3]:
            observations.append({
                "id": f"obs_risk_{_short_id()}",
                "type": "risk.observed",
                "theme": "风险提示",
                "signal_level": "L2",
                "summary": risk,
                "evidence": ["risk_alert"],
                "confidence": 0.6,
                "prediction_id": "",
                "decision_envelope_ref": "",
            })

        return observations

    def _from_alerts(self, alerts: list[dict]) -> list[dict]:
        """Extract observations from active DecisionEnvelope alerts."""
        observations = []
        for alert in (alerts or [])[:5]:
            level = alert.get("level", "L0")
            source = alert.get("source", "")
            theme_ctx = alert.get("theme_context") or {}
            theme = theme_ctx.get("theme_id", alert.get("type", "unknown"))

            observations.append({
                "id": f"obs_alert_{alert.get('id', _short_id())}",
                "type": f"signal.{source}" if source else "signal.detected",
                "theme": theme,
                "signal_level": level.upper() if not level.startswith("L") else level,
                "summary": alert.get("impact", "") or f"{level} signal from {source}",
                "evidence": [
                    f"confidence_{alert.get('confidence', 0)}",
                    f"source_{source}",
                ],
                "confidence": float(alert.get("confidence", 0.5)),
                "prediction_id": alert.get("prediction_id", ""),
                "decision_envelope_ref": alert.get("id", ""),
            })
        return observations

    async def health(self) -> tuple[bool, str]:
        try:
            return await self._adapter.health()
        except Exception:
            return False, "contract mapper — adapter health check failed"


def _short_id() -> str:
    import uuid
    return uuid.uuid4().hex[:8]


__all__ = ["IntelligenceContractMapper"]

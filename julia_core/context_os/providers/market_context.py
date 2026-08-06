"""M2.1 Market Brief Context Adapter — DecisionEnvelope → ContextBlock.

Converts ai_theme_app Market Brain output into governed ContextBlocks
for Julia Reasoning. This is the ONLY path through which market data
enters Julia's cognitive context.

ADR-026 P2: Context OS is Single Authority — no domain assembles prompts.
ADR-026 P4: Provider supplies capability, not cognition.
ADR-026 P5: Provider output ≠ Identity truth — governance before context.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from julia_core.context_os.block import ContextBlock

CST = timezone(timedelta(hours=8))


# ── Market Context Adapter ──────────────────────────────────────────────────

class MarketBriefContextAdapter:
    """Converts a CapabilityResult from market.snapshot.read into ContextBlocks.

    Does NOT:
      - Call MCP directly
      - Interpret market data
      - Generate Julia's response
      - Write to memory

    Responsibilities:
      1. Validate schema_version (DecisionEnvelope v1.1)
      2. Extract structured facts into ContextBlocks
      3. Attach evidence_refs and source_refs for provenance
    """

    REQUIRED_SCHEMA = "1.1"
    SOURCE_DOMAIN = "ai_theme_app"
    AUTHORITY = "market_data"

    def build_context_blocks(self, capability_result: dict) -> list[ContextBlock]:
        """Convert a market.snapshot.read capability result into ContextBlocks.

        capability_result: the data dict from AiThemeProvider.execute()
        Returns: list of ContextBlocks ready for Context OS assembly
        """
        # Validate schema
        schema_version = capability_result.get("schema_version", "")
        if schema_version != self.REQUIRED_SCHEMA:
            return [self._schema_warning_block(schema_version)]

        data = capability_result.get("data", {})
        if not data:
            return [self._empty_data_block()]

        blocks: list[ContextBlock] = []

        # Block 1: Market Overview (required — always included)
        overview = self._market_overview_block(data)
        if overview:
            blocks.append(overview)

        # Block 2: Active Themes (required — always included)
        themes = self._active_themes_block(data)
        if themes:
            blocks.append(themes)

        # Block 3: Top Signals (optional — included when present)
        signals = self._top_signals_block(data)
        if signals:
            blocks.append(signals)

        # Block 4: Risk Alerts (required — always included)
        risks = self._risk_alerts_block(data)
        if risks:
            blocks.append(risks)

        # Evidence envelope — wraps all blocks with provenance
        evidence = self._evidence_envelope(capability_result)
        if evidence:
            blocks.append(evidence)

        return blocks

    # ── Block Builders ──────────────────────────────────────────────────

    def _market_overview_block(self, data: dict) -> ContextBlock | None:
        sentiment = data.get("market_sentiment", "未知")
        date = data.get("date", "")

        content = {
            "section": "market_overview",
            "sentiment": sentiment,
            "date": date,
            "summary": f"今日市场情绪: {sentiment}" if sentiment != "未知" else "今日市场数据不可用",
        }

        return ContextBlock(
            source=self.SOURCE_DOMAIN,
            content=content,
            authority=self.AUTHORITY,
            block_type="market_overview",
            block_kind="external_intelligence",
            domain="market",
            authority_score=0.8,
            required=True,
            estimated_tokens=100,
        )

    def _active_themes_block(self, data: dict) -> ContextBlock | None:
        themes = data.get("active_themes", [])
        if not themes:
            return None

        content = {
            "section": "active_themes",
            "themes": list(themes),
            "count": len(themes),
            "summary": f"当前活跃题材: {', '.join(themes[:5])}",
        }

        return ContextBlock(
            source=self.SOURCE_DOMAIN,
            content=content,
            authority=self.AUTHORITY,
            block_type="market_themes",
            block_kind="external_intelligence",
            domain="market",
            authority_score=0.75,
            required=True,
            estimated_tokens=150,
        )

    def _top_signals_block(self, data: dict) -> ContextBlock | None:
        signals = data.get("top_signals", [])
        if not signals:
            return None

        # Extract key signal metadata without full DecisionEnvelope body
        signal_summaries = []
        prediction_ids = []
        for sig in signals[:3]:
            signal_summaries.append({
                "id": sig.get("id", ""),
                "level": sig.get("level", ""),
                "impact": sig.get("impact", ""),
                "confidence": sig.get("confidence", 0.0),
                "type": sig.get("type", ""),
            })
            if sig.get("prediction_id"):
                prediction_ids.append(sig["prediction_id"])

        content = {
            "section": "top_signals",
            "signal_count": len(signals),
            "signals": signal_summaries,
            "prediction_ids": prediction_ids,
        }

        return ContextBlock(
            source=self.SOURCE_DOMAIN,
            content=content,
            authority=self.AUTHORITY,
            block_type="market_signals",
            block_kind="external_intelligence",
            domain="market",
            evidence_refs=tuple(s["id"] for s in signal_summaries if s["id"]),
            authority_score=0.7,
            required=False,
            estimated_tokens=200,
        )

    def _risk_alerts_block(self, data: dict) -> ContextBlock | None:
        risks = data.get("risk_alerts", [])
        if not risks:
            return None

        content = {
            "section": "risk_alerts",
            "risks": list(risks),
            "count": len(risks),
            "summary": f"当前风险提示: {'; '.join(risks[:5])}",
        }

        return ContextBlock(
            source=self.SOURCE_DOMAIN,
            content=content,
            authority=self.AUTHORITY,
            block_type="market_risks",
            block_kind="external_intelligence",
            domain="market",
            authority_score=0.8,
            required=True,
            estimated_tokens=120,
        )

    def _evidence_envelope(self, capability_result: dict) -> ContextBlock | None:
        """Create a provenance block linking all market context to its source."""
        return ContextBlock(
            source=self.SOURCE_DOMAIN,
            content={
                "section": "evidence",
                "provider": capability_result.get("provider", self.SOURCE_DOMAIN),
                "schema_version": capability_result.get("schema_version", ""),
                "capability": capability_result.get("capability", ""),
                "request_id": capability_result.get("request_id", ""),
                "generated_at": datetime.now(CST).isoformat(),
            },
            authority=f"{self.AUTHORITY}.evidence",
            block_type="evidence_envelope",
            block_kind="provenance",
            domain="market",
            authority_score=1.0,
            required=False,
            estimated_tokens=80,
        )

    def _schema_warning_block(self, version: str) -> ContextBlock:
        return ContextBlock(
            source=self.SOURCE_DOMAIN,
            content={
                "section": "schema_warning",
                "message": f"Market data schema version mismatch: got {version}, expected {self.REQUIRED_SCHEMA}",
            },
            authority=self.AUTHORITY,
            block_type="market_schema_warning",
            block_kind="error",
            domain="market",
            authority_score=0.0,
            required=True,
            estimated_tokens=50,
        )

    def _empty_data_block(self) -> ContextBlock:
        return ContextBlock(
            source=self.SOURCE_DOMAIN,
            content={
                "section": "no_data",
                "message": "Market data is currently unavailable",
            },
            authority=self.AUTHORITY,
            block_type="market_no_data",
            block_kind="error",
            domain="market",
            authority_score=0.0,
            required=True,
            estimated_tokens=50,
        )


__all__ = ["MarketBriefContextAdapter"]

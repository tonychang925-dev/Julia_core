"""M1.1 AiThemeProvider — ai_theme_app Market Brain as a Julia Capability Provider.

Implements CapabilityProvider protocol for market intelligence capabilities.
Wraps MCP tool results in CapabilityResult with schema version metadata.

This provider does NOT:
  - Analyze stocks
  - Interpret markets
  - Generate advice
  - Own reasoning

Those belong to ai_theme_app (facts) and Julia Reasoning (interpretation).

ADR-002/ADR-026: Domain provides facts, Julia provides interpretation.
Never the other way around.
"""

from __future__ import annotations

from julia_core.capability.models import CapabilityRequest
from julia_core.capability.providers.ai_theme.adapter import MCPToolAdapter

# ── Schema version: must match ai_theme_app DecisionEnvelope v1.1 ──────────
DECISION_ENVELOPE_VERSION = "1.1"


class AiThemeProvider:
    """External Intelligence Provider — ai_theme_app Market Brain.

    Three read-only capabilities (M1 scope):
      market.snapshot.read    — Today's market overview
      market.alert.query      — Active alerts at/above given level
      market.decision.explain — Why a specific decision was made

    Future (M2/M3): market.theme.observe, market.event.subscribe
    """

    def __init__(self, adapter: MCPToolAdapter | None = None):
        self.adapter = adapter or MCPToolAdapter()

    # ── CapabilityProvider Protocol ────────────────────────────────────

    async def execute(self, request: CapabilityRequest) -> dict:
        """Execute a market intelligence capability.

        For M3.2.1: market.intelligence.observe uses ContractMapper
        to compose observations from real MCP tools (snapshot + alerts).

        Other capabilities (snapshot.read, alert.query, decision.explain)
        use direct MCP tool mapping as before.
        """
        # M3.2.1: Intelligence observation path
        if request.capability_name == "market.intelligence.observe":
            from julia_core.capability.providers.ai_theme.contract_mapper import (
                IntelligenceContractMapper,
            )
            mapper = IntelligenceContractMapper(self.adapter)
            result = await mapper.observe()
            return {
                "provider": "ai_theme_app",
                "schema": "Observation.v1.0",
                "schema_version": "1.0",
                "capability": request.capability_name,
                "data": result,
                "request_id": request.request_id,
            }

        # Existing path: direct MCP tool mapping
        raw = await self.adapter.call(
            request.capability_name,
            request.arguments,
        )

        return {
            "provider": "ai_theme_app",
            "schema": f"DecisionEnvelope.v{DECISION_ENVELOPE_VERSION}",
            "schema_version": DECISION_ENVELOPE_VERSION,
            "capability": request.capability_name,
            "data": raw,
            "request_id": request.request_id,
        }

    async def health(self) -> tuple[bool, str]:
        """Check if ai_theme_app MCP is reachable."""
        return await self.adapter.health()


__all__ = ["AiThemeProvider", "DECISION_ENVELOPE_VERSION"]

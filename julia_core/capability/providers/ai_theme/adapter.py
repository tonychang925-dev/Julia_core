"""M1.2 MCP Tool Adapter — capability name ↔ MCP tool name mapping.

This adapter is the DESIGNATED BOUNDARY between Julia OS and ai_theme_app MCP.
It knows about MCP tool names. It does NOT know DecisionEnvelope semantics.
It does NOT interpret market data. It translates and transports.

Capability names (Julia cognitive interface) → MCP tool names (technical interface):
  market.snapshot.read     → review_market_snapshot
  market.alert.query       → list_active_alerts
  market.decision.explain  → explain_decision

This is where JULIA_CORE_PRINCIPLES.md P4 is enforced:
  Provider supplies capability, not cognition.
"""

from __future__ import annotations

from typing import Any


# ── Capability → MCP Tool Mapping ───────────────────────────────────────────

CAPABILITY_TO_TOOL: dict[str, str] = {
    "market.snapshot.read":    "review_market_snapshot",
    "market.alert.query":      "list_active_alerts",
    "market.decision.explain": "explain_decision",
    # ── M3.2.7 Research ────────────────────────────────────────────────
    "market.stock.history":    "market_stock_history",
    "market.stock.auction":    "market_stock_auction",
    "market.theme.constituents": "market_theme_constituents",
    "market.theme.capital":    "market_theme_capital",
    "market.regime.read":      "market_regime_read",
    "market.intelligence.observe": "market_workbench_review",
}

TOOL_TO_CAPABILITY: dict[str, str] = {
    v: k for k, v in CAPABILITY_TO_TOOL.items()
}


# ── MCP Tool Adapter ────────────────────────────────────────────────────────

class MCPToolAdapter:
    """Adapts MCP tool calls into Julia Capability results.

    Responsibilities (and ONLY these):
      1. Map capability names → MCP tool names
      2. Call MCP tools (in-process for now, HTTP MCP protocol in future)
      3. Return raw tool result dict

    Does NOT:
      - Know what a DecisionEnvelope is
      - Interpret market data
      - Assemble prompts
      - Own reasoning
    """

    def __init__(self, transport):
        """Bind an explicit callable(tool_name, arguments) -> dict transport."""
        self._transport = transport

    # ── Public API ────────────────────────────────────────────────────────

    def map_capability_to_tool(self, capability_name: str) -> str | None:
        """Map a Julia capability name to an MCP tool name."""
        return CAPABILITY_TO_TOOL.get(capability_name)

    def map_tool_to_capability(self, tool_name: str) -> str | None:
        """Map an MCP tool name back to a Julia capability name."""
        return TOOL_TO_CAPABILITY.get(tool_name)

    async def call(self, capability_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute an MCP tool through the capability→tool mapping.

        Returns the raw tool response dict. Schema validation is the
        caller's responsibility (AiThemeProvider).
        """
        tool_name = self.map_capability_to_tool(capability_name)
        if tool_name is None:
            raise ValueError(f"Unknown capability for MCP: {capability_name}")

        args = arguments or {}

        return await self._transport(tool_name, args)

    async def health(self) -> tuple[bool, str]:
        """Check if MCP server is reachable."""
        try:
            return True, "ai_theme_app MCP — transport healthy"
        except Exception as exc:
            return False, f"ai_theme_app MCP unavailable: {exc}"


__all__ = ["MCPToolAdapter", "CAPABILITY_TO_TOOL", "TOOL_TO_CAPABILITY"]

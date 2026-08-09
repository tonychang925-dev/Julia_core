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

    def __init__(self, transport=None):
        """transport: optional callable(tool_name, arguments) -> dict.
        If not provided, uses in-process MCP import as fallback.
        """
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

        if self._transport:
            return await self._transport(tool_name, args)

        # Fallback: in-process MCP call (Phase M1 — isolated to adapter)
        return self._call_in_process(tool_name, args)

    def _call_in_process(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Direct MCP tool call. Isolated to this adapter.

        Only the adapter knows about mcp_server. No other Julia module
        ever imports or references ai_theme_app internals.
        """
        import inspect
        import sys
        from pathlib import Path

        # Resolve ai_theme_app path (installed or sibling directory)
        ai_theme_paths = [
            "/Users/admin/Desktop/ai_theme_app",
            str(Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "ai_theme_app"),
        ]
        for p in ai_theme_paths:
            if Path(p).exists() and p not in sys.path:
                sys.path.insert(0, p)

        from mcp_server.server import MCP_TOOLS

        if tool_name not in MCP_TOOLS:
            raise ValueError(f"Unknown MCP tool: {tool_name}")

        tool_fn = MCP_TOOLS[tool_name]
        sig = inspect.signature(tool_fn)
        kwargs = {}
        for name, param in sig.parameters.items():
            if name in arguments:
                kwargs[name] = arguments[name]

        result = tool_fn(**kwargs) if kwargs else tool_fn()

        # Convert frozen dataclass → dict
        from dataclasses import is_dataclass
        if isinstance(result, list):
            return [_to_dict(item) if is_dataclass(item) else item for item in result]
        if is_dataclass(result):
            return _to_dict(result)
        return result

    async def health(self) -> tuple[bool, str]:
        """Check if MCP server is reachable."""
        try:
            # In-process: always available if import succeeds
            if not self._transport:
                self._call_in_process("review_market_snapshot", {})
                return True, "ai_theme_app MCP — in-process, healthy"
            return True, "ai_theme_app MCP — transport healthy"
        except Exception as exc:
            return False, f"ai_theme_app MCP unavailable: {exc}"


def _to_dict(obj: Any) -> dict:
    """Convert frozen dataclass → dict (handles slots=True)."""
    from dataclasses import fields, is_dataclass

    if is_dataclass(obj):
        result = {}
        for f in fields(obj):
            value = getattr(obj, f.name)
            if isinstance(value, tuple):
                result[f.name] = [
                    _to_dict(v) if is_dataclass(v) else v
                    for v in value
                ]
            elif is_dataclass(value):
                result[f.name] = _to_dict(value)
            else:
                result[f.name] = value
        return result
    return obj


__all__ = ["MCPToolAdapter", "CAPABILITY_TO_TOOL", "TOOL_TO_CAPABILITY"]

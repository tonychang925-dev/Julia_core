"""MarketBrainClient — Julia's first neural connection to ai_theme_app.

Read-only. All tools return structured data that Julia interprets.
ai_theme_app owns facts. Julia owns understanding.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Any

from julia_core.mcp_client.models import (
    DecisionEnvelope,
    ThemeStatusSnapshot,
    MarketSnapshot,
    DecisionExplanation,
    ChannelState,
    Evidence,
    CausalLink,
    ThemeContext,
)


def _to_evidence(data: dict) -> Evidence:
    return Evidence(
        type=data.get("type", ""),
        text=data.get("text", ""),
        source=data.get("source", ""),
        ref_id=data.get("ref_id", ""),
        authority=data.get("authority", 0.5),
    )


def _to_causal_link(data: dict) -> CausalLink:
    return CausalLink(
        cause=data.get("cause", ""),
        effect=data.get("effect", ""),
        market_response=data.get("market_response", ""),
        confidence=data.get("confidence", 0.5),
    )


def _to_theme_context(data: dict | None) -> ThemeContext | None:
    if data is None:
        return None
    return ThemeContext(
        theme_id=data.get("theme_id", ""),
        lifecycle=data.get("lifecycle", ""),
        previous_state=data.get("previous_state", ""),
        change=data.get("change", ""),
        first_signal_date=data.get("first_signal_date", ""),
        days_active=data.get("days_active", 0),
    )


def _to_decision_envelope(data: dict) -> DecisionEnvelope:
    return DecisionEnvelope(
        id=data.get("id", ""),
        timestamp=data.get("timestamp", ""),
        source=data.get("source", ""),
        type=data.get("type", ""),
        level=data.get("level", ""),
        evidence=tuple(_to_evidence(e) for e in data.get("evidence", ())),
        causal_chain=tuple(_to_causal_link(c) for c in data.get("causal_chain", ())),
        theme_context=_to_theme_context(data.get("theme_context")),
        prediction_id=data.get("prediction_id"),
        confidence=data.get("confidence", 0.0),
        impact=data.get("impact", "unknown"),
        expiry=data.get("expiry"),
        payload=data.get("payload", {}),
    )


class MarketBrainClient:
    """Read-only MCP transport to ai_theme_app Market Brain.

    Usage:
        brain = MarketBrainClient(endpoint="http://localhost:8010")
        snap = await brain.review_market_snapshot()
        alerts = await brain.list_active_alerts(level="decision")
    """

    def __init__(self, endpoint: str | None = None):
        self.endpoint = endpoint or os.environ.get(
            "AI_THEME_APP_ENDPOINT", "http://localhost:8010"
        )

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Raw MCP tool call. Override in subclasses for real HTTP transport."""
        # Phase 2: In-process direct call for testing.
        # Phase 3: Replace with httpx async HTTP → MCP protocol.
        from mcp_server.server import MCP_TOOLS

        if tool_name not in MCP_TOOLS:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool_fn = MCP_TOOLS[tool_name]

        # Detect required positional args and extract from params
        import inspect
        sig = inspect.signature(tool_fn)
        kwargs = {}
        for name, param in sig.parameters.items():
            if name in params:
                kwargs[name] = params[name]
            elif param.default is param.empty and name != "date" and name != "level" and name != "agent_id":
                pass  # will use default

        result = tool_fn(**kwargs) if kwargs else tool_fn()

        # Convert frozen dataclass → dict for transport
        from dataclasses import is_dataclass
        if isinstance(result, list):
            return [_dataclass_to_dict(item) if is_dataclass(item) else item for item in result]
        if is_dataclass(result):
            return _dataclass_to_dict(result)
        return result

    # ── 5 MCP Tools ──

    async def query_theme_status(self, theme_id: str) -> ThemeStatusSnapshot:
        """Tool 1: What's the status of a specific theme?"""
        data = await self.call_tool("query_theme_status", {"theme_id": theme_id})
        return ThemeStatusSnapshot(
            theme=data.get("theme", ""),
            lifecycle=data.get("lifecycle", ""),
            heat_score=data.get("heat_score", 0),
            leaders=tuple(data.get("leaders", ())),
            money_flow=data.get("money_flow", ""),
            causal_chain=tuple(_to_causal_link(c) for c in data.get("causal_chain", ())),
            risk=data.get("risk", "unknown"),
        )

    async def list_active_alerts(self, level: str = "decision") -> list[DecisionEnvelope]:
        """Tool 2: What L4 signals are active right now?"""
        data = await self.call_tool("list_active_alerts", {"level": level})
        if isinstance(data, list):
            return [_to_decision_envelope(d) for d in data]
        return []

    async def review_market_snapshot(self) -> MarketSnapshot:
        """Tool 3: Today's market overview."""
        data = await self.call_tool("review_market_snapshot", {})
        return MarketSnapshot(
            market_sentiment=data.get("market_sentiment", ""),
            active_themes=tuple(data.get("active_themes", ())),
            top_signals=tuple(_to_decision_envelope(d) for d in data.get("top_signals", ())),
            risk_alerts=tuple(data.get("risk_alerts", ())),
            date=data.get("date", ""),
        )

    async def subscribe_agent_channel(self, channels: list[str]) -> ChannelState:
        """Tool 4: Subscribe to market observation channels."""
        data = await self.call_tool("subscribe_agent_channel", {"channels": channels})
        return ChannelState(
            subscribed=tuple(data.get("subscribed", ())),
            active=data.get("active", False),
        )

    async def explain_decision(self, decision_id: str) -> DecisionExplanation | None:
        """Tool 5: Why was this decision made?"""
        data = await self.call_tool("explain_decision", {"decision_id": decision_id})
        if data is None:
            return None
        return DecisionExplanation(
            decision_id=data.get("decision_id", ""),
            summary=data.get("summary", ""),
            causal_chain=tuple(_to_causal_link(c) for c in data.get("causal_chain", ())),
            supporting_evidence=data.get("supporting_evidence", 0),
            opposing_evidence=data.get("opposing_evidence", 0),
            confidence=data.get("confidence", 0.0),
            risk_factors=tuple(data.get("risk_factors", ())),
            alternatives=tuple(data.get("alternatives", ())),
        )


def _dataclass_to_dict(obj: Any) -> dict:
    """Convert frozen dataclass → dict, handling nested tuples of dataclasses.

    Uses dataclasses.fields() instead of __dict__ because slots=True dataclasses
    have no __dict__.
    """
    from dataclasses import fields, is_dataclass

    if is_dataclass(obj):
        result = {}
        for field in fields(obj):
            name = field.name
            value = getattr(obj, name)
            if isinstance(value, tuple):
                result[name] = [
                    _dataclass_to_dict(v) if is_dataclass(v) else v
                    for v in value
                ]
            elif is_dataclass(value):
                result[name] = _dataclass_to_dict(value)
            else:
                result[name] = value
        return result
    return obj

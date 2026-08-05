"""Julia Core MCP Client — neural connection to Market Brain (ai_theme_app).

Read-only. Julia interprets; ai_theme_app supplies facts.
"""
from julia_core.mcp_client.client import MarketBrainClient
from julia_core.mcp_client.models import (
    DecisionEnvelope,
    ThemeStatusSnapshot,
    MarketSnapshot,
    DecisionExplanation,
    ChannelState,
)

__all__ = [
    "MarketBrainClient",
    "DecisionEnvelope",
    "ThemeStatusSnapshot",
    "MarketSnapshot",
    "DecisionExplanation",
    "ChannelState",
]

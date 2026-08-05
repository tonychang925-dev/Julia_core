"""MCP Client Models — Julia-side mirrors of ai_theme_app DecisionEnvelope v1.1.

Two systems share the protocol, not the code. These dataclasses are the
Julia-side representation of Market Brain outputs. They NEVER own facts —
they only represent what ai_theme_app has already computed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

CST = timezone(timedelta(hours=8))


@dataclass(frozen=True, slots=True)
class Evidence:
    """Source-traceable evidence item (read from MCP)."""
    type: str = ""
    text: str = ""
    source: str = ""
    ref_id: str = ""
    authority: float = 0.5


@dataclass(frozen=True, slots=True)
class CausalLink:
    """One link in the causal chain."""
    cause: str = ""
    effect: str = ""
    market_response: str = ""
    confidence: float = 0.5


@dataclass(frozen=True, slots=True)
class ThemeContext:
    """Theme lifecycle position."""
    theme_id: str = ""
    lifecycle: str = ""
    previous_state: str = ""
    change: str = ""
    first_signal_date: str = ""
    days_active: int = 0


@dataclass(frozen=True, slots=True)
class DecisionEnvelope:
    """Market Brain output — Julia reads, never writes."""
    id: str = ""
    timestamp: str = ""
    source: str = ""
    type: str = ""
    level: str = ""
    evidence: tuple[Evidence, ...] = ()
    causal_chain: tuple[CausalLink, ...] = ()
    theme_context: ThemeContext | None = None
    prediction_id: str | None = None
    confidence: float = 0.0
    impact: str = "unknown"
    expiry: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.75


@dataclass(frozen=True, slots=True)
class ThemeStatusSnapshot:
    """Theme state at a glance."""
    theme: str = ""
    lifecycle: str = ""
    heat_score: int = 0
    leaders: tuple[str, ...] = ()
    money_flow: str = ""
    causal_chain: tuple[CausalLink, ...] = ()
    risk: str = "unknown"


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """Today's market overview."""
    market_sentiment: str = ""
    active_themes: tuple[str, ...] = ()
    top_signals: tuple[DecisionEnvelope, ...] = ()
    risk_alerts: tuple[str, ...] = ()
    date: str = ""


@dataclass(frozen=True, slots=True)
class DecisionExplanation:
    """Structured explanation for a single decision."""
    decision_id: str = ""
    summary: str = ""
    causal_chain: tuple[CausalLink, ...] = ()
    supporting_evidence: int = 0
    opposing_evidence: int = 0
    confidence: float = 0.0
    risk_factors: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ChannelState:
    """Active subscriptions."""
    subscribed: tuple[str, ...] = ()
    active: bool = False

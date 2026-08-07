"""M3.2.7 Requirement Binding Registry — maps strategy required_data → Julia capability_name.

This belongs in Julia_core because CapabilityManager is Julia's.
ai_theme_app StrategyCards only know abstract requirement names
(e.g. "leader_5d_return"), not how to fulfill them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RequirementBinding:
    """Maps one strategy-level requirement to a Julia capability invocation."""
    requirement_id: str
    capability_name: str             # e.g. "market.stock.history"
    arguments_template: dict[str, Any]  # $subject.key references
    derive_metric: str = ""
    output_type: str = ""
    missing_policy: str = "INSUFFICIENT_EVIDENCE"


REQUIREMENT_BINDINGS: dict[str, RequirementBinding] = {
    # ── Leader research ─────────────────────────────────────────────────
    "leader_5d_return": RequirementBinding(
        requirement_id="leader_5d_return",
        capability_name="market.stock.history",
        arguments_template={
            "stock_code": "$subject.leader_code",
            "as_of": "$subject.trade_date",
            "lookback_sessions": 5,
        },
        derive_metric="total_return",
        output_type="ratio",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),
    "leader_drawdown_from_peak": RequirementBinding(
        requirement_id="leader_drawdown_from_peak",
        capability_name="market.stock.history",
        arguments_template={
            "stock_code": "$subject.leader_code",
            "as_of": "$subject.trade_date",
            "lookback_sessions": 5,
        },
        derive_metric="max_drawdown_from_peak",
        output_type="ratio",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),
    "leader_volume_pattern": RequirementBinding(
        requirement_id="leader_volume_pattern",
        capability_name="market.stock.history",
        arguments_template={
            "stock_code": "$subject.leader_code",
            "as_of": "$subject.trade_date",
            "lookback_sessions": 5,
        },
        derive_metric="volume_trend",
        output_type="categorical",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),
    "key_level_status": RequirementBinding(
        requirement_id="key_level_status",
        capability_name="market.stock.history",
        arguments_template={
            "stock_code": "$subject.leader_code",
            "as_of": "$subject.trade_date",
            "lookback_sessions": 5,
        },
        derive_metric="key_level_status",
        output_type="categorical",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),
    # weak_to_strong Card uses different name → alias
    "leader_key_level": RequirementBinding(
        requirement_id="leader_key_level",
        capability_name="market.stock.history",
        arguments_template={
            "stock_code": "$subject.leader_code",
            "as_of": "$subject.trade_date",
            "lookback_sessions": 5,
        },
        derive_metric="key_level_status",
        output_type="categorical",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),

    # ── Theme structure ─────────────────────────────────────────────────
    "peer_relative_strength": RequirementBinding(
        requirement_id="peer_relative_strength",
        capability_name="market.theme.constituents",
        arguments_template={
            "subject_key": "$subject.subject_key",
            "as_of": "$subject.trade_date",
        },
        derive_metric="peer_relative_strength",
        output_type="dict",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),
    "theme_breadth_change": RequirementBinding(
        requirement_id="theme_breadth_change",
        capability_name="market.theme.constituents",
        arguments_template={
            "subject_key": "$subject.subject_key",
            "as_of": "$subject.trade_date",
        },
        derive_metric="breadth_change",
        output_type="dict",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),
    "new_leader_candidates": RequirementBinding(
        requirement_id="new_leader_candidates",
        capability_name="market.theme.constituents",
        arguments_template={
            "subject_key": "$subject.subject_key",
            "as_of": "$subject.trade_date",
        },
        derive_metric="emerging_leaders",
        output_type="list",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),

    # ── Capital ─────────────────────────────────────────────────────────
    "capital_persistence": RequirementBinding(
        requirement_id="capital_persistence",
        capability_name="market.theme.capital",
        arguments_template={
            "subject_key": "$subject.subject_key",
            "as_of": "$subject.trade_date",
        },
        derive_metric="capital_flow_trend",
        output_type="categorical",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),

    # ── Market context ──────────────────────────────────────────────────
    "market_regime": RequirementBinding(
        requirement_id="market_regime",
        capability_name="market.regime.read",
        arguments_template={
            "as_of": "$subject.trade_date",
        },
        derive_metric="derived.regime_assessment.value",
        output_type="dict",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),

    # ── Auction ─────────────────────────────────────────────────────────
    "auction_strength": RequirementBinding(
        requirement_id="auction_strength",
        capability_name="market.stock.auction",
        arguments_template={
            "stock_code": "$subject.leader_code",
            "as_of": "$subject.trade_date",
        },
        derive_metric="auction_trend",
        output_type="categorical",
        missing_policy="DATA_UNAVAILABLE",
    ),
    "open_gap": RequirementBinding(
        requirement_id="open_gap",
        capability_name="market.stock.history",
        arguments_template={
            "stock_code": "$subject.leader_code",
            "as_of": "$subject.trade_date",
        },
        derive_metric="open_gap_vs_prev_close",
        output_type="ratio",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),
    "intraday_volume": RequirementBinding(
        requirement_id="intraday_volume",
        capability_name="market.stock.history",
        arguments_template={
            "stock_code": "$subject.leader_code",
            "as_of": "$subject.trade_date",
        },
        derive_metric="intraday_volume_vs_prev",
        output_type="categorical",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),
    "limit_up_seal_quality": RequirementBinding(
        requirement_id="limit_up_seal_quality",
        capability_name="market.stock.history",
        arguments_template={
            "stock_code": "$subject.leader_code",
            "as_of": "$subject.trade_date",
        },
        derive_metric="limit_up_seal",
        output_type="categorical",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),
    "peer_follow_through": RequirementBinding(
        requirement_id="peer_follow_through",
        capability_name="market.theme.constituents",
        arguments_template={
            "subject_key": "$subject.subject_key",
            "as_of": "$subject.trade_date",
        },
        derive_metric="peer_limit_up_ratio",
        output_type="ratio",
        missing_policy="INSUFFICIENT_EVIDENCE",
    ),
}


__all__ = ["RequirementBinding", "REQUIREMENT_BINDINGS"]

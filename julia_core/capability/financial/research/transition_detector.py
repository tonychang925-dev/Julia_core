"""M3.2.7.5 Transition Detector — T-1 → T0 structural change detection.

Deterministic. Zero LLM. Answers only: what happened between two sessions?
Does NOT re-judge market stage or strategy state.

Output: TransitionResult with type, evidence, and next-card suggestion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TransitionResult:
    transition_type: str
    from_date: str
    to_date: str
    supported_by: list[str] = field(default_factory=list)
    suggested_next_card: str = ""
    rule_version: str = "transition-detector.v1"


class TransitionDetector:
    """Detects session-to-session structural transitions from EvidenceBundle.

    Only reads breadth_change evidence (from/to/delta).
    Does NOT access market_stage, strategy_state, or any opinion.
    """

    def detect(self, evidence: dict[str, Any]) -> TransitionResult | None:
        """Detect transition type from breadth_change evidence.

        Returns None if insufficient data for detection.
        """
        bc_item = evidence.get("theme_breadth_change")
        if not bc_item or bc_item.status not in ("success", "live"):
            return None

        bc = bc_item.derived_value or {}
        from_data = bc.get("from", {})
        to_data = bc.get("to", {})
        delta = bc.get("delta", {})

        from_date = bc.get("from_trade_date", "?")
        to_date = bc.get("to_trade_date", "?")

        results = []

        # Rule: synchronized_repair
        prev_pos = _num(from_data.get("positive_ratio", 0))
        t0_pos = _num(to_data.get("positive_ratio", 0))
        delta_pos = _num(delta.get("positive_ratio", 0))
        t0_limit = _num(to_data.get("limit_up_ratio", 0))

        if (
            prev_pos <= 0.33
            and t0_pos >= 0.67
            and delta_pos >= 0.50
            and t0_limit >= 0.50
        ):
            results.append({
                "type": "synchronized_repair",
                "supported_by": [
                    f"positive_ratio: {prev_pos} → {t0_pos} (delta={delta_pos})",
                    f"limit_up_ratio: {_num(from_data.get('limit_up_ratio',0))} → {t0_limit}",
                ],
            })

        # Rule: divergence_deepening
        prev_abv = _num(from_data.get("above_ma5_ratio", 0))
        t0_abv = _num(to_data.get("above_ma5_ratio", 0))
        if prev_pos <= 0.33 and t0_pos <= 0.33 and prev_abv > t0_abv:
            results.append({
                "type": "divergence_deepening",
                "supported_by": [
                    f"positive_ratio stayed low: {prev_pos} → {t0_pos}",
                    f"above_ma5_ratio declining: {prev_abv} → {t0_abv}",
                ],
            })

        if not results:
            return TransitionResult(
                transition_type="no_significant_transition",
                from_date=from_date,
                to_date=to_date,
                supported_by=[f"no clear structural shift detected in breadth metrics"],
            )

        # Pick first match
        best = results[0]
        card_map = {
            "synchronized_repair": "weak_to_strong",
            "divergence_deepening": "leader_divergence",
        }

        return TransitionResult(
            transition_type=best["type"],
            from_date=from_date,
            to_date=to_date,
            supported_by=best["supported_by"],
            suggested_next_card=card_map.get(best["type"], ""),
        )


def _num(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


__all__ = ["TransitionDetector", "TransitionResult"]

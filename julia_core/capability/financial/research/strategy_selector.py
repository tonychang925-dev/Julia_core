"""M3.2.7.6 Strategy Selector — TransitionType → candidate StrategyCards.

Separate from TransitionDetector. Detector answers what happened.
Selector answers what strategies to consider next.

Does NOT execute research — only returns candidate card_ids.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SelectionResult:
    transition_type: str
    card_ids: list[str] = field(default_factory=list)
    primary_card: str = ""
    reason: str = ""


class StrategySelector:
    """Maps detected transitions to relevant StrategyCards.

    Does NOT load or execute cards. Returns card_ids for the Compiler.
    """

    # Transition → candidate StrategyCards
    TRANSITION_MAP: dict[str, list[str]] = {
        "synchronized_repair": ["weak_to_strong"],
        "divergence_deepening": ["leader_divergence"],
        "no_significant_transition": [],
    }

    def select(self, transition_type: str) -> SelectionResult:
        cards = self.TRANSITION_MAP.get(transition_type, [])
        return SelectionResult(
            transition_type=transition_type,
            card_ids=cards,
            primary_card=cards[0] if cards else "",
            reason=f"transition '{transition_type}' maps to {cards}" if cards else f"no strategy cards for transition '{transition_type}'",
        )


__all__ = ["StrategySelector", "SelectionResult"]

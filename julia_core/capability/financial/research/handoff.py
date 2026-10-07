"""M3.2.7.6a Recursive Research Handoff — Transition → ResearchPlan #2.

Orchestrates: RC-001 outcome → Transition → Selector → Card → Compiler → RC-002.
Automatically sets lineage: parent_case_id + trigger_transition.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from julia_core.capability.financial.research.compiler import StrategyResearchCompiler
from julia_core.capability.financial.research.models import ResearchPlan
from julia_core.capability.financial.research.strategy_selector import StrategySelector
from julia_core.capability.financial.research.transition_detector import TransitionDetector, TransitionResult


STRATEGY_CARD_DIR_ENV = "STRATEGY_CARD_DIR"


class StrategyCardDirNotConfigured(RuntimeError):
    """The strategy card directory is not (validly) configured; no fallback location is used (#246)."""


class RecursiveResearchHandoff:
    """Orchestrates: RC-001 evidence → Transition → Strategy → RC-002."""

    def __init__(self, card_dir: str = ""):
        # #246: the strategy-card directory comes ONLY from the explicit argument or STRATEGY_CARD_DIR.
        # No sibling-checkout or Desktop guess. Resolution is lazy so that a research workflow that
        # never reaches the handoff can still be built; the first USE without a valid directory fails closed.
        self._configured = card_dir or os.environ.get(STRATEGY_CARD_DIR_ENV, "")
        self.detector = TransitionDetector()
        self.selector = StrategySelector()
        self.compiler = StrategyResearchCompiler()

    @property
    def card_dir(self) -> Path:
        if not self._configured:
            raise StrategyCardDirNotConfigured(
                f"{STRATEGY_CARD_DIR_ENV} is not set and no card_dir was given: "
                "the strategy card directory must be configured explicitly"
            )
        path = Path(self._configured)
        if not path.is_dir():
            raise StrategyCardDirNotConfigured(
                f"{STRATEGY_CARD_DIR_ENV}/card_dir does not point to a directory: {self._configured}"
            )
        return path

    def create_next_plan(
        self,
        parent_plan: ResearchPlan,
        evidence: dict[str, Any],
        subject: dict,
    ) -> ResearchPlan | None:
        """Attempt to generate RC-002 from RC-001's evidence.

        Returns None if: no transition detected, no card selected,
        or card file not found.
        """
        # Step 1: Detect transition
        transition = self.detector.detect(evidence)
        if transition is None or transition.transition_type in (
            "no_significant_transition", "INSUFFICIENT_EVIDENCE"
        ):
            return None

        # Step 2: Select strategy card
        selection = self.selector.select(transition.transition_type)
        if not selection.primary_card:
            return None

        # Step 3: Load card
        card_path = self.card_dir / f"{selection.primary_card}.json"   # raises when the directory is not configured
        if not card_path.exists():
            return None
        card = json.loads(card_path.read_text(encoding="utf-8"))

        # Step 4: Compile RC-002 with lineage
        next_plan = self.compiler.compile(card, subject)
        next_plan.parent_case_id = parent_plan.research_case_id
        next_plan.trigger_transition = transition.transition_type

        return next_plan


__all__ = ["RecursiveResearchHandoff"]

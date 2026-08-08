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


class RecursiveResearchHandoff:
    """Orchestrates: RC-001 evidence → Transition → Strategy → RC-002."""

    def __init__(self, card_dir: str = ""):
        if card_dir:
            self.card_dir = Path(card_dir)
        else:
            # Resolve from env, then relative to ai_theme_app project root, then fallback
            env_dir = os.environ.get("STRATEGY_CARD_DIR", "")
            if env_dir:
                self.card_dir = Path(env_dir)
            else:
                # Try relative to this file's location (julia_core repo root)
                # handoff.py is at: <workspace>/julia_core/julia_core/capability/financial/research/handoff.py
                # parents[4] = <workspace>/julia_core (repo root), .parent → <workspace>
                julia_root = Path(__file__).resolve().parents[4]
                ai_theme_root = julia_root.parent / "ai_theme_app" / "strategy_knowledge" / "cards"
                if ai_theme_root.exists():
                    self.card_dir = ai_theme_root
                else:
                    self.card_dir = Path("/Users/admin/Desktop/ai_theme_app/strategy_knowledge/cards")
        self.detector = TransitionDetector()
        self.selector = StrategySelector()
        self.compiler = StrategyResearchCompiler()

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
        card_path = self.card_dir / f"{selection.primary_card}.json"
        if not card_path.exists():
            return None
        card = json.loads(card_path.read_text(encoding="utf-8"))

        # Step 4: Compile RC-002 with lineage
        next_plan = self.compiler.compile(card, subject)
        next_plan.parent_case_id = parent_plan.research_case_id
        next_plan.trigger_transition = transition.transition_type

        return next_plan


__all__ = ["RecursiveResearchHandoff"]

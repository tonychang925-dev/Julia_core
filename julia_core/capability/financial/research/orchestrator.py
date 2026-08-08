"""M3.3.0 Cognitive Loop Orchestrator — autonomous recursive research runtime.

Wraps the deterministic research pipeline into a managed loop with:
  - max_rounds / query_budget / stop_reason
  - parent_case_id lineage across rounds
  - Replay mode: inject frozen evidence, skip live CapabilityManager
  - Constraint enforcement: blind judgment immutability, no Workbench, no future data

Zero LLM. Zero human input after initial subject configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from julia_core.capability.financial.research.compiler import StrategyResearchCompiler
from julia_core.capability.financial.research.evidence_normalizer import (
    ResearchEvidenceNormalizer,
    normalize_bundle,
)
from julia_core.capability.financial.research.handoff import RecursiveResearchHandoff
from julia_core.capability.financial.research.hypothesis_evaluator import (
    EvalStatus,
    HypothesisEvaluation,
    HypothesisEvaluator,
)
from julia_core.capability.financial.research.models import (
    EvidenceBundle,
    EvidenceItem,
    ResearchPlan,
    ResearchProbe,
)
from julia_core.capability.financial.research.strategy_selector import StrategySelector
from julia_core.capability.financial.research.transition_detector import (
    TransitionDetector,
    TransitionResult,
)

CST = timezone(timedelta(hours=8))


# ── Config & Results ──────────────────────────────────────────────────────────

@dataclass
class CognitiveLoopConfig:
    """Immutable configuration for one cognitive loop execution."""
    max_rounds: int = 3
    query_budget: int = 20
    as_of: str = ""                       # all evidence gated to this timestamp
    blind_judgment_immutable: bool = True
    initial_card: str = ""                # card to use for Round 0 (blank → selector picks)


@dataclass
class RoundRecord:
    """One round of autonomous research."""
    round_index: int
    research_case_id: str
    parent_case_id: str = ""
    trigger_transition: str = ""
    plan: ResearchPlan | None = None
    evidence_bundle: EvidenceBundle | None = None
    hypothesis_evaluations: dict[str, HypothesisEvaluation] = field(default_factory=dict)
    transition_result: TransitionResult | None = None
    stop_reason: str = ""                 # "" if continuing to next round


@dataclass
class CognitiveLoopResult:
    """Complete output of autonomous research loop."""
    rounds: list[RoundRecord] = field(default_factory=list)
    final_conclusion: dict[str, Any] = field(default_factory=dict)
    evidence_ledger: list[EvidenceItem] = field(default_factory=list)
    stop_reason: str = ""
    total_queries: int = 0
    lineage: list[dict[str, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ── Constraint Violations ────────────────────────────────────────────────────

class ConstraintViolation(Exception):
    """Hard gate violation — loop cannot continue."""


# ── Orchestrator ──────────────────────────────────────────────────────────────

class CognitiveLoopOrchestrator:
    """Manages autonomous recursive research: Round 0 → Transition → Round N → Stop.

    Usage (live):
        orchestrator = CognitiveLoopOrchestrator(
            capability_manager=manager,
            card_dir="/path/to/cards",
            config=CognitiveLoopConfig(max_rounds=2, as_of="2026-07-14"),
        )
        result = await orchestrator.run({
            "subject_key": "9010270",
            "trade_date": "2026-07-14",
            "leader_code": "601969",
        })

    Usage (replay):
        orchestrator = CognitiveLoopOrchestrator(
            capability_manager=manager,
            card_dir="/path/to/cards",
            config=CognitiveLoopConfig(max_rounds=2),
            evidence_injector={
                "RC-001": {"leader_drawdown_from_peak": frozen_item, ...},
                "RC-002": {"leader_key_level": frozen_item, ...},
            },
        )
        result = await orchestrator.run(subject)
    """

    def __init__(
        self,
        capability_manager,                      # CapabilityManager instance
        card_dir: str = "",
        config: CognitiveLoopConfig | None = None,
        evidence_injector: dict[str, dict[str, EvidenceItem]] | None = None,
    ):
        self.capability_manager = capability_manager
        self.config = config or CognitiveLoopConfig()

        self.compiler = StrategyResearchCompiler()
        self.evaluator = HypothesisEvaluator()
        self.normalizer = ResearchEvidenceNormalizer()
        self.detector = TransitionDetector()
        self.selector = StrategySelector()
        self.handoff = RecursiveResearchHandoff(card_dir=card_dir)

        # Replay mode: pre-baked evidence keyed by research_case_id → requirement_id
        self._injector = evidence_injector or {}

        # Internal state
        self._blind_judgment: dict[str, Any] = {}
        self._query_count: int = 0
        self._errors: list[str] = []

    # ── Main entry point ──────────────────────────────────────────────────

    async def run(self, subject: dict) -> CognitiveLoopResult:
        """Execute autonomous research loop. Returns full CognitiveLoopResult."""
        self._validate_subject(subject)
        result = CognitiveLoopResult()

        # ── Round 0: Initial research ─────────────────────────────────────
        round0 = await self._execute_round(
            subject=subject,
            round_index=0,
            parent_plan=None,
            evidence=None,
            trigger_transition="",
        )
        result.rounds.append(round0)
        result.evidence_ledger.extend(
            round0.evidence_bundle.evidence if round0.evidence_bundle else []
        )
        result.lineage.append({
            "parent": round0.parent_case_id or "null",
            "child": round0.research_case_id,
            "trigger": round0.trigger_transition or "initial",
        })
        result.total_queries = self._query_count

        if round0.stop_reason:
            result.stop_reason = round0.stop_reason
            result.final_conclusion = self._build_final_conclusion(result)
            result.errors = self._errors
            return result

        # ── Round N: Recursive research ────────────────────────────────────
        current_plan = round0.plan
        current_evidence = self._evidence_as_dict(round0.evidence_bundle)

        for round_idx in range(1, self.config.max_rounds + 1):
            # Budget check
            if self._query_count >= self.config.query_budget:
                result.stop_reason = "budget_exhausted"
                break

            next_plan = self.handoff.create_next_plan(current_plan, current_evidence, subject)
            if next_plan is None:
                result.stop_reason = "no_transition_or_no_card"
                break

            round_n = await self._execute_round(
                subject=subject,
                round_index=round_idx,
                parent_plan=current_plan,
                evidence=current_evidence,
                trigger_transition=next_plan.trigger_transition,
                pre_compiled_plan=next_plan,
            )
            result.rounds.append(round_n)
            result.evidence_ledger.extend(
                round_n.evidence_bundle.evidence if round_n.evidence_bundle else []
            )
            result.lineage.append({
                "parent": round_n.parent_case_id,
                "child": round_n.research_case_id,
                "trigger": round_n.trigger_transition,
            })
            result.total_queries = self._query_count

            if round_n.stop_reason:
                result.stop_reason = round_n.stop_reason
                break

            current_plan = round_n.plan
            current_evidence = self._evidence_as_dict(round_n.evidence_bundle)

        if not result.stop_reason:
            result.stop_reason = "max_rounds"

        result.final_conclusion = self._build_final_conclusion(result)
        result.errors = self._errors
        return result

    # ── Round execution ───────────────────────────────────────────────────

    async def _execute_round(
        self,
        subject: dict,
        round_index: int,
        parent_plan: ResearchPlan | None,
        evidence: dict[str, Any] | None,
        trigger_transition: str = "",
        pre_compiled_plan: ResearchPlan | None = None,
    ) -> RoundRecord:
        """Execute one research round: compile → execute probes → normalize → evaluate → detect transition."""

        # 1. Compile (or use pre-compiled from handoff)
        if pre_compiled_plan is not None:
            plan = pre_compiled_plan
        else:
            card = self._load_initial_card(subject)
            plan = self.compiler.compile(card, subject)

        # 2. Execute probes → EvidenceBundle
        bundle = await self._execute_probes(plan)

        # 3. Evaluate hypotheses
        evaluations: dict[str, HypothesisEvaluation] = {}
        evidence_dict = self._evidence_as_dict(bundle)
        for hyp in plan.candidate_hypotheses:
            ev = self.evaluator.evaluate(hyp, evidence_dict)
            evaluations[hyp["canonical_state"]] = ev

        # 4. Detect transition
        transition = self.detector.detect(evidence_dict)

        # 5. Determine stop reason
        stop_reason = ""
        if transition is None or transition.transition_type in (
            "no_significant_transition", "INSUFFICIENT_EVIDENCE"
        ):
            stop_reason = "no_transition"
        elif round_index >= self.config.max_rounds:
            stop_reason = "max_rounds"
        elif self._all_hypotheses_resolved(evaluations):
            stop_reason = "all_resolved"

        return RoundRecord(
            round_index=round_index,
            research_case_id=plan.research_case_id,
            parent_case_id=plan.parent_case_id or (parent_plan.research_case_id if parent_plan else ""),
            trigger_transition=trigger_transition,
            plan=plan,
            evidence_bundle=bundle,
            hypothesis_evaluations=evaluations,
            transition_result=transition,
            stop_reason=stop_reason,
        )

    # ── Probe execution ───────────────────────────────────────────────────

    async def _execute_probes(self, plan: ResearchPlan) -> EvidenceBundle:
        """Execute all probes via CapabilityManager (or injector in replay mode)."""
        injector_for_case = self._injector.get(plan.research_case_id, {})

        items: list[EvidenceItem] = []
        for probe in plan.probes:
            # Replay mode: use frozen evidence
            if injector_for_case and probe.requirement_id in injector_for_case:
                items.append(injector_for_case[probe.requirement_id])
                continue

            # Live mode: execute via CapabilityManager
            self._query_count += 1
            if self._query_count > self.config.query_budget:
                # Budget exceeded mid-round — record insufficient for remaining probes
                items.append(EvidenceItem(
                    requirement_id=probe.requirement_id,
                    probe_id=probe.probe_id,
                    status="insufficient_evidence",
                    missing_policy=probe.missing_policy,
                ))
                continue

            try:
                result = await self.capability_manager.execute(probe.request)
                item = self.normalizer.normalize(probe, result)
            except Exception as exc:
                self._errors.append(f"{probe.requirement_id}: {exc}")
                item = EvidenceItem(
                    requirement_id=probe.requirement_id,
                    probe_id=probe.probe_id,
                    status="error",
                    missing_policy=probe.missing_policy,
                )
            items.append(item)

        bundle = EvidenceBundle(
            research_case_id=plan.research_case_id,
            subject_key=plan.subject_key,
            as_of=plan.trade_date,
            evidence=items,
            evidence_count=len(items),
            success_count=sum(1 for i in items if i.status == "success"),
            unavailable_count=sum(1 for i in items if i.status == "unavailable"),
            error_count=sum(1 for i in items if i.status == "error"),
        )
        return bundle

    # ── Constraint enforcement ────────────────────────────────────────────

    def _validate_subject(self, subject: dict):
        """Hard-gate: subject must have required fields."""
        for req in ("subject_key", "trade_date"):
            if not subject.get(req):
                raise ConstraintViolation(f"subject.{req} is required")

        if self.config.as_of and subject["trade_date"] != self.config.as_of:
            raise ConstraintViolation(
                f"subject.trade_date={subject['trade_date']} != config.as_of={self.config.as_of}"
            )

    def _load_initial_card(self, subject: dict) -> dict:
        """Load the initial StrategyCard for Round 0."""
        import json
        from pathlib import Path

        card_dir = self.handoff.card_dir
        card_name = self.config.initial_card or "leader_divergence"
        card_path = card_dir / f"{card_name}.json"

        if not card_path.exists():
            raise ConstraintViolation(f"Initial card not found: {card_path}")

        return json.loads(card_path.read_text(encoding="utf-8"))

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _evidence_as_dict(bundle: EvidenceBundle | None) -> dict[str, EvidenceItem]:
        """Convert EvidenceBundle to {requirement_id: EvidenceItem} dict."""
        if bundle is None:
            return {}
        return {item.requirement_id: item for item in bundle.evidence}

    @staticmethod
    def _all_hypotheses_resolved(evaluations: dict[str, HypothesisEvaluation]) -> bool:
        """True when all hypotheses are either decisive-CONTRADICTED or definitive."""
        if not evaluations:
            return False
        for ev in evaluations.values():
            if ev.status not in (EvalStatus.CONTRADICTED, EvalStatus.SUPPORTED):
                return False
            if ev.status == EvalStatus.CONTRADICTED and not ev.decisive:
                return False
        return True

    @staticmethod
    def _build_final_conclusion(result: CognitiveLoopResult) -> dict:
        """Build final conclusion from all rounds."""
        if not result.rounds:
            return {"state": "no_research_executed"}

        last_round = result.rounds[-1]
        last_evals = last_round.hypothesis_evaluations

        # Find supported or partial states
        supported = [k for k, v in last_evals.items() if v.status == "SUPPORTED"]
        partial = [k for k, v in last_evals.items() if v.status == "PARTIAL"]
        contradicted = [k for k, v in last_evals.items() if v.status == "CONTRADICTED"]

        if supported:
            primary_state = supported[0]
            state_type = "supported"
        elif partial:
            primary_state = partial[0]
            state_type = "partial"
        else:
            primary_state = "unknown"
            state_type = "inconclusive"

        return {
            "primary_state": primary_state,
            "state_type": state_type,
            "rounds_executed": len(result.rounds),
            "stop_reason": result.stop_reason,
            "total_queries": result.total_queries,
            "supported": supported,
            "partial": partial,
            "contradicted": contradicted,
            "lineage": result.lineage,
        }


__all__ = [
    "CognitiveLoopConfig",
    "CognitiveLoopResult",
    "CognitiveLoopOrchestrator",
    "RoundRecord",
    "ConstraintViolation",
]

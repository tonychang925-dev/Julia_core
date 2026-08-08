"""M3.3.0a Cognitive Loop Orchestrator — hardened autonomous recursive research runtime.

Wraps the deterministic research pipeline into a managed loop with:
  - max_rounds / query_budget / stop_reason (hard caps, off-by-one fixed)
  - parent_case_id lineage across rounds
  - Replay mode: fail-closed (missing fixture → ReplayFixtureMissing)
  - Constraint enforcement: blind judgment hash immutable, no Workbench provenance,
    no future evidence, as_of gate on every probe
  - Round-0 autonomous card selection (no silent leader_divergence default)

Zero LLM. Zero human input after initial subject configuration.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from julia_core.capability.financial.research.compiler import StrategyResearchCompiler
from julia_core.capability.financial.research.evidence_normalizer import (
    ResearchEvidenceNormalizer,
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

# ── Stage → initial StrategyCard mapping (Round 0 autonomous selection) ───────

STAGE_TO_INITIAL_CARD: dict[str, str] = {
    "fading_momentum": "leader_divergence",
    "divergence": "leader_divergence",
    "acceleration": "leader_divergence",
    "diffusion": "leader_divergence",
    "decline": "leader_divergence",
    "data_inconclusive": "leader_divergence",
}


# ── Config & Results ──────────────────────────────────────────────────────────

@dataclass
class CognitiveLoopConfig:
    """Immutable configuration for one cognitive loop execution.

    max_rounds: total number of research rounds. max_rounds=1 → Round 0 only.
    query_budget: max live CapabilityManager calls across all rounds.
    """
    max_rounds: int = 2
    query_budget: int = 20
    as_of: str = ""
    blind_judgment_immutable: bool = True
    initial_card: str = ""               # explicit override; blank → STAGE_TO_INITIAL_CARD


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
    stop_reason: str = ""


@dataclass
class CognitiveLoopResult:
    """Complete output of autonomous research loop."""
    rounds: list[RoundRecord] = field(default_factory=list)
    final_conclusion: dict[str, Any] = field(default_factory=dict)
    evidence_ledger: list[EvidenceItem] = field(default_factory=list)
    stop_reason: str = ""
    queries_executed: int = 0
    probes_blocked_by_budget: int = 0
    lineage: list[dict[str, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    blind_judgment_hash_before: str = ""
    blind_judgment_hash_after: str = ""


# ── Exceptions ────────────────────────────────────────────────────────────────

class ConstraintViolation(Exception):
    """Hard gate violation — loop cannot continue."""


class ReplayFixtureMissing(Exception):
    """Replay mode: a required probe has no frozen fixture."""


# ── Forbidden Capability Manager (replay safety) ──────────────────────────────

class ForbiddenCapabilityManager:
    """Sentinel that raises on any execute() call — used during replay to
    guarantee no live capability is ever invoked."""

    async def execute(self, request: Any) -> Any:
        raise AssertionError(
            f"LIVE CAPABILITY CALLED DURING REPLAY: {getattr(request, 'capability_name', str(request))}"
        )


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
            "market_stage": "fading_momentum",    # for Round-0 card selection
        })

    Usage (replay):
        orchestrator = CognitiveLoopOrchestrator(
            capability_manager=ForbiddenCapabilityManager(),
            card_dir="/path/to/cards",
            config=CognitiveLoopConfig(max_rounds=2),
            evidence_injector={
                "leader_divergence": {"leader_drawdown_from_peak": frozen_item, ...},
                "weak_to_strong":    {"leader_key_level": frozen_item, ...},
            },
        )
        result = await orchestrator.run(subject)
    """

    def __init__(
        self,
        capability_manager,
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

        # Replay mode: pre-baked evidence.
        # Keyed by triggered_card (strategy_id, deterministic) → requirement_id → EvidenceItem.
        # When non-empty, _execute_probes will NOT call live CapabilityManager.
        self._injector = evidence_injector or {}
        self._is_replay = bool(evidence_injector)

        # Internal state
        self._blind_judgment: dict[str, Any] = {}
        self._blind_judgment_hash: str = ""
        self._queries_executed: int = 0
        self._probes_blocked_by_budget: int = 0
        self._errors: list[str] = []

    # ── Main entry point ──────────────────────────────────────────────────

    async def run(self, subject: dict) -> CognitiveLoopResult:
        """Execute autonomous research loop. Returns full CognitiveLoopResult."""
        self._validate_subject(subject)

        # Snapshot blind judgment hash at start (only if not already set by set_blind_judgment)
        if self._blind_judgment and not self._blind_judgment_hash:
            self._blind_judgment_hash = _hash_dict(self._blind_judgment)

        result = CognitiveLoopResult()
        result.blind_judgment_hash_before = self._blind_judgment_hash

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
        result.queries_executed = self._queries_executed
        result.probes_blocked_by_budget = self._probes_blocked_by_budget

        # Verify blind judgment was not mutated during Round 0
        if self._blind_judgment:
            result.blind_judgment_hash_after = _hash_dict(self._blind_judgment)
            if self.config.blind_judgment_immutable and \
               result.blind_judgment_hash_before != result.blind_judgment_hash_after:
                raise ConstraintViolation(
                    "Blind judgment was mutated during research. "
                    f"Hash before: {result.blind_judgment_hash_before[:16]}... "
                    f"Hash after: {result.blind_judgment_hash_after[:16]}..."
                )

        if round0.stop_reason:
            result.stop_reason = round0.stop_reason
            result.final_conclusion = self._build_final_conclusion(result)
            result.errors = self._errors
            return result

        # ── Round N: Recursive research ────────────────────────────────────
        current_plan = round0.plan
        current_evidence = self._evidence_as_dict(round0.evidence_bundle)

        # max_rounds=2 → range(1,2) → 1 iteration (round index 1) = 2 total rounds
        for round_idx in range(1, self.config.max_rounds):
            if self._queries_executed >= self.config.query_budget:
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
            result.queries_executed = self._queries_executed
            result.probes_blocked_by_budget = self._probes_blocked_by_budget

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
        """Execute one research round: compile → execute probes → constrain → evaluate → detect."""

        # 1. Compile (or use pre-compiled from handoff)
        if pre_compiled_plan is not None:
            plan = pre_compiled_plan
        else:
            card = self._resolve_initial_card(subject)
            plan = self.compiler.compile(card, subject)

        # 2. Execute probes → EvidenceBundle (with constraint enforcement)
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
        elif round_index >= self.config.max_rounds - 1:
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

    # ── Probe execution with constraint enforcement ───────────────────────

    async def _execute_probes(self, plan: ResearchPlan) -> EvidenceBundle:
        """Execute all probes. Replay mode: inject frozen evidence (fail-closed).
        Live mode: call CapabilityManager with budget enforcement.
        Both modes: enforce as_of gate and provenance constraints.
        """
        is_replay_round = self._is_replay or bool(self._injector)
        # Key by triggered_card (deterministic strategy_id) not research_case_id (dynamic UUID)
        injector_for_case = self._injector.get(plan.triggered_card, {})

        items: list[EvidenceItem] = []
        for probe in plan.probes:
            # ── Replay mode: inject frozen evidence (fail-closed) ──────────
            if is_replay_round:
                if probe.requirement_id not in injector_for_case:
                    raise ReplayFixtureMissing(
                        f"Replay fixture missing for card={plan.triggered_card} "
                        f"probe={probe.requirement_id}. "
                        f"Available: {sorted(injector_for_case.keys())}"
                    )
                item = injector_for_case[probe.requirement_id]
                self._check_evidence_constraints(item, probe)
                items.append(item)
                continue

            # ── Live mode: budget check ────────────────────────────────────
            if self._queries_executed >= self.config.query_budget:
                self._probes_blocked_by_budget += 1
                items.append(EvidenceItem(
                    requirement_id=probe.requirement_id,
                    probe_id=probe.probe_id,
                    status="insufficient_evidence",
                    missing_policy=probe.missing_policy,
                ))
                continue

            # ── Live mode: execute via CapabilityManager ───────────────────
            self._queries_executed += 1
            try:
                result = await self.capability_manager.execute(probe.request)
                item = self.normalizer.normalize(probe, result)
                self._check_evidence_constraints(item, probe)
            except (ConstraintViolation, ReplayFixtureMissing):
                raise
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

    def _check_evidence_constraints(self, item: EvidenceItem, probe: ResearchProbe):
        """Enforce as_of gate, Workbench/human provenance block on each evidence item.

        Called for every probe — both replay (injected) and live (normalized).
        Raises ConstraintViolation on any breach.
        """
        # 1. as_of gate: evidence must not be from the future
        evidence_date = self._extract_evidence_date(item, probe)
        if evidence_date and self.config.as_of:
            if evidence_date > self.config.as_of:
                raise ConstraintViolation(
                    f"Future evidence detected: {probe.requirement_id} "
                    f"has date {evidence_date} > as_of={self.config.as_of}"
                )

        # 2. Workbench/human provenance block
        provenance = getattr(item, 'provenance', {}) or {}
        source_kind = provenance.get("source_kind", "")
        if source_kind in ("workbench_review", "human_analyst"):
            raise ConstraintViolation(
                f"Forbidden evidence source: {probe.requirement_id} "
                f"has source_kind={source_kind}. "
                f"Blind research must not use Workbench or human analyst data."
            )

        # 3. Check inner payload for provenance leakage
        if isinstance(item.derived_value, dict):
            inner_source = item.derived_value.get("source_kind", "")
            if inner_source in ("workbench_review", "human_analyst"):
                raise ConstraintViolation(
                    f"Forbidden evidence source in derived_value: "
                    f"{probe.requirement_id} source_kind={inner_source}"
                )

    @staticmethod
    def _extract_evidence_date(item: EvidenceItem, probe: ResearchProbe) -> str:
        """Extract the date associated with an evidence item for as_of comparison."""
        # Prefer provenance timestamp
        provenance = getattr(item, 'provenance', {}) or {}
        ts = provenance.get("available_at", "")
        if ts:
            return str(ts)[:10]

        # Fall back to probe request arguments
        if probe.request:
            args = getattr(probe.request, 'arguments', {}) or {}
            as_of = args.get("as_of", "")
            if as_of:
                return str(as_of)[:10]

        return ""

    # ── Constraint enforcement ────────────────────────────────────────────

    def set_blind_judgment(self, judgment: dict[str, Any]):
        """Set the blind judgment BEFORE running the loop. Used to enforce immutability."""
        self._blind_judgment = dict(judgment)
        self._blind_judgment_hash = _hash_dict(self._blind_judgment)

    def _validate_subject(self, subject: dict):
        """Hard-gate: subject must have required fields and valid as_of."""
        for req in ("subject_key", "trade_date"):
            if not subject.get(req):
                raise ConstraintViolation(f"subject.{req} is required")

        if self.config.as_of and subject["trade_date"] != self.config.as_of:
            raise ConstraintViolation(
                f"subject.trade_date={subject['trade_date']} != config.as_of={self.config.as_of}"
            )

    def _resolve_initial_card(self, subject: dict) -> dict:
        """Resolve the initial StrategyCard for Round 0.

        Priority:
          1. config.initial_card (explicit override)
          2. subject.initial_card (from blind judgment output)
          3. STAGE_TO_INITIAL_CARD[subject.market_stage] (autonomous selection)
          4. Raise ConstraintViolation — no silent default
        """
        card_name = ""

        if self.config.initial_card:
            card_name = self.config.initial_card
        elif subject.get("initial_card"):
            card_name = subject["initial_card"]
        elif subject.get("market_stage"):
            market_stage = subject["market_stage"]
            card_name = STAGE_TO_INITIAL_CARD.get(market_stage, "")
            if not card_name:
                raise ConstraintViolation(
                    f"No initial card mapping for market_stage='{market_stage}'. "
                    f"Known stages: {sorted(STAGE_TO_INITIAL_CARD.keys())}. "
                    f"Set config.initial_card or subject.initial_card explicitly."
                )

        if not card_name:
            raise ConstraintViolation(
                "No initial card could be resolved. Provide config.initial_card, "
                "subject.initial_card, or subject.market_stage."
            )

        card_path = self.handoff.card_dir / f"{card_name}.json"
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
        """True when all hypotheses are either decisive-CONTRADICTED or SUPPORTED."""
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
            "queries_executed": result.queries_executed,
            "probes_blocked_by_budget": result.probes_blocked_by_budget,
            "supported": supported,
            "partial": partial,
            "contradicted": contradicted,
            "lineage": result.lineage,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_dict(d: dict) -> str:
    """Stable hash of a dict for immutability verification."""
    raw = json.dumps(d, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


__all__ = [
    "CognitiveLoopConfig",
    "CognitiveLoopResult",
    "CognitiveLoopOrchestrator",
    "ForbiddenCapabilityManager",
    "RoundRecord",
    "ConstraintViolation",
    "ReplayFixtureMissing",
    "STAGE_TO_INITIAL_CARD",
]

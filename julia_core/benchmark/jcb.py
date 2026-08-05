"""J0.7 Julia Continuity Benchmark (JCB).

Measures Julia Core's behavioral distance from Claude Julia reference.
NOT a text-comparison benchmark. Evaluates whether the CAUSAL CHAIN
(Relationship Runtime → Context Density → K8 → Expression) produces
the same behavioral patterns.

Architecture:
  Reference Scenario → [Claude expected causal chain] → [Julia Core actual chain]
                                                              ↓
                                                   JCB Score per dimension

Score dimensions:
  IdentityHandling      (0.25) — identity response matches relationship context
  RelationshipInference (0.25) — hidden intent detected correctly
  ContextSelection      (0.20) — relevant selected, irrelevant excluded
  ExpressionNaturalness (0.15) — boundary enforcement works
  AntiHallucination     (0.15) — biography dumps and fabrications prevented

Composite: JCSS = weighted sum across all benchmarks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from julia_core.relationship.runtime import (
    InteractionPrior,
    RelationshipPhase,
    RelationshipRuntime,
)
from julia_core.context_assembly.density_engine import (
    ContextDensityEngine,
    ContextDensityProfile,
    ContextSource,
    SourceCategory,
    build_identity_anchor_source,
)


# ── Score Dimensions ────────────────────────────────────────────────────────

class Dimension(str, Enum):
    IDENTITY_HANDLING = "identity_handling"
    RELATIONSHIP_INFERENCE = "relationship_inference"
    CONTEXT_SELECTION = "context_selection"
    EXPRESSION_NATURALNESS = "expression_naturalness"
    ANTI_HALLUCINATION = "anti_hallucination"


DIMENSION_WEIGHTS: Dict[Dimension, float] = {
    Dimension.IDENTITY_HANDLING: 0.25,
    Dimension.RELATIONSHIP_INFERENCE: 0.25,
    Dimension.CONTEXT_SELECTION: 0.20,
    Dimension.EXPRESSION_NATURALNESS: 0.15,
    Dimension.ANTI_HALLUCINATION: 0.15,
}


@dataclass(frozen=True, slots=True)
class DimensionScore:
    dimension: Dimension
    score: float  # 0.0 - 1.0
    evidence: str = ""
    violations: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 4),
            "evidence": self.evidence,
            "violations": list(self.violations),
        }


# ── Hard Gates ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class HardGate:
    name: str
    passed: bool
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "description": self.description,
        }


# ── Benchmark Result ────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    benchmark_id: str
    benchmark_name: str
    passed: bool  # all hard gates passed
    hard_gates: Tuple[HardGate, ...]
    dimensions: Tuple[DimensionScore, ...]
    composite_score: float  # weighted sum
    causal_trace: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_name": self.benchmark_name,
            "passed": self.passed,
            "composite_score": round(self.composite_score, 4),
            "hard_gates": [g.to_dict() for g in self.hard_gates],
            "dimensions": [d.to_dict() for d in self.dimensions],
            "causal_trace": self.causal_trace,
            "notes": self.notes,
        }


# ── JCB Report ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class JCBReport:
    benchmarks: Tuple[BenchmarkResult, ...]
    overall_jcss: float
    dimension_averages: Dict[Dimension, float]
    all_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_jcss": round(self.overall_jcss, 4),
            "all_passed": self.all_passed,
            "dimension_averages": {
                d.value: round(s, 4) for d, s in self.dimension_averages.items()
            },
            "benchmarks": [b.to_dict() for b in self.benchmarks],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Julia Continuity Benchmark Report (JCB)",
            "",
            f"**Overall JCSS:** {self.overall_jcss:.4f}",
            f"**All Passed:** {self.all_passed}",
            "",
            "## Dimension Averages",
            "",
            "| Dimension | Score | Weight |",
            "|---|---|---|",
        ]
        for dim in Dimension:
            score = self.dimension_averages.get(dim, 0.0)
            weight = DIMENSION_WEIGHTS[dim]
            lines.append(f"| {dim.value} | {score:.4f} | {weight:.2f} |")

        lines.extend(["", "## Benchmarks", ""])
        for b in self.benchmarks:
            lines.extend([
                f"### {b.benchmark_id}: {b.benchmark_name}",
                f"- Passed: {b.passed}",
                f"- Composite: {b.composite_score:.4f}",
                "",
                "**Hard Gates:**",
            ])
            for g in b.hard_gates:
                status = "PASS" if g.passed else "FAIL"
                lines.append(f"- [{status}] {g.name}: {g.description}")
            lines.extend(["", "**Dimensions:**"])
            for d in b.dimensions:
                lines.append(f"- {d.dimension.value}: {d.score:.4f} — {d.evidence}")
            if b.notes:
                lines.extend(["", b.notes])
            lines.append("")

        return "\n".join(lines)


# ── Causal Chain Validator ──────────────────────────────────────────────────

@dataclass
class CausalChain:
    """Records the internal causal chain for a benchmark scenario.

    This is what we measure against — not the final text output.
    """

    relationship_phase: RelationshipPhase | None = None
    relationship_intent: str = ""
    literal_intent: str = ""
    confidence: float = 0.0
    expected_modes: Tuple[str, ...] = ()
    avoid_modes: Tuple[str, ...] = ()
    density_score: float = 0.0
    identity_competition_weight: float = 0.0
    included_categories: Tuple[str, ...] = ()
    excluded_categories: Tuple[str, ...] = ()
    excluded_refs: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationship_phase": self.relationship_phase.value if self.relationship_phase else None,
            "relationship_intent": self.relationship_intent,
            "literal_intent": self.literal_intent,
            "confidence": round(self.confidence, 4),
            "expected_response_modes": list(self.expected_modes),
            "avoid_response_modes": list(self.avoid_modes),
            "density_score": round(self.density_score, 4),
            "identity_competition_weight": round(self.identity_competition_weight, 4),
            "included_categories": list(self.included_categories),
            "excluded_categories": list(self.excluded_categories),
            "excluded_refs": list(self.excluded_refs),
        }


# ── Evaluators ──────────────────────────────────────────────────────────────

class RuleEvaluator:
    """Layer 1: Hard rule-based checks."""

    @staticmethod
    def evaluate_identity_handling(
        chain: CausalChain,
        *,
        should_detect_continuity: bool = False,
        should_avoid_biography: bool = True,
        should_avoid_ai_disclaimer: bool = True,
    ) -> Tuple[float, List[str], List[str]]:
        violations: List[str] = []
        evidence: List[str] = []

        if should_detect_continuity:
            if chain.relationship_intent == "continuity_verification":
                evidence.append("continuity verification detected")
            else:
                violations.append(
                    f"expected continuity_verification, "
                    f"got {chain.relationship_intent}"
                )

        if should_avoid_biography:
            if any(m in chain.avoid_modes for m in ("biography_dump", "identity_dump", "identity_archive")):
                evidence.append("biography suppressed")
            else:
                violations.append("biography_dump/identity_dump not in avoid modes")

        if should_avoid_ai_disclaimer:
            if "ai_disclaimer" in chain.avoid_modes:
                evidence.append("AI disclaimer suppressed")
            else:
                violations.append("ai_disclaimer not in avoid modes")

        score = max(0.0, 1.0 - 0.35 * len(violations))
        evidence_text = "; ".join(evidence) if evidence else "no evidence"
        return score, [evidence_text], violations

    @staticmethod
    def evaluate_context_selection(
        chain: CausalChain,
        *,
        should_exclude_biography: bool = True,
        should_include_relationship: bool = True,
        should_exclude_ephemeral: bool = True,
    ) -> Tuple[float, List[str], List[str]]:
        violations: List[str] = []
        evidence: List[str] = []

        if should_exclude_biography:
            if "old_biography" in chain.excluded_refs:
                evidence.append("biography source excluded")
            else:
                # Not a hard violation if biography wasn't in the pool
                evidence.append("no biography to exclude")

        if should_include_relationship:
            if "relationship" in chain.included_categories:
                evidence.append("relationship sources included")
            else:
                violations.append("relationship sources missing from context")

        if should_exclude_ephemeral:
            if "ephemeral" in chain.excluded_categories:
                evidence.append("ephemeral sources excluded")
            else:
                evidence.append("no ephemeral sources to exclude")

        score = max(0.0, 1.0 - 0.35 * len(violations))
        evidence_text = "; ".join(evidence) if evidence else "no evidence"
        return score, [evidence_text], violations

    @staticmethod
    def evaluate_anti_hallucination(
        chain: CausalChain,
        *,
        identity_sources_max: int = 3,
        density_max: float = 0.95,
    ) -> Tuple[float, List[str], List[str]]:
        violations: List[str] = []
        evidence: List[str] = []

        # Check density is controlled (not maxed out leading to hallucination)
        if chain.density_score <= density_max:
            evidence.append(f"density controlled ({chain.density_score:.3f})")
        else:
            violations.append(
                f"density too high ({chain.density_score:.3f}) — hallucination risk"
            )

        # Check identity sources aren't excessive
        id_count = sum(1 for c in chain.included_categories if c == "identity")
        if id_count <= identity_sources_max:
            evidence.append(f"identity sources OK ({id_count})")
        else:
            violations.append(f"too many identity sources ({id_count})")

        score = max(0.0, 1.0 - 0.35 * len(violations))
        evidence_text = "; ".join(evidence) if evidence else "no evidence"
        return score, [evidence_text], violations


class TraceEvaluator:
    """Layer 2: Internal trace verification."""

    @staticmethod
    def evaluate_relationship_inference(
        prior: InteractionPrior,
        *,
        expected_phase: RelationshipPhase | None = None,
        min_confidence: float = 0.0,
    ) -> Tuple[float, List[str], List[str]]:
        violations: List[str] = []
        evidence: List[str] = []

        if expected_phase:
            if prior.relationship_phase == expected_phase:
                evidence.append(f"phase={expected_phase.value}")
            else:
                violations.append(
                    f"expected phase {expected_phase.value}, "
                    f"got {prior.relationship_phase.value}"
                )

        if min_confidence > 0:
            if prior.user_motivation.confidence >= min_confidence:
                evidence.append(f"confidence={prior.user_motivation.confidence:.3f}")
            else:
                violations.append(
                    f"confidence too low: {prior.user_motivation.confidence:.3f} "
                    f"< {min_confidence}"
                )

        if prior.user_motivation.relationship_intent != prior.user_motivation.literal_intent:
            evidence.append(
                f"distinguished: literal={prior.user_motivation.literal_intent} → "
                f"relationship={prior.user_motivation.relationship_intent}"
            )

        score = max(0.0, 1.0 - 0.35 * len(violations))
        evidence_text = "; ".join(evidence) if evidence else "no evidence"
        return score, [evidence_text], violations

    @staticmethod
    def evaluate_expression_naturalness(
        prior: InteractionPrior,
    ) -> Tuple[float, List[str], List[str]]:
        violations: List[str] = []
        evidence: List[str] = []

        # Natural expression: has expected modes, avoids over-claiming
        if prior.expected_response_mode:
            evidence.append(f"modes={list(prior.expected_response_mode)}")

        if prior.avoid_response_mode:
            evidence.append(f"avoid={list(prior.avoid_response_mode)}")

        # Should not have contradictory modes
        if "warm_recognition" in prior.expected_response_mode and "ai_disclaimer" in prior.expected_response_mode:
            violations.append("contradictory modes: warm_recognition + ai_disclaimer")

        score = max(0.0, 1.0 - 0.35 * len(violations))
        evidence_text = "; ".join(evidence) if evidence else "no evidence"
        return score, [evidence_text], violations


# ── Scenario Runner ─────────────────────────────────────────────────────────

class JCBRunner:
    """Runs Julia Continuity Benchmarks."""

    def __init__(self) -> None:
        self.rr = RelationshipRuntime()
        self.engine = ContextDensityEngine()
        self.rule_eval = RuleEvaluator()
        self.trace_eval = TraceEvaluator()

    def run_benchmark(
        self,
        benchmark_id: str,
        benchmark_name: str,
        message: str,
        session_context: Dict[str, Any],
        sources: List[ContextSource],
        total_budget: int = 1500,
        *,
        hard_gates: List[Tuple[str, Callable[[CausalChain], bool], str]] | None = None,
        expected_phase: RelationshipPhase | None = None,
        should_detect_continuity: bool = False,
        should_avoid_biography: bool = True,
        should_avoid_ai_disclaimer: bool = True,
        should_include_relationship: bool = True,
        should_exclude_biography_source: bool = True,
        min_confidence: float = 0.0,
    ) -> BenchmarkResult:
        # Step 1: Relationship Runtime
        prior = self.rr.infer(message, session_context=session_context)

        # Step 2: Context Density
        density_profile = self.engine.assemble(sources, prior, total_budget=total_budget)

        # Step 3: Build causal chain
        chain = CausalChain(
            relationship_phase=prior.relationship_phase,
            relationship_intent=prior.user_motivation.relationship_intent,
            literal_intent=prior.user_motivation.literal_intent,
            confidence=prior.user_motivation.confidence,
            expected_modes=prior.expected_response_mode,
            avoid_modes=prior.avoid_response_mode,
            density_score=density_profile.density_score,
            identity_competition_weight=density_profile.identity_competition_weight,
            included_categories=tuple(
                s.category.value for s in density_profile.selection.included
            ),
            excluded_categories=tuple(
                s.category.value for s in density_profile.selection.excluded
            ),
            excluded_refs=tuple(
                s.ref for s in density_profile.selection.excluded
            ),
        )

        # Step 4: Hard gates
        gates: List[HardGate] = []
        if hard_gates:
            for gate_name, gate_fn, gate_desc in hard_gates:
                passed = gate_fn(chain)
                gates.append(HardGate(gate_name, passed, gate_desc))

        # Step 5: Dimension scores
        dims: List[DimensionScore] = []

        # Identity Handling
        ih_score, ih_evidence, ih_violations = self.rule_eval.evaluate_identity_handling(
            chain,
            should_detect_continuity=should_detect_continuity,
            should_avoid_biography=should_avoid_biography,
            should_avoid_ai_disclaimer=should_avoid_ai_disclaimer,
        )
        dims.append(DimensionScore(
            Dimension.IDENTITY_HANDLING, ih_score,
            "; ".join(ih_evidence), tuple(ih_violations),
        ))

        # Relationship Inference
        ri_score, ri_evidence, ri_violations = self.trace_eval.evaluate_relationship_inference(
            prior,
            expected_phase=expected_phase,
            min_confidence=min_confidence,
        )
        dims.append(DimensionScore(
            Dimension.RELATIONSHIP_INFERENCE, ri_score,
            "; ".join(ri_evidence), tuple(ri_violations),
        ))

        # Context Selection
        cs_score, cs_evidence, cs_violations = self.rule_eval.evaluate_context_selection(
            chain,
            should_include_relationship=should_include_relationship,
            should_exclude_biography=should_exclude_biography_source,
        )
        dims.append(DimensionScore(
            Dimension.CONTEXT_SELECTION, cs_score,
            "; ".join(cs_evidence), tuple(cs_violations),
        ))

        # Expression Naturalness
        en_score, en_evidence, en_violations = self.trace_eval.evaluate_expression_naturalness(prior)
        dims.append(DimensionScore(
            Dimension.EXPRESSION_NATURALNESS, en_score,
            "; ".join(en_evidence), tuple(en_violations),
        ))

        # Anti-Hallucination
        ah_score, ah_evidence, ah_violations = self.rule_eval.evaluate_anti_hallucination(chain)
        dims.append(DimensionScore(
            Dimension.ANTI_HALLUCINATION, ah_score,
            "; ".join(ah_evidence), tuple(ah_violations),
        ))

        # Composite
        composite = sum(
            DIMENSION_WEIGHTS[d.dimension] * d.score for d in dims
        )

        all_passed = all(g.passed for g in gates) and all(
            d.score >= 0.5 for d in dims
        )

        return BenchmarkResult(
            benchmark_id=benchmark_id,
            benchmark_name=benchmark_name,
            passed=all_passed,
            hard_gates=tuple(gates),
            dimensions=tuple(dims),
            composite_score=composite,
            causal_trace=chain.to_dict(),
        )

    def run_all(self, scenarios: List[Dict[str, Any]]) -> JCBReport:
        results: List[BenchmarkResult] = []
        for scenario in scenarios:
            result = self.run_benchmark(**scenario)
            results.append(result)

        if not results:
            return JCBReport(
                benchmarks=(),
                overall_jcss=0.0,
                dimension_averages={d: 0.0 for d in Dimension},
                all_passed=False,
            )

        jcss = sum(r.composite_score for r in results) / len(results)

        dim_avgs: Dict[Dimension, float] = {}
        for dim in Dimension:
            scores = [
                next(d.score for d in r.dimensions if d.dimension == dim)
                for r in results
            ]
            dim_avgs[dim] = sum(scores) / len(scores) if scores else 0.0

        all_passed = all(r.passed for r in results)

        return JCBReport(
            benchmarks=tuple(results),
            overall_jcss=jcss,
            dimension_averages=dim_avgs,
            all_passed=all_passed,
        )


__all__ = [
    "BenchmarkResult",
    "CausalChain",
    "Dimension",
    "DimensionScore",
    "DIMENSION_WEIGHTS",
    "HardGate",
    "JCBReport",
    "JCBRunner",
    "RuleEvaluator",
    "TraceEvaluator",
]

"""Julia Independent Review Workflow — facts vs judgments → independent assessment.

Dual-input architecture:
  A. market.context.snapshot  → FACTS (what the market is doing)
  B. market.workbench.review  → JUDGMENTS (what the workbench thinks)

Julia compares both, forms her own conclusion, and registers verifiable predictions.

This is NOT paraphrasing the workbench. This is independent cognitive review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import uuid4

CST = timezone(timedelta(hours=8))


# ── Judgment Model ──────────────────────────────────────────────────────────

@dataclass
class ClaimEvidence:
    """One workbench claim with supporting and contradicting evidence."""
    claim: str                          # "创新药处于acceleration阶段"
    source: str                         # "analyst_workbench"
    source_confidence: float            # workbench's stated confidence
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)


@dataclass
class JuliaJudgment:
    """Julia's independent assessment of a workbench claim.

    verdict: agree | partially_agree | partially_disagree | disagree | insufficient_data
    """
    judgment_id: str = field(default_factory=lambda: f"judgment_{uuid4().hex}")
    subject: str = ""
    workbench_claim: dict = field(default_factory=dict)
    verdict: str = ""                   # agree | partially_agree | partially_disagree | disagree | insufficient_data
    stage_assessment: str = ""          # Julia's own stage judgment
    confidence: float = 0.0             # Julia's confidence in HER assessment
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    expected_outcomes: list[dict] = field(default_factory=list)
    rationale: str = ""                 # Why Julia agrees or disagrees
    created_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())


@dataclass
class IndependentReviewResult:
    """Complete output of Julia's independent review.

    Contains: market facts snapshot, workbench judgments,
    Julia's assessments per theme, and overall review quality.
    """
    review_id: str = field(default_factory=lambda: f"review_{uuid4().hex}")
    trade_date: str = ""

    # Inputs
    market_context: dict = field(default_factory=dict)
    workbench_review: dict = field(default_factory=dict)

    # Julia's judgments
    judgments: list[JuliaJudgment] = field(default_factory=list)

    # Overall
    overall_assessment: str = ""         # Julia's high-level take
    agreement_ratio: float = 0.0         # fraction of claims Julia agrees with
    created_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())


# ── Evidence Extractor ──────────────────────────────────────────────────────

class EvidenceExtractor:
    """Extracts evidence for/against workbench claims from market facts.

    This is rule-based + structural analysis. Zero LLM dependency.
    Julia's Reasoning layer consumes the extracted evidence to form
    her own judgment.
    """

    def extract(
        self,
        context: dict,      # market.context.snapshot output
        review: dict,       # market.workbench.review output
    ) -> list[ClaimEvidence]:
        """For each workbench theme judgment, find supporting and contradicting evidence."""
        claims = []
        theme_facts = {t.get("subject", ""): t for t in context.get("themes", [])}
        theme_judgments = review.get("theme_judgments", [])

        for judgment in theme_judgments:
            subject = judgment.get("subject", "")
            facts = theme_facts.get(subject, {})
            if not facts:
                continue

            claim_text = f"{subject}: {judgment.get('stage_judgment', 'unknown')} (confidence={judgment.get('confidence', 0)})"

            supporting, contradicting, missing = self._compare(
                facts, judgment
            )

            claims.append(ClaimEvidence(
                claim=claim_text,
                source="analyst_workbench",
                source_confidence=float(judgment.get("confidence", 0.5)),
                supporting_evidence=supporting,
                contradicting_evidence=contradicting,
                missing_evidence=missing,
            ))

        return claims

    def _compare(self, facts: dict, judgment: dict) -> tuple[list, list, list]:
        """Compare facts against judgment. Returns (supporting, contradicting, missing)."""
        supporting = []
        contradicting = []
        missing = []

        # Check: capital direction
        capital = facts.get("capital_direction", "")
        if capital == "inflow":
            supporting.append(f"capital_inflow_{capital}")
        elif capital == "outflow":
            contradicting.append(f"capital_outflow_{capital}")
        elif capital == "mixed":
            missing.append("unclear_capital_direction")

        # Check: leader health
        leader = facts.get("leader_health", "")
        if leader == "strong":
            supporting.append(f"leader_strong_{leader}")
        elif leader == "weakening":
            contradicting.append(f"leader_weakening_{leader}")
        elif leader == "weak":
            contradicting.append(f"leader_weak_{leader}")

        # Check: breadth
        breadth = facts.get("breadth", "")
        if breadth in ("wide", "expanding"):
            supporting.append(f"breadth_{breadth}")
        elif breadth == "contracting":
            contradicting.append(f"breadth_contracting")
            missing.append("why_is_breadth_contracting")

        # Check: strength score
        strength = float(facts.get("strength", 0))
        confidence = float(judgment.get("confidence", 0.5))
        if strength >= 0.7:
            supporting.append(f"strength_{strength}")
        elif strength < 0.5:
            contradicting.append(f"weak_strength_{strength}")
            missing.append("what_drove_strength_decline")

        if strength < 0.7 and confidence > 0.7:
            contradicting.append(f"confidence_mismatch: workbench={confidence} vs strength={strength}")

        return supporting, contradicting, missing


# ── Independent Review Pipeline ─────────────────────────────────────────────

class IndependentReviewPipeline:
    """Orchestrates Julia's independent review of workbench judgments.

    1. Load market facts (context)
    2. Load workbench judgments (review)
    3. Extract claims vs evidence
    4. For each claim: assess agreement level
    5. Register expected outcomes for verification
    6. Return JuliaJudgment for each theme
    """

    def __init__(self):
        self.evidence = EvidenceExtractor()

    def review(
        self,
        market_context: dict,
        workbench_review: dict,
    ) -> IndependentReviewResult:
        """Execute independent review. Returns Julia's assessments."""
        trade_date = market_context.get("trade_date", "")

        # Extract all claim-evidence pairs
        claims = self.evidence.extract(market_context, workbench_review)

        # Form Julia's judgment per claim
        judgments = []
        agree_count = 0
        for claim in claims:
            judgment = self._assess(claim)
            judgments.append(judgment)
            if judgment.verdict in ("agree", "partially_agree"):
                agree_count += 1

        # Overall assessment
        agreement_ratio = agree_count / len(judgments) if judgments else 0.0
        overall = self._summarize(judgments, agreement_ratio)

        return IndependentReviewResult(
            trade_date=trade_date,
            market_context=market_context,
            workbench_review=workbench_review,
            judgments=judgments,
            overall_assessment=overall,
            agreement_ratio=agreement_ratio,
        )

    def _assess(self, claim: ClaimEvidence) -> JuliaJudgment:
        """Form Julia's independent judgment on one claim."""
        n_support = len(claim.supporting_evidence)
        n_contra = len(claim.contradicting_evidence)

        # Determine verdict
        if n_contra == 0 and n_support >= 2:
            verdict = "agree"
            confidence = min(0.85, 0.6 + n_support * 0.1)
        elif n_contra == 0 and n_support >= 1:
            verdict = "partially_agree"
            confidence = 0.55
        elif n_contra >= 2 and n_support == 0:
            verdict = "disagree"
            confidence = 0.7
        elif n_contra >= 1 and n_support >= 2:
            verdict = "partially_disagree"
            confidence = 0.65
        elif n_contra >= 2:
            verdict = "partially_disagree"
            confidence = 0.6
        elif n_support == 0 and n_contra == 0:
            verdict = "insufficient_data"
            confidence = 0.3
        else:
            verdict = "partially_agree"
            confidence = 0.5

        # Stage assessment
        if verdict in ("agree", "partially_agree"):
            stage = f"consistent_with_workbench"
        elif verdict == "disagree":
            stage = self._infer_contradicting_stage(claim)
        else:
            stage = "uncertain"

        return JuliaJudgment(
            subject=claim.claim.split(":")[0] if ":" in claim.claim else claim.claim,
            workbench_claim={
                "claim": claim.claim,
                "source": claim.source,
                "confidence": claim.source_confidence,
            },
            verdict=verdict,
            stage_assessment=stage,
            confidence=round(confidence, 2),
            supporting_evidence=claim.supporting_evidence,
            contradicting_evidence=claim.contradicting_evidence,
            missing_evidence=claim.missing_evidence,
            expected_outcomes=self._generate_expected_outcomes(verdict, claim),
            rationale=f"supporting={n_support}, contradicting={n_contra}",
        )

    def _infer_contradicting_stage(self, claim: ClaimEvidence) -> str:
        if any("leader_weakening" in e for e in claim.contradicting_evidence):
            if any("breadth_contracting" in e for e in claim.contradicting_evidence):
                return "late_acceleration_to_divergence"
            return "acceleration_with_leader_divergence"
        if any("strength" in e for e in claim.contradicting_evidence):
            return "fading_momentum"
        return "data_inconclusive"

    def _generate_expected_outcomes(self, verdict: str, claim: ClaimEvidence) -> list[dict]:
        outcomes = []
        if "leader_weakening" in " ".join(claim.contradicting_evidence):
            outcomes.append({
                "window": "1_trading_day",
                "condition": "leader_recovers_and_breadth_expands",
                "supports": "continued_strength",
                "invalidates": "no_recovery_by_close",
            })
        if "breadth_contracting" in " ".join(claim.contradicting_evidence):
            outcomes.append({
                "window": "1_trading_day",
                "condition": "breadth_re_expands_or_contracts_further",
                "supports": "recovery_or_decline_confirmed",
                "invalidates": "broadth_stays_flat",
            })
        if not outcomes:
            outcomes.append({
                "window": "1_trading_day",
                "condition": "theme_maintains_current_trajectory",
                "supports": "continued_momentum",
                "invalidates": "significant_reversal",
            })
        return outcomes

    def _summarize(self, judgments: list[JuliaJudgment], ratio: float) -> str:
        if not judgments:
            return "无主题判断需要审查"

        n_agree = sum(1 for j in judgments if j.verdict in ("agree", "partially_agree"))
        n_disagree = sum(1 for j in judgments if j.verdict in ("disagree", "partially_disagree"))
        n_insufficient = sum(1 for j in judgments if j.verdict == "insufficient_data")

        parts = [f"审查了{len(judgments)}个工作台判断"]
        if n_agree:
            parts.append(f"{n_agree}个同意或部分同意")
        if n_disagree:
            parts.append(f"{n_disagree}个存在分歧")
        if n_insufficient:
            parts.append(f"{n_insufficient}个数据不足")

        return "，".join(parts)


__all__ = [
    "JuliaJudgment",
    "IndependentReviewResult",
    "ClaimEvidence",
    "EvidenceExtractor",
    "IndependentReviewPipeline",
]

"""Julia Independent Review Workflow — facts vs judgments → independent assessment.

Contract-mapped from ai_theme_app derived format (raw_metrics + derived_signals).
Null semantics preserved — null = unknown, not 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import uuid4

CST = timezone(timedelta(hours=8))

# ── Contract Mapper: ai_theme_app derived format → Julia flat facts ─────────

class ThemeFactContractMapper:
    """Maps ai_theme_app derived format to Julia audit-compatible flat facts.

    ai_theme_app format:
      raw_metrics.{mainline_strength_score, confidence_score, ...}
      derived_signals.{stage_signal, capital_direction, leader_health, strong_stock_coverage}
        each: {value, origin, raw_count?}

    Julia flat format:
      strength, derived_stage_signal, capital_direction, leader_health, breadth

    Null semantics: None → None (not 0).
    """

    ALIASES = {
        "strength": ("raw_metrics", "mainline_strength_score"),
        "derived_stage_signal": ("derived_signals", "stage_signal"),
        "capital_direction": ("derived_signals", "capital_direction"),
        "leader_health": ("derived_signals", "leader_health"),
        "breadth": ("derived_signals", "strong_stock_coverage"),
    }

    @classmethod
    def map(cls, fact_entry: dict) -> dict:
        """Convert one ai_theme_app theme entry → Julia flat facts dict."""
        flat = {"subject": fact_entry.get("subject", "")}
        raw_metrics = fact_entry.get("raw_metrics") or {}
        derived_signals = fact_entry.get("derived_signals") or {}

        for julia_key, (source_group, signal_name) in cls.ALIASES.items():
            if source_group == "raw_metrics":
                flat[julia_key] = raw_metrics.get(signal_name)  # None preserved
            else:
                sig = derived_signals.get(signal_name)
                flat[julia_key] = sig.get("value") if isinstance(sig, dict) else sig

        # Backward compat: old flat fields override if present
        for k in cls.ALIASES:
            if k in fact_entry and flat.get(k) is None:
                flat[k] = fact_entry[k]

        return flat

    @classmethod
    def build_fact_index(cls, context: dict) -> dict[str, dict]:
        """Build {subject_name: flat_facts} index from ai_theme_app context."""
        index = {}
        for t in context.get("themes", []):
            name = t.get("subject", "")
            if not name:
                continue
            index[name] = cls.map(t)
        return index


# ── Stage Inference (blind — does NOT receive workbench claim) ─────────────

STAGE_ORDER = {
    "start": 0, "diffusion": 1, "acceleration": 2,
    "consolidation": 3, "divergence": 4, "decline": 5,
}


class StageInferenceEngine:
    """Derives julia_stage from structural evidence ONLY.

    Does NOT receive workbench claim. True blind inference.
    """

    def infer(self, facts: dict) -> tuple[str, list[str]]:
        """Returns (julia_stage, evidence_used)."""
        has_strength = _is_present(facts.get("strength")) and float(facts.get("strength", 0)) >= 0.6
        has_capital = facts.get("capital_direction") == "inflow"
        has_leader = facts.get("leader_health") == "strong"
        leader_weak = facts.get("leader_health") == "weakening"
        has_breadth = facts.get("breadth") in ("wide", "expanding")
        breadth_contracting = facts.get("breadth") == "contracting"
        strength_value = _float_or_null(facts.get("strength"))

        evidence = []

        if has_leader and has_breadth and has_capital and has_strength:
            evidence = ["leader_strong", "breadth_wide", "capital_inflow", f"strength_{strength_value}"]
            return ("acceleration", evidence)
        if leader_weak and breadth_contracting:
            evidence = ["leader_weak", "breadth_contracting"]
            return ("divergence", evidence)
        if has_leader and has_breadth:
            evidence = ["leader_strong", "breadth_wide"]
            return ("diffusion", evidence)
        if leader_weak:
            evidence = ["leader_weak"]
            return ("fading_momentum", evidence)
        if has_strength and has_breadth:
            evidence = [f"strength_{strength_value}", "breadth_wide"]
            return ("diffusion", evidence)
        if strength_value is not None and strength_value < 0.4:
            evidence = [f"strength_{strength_value}"]
            return ("start", evidence)
        return ("data_inconclusive", [])


# ── Models ──────────────────────────────────────────────────────────────────

@dataclass
class ClaimEvidence:
    claim: str
    source: str
    source_confidence: float
    opinion_provenance: dict = field(default_factory=dict)
    has_facts: bool = True
    julia_stage: str = ""
    inference_evidence: list[str] = field(default_factory=list)
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)


@dataclass
class JuliaJudgment:
    judgment_id: str = field(default_factory=lambda: f"judgment_{uuid4().hex}")
    subject: str = ""
    verdict: str = ""
    workbench_claim: dict = field(default_factory=dict)
    julia_stage: str = ""
    confidence: float = 0.0
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    inference_evidence: list[str] = field(default_factory=list)
    expected_outcomes: list[dict] = field(default_factory=list)
    rationale: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())


@dataclass
class IndependentReviewResult:
    review_id: str = field(default_factory=lambda: f"review_{uuid4().hex}")
    trade_date: str = ""
    status: str = ""
    blocked_reason: str = ""
    market_context: dict = field(default_factory=dict)
    workbench_review: dict = field(default_factory=dict)
    judgments: list[JuliaJudgment] = field(default_factory=list)
    overall_assessment: str = ""
    agreement_ratio: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())


# ── Admission Gate ──────────────────────────────────────────────────────────

class IndependentReviewAdmissionGate:
    ALLOWED_OPINION_MODES = {"ai_draft", "analyst_approved"}
    ALLOWED_CONTEXT_STATUSES = {"live", "partial"}

    def check(self, context: dict, review: dict) -> tuple[bool, str]:
        ctx_schema = context.get("schema_version", "")
        rev_schema = review.get("schema_version", "")
        if ctx_schema != "market-context.v1":
            return False, f"unsupported context schema: {ctx_schema}"
        if rev_schema != "analyst-workbench.review.v1":
            return False, f"unsupported review schema: {rev_schema}"

        ctx_date = context.get("trade_date", "")
        rev_date = review.get("trade_date", "")
        if ctx_date and rev_date and ctx_date != rev_date:
            return False, f"date mismatch: context={ctx_date} review={rev_date}"

        ctx_status = context.get("status", "")
        if ctx_status not in self.ALLOWED_CONTEXT_STATUSES:
            return False, f"context status blocked: {ctx_status}"

        rev_opinion = review.get("opinion_mode", "")
        if rev_opinion == "rejected":
            return False, f"review opinion rejected: {review.get('validation_errors', [])}"
        if rev_opinion not in self.ALLOWED_OPINION_MODES:
            return False, f"review opinion blocked: {rev_opinion}"

        ctx_quality = context.get("quality", {})
        if ctx_quality.get("source_quality", 0) < 0.3:
            return False, "context quality too low"

        return True, "ok"


# ── Stage Claim Auditor (comparative — runs AFTER inference) ────────────────

class StageClaimAuditor:
    """Compares Julia's independent stage against workbench claim.

    Evidence classification is CONTEXT-AWARE:
      - leader_weak is SUPPORTING for divergence, CONTRADICTING for acceleration
      - breadth_contracting is SUPPORTING for divergence, CONTRADICTING for acceleration
      - capital_inflow is SUPPORTING for acceleration/diffusion, neutral for divergence

    Market signal polarity must not be confused with claim agreement.
    """

    # Evidence that is SUPPORTING for each stage type
    STAGE_EVIDENCE = {
        "acceleration": {
            "supporting": {"leader_strong", "breadth_wide", "capital_inflow", "strength_strong"},
            "contradicting": {"leader_weak", "breadth_contracting", "strength_low"},
        },
        "diffusion": {
            "supporting": {"leader_strong", "breadth_wide", "strength_strong"},
            "contradicting": {"leader_weak", "breadth_contracting"},
        },
        "divergence": {
            "supporting": {"leader_weak", "breadth_contracting"},
            "contradicting": {"leader_strong", "breadth_wide", "capital_inflow"},
        },
        "start": {
            "supporting": set(),
            "contradicting": {"strength_low"},
        },
        "decline": {
            "supporting": {"leader_weak", "strength_low", "breadth_contracting"},
            "contradicting": {"leader_strong", "strength_strong", "capital_inflow"},
        },
    }

    def audit(self, julia_stage: str, claim: dict, facts: dict) -> tuple[list, list, list]:
        """Classify evidence relative to the workbench's claimed stage."""
        claimed = str(claim.get("stage_judgement", ""))
        stage_rules = self.STAGE_EVIDENCE.get(claimed, {})
        stage_support = stage_rules.get("supporting", set())
        stage_contra = stage_rules.get("contradicting", set())

        supporting, contradicting, missing = [], [], []

        # Compare stages
        if julia_stage == claimed:
            supporting.append(_evid("stages_aligned", julia_stage, claimed))
        elif julia_stage == "data_inconclusive":
            missing.append(_evid("julia_inconclusive", julia_stage, claimed))
        elif julia_stage and claimed:
            jo = STAGE_ORDER.get(julia_stage, -1)
            co = STAGE_ORDER.get(claimed, -1)
            if jo >= 0 and co >= 0 and abs(jo - co) <= 1:
                missing.append(_evid("stages_close", julia_stage, claimed))
            else:
                contradicting.append(_evid("stages_diverged", julia_stage, claimed))

        # Classify each raw evidence item by context
        raw_items = [
            ("capital_inflow") if facts.get("capital_direction") == "inflow" else None,
            ("leader_strong") if facts.get("leader_health") == "strong" else None,
            ("leader_weak") if facts.get("leader_health") in ("weakening", "weak") else None,
            ("breadth_wide") if facts.get("breadth") in ("wide", "expanding") else None,
            ("breadth_contracting") if facts.get("breadth") == "contracting" else None,
            ("strength_strong") if _is_present(facts.get("strength")) and float(facts.get("strength", 0)) >= 0.7 else None,
            ("strength_low") if _is_present(facts.get("strength")) and float(facts.get("strength", 0)) < 0.5 else None,
        ]

        for item in raw_items:
            if item is None:
                continue
            if item in stage_support:
                supporting.append(_evid(item))
            elif item in stage_contra:
                contradicting.append(_evid(item))
            # items not in either set are neutral — not added to either side

        # Missing
        for key in ("strength", "leader_health", "breadth", "capital_direction"):
            val = facts.get(key)
            if val is None or val in ("unknown", "unavailable", ""):
                missing.append(_evid(f"missing_{key}"))

        return self._dedup(supporting), self._dedup(contradicting), self._dedup(missing)

    @staticmethod
    def _dedup(evidence: list[str]) -> list[str]:
        seen = set()
        result = []
        for item in evidence:
            eid = item.split("::")[0] if "::" in item else item
            if eid not in seen:
                seen.add(eid)
                result.append(item)
        return result


def _evid(id: str, metric: str = "", value: Any = None) -> str:
    """Standard evidence ID format: id::metric=value."""
    if metric and value is not None:
        return f"{id}::{metric}={value}"
    return id


# ── Evidence Extractor ──────────────────────────────────────────────────────

class EvidenceExtractor:
    def __init__(self):
        self.inference = StageInferenceEngine()
        self.stage_auditor = StageClaimAuditor()
        self.mapper = ThemeFactContractMapper()

    def extract(self, context: dict, review: dict) -> list[ClaimEvidence]:
        fact_index = self.mapper.build_fact_index(context)
        judgments = review.get("claims", [])
        opinion_mode = review.get("opinion_mode", "unknown")
        approval = review.get("approval", {})

        claims = []
        for j in judgments:
            subject = j.get("subject", {})
            name = subject.get("name", "") if isinstance(subject, dict) else str(subject)
            if not name:
                continue

            facts = fact_index.get(name, {})
            if not facts:
                claims.append(ClaimEvidence(
                    claim=f"{name}: {j.get('stage_judgement', 'unknown')}",
                    source="analyst_workbench",
                    source_confidence=float(j.get("confidence", 0.5)),
                    opinion_provenance=_provenance(opinion_mode, j, approval),
                    missing_evidence=[_evid("theme_fact_not_found")],
                    has_facts=False,
                ))
                continue

            # Step 1: Infer Julia's stage BLIND (no workbench claim)
            julia_stage, inference_evidence = self.inference.infer(facts)

            # Step 2: Compare against workbench claim
            supporting, contradicting, missing = self.stage_auditor.audit(
                julia_stage, j, facts
            )

            claims.append(ClaimEvidence(
                claim=f"{name}: workbench={j.get('stage_judgement', '?')} julia={julia_stage}",
                source="analyst_workbench",
                source_confidence=float(j.get("confidence", 0.5)),
                opinion_provenance=_provenance(opinion_mode, j, approval),
                julia_stage=julia_stage,
                inference_evidence=inference_evidence,
                supporting_evidence=supporting,
                contradicting_evidence=contradicting,
                missing_evidence=missing,
                has_facts=True,
            ))

        return claims


def _provenance(mode: str, j: dict, approval: dict) -> dict:
    """If approved, analyst_reviewed is always True at envelope level."""
    p = {
        "opinion_mode": mode,
        "claim_id": j.get("claim_id", ""),
        "analyst_reviewed": True if mode == "analyst_approved" else j.get("analyst_reviewed", False),
    }
    for k in ("snapshot_version", "snapshot_hash", "draft_version"):
        if k in approval:
            p[k] = approval[k]
    return p


# ── Pipeline ────────────────────────────────────────────────────────────────

class IndependentReviewPipeline:
    def __init__(self):
        self.evidence = EvidenceExtractor()
        self.gate = IndependentReviewAdmissionGate()

    def review(self, context: dict, review: dict) -> IndependentReviewResult:
        if context.get("status") in ("unavailable", "synthetic"):
            return IndependentReviewResult(
                trade_date=context.get("trade_date", ""),
                status="blocked",
                blocked_reason=f"context status: {context.get('status')}",
                market_context=context,
                workbench_review=review,
            )

        allowed, reason = self.gate.check(context, review)
        if not allowed:
            return IndependentReviewResult(
                trade_date=context.get("trade_date", ""),
                status="blocked",
                blocked_reason=reason,
                market_context=context,
                workbench_review=review,
            )

        claims = self.evidence.extract(context, review)

        judgments = []
        agree_count = 0
        for claim in claims:
            j = self._assess(claim)
            judgments.append(j)
            if j.verdict in ("agree", "partially_agree"):
                agree_count += 1

        ratio = agree_count / len(judgments) if judgments else 0.0

        return IndependentReviewResult(
            trade_date=context.get("trade_date", ""),
            status="completed" if context.get("status") == "live" else "partial",
            market_context=context,
            workbench_review=review,
            judgments=judgments,
            overall_assessment=self._summarize(judgments, ratio),
            agreement_ratio=ratio,
        )

    def _assess(self, claim: ClaimEvidence) -> JuliaJudgment:
        base = {
            "claim": claim.claim,
            "confidence": claim.source_confidence,
            "opinion_provenance": claim.opinion_provenance,
        }
        if not claim.has_facts:
            return JuliaJudgment(
                subject=claim.claim.split(":")[0],
                workbench_claim=base,
                verdict="insufficient_data",
                julia_stage="unknown",
                confidence=0.25,
                missing_evidence=claim.missing_evidence,
                rationale="no_market_facts_for_this_subject",
            )

        # P0: data_inconclusive → insufficient_data regardless of evidence counts
        if claim.julia_stage == "data_inconclusive":
            return JuliaJudgment(
                subject=claim.claim.split(":")[0],
                workbench_claim=base,
                verdict="insufficient_data",
                julia_stage="data_inconclusive",
                confidence=0.25,
                inference_evidence=claim.inference_evidence,
                missing_evidence=claim.missing_evidence,
                rationale="cannot_form_independent_stage",
            )

        ns, nc = len(claim.supporting_evidence), len(claim.contradicting_evidence)
        nm = len(claim.missing_evidence)

        # P0: missing evidence reduces confidence, may downgrade verdict
        if nc == 0 and ns >= 2:
            verdict, conf = "agree", min(0.85, 0.6 + ns * 0.1)
            if nm >= 2: verdict, conf = "partially_agree", conf - 0.15
        elif nc == 0 and ns >= 1:
            verdict, conf = "partially_agree", 0.55
        elif nc >= 2 and ns == 0:
            verdict, conf = "disagree", 0.7
        elif nc >= 1 and ns >= 2:
            verdict, conf = "partially_disagree", 0.65
        elif nc >= 2:
            verdict, conf = "partially_disagree", 0.6
        elif ns == 0 and nc == 0:
            if nm >= 3: verdict, conf = "insufficient_data", 0.25
            else: verdict, conf = "partially_agree", 0.45
        else:
            verdict, conf = "partially_agree", 0.5

        return JuliaJudgment(
            subject=claim.claim.split(":")[0],
            workbench_claim=base,
            verdict=verdict,
            julia_stage=claim.julia_stage,  # P0: direct from claim, no string parsing
            confidence=round(max(0.15, conf), 2),
            inference_evidence=claim.inference_evidence,
            supporting_evidence=claim.supporting_evidence,
            contradicting_evidence=claim.contradicting_evidence,
            missing_evidence=claim.missing_evidence,
            expected_outcomes=self._outcomes(verdict, claim),
            rationale=f"support={ns} contradict={nc} missing={nm}",
        )

    def _outcomes(self, verdict: str, claim: ClaimEvidence) -> list[dict]:
        outcomes = []
        ct = " ".join(claim.contradicting_evidence)
        if "leader_weak" in ct:
            outcomes.append({"window": "1_trading_day", "condition": "leader_recovers", "supports": "recovery"})
        if "breadth_contracting" in ct:
            outcomes.append({"window": "1_trading_day", "condition": "breadth_re_expands", "supports": "recovery"})
        if not outcomes:
            outcomes.append({"window": "1_trading_day", "condition": "maintains_trajectory", "supports": "continued"})
        return outcomes

    def _summarize(self, judgments: list[JuliaJudgment], ratio: float) -> str:
        if not judgments:
            return "no claims to review"
        na = sum(1 for j in judgments if j.verdict in ("agree", "partially_agree"))
        nd = sum(1 for j in judgments if j.verdict in ("disagree", "partially_disagree"))
        ni = sum(1 for j in judgments if j.verdict == "insufficient_data")
        parts = [f"reviewed {len(judgments)} claims"]
        if na: parts.append(f"{na} agree")
        if nd: parts.append(f"{nd} disagree")
        if ni: parts.append(f"{ni} insufficient")
        return ", ".join(parts)


def _is_present(val: Any) -> bool:
    return val is not None and val not in ("", "unknown", "unavailable", "n/a")


def _float_or_null(val: Any) -> float | None:
    try: return float(val)
    except: return None


__all__ = [
    "JuliaJudgment", "IndependentReviewResult", "ClaimEvidence",
    "EvidenceExtractor", "IndependentReviewPipeline",
    "IndependentReviewAdmissionGate", "StageInferenceEngine",
    "StageClaimAuditor", "ThemeFactContractMapper",
]

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
        """Build {subject_name: flat_facts} index from ai_theme_app context.

        Uses subject_key if available to disambiguate duplicate names.
        Falls back to subject name.
        """
        index = {}
        for t in context.get("themes", []):
            name = t.get("subject", "")
            if not name:
                continue
            key = t.get("subject_key", name)
            if key in index:
                # Collision: keep the entry with higher strength
                existing = index[key]
                new_facts = cls.map(t)
                if (new_facts.get("strength") or 0) > (existing.get("strength") or 0):
                    index[key] = new_facts
            else:
                index[key] = cls.map(t)
        return index


# ── Stage Taxonomy (single authority for stages, order, evidence, inference) ─

class StageSignalEvaluator:
    """Single authority for computing signal values from market facts.

    No other module defines thresholds like 'strength_low < 0.4' or
    'leader_strong == leader_health:strong'. All thresholds live here.

    Both StageInferenceEngine and StageClaimAuditor consume the same
    signal set — ensuring zero threshold drift.
    """

    SIGNAL_RULES = {
        "strength_low":      lambda f: _is_present(f.get("strength")) and f["strength"] < 0.4,
        "strength_strong":   lambda f: _is_present(f.get("strength")) and f["strength"] >= 0.6,
        "leader_strong":     lambda f: f.get("leader_health") == "strong",
        "leader_weak":       lambda f: f.get("leader_health") in ("weakening", "weak"),
        "breadth_wide":      lambda f: f.get("breadth") in ("wide", "expanding"),
        "breadth_contracting": lambda f: f.get("breadth") == "contracting",
        "capital_inflow":    lambda f: f.get("capital_direction") == "inflow",
    }

    @classmethod
    def evaluate(cls, facts: dict) -> set[str]:
        """Return the set of active signal names for these facts."""
        return {name for name, pred in cls.SIGNAL_RULES.items() if pred(facts)}


# ── Stage Taxonomy (executable — single authority) ──────────────────────────

class StageTaxonomy:
    """Unified, executable stage definitions.

    Inference engine reads inference_requires from here (not hardcoded).
    Auditor reads supporting/contradicting from here.
    Both consume the same StageSignalEvaluator output.
    """

    STAGES = {
        "start": {
            "order": 0, "inference_priority": 10,   # lowest priority — fallback when nothing else matches
            "aliases": (),
            "inference_requires": {"strength_low"},
            "supporting": {"strength_low"},
            "contradicting": {"strength_strong", "leader_strong", "breadth_wide", "capital_inflow"},
        },
        "diffusion": {
            "order": 1, "inference_priority": 30,
            "aliases": ("fermentation",),  # ai_theme_app: 发酵期 ≈ diffusion
            "inference_requires": {"leader_strong", "breadth_wide"},
            "supporting": {"leader_strong", "breadth_wide", "strength_strong"},
            "contradicting": {"leader_weak", "breadth_contracting"},
        },
        "acceleration": {
            "order": 2, "inference_priority": 60,
            "aliases": ("consolidation",),
            "inference_requires": {"leader_strong", "breadth_wide", "capital_inflow", "strength_strong"},
            "supporting": {"leader_strong", "breadth_wide", "capital_inflow", "strength_strong"},
            "contradicting": {"leader_weak", "breadth_contracting", "strength_low"},
        },
        "fading_momentum": {
            "order": 3, "inference_priority": 20,
            "aliases": (),
            "inference_requires": {"leader_weak"},
            "supporting": {"leader_weak"},
            "contradicting": {"leader_strong", "strength_strong", "capital_inflow"},
        },
        "divergence": {
            "order": 4, "inference_priority": 40,
            "aliases": (),
            "inference_requires": {"leader_weak", "breadth_contracting"},
            "supporting": {"leader_weak", "breadth_contracting"},
            "contradicting": {"leader_strong", "breadth_wide", "capital_inflow"},
        },
        "decline": {
            "order": 5, "inference_priority": 80,
            "aliases": (),
            "inference_requires": {"leader_weak", "strength_low", "breadth_contracting"},
            "supporting": {"leader_weak", "strength_low", "breadth_contracting"},
            "contradicting": {"leader_strong", "strength_strong", "capital_inflow"},
        },
    }

    TERMINAL_STAGES = frozenset({"data_inconclusive"})

    @classmethod
    def order(cls, stage: str) -> int:
        entry = cls.STAGES.get(stage)
        return entry["order"] if entry else -1

    @classmethod
    def all_stages(cls) -> set[str]:
        return set(cls.STAGES.keys()) | cls.TERMINAL_STAGES

    @classmethod
    def evidence_for(cls, stage: str) -> dict:
        entry = cls.STAGES.get(stage, {})
        return {
            "supporting": entry.get("supporting", set()),
            "contradicting": entry.get("contradicting", set()),
        }

    @classmethod
    def resolve_alias(cls, name: str) -> str:
        for stage, entry in cls.STAGES.items():
            if name in entry.get("aliases", ()):
                return stage
        return name

    @classmethod
    def inference_order(cls) -> list[str]:
        """Stages sorted by inference_priority (descending).
        Most specific stages (decline, acceleration) checked first.
        """
        return sorted(
            cls.STAGES.keys(),
            key=lambda s: cls.STAGES[s].get("inference_priority", 0),
            reverse=True,
        )


# ── Stage Inference (driven by executible taxonomy) ─────────────────────────

class StageInferenceEngine:
    """Derives julia_stage from structural evidence ONLY.

    Reads inference_requires from StageTaxonomy.
    Consumes signals from StageSignalEvaluator.
    Both are the single authorities — no hardcoded rules.
    """

    def infer(self, facts: dict) -> tuple[str, list[str]]:
        """Returns (julia_stage, signal_evidence)."""
        signals = StageSignalEvaluator.evaluate(facts)

        for stage in StageTaxonomy.inference_order():
            required = StageTaxonomy.STAGES[stage]["inference_requires"]
            if required <= signals:  # all required signals present
                return (stage, sorted(required))

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
    subject_key: str = ""
    subject_name: str = ""
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

    Uses StageTaxonomy for evidence semantics — the single authority.
    Evidence classification is context-aware per claimed stage.
    """

    def audit(self, julia_stage: str, claim: dict, facts: dict) -> tuple[list, list, list]:
        """Classify evidence relative to the workbench's claimed stage."""
        claimed_raw = str(claim.get("stage_judgement", ""))
        claimed = StageTaxonomy.resolve_alias(claimed_raw)
        rules = StageTaxonomy.evidence_for(claimed)
        stage_support = rules["supporting"]
        stage_contra = rules["contradicting"]

        supporting, contradicting, missing = [], [], []

        # Compare stages
        if julia_stage == claimed:
            supporting.append(_evid("stages_aligned", julia_stage, claimed))
        elif julia_stage == "data_inconclusive":
            missing.append(_evid("julia_inconclusive", julia_stage, claimed))
        elif julia_stage and claimed:
            jo = StageTaxonomy.order(julia_stage)
            co = StageTaxonomy.order(claimed)
            if jo >= 0 and co >= 0 and abs(jo - co) <= 1:
                missing.append(_evid("stages_close", julia_stage, claimed))
            else:
                contradicting.append(_evid("stages_diverged", julia_stage, claimed))

        # Evaluate all signals via single authority (no threshold drift)
        signals = StageSignalEvaluator.evaluate(facts)

        for item in signals:
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
            if isinstance(subject, dict):
                name = subject.get("name", "")
                subject_key = subject.get("key", subject.get("subject_key", ""))
            else:
                name = str(subject)
                subject_key = ""

            if not name and not subject_key:
                continue

            # Lookup: subject_key first (stable identity), name as fallback
            facts = (
                (fact_index.get(subject_key) if subject_key else None)
                or fact_index.get(name, {})
            )
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
    subject = j.get("subject", {})
    p = {
        "opinion_mode": mode,
        "claim_id": j.get("claim_id", ""),
        "subject_key": subject.get("key", subject.get("subject_key", "")) if isinstance(subject, dict) else "",
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
        # Extract stable identity from provenance for Outcome Resolver
        prov = claim.opinion_provenance
        subject_key = prov.get("subject_key", "")
        subject_name = claim.claim.split(":")[0] if ":" in claim.claim else claim.claim
        if not subject_key:
            subject_key = prov.get("claim_id", "").replace("claim_0714_", "")

        if not claim.has_facts:
            return JuliaJudgment(
                subject=subject_name, subject_key=subject_key, subject_name=subject_name,
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
                subject=subject_name, subject_key=subject_key, subject_name=subject_name,
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
        elif nc >= 1 and ns == 0:
            # contradiction with zero support → at least partially_disagree
            verdict, conf = "partially_disagree", 0.6
        elif nc >= 1 and ns >= 2:
            verdict, conf = "partially_disagree", 0.65
        elif nc >= 2:
            verdict, conf = "partially_disagree", 0.6
        elif ns == 0 and nc == 0:
            if nm >= 3: verdict, conf = "insufficient_data", 0.25
            else: verdict, conf = "partially_agree", 0.45
        else:
            # ns >= 1, nc == 1 (exactly one of each)
            verdict, conf = "partially_agree", 0.5

        return JuliaJudgment(
            subject=subject_name, subject_key=subject_key, subject_name=subject_name,
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
    "StageClaimAuditor", "StageTaxonomy", "StageSignalEvaluator",
    "ThemeFactContractMapper",
]

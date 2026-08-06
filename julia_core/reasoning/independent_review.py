"""Julia Independent Review Workflow — facts vs judgments → independent assessment.

Dual-input architecture:
  A. market.context.snapshot  → FACTS (what the market is doing)
  B. market.workbench.review  → JUDGMENTS (what the workbench thinks)

Julia compares both, audits stage claims with claim-type-specific logic,
and forms her own judgment. Missing facts produce insufficient_data — never dropped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import uuid4

CST = timezone(timedelta(hours=8))


# ── Stage Definitions ───────────────────────────────────────────────────────

STAGE_ORDER = {
    "start": 0, "diffusion": 1, "acceleration": 2,
    "consolidation": 3, "divergence": 4, "decline": 5,
}

STAGE_REQUIREMENTS = {
    "acceleration": {
        "required": ["strength >= 0.7", "capital_inflow", "leader_strong"],
        "contradicting": ["leader_weakening", "breadth_contracting"],
        "description": "强度提升+资金流入+龙头健康",
    },
    "diffusion": {
        "required": ["strength >= 0.5"],
        "contradicting": ["strength < 0.4"],
        "description": "产业链扩散，中等强度以上",
    },
    "start": {
        "required": [],
        "contradicting": ["strength < 0.3"],
        "description": "早期阶段",
    },
    "divergence": {
        "required": ["leader_weakening"],
        "contradicting": ["leader_strong", "capital_strong_inflow"],
        "description": "龙头走弱，板块分化",
    },
}


# ── Models ──────────────────────────────────────────────────────────────────

@dataclass
class ClaimEvidence:
    claim: str
    source: str
    source_confidence: float
    opinion_provenance: dict = field(default_factory=dict)  # opinion_mode, claim_id, version, hash
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    has_facts: bool = True


@dataclass
class JuliaJudgment:
    judgment_id: str = field(default_factory=lambda: f"judgment_{uuid4().hex}")
    subject: str = ""
    workbench_claim: dict = field(default_factory=dict)
    verdict: str = ""          # agree | partially_agree | partially_disagree | disagree | insufficient_data
    julia_stage: str = ""      # Julia's own stage assessment
    confidence: float = 0.0
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    expected_outcomes: list[dict] = field(default_factory=list)
    rationale: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())


@dataclass
class IndependentReviewResult:
    review_id: str = field(default_factory=lambda: f"review_{uuid4().hex}")
    trade_date: str = ""
    status: str = ""           # "completed" | "blocked" | "partial"
    blocked_reason: str = ""   # set when status=blocked
    market_context: dict = field(default_factory=dict)
    workbench_review: dict = field(default_factory=dict)
    judgments: list[JuliaJudgment] = field(default_factory=list)
    overall_assessment: str = ""
    agreement_ratio: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())


# ── Admission Gate ──────────────────────────────────────────────────────────

class IndependentReviewAdmissionGate:
    """Validates inputs before independent review. Blocks mismatched/invalid data."""

    SUPPORTED_SCHEMAS = {
        "market-context.v1",
        "analyst-workbench.review.v1",
    }

    def check(self, context: dict, review: dict) -> tuple[bool, str]:
        """Returns (allowed, reason)."""
        # Schema versions
        ctx_schema = context.get("schema_version", "")
        rev_schema = review.get("schema_version", "")
        if ctx_schema not in self.SUPPORTED_SCHEMAS:
            return False, f"unsupported context schema: {ctx_schema}"
        if rev_schema not in self.SUPPORTED_SCHEMAS:
            return False, f"unsupported review schema: {rev_schema}"

        # Trade date consistency
        ctx_date = context.get("trade_date", "")
        rev_date = review.get("trade_date", "")
        if ctx_date and rev_date and ctx_date != rev_date:
            return False, f"date mismatch: context={ctx_date} review={rev_date}"

        # Context status
        ctx_status = context.get("status", "")
        if ctx_status == "unavailable":
            return False, "market context unavailable"
        if ctx_status == "synthetic":
            return False, "market context is synthetic — not real data"

        # Review status
        rev_opinion = review.get("opinion_mode", review.get("status", ""))
        if rev_opinion == "not_ready":
            return False, "workbench review not ready"

        # Quality floor
        ctx_quality = context.get("quality", {})
        if ctx_quality.get("source_quality", 0) < 0.3:
            return False, "market context quality too low"

        return True, "ok"


# ── Stage Claim Auditor ─────────────────────────────────────────────────────

class StageClaimAuditor:
    """Compares workbench stage claim against market facts.

    Checks:
      1. Does the claimed stage match fact stage?
      2. Does the workbench stage's requirements hold?
      3. Are contradicting signals present?
    """

    def audit(self, claim: dict, facts: dict) -> tuple[list, list, list]:
        """Returns (supporting, contradicting, missing) evidence.

        Notes: facts['derived_stage_signal'] is a market algorithm output,
        NOT objective truth. It serves as supporting/contradicting evidence,
        not as the ground truth for Julia's stage derivation.
        """
        supporting, contradicting, missing = [], [], []

        claimed_stage = str(claim.get("stage_judgement", ""))
        derived_signal = str(facts.get("derived_stage_signal", facts.get("stage", "")))

        # P0: Compare claim stage vs derived_signal (NOT ground truth)
        if claimed_stage and derived_signal:
            if claimed_stage == derived_signal:
                supporting.append(f"signal_aligned: derived_stage={derived_signal}")
            else:
                signal_order = STAGE_ORDER.get(derived_signal, -1)
                claim_order = STAGE_ORDER.get(claimed_stage, -1)
                if abs(signal_order - claim_order) <= 1:
                    missing.append(f"stage_close: derived={derived_signal} claim={claimed_stage}")
                else:
                    contradicting.append(f"signal_divergence: derived={derived_signal} vs claim={claimed_stage}")

        # Check stage requirements
        reqs = STAGE_REQUIREMENTS.get(claimed_stage, {})
        required = reqs.get("required", [])
        contradict_flags = reqs.get("contradicting", [])

        # Check required conditions
        for req in required:
            if self._check_condition(req, facts):
                supporting.append(f"requirement_met: {req}")
            else:
                contradicting.append(f"requirement_failed: {req}")

        # Check contradicting flags
        for flag in contradict_flags:
            if self._check_condition(flag, facts):
                contradicting.append(f"contradiction_found: {flag}")

        # General evidence (non-stage-specific)
        supporting.extend(self._general_support(facts))
        contradicting.extend(self._general_contradictions(claim, facts))
        missing.extend(self._general_missing(facts))

        return supporting, contradicting, missing

    # Semantic condition → fact key mapping
    CONDITION_MAP = {
        "capital_inflow": ("capital_direction", "inflow"),
        "capital_strong_inflow": ("capital_direction", "strong_inflow"),
        "leader_strong": ("leader_health", "strong"),
        "leader_weakening": ("leader_health", "weakening"),
        "breadth_contracting": ("breadth", "contracting"),
    }

    def _check_condition(self, cond: str, facts: dict) -> bool:
        """Condition checker: 'strength >= 0.7', 'capital_inflow', etc."""
        # Operator-based
        if ">=" in cond:
            key, val = cond.split(">=")
            return float(facts.get(key.strip(), 0)) >= float(val.strip())
        if ">" in cond:
            key, val = cond.split(">")
            return float(facts.get(key.strip(), 0)) > float(val.strip())
        if "<" in cond:
            key, val = cond.split("<")
            return float(facts.get(key.strip(), 0)) < float(val.strip())
        # Named condition: use semantic mapping
        key = cond.strip()
        if key in self.CONDITION_MAP:
            fact_key, expected = self.CONDITION_MAP[key]
            return str(facts.get(fact_key, "")).lower() == expected.lower()
        # Direct key lookup
        val = facts.get(key, None)
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "yes", "strong", "inflow", "wide", "expanding", "improving")
        return bool(val)

    def _general_support(self, facts: dict) -> list:
        supporting = []
        if facts.get("capital_direction") == "inflow":
            supporting.append("capital_inflow")
        if str(facts.get("leader_health", "")).lower() in ("strong",):
            supporting.append("leader_strong")
        if str(facts.get("breadth", "")).lower() in ("wide", "expanding"):
            supporting.append(f"breadth_{facts.get('breadth')}")
        if float(facts.get("strength", 0)) >= 0.7:
            supporting.append(f"strength_{facts['strength']}")
        return supporting

    def _general_contradictions(self, claim: dict, facts: dict) -> list:
        contradicting = []
        leader = str(facts.get("leader_health", "")).lower()
        if leader in ("weakening", "weak"):
            contradicting.append(f"leader_{leader}")
        breadth = str(facts.get("breadth", "")).lower()
        if breadth == "contracting":
            contradicting.append("breadth_contracting")
        strength = float(facts.get("strength", 0))
        conf = float(claim.get("confidence", 0.5))
        if strength < 0.5 and conf > 0.7:
            contradicting.append(f"confidence_mismatch: claim_conf={conf} vs strength={strength}")
        return contradicting

    def _general_missing(self, facts: dict) -> list:
        missing = []
        if facts.get("capital_direction", "") == "mixed":
            missing.append("unclear_capital_direction")
        if not facts.get("leader_health"):
            missing.append("missing_leader_health")
        if not facts.get("breadth"):
            missing.append("missing_breadth_data")
        if not facts.get("strength"):
            missing.append("missing_strength_score")
        return missing


# ── Evidence Extractor (updated) ─────────────────────────────────────────────

class EvidenceExtractor:
    """Extracts evidence for/against workbench claims from market facts.

    Uses StageClaimAuditor for stage claims. Generic fallback for other types.
    Missing facts → insufficient_data claim (never dropped silently).
    """

    def __init__(self):
        self.stage_auditor = StageClaimAuditor()

    def extract(self, context: dict, review: dict) -> list[ClaimEvidence]:
        theme_facts = self._build_fact_index(context)
        theme_judgments = review.get("claims", review.get("theme_judgments", []))
        opinion_mode = review.get("opinion_mode", "unknown")
        approval = review.get("approval", {})

        claims = []
        for judgment in theme_judgments:
            subject = judgment.get("subject", {})
            subject_name = subject.get("name", "") if isinstance(subject, dict) else str(subject)
            if not subject_name:
                continue

            facts = theme_facts.get(subject_name, {})

            if not facts:
                claims.append(ClaimEvidence(
                    claim=f"{subject_name}: {judgment.get('stage_judgement', 'unknown')}",
                    source="analyst_workbench",
                    source_confidence=float(judgment.get("confidence", 0.5)),
                    opinion_provenance={
                        "opinion_mode": opinion_mode,
                        "claim_id": judgment.get("claim_id", ""),
                        "analyst_reviewed": judgment.get("analyst_reviewed", False),
                        **{k: approval[k] for k in ("snapshot_version", "snapshot_hash", "draft_version") if k in approval},
                    },
                    missing_evidence=["theme_fact_not_found"],
                    has_facts=False,
                ))
                continue

            claim_type = judgment.get("claim_type", "theme_stage")
            if claim_type == "theme_stage":
                supporting, contradicting, missing = self.stage_auditor.audit(judgment, facts)
            else:
                supporting, contradicting, missing = [], [], []

            # Check for unknown-derived values → missing
            missing.extend(self._check_unknown_signals(facts))

            claims.append(ClaimEvidence(
                claim=f"{subject_name}: {judgment.get('stage_judgement', 'unknown')}",
                source="analyst_workbench",
                source_confidence=float(judgment.get("confidence", 0.5)),
                opinion_provenance={
                    "opinion_mode": opinion_mode,
                    "claim_id": judgment.get("claim_id", ""),
                    "analyst_reviewed": judgment.get("analyst_reviewed", False),
                    **{k: approval[k] for k in ("snapshot_version", "snapshot_hash", "draft_version") if k in approval},
                },
                supporting_evidence=self._dedup(supporting),
                contradicting_evidence=self._dedup(contradicting),
                missing_evidence=self._dedup(missing),
                has_facts=True,
            ))

        return claims

    def _build_fact_index(self, context: dict) -> dict:
        """Index themes by subject name from new derived format."""
        index = {}
        for t in context.get("themes", []):
            name = t.get("subject", "")
            if not name:
                continue
            # Flatten nested signal structure for auditor compatibility
            flat = {"subject": name}
            raw = t.get("raw_metrics", {}) or {}
            for k, v in raw.items():
                flat[k] = v if v is not None else 0
            signals = t.get("derived_signals", {}) or {}
            for sig_name, sig_data in signals.items():
                if isinstance(sig_data, dict):
                    flat[sig_name] = sig_data.get("value")
                else:
                    flat[sig_name] = sig_data
            # Backward compat: old flat fields
            for k in ("derived_stage_signal", "capital_direction", "leader_health", "breadth", "strength"):
                if k not in flat and k in t:
                    flat[k] = t[k]
            index[name] = flat
        return index

    @staticmethod
    def _check_unknown_signals(facts: dict) -> list[str]:
        """Signal values that are effectively missing."""
        MISSING = {"", None, "unknown", "unavailable", "n/a"}
        missing = []
        for key in ("capital_direction", "leader_health", "strong_stock_coverage", "stage_signal", "breadth"):
            val = facts.get(key)
            if val in MISSING or (isinstance(val, dict) and val.get("value") in MISSING):
                missing.append(f"unknown_{key}")
        return missing

    @staticmethod
    def _dedup(evidence: list[str]) -> list[str]:
        """Dedup evidence items: normalize to standard evidence IDs."""
        seen = set()
        result = []
        for item in evidence:
            # Extract core evidence ID from descriptive strings
            eid = item.split(":")[0].strip()
            if eid not in seen:
                seen.add(eid)
                result.append(item)
        return result


# ── Independent Review Pipeline ─────────────────────────────────────────────

class IndependentReviewPipeline:
    """Orchestrates Julia's independent review with admission gate + stage auditing."""

    def __init__(self):
        self.evidence = EvidenceExtractor()
        self.gate = IndependentReviewAdmissionGate()

    def review(self, market_context: dict, workbench_review: dict) -> IndependentReviewResult:
        # P0: Admission gate
        allowed, reason = self.gate.check(market_context, workbench_review)
        if not allowed:
            return IndependentReviewResult(
                trade_date=market_context.get("trade_date", ""),
                status="blocked",
                blocked_reason=reason,
                market_context=market_context,
                workbench_review=workbench_review,
            )

        claims = self.evidence.extract(market_context, workbench_review)

        judgments = []
        agree_count = 0
        for claim in claims:
            judgment = self._assess(claim)
            judgments.append(judgment)
            if judgment.verdict in ("agree", "partially_agree"):
                agree_count += 1

        agreement_ratio = agree_count / len(judgments) if judgments else 0.0
        overall = self._summarize(judgments, agreement_ratio)

        return IndependentReviewResult(
            trade_date=market_context.get("trade_date", ""),
            status="completed",
            market_context=market_context,
            workbench_review=workbench_review,
            judgments=judgments,
            overall_assessment=overall,
            agreement_ratio=agreement_ratio,
        )

    def _assess(self, claim: ClaimEvidence) -> JuliaJudgment:
        base_claim = {
            "claim": claim.claim,
            "confidence": claim.source_confidence,
            "opinion_provenance": claim.opinion_provenance,
        }

        if not claim.has_facts:
            return JuliaJudgment(
                subject=claim.claim.split(":")[0],
                workbench_claim=base_claim,
                verdict="insufficient_data",
                julia_stage="unknown",
                confidence=0.25,
                missing_evidence=claim.missing_evidence,
                rationale="no_market_facts_for_this_subject",
            )

        n_support = len(claim.supporting_evidence)
        n_contra = len(claim.contradicting_evidence)

        if n_contra == 0 and n_support >= 2:
            verdict, confidence = "agree", min(0.85, 0.6 + n_support * 0.1)
        elif n_contra == 0 and n_support >= 1:
            verdict, confidence = "partially_agree", 0.55
        elif n_contra >= 2 and n_support == 0:
            verdict, confidence = "disagree", 0.7
        elif n_contra >= 1 and n_support >= 2:
            verdict, confidence = "partially_disagree", 0.65
        elif n_contra >= 2:
            verdict, confidence = "partially_disagree", 0.6
        elif n_support == 0 and n_contra == 0:
            verdict, confidence = "insufficient_data", 0.3
        else:
            verdict, confidence = "partially_agree", 0.5

        julia_stage = self._infer_julia_stage(claim, verdict)
        outcomes = self._generate_outcomes(verdict, claim)

        return JuliaJudgment(
            subject=claim.claim.split(":")[0],
            workbench_claim=base_claim,
            verdict=verdict,
            julia_stage=julia_stage,
            confidence=round(confidence, 2),
            supporting_evidence=claim.supporting_evidence,
            contradicting_evidence=claim.contradicting_evidence,
            missing_evidence=claim.missing_evidence,
            expected_outcomes=outcomes,
            rationale=f"supporting={n_support} contradicting={n_contra}",
        )

    def _infer_julia_stage(self, claim: ClaimEvidence, verdict: str) -> str:
        """Derive Julia's independent stage from evidence.

        Even when agreeing, Julia outputs her OWN stage conclusion,
        not just 'consistent_with_workbench'.
        """
        # Derive from supporting/contradicting evidence
        support_str = " ".join(claim.supporting_evidence)
        contra_str = " ".join(claim.contradicting_evidence)

        has_leader_strong = "leader_strong" in support_str
        has_leader_weak = "leader_weakening" in contra_str
        has_breadth_wide = "breadth_wide" in support_str or "breadth_expanding" in support_str
        has_breadth_contract = "breadth_contracting" in contra_str
        has_capital_inflow = "capital_inflow" in support_str
        has_strength = any("requirement_met: strength" in s or "strength_0." in s for s in claim.supporting_evidence)

        # Derive stage from structural evidence
        if has_leader_strong and has_breadth_wide and has_capital_inflow and has_strength:
            return "acceleration"
        if has_leader_weak and has_breadth_contract:
            return "divergence"
        if has_leader_strong and has_breadth_wide:
            return "diffusion"
        if has_leader_weak:
            return "fading_momentum"
        if has_strength and has_breadth_wide:
            return "diffusion"
        if not has_strength:
            return "start"
        return "data_inconclusive"

    def _generate_outcomes(self, verdict: str, claim: ClaimEvidence) -> list[dict]:
        outcomes = []
        contras = " ".join(claim.contradicting_evidence)
        if "leader_weakening" in contras:
            outcomes.append({
                "window": "1_trading_day",
                "condition": "leader_recovers_and_breadth_expands",
                "supports": "continued_strength",
            })
        if "breadth_contracting" in contras:
            outcomes.append({
                "window": "1_trading_day",
                "condition": "breadth_re_expands_or_further_contracts",
                "supports": "recovery_or_decline_confirmed",
            })
        if not outcomes:
            outcomes.append({
                "window": "1_trading_day",
                "condition": "theme_maintains_current_trajectory",
                "supports": "continued_momentum",
            })
        return outcomes

    def _summarize(self, judgments: list[JuliaJudgment], ratio: float) -> str:
        if not judgments:
            return "no claims to review"
        n_agree = sum(1 for j in judgments if j.verdict in ("agree", "partially_agree"))
        n_disagree = sum(1 for j in judgments if j.verdict in ("disagree", "partially_disagree"))
        n_insuff = sum(1 for j in judgments if j.verdict == "insufficient_data")
        parts = [f"reviewed {len(judgments)} claims"]
        if n_agree:
            parts.append(f"{n_agree} agree/partially_agree")
        if n_disagree:
            parts.append(f"{n_disagree} disagree/partially_disagree")
        if n_insuff:
            parts.append(f"{n_insuff} insufficient_data")
        return ", ".join(parts)


__all__ = [
    "JuliaJudgment", "IndependentReviewResult", "ClaimEvidence",
    "EvidenceExtractor", "IndependentReviewPipeline",
    "IndependentReviewAdmissionGate", "StageClaimAuditor",
]

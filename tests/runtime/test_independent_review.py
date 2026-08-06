"""Independent Review Pipeline Tests — updated for stage audit + missing facts + admission gate.

Run: python -m pytest tests/runtime/test_independent_review.py -v
"""

import pytest

from julia_core.reasoning.independent_review import (
    IndependentReviewPipeline,
    IndependentReviewAdmissionGate,
    StageClaimAuditor,
    JuliaJudgment,
)


@pytest.fixture
def live_context():
    return {
        "schema_version": "market-context.v1",
        "trade_date": "2026-08-06",
        "status": "live",
        "market_state": {"breadth": {"up_count": 3200}, "emotion": {"node": "REPAIR", "score": 18}},
        "themes": [
            {"subject": "创新药", "strength": 0.81, "derived_stage_signal": "acceleration", "capital_direction": "inflow", "leader_health": "strong", "breadth": "wide"},
            {"subject": "半导体设备", "strength": 0.62, "derived_stage_signal": "divergence", "capital_direction": "mixed", "leader_health": "weakening", "breadth": "contracting"},
        ],
        "quality": {"source_quality": 0.85},
    }


@pytest.fixture
def draft_review():
    return {
        "schema_version": "analyst-workbench.review.v1",
        "trade_date": "2026-08-06",
        "opinion_mode": "ai_draft",
        "claims": [
            {"claim_id": "claim_draft_001", "subject": {"type": "theme", "name": "创新药"}, "claim_type": "theme_stage", "stage_judgement": "acceleration", "attention_level": "CRITICAL", "confidence": 0.82, "analyst_reviewed": False},
            {"claim_id": "claim_draft_002", "subject": {"type": "theme", "name": "半导体设备"}, "claim_type": "theme_stage", "stage_judgement": "diffusion", "attention_level": "HIGH", "confidence": 0.62, "analyst_reviewed": False},
            {"claim_id": "claim_draft_003", "subject": {"type": "theme", "name": "未知题材"}, "claim_type": "theme_stage", "stage_judgement": "start", "confidence": 0.4, "analyst_reviewed": False},
        ],
        "approval": {"draft_version": 1},
    }


# ── Admission Gate ──────────────────────────────────────────────────────────

def test_admission_allows_valid_inputs(live_context, draft_review):
    gate = IndependentReviewAdmissionGate()
    ok, reason = gate.check(live_context, draft_review)
    assert ok, reason


def test_admission_blocks_date_mismatch(live_context):
    gate = IndependentReviewAdmissionGate()
    review = {"schema_version": "analyst-workbench.review.v1", "trade_date": "2026-08-05", "opinion_mode": "ai_draft"}
    ok, reason = gate.check(live_context, review)
    assert not ok
    assert "mismatch" in reason


def test_admission_blocks_unavailable_context():
    gate = IndependentReviewAdmissionGate()
    ctx = {"schema_version": "market-context.v1", "status": "unavailable", "trade_date": "2026-08-06"}
    ok, _ = gate.check(ctx, {"schema_version": "analyst-workbench.review.v1", "opinion_mode": "ai_draft"})
    assert not ok


def test_admission_blocks_synthetic_context():
    gate = IndependentReviewAdmissionGate()
    ctx = {"schema_version": "market-context.v1", "status": "synthetic", "trade_date": "2026-08-06"}
    ok, _ = gate.check(ctx, {"schema_version": "analyst-workbench.review.v1", "opinion_mode": "ai_draft"})
    assert not ok


def test_admission_blocks_not_ready_review(live_context):
    gate = IndependentReviewAdmissionGate()
    ok, _ = gate.check(live_context, {"schema_version": "analyst-workbench.review.v1", "opinion_mode": "not_ready"})
    assert not ok


# ── Stage Claim Auditor ─────────────────────────────────────────────────────

def test_stage_auditor_detects_mismatch():
    """Derived signal=divergence, claim=diffusion → contradicting."""
    auditor = StageClaimAuditor()
    facts = {"derived_stage_signal": "divergence", "strength": 0.62, "leader_health": "weakening", "breadth": "contracting"}
    claim = {"stage_judgement": "diffusion", "confidence": 0.62}
    sup, contra, miss = auditor.audit(claim, facts)
    assert any("signal_divergence" in c for c in contra)


def test_stage_auditor_confirms_match():
    """Derived signal=acceleration, claim=acceleration → aligned."""
    auditor = StageClaimAuditor()
    facts = {"derived_stage_signal": "acceleration", "strength": 0.81, "leader_health": "strong", "capital_direction": "inflow", "breadth": "wide"}
    claim = {"stage_judgement": "acceleration", "confidence": 0.82}
    sup, contra, miss = auditor.audit(claim, facts)
    assert any("signal_aligned" in s for s in sup)


# ── Independent Review ──────────────────────────────────────────────────────

def test_review_detects_stage_mismatch(live_context, draft_review):
    """半导体: derived=divergence, claim=diffusion → disagree."""
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(live_context, draft_review)
    assert result.status == "completed"
    semi = [j for j in result.judgments if "半导体" in j.subject][0]
    assert semi.verdict in ("disagree", "partially_disagree")


def test_review_agrees_on_stage_match(live_context, draft_review):
    """创新药: derived=acceleration, claim=acceleration → agree."""
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(live_context, draft_review)
    innovation = [j for j in result.judgments if "创新药" in j.subject][0]
    assert innovation.verdict in ("agree", "partially_agree")


def test_missing_fact_produces_insufficient_data(live_context, draft_review):
    """P0: 未知题材 has no facts → insufficient_data, NOT dropped."""
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(live_context, draft_review)
    unknown = [j for j in result.judgments if "未知题材" in j.subject]
    assert len(unknown) == 1
    assert unknown[0].verdict == "insufficient_data"
    assert "theme_fact_not_found" in unknown[0].missing_evidence


def test_blocked_review_has_no_judgments():
    """Admission gate blocked → no judgments, status=blocked."""
    pipeline = IndependentReviewPipeline()
    ctx = {"schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "unavailable", "quality": {"source_quality": 0}}
    result = pipeline.review(ctx, {"schema_version": "analyst-workbench.review.v1", "opinion_mode": "not_ready"})
    assert result.status == "blocked"
    assert result.judgments == []


def test_empty_data_is_graceful():
    pipeline = IndependentReviewPipeline()
    ctx = {"schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live", "themes": [], "market_state": {}, "quality": {"source_quality": 0.8}}
    rev = {"schema_version": "analyst-workbench.review.v1", "trade_date": "2026-08-06", "opinion_mode": "ai_draft", "claims": []}
    result = pipeline.review(ctx, rev)
    assert result.status == "completed"
    assert result.judgments == []


def test_opinion_provenance_preserved(live_context, draft_review):
    """Judgment preserves opinion_mode, claim_id, draft_version from source."""
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(live_context, draft_review)
    for j in result.judgments:
        wc = j.workbench_claim
        assert "opinion_provenance" in wc or "opinion_mode" in str(wc), \
            f"Judgment should carry opinion provenance"

def test_julia_stage_is_independent_not_just_consistent(live_context, draft_review):
    """Julia outputs her own stage assessment — even when agreeing."""
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(live_context, draft_review)
    for j in result.judgments:
        if j.verdict == "insufficient_data":
            assert j.julia_stage == "unknown"
        else:
            assert j.julia_stage != ""
            assert j.julia_stage != "consistent_with_workbench", (
                f"Julia must output independent stage for '{j.subject}', got '{j.julia_stage}'"
            )

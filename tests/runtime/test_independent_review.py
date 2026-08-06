"""Independent Review Pipeline Tests — ai_theme_app derived format.

Uses real raw_metrics + derived_signals format (not old flat fields).
"""

import pytest

from julia_core.reasoning.independent_review import (
    IndependentReviewPipeline,
    IndependentReviewAdmissionGate,
    StageInferenceEngine,
    StageClaimAuditor,
    ThemeFactContractMapper,
)


@pytest.fixture
def live_context():
    """Real ai_theme_app derived format: raw_metrics + derived_signals."""
    return {
        "schema_version": "market-context.v1",
        "trade_date": "2026-08-06",
        "status": "live",
        "themes": [
            {
                "subject": "创新药",
                "raw_metrics": {"mainline_strength_score": 0.81, "confidence_score": 0.86},
                "derived_signals": {
                    "stage_signal": {"value": "acceleration"},
                    "capital_direction": {"value": "inflow"},
                    "leader_health": {"value": "strong"},
                    "strong_stock_coverage": {"value": "wide"},
                },
            },
            {
                "subject": "半导体设备",
                "raw_metrics": {"mainline_strength_score": 0.62, "confidence_score": 0.55},
                "derived_signals": {
                    "stage_signal": {"value": "divergence"},
                    "capital_direction": {"value": "mixed"},
                    "leader_health": {"value": "weakening"},
                    "strong_stock_coverage": {"value": "contracting"},
                },
            },
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
            {"claim_id": "claim_d_001", "subject": {"type": "theme", "name": "创新药"}, "stage_judgement": "acceleration", "confidence": 0.82},
            {"claim_id": "claim_d_002", "subject": {"type": "theme", "name": "半导体设备"}, "stage_judgement": "diffusion", "confidence": 0.62},
            {"claim_id": "claim_d_003", "subject": {"type": "theme", "name": "未知题材"}, "stage_judgement": "start", "confidence": 0.4},
        ],
        "approval": {},
    }


@pytest.fixture
def approved_review():
    return {
        "schema_version": "analyst-workbench.review.v1",
        "trade_date": "2026-08-06",
        "opinion_mode": "analyst_approved",
        "claims": [
            {"claim_id": "claim_a_001", "subject": {"type": "theme", "name": "创新药"}, "stage_judgement": "acceleration", "confidence": 0.82},
        ],
        "approval": {"snapshot_version": 3, "snapshot_hash": "abc123"},
    }


@pytest.fixture
def rejected_review():
    return {
        "schema_version": "analyst-workbench.review.v1",
        "trade_date": "2026-08-06",
        "opinion_mode": "rejected",
        "validation_errors": ["hash_mismatch"],
        "claims": [],
        "approval": {},
    }


# ── Contract Mapper ───────────────────────────────────────────────────────

def test_mapper_converts_derived_to_flat():
    mapper = ThemeFactContractMapper()
    ai_format = {
        "subject": "测试",
        "raw_metrics": {"mainline_strength_score": 0.75},
        "derived_signals": {
            "stage_signal": {"value": "diffusion"},
            "capital_direction": {"value": "inflow"},
            "leader_health": {"value": "strong"},
            "strong_stock_coverage": {"value": "wide"},
        },
    }
    flat = mapper.map(ai_format)
    assert flat["strength"] == 0.75
    assert flat["derived_stage_signal"] == "diffusion"
    assert flat["capital_direction"] == "inflow"
    assert flat["leader_health"] == "strong"
    assert flat["breadth"] == "wide"


def test_mapper_preserves_null():
    mapper = ThemeFactContractMapper()
    ai_format = {
        "subject": "空缺",
        "raw_metrics": {},
        "derived_signals": {
            "stage_signal": None,
            "capital_direction": None,
            "leader_health": None,
            "strong_stock_coverage": None,
        },
    }
    flat = mapper.map(ai_format)
    assert flat["strength"] is None
    assert flat["capital_direction"] is None


# ── Blind Stage Inference ─────────────────────────────────────────────────

def test_inference_blind_to_claim():
    """StageInferenceEngine does NOT receive workbench claim."""
    engine = StageInferenceEngine()
    facts = {"strength": 0.81, "leader_health": "strong", "breadth": "wide", "capital_direction": "inflow"}
    stage, evidence = engine.infer(facts)
    assert stage == "acceleration"
    # Source code must not reference "claim" or "judgement"
    import inspect
    src = inspect.getsource(engine.infer)
    assert "claim" not in src.lower()
    assert "judgment" not in src.lower()
    assert "workbench" not in src.lower()


def test_inference_detects_divergence():
    engine = StageInferenceEngine()
    facts = {"leader_health": "weakening", "breadth": "contracting"}
    stage, _ = engine.infer(facts)
    assert stage == "divergence"


# ── Admission Gate ────────────────────────────────────────────────────────

def test_rejected_is_blocked(rejected_review):
    gate = IndependentReviewAdmissionGate()
    ctx = {"schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live", "quality": {"source_quality": 0.8}}
    ok, reason = gate.check(ctx, rejected_review)
    assert not ok
    assert "rejected" in reason


# ── Independent Review ────────────────────────────────────────────────────

def test_real_format_review_produces_judgments(live_context, draft_review):
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(live_context, draft_review)
    assert result.status in ("completed", "partial")
    assert len(result.judgments) == 3

    # 创新药: strong → acceleration, claim=acceleration → agree
    innovation = [j for j in result.judgments if "创新药" in j.subject][0]
    assert innovation.verdict in ("agree", "partially_agree")
    assert innovation.julia_stage != ""

    # 半导体: weakening+contracting → Julia says divergence, claim says diffusion → disagree
    semi = [j for j in result.judgments if "半导体" in j.subject][0]
    assert semi.verdict in ("disagree", "partially_disagree")


def test_insufficient_data_for_missing_fact(live_context, draft_review):
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(live_context, draft_review)
    unknown = [j for j in result.judgments if "未知题材" in j.subject]
    assert len(unknown) == 1
    assert unknown[0].verdict == "insufficient_data"


def test_approved_has_analyst_reviewed_true(approved_review):
    """P0: approved claim → analyst_reviewed=True."""
    ctx = {"schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live",
           "themes": [{"subject": "创新药", "raw_metrics": {"mainline_strength_score": 0.81},
                       "derived_signals": {"stage_signal": {"value": "acceleration"},
                                           "capital_direction": {"value": "inflow"},
                                           "leader_health": {"value": "strong"},
                                           "strong_stock_coverage": {"value": "wide"}}}],
           "quality": {"source_quality": 0.8}}
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(ctx, approved_review)
    j = result.judgments[0]
    assert j.workbench_claim["opinion_provenance"]["analyst_reviewed"] is True
    assert j.workbench_claim["opinion_provenance"]["snapshot_version"] == 3


def test_opinion_provenance_preserved(live_context, draft_review):
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(live_context, draft_review)
    for j in result.judgments:
        assert "opinion_provenance" in j.workbench_claim
        assert "opinion_mode" in j.workbench_claim["opinion_provenance"]


def test_null_not_converted_to_zero():
    """P0: null strength stays None, not 0."""
    ctx = {"schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live",
           "themes": [{"subject": "数据缺失股", "raw_metrics": {},
                       "derived_signals": {"stage_signal": None,
                                           "capital_direction": None,
                                           "leader_health": None,
                                           "strong_stock_coverage": None}}],
           "quality": {"source_quality": 0.8}}
    rev = {"schema_version": "analyst-workbench.review.v1", "trade_date": "2026-08-06",
           "opinion_mode": "ai_draft",
           "claims": [{"subject": {"name": "数据缺失股"}, "stage_judgement": "start", "confidence": 0.3}],
           "approval": {}}
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(ctx, rev)
    j = result.judgments[0]
    # Should have missing evidence (not evaluated as strength=0)
    assert j.missing_evidence, "Should have missing_evidence for null fields"
    # Should NOT be classified as "agree" with strength=0 interpreted as start
    assert j.verdict in ("insufficient_data", "partially_disagree", "disagree")


def test_empty_context_blocked(live_context):
    ctx = {"schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "unavailable", "quality": {"source_quality": 0}}
    rev = {"schema_version": "analyst-workbench.review.v1", "opinion_mode": "ai_draft"}
    result = IndependentReviewPipeline().review(ctx, rev)
    assert result.status == "blocked"

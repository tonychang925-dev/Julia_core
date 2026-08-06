"""Independent Review Pipeline Tests.

Dual-input architecture: market facts + workbench judgments → Julia's assessment.

Run:
  python -m pytest tests/runtime/test_independent_review.py -v
"""

import pytest

from julia_core.reasoning.independent_review import (
    ClaimEvidence,
    JuliaJudgment,
    IndependentReviewResult,
    EvidenceExtractor,
    IndependentReviewPipeline,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def market_context():
    """Simulated market.context.snapshot output."""
    return {
        "schema_version": "market-context.v1",
        "trade_date": "2026-08-06",
        "market_state": {
            "breadth": {"up_count": 3200, "down_count": 1800},
            "emotion": {"node": "REPAIR", "score": 18},
        },
        "themes": [
            {
                "subject": "创新药",
                "strength": 0.81,
                "stage": "acceleration",
                "capital_direction": "inflow",
                "leader_health": "strong",
                "breadth": "wide",
            },
            {
                "subject": "半导体设备",
                "strength": 0.62,
                "stage": "diffusion",
                "capital_direction": "mixed",
                "leader_health": "weakening",
                "breadth": "contracting",
            },
        ],
    }


@pytest.fixture
def workbench_review():
    """Simulated market.workbench.review output."""
    return {
        "schema_version": "analyst-workbench.review.v1",
        "trade_date": "2026-08-06",
        "market_judgment": {
            "phase": "REPAIR",
            "risk_level": "MEDIUM",
        },
        "theme_judgments": [
            {
                "subject": "创新药",
                "attention_level": "CRITICAL",
                "stage_judgment": "acceleration",
                "strategy_bias": "持有核心",
                "confidence": 0.82,
                "rationale": "资金流入、龙头健康",
            },
            {
                "subject": "半导体设备",
                "attention_level": "HIGH",
                "stage_judgment": "diffusion",
                "strategy_bias": "谨慎持有",
                "confidence": 0.62,
                "rationale": "龙头走弱",
            },
        ],
    }


# ── Evidence Extraction ─────────────────────────────────────────────────────

def test_evidence_extractor_finds_supporting(market_context, workbench_review):
    """Strong theme with matching facts → supporting evidence found."""
    extractor = EvidenceExtractor()
    claims = extractor.extract(market_context, workbench_review)

    innovation = [c for c in claims if "创新药" in c.claim][0]
    assert len(innovation.supporting_evidence) >= 2  # inflow + strong leader + wide breadth
    assert len(innovation.contradicting_evidence) == 0


def test_evidence_extractor_finds_contradicting(market_context, workbench_review):
    """Theme with weakening signals → contradicting evidence found."""
    extractor = EvidenceExtractor()
    claims = extractor.extract(market_context, workbench_review)

    semi = [c for c in claims if "半导体" in c.claim][0]
    # leader_weakening + breadth_contracting are present
    assert len(semi.contradicting_evidence) >= 1


def test_evidence_extractor_identifies_missing(market_context, workbench_review):
    """Missing/unclear signals → missing_evidence populated."""
    extractor = EvidenceExtractor()
    claims = extractor.extract(market_context, workbench_review)

    semi = [c for c in claims if "半导体" in c.claim][0]
    # "mixed" capital direction → "unclear_capital_direction"
    assert len(semi.missing_evidence) >= 1


# ── Independent Review ───────────────────────────────────────────────────────

def test_pipeline_agrees_with_strong_support(market_context, workbench_review):
    """Strong supporting evidence, no contradictions → agree."""
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(market_context, workbench_review)

    innovation = [j for j in result.judgments if "创新药" in j.subject][0]
    assert innovation.verdict in ("agree", "partially_agree")
    assert innovation.confidence >= 0.5


def test_pipeline_disagrees_with_contradictions(market_context, workbench_review):
    """Contradicting evidence → disagree or partially_disagree."""
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(market_context, workbench_review)

    semi = [j for j in result.judgments if "半导体" in j.subject][0]
    assert semi.verdict in ("partially_disagree", "disagree")
    assert semi.contradicting_evidence
    assert semi.rationale != ""


def test_pipeline_produces_expected_outcomes(market_context, workbench_review):
    """Every judgment has at least one expected outcome for verification."""
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(market_context, workbench_review)

    for judgment in result.judgments:
        assert len(judgment.expected_outcomes) >= 1, (
            f"Judgment for {judgment.subject} has no expected outcomes"
        )
        for outcome in judgment.expected_outcomes:
            assert "window" in outcome
            assert "condition" in outcome


def test_pipeline_agreement_ratio(market_context, workbench_review):
    """Agreement ratio correctly reflects agree/disagree distribution."""
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(market_context, workbench_review)

    assert 0.0 <= result.agreement_ratio <= 1.0
    assert result.overall_assessment != ""


def test_pipeline_handles_empty_data():
    """Empty context and review → graceful empty result."""
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(
        {"themes": [], "market_state": {}},
        {"theme_judgments": [], "market_judgment": {}},
    )
    assert result.judgments == []
    assert result.overall_assessment != ""
    assert result.agreement_ratio == 0.0


# ── Judgment Model ───────────────────────────────────────────────────────────

def test_judgment_has_required_fields():
    """JuliaJudgment contains all fields needed for M7 feedback."""
    judgment = JuliaJudgment(
        subject="test_theme",
        verdict="partially_disagree",
        stage_assessment="late_acceleration_to_divergence",
        confidence=0.71,
        supporting_evidence=["e1", "e2"],
        contradicting_evidence=["c1", "c2"],
        missing_evidence=["m1"],
    )
    assert judgment.judgment_id != ""
    assert judgment.subject == "test_theme"
    assert judgment.verdict == "partially_disagree"
    assert len(judgment.supporting_evidence) == 2
    assert len(judgment.contradicting_evidence) == 2
    assert len(judgment.missing_evidence) == 1
    assert judgment.created_at != ""


# ── Verdict types coverage ───────────────────────────────────────────────────

def test_all_verdict_types_possible(market_context, workbench_review):
    """Pipeline can produce agree, partially_agree, partially_disagree, disagree."""
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(market_context, workbench_review)

    verdicts = {j.verdict for j in result.judgments}
    assert len(verdicts) >= 2, f"Expected diverse verdicts, got: {verdicts}"
    valid = {"agree", "partially_agree", "partially_disagree", "disagree", "insufficient_data"}
    assert verdicts.issubset(valid), f"Invalid verdicts: {verdicts - valid}"

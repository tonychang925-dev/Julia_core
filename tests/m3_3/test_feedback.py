"""M3.3 Experience Feedback Acceptance Tests — AC-M3.3-1 through AC-M3.3-5.

ADR-031: Governed experience evolution — Prediction → Outcome → Update.

Run:
  python -m pytest tests/m3_3/test_feedback.py -v
"""

import pytest

from julia_core.experience.feedback_models import (
    PredictionRecord,
    RealityOutcome,
    ExperienceUpdate,
)
from julia_core.experience.feedback import (
    OutcomeBinder,
    DeviationAnalyzer,
    FeedbackPipeline,
)


# ── AC-M3.3-1: Prediction Trace ─────────────────────────────────────────────

def test_prediction_links_to_observation():
    """Every prediction carries observation_id for traceability."""
    pred = PredictionRecord(
        prediction_id="pred_001",
        observation_id="obs_123",
        hypothesis="AI机器人主题进入扩散阶段",
        confidence=0.82,
        source="ai_theme_app",
    )
    assert pred.observation_id != ""
    assert pred.prediction_id != ""
    assert pred.source != ""


# ── AC-M3.3-2: Outcome Binding ─────────────────────────────────────────────

def test_binder_accepts_valid_binding():
    """Outcome with matching prediction_id binds successfully."""
    binder = OutcomeBinder()
    pred = PredictionRecord(prediction_id="pred_001", confidence=0.8, source="test")
    outcome = RealityOutcome(prediction_id="pred_001", actual_result="confirmed")

    bound, reason = binder.bind(outcome, pred)
    assert bound, reason


def test_binder_rejects_mismatched_prediction_id():
    """Mismatched prediction_id → rejected."""
    binder = OutcomeBinder()
    pred = PredictionRecord(prediction_id="pred_001", confidence=0.8, source="test")
    outcome = RealityOutcome(prediction_id="pred_002", actual_result="confirmed")

    bound, reason = binder.bind(outcome, pred)
    assert bound is False
    assert "mismatch" in reason


def test_binder_rejects_outcome_without_prediction_id():
    """Outcome with no prediction_id → rejected."""
    binder = OutcomeBinder()
    pred = PredictionRecord(prediction_id="pred_001", confidence=0.8, source="test")
    outcome = RealityOutcome(prediction_id="", actual_result="confirmed")

    bound, reason = binder.bind(outcome, pred)
    assert bound is False
    assert "no prediction_id" in reason


# ── AC-M3.3-3: Deviation Measurement ────────────────────────────────────────

def test_deviation_confirmed_produces_positive_delta():
    """Confirmed outcome → positive confidence delta."""
    analyzer = DeviationAnalyzer()
    pred = PredictionRecord(prediction_id="pred_001", confidence=0.82, source="test")
    outcome = RealityOutcome(prediction_id="pred_001", actual_result="confirmed")

    delta = analyzer.analyze(pred, outcome)
    assert delta["result"] == "confirmed"
    assert delta["confidence_delta"] > 0


def test_deviation_disconfirmed_produces_negative_delta():
    """Disconfirmed outcome → negative confidence delta."""
    analyzer = DeviationAnalyzer()
    pred = PredictionRecord(prediction_id="pred_001", confidence=0.82, source="test")
    outcome = RealityOutcome(prediction_id="pred_001", actual_result="disconfirmed")

    delta = analyzer.analyze(pred, outcome)
    assert delta["result"] == "disconfirmed"
    assert delta["confidence_delta"] < 0


# ── AC-M3.3-4: Controlled Experience Mutation ──────────────────────────────

def test_feedback_pipeline_admits_high_confidence():
    """High confidence prediction → admitted experience update."""
    pipeline = FeedbackPipeline()
    pred = PredictionRecord(
        prediction_id="pred_001", observation_id="obs_123",
        hypothesis="AI机器人主题扩散", confidence=0.85,
        source="ai_theme_app",
    )
    outcome = RealityOutcome(prediction_id="pred_001", actual_result="confirmed")

    update = pipeline.process(pred, outcome)
    assert update is not None
    assert update.admitted is True
    assert update.delta > 0


def test_feedback_pipeline_rejects_low_confidence():
    """Low confidence prediction → rejected (below admission threshold)."""
    pipeline = FeedbackPipeline()
    pred = PredictionRecord(
        prediction_id="pred_001", confidence=0.5,  # below min_confidence=0.7
        source="test",
    )
    outcome = RealityOutcome(prediction_id="pred_001", actual_result="confirmed")

    update = pipeline.process(pred, outcome, min_confidence=0.7)
    assert update is None, "Low confidence should not produce experience update"


def test_unlinked_outcome_produces_no_update():
    """Outcome without valid prediction binding → None."""
    pipeline = FeedbackPipeline()
    pred = PredictionRecord(prediction_id="pred_A", confidence=0.8, source="test")
    outcome = RealityOutcome(prediction_id="pred_B", actual_result="confirmed")

    update = pipeline.process(pred, outcome)
    assert update is None


# ── AC-M3.3-5: Timeline Complete ───────────────────────────────────────────

def test_full_feedback_timeline():
    """Observation → Prediction → Outcome → Update — full trace."""
    # Step 1: Prediction from observation
    pred = PredictionRecord(
        prediction_id="pred_full_001",
        observation_id="obs_full_123",
        hypothesis="半导体设备共振",
        confidence=0.88,
        expected_window="5 trading days",
        evidence_refs=("dec_001", "obs_123"),
        source="ai_theme_app",
    )

    # Step 2: Reality outcome (5 days later)
    outcome = RealityOutcome(
        prediction_id="pred_full_001",
        actual_result="confirmed",
        metrics={"theme_return": "+15%", "volume_confirmed": True},
    )

    # Step 3: Feedback
    pipeline = FeedbackPipeline()
    update = pipeline.process(pred, outcome)

    assert update is not None
    assert update.admitted is True

    # Step 4: Full trace
    assert update.prediction_id == pred.prediction_id
    assert update.outcome_id == outcome.outcome_id
    assert pred.observation_id == "obs_full_123"
    assert pred.prediction_id == "pred_full_001"

    # Complete chain: observation → prediction → outcome → update
    chain = [
        pred.observation_id,
        pred.prediction_id,
        outcome.outcome_id,
        update.update_id,
    ]
    assert all(link != "" for link in chain), f"Broken chain: {chain}"

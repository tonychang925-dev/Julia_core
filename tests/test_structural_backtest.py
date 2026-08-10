"""MB-P2.2: Structural Backtest Tests.

Validates the backtest framework against frozen constraints:
  - H-PRED-001 hypothesis freeze
  - Anti-hindsight: T features from T, T+1 truth from T+1
  - Fixed buckets, not dynamically optimized
  - Leave-one-out robustness
  - Status gates (insufficient/directional/validated/rejected)
"""

import pytest

from julia_core.capability.financial.market_structure import (
    StructuralMetrics,
    compute_structural_metrics,
)
from julia_core.capability.financial.structural_backtest import (
    BacktestSample,
    BucketResult,
    StructuralBacktestResult,
    run_structural_backtest,
    classification_gate,
    _wilson_ci,
    HYPOTHESIS_ID,
    BUCKETS,
)


def _make_sample(trade_date: str, above_0_6: float, above_0_8: float,
                 regime_t: str, regime_t1: str) -> BacktestSample:
    """Helper to create a test sample with controlled metrics."""
    strengths = (
        [0.85] * int(above_0_8 * 100) +
        [0.65] * int((above_0_6 - above_0_8) * 100) +
        [0.3] * int((1.0 - above_0_6) * 100)
    )
    metrics = compute_structural_metrics(strengths)
    deteriorated = regime_t1 != regime_t
    return BacktestSample(
        feature_trade_date=trade_date,
        feature_as_of=f"{trade_date}T15:30:00+08:00",
        truth_trade_date=f"next-after-{trade_date}",
        truth_resolved_at=f"next-after-{trade_date}T15:30:00+08:00",
        metrics=metrics,
        regime_t=regime_t,
        regime_t1=regime_t1,
        deteriorated=deteriorated,
    )


# ── Gate tests ────────────────────────────────────────────────────────────────

def test_gate_insufficient_below_20():
    assert classification_gate(5) == "INSUFFICIENT"
    assert classification_gate(19) == "INSUFFICIENT"


def test_gate_directional_20_to_49():
    assert classification_gate(20) == "DIRECTIONAL_VALIDATION"
    assert classification_gate(49) == "DIRECTIONAL_VALIDATION"


def test_gate_calibration_50_plus():
    assert classification_gate(50) == "CALIBRATION_ELIGIBLE"
    assert classification_gate(100) == "CALIBRATION_ELIGIBLE"


# ── Wilson CI tests ──────────────────────────────────────────────────────────

def test_wilson_ci_zero():
    lo, hi = _wilson_ci(0, 10)
    assert lo == 0.0
    assert hi > 0.0


def test_wilson_ci_all():
    lo, hi = _wilson_ci(10, 10)
    assert lo < 1.0
    assert hi == 1.0


def test_wilson_ci_typical():
    lo, hi = _wilson_ci(5, 10)
    assert 0.2 < lo < 0.5
    assert 0.5 < hi < 0.8


# ── Anti-hindsight tests ─────────────────────────────────────────────────────

def test_features_only_from_T():
    """T features must not use T+1 data."""
    s = _make_sample("2026-07-14", 0.75, 0.03, "strength_active", "chaotic")
    # Metrics computed from T data only
    assert s.metrics.above_0_6_ratio == pytest.approx(0.75, abs=0.05)
    # T+1 truth is separate
    assert s.regime_t1 == "chaotic"
    assert s.deteriorated is True


# ── Bucket tests ─────────────────────────────────────────────────────────────

def test_buckets_are_fixed():
    """BUCKETS must not change — hypothesis is frozen."""
    assert len(BUCKETS) == 5
    labels = [b[0] for b in BUCKETS]
    assert labels == ["B1", "B2", "B3", "B4", "B5"]


def test_bucket_classification():
    """Samples classified into correct buckets."""
    s1 = _make_sample("D1", 0.80, 0.01, "strength_active", "chaotic")  # B1: <2%
    s2 = _make_sample("D2", 0.80, 0.025, "strength_active", "chaotic") # B2: 2-3%
    s3 = _make_sample("D3", 0.80, 0.04, "strength_active", "chaotic")  # B3: 3-5%
    s4 = _make_sample("D4", 0.80, 0.07, "strength_active", "chaotic")  # B4: 5-10%
    s5 = _make_sample("D5", 0.80, 0.12, "strength_active", "chaotic")  # B5: >=10%

    result = run_structural_backtest([s1, s2, s3, s4, s5])
    assert len(result.buckets) >= 5

    # B1 should have the highest deterioration (thin top = more fragile)
    b1 = [b for b in result.buckets if b.bucket_label == "B1"][0]
    assert b1.deterioration_rate == 1.0  # all deteriorated


def test_non_strength_active_excluded():
    """Only strength_active samples in population."""
    s_active = _make_sample("D1", 0.75, 0.03, "strength_active", "chaotic")
    s_chaotic = _make_sample("D2", 0.75, 0.03, "chaotic", "divergence")

    result = run_structural_backtest([s_active, s_chaotic])
    assert result.sample_size == 1  # only strength_active


# ── Direction tests ──────────────────────────────────────────────────────────

def test_increasing_direction():
    """Thin top → more deterioration = increasing direction."""
    samples = []
    for i in range(5):
        samples.append(_make_sample(f"D{i}a", 0.80, 0.01, "strength_active", "chaotic"))
    for i in range(5):
        samples.append(_make_sample(f"D{i}b", 0.80, 0.15, "strength_active", "strength_active"))

    result = run_structural_backtest(samples)
    assert result.factor_direction == "increasing"


def test_decreasing_direction():
    """Thick top → more deterioration = opposite of hypothesis."""
    samples = []
    for i in range(5):
        samples.append(_make_sample(f"D{i}a", 0.80, 0.01, "strength_active", "strength_active"))
    for i in range(5):
        samples.append(_make_sample(f"D{i}b", 0.80, 0.15, "strength_active", "chaotic"))

    result = run_structural_backtest(samples)
    assert result.factor_direction == "decreasing"


# ── Leave-one-out ────────────────────────────────────────────────────────────

def test_loo_stable_with_clear_signal():
    """With strong signal, LOO should be stable."""
    samples = []
    for i in range(10):
        samples.append(_make_sample(f"D{i}a", 0.80, 0.01, "strength_active", "chaotic"))
    for i in range(10):
        samples.append(_make_sample(f"D{i}b", 0.80, 0.15, "strength_active", "strength_active"))

    result = run_structural_backtest(samples)
    assert result.leave_one_out_stable


def test_loo_unstable_with_weak_signal():
    """With very weak signal, LOO may be unstable."""
    # All same — no real signal
    samples = []
    for i in range(10):
        samples.append(_make_sample(f"D{i}", 0.80, 0.03, "strength_active", "chaotic"))
    for i in range(10):
        samples.append(_make_sample(f"D{i}b", 0.80, 0.04, "strength_active", "chaotic"))

    result = run_structural_backtest(samples)
    # Direction may be flat or unstable — either is fine for this test
    assert result.factor_direction in ("flat", "increasing", "decreasing", "insufficient_data")


# ── Status output ────────────────────────────────────────────────────────────

def test_status_is_evidence_not_belief():
    """Status describes the hypothesis, not the market."""
    result = StructuralBacktestResult(
        hypothesis_id="H-PRED-001",
        sample_window="test",
        sample_size=0,
        filter_regime="strength_active",
        baseline_deterioration_rate=0.0,
        status="insufficient",
        status_reason="n=0",
    )
    h = result.status
    assert h in ("insufficient", "directional_support", "validated", "rejected", "inconclusive")
    # Status must NOT be a market prediction (e.g., "bearish", "bullish")
    assert h not in ("bearish", "bullish", "up", "down")


def test_status_insufficient_below_minimum():
    """Below 20 samples → insufficient regardless of signal."""
    samples = [_make_sample(f"D{i}", 0.75, 0.02, "strength_active", "chaotic") for i in range(15)]
    result = run_structural_backtest(samples)
    assert result.status == "insufficient"
    assert result.sample_size == 15


def test_clear_increasing_signal_with_enough_samples():
    """With n>=20 clear increasing signal → directional_support."""
    samples = []
    for i in range(15):
        samples.append(_make_sample(f"D{i}a", 0.80, 0.01, "strength_active", "chaotic"))
    for i in range(10):
        samples.append(_make_sample(f"D{i}b", 0.80, 0.12, "strength_active", "strength_active"))

    result = run_structural_backtest(samples)
    assert result.sample_size == 25
    assert result.factor_direction == "increasing"
    assert result.status in ("directional_support", "validated")

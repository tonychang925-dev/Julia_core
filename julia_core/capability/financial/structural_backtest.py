"""MB-P2.2 Historical Structural Backtest — validate H-PRED-001.

Frozen hypothesis:
  H-PRED-001: strength_active with thin top-end (above_0_8_ratio)
  has elevated next-day regime deterioration risk.

Design constraints (from Tony's gate):
  - Hypothesis frozen BEFORE backtest — no post-hoc redefinition
  - Fixed buckets (B1-B5), not dynamically optimized
  - Anti-hindsight: T features from T only, T+1 truth from T+1 only
  - Two baselines: unconditional + breadth-only
  - Leave-one-out robustness check
  - Output is Evidence (C-00/C-08), not Julia's belief
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from julia_core.capability.financial.market_structure import (
    StructuralMetrics,
    compute_structural_metrics,
    CalibrationHypothesis,
)

CST = timezone(timedelta(hours=8))

# ── Frozen backtest configuration (do not tune after seeing results) ────────

HYPOTHESIS_ID = "H-PRED-001"
PRIMARY_FACTOR = "above_0_8_ratio"

# Fixed buckets — must not be adjusted post-hoc
BUCKETS = [
    ("B1", None, 0.02),      # <2%
    ("B2", 0.02, 0.03),      # 2-3%
    ("B3", 0.03, 0.05),      # 3-5%
    ("B4", 0.05, 0.10),      # 5-10%
    ("B5", 0.10, None),      # >=10%
]


@dataclass(frozen=True, slots=True)
class BacktestSample:
    """One historical observation: T features → T+1 truth."""

    feature_trade_date: str       # T — when features were observable
    feature_as_of: str            # T cutoff timestamp
    truth_trade_date: str         # T+1 — the next trading day
    truth_resolved_at: str        # when truth became known

    # Structural metrics at T
    metrics: StructuralMetrics

    # Regime at T (from market_context / snapshot)
    regime_t: str

    # Regime at T+1 (truth)
    regime_t1: str

    # Derived outcome
    deteriorated: bool       # regime_t1 != regime_t when regime_t is "strength_active"
    truth_known: bool = True # False when T+1 data unavailable (exclude from analysis)

    # Provenance
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BucketResult:
    """Aggregate statistics for one above_0_8_ratio bucket."""

    bucket_label: str
    min_ratio: float | None
    max_ratio: float | None

    sample_count: int
    deterioration_count: int
    deterioration_rate: float
    continuation_count: int
    continuation_rate: float

    # Confidence interval (Wilson score, 95%)
    ci_lower: float
    ci_upper: float

    avg_next_day_change: float = 0.0   # mean regime change magnitude


@dataclass(frozen=True, slots=True)
class StructuralBacktestResult:
    """Complete backtest result for one hypothesis.

    This is Evidence (C-08), not Julia's belief.
    Output status is about the hypothesis, not about the market.
    """

    hypothesis_id: str
    sample_window: str              # date range
    sample_size: int

    # Population: only dates with regime_t == filter_regime
    filter_regime: str

    # Baseline: unconditional deterioration rate
    baseline_deterioration_rate: float

    # Breadth-only baseline comparison
    breadth_only_lift: float = 0.0

    # Bucket analysis
    buckets: tuple[BucketResult, ...] = ()

    # Factor assessment
    factor_direction: str = ""      # "increasing" | "flat" | "decreasing"
    monotonicity_score: float = 0.0 # -1.0 to 1.0
    lift_vs_baseline: float = 0.0

    # Robustness
    leave_one_out_stable: bool = True
    direction_flips_without_extremes: bool = False

    # Conclusion
    status: str = "insufficient"    # insufficient | directional_support | validated | rejected | inconclusive
    status_reason: str = ""

    # Provenance
    generated_at: str = ""
    evidence_refs: tuple[str, ...] = ()


# ── Sample gate ──────────────────────────────────────────────────────────────

def classification_gate(sample_size: int) -> str:
    """Determine what the sample can support."""
    if sample_size < 20:
        return "INSUFFICIENT"
    elif sample_size < 50:
        return "DIRECTIONAL_VALIDATION"
    else:
        return "CALIBRATION_ELIGIBLE"


# ── Wilson score confidence interval ─────────────────────────────────────────

def _wilson_ci(success: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a proportion."""
    if total == 0:
        return (0.0, 0.0)
    p = success / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * ((p * (1 - p) + z * z / (4 * total)) / total) ** 0.5 / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


# ── Main backtest ────────────────────────────────────────────────────────────

def run_structural_backtest(
    samples: list[BacktestSample],
    filter_regime: str = "strength_active",
) -> StructuralBacktestResult:
    """Run H-PRED-001 backtest over historical samples.

    Only samples with regime_t == filter_regime are included in the analysis.
    Other regimes are excluded (the hypothesis is regime-conditioned).
    """
    gate = classification_gate(len(samples))

    # ── Filter to target regime, exclude unknown T+1 ─────────────────────
    population = [
        s for s in samples
        if s.regime_t == filter_regime and s.truth_known
    ]
    n = len(population)
    baseline_deterioration = (
        sum(1 for s in population if s.deteriorated) / n if n > 0 else 0.0
    )

    # ── Bucket analysis ──────────────────────────────────────────────────
    bucket_results: list[BucketResult] = []
    for label, lo, hi in BUCKETS:
        bucket = [
            s for s in population
            if (lo is None or s.metrics.above_0_8_ratio >= lo)
            and (hi is None or s.metrics.above_0_8_ratio < hi)
        ]
        bc = len(bucket)
        if bc == 0:
            continue
        det = sum(1 for s in bucket if s.deteriorated)
        rate = det / bc if bc > 0 else 0.0
        ci_low, ci_high = _wilson_ci(det, bc)
        bucket_results.append(BucketResult(
            bucket_label=label,
            min_ratio=lo,
            max_ratio=hi,
            sample_count=bc,
            deterioration_count=det,
            deterioration_rate=rate,
            continuation_count=bc - det,
            continuation_rate=1.0 - rate,
            ci_lower=ci_low,
            ci_upper=ci_high,
        ))

    # ── Direction + monotonicity ─────────────────────────────────────────
    rates = [
        (b.min_ratio or 0.0, b.deterioration_rate)
        for b in bucket_results
    ]
    if len(rates) >= 2:
        # Spearman-like: count pairwise inversions
        pairs = 0
        inversions = 0
        for i in range(len(rates)):
            for j in range(i + 1, len(rates)):
                pairs += 1
                if (rates[i][0] < rates[j][0]) != (rates[i][1] < rates[j][1]):
                    inversions += 1
        monotonicity = 1.0 - (2 * inversions / pairs) if pairs > 0 else 0.0
    else:
        monotonicity = 0.0

    # Direction: increasing (thin→high deterioration) or decreasing
    if len(rates) >= 2:
        first_rate = rates[0][1]   # thinnest bucket
        last_rate = rates[-1][1]   # deepest bucket
        if first_rate > last_rate * 1.2:
            direction = "increasing"  # thin = more deterioration ✅ predicted
        elif last_rate > first_rate * 1.2:
            direction = "decreasing"  # opposite of prediction
        else:
            direction = "flat"
    else:
        direction = "insufficient_data"

    # ── Lift vs baseline ─────────────────────────────────────────────────
    lift = 0.0
    if bucket_results and baseline_deterioration > 0:
        thinnest = bucket_results[0]
        lift = (thinnest.deterioration_rate - baseline_deterioration) / baseline_deterioration

    # ── Breadth-only baseline ────────────────────────────────────────────
    # Compare: does above_0_8_ratio add signal beyond above_0_6_ratio?
    # Split population by median above_0_6_ratio, compute deterioration for each half.
    breadth_lift = 0.0
    if n >= 10:
        sorted_by_breadth = sorted(population, key=lambda s: s.metrics.above_0_6_ratio)
        mid = n // 2
        low_breadth = sorted_by_breadth[:mid]
        high_breadth = sorted_by_breadth[mid:]
        low_det = sum(1 for s in low_breadth if s.deteriorated) / max(len(low_breadth), 1)
        high_det = sum(1 for s in high_breadth if s.deteriorated) / max(len(high_breadth), 1)
        # Breadth alone explains this much of the deterioration spread
        breadth_spread = abs(low_det - high_det)
        # Depth spread = extra signal beyond breadth
        if bucket_results:
            depth_spread = abs(
                bucket_results[0].deterioration_rate -
                bucket_results[-1].deterioration_rate
            ) if len(bucket_results) >= 2 else 0.0
            breadth_lift = depth_spread - breadth_spread  # positive = depth adds signal

    # ── Leave-one-out ────────────────────────────────────────────────────
    loo_stable = True
    if n >= 5:
        full_dir = direction
        for i in range(n):
            loo_pop = population[:i] + population[i + 1:]
            loo_det = sum(1 for s in loo_pop if s.deteriorated) / len(loo_pop) if loo_pop else 0
            loo_buckets = []
            for label, lo, hi in BUCKETS:
                lb = [s for s in loo_pop if (lo is None or s.metrics.above_0_8_ratio >= lo) and (hi is None or s.metrics.above_0_8_ratio < hi)]
                if lb:
                    loo_buckets.append(sum(1 for s in lb if s.deteriorated) / len(lb))
            if len(loo_buckets) >= 2:
                loo_dir = "increasing" if loo_buckets[0] > loo_buckets[-1] * 1.2 else "decreasing" if loo_buckets[-1] > loo_buckets[0] * 1.2 else "flat"
                if loo_dir != full_dir:
                    loo_stable = False
                    break

    # ── Status determination ─────────────────────────────────────────────
    status = "insufficient"
    reason = ""
    if n < 20:
        status = "insufficient"
        reason = f"n={n} < 20 minimum for directional validation"
    elif direction == "decreasing":
        status = "rejected"
        reason = "Direction opposite to hypothesis — thin top-end associated with LOWER deterioration"
    elif direction == "flat":
        status = "inconclusive"
        reason = "No directional relationship between thin top-end and deterioration"
    elif lift <= 0.05:
        status = "inconclusive"
        reason = f"Lift vs baseline ({lift:.1%}) too small to support hypothesis"
    elif not loo_stable:
        status = "directional_support"
        reason = "Direction supports hypothesis but not leave-one-out stable"
    elif n < 50:
        status = "directional_support"
        reason = f"Direction supports hypothesis (n={n}), monotonicity={monotonicity:.2f}, lift={lift:.1%}. Need n>=50 for calibration."
    else:
        status = "validated"
        reason = f"Hypothesis validated: direction={direction}, monotonicity={monotonicity:.2f}, lift={lift:.1%}, loo_stable=True"

    # ── Update hypothesis registry ───────────────────────────────────────
    CalibrationHypothesis.update(
        HYPOTHESIS_ID,
        sample_size=n,
        backtest_status=status,
        backtest_date=datetime.now(CST).isoformat(),
    )

    return StructuralBacktestResult(
        hypothesis_id=HYPOTHESIS_ID,
        sample_window=f"{population[0].feature_trade_date} to {population[-1].feature_trade_date}" if population else "N/A",
        sample_size=n,
        filter_regime=filter_regime,
        baseline_deterioration_rate=baseline_deterioration,
        breadth_only_lift=breadth_lift,
        buckets=tuple(bucket_results),
        factor_direction=direction,
        monotonicity_score=monotonicity,
        lift_vs_baseline=lift,
        leave_one_out_stable=loo_stable,
        status=status,
        status_reason=reason,
        generated_at=datetime.now(CST).isoformat(),
        direction_flips_without_extremes=False,
    )


# ── Sample extraction helpers ────────────────────────────────────────────────

def extract_samples_from_workbench(
    base_dir: str,
) -> list[BacktestSample]:
    """Extract historical samples using CANONICAL replay normalization.

    Uses canonical_replay.replay_snapshot() which normalizes
    mainline_strength_score / 64.0 (NOT /100.0).
    """
    import json
    import os

    from julia_core.capability.financial.canonical_replay import replay_snapshot

    base = base_dir
    date_dirs = sorted([
        d for d in os.listdir(base)
        if os.path.isdir(os.path.join(base, d))
        and d >= "2026-07-01"
        and not d.endswith(".bak")
    ])

    samples: list[BacktestSample] = []

    for i, d in enumerate(date_dirs):
        ctx_path = os.path.join(base, d, "draft_context.json")
        snap_path = os.path.join(base, d, "snapshot.json")

        if not os.path.exists(ctx_path):
            continue

        try:
            ctx = json.load(open(ctx_path))
            snap = json.load(open(snap_path)) if os.path.exists(snap_path) else None
        except Exception:
            continue

        # Use canonical replay for proper normalization (/64.0 not /100.0)
        replayed = replay_snapshot(ctx, snap, trade_date=d)
        themes = list(replayed.themes)
        if not themes:
            continue

        strengths = [t["raw_metrics"]["mainline_strength_score"] for t in themes]
        metrics = compute_structural_metrics(strengths)

        # Canonical regime from stage signals (not workbench emotion)
        stages = [t["derived_signals"]["stage_signal"]["value"] for t in themes]
        from collections import Counter
        stage_counts = Counter(stages)
        dominant = stage_counts.most_common(1)[0][0] if stage_counts else "unknown"
        canonical_regime = dominant

        # Use real as_of from source, not inferred
        as_of = replayed.as_of

        # Look up T+1 using same canonical replay
        regime_t1 = "unknown"
        truth_known = False
        if i + 1 < len(date_dirs):
            next_d = date_dirs[i + 1]
            next_ctx_path = os.path.join(base, next_d, "draft_context.json")
            next_snap_path = os.path.join(base, next_d, "snapshot.json")
            if os.path.exists(next_ctx_path):
                try:
                    next_ctx = json.load(open(next_ctx_path))
                    next_snap = json.load(open(next_snap_path)) if os.path.exists(next_snap_path) else None
                    next_replayed = replay_snapshot(next_ctx, next_snap, trade_date=next_d)
                    next_themes = list(next_replayed.themes)
                    next_stages = [t["derived_signals"]["stage_signal"]["value"] for t in next_themes]
                    next_counts = Counter(next_stages)
                    regime_t1 = next_counts.most_common(1)[0][0] if next_counts else "unknown"
                    truth_known = (regime_t1 != "unknown")
                except Exception:
                    pass

        deteriorated = (regime_t1 != canonical_regime) if truth_known else False

        sample = BacktestSample(
            feature_trade_date=d,
            feature_as_of=as_of,
            truth_trade_date=date_dirs[i + 1] if i + 1 < len(date_dirs) else "",
            truth_resolved_at=replayed.source_max_observed_at,
            metrics=metrics,
            regime_t=canonical_regime,
            regime_t1=regime_t1,
            deteriorated=deteriorated,
            truth_known=truth_known,
            source_refs=("draft_context.json", "snapshot.json"),
        )
        samples.append(sample)

    return samples


def _map_workbench_regime(emotion_node: str, emotion_score: float) -> str:
    """Map workbench emotion taxonomy to canonical regime.

    This is a PROVISIONAL mapping. The canonical taxonomy comes from
    StageTaxonomy in julia_core, which requires the full market_context
    format. Workbench emotion data is a temporary proxy.
    """
    mapping = {
        "CONTINUATION": "strength_active",
        "REBOUND": "strength_active",
        "DIVERGENCE": "divergence",
        "CHAOS": "chaotic",
        "ICE_POINT": "decline",
        "REPAIR": "strength_active",
    }
    return mapping.get(emotion_node, "unknown")


def _regime_equivalent_to_strength_active(emotion_node: str) -> bool:
    """Is this workbench emotion equivalent to strength_active?"""
    return emotion_node in ("CONTINUATION", "REBOUND", "REPAIR")


__all__ = [
    "BacktestSample",
    "BucketResult",
    "StructuralBacktestResult",
    "run_structural_backtest",
    "extract_samples_from_workbench",
    "classification_gate",
    "HYPOTHESIS_ID",
    "BUCKETS",
]

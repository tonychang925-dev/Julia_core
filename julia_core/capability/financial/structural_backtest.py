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

    # Derived outcome (H-PRED-001, SUPERSEDED)
    deteriorated: bool       # regime_t1 != regime_t when regime_t is "strength_active"

    # H-PRED-002 outcomes (canonical-native, no regime dependency)
    breadth_t1: float | None = None    # above_0_6_ratio at T+1
    lost_breadth: bool | None = None   # above_0_6_ratio_T+1 < 0.50
    breadth_delta: float | None = None # T+1 - T above_0_6_ratio delta

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
    # ── Filter to target regime, exclude unknown T+1 ─────────────────────
    population = [
        s for s in samples
        if s.regime_t == filter_regime and s.truth_known
    ]
    n = len(population)
    gate = classification_gate(n)  # R4: gate on hypothesis population, not total

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


# ── H-PRED-002: Breadth Fragility Backtest ───────────────────────────────────

H002_POPULATION_THRESHOLD = 0.50       # above_0_6_ratio >= this → "broad"
H002_THIN_THRESHOLD = 0.05             # above_0_8_ratio < this → "thin top-end"
H002_BREADTH_LOSS_THRESHOLD = 0.50     # T+1 below this → "lost breadth"


def run_breadth_fragility_backtest(
    samples: list[BacktestSample],
) -> StructuralBacktestResult:
    """Run H-PRED-002 backtest over historical samples.

    Population: above_0_6_ratio >= 0.50 (canonical broad participation).
    Factor: above_0_8_ratio buckets (thin → deep).
    Primary truth: above_0_6_ratio_T+1 < 0.50 (lost breadth).
    Secondary truth: Δ above_0_6_ratio (T+1 - T).

    No regime dependency. All inputs from canonical replay.
    """
    # ── Filter: broad participation, known T+1 ────────────────────────────
    population = [
        s for s in samples
        if s.metrics.above_0_6_ratio >= H002_POPULATION_THRESHOLD
        and s.truth_known
        and s.breadth_t1 is not None
    ]
    n = len(population)
    gate = classification_gate(n)

    # Baseline: unconditional loss-of-breadth rate among broad days
    loss_count = sum(1 for s in population if s.lost_breadth)
    baseline_loss_rate = loss_count / n if n > 0 else 0.0

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
        lost = sum(1 for s in bucket if s.lost_breadth)
        rate = lost / bc
        ci_low, ci_high = _wilson_ci(lost, bc)
        avg_delta = sum(s.breadth_delta for s in bucket if s.breadth_delta is not None) / bc if bc else 0.0
        bucket_results.append(BucketResult(
            bucket_label=label,
            min_ratio=lo,
            max_ratio=hi,
            sample_count=bc,
            deterioration_count=lost,
            deterioration_rate=rate,
            continuation_count=bc - lost,
            continuation_rate=1.0 - rate,
            ci_lower=ci_low,
            ci_upper=ci_high,
            avg_next_day_change=avg_delta,
        ))

    # ── B1-B5 dose-response monotonicity (secondary) ─────────────────────
    rates = [(b.min_ratio or 0.0, b.deterioration_rate) for b in bucket_results]
    if len(rates) >= 2:
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

    # ── Primary direction: THIN(<5%) vs NON_THIN(>=5%) ────────────────────
    thin = [s for s in population if s.metrics.above_0_8_ratio < H002_THIN_THRESHOLD]
    non_thin = [s for s in population if s.metrics.above_0_8_ratio >= H002_THIN_THRESHOLD]
    thin_loss = sum(1 for s in thin if s.lost_breadth) / max(len(thin), 1)
    non_thin_loss = sum(1 for s in non_thin if s.lost_breadth) / max(len(non_thin), 1)

    if len(thin) >= 4 and len(non_thin) >= 4:
        if thin_loss > non_thin_loss * 1.2:
            direction = "increasing"   # thin → more loss ✅ predicted
        elif non_thin_loss > thin_loss * 1.2:
            direction = "decreasing"   # opposite of prediction
        else:
            direction = "flat"
    else:
        direction = "insufficient_data"

    lift = (thin_loss - baseline_loss_rate) / baseline_loss_rate if baseline_loss_rate > 0 else 0.0

    # ── Secondary: breadth delta ──────────────────────────────────────────
    thin_delta = sum(s.breadth_delta for s in thin if s.breadth_delta is not None) / max(len(thin), 1)
    non_thin_delta = sum(s.breadth_delta for s in non_thin if s.breadth_delta is not None) / max(len(non_thin), 1)

    # ── Leave-one-out: same THIN vs NON_THIN estimand ─────────────────────
    loo_stable = True
    if n >= 5 and direction != "insufficient_data":
        full_effect_is_positive = thin_loss > non_thin_loss
        for i in range(n):
            loo_pop = population[:i] + population[i + 1:]
            loo_thin = [s for s in loo_pop if s.metrics.above_0_8_ratio < H002_THIN_THRESHOLD]
            loo_non = [s for s in loo_pop if s.metrics.above_0_8_ratio >= H002_THIN_THRESHOLD]
            if len(loo_thin) < 4 or len(loo_non) < 4:
                continue
            loo_tl = sum(1 for s in loo_thin if s.lost_breadth) / len(loo_thin)
            loo_ntl = sum(1 for s in loo_non if s.lost_breadth) / len(loo_non)
            loo_effect_is_positive = loo_tl > loo_ntl
            if loo_effect_is_positive != full_effect_is_positive:
                loo_stable = False
                break

    # ── Fixed breadth strata baseline (H-PRED-002 frozen) ─────────────────
    # Pre-registered strata — NOT data-driven. Prove depth adds signal
    # beyond raw breadth level, without letting the sample distribution
    # choose the strata boundaries.
    BREADTH_STRATA = [
        ("S1", 0.50, 0.60),
        ("S2", 0.60, 0.70),
        ("S3", 0.70, None),    # None = no upper bound — captures 1.0
    ]
    strata_results: dict[str, dict[str, Any]] = {}
    total_weighted_effect = 0.0
    total_weight = 0
    strata_sufficient_count = 0
    for s_label, s_lo, s_hi in BREADTH_STRATA:
        if s_hi is None:
            stratum = [s for s in population if s.metrics.above_0_6_ratio >= s_lo]
        else:
            stratum = [s for s in population if s_lo <= s.metrics.above_0_6_ratio < s_hi]
        if len(stratum) < 4:
            strata_results[s_label] = {"status": "insufficient_samples", "n": len(stratum)}
            continue
        s_thin = [s for s in stratum if s.metrics.above_0_8_ratio < H002_THIN_THRESHOLD]
        s_non = [s for s in stratum if s.metrics.above_0_8_ratio >= H002_THIN_THRESHOLD]
        if not s_thin or not s_non:
            strata_results[s_label] = {
                "n": len(stratum), "thin_n": len(s_thin), "non_thin_n": len(s_non),
                "status": "insufficient_comparison",
            }
            continue  # no effect estimate — fake 0% control arm
        s_tl = sum(1 for s in s_thin if s.lost_breadth) / len(s_thin)
        s_nt = sum(1 for s in s_non if s.lost_breadth) / len(s_non)
        effect = s_tl - s_nt
        strata_results[s_label] = {
            "n": len(stratum), "thin_n": len(s_thin), "non_thin_n": len(s_non),
            "thin_loss": s_tl, "non_thin_loss": s_nt, "effect": effect,
            "status": "sufficient",
        }
        total_weighted_effect += effect * len(stratum)
        total_weight += len(stratum)
        strata_sufficient_count += 1
    breadth_lift = total_weighted_effect / total_weight if total_weight > 0 else 0.0
    strata_sufficient = strata_sufficient_count >= 1

    # ── Status ────────────────────────────────────────────────────────────
    status = "insufficient"
    reason = ""
    if n < 20:
        status = "insufficient"
        reason = f"n={n} < 20 minimum for directional validation"
    elif direction == "decreasing":
        status = "rejected"
        reason = "Direction opposite to hypothesis — thin top-end associated with LOWER breadth loss"
    elif direction == "flat":
        status = "inconclusive"
        reason = "No directional relationship between thin top-end and breadth loss"
    elif direction == "insufficient_data":
        status = "insufficient"
        reason = (
            f"Primary exposure arms insufficient for directional comparison: "
            f"thin_n={len(thin)}, non_thin_n={len(non_thin)}"
        )
    elif direction != "increasing":
        # Safety: VALIDATED requires direction == "increasing"
        status = "inconclusive"
        reason = f"Unexpected direction={direction} — cannot validate"
    elif lift <= 0.05:
        status = "inconclusive"
        reason = f"Lift vs baseline ({lift:.1%}) too small to support hypothesis"
    elif not loo_stable:
        status = "directional_support"
        reason = f"Direction supports hypothesis but not leave-one-out stable (n={n})"
    elif n < 50:
        status = "directional_support"
        reason = f"Direction supports hypothesis (n={n}), monotonicity={monotonicity:.2f}, lift={lift:.1%}. Need n>=50 for calibration."
    elif not strata_sufficient:
        status = "directional_support"
        reason = f"Primary effect supports hypothesis but breadth-controlled strata insufficient for VALIDATED. n={n}, lift={lift:.1%}"
    elif breadth_lift <= 0:
        status = "inconclusive"
        reason = f"Primary effect positive but breadth-controlled effect reversed (breadth_lift={breadth_lift:.3f}). Depth may not add signal beyond breadth."
    else:
        status = "validated"
        reason = f"Hypothesis validated: thin_loss={thin_loss:.1%} vs non_thin_loss={non_thin_loss:.1%}, n={n}, breadth_lift={breadth_lift:.3f}"

    CalibrationHypothesis.update(
        "H-PRED-002",
        sample_size=n,
        backtest_status=status,
        thin_count=len(thin),
        non_thin_count=len(non_thin),
        thin_loss_rate=thin_loss,
        non_thin_loss_rate=non_thin_loss,
        thin_delta=thin_delta,
        non_thin_delta=non_thin_delta,
        backtest_date=datetime.now(CST).isoformat(),
    )

    return StructuralBacktestResult(
        hypothesis_id="H-PRED-002",
        sample_window=f"{population[0].feature_trade_date} to {population[-1].feature_trade_date}" if population else "N/A",
        sample_size=n,
        filter_regime=f"above_0_6_ratio >= {H002_POPULATION_THRESHOLD}",
        baseline_deterioration_rate=baseline_loss_rate,
        breadth_only_lift=breadth_lift,
        buckets=tuple(bucket_results),
        factor_direction=direction,
        monotonicity_score=monotonicity,
        lift_vs_baseline=lift,
        leave_one_out_stable=loo_stable,
        status=status,
        status_reason=reason,
        generated_at=datetime.now(CST).isoformat(),
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

        # H-PRED-002: breadth-based outcomes (canonical-native)
        breadth_t1_val = None
        lost_breadth_val = None
        breadth_delta_val = None
        if truth_known and i + 1 < len(date_dirs):
            try:
                next_d = date_dirs[i + 1]
                next_ctx = json.load(open(os.path.join(base, next_d, "draft_context.json")))
                next_snap = json.load(open(os.path.join(base, next_d, "snapshot.json"))) if os.path.exists(os.path.join(base, next_d, "snapshot.json")) else None
                next_replayed = replay_snapshot(next_ctx, next_snap, trade_date=next_d)
                next_strengths = [t["raw_metrics"]["mainline_strength_score"] for t in next_replayed.themes]
                next_metrics = compute_structural_metrics(next_strengths)
                breadth_t1_val = next_metrics.above_0_6_ratio
                lost_breadth_val = breadth_t1_val < 0.50
                breadth_delta_val = breadth_t1_val - metrics.above_0_6_ratio
            except Exception:
                pass

        sample = BacktestSample(
            feature_trade_date=d,
            feature_as_of=as_of,
            truth_trade_date=date_dirs[i + 1] if i + 1 < len(date_dirs) else "",
            truth_resolved_at=replayed.source_max_observed_at,
            metrics=metrics,
            regime_t=canonical_regime,
            regime_t1=regime_t1,
            deteriorated=deteriorated,
            breadth_t1=breadth_t1_val,
            lost_breadth=lost_breadth_val,
            breadth_delta=breadth_delta_val,
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

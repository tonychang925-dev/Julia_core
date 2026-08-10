# MB-P2.2a — Historical Canonical Replay Contract

**Status**: FROZEN 2026-08-10
**Scope**: Market Brain feature-level contract (not Core C-series)
**Parent**: C-08 Capability/Tool Contract, C-12 Evidence/Action/Trace Contract

## HR-01 — Historical Source Only

Replay uses historical source data only. No forward-looking information at T
may enter the feature calculation for T.

## HR-02 — Anti-Hindsight Cutoff

For every replayed snapshot at trade_date T with as_of cutoff C:
`source_max_observed_at <= as_of <= C`. Any source observation later than C
must not affect the replay.

## HR-03 — Canonical Scoring Semantics

Replay uses the same canonical scoring semantics as production snapshot
generation. Normalization (`mainline_strength_score / 64.0`), threshold
semantics (>= inclusive), and metric definitions are identical.

## HR-04 — Canonical Regime Taxonomy

Replay uses the same canonical regime taxonomy (`stage-taxonomy.v1`).
Workbench emotion taxonomy is not a regime input.

## HR-05 — Workbench Exclusion

Workbench opinions and emotion taxonomy are not canonical replay inputs.
They may exist as parallel EXPLORATORY proxy evidence only.

## HR-06 — Derived Deterministic Evidence

Replay artifacts are `DERIVED_DETERMINISTIC` Evidence (C-12), not
historical canonical records claiming to have existed at T.
`replayed_at` may be after `as_of`; `source_max_observed_at` must not.

## HR-07 — Generator Provenance

Every replay snapshot carries: `generator_version`, `scoring_version`,
`taxonomy_version`, `source_refs`, `source_max_observed_at`,
`snapshot_digest`, `replayed_at`.

## R2 — 7/14 Golden Parity Gate

Before any batch historical replay, the generator MUST reproduce
the frozen 2026-07-14 golden `market_context.json` within tolerance:

- `schema_version`: exact match
- `trade_date`: exact match
- `theme_count`: within 5%
- `score_match`: max diff <= 0.001
- `above_0_6_ratio`: abs diff < 0.02
- `above_0_8_ratio`: abs diff < 0.02
- `stage_signals`: >= 95% match

If parity fails, classify mismatch by taxonomy:
`SOURCE_GAP | SOURCE_REVISION | GENERATOR_DRIFT | TAXONOMY_DRIFT | SCORING_DRIFT | UNIVERSE_DRIFT | TIME_CUTOFF_DRIFT | UNKNOWN`

Do not adjust results to pass. Classify and report.

## R3 — Continuous Trading Calendar

Replay covers a continuous trading-date sequence, not cherry-picked dates.
`T+1` is `next_trading_day(T)`, not `next_available_directory()`.
Missing T+1 → truth_status=MISSING, sample excluded.

Feature source classes:
- `CANONICAL_GOLDEN` — frozen golden artifact
- `CANONICAL_REPLAY` — regenerated from historical raw data
- `WORKBENCH_PROXY` — exploratory only, not primary

Only CANONICAL_GOLDEN and CANONICAL_REPLAY enter `run_structural_backtest()`.

## Hypothesis Selection

**Hypothesis B (Current-Model Retrospective)**: All historical dates use the
same frozen generator/taxonomy/scoring version. The question is: if today's
Market Brain methodology had been applied historically, would the thin
top-end factor have had predictive value?

## Gate Sequence

```
R1 Contract FROZEN
  → R2 7/14 Parity PASS
    → R3 Continuous Calendar Replay (60-120+ trading days)
      → BacktestSample[] (CANONICAL_REPLAY only)
        → n < 20: INSUFFICIENT
        → 20-49: DIRECTIONAL_VALIDATION
        → >=50: CALIBRATION_ELIGIBLE
```

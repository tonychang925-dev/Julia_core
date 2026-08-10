"""MB-P2.2a-R3: Continuous Canonical Replay Dataset Generator.

Builds a blind replay dataset from raw workbench data. Produces:
  - ReplaySnapshot[] (canonical market_context regeneration)
  - T/T+1 BacktestSample[] (paired observations)
  - DatasetManifest (blind metadata only, NO aggregate statistics)

The manifest is safe to inspect — it reports coverage, not effects.
"""

from __future__ import annotations

import json
import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from julia_core.capability.financial.canonical_replay import (
    replay_snapshot,
    ReplaySnapshot,
    CANONICAL_SCORE_DIVISOR,
    GENERATOR_VERSION,
)
from julia_core.capability.financial.market_structure import (
    compute_structural_metrics,
)
from julia_core.capability.financial.structural_backtest import (
    BacktestSample,
)

CST = timezone(timedelta(hours=8))


@dataclass
class DatasetManifest:
    """Blind dataset metadata — NO aggregate statistics."""

    # Coverage
    raw_dates_available: int
    replay_successful: int
    replay_failed: int
    missing_source: int
    invalid_provenance: int

    # T/T+1 pairing
    valid_pairs: int
    missing_t1: int  # no T+1 data

    # Versions
    generator_version: str
    scoring_version: str = "v1"
    taxonomy_version: str = "stage-taxonomy.v1"

    # Study window
    primary_window_start: str = ""
    primary_window_end: str = ""
    primary_window_trading_days: int = 0
    extension_window_trading_days: int = 0

    # Digest
    dataset_digest: str = ""
    generated_at: str = ""

    def to_report(self) -> str:
        """Human-readable manifest report — safe to inspect pre-unblind."""
        lines = [
            "═" * 50,
            " R3 REPLAY DATASET MANIFEST (BLIND)",
            "═" * 50,
            "",
            "Coverage",
            f"  Raw dates available: {self.raw_dates_available}",
            f"  Replay successful:  {self.replay_successful}",
            f"  Replay failed:      {self.replay_failed}",
            f"  Missing source:     {self.missing_source}",
            f"  Invalid provenance: {self.invalid_provenance}",
            "",
            "T/T+1 Pairing",
            f"  Valid pairs:        {self.valid_pairs}",
            f"  Missing T+1:        {self.missing_t1}",
            "",
            "Versions",
            f"  Generator:  {self.generator_version}",
            f"  Scoring:    {self.scoring_version}",
            f"  Taxonomy:   {self.taxonomy_version}",
            "",
            "Study Window",
            f"  Primary:    {self.primary_window_start} → {self.primary_window_end}",
            f"  Days:       {self.primary_window_trading_days}",
            "",
            "Digest",
            f"  {self.dataset_digest}",
            "",
            "Status: BLIND — suitable for R3 gate review.",
            "        Aggregate statistics WILL NOT BE COMPUTED.",
        ]
        return "\n".join(lines)


def generate_replay_dataset(
    raw_data_dir: str,
    *,
    study_window_start: str = "",
    study_window_end: str = "",
) -> tuple[list[ReplaySnapshot], list[BacktestSample], DatasetManifest]:
    """Generate canonical replay snapshots from raw workbench data.

    R3.1: TradingCalendar is T+1 authority. T+1 = next_trading_day(T),
    NOT next_available_directory(). Enforces HR-02 anti-hindsight.

    Does NOT run any aggregate analysis. Produces blind manifest only.
    """
    from julia_core.capability.financial.trading_calendar import (
        next_trading_day,
        trading_days_between,
    )

    base = raw_data_dir
    # R3.1: discover ALL available raw date dirs, not hardcoded >= 2026-07-01
    all_date_dirs = sorted([
        d for d in os.listdir(base)
        if os.path.isdir(os.path.join(base, d))
        and not d.endswith(".bak")
        and len(d) >= 10  # plausible YYYY-MM-DD
    ])

    # Apply study window filter if set
    if study_window_start:
        all_date_dirs = [d for d in all_date_dirs if d >= study_window_start]
    if study_window_end:
        all_date_dirs = [d for d in all_date_dirs if d <= study_window_end]

    date_dirs = all_date_dirs

    # Expected trading days in window
    calendar_dates: list[str] = []
    calendar_missing: list[str] = []
    if study_window_start and study_window_end:
        sw_start = date.fromisoformat(study_window_start)
        sw_end = date.fromisoformat(study_window_end)
        for td in trading_days_between(sw_start, sw_end):
            d_str = td.isoformat()
            calendar_dates.append(d_str)
            if d_str not in set(date_dirs):
                calendar_missing.append(d_str)

    snapshots: list[ReplaySnapshot] = []
    failed_dates: list[str] = []
    missing_source: list[str] = []
    invalid_prov: list[str] = []

    for d in date_dirs:
        ctx_path = os.path.join(base, d, "draft_context.json")
        snap_path = os.path.join(base, d, "snapshot.json")

        if not os.path.exists(ctx_path):
            missing_source.append(d)
            continue

        try:
            ctx = json.loads(Path(ctx_path).read_text())
            snap = None
            if os.path.exists(snap_path):
                snap = json.loads(Path(snap_path).read_text())

            replayed = replay_snapshot(ctx, snap, trade_date=d)

            # HR-07: provenance must exist
            if not replayed.snapshot_digest:
                invalid_prov.append(d)
                continue

            # HR-02: anti-hindsight — source must not exceed as_of
            if replayed.source_max_observed_at and replayed.as_of:
                if replayed.source_max_observed_at > replayed.as_of:
                    invalid_prov.append(d)
                    continue

            snapshots.append(replayed)
        except Exception:
            failed_dates.append(d)

    # ── T/T+1 pairing (R3.1: TradingCalendar authority) ──────────────────
    snap_by_date = {s.trade_date: s for s in snapshots}
    samples: list[BacktestSample] = []

    for d in date_dirs:
        if d not in snap_by_date:
            continue

        s_t = snap_by_date[d]
        themes_t = list(s_t.themes)
        if not themes_t:
            continue

        strengths_t = [t["raw_metrics"]["mainline_strength_score"] for t in themes_t]
        metrics_t = compute_structural_metrics(strengths_t)

        from collections import Counter
        stages = [t["derived_signals"]["stage_signal"]["value"] for t in themes_t]
        regime_t = Counter(stages).most_common(1)[0][0] if stages else "unknown"

        # R3.1: T+1 = next_trading_day(D) — NOT next_available_directory
        t1_calendar = next_trading_day(date.fromisoformat(d))
        t1_date = t1_calendar.isoformat() if t1_calendar else None

        breadth_t1 = None
        lost_breadth = None
        breadth_delta = None
        truth_known = False
        regime_t1 = "unknown"

        # Only pair if exact T+1 has a replay snapshot
        if t1_date and t1_date in snap_by_date:
            s_t1 = snap_by_date[t1_date]
            themes_t1 = list(s_t1.themes)
            if themes_t1:
                strengths_t1 = [t["raw_metrics"]["mainline_strength_score"] for t in themes_t1]
                metrics_t1 = compute_structural_metrics(strengths_t1)
                breadth_t1 = metrics_t1.above_0_6_ratio
                lost_breadth = breadth_t1 < 0.50
                breadth_delta = breadth_t1 - metrics_t.above_0_6_ratio
                truth_known = True

                stages_t1 = [t["derived_signals"]["stage_signal"]["value"] for t in themes_t1]
                regime_t1 = Counter(stages_t1).most_common(1)[0][0] if stages_t1 else "unknown"

        sample = BacktestSample(
            feature_trade_date=d,
            feature_as_of=s_t.as_of,
            truth_trade_date=t1_date or "",
            # R3.1: truth_resolved_at from T+1 source, not T
            truth_resolved_at=s_t1.source_max_observed_at if (t1_date and t1_date in snap_by_date) else "",
            metrics=metrics_t,
            regime_t=regime_t,
            regime_t1=regime_t1,
            deteriorated=(regime_t1 != regime_t) if truth_known else False,
            breadth_t1=breadth_t1,
            lost_breadth=lost_breadth,
            breadth_delta=breadth_delta,
            truth_known=truth_known,
            source_refs=("draft_context.json", "snapshot.json"),
        )
        samples.append(sample)

    # ── Manifest ─────────────────────────────────────────────────────────
    digest_input = json.dumps({
        "dates": [s.trade_date for s in snapshots],
        "digests": [s.snapshot_digest for s in snapshots],
        "generator": GENERATOR_VERSION,
    }, sort_keys=True).encode()
    dataset_digest = hashlib.sha256(digest_input).hexdigest()

    exact_pairs = len([s for s in samples if s.truth_known])
    manifest = DatasetManifest(
        raw_dates_available=len(date_dirs),
        replay_successful=len(snapshots),
        replay_failed=len(failed_dates),
        missing_source=len(missing_source),
        invalid_provenance=len(invalid_prov),
        valid_pairs=exact_pairs,
        missing_t1=len([s for s in samples if not s.truth_known]),
        generator_version=GENERATOR_VERSION,
        primary_window_start=date_dirs[0] if date_dirs else "",
        primary_window_end=date_dirs[-1] if date_dirs else "",
        primary_window_trading_days=len(date_dirs),
        dataset_digest=dataset_digest,
        generated_at=datetime.now(CST).isoformat(),
    )

    return snapshots, samples, manifest


__all__ = [
    "DatasetManifest",
    "generate_replay_dataset",
]

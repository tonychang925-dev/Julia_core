"""MB-P2.2a-R2: 7/14 Golden Parity Tests.

HR-02: Every replay checkpoint must match frozen golden within tolerance.
"""

import json
import pytest
from pathlib import Path

from julia_core.capability.financial.canonical_replay import (
    replay_snapshot,
    verify_golden_parity,
    CANONICAL_SCORE_DIVISOR,
)

GOLDEN_DIR = Path("/Users/admin/Desktop/ai_theme_app/golden/2026-07-14")
WORKBENCH_DIR = Path("/Users/admin/Desktop/ai_theme_app/tmp/analyst_workbench/2026-07-14")


def _load_golden():
    return json.loads((GOLDEN_DIR / "market_context.json").read_text())


def _load_raw():
    ctx = json.loads((WORKBENCH_DIR / "draft_context.json").read_text())
    snap_path = WORKBENCH_DIR / "snapshot.json"
    snap = json.loads(snap_path.read_text()) if snap_path.exists() else None
    return ctx, snap


def test_golden_parity_all_checks_pass():
    """R2: Replayed 7/14 matches frozen golden on all dimensions."""
    ctx, snap = _load_raw()
    golden = _load_golden()

    replayed = replay_snapshot(ctx, snap, trade_date="2026-07-14")
    result = verify_golden_parity(replayed, golden)

    assert result.passed, f"Parity failed: {[c for c in result.checks if not c['pass']]}"


def test_schema_version_match():
    ctx, snap = _load_raw()
    golden = _load_golden()
    replayed = replay_snapshot(ctx, snap, trade_date="2026-07-14")
    assert replayed.schema_version == golden["schema_version"]


def test_trade_date_match():
    ctx, snap = _load_raw()
    golden = _load_golden()
    replayed = replay_snapshot(ctx, snap, trade_date="2026-07-14")
    assert replayed.trade_date == golden["trade_date"]


def test_theme_count_match():
    ctx, snap = _load_raw()
    golden = _load_golden()
    replayed = replay_snapshot(ctx, snap, trade_date="2026-07-14")
    assert len(replayed.themes) == len(golden["themes"])


def test_scores_exact_match():
    """Every replayed score must exactly match golden (HR-03)."""
    ctx, snap = _load_raw()
    golden = _load_golden()
    replayed = replay_snapshot(ctx, snap, trade_date="2026-07-14")

    replayed_scores = [t["raw_metrics"]["mainline_strength_score"] for t in replayed.themes]
    golden_scores = [t["raw_metrics"]["mainline_strength_score"] for t in golden["themes"]]

    for i, (r, g) in enumerate(zip(replayed_scores, golden_scores)):
        assert abs(r - g) <= 0.001, f"Theme {i}: replayed={r}, golden={g}"


def test_structural_metrics_match():
    """above_0.6_ratio and above_0.8_ratio must match golden within 0.02."""
    ctx, snap = _load_raw()
    golden = _load_golden()
    replayed = replay_snapshot(ctx, snap, trade_date="2026-07-14")

    rs = [t["raw_metrics"]["mainline_strength_score"] for t in replayed.themes]
    gs = [t["raw_metrics"]["mainline_strength_score"] for t in golden["themes"]]

    r_06 = sum(1 for s in rs if s >= 0.6) / len(rs)
    r_08 = sum(1 for s in rs if s >= 0.8) / len(rs)
    g_06 = sum(1 for s in gs if s >= 0.6) / len(gs)
    g_08 = sum(1 for s in gs if s >= 0.8) / len(gs)

    assert abs(r_06 - g_06) < 0.02
    assert abs(r_08 - g_08) < 0.02


def test_stage_signals_match():
    """At least 95% of stage signals must match golden."""
    ctx, snap = _load_raw()
    golden = _load_golden()
    replayed = replay_snapshot(ctx, snap, trade_date="2026-07-14")

    rs = [t["derived_signals"]["stage_signal"]["value"] for t in replayed.themes]
    gs = [t["derived_signals"].get("stage_signal", {}).get("value", "unknown") for t in golden["themes"]]

    matches = sum(1 for r, g in zip(rs, gs) if r == g)
    assert matches >= len(gs) * 0.95


def test_canonical_divisor_is_64():
    """HR-03: Normalization divisor must be 64.0."""
    assert CANONICAL_SCORE_DIVISOR == 64.0


def test_replay_has_provenance():
    """HR-07: Every replay carries generator provenance."""
    ctx, snap = _load_raw()
    replayed = replay_snapshot(ctx, snap, trade_date="2026-07-14")

    assert replayed.generator_version
    assert replayed.taxonomy_version
    assert replayed.scoring_version
    assert replayed.snapshot_digest
    assert replayed.replayed_at
    assert replayed.source_refs


def test_replay_marks_derived_not_original():
    """HR-06: replayed_at != as_of proves this is derived, not original."""
    ctx, snap = _load_raw()
    replayed = replay_snapshot(ctx, snap, trade_date="2026-07-14")

    # replayed_at is today, as_of is 2026-07-14 — they must differ
    assert replayed.replayed_at[:10] != replayed.as_of[:10], \
        "replayed_at should be today, as_of should be 2026-07-14"

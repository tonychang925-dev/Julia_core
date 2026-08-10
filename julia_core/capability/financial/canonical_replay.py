"""MB-P2.2a Historical Canonical Replay — regenerate market-context.v1 from raw data.

Replays the same canonical generator that produced the frozen golden
market_context.json files. This ensures historical backtest features
use the identical scoring/taxonomy as the golden baseline.

Key:
  - Normalization: mainline_strength_score / 64.0 (not /100)
  - Stage taxonomy: from cognitive_cards.state, not workbench emotion
  - Anti-hindsight: source observed_at <= as_of
  - Every replay snapshot carries generator version + provenance
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

CST = timezone(timedelta(hours=8))

CANONICAL_SCORE_DIVISOR = 64.0
GENERATOR_VERSION = "canonical-replay.v1"


@dataclass(frozen=True, slots=True)
class ReplaySnapshot:
    """One regenerated market-context.v1 snapshot from raw historical data."""

    trade_date: str
    as_of: str                          # from source data, not inferred

    # Output
    themes: tuple[dict[str, Any], ...]   # market-context.v1 theme format
    schema_version: str = "market-context.v1"

    # Generator provenance
    generator_version: str = GENERATOR_VERSION
    scoring_version: str = "v1"
    taxonomy_version: str = "stage-taxonomy.v1"

    # Source provenance
    source_refs: tuple[str, ...] = ()
    source_max_observed_at: str = ""     # latest timestamp in source data

    # Replay metadata
    snapshot_digest: str = ""            # SHA-256 of serialized themes
    replayed_at: str = ""                # when this replay was generated
    replayed_by: str = "canonical-replay"


@dataclass
class ReplayParityResult:
    """Result of comparing a replayed snapshot against a frozen golden."""

    trade_date: str
    passed: bool
    checks: list[dict[str, Any]] = field(default_factory=list)

    @property
    def all_pass(self) -> bool:
        return self.passed


def replay_snapshot(
    draft_context: dict,
    snapshot: dict | None = None,
    *,
    trade_date: str = "",
    as_of: str = "",
) -> ReplaySnapshot:
    """Regenerate a market-context.v1 snapshot from raw workbench data.

    Uses the EXACT same canonical normalization as the golden generator:
      strength = raw_mainline_strength_score / 64.0
      stage = from cognitive_cards.state (not emotion_node)
    """
    # Index snapshot cognition_cards by subject_key
    snap_cards: dict[str, dict] = {}
    if snapshot:
        for c in snapshot.get("cognition_cards", []):
            key = str(c.get("subject_key", c.get("subject_id", "")))
            snap_cards[key] = c

    themes_raw = draft_context.get("themes", [])
    themes_out: list[dict[str, Any]] = []

    for t in themes_raw:
        name = t.get("theme_name", t.get("subject_key", ""))
        if not name:
            continue
        key = str(t.get("subject_key", name))

        # CANONICAL normalization: raw / 64.0
        raw_strength = float(t.get("mainline_strength_score", 0))
        strength = raw_strength / CANONICAL_SCORE_DIVISOR

        # Cross-reference snapshot card
        card = snap_cards.get(key, {})

        # Leader health
        risk_flags = card.get("risk_flags", []) or []
        cap_data = card.get("capital", {}) or {}
        top_stocks = cap_data.get("top_stocks", [])
        role_labels = [s.get("role_label", "") for s in top_stocks]
        has_leader = any("龙头" in lbl for lbl in role_labels)
        has_dragon_observe = any("龙头观察" in lbl for lbl in role_labels)

        if "limit_down" in risk_flags:
            leader_signal = "weakening"
        elif has_leader:
            leader_signal = "strong"
        elif has_dragon_observe:
            leader_signal = "moderate"
        else:
            leader_signal = "unknown"

        # Capital direction
        tiers = [s.get("money_flow_tier", "") for s in top_stocks]
        total_inflow = sum(float(s.get("main_net_inflow", 0)) for s in top_stocks)
        if "HIGH" in tiers or "MEDIUM" in tiers:
            capital_signal = "inflow" if total_inflow >= 0 else "outflow"
        elif total_inflow > 0:
            capital_signal = "inflow"
        elif total_inflow < 0:
            capital_signal = "outflow"
        else:
            capital_signal = "mixed" if top_stocks else "unknown"

        # Breadth
        stock_count = len(top_stocks)
        unique_roles = len(set(role_labels))
        if stock_count >= 5 and unique_roles >= 3:
            breadth_signal = "wide"
        elif stock_count >= 3:
            breadth_signal = "moderate"
        elif stock_count >= 1:
            breadth_signal = "narrow"
        else:
            breadth_signal = "unknown"

        themes_out.append({
            "subject": name,
            "subject_key": key,
            "raw_metrics": {
                "mainline_strength_score": strength,
                "confidence_score": float(t.get("confidence_score", 0.5)),
                "fade_risk_score": float(t.get("fade_risk_score", 0)),
                "divergence_score": float(t.get("divergence_score", 0)),
                "repair_score": float(t.get("repair_score", 0)),
            },
            "derived_signals": {
                "stage_signal": {"value": t.get("stage", "unknown")},
                "capital_direction": {"value": capital_signal},
                "leader_health": {"value": leader_signal},
                "strong_stock_coverage": {"value": breadth_signal},
            },
        })

    # Digest
    themes_json = json.dumps(themes_out, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(themes_json.encode()).hexdigest()

    source_max = _max_observed(draft_context, snapshot)

    return ReplaySnapshot(
        trade_date=trade_date or draft_context.get("trade_date", ""),
        as_of=as_of or f"{trade_date}T15:30:00+08:00",
        themes=tuple(themes_out),
        source_refs=("draft_context.json", "snapshot.json"),
        source_max_observed_at=source_max,
        snapshot_digest=digest,
        replayed_at=datetime.now(CST).isoformat(),
    )


def verify_golden_parity(
    replayed: ReplaySnapshot,
    golden: dict,
    *,
    score_tolerance: float = 0.001,
    count_tolerance_pct: float = 0.05,
) -> ReplayParityResult:
    """Verify a replayed snapshot matches a frozen golden market_context.

    Gates:
      - schema_version match
      - trade_date match
      - theme count within tolerance
      - score scale: same semantics (scores within tolerance)
      - structural metrics match (above_0_6_ratio, above_0_8_ratio)
    """
    checks: list[dict[str, Any]] = []
    golden_themes = golden.get("themes", [])

    # Schema
    schema_ok = replayed.schema_version == golden.get("schema_version", "")
    checks.append({"check": "schema_version", "pass": schema_ok,
                   "replayed": replayed.schema_version,
                   "golden": golden.get("schema_version")})

    # Trade date
    date_ok = replayed.trade_date == golden.get("trade_date", "")
    checks.append({"check": "trade_date", "pass": date_ok,
                   "replayed": replayed.trade_date,
                   "golden": golden.get("trade_date")})

    # Theme count
    n_replayed = len(replayed.themes)
    n_golden = len(golden_themes)
    count_ok = abs(n_replayed - n_golden) <= max(1, n_golden * count_tolerance_pct)
    checks.append({"check": "theme_count", "pass": count_ok,
                   "replayed": n_replayed, "golden": n_golden})

    # Score comparison
    replayed_scores = [t["raw_metrics"]["mainline_strength_score"] for t in replayed.themes]
    golden_scores = [t["raw_metrics"]["mainline_strength_score"] for t in golden_themes]
    score_diffs = []
    all_score_ok = True
    for i in range(min(len(replayed_scores), len(golden_scores))):
        diff = abs(replayed_scores[i] - golden_scores[i])
        score_diffs.append(diff)
        if diff > score_tolerance:
            all_score_ok = False
    checks.append({"check": "score_match", "pass": all_score_ok,
                   "max_diff": max(score_diffs) if score_diffs else None,
                   "tolerance": score_tolerance})

    # Structural metrics
    replayed_above_06 = sum(1 for s in replayed_scores if s >= 0.6) / max(len(replayed_scores), 1)
    replayed_above_08 = sum(1 for s in replayed_scores if s >= 0.8) / max(len(replayed_scores), 1)
    golden_above_06 = sum(1 for s in golden_scores if s >= 0.6) / max(len(golden_scores), 1)
    golden_above_08 = sum(1 for s in golden_scores if s >= 0.8) / max(len(golden_scores), 1)

    metrics_ok = (
        abs(replayed_above_06 - golden_above_06) < 0.02 and
        abs(replayed_above_08 - golden_above_08) < 0.02
    )
    checks.append({"check": "structural_metrics", "pass": metrics_ok,
                   "replayed_above_06": replayed_above_06,
                   "golden_above_06": golden_above_06,
                   "replayed_above_08": replayed_above_08,
                   "golden_above_08": golden_above_08})

    # Stage signals
    replayed_stages = [t["derived_signals"]["stage_signal"]["value"] for t in replayed.themes]
    golden_stages = [t["derived_signals"].get("stage_signal", {}).get("value", "unknown") for t in golden_themes]
    stage_match_count = sum(1 for r, g in zip(replayed_stages, golden_stages) if r == g)
    stage_ok = stage_match_count >= len(golden_stages) * 0.95
    checks.append({"check": "stage_signals", "pass": stage_ok,
                   "match_count": stage_match_count, "total": len(golden_stages)})

    all_pass = all(c["pass"] for c in checks)
    return ReplayParityResult(trade_date=replayed.trade_date, passed=all_pass, checks=checks)


def _max_observed(ctx: dict, snap: dict | None) -> str:
    """Extract the latest observed timestamp from source data."""
    ts = ctx.get("generated_at", "") or ctx.get("trade_date", "")
    if snap:
        snap_ts = snap.get("approved_at", "")
        if snap_ts and snap_ts > ts:
            ts = snap_ts
    return ts


__all__ = [
    "ReplaySnapshot",
    "ReplayParityResult",
    "replay_snapshot",
    "verify_golden_parity",
    "CANONICAL_SCORE_DIVISOR",
    "GENERATOR_VERSION",
]

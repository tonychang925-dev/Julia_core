# 05 — DERIVED METRIC OWNERSHIP V2 (normative; no OPEN/TBD)

derived-ownership_version: market.derived-ownership.v2
Every value below is frozen as IN_WAVE1 (with formula) or NOT_IN_WAVE1. No "CAPABILITY_DERIVED + TBD".

## market.stock.history
IN_WAVE1 (normalization-derived; owner ai_theme_app; formulas fixed):
- pct_change = close_t/close_{t-1} - 1 (adjusted series when adjustment_mode != NONE); decimal precision per
  source policy recorded at implementation acceptance.
- amplitude = (high-low)/prev_close where prev_close>0 else row omitted from amplitude computation (field
  not emitted) — i.e., amplitude computed only when defined.
NOT_IN_WAVE1 (explicit): turnover-related values, moving averages, log/simple returns (only pct_change is
canonical), volume ratios / intraday_volume_vs_prev, total_return, max_drawdown_from_peak,
open_gap_vs_prev_close, key_level_status, limit_up_seal. These remain ai_theme_app domain-owned future
derived metrics; Wave-1 response does not contain them.

## market.theme.constituents
IN_WAVE1: none beyond the canonical membership rows (04). NOT_IN_WAVE1 (explicit): relative_strength_rank,
breadth_change, emerging_leaders, peer_limit_up_ratio, coverage — theme ranking/breadth/peer rules are not
Wave-1; their rule versions freeze when added as future derived capabilities.

Consumer (Julia/Strategy) never ad-hoc computes a NOT_IN_WAVE1 metric and labels it canonical; any future
addition requires its own contract addendum + owner approval.

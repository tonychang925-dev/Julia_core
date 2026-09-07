# 05 - DERIVED METRIC OWNERSHIP V3

derived_ownership_version: `market.derived-ownership.v3`
status: FROZEN_AS_GOVERNANCE
supersedes: `market.derived-ownership.v2`

Every listed value is frozen as `IN_WAVE1` or `NOT_IN_WAVE1`.

## market.stock.history

`IN_WAVE1`: none beyond source-normalized OHLCV response rows in `market.response.v3`.

`NOT_IN_WAVE1`: `pct_change`, `amplitude`, turnover-related values, moving averages, log returns, simple
returns, volume ratios, intraday volume comparisons, total return, max drawdown from peak, open gap versus
previous close, key level status, and limit-up seal.

`pct_change` and `amplitude` are not canonical Wave-1 fields. Future inclusion requires a contract version
bump that freezes field name, type, formula, adjustment semantics, null semantics, precision, rounding,
provenance, and rule version.

## market.theme.constituents

`IN_WAVE1`: none beyond canonical membership rows in `market.response.v3`.

`NOT_IN_WAVE1`: relative strength rank, breadth change, emerging leaders, peer limit-up ratio, coverage,
and theme ranking/breadth/peer metrics.

Consumer code must not compute a `NOT_IN_WAVE1` metric and label it canonical.

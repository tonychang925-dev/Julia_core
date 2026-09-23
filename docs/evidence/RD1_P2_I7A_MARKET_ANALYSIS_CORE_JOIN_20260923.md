# RD1 P2-I7A Market Analysis Core Join Evidence

## SHAs

- Core base: `6f8fe6487f3d6a3e25b5262135354ba35e0dfc18`
- Market canonical: `bc34e973686d7f78b0e9c3efd67b433f0901f21a`

## Real Market Binding Precheck

- Capability: `market.analysis.read`
- Request: `{"trade_date":"2026-07-09"}`
- Execution: PASS
- Operation status: `SUCCESS`
- Data state: `READY`
- Evidence count: 184
- Quality: `partial`, score `0.5`
- Missing modules: `engine_summary`, `daily_recap_essentials`, `mainline_states`, `limit_up_theme_events`, `new_high_summary`
- Source refs: `post_market_recap_snapshot:2026-07-09`, `daily_review_generate.full_truth_rebuild.fa111eb8`, `0750e71214c3`, `97b9a5d4cce7`
- Public object refs: `mes:2026-07-09:ccdbdbef4a76ef43`, `mkb:2026-07-09:6696c603df3b75d6`
- `calendar.next_trade_date`: present, value `2026-07-10`
- Watchlist evidence count: 140
- Setup evidence count: 40

The Market envelope remained structurally intact in Core. Market missing-module and partial-quality semantics were not upgraded or remapped.

## Real Julia Product E2E

- Exact query submitted through `CoreConversationIngress`.
- Base invocation policy verified unchanged:
  `market.stock.quote.read` / `600519.SH` / `2026-09-23`.
- Julia independently selected `market.analysis.read` with `{"trade_date":"2026-07-09"}`.
- Capability calls: 1
- ToolResults: 1
- Evidence: 1
- EvidenceFrame: present through C03 re-entry
- Research calls: 0
- Julia cognition calls: 2
- Julia produced a fresh second-pass judgment and explicitly preserved the partial-evidence and unavailable review-maturity boundaries without fabricating setup rationale or analyst approval.

## Gates

- Focused tests after narrow correction: `14 passed`
- `git diff --check`: PASS
- NCF: PASS (`P0_NEW=0`, `P1_NEW=0`, `P2_NEW=0`)

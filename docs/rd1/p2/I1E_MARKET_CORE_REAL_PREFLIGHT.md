# RD1-P2-I1E Market/Core Real Integration Preflight

## Scope

This is test/experiment-only composition evidence. It does not modify production code, merge candidates, deploy services, or authorize trading.

## Frozen Inputs

- Core repository: `tonychang925-dev/Julia_core`
- Core base/main: `52cacb1e7e61acc5c48335303df2c51db9f8dd5c`
- Accepted Core binding candidate: `71919611416ad8c440f8a2d06995947181d846f4`
- Market repository: `tonychang925-dev/ai_theme_app`
- Market base/main: `d183241dad266a50d9ad8b12d831734317edf7b7`
- Accepted Market public candidate: `0e6b599614842085e3f6cb505a0695ae5a80d1c3`

The runner verifies the two candidate objects in the explicitly supplied local repositories and imports only temporary `git archive` extractions of those exact commits. It does not check out or mutate either source repository.

## Composition

```text
RuntimeCapabilityBridge @ Core accepted SHA
  -> MarketPublicProviderAdapter @ Core accepted SHA
  -> recording composition wrapper
  -> MarketPublicFactory.create() @ Market accepted SHA
  -> real _MarketPublicProvider
  -> MarketResultEnvelope
  -> Core ToolResult structured_output
```

The recording wrapper only forwards arguments and preserves the returned envelope for truth comparison. It does not adapt, reinterpret, cache, retry, or replace Market behavior. The runner compares the accepted Core adapter's structural conversion of the real envelope with Core's final `structured_output`.

## Real Case Identities

- `market.event.resolve`: exact-date structured query `feed_date=2026-05-19`, `stock_id=null`, `limit=200`.
- `market.event.read`: the first decodable event identity selected only from the real `READY` resolve payload. The historical item `event:8410:9043089` remains documented as a source-bound candidate, but is not substituted when it is not visible to the exact public read path.
- `market.product.read`: `subject_key=9043089`, source-bound in Market accepted SHA at `evaluate_service/output/baselines/pm_e2e_phase47_final_100_20260519/sps_payload.json`.
- `market.product.linkage.read`: `subject_key=9043089`, `mapping_scope=all`, `include_leaders=true`, `limit=100`.
- `market.state.read`: exact `trade_date=2026-05-15`, matching the source-bound SPS payload trade date.

All selected primary requests are issued even when Market returns a real `UNAVAILABLE` envelope. A dependency limitation is recorded rather than converted into an empty or successful result.

## Semantic Invariants

- Market `FAILURE` remains Core execution `success` when a valid envelope exists.
- Market `EMPTY` remains `EMPTY`; it is not `UNAVAILABLE`.
- Market `UNAVAILABLE` remains `UNAVAILABLE`; it is not `EMPTY`.
- `STALE`, `PARTIAL`, and `NOT_APPLICABLE` retain their Market meanings.
- A provider exception before a valid envelope remains a Core execution error.
- No fallback provider or local Market implementation is used.
- Request IDs and correlation IDs are generated once and preserved through both boundaries.

## Linkage Projection Check

If real linkage data is `READY`, every payload row must contain only:

```text
subject_key
theme_id
theme_name
stock_id
stock_name
relation_type_candidate
mapping_scope
source_type
reason
remark
confidence
top
sort
stock_remark
```

`detail_html`, `price`, and `pct_chg` must be absent. The check is not downgraded to PASS when the rows are unavailable; the overall run remains blocked on the real dependency.

## Exact-State Check

For a `READY` `market.state.read`, the Market payload trade date/source identity must match `2026-05-15`. No latest-date substitution is allowed. Real `EMPTY` remains valid exact-date evidence.

## Isolated Negative Matrix

The runner separately exercises and records:

- missing Core Market provider binding (`provider_not_found`);
- C08 denial before provider invocation;
- pre-envelope provider exception as Core execution error;
- invalid request contract mismatch.

Only the invalid-request record uses the real Market provider in the primary run. The first three use explicitly classified isolated unit fixtures and are never counted as primary integration evidence.

## Truthful Outcome

- `REAL_INTEGRATION_PASS` requires all five real calls to produce valid envelopes, preserve semantics through Core, satisfy linkage/exact-date checks when READY, and avoid `UNAVAILABLE`.
- Real `READY` or `EMPTY` is acceptable when it is the correct Market domain result.
- Any real dependency/data `UNAVAILABLE` yields `BLOCKED_REAL_MARKET_DEPENDENCY`.
- A Core adapter/binding error or semantic mismatch yields `FAIL`, never a fabricated Market envelope.

No credentials or database DSNs are written to result artifacts.

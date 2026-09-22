# RD1 P1-I5 — Stock Quote Core Catalog Real Rerun

## Bases And Candidates

- Core base: `6b815cf3df58e6bfd3906b61ba5f918f11ef35c7`
- Assistant base: `ec20d4f2be6db09cfb63c8340777dcb1c76e4921`
- Market base: `5a38999623c2b9254865a37cbb3a7a7379d2a22e`
- Market candidate: `dfde53dc6066b36698ff4d73fae814f9b4571cb7`
- Market PR: `#410`

## Catalog Proof

- Core model-visible capability added: `market.stock.quote.read`
- Exact model-visible arguments:
  - `stock_id`: exact source-namespaced stock identifier, for example `600519.SH`
  - `trade_date`: exact `YYYY-MM-DD` trade date
- Core adapter loads only Market-exported `StockQuoteReadRequest`.
- No raw user-text routing, Market-private import, keyword router, or hard-coded `600519` selector was added.
- Existing Market definitions now expose their mechanically known exact input schemas in the CapabilityFrame.

## Real Rerun

- Query: `查一下 600519 今天的行情`
- Canonical Assistant route: HTTP `200`
- Core turn: HTTP `200`, status `completed`
- Real DeepSeek request count: `1`
- Assistant direct LLM call: `NO`
- Cognition pass count observed through provider calls: `1`
- Model structured tool-call output count: `0`
- Capability execution count: `0`
- Market call count: `0`
- Stock-quote call count: `0`
- Research call count: `0`
- ToolResult count: `0`
- Evidence count: `0`
- Evidence re-entry: `NO`
- Final response owner: Julia/Core
- Final response nonempty: `YES`

Julia's first-pass response explained that it did not have a reliable current date and asked the user for an exact date. It did not invoke the now-visible stock-quote capability.

Per the task's epistemic policy, `IterativeReasoningLoop`, deterministic routing, and external-evidence enforcement were not modified.

Disposition:

`BLOCKED_JULIA_EXTERNAL_EVIDENCE_POLICY_NOT_ENFORCED`

Raw sanitized execution log:
`/private/tmp/rd1_stock_quote_real_i5.json`

Model output SHA-256:
`98858c35ad33200930e8bb65c8c7931909ab99234697d82628950c852a018152`

## Verification

```text
PYTHONPATH=<market-candidate> /opt/miniconda3/bin/python -m pytest \
  tests/capability/test_rd1_generic_market_provider_binding.py \
  tests/public/test_rd1_market_public_composition_binding.py -q

36 passed in 0.31s
```

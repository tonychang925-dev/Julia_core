# RD1-L1-R9-D2C Atomic Frozen Rebind to Data-Conversion Closure Report

## Executive verdict

PASS. The controlled 18090 runtime now atomically uses Market D2B source closure `f0aae447654bc50100bc6a26a3e204fbdac6a707`. The clean-source recomputation, Core constants, launcher configuration, immutable release, provider source identity, trace identity, loaded adapter/DB modules, and readiness attestation all agree. No resolver query or Market read was executed.

## Source states

- Core base: `fce9be72a85629b4d3dc9b8265ba7b58b46ec832`
- Core source closure: `4109217269cf14dfc2dad6e17b2cdafb28d6f9cf`
- Market runtime source: `f0aae447654bc50100bc6a26a3e204fbdac6a707`
- Market report-only head not used: `64e7f9356d17a9b3d63233f19373b19290b20558`

Production files changed:

- `julia_core/capability/providers/ai_theme/frozen_market.py`
- `julia_core/runtime/capability_bridge.py`
- `executables/start-controlled-brain-18090-r9-d1a.sh`

Test files changed:

- `tests/runtime/test_r9_d1a_market_db_source_identity.py`
- `tests/runtime/test_r9_d1_canonical_market_provider_composition.py`
- `tests/capability/test_l0b_f1_market_frozen_composition.py`

## Clean-source identity recomputation

A clean export of Market `f0aae447654bc50100bc6a26a3e204fbdac6a707` was recomputed with the canonical Core path/content digest algorithm:

- Adapter digest: `34f72e3ac3d025c05e18814f76d75999ed385baa865b5263dbfb64eab20805f4`
- DB runtime digest: `23bc6dcf76650700353150f2eb95773169d14a3708293ac8b7826cde4f6b7454`
- DB runtime file count: 29
- DB runtime file-set change: NO

Both values exactly matched the required D2B identities.

## Releases

New immutable release:

`/Users/admin/julia_rd1_controlled/releases/market-f0aae447654bc50100bc6a26a3e204fbdac6a707`

Old release digests remained unchanged:

- `market-d6889f4...`: adapter `b07d454ac2c067717c7bdf70fc012c811d9d1636b427dd917134227e0df604dd`; DB runtime `19a4765e6e323bebb5b975560fce0a5a4111000844d95804a9dede1458935cff`
- `market-0bb026...`: adapter `a389f92a0026291bbb2820bfce03fb9ff2545553859022dea3a413b8f1d52ad1`; DB runtime `19a4765e6e323bebb5b975560fce0a5a4111000844d95804a9dede1458935cff`

Focused tests prove both old releases are rejected by the new target constants.

## Actual fresh controlled startup

The canonical launcher started a fresh process and preserved this order:

1. `RuntimeCapabilityBridge()`
2. `register_canonical_market_provider(retain_modules=True)`
3. source/adapter/DB identity validation
4. DatabaseGateway initialization and SELECT-1 health
5. exact provider registration
6. `bridge.initialize()`
7. `configure_capability_bridge(bridge)`
8. readiness/provenance checks
9. serve `127.0.0.1:18090`

No fallback provider was used. The process was stopped after attestation and before any resolver/read request.

Attestation results:

- Market SHA/provider SHA/trace SHA: `f0aae447654bc50100bc6a26a3e204fbdac6a707`
- Adapter digest: `34f72e3ac3d025c05e18814f76d75999ed385baa865b5263dbfb64eab20805f4`
- DB runtime digest: `23bc6dcf76650700353150f2eb95773169d14a3708293ac8b7826cde4f6b7454`
- Gateway initialized and SELECT-1: PASS
- Provider health: PASS
- Resolve/read capability status: AVAILABLE
- Bridge/provider identity: PASS
- Resolver gateway identity: PASS
- Reader gateway identity: PASS
- Preloaded Market modules: 0
- Preloaded DB modules: 0
- Every loaded `database_service.*` module under target release root: YES

## Loaded provenance

- Domain adapter: `/Users/admin/julia_rd1_controlled/releases/market-f0aae447654bc50100bc6a26a3e204fbdac6a707/stock_processing_service/application/services/julia_domain_adapter/adapter.py`
- Event resolver: `/Users/admin/julia_rd1_controlled/releases/market-f0aae447654bc50100bc6a26a3e204fbdac6a707/stock_processing_service/application/services/julia_domain_adapter/operations/event_resolve.py`
- Event reader: `/Users/admin/julia_rd1_controlled/releases/market-f0aae447654bc50100bc6a26a3e204fbdac6a707/stock_processing_service/application/services/julia_domain_adapter/operations/event_read.py`
- DatabaseGateway: `/Users/admin/julia_rd1_controlled/releases/market-f0aae447654bc50100bc6a26a3e204fbdac6a707/database_service/gateway.py`
- Postgres manager: `/Users/admin/julia_rd1_controlled/releases/market-f0aae447654bc50100bc6a26a3e204fbdac6a707/database_service/managers/postgres_manager.py`

## D2B and R9 fingerprints

Actual loaded source attestation proves:

- `_decode_json_array` is present and used by `resolve_market_event_candidates()`
- Python lists pass through; JSON array strings decode
- malformed JSON, non-array JSON, invalid scalar values, and `None` fail closed
- `CANDIDATE_FAILURE_LAYER`, `candidate_index`, `raw_candidate_count`, `matched_subjects_type`, and `pre_collapse_failure` are present
- R9-F1 exception diagnostics remain present
- R9-F1A bounded/redacted closure remains present

## Tests

Focused identity/composition:

```text
/opt/miniconda3/bin/pytest -q tests/runtime/test_r9_d1a_market_db_source_identity.py tests/runtime/test_r9_d1_canonical_market_provider_composition.py
```

Result: `16 passed in 59.44s`

Required focused regression set:

```text
/opt/miniconda3/bin/pytest -q tests/runtime/test_r9_d1a_market_db_source_identity.py tests/runtime/test_r9_d1_canonical_market_provider_composition.py tests/capability/test_l0b_f1_market_frozen_composition.py tests/runtime/test_capability_bridge_composition.py tests/runtime/test_r9_f1_capability_failure_event_retention.py tests/runtime/test_l1_f2_deterministic_research_desk_ingress.py tests/runtime/test_i4_same_turn_research_orchestration.py
```

Result: `64 passed in 71.41s`

The D1A helper/package test is included in `test_r9_d1a_market_db_source_identity.py`.

## Static checks

```text
python -m compileall -q julia_core/capability/providers/ai_theme/frozen_market.py julia_core/runtime/capability_bridge.py tests/runtime/test_r9_d1a_market_db_source_identity.py tests/runtime/test_r9_d1_canonical_market_provider_composition.py tests/capability/test_l0b_f1_market_frozen_composition.py
git diff --check
```

Results: PASS / PASS.

## Execution counters

- Real resolver executions: 0
- Market event read executions: 0
- User turns: 0
- D1/C1/C2 executions: 0
- Assistant research brief executions: 0
- Database writes: 0
- Market resolver retries: 0
- Market resolver fallbacks: 0

## Gates

- R9-D2C ready to close: YES
- R9-D2D ready: YES
- R9-D2D authorized: NO
- R9-D3 ready: NO
- R10 ready: NO
- R10 authorized: NO


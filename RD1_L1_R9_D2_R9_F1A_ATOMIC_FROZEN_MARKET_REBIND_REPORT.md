# RD1-L1-R9-D2 R9-F1A Atomic Frozen Market Rebind Report

## Executive verdict

PASS. The controlled 18090 runtime atomically moved from Market `d6889f4f39fc4f8adf404ea7c51eee3ad22d7fa7` to approved source closure `0bb026889f5c51e72aff9561b5eb542db7adf088`. Adapter SHA, configured identity, filesystem digest, provider label, trace label, gateway/provider identity, readiness, and loaded module provenance all agree. No resolver/read execution, user turn, D1 execution, SQL edit, or database write occurred.

## Source states

- Core base: `27ae906bfff026c195c55b84ec90f0f09c73d05d`
- Core source closure: `f0694f62816d37576774827316eaf5c3581b6a81`
- Market old source: `d6889f4f39fc4f8adf404ea7c51eee3ad22d7fa7`
- Market target source: `0bb026889f5c51e72aff9561b5eb542db7adf088`
- Market report-only head intentionally not used: `a9725315e914a62b9e7e71d34fec4e2eecf6bfb9`

## Changed files

- `julia_core/capability/providers/ai_theme/frozen_market.py`
- `julia_core/runtime/capability_bridge.py`
- `executables/start-controlled-brain-18090-r9-d1a.sh`
- `tests/runtime/test_r9_d1a_market_db_source_identity.py`
- `tests/runtime/test_r9_d1_canonical_market_provider_composition.py`
- `tests/capability/test_l0b_f1_market_frozen_composition.py`

Market production files changed: 0. Core production files changed: 3.

## Adapter identity

Target source was exported cleanly from Market commit `0bb026889f5c51e72aff9561b5eb542db7adf088`. Recomputation used the canonical Core path/content digest algorithm.

- Old adapter digest: `b07d454ac2c067717c7bdf70fc012c811d9d1636b427dd917134227e0df604dd`
- Target adapter digest: `a389f92a0026291bbb2820bfce03fb9ff2545553859022dea3a413b8f1d52ad1`
- Required value: `a389f92a0026291bbb2820bfce03fb9ff2545553859022dea3a413b8f1d52ad1`
- Recomputation result: PASS

## DB runtime identity

The target DB runtime dependency set was re-audited relative to `DatabaseGateway.initialize()`, resolver/read operations, factory/config/manager paths, reconnect/lazy import paths, and the prior deterministic closure. The old-to-target source diff did not alter any `database_service/*` file. The D1A 29-file ordered closure remains complete; no files were added or removed.

- D1A DB digest: `19a4765e6e323bebb5b975560fce0a5a4111000844d95804a9dede1458935cff`
- Target recomputed DB digest: `19a4765e6e323bebb5b975560fce0a5a4111000844d95804a9dede1458935cff`
- Result: `UNCHANGED_BY_RECOMPUTATION`
- D1A file count: 29
- D2 file count: 29
- Files added: NONE
- Files removed: NONE

Closure files:

1. `database_service/__init__.py`
2. `database_service/client.py`
3. `database_service/config.py`
4. `database_service/factory.py`
5. `database_service/gateway.py`
6. `database_service/interface.py`
7. `database_service/managers/__init__.py`
8. `database_service/managers/base_manager.py`
9. `database_service/managers/memory_manager.py`
10. `database_service/managers/postgres_manager.py`
11. `database_service/managers/redis_cached_manager.py`
12. `database_service/managers/redis_event_bus.py`
13. `database_service/managers/redis_stream_bus.py`
14. `database_service/streams/__init__.py`
15. `database_service/streams/database_interface_ext.py`
16. `database_service/streams/producers/__init__.py`
17. `database_service/streams/producers/event_producer.py`
18. `database_service/streams/producers/news_producer.py`
19. `database_service/streams/producers/theme_producer.py`
20. `database_service/streams/stream_config.py`
21. `database_service/streams/stream_factory.py`
22. `database_service/streams/stream_gateway.py`
23. `database_service/streams/stream_interface.py`
24. `database_service/streams/stream_manager.py`
25. `database_service/streams/utils/__init__.py`
26. `database_service/streams/utils/alert_service.py`
27. `database_service/streams/utils/consumer_group_manager.py`
28. `database_service/streams/utils/error_handler.py`
29. `database_service/streams/utils/retry_manager.py`

## Release identity

- Target release root: `/Users/admin/julia_rd1_controlled/releases/market-0bb026889f5c51e72aff9561b5eb542db7adf088`
- Target release created: YES; directories mode 0555 and files mode 0444
- Old release root remained present and unchanged
- Old release recomputed adapter digest: `b07d454ac2c067717c7bdf70fc012c811d9d1636b427dd917134227e0df604dd`
- Old release recomputed DB digest: `19a4765e6e323bebb5b975560fce0a5a4111000844d95804a9dede1458935cff`
- Old source SHA rejection test: PASS
- Target source acceptance: PASS
- Report-only head used as runtime source: NO

## Fresh controlled runtime attestation

Fresh process startup used `executables/start-controlled-brain-18090-r9-d1a.sh` and `run_controlled_brain(18090)`. Canonical provider registration occurred before `bridge.initialize()`, with retained pinned modules and no fallback provider.

Attestation result:

- Provider SHA: `0bb026889f5c51e72aff9561b5eb542db7adf088`
- Trace SHA: `0bb026889f5c51e72aff9561b5eb542db7adf088`
- Adapter digest: `a389f92a0026291bbb2820bfce03fb9ff2545553859022dea3a413b8f1d52ad1`
- DB runtime digest: `19a4765e6e323bebb5b975560fce0a5a4111000844d95804a9dede1458935cff`
- Gateway initialized/SELECT 1: PASS
- Bridge/provider identity: PASS
- Resolver gateway identity: PASS
- Reader gateway identity: PASS
- Provider health: PASS
- `market.event.resolve`: AVAILABLE
- `market.event.read`: AVAILABLE
- Preloaded Market modules: 0
- Preloaded DB modules: 0
- All Market/DB module paths under target release root: YES

Loaded paths:

- Domain adapter: `/Users/admin/julia_rd1_controlled/releases/market-0bb026889f5c51e72aff9561b5eb542db7adf088/stock_processing_service/application/services/julia_domain_adapter/adapter.py`
- Event resolver: `/Users/admin/julia_rd1_controlled/releases/market-0bb026889f5c51e72aff9561b5eb542db7adf088/stock_processing_service/application/services/julia_domain_adapter/operations/event_resolve.py`
- Event reader: `/Users/admin/julia_rd1_controlled/releases/market-0bb026889f5c51e72aff9561b5eb542db7adf088/stock_processing_service/application/services/julia_domain_adapter/operations/event_read.py`
- DatabaseGateway: `/Users/admin/julia_rd1_controlled/releases/market-0bb026889f5c51e72aff9561b5eb542db7adf088/database_service/gateway.py`
- Postgres manager: `/Users/admin/julia_rd1_controlled/releases/market-0bb026889f5c51e72aff9561b5eb542db7adf088/database_service/managers/postgres_manager.py`

## R9-F1/F1A source fingerprint

The loaded `event_resolve.py` contains operation symbol, failure layer, exception class/message, SQLSTATE, pgcode, errno, error code, process PID, observed time, resolver query, normalized theme, time window, correlation ID, and idempotency ID. F1A closure uses bounded normalized text, `redact_diagnostics`, genuine exception-derived provider status, and retains no traceback. Focused fingerprint and pinned-module tests PASS.

## Fail-closed proofs

- Target DB file mutation while adapter digest matches: rejected
- Adapter file mutation while DB digest matches: rejected independently
- Invalid configured DB digest: rejected
- Old source SHA with target constants: rejected
- Ambient `database_service`: safely displaced by pinned modules

## Test and static results

Commands:

```text
/opt/miniconda3/bin/pytest -q tests/runtime/test_r9_d1a_market_db_source_identity.py tests/runtime/test_r9_d1_canonical_market_provider_composition.py
```

Result: `14 passed in 63.59s`

```text
/opt/miniconda3/bin/pytest -q tests/runtime/test_r9_d1a_market_db_source_identity.py tests/runtime/test_r9_d1_canonical_market_provider_composition.py tests/capability/test_l0b_f1_market_frozen_composition.py tests/runtime/test_capability_bridge_composition.py tests/runtime/test_r9_f1_capability_failure_event_retention.py tests/runtime/test_l1_f2_deterministic_research_desk_ingress.py tests/runtime/test_i4_same_turn_research_orchestration.py
```

Result: `62 passed in 76.71s`

```text
python -m compileall -q julia_core/capability/providers/ai_theme/frozen_market.py julia_core/runtime/capability_bridge.py tests/runtime/test_r9_d1a_market_db_source_identity.py tests/runtime/test_r9_d1_canonical_market_provider_composition.py tests/capability/test_l0b_f1_market_frozen_composition.py
git diff --check
```

Results: PASS / PASS.

The initial frozen-composition regression run exposed two stale old-digest expectations and failed 2/62. Those test expectations were updated to the approved target digest; no production defect or pre-existing unrelated failure remains.

## Execution counts

- User turns: 0
- Resolver technical probes: 0
- Real resolver executions: 0
- Market event read executions: 0
- D1 executions: 0
- D1 retries: 0
- D1 fallbacks: 0
- Database writes: 0

## Gate

- R9-D2 ready to close: YES
- R9-D2A ready: YES
- R9-D2A authorized: NO
- R10 ready: NO
- R10 authorized: NO


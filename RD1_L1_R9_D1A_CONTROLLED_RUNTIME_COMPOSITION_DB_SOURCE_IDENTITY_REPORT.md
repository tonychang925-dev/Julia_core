# RD1-L1-R9-D1A Controlled Runtime Composition + DB Source Identity Report

## Source state

- Core base: `a15b40affc2aa78aede79ff51b82b845946fe86c`
- Core source-closure commit: `2fb73be0f9a5c914185fd5c46f0316d3b48dcdd9`
- Branch: `glm-d/rd1-l1-r9-d1a-controlled-db-identity`
- Market source: `d6889f4f39fc4f8adf404ea7c51eee3ad22d7fa7`
- Adapter digest: `b07d454ac2c067717c7bdf70fc012c811d9d1636b427dd917134227e0df604dd`
- DB runtime digest: `19a4765e6e323bebb5b975560fce0a5a4111000844d95804a9dede1458935cff`
- No R9-F1A rebind, resolver SQL change, Market source change, or data mutation occurred.

## Actual controlled startup

```text
CONTROLLED_STARTUP_FILE = executables/start-controlled-brain-18090-r9-d1a.sh
CONTROLLED_STARTUP_SYMBOL = run_controlled_brain
CONTROLLED_BRIDGE_CREATION_SYMBOL = RuntimeCapabilityBridge()
```

Exact source-backed call order:

```text
fresh Python process
→ run_controlled_brain(18090)
→ RuntimeCapabilityBridge()
→ bridge.register_canonical_market_provider(retain_modules=True)
→ frozen adapter identity validation
→ DB runtime configured/observed digest validation
→ pinned DatabaseGateway import
→ DatabaseGateway.initialize()
→ exact provider registration
→ bridge.initialize()
→ configure_capability_bridge(bridge)
→ object identity/readiness checks
→ module provenance checks
→ SELECT 1 health
→ Assistant legacy conversation wiring
→ uvicorn service loop
```

The canonical provider is registered before bridge initialization. The controlled path never invokes the no-provider fallback.

## Fresh-process attestation

A fresh process listened on `127.0.0.1:18090`, wrote `/tmp/rd1-l1-r9-d1a-runtime/composition_attestation.json`, and was stopped before any client/user action.

Observed values:

```text
PRELOADED_MARKET_MODULE_COUNT = 0
PRELOADED_DB_MODULE_COUNT = 0
MANAGER_PROVIDER_IDENTITY_PASS = YES
RESOLVER_GATEWAY_IDENTITY_PASS = YES
READER_GATEWAY_IDENTITY_PASS = YES
GATEWAY_INITIALIZED = YES
GATEWAY_SELECT_1 = YES
PROVIDER_HEALTH = PASS
MARKET_EVENT_RESOLVE_STATUS = AVAILABLE
MARKET_EVENT_READ_STATUS = AVAILABLE
ALL_MARKET_MODULES_FROM_PINNED_ROOT = YES
USER_TURNS = 0
REAL_RESOLVER_EXECUTIONS = 0
D1_EXECUTIONS = 0
DB_WRITES = 0
```

The actual process retained 24 loaded `database_service` modules, all under the pinned Market root. The larger 29-file static closure includes additional conditionally imported/reconnect-capable files and is fully covered by the digest.

## Runtime identity matrix

| Identity | Expected | Configured/observed |
|---|---|---|
| Market SHA | `d6889f4f...` | `d6889f4f...` |
| Provider SHA | `d6889f4f...` | `d6889f4f...` |
| Trace Market SHA | `d6889f4f...` | `d6889f4f...` |
| Adapter digest | `b07d454a...` | `b07d454a...` |
| DB runtime digest | `19a4765e...` | `19a4765e...` |
| Filesystem identity | original release | export has no `.git`; release name plus both exact digests agree |

The trace identity was proven with a safe recording adapter and no DB resolver execution: `MarketDomainAdapterProvider` propagates `source_sha` into `trace_metadata.market_source_sha`.

## DB runtime dependency closure

Static import traversal covered top-level and lazy imports plus package initializers reachable from `database_service.gateway`. The deterministic, path-sensitive, order-stable closure is:

```text
database_service/__init__.py
database_service/client.py
database_service/config.py
database_service/factory.py
database_service/gateway.py
database_service/interface.py
database_service/managers/__init__.py
database_service/managers/base_manager.py
database_service/managers/memory_manager.py
database_service/managers/postgres_manager.py
database_service/managers/redis_cached_manager.py
database_service/managers/redis_event_bus.py
database_service/managers/redis_stream_bus.py
database_service/streams/__init__.py
database_service/streams/database_interface_ext.py
database_service/streams/producers/__init__.py
database_service/streams/producers/event_producer.py
database_service/streams/producers/news_producer.py
database_service/streams/producers/theme_producer.py
database_service/streams/stream_config.py
database_service/streams/stream_factory.py
database_service/streams/stream_gateway.py
database_service/streams/stream_interface.py
database_service/streams/stream_manager.py
database_service/streams/utils/__init__.py
database_service/streams/utils/alert_service.py
database_service/streams/utils/consumer_group_manager.py
database_service/streams/utils/error_handler.py
database_service/streams/utils/retry_manager.py
```

Digest construction matches the existing approved-tree style:

```text
SHA256(relative_path_utf8 || NUL || SHA256(file_bytes).digest() || NUL)
```

The tuple is sorted and contains 29 files. Both configured and observed DB runtime digest must equal the Core constant before `DatabaseGateway` is imported.

## Reconnect and module identity

Source audit finds lazy DB imports:

- `DatabaseGateway.initialize()` imports `PostgresDatabaseManager`;
- `DatabaseGateway._reconnect()` imports `PostgresDatabaseManager`;
- package `__getattr__` and conditional package imports can load additional manager modules.

Therefore `RECONNECT_MODULE_IDENTITY_RISK = YES` before mitigation. Controlled composition mitigates it by retaining the pinned `database_service` module graph in `sys.modules`; lazy/reconnect imports resolve from that graph rather than ambient source. Every retained DB module path was proven under the pinned root.

## Fail-closed proofs

- Missing or incorrect configured DB digest rejects composition.
- DB runtime file mutation changes the DB digest while leaving adapter digest unchanged, and composition rejects it.
- Adapter mutation changes adapter digest independently while DB digest remains unchanged.
- Ambient `database_service` modules are displaced by pinned modules and validated before use.
- Controlled startup checks provider/gateway identity, health, readiness, and module provenance before serving.
- No identity failure can advertise the DB-dependent capabilities as `AVAILABLE`.

## Test and static results

```text
/opt/miniconda3/bin/pytest -q tests/runtime/test_r9_d1a_market_db_source_identity.py
7 passed in 43.23s

/opt/miniconda3/bin/pytest -q tests/runtime/test_r9_d1a_market_db_source_identity.py tests/runtime/test_r9_d1_canonical_market_provider_composition.py tests/capability/test_l0b_f1_market_frozen_composition.py tests/runtime/test_capability_bridge_composition.py tests/runtime/test_r9_f1_capability_failure_event_retention.py tests/runtime/test_l1_f2_deterministic_research_desk_ingress.py tests/runtime/test_i4_same_turn_research_orchestration.py
58 passed in 71.74s

/opt/miniconda3/bin/python -m compileall -q julia_core/capability/providers/ai_theme/frozen_market.py julia_core/runtime/capability_bridge.py tests/runtime/test_r9_d1a_market_db_source_identity.py
PASS

git diff --check
PASS
```

No pre-existing failures were observed.

## Changed files

Core production:

```text
julia_core/capability/providers/ai_theme/frozen_market.py
julia_core/runtime/capability_bridge.py
executables/start-controlled-brain-18090-r9-d1a.sh
```

Core tests:

```text
tests/runtime/test_r9_d1a_market_db_source_identity.py
```

Market, Assistant, D1, Client, and Voice source edits: `0`.

## Gate

```text
ACTUAL_18090_STARTUP_WIRING = PASS
DB_RUNTIME_DEPENDENCY_CLOSURE_PROVEN = YES
DB_RUNTIME_TREE_DIGEST_PROVEN = YES
SPLIT_MODULE_GRAPH_PREVENTED = YES
IDENTITY_FAILURE_FAILS_CLOSED = YES
R9_D1 = CLOSED
R9_D2_READY = YES
R9_D2_AUTHORIZED = NO
R10_READY = NO
R10_AUTHORIZED = NO
VERDICT = PASS
```

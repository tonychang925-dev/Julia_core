# RD1-L1-R9-D1 Canonical Market Provider Composition Closure Report

## Source state

- Core base: `be5d2b3e9b699a90467062182b2ddf531f86dd82`
- Dedicated branch: `glm-d/rd1-l1-r9-d1-market-provider-composition`
- Market source remains `d6889f4f39fc4f8adf404ea7c51eee3ad22d7fa7`
- Market approved-tree digest remains `b07d454ac2c067717c7bdf70fc012c811d9d1636b427dd917134227e0df604dd`
- No frozen SHA or digest was changed.

## Composition-root audit

No explicit controlled Assistant composition root constructs `DatabaseGateway` or a Market provider. `voice_api/server.py` wires legacy conversation state only. `JuliaSession.__init__` obtains the default `RuntimeCapabilityBridge` through `get_capability_bridge()`.

The narrow Core seams selected are:

1. `julia_core/capability/providers/ai_theme/frozen_market.py`
   - `compose_frozen_market_provider(environment)`
   - `frozen_market_database_gateways_bound(adapter)`
   - `MarketDomainAdapterProvider.health()`
2. `julia_core/runtime/capability_bridge.py`
   - `RuntimeCapabilityBridge.register_canonical_market_provider(...)`
   - `RuntimeCapabilityBridge.initialize()`

`compose_frozen_market_provider()` validates the frozen binding, imports Market's `DatabaseGateway` from the pinned source root, initializes it through its existing class/config path, and passes that exact object into the frozen adapter. No credentials or DSN are duplicated in Core.

## Production changes

- Canonical async composition returns `(provider, gateway)` and registers exactly one `ai_theme_app` provider.
- Explicit callers may inject an already initialized gateway through the same canonical registration method.
- Provider health now fails when either DB-dependent operation lacks a gateway.
- Default no-provider fallback still imports the frozen adapter but marks Market capabilities `DEGRADED` when the DB gateway is absent; it cannot silently report DB-dependent readiness as `AVAILABLE`.
- Pinned module loading now supports retaining the Market database package until gateway initialization completes, then restores the previous module-cache state.

Changed Core production files:

```text
julia_core/capability/providers/ai_theme/frozen_market.py
julia_core/runtime/capability_bridge.py
```

Changed Core test files:

```text
tests/capability/test_l0b_f1_market_frozen_composition.py
tests/runtime/test_r9_d1_canonical_market_provider_composition.py
```

Market production files changed: `0`.

## Object identity and readiness proof

The focused composition test proves:

- one gateway object is accepted and returned;
- resolver and reader operations hold that same object;
- bridge and manager hold the exact provider;
- only one `ai_theme_app` provider exists;
- provider health is healthy with a bound initialized gateway;
- DB-dependent definitions are `AVAILABLE` after canonical registration.

A separate real, non-resolver composition diagnostic against the controlled frozen source and local PostgreSQL returned:

```text
PROVIDER_HEALTH (True, 'frozen Market adapter sha:d6889f4f39fc4f8adf404ea7c51eee3ad22d7fa7')
MANAGER_PROVIDER_IDENTITY True
RESOLVER_GATEWAY_IDENTITY True
READER_GATEWAY_IDENTITY True
GATEWAY_INITIALIZED True
GATEWAY_SELECT_1 True
```

Therefore gateway construction, initialization, provider registration, and object identity are closed. The default half-composed fallback is visibly `DEGRADED`.

## Authorized canonical technical probe

Exactly one non-live resolver capability probe was attempted through:

```text
CapabilityRequest
→ RuntimeCapabilityBridge.manager.execute_typed
→ MarketDomainAdapterProvider.execute
→ DomainIntelligenceAdapter
→ MarketEventResolveOperation.execute
→ DatabaseGateway.resolve_market_event_candidates
→ PostgresDatabaseManager.resolve_market_event_candidates
```

Input:

```text
query = Token出海
normalized_theme = Token出海
time_window.date = 2026-07-19
```

Observed typed status:

```text
TECHNICAL_PROBE_STATUS unavailable
```

The probe harness then attempted to index `payload["state"]` before printing the failure envelope and raised `KeyError: 'state'`. Consequently the legacy frozen source's collapsed diagnostic fields were not captured. The authorization allowed exactly one resolver probe, so no second probe was run.

The focused canonical-path fixture proves Market converts the ISO date string to `datetime.date` before gateway delivery and preserves Market event ID `215257` with a fake gateway. The real canonical date-type and positive-sample result remain unproven because the sole authorized real probe failed.

## Gateway lifecycle

- Gateway creation and initialization occur in the asyncio context executing `register_canonical_market_provider()`.
- The same provider, operations, gateway, and probe execute in that loop.
- No cross-loop or cross-thread handoff is introduced.
- No async/session refactor was performed.
- Gateway closure follows the technical process after probe/readiness diagnostics.

The real resolver's `UNAVAILABLE` result is therefore an unresolved DB-runtime possibility, but its exact root exception is not recoverable from this run because current frozen Market predates R9-F1A observability and the one-shot harness did not print the failure envelope.

## Test and static results

```text
/opt/miniconda3/bin/pytest -q tests/runtime/test_r9_d1_canonical_market_provider_composition.py
3 passed in 13.84s

/opt/miniconda3/bin/pytest -q tests/runtime/test_r9_d1_canonical_market_provider_composition.py tests/capability/test_l0b_f1_market_frozen_composition.py
13 passed in 28.60s

/opt/miniconda3/bin/pytest -q tests/runtime/test_r9_d1_canonical_market_provider_composition.py tests/capability/test_l0b_f1_market_frozen_composition.py tests/runtime/test_capability_bridge_composition.py tests/runtime/test_r9_f1_capability_failure_event_retention.py tests/runtime/test_l1_f2_deterministic_research_desk_ingress.py tests/runtime/test_i4_same_turn_research_orchestration.py
51 passed in 30.20s

/opt/miniconda3/bin/pytest -q tests/julia_domain_adapter/test_i2a_market_event_resolve.py
10 passed in 0.28s

/opt/miniconda3/bin/pytest -q tests/runtime/test_r9_d1_canonical_market_provider_composition.py tests/capability/test_l0b_f1_market_frozen_composition.py tests/runtime/test_capability_bridge_composition.py tests/runtime/test_r9_f1_capability_failure_event_retention.py
21 passed in 29.52s

/opt/miniconda3/bin/python -m compileall -q julia_core/capability/providers/ai_theme/frozen_market.py julia_core/runtime/capability_bridge.py tests/runtime/test_r9_d1_canonical_market_provider_composition.py tests/capability/test_l0b_f1_market_frozen_composition.py
PASS

git diff --check
PASS
```

No pre-existing unrelated failures were newly observed. One intentional existing expectation was updated: a default frozen provider without a gateway must register DB-dependent Market capabilities as `DEGRADED`, not `AVAILABLE`.

## Execution counters

```text
USER_TURNS = 0
MARKET_RESOLVE_TECHNICAL_PROBE = 1
MARKET_EVENT_READ_EXECUTIONS = 0
D1_EXECUTIONS = 0
D1_RETRY = 0
D1_FALLBACK = 0
MARKET_RESOLVER_RETRY = 0
MARKET_RESOLVER_FALLBACK = 0
DB_WRITES = 0
NORMAL_BRAIN_TOUCHED = NO
FROZEN_REBIND_IN_R9_D1 = NO
SQL_EDIT = NO
RESOLVER_CONTRACT_DRIFT = NONE
ASSISTANT_SOURCE_EDITS = 0
D1_SOURCE_EDITS = 0
CLIENT_SOURCE_EDITS = 0
VOICE_SOURCE_EDITS = 0
```

## Gate

Composition identity and fail-visible readiness are repaired, but D1 acceptance is not complete because the sole authorized real canonical resolver probe returned `UNAVAILABLE` and its exact root exception was not captured.

```text
R9_D1_READY_TO_CLOSE = NO
R9_D2_REQUIRED = YES
R10_READY = NO
R10_AUTHORIZED = NO
VERDICT = BLOCKING_DB_RUNTIME
```

Do not treat this branch as R10-ready. Tony retains authorization authority.

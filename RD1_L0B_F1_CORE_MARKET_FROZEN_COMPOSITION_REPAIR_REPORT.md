# RD1-L0B-F1 Core / Market Frozen Composition Repair Report

## 1. Exact bases

- Core base: `f85b7b86b2b55f5f07564419f0ae01335fea7404`
- Market frozen: `d6889f4f39fc4f8adf404ea7c51eee3ad22d7fa7`
- Frozen approved tree digest: `b07d454ac2c067717c7bdf70fc012c811d9d1636b427dd917134227e0df604dd`

## 2. Source-proved root cause

Legacy startup followed this chain:

```text
RuntimeCapabilityBridge.initialize()
→ create_ai_theme_provider()
→ AiThemeProvider(MCPToolAdapter())
→ MCPToolAdapter._call_in_process()
→ hardcoded /Users/admin/Desktop/ai_theme_app and sibling sys.path insertion
→ from mcp_server.server import MCP_TOOLS
```

Relevant legacy source functions/files:

- `RuntimeCapabilityBridge.initialize` in `julia_core/runtime/capability_bridge.py`
- `create_ai_theme_provider` in `julia_core/capability/providers/ai_theme/__init__.py`
- `MCPToolAdapter._call_in_process` in `julia_core/capability/providers/ai_theme/adapter.py`

This allowed ambient `PYTHONPATH`, cached modules, and an unrelated dirty worktree to affect Market import resolution.

## 3. Composition repair

The repaired default path is:

```text
Core ai_theme_app provider namespace
→ pinned frozen Market root
→ approved-file tree digest validation
→ DomainIntelligenceAdapter
→ AdapterRequest
→ DomainObservationEnvelope
→ ProviderExecutionOutcome
```

Required environment pin:

- `JULIA_MARKET_SOURCE_ROOT`
- `JULIA_MARKET_SOURCE_SHA`
- `JULIA_MARKET_TREE_DIGEST`

The source SHA must equal the frozen SHA and the observed approved-file digest must equal the frozen digest. Import resolution temporarily uses only the exact pinned root, removes displaced Market module cache entries, verifies every imported Market module remains under that root, and restores the prior `sys.path`. There is no ambient fallback.

Missing or invalid configuration binds an explicit unavailable provider and registers Market capabilities as `DEGRADED`; it does not import unrelated Market code.

## 4. Registered operations

The frozen direct provider registers:

- `market.event.resolve`
- `market.event.read`
- `market.snapshot.read` → `market.snapshot`
- `market.alert.query` → `market.alerts`

The frozen Market owns `DomainIntelligenceAdapter`, `AdapterRequest`, `DomainObservationEnvelope`, PostgreSQL/`DatabaseGateway`, and canonical `public.news_event.id`. Core retains only capability registry, permission policy, manager, runtime bridge, and provider namespace ownership.

## 5. Legacy MCP boundary

The implicit in-process fallback and `mcp_server.server.MCP_TOOLS` import were removed. `MCPToolAdapter` now requires an explicitly injected transport. Product-owned injected providers retain legacy registration precedence for existing tests. Default runtime startup no longer depends on `mcp_server`, the Desktop worktree, ambient `PYTHONPATH`, or uncommitted Market files.

## 6. Tests

Focused:

```text
/opt/miniconda3/bin/pytest -q tests/capability/test_l0b_f1_market_frozen_composition.py
10 passed
```

Core capability regressions:

```text
/opt/miniconda3/bin/pytest -q tests/capability
176 passed, 11 xfailed
```

Runtime and research regressions:

```text
/opt/miniconda3/bin/pytest -q tests/runtime/test_i1_streaming_capability_continuation.py tests/runtime/test_i4_same_turn_research_orchestration.py tests/research/test_l0a_f1_core_d1_provider_binding.py tests/research/test_c1_research_event_enrichment.py tests/research/test_c2_preliminary_research_judgment.py
81 passed
```

Additional runtime injection regressions:

```text
/opt/miniconda3/bin/pytest -q tests/runtime/test_runtime_e2e.py tests/runtime/test_r1_1_workflow_authority.py
23 passed
```

Frozen Market focused tests, run from clean `git archive` export at `d6889f4...`:

```text
/opt/miniconda3/bin/pytest -q tests/julia_domain_adapter/test_i2a_market_event_resolve.py tests/julia_domain_adapter/test_m1a_market_event_read.py
17 passed
```

Static checks:

```text
/opt/miniconda3/bin/python -m compileall -q julia_core/capability/providers/ai_theme/frozen_market.py julia_core/capability/providers/ai_theme/adapter.py julia_core/capability/providers/ai_theme/__init__.py julia_core/runtime/capability_bridge.py
PASS

git diff --check
PASS
```

## 7. Test matrix proof

- F1 frozen Core imports and composes only the pinned frozen Market export: PASS
- F2 no `mcp_server` dependency is required: PASS
- F3 dirty alternate Market path/cached module cannot win import resolution: PASS
- F4 `market.event.resolve` registers as AVAILABLE under a valid pin: PASS
- F5 `market.event.read` registers as AVAILABLE under a valid pin: PASS
- F6 exact operation, arguments, identity, and trace metadata reach the frozen adapter contract: PASS
- F7 missing/wrong root, wrong SHA, or wrong tree digest fails closed as typed composition error/DEGRADED: PASS
- F8 no database query occurs during focused composition tests: PASS
- F9 no D1/provider network call occurs during focused composition tests: PASS
- F10 Voice, Julia_client, Assistant, and Market production edits: none

## 8. Boundaries and deviations

- Market production edits: 0
- DB queries: 0
- Market executions: 0
- D1 executions: 0
- Provider network calls: 0
- Voice executions / user traffic: 0
- Architecture deviations: NONE
- Blockers: NONE
- L0B rerun ready: YES

## 9. Verdict

```text
RD1-L0B-F1 = PASS
```

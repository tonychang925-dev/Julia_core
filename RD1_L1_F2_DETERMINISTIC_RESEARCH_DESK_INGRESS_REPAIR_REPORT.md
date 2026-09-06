# RD1-L1-F2 — Deterministic Research Desk Ingress Repair Report

## Assignment

```text
AGENT: GLM-A
CROSS_REVIEW_OWNER: GLM-D
TASK: RD1-L1-F2 DETERMINISTIC RESEARCH DESK NATURAL-LANGUAGE INGRESS REPAIR
BASE_SHA: a6031caad20c3a5213f5c9dc126d451262ffbef2
```

## Changed files

```text
julia_core/runtime/julia_session.py
tests/runtime/test_l1_f2_deterministic_research_desk_ingress.py
```

No Market, Assistant, D1, Client, Voice, provider, or workflow-framework production files were changed.

## Existing seams reused

- `JuliaSession.process_stream()`
- `JuliaSession._prepare_turn()`
- Context OS preparation/validation
- `SameTurnResearchContinuation.run()`
- existing `market.event.resolve` → `market.event.read` → `research.event.enrich` → C1 → C2 chain
- existing product hook/sink and same-turn final cognition continuation

No second cognition path, capability family, transport, Result/Evidence family, or Research Desk runtime was created.

## Implemented ingress

`JuliaSession._build_research_desk_resolver_call()` performs only bounded deterministic admission:

```text
1. normalize whitespace
2. reject >512-character input
3. reject explicit trading-action language
4. require an explicit research action
5. require a market/event/topic/brief object
6. use the bounded user text as query
7. optionally preserve one quoted normalized_theme
8. optionally convert one explicit yyyy年m月d日 date to time_window.date
9. return only market.event.resolve frozen arguments
```

Recognized research actions:

```text
研究
调研
查证
```

Required object/product terms include:

```text
市场
行情
事件
主题
简报
```

The helper never:

```text
forms a thesis
forms evidence
mints verification state
selects an ambiguous candidate
infers event identity
invokes D1 directly
performs research cognition
```

## Streaming lifecycle

The new branch runs only after:

```text
JuliaSession.process_stream()
→ JuliaSession._prepare_turn()
→ Context OS prepare/validation
```

It then executes:

```text
deterministic resolver carrier
→ SameTurnResearchContinuation
→ final provider stream
→ caller's ConversationRuntime commit
```

The first model pass is not required for an admitted Research Desk request. Model-generated `market.event.resolve` tool calls continue through the pre-existing branch unchanged.

## Authority preservation

```text
Conversation authority: ConversationRuntime
Model-visible context: Context OS
Cognition/routing boundary: JuliaSession/Core
Market event identity/data: Market
D1 observation: D1
Verification state: C1
Preliminary judgment: C2
Presentation/transport: Assistant
Client cognition: none
```

Core emits only resolver `query`/optional deterministic hints. Market alone emits `selected_event_id`; Core only consumes it for `market.event.read`.

## STOP semantics

The implementation does not modify resolver-state handling. Existing tests and focused regressions prove:

```text
UNRESOLVED → no read/research
AMBIGUOUS → no read/research
UPSTREAM_UNAVAILABLE → no read/research
```

No D1 call occurs for those states.

## Trading boundary

Deterministic ingress excludes explicit trading-action terms before Research Desk admission:

```text
买
卖
做多
做空
仓位
目标价
止损
止盈
```

Downstream C2/B1 trading guards remain unchanged.

## Tests

Focused new suite:

```text
python3.13 -m pytest -q tests/runtime/test_l1_f2_deterministic_research_desk_ingress.py
→ 23 passed
```

Research/I1/I4/C1/C2:

```text
python3.13 -m pytest -q \
  tests/runtime/test_i1_streaming_capability_continuation.py \
  tests/runtime/test_i4_same_turn_research_orchestration.py \
  tests/research/test_c1_research_event_enrichment.py \
  tests/research/test_c2_preliminary_research_judgment.py
→ 72 passed
```

Capability/Market/D1/bootstrap composition:

```text
python3.13 -m pytest -q \
  tests/runtime/test_capability_bridge_composition.py \
  tests/capability/test_l0b_f1_market_frozen_composition.py \
  tests/runtime/test_l0b_f2_conversation_bootstrap_compatibility.py \
  tests/research/test_l0a_f1_core_d1_provider_binding.py
→ 35 passed, 1 warning
```

Conversation authority/bootstrap:

```text
python3.13 -m pytest -q \
  tests/test_conversation_authority.py \
  tests/runtime/test_l0b_f2_conversation_bootstrap_compatibility.py
→ 34 passed, 1 warning
```

Static checks:

```text
python3.13 -m compileall -q julia_core tests/runtime/test_l1_f2_deterministic_research_desk_ingress.py
git diff --check
→ PASS
```

The warning is a pre-existing Starlette `python_multipart` pending-deprecation warning.

## Mandatory matrix coverage

```text
T01 explicit phrases → admission PASS
T02 controlled DUV request → resolver selected without first-pass tool call PASS
T03 ordinary Market status behavior unchanged PASS
T04 trading requests excluded PASS
T05 resolve precedes read PASS
T06 read precedes enrich PASS
T07 UNRESOLVED stops before D1 PASS
T08 AMBIGUOUS stops before D1 PASS
T09 UPSTREAM_UNAVAILABLE stops before D1 PASS
T10 event ID originates only from Market PASS
T11 C1/C2 regressions unchanged PASS
T12 same conversation_id/turn_id PASS
T13 no second assistant turn PASS
T14 model-generated tool call still works PASS
T15 file capability unchanged PASS
T16 generic market status not captured PASS
```

## Execution boundary

```text
D1_EXECUTIONS: 0
D1_RETRY: 0
D1_FALLBACK: 0
DB_QUERIES: 0
LIVE_PROVIDER_CALLS: 0
USER_TURNS: 0
```

All capability/research tests used deterministic fixtures registered through the existing provider seam.

## Architecture deviations

```text
NONE
```

The repair is one deterministic admission helper and one branch in the existing canonical streaming cognition path.

## Verdict

```text
RD1-L1-F2 = PASS
L1_RERUN_READY = YES
```

# RD1-I4 Same-Turn Research Orchestration Report

## AGENT

GLM-A

## ROLE

Same-Turn Research Orchestration Implementation Owner

## TASK

RD1-I4 SAME-TURN RESEARCH ORCHESTRATION

## CORE_BASE_SHA

ff545b7561641e35d6bb689b686d05c3343165fa

## ASSISTANT_BASE_SHA

ee45c703623ee5c55fea547e24d6a6a45492272c

## CORE_HEAD_SHA

d11aff6b84138c2e297c475582c1525e5919f9ef

This is the exact Core implementation commit. The report itself is appended as a separate audit-artifact commit and contains no production edits.

## ASSISTANT_HEAD_SHA

0aabd45cc9191cf51423cafc4ec2786b731643da

## REMOTE_BRANCHES

- Core: `glm-a/rd1-i4-same-turn-research-orchestration`
- Assistant: `glm-a/rd1-i4-product-metadata-binding`

## PRODUCTION_EDITS

- `julia_core/capability/providers/ai_theme/__init__.py`
- `julia_core/runtime/capability_bridge.py`
- `julia_core/runtime/context_execution_runtime.py`
- `julia_core/runtime/julia_session.py`
- `julia_core/runtime/research_continuation.py`
- `../b1_assistant/voice_api/conversation_routes.py`
- `../b1_assistant/voice_api/research_product_binding.py`
- `../b1_assistant/tests/test_i4_canonical_stream_product_metadata.py`
- `tests/runtime/test_i4_same_turn_research_orchestration.py`

## MARKET_RESOLVER_REACHABLE

PASS — `market.event.resolve` is registered as an `ai_theme_app` capability and is reachable only after Julia cognition emits a governed tool call.

## MARKET_READ_REUSED

PASS — the resolver-selected Market-owned `selected_event_id` invokes `market.event.read` through the capability bridge; Core never reconstructs Market truth.

## RESEARCH_EVENT_ENRICH_REUSED

PASS — `MarketEventResearchAdapter.build_request()` produces the frozen `CapabilityRequest`, and `RuntimeCapabilityBridge.execute_capability_request_async()` awaits the governed provider call. D1 is never called directly.

## C1_PRESERVED

PASS — the sole verification transition remains `ResearchEvidenceNormalizer.normalize_provider_outcome()`. I4 does not mint, upgrade, downgrade, or rewrite verification states.

## C2_IN_SAME_TURN

PASS — `JuliaSession.form_preliminary_research_judgment()` runs inside the original streaming turn using canonical Market context and normalized enrichment.

## B1_IN_SAME_TURN

PASS — the injected product hook invokes the frozen `ResearchBriefComposer`; I4 adds only serialization and same-turn binding. B1 receives the exact C2 judgment and Market metadata.

## B2_PRESENTATION_ONLY

PASS — `ResearchBriefProductAdapter` validates presentation only. Assistant transport neither selects research nor composes research truth.

## PRODUCT_METADATA_EMITTED

PASS — successful same-turn research emits `julia.product.events.v1` containing events, `research.brief.v1`, and trace after canonical assistant commit and before `[DONE]`.

## SAME_CONVERSATION_ID

PASS — `conversation_id` is supplied once to `process_stream()` and retained across resolver, read, enrichment, judgment, brief, final cognition, and settlement.

## SAME_TURN_ID

PASS — `turn_id` is retained across every capability continuation and the final assistant commit; no second semantic turn is opened.

## EXACTLY_ONCE_SETTLEMENT

PASS — Assistant commits once before `[DONE]`; cancellation uses the existing `cancel_streaming_turn()` path, and later commit is rejected by ConversationRuntime.

## CANCELLATION

PASS (fixture/local transport cancellation) — canceling before research completion retains the accepted user fact, prevents assistant commit, and settles the turn once. No external provider abort is claimed.

## PROGRESS_EVENTS

PASS — existing capability events emit `capability.started`, `capability.completed`, `capability.failed`, and `capability.cancelled` as non-transcript runtime truth.

## VOICE_EDITS

0

## CLIENT_EDITS

0

## LIVE_NETWORK_CALLS

0

## TESTS

- Core focused: `/opt/miniconda3/bin/python -m pytest tests/runtime/test_i4_same_turn_research_orchestration.py -q` — 7 passed.
- Core I1 + I4: `/opt/miniconda3/bin/python -m pytest tests/runtime/test_i1_streaming_capability_continuation.py tests/runtime/test_i4_same_turn_research_orchestration.py -q` — 15 passed.
- Core research/runtime: `/opt/miniconda3/bin/python -m pytest tests/runtime tests/research -q` — 258 passed, 6 skipped, 13 xfailed, 17 pre-existing failures.
- Core capability: `/opt/miniconda3/bin/python -m pytest tests/capability -q` — 166 passed, 11 xfailed.
- Core conversation/context authority: `/opt/miniconda3/bin/python -m pytest tests/test_conversation_authority.py tests/test_context_continuity_boundary.py tests/test_context_reconstruction.py -q` — 29 passed.
- Core cognition/review regressions: `/opt/miniconda3/bin/python -m pytest tests/review tests/runtime/test_c1_rev2_sync_stream_authority.py tests/runtime/test_c1_rev2_cognitive_boundary.py tests/runtime/test_no_fallback_hardening.py -q` — 263 passed, 2 skipped, 6 xfailed.
- Assistant B1/B2/I4: `/opt/miniconda3/bin/python -m pytest tests/test_i4_canonical_stream_product_metadata.py tests/test_b1_research_brief_composition.py tests/test_b2_research_brief_product_surface.py -q` — 51 passed, 1 warning.
- Core compile/check: `/opt/miniconda3/bin/python -m compileall -q <changed modules>` and `git diff --check` — passed.
- Assistant compile/check: `/opt/miniconda3/bin/python -m compileall -q <changed modules>` and `git diff --check` — passed.

The 17 `tests/runtime/test_chat_e2e.py` / `test_r1_events_workflow.py` failures are unchanged at exact I1 base `ff545b7561641e35d6bb689b686d05c3343165fa`; they fail because legacy fixtures omit `JuliaSession.context_os`. The three Assistant segmented-conversation failures are also pre-existing stale tests that assume turn ingestion creates a conversation. No unrelated expectation was changed.

## PROVEN

- Julia cognition owns the initial `market.event.resolve` decision.
- Market owns canonical event identity; cognition cannot generate an authoritative event ID.
- RESOLVED, UNRESOLVED, and AMBIGUOUS outcomes reach Julia continuation without arbitrary selection.
- Market read, research enrichment, C1 normalization, C2 judgment, and B1 brief composition stay in one canonical streaming turn.
- `REPORT_ONLY`, `NOT_PROVEN`, and `BLOCKED` remain unchanged.
- Contradictions, unknowns, confidence basis, reasoning limits, evidence references, and source references remain visible.
- Hostile research/source material is projected as inert evidence.
- Prohibited trading structured fields fail closed before B1 composition.
- ResearchBrief is product metadata, never transcript truth.
- Ordinary no-tool conversation preserves its single-cognition-call behavior.

## NOT_PROVEN

- Live Market resolver/read behavior.
- Live D1 provider transport or abort behavior.
- Voice/S2S product rendering.
- Electron/client consumption of product metadata.
- Multi-event research orchestration (explicitly out of scope).

## ARCHITECTURE_DEVIATIONS

- NONE

## BLOCKERS

- NONE

## ARTIFACT

`RD1_I4_SAME_TURN_RESEARCH_ORCHESTRATION_REPORT.md`

## VERDICT

I4 = PASS

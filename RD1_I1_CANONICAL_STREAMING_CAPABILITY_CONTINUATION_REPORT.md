# RD1-I1 — Canonical Streaming Capability Continuation Implementation Report

## 1. Exact base SHAs

- `Julia_core` base: `28121c3343d2c8dd30a6a8558e1a960b713a62c8`
- `Julia-AI-Assistant` base: `ee45c703623ee5c55fea547e24d6a6a45492272c`
- Assistant remains unchanged.
- No Market, D1, Voice, Electron, client, B1 truth, or B2 truth files were modified.

## 2. Changed files

- `julia_core/runtime/capability_bridge.py`
- `julia_core/runtime/julia_session.py`
- `julia_core/runtime/conversation_runtime.py`
- `tests/runtime/test_c1_rev2_sync_stream_authority.py`
- `tests/runtime/test_i1_streaming_capability_continuation.py`
- `RD1_I1_CANONICAL_STREAMING_CAPABILITY_CONTINUATION_REPORT.md`

## 3. Existing seams reused

- `ConversationRuntime.begin_turn_streaming()`
- `TurnStreamingContext`
- `ConversationMessage` durable storage
- `JuliaSession.process_stream()`
- `ContextExecutionRuntime.project_tool_result()`
- model-owned structured `tool_call` detection
- `RuntimeCapabilityBridge`
- `CapabilityRequest`, `CapabilityCall`, `ToolResult`, and `Evidence`
- `CapabilityManager.execute_typed()`
- existing action lifecycle
- existing C1 `MarketEventResearchAdapter` and frozen research registration contract

No new runtime, workflow engine, agent loop, generic result family, generic evidence family, model gateway, or provider transport was introduced.

## 4. Streaming capability lifecycle

The implemented logical lifecycle is:

```text
USER_ACCEPTED_DURABLE
→ COGNITION_RUNNING
→ CAPABILITY_PENDING
→ CAPABILITY_RUNNING
→ CAPABILITY_RESULT_AVAILABLE
→ COGNITION_RESUMED
→ ASSISTANT_GENERATING
→ ASSISTANT_FINALIZED
→ TURN_COMPLETED
```

The first model pass is buffered until tool-call intent is resolved. This prevents a structured tool request from becoming visible assistant content. If no capability is requested, the original model deltas stream normally. If cognition requests a capability, execution is awaited, the exact typed outcome is projected through Context OS, and only resumed Julia cognition streams final assistant deltas.

Intermediate capability facts are runtime events, never `ConversationMessage` records.

## 5. research.event.enrich registration/binding

- `RuntimeCapabilityBridge.initialize()` now registers the frozen C1 `research.event.enrich` definition and permission rule.
- Its selector remains the explicit `research_enrichment` provider namespace.
- No production network provider is bound by I1. Without a binding, `CapabilityManager` returns a typed `UNAVAILABLE` result with `provider_not_found`; there is no fallback.
- Product/test provider binding uses the existing `register_provider()` seam.
- The model-visible manifest includes the capability, but model context cannot select provider transport.
- The adapter accepts only the frozen Market event/context contract. I1 does not resolve or synthesize `market_event_id`; fixture setup supplies the valid canonical event identity and full frozen context.
- Invalid research context resolves to fail-closed `INVALID_MARKET_CONTEXT`, not a guessed event.

## 6. Await/resume behavior

- `execute_tool_typed_async()` awaits `CapabilityManager.execute_typed()` in the caller's event loop.
- The original `TurnContext` remains live across capability execution.
- The provider result returns as the exact `CapabilityExecution`.
- `_dispatch_typed_outcome()` projects its `ToolResult` and exact `Evidence` through Context OS.
- The resumed provider stream consumes that projection and the prior cognition output.
- The tool result is not converted into a new user turn or detached response.

## 7. Same-turn proof

Focused fixture I1-F01/F02 proves:

- `conversation_id` remains `conv`;
- `turn_id` remains `turn-001`;
- the same `TurnContext` performs first cognition, capability request, await, result projection, and resumed cognition;
- only one assistant message commits under the canonical turn;
- the request carries `turn_id` and turn correlation;
- `CapabilityRequest`, `CapabilityCall`, and `ToolResult` identities remain directly available;
- model/provider IDs do not replace Julia conversation IDs.

## 8. Cancellation

Focused fixture I1-F04 cancels the streaming async generator while the fixture provider is pending:

- cancellation propagates through the awaited capability execution;
- a non-transcript `capability_cancelled` runtime event is emitted;
- `ConversationRuntime.cancel_streaming_turn()` settles the turn once;
- the accepted user `ConversationMessage` remains completed;
- no assistant completion is committed;
- a later commit on the same context is rejected.

I1 proves runtime/coroutine cancellation and canonical settlement. It does not claim external HTTP/WebFetch provider abort beyond that propagation boundary.

## 9. Exactly-once settlement

`TurnStreamingContext` now records whether the particular streaming context has settled.

- first `commit_streaming_turn()` commits one assistant message and stores the result;
- duplicate commit raises before repository mutation;
- first `cancel_streaming_turn()` settles cancellation and releases the lock;
- duplicate cancel cannot double-release the same lock;
- commit after cancel raises;
- an idempotent already-completed replay context cannot commit again;
- there is no second assistant semantic turn.

The existing Assistant streaming route already uses one local settle flag; the Core runtime guard now enforces the same invariant at the authority boundary.

## 10. Progress events

The async capability seam emits immutable, non-authoritative `EventCategory.CAPABILITY` runtime events:

- `capability.started`
- `capability.completed`
- `capability.failed`
- `capability.cancelled`

Payloads include available `capability_id`, `capability_request_id`, `capability_call_id`, `turn_id`, `generation_id`, correlation, status, and evidence refs as those artifacts become available. Missing later IDs are not invented.

These events are not conversation transcript truth and do not render as fake assistant messages.

## 11. Provenance

The streaming chain preserves:

- `conversation_id`
- `turn_id`
- turn `correlation_id`
- `capability_request_id`
- `capability_call_id`
- `ToolResult` identity
- exact `Evidence.evidence_id` refs
- C1 `market_event_id` and source trace provenance already carried by the frozen request contract

I1 does not create or rewrite `judgment_id` or `brief_id`. Those later-stage artifacts remain downstream C2/B1 identities and are absent here rather than fabricated.

## 12. Tests

Focused fixture coverage in `tests/runtime/test_i1_streaming_capability_continuation.py`:

- I1-F01 happy path: one capability request, result, resumed cognition, one commit.
- I1-F02 same conversation and turn identity.
- I1-F03 provider unavailable/failure re-enters cognition without success fabrication.
- I1-F04 cancellation before capability completion.
- I1-F05 duplicate completion callback/settlement rejection.
- I1-F06 REPORT_ONLY remains REPORT_ONLY.
- I1-F07 NOT_PROVEN/BLOCKED material remains visible.
- I1-F08 hostile source content is inert governed material.
- I1-F09 downstream C2 trading prohibition remains fail-closed.
- I1-F10 ordinary no-capability stream remains unchanged.
- Registration is available, model-visible, provider-isolated, and fails closed without a provider binding.

The two former strict streaming-authority `xfail` expectations were resolved, not weakened: streaming now performs governed capability execution and typed Context OS re-entry. Their assertions now require the exact typed `ToolResult`.

## 13. Regressions

Passed:

```text
/opt/miniconda3/bin/python -m compileall -q \
  julia_core/runtime \
  julia_core/research \
  tests/runtime/test_i1_streaming_capability_continuation.py

/opt/miniconda3/bin/python -m pytest \
  tests/runtime/test_i1_streaming_capability_continuation.py \
  tests/runtime/test_c1_rev2_sync_stream_authority.py \
  tests/runtime/test_r2_p3_context_os_typed_projection.py \
  tests/runtime/test_r2_p3_2_bridge_typed_delivery.py \
  tests/runtime/test_r2_p3_2_3b_session_wiring.py \
  tests/runtime/test_c1_rev2_legacy_reachability_contract.py \
  tests/research/test_c1_research_event_enrichment.py \
  tests/research/test_c2_preliminary_research_judgment.py \
  tests/capability/test_r2_p1b_manager_canonical_lifecycle.py \
  tests/capability/test_r2_p3_2_manager_typed_bundle.py \
  tests/test_conversation_authority.py \
  tests/test_baseline_e2e_conversation.py \
  tests/review/test_review_invocation.py \
  -q
```

Result:

```text
175 passed, 5 skipped, 1 xfailed
```

Also passed:

```text
/opt/miniconda3/bin/python -m pytest tests/capability \
  tests/runtime/test_c1_rev2_sync_stream_authority.py \
  tests/runtime/test_i1_streaming_capability_continuation.py -q
```

Result:

```text
178 passed, 1 skipped, 11 xfailed
```

`git diff --check` passed.

Two exact-dict assertions in `tests/rt2_r3/test_core_acceptance.py` fail identically at the frozen base SHA and are pre-existing; they were not changed to make I1 green.

## 14. Architecture deviations

None.

The change extends the existing Julia cognition/capability path and does not create a second cognition stack. B2 remains presentation-only and untouched.

## 15. Not proven

- Live external provider latency or transport cancellation.
- Natural-language resolution from an utterance to `market_event_id`.
- Production D1 provider binding; I1 uses the existing explicit provider-binding seam and fixture provider.
- Automatic C2 judgment and B1 brief composition inside the same turn; those later-stage IDs remain absent.
- Client/Electron progress rendering, owned by J2/I3.
- S2S production conversation identity stability.

## 16. Verdict

```text
I1 = PASS
```

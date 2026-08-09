# P0-A — Production Cognitive Path Reality Audit

**Status**: READ-ONLY AUDIT
**Date**: 2026-08-09
**Production code changes**: 0

## P0A-1: ModelProvider Invocation Inventory

### Primary production paths (julia_core)

| # | File | Call | Type | Production? |
|---|------|------|------|-------------|
| 1 | `runtime/julia_session.py:303` | `self.provider.chat(messages)` | sync | ✅ main cognitive path |
| 2 | `runtime/julia_session.py:317` | `self.provider.chat(messages)` | sync | ✅ tool retry pass 2 |
| 3 | `runtime/julia_session.py:329` | `self.provider.chat(messages)` | sync | ✅ tool result pass 3 |
| 4 | `runtime/julia_session.py:196` | `self.provider.stream_async(messages)` | async | ✅ streaming path |
| 5 | `runtime/session_store.py:119` | `js.provider.chat(...)` | sync | ⚠️ title generation |
| 6 | `runtime/session_recorder.py:101` | `provider.chat(...)` | sync | ⚠️ memory consolidation |
| 7 | `runtime/session/summarizer.py:50` | `provider.chat(...)` | sync | ⚠️ session summary |

### Brain adapter paths (julia_ai_assistant)

| # | File | Call | Type | Production? |
|---|------|------|------|-------------|
| 8 | `server_v2_1.py:391` | `provider.chat(messages)` | sync | ✅ OLD voice path |
| 9 | `server_v2_1.py:541` | `provider.chat(messages)` | sync | ✅ OLD chat endpoint |
| 10 | `voice_api/openai_compat.py:130` | `provider.stream_async(prepared.messages)` | async | ✅ S2S/voice streaming |
| 11 | `voice_api/openai_compat.py:181` | `provider.stream_async(prepared.messages)` | async | ✅ S2S non-stream |
| 12 | `voice_api/julia_core_adapter.py:80` | `provider.chat(...)` | sync | ⚠️ legacy adapter |

### gateway paths

| # | File | Call | Type | Production? |
|---|------|------|------|-------------|
| 13 | `runtime/gateway_server.py:273` | `js.chat(text)` → `provider.chat()` | sync | ⚠️ Gateway HTTP /chat |
| 14 | `runtime/gateway_server.py:365` | `js.chat(text)` → `provider.chat()` | sync | ⚠️ Gateway WS voice |
| 15 | `runtime/gateway.py:38` | `self._js.chat(text)` | sync | ⚠️ Gateway internal |

### Summary

**5 distinct cognitive ingress points** in production:

1. JuliaSession._chat_impl() — via ConversationRuntime (native text/voice turn)
2. JuliaSession.process_stream() — native streaming
3. server_v2_1 direct — old chat endpoint (legacy)
4. openai_compat S2S — caller-owned history voice path
5. Gateway :8100 — direct js.chat() (not in product topology)

Only #1 and #2 go through the full cognitive pipeline (persona, interaction, market, capability, tools).

## P0A-2: Model-Visible Context Path Audit

### Context sources (what the model actually sees)

| Source | Injection point | Bypasses Context OS? |
|--------|----------------|---------------------|
| Identity/persona | `_prepare_turn()` string concat → system message | ✅ YES |
| Bootstrap (memory files) | `_prepare_turn()` / `_load_recent_experiences()` | ✅ YES |
| Conversation history | `ctx.history[-20:]` → messages.extend | ✅ YES |
| Interaction state | `ctx.interaction.to_context()` → string concat | ✅ YES |
| Market evidence | `_resolve_market_context()` → string concat | ✅ YES |
| Capability manifest | `self.capability.tool_manifest()` → string concat | ✅ YES |
| Conversation state | `_build_conversation_state()` → string concat | ✅ YES |
| Tool results | Direct `messages.append(tool_result)` | ✅ YES |
| Voice bootstrap history | `shared_orchestration._build_julia_system()` → BOOTSTRAP + TOOLS_PROMPT + VOICE_PROMPT | ✅ YES |
| SessionStore Wake State | `_load_recent_experiences()` → string concat | ✅ YES |

### Conclusion

**100% of model-visible context bypasses the Context OS pipeline.** The `context_os/planner.py`, `resolver.py`, `block.py` modules exist but are not in the production cognitive path. All model context is assembled through manual string concatenation in `_prepare_turn()` and `_build_julia_system()`.

### Direct injections that should be ContextSources

```
IdentitySource     → _identity_system (persona + bootstrap)
ConversationSource → ctx.history[-20:] (hardcoded window)
InteractionSource  → ctx.interaction.to_context()
ExperienceSource   → _load_recent_experiences() (SessionStore Wake State)
CapabilitySource   → self.capability.tool_manifest()
DomainEvidenceSource → _resolve_market_context() (Market Brain)
```

## P0A-3: Streaming / Non-Streaming / Voice Differential

### Text non-streaming

```
crt.process_turn(cognitive_fn=js.process)
  → js.process() → TurnContext
  → _chat_impl() → _prepare_turn() → provider.chat()
  → tool_call detect → execute → provider.chat() again
  → self.history.append(user+assistant)
  → relationship.update() → recorder.record()
  → crt persists user+assistant (via process_turn wrapper)
```

Conversation write: **double persistence** — crt.process_turn() persists + _chat_impl appends to self.history.

### Text streaming

```
Brain SSE → crt.begin_turn_streaming()
  → js.process_stream() → _prepare_turn() → provider.stream_async()
  → crt.commit_streaming_turn()
```

Differences from non-streaming:
- ❌ No tool_call detection
- ❌ No tool execution
- ❌ No action lifecycle
- ❌ No SessionRecorder
- ❌ No turn.completed event
- ❌ No conversation state update
- ❌ No relationship update
- ✅ Same _prepare_turn() context assembly
- ✅ Same persona/interaction/market/capability injection

### Voice/S2S (openai_compat)

```
S2S → /v1/chat/completions
  → prepare_voice_turn() → external_history → _build_julia_system()
  → provider.stream_async(prepared.messages)
```

Differences from text:
- ❌ Does not go through ConversationRuntime (unless conversation_id present)
- ❌ Uses caller-owned external_history as authority
- ✅ conversation_id present → routes through native _stream_turn → same as text stream
- ❌ Different context assembly: BOOTSTRAP + TOOLS_PROMPT + VOICE_PROMPT vs _prepare_turn()

### Three cognition semantics, not one

| Feature | Text non-stream | Text stream | Voice/S2S |
|---------|---------------|-------------|-----------|
| Persona | ✅ | ✅ | ✅ |
| Market context | ✅ | ✅ | ❌ (only if B1 triggers) |
| Tool execution | ✅ | ❌ | ❌ |
| Action lifecycle | ✅ | ❌ | ❌ |
| Recorder | ✅ | ❌ | ❌ |
| Interaction state | ✅ | ✅ | ❌ |
| Conversation authority | ✅ (dual persist) | ✅ | ❌ (unless conv_id) |

## P0A-4: Reasoning-like Module Classification

### COGNITIVE — should belong to LLM cognition loop

| Module | Current behavior | Concern |
|--------|-----------------|---------|
| `workflow_router.py` | Market intent → hardcoded capability dispatch | Replaces LLM tool-need recognition |
| `reasoning/intents/market_brief.py` | Keyword-based market intent resolution | Pre-cognitive intent classification |
| `reasoning/market_brief_pipeline.py` | Composed market intelligence pipeline | Domain workflow decides investigation path |
| `server_v2_1_semantic_router.py` | LLM-based intent → capability routing | Borderline — LLM is involved, but routing replaces model tool choice |

### STRUCTURAL — Core may retain

| Module | Why |
|--------|-----|
| `context_os/planner.py` | Domain-independent context planning |
| `context_os/resolver.py` | Dedup, rank, budget — structural |
| `context_os/block.py` | ContextBlock data structure |
| `context_os/reconstruction.py` | Continuity → Context bridge |
| `continuity/checkpoint.py` | Identity checkpoint persistence |
| `continuity/recovery.py` | Recovery plan execution |

### POLICY / GOVERNANCE — Core may retain

| Module | Why |
|--------|-----|
| `continuity/policy.py` | Continuity classification |
| `memory/governance/` | Memory admission policy |
| `alignment_os/contracts.py` | Provider-neutral behavior contracts |
| `capability/policy.py` | Permission policy |

### DOMAIN CAPABILITY — belongs to provider layer

| Module | Why |
|--------|-----|
| `capability/financial/research/*` | Financial domain analysis |
| `mcp_client/` | Market Brain transport |
| `capability/market_evidence_formatter.py` | Domain-specific formatting |
| `experience/market_brief_artifact.py` | Financial artifact |

### TRANSPORT / EXECUTION — Runtime / Gateway

| Module | Why |
|--------|-----|
| `gateway/ws_server.py` | WebSocket transport |
| `runtime/gateway_server.py` | HTTP + WS gateway |
| `runtime/conversation_runtime.py` | Turn lifecycle |
| `runtime/action.py` | Action lifecycle tracking |

### LEGACY / REMOVE candidates

| Module | Why |
|--------|-----|
| `conversation_cognition/*` | Pre-CORE-C1 cognition modules — not in production path |
| `cognitive_router.py` | Unused in production |
| `self_model/*` | Not bound to production cognitive pipeline |
| `observer/pilot_observer.py` | Experimental, not in production |
| `awareness/*` | Experimental, not in production |
| `behavior/*` | Benchmark/comparison, not cognition |
| `conversation_behavior.py` | Legacy conversation analysis |

### UNRESOLVED — requires Contract discussion

| Module | Concern |
|--------|---------|
| `voice_os/emotion_state.py` | Claims CognitiveEmotion ownership — conflicts with UA §17.4 |
| `relationship/runtime.py` | Splits relationship state across two modules |
| `narrative/rk_compiler.py` | Domain-specific narrative compilation |
| `compact/*` | Pre-CXT-C1 compact design — may need rework |

## P0A-5: Production Contract Input Ledger

| Production Fact | Architectural Concern | Affected Contract |
|----------------|---------------------|-------------------|
| `_prepare_turn()` string concat | Model-visible context bypass | C-03 Context OS |
| `history[-20:]` hardcoded window | No budget/projection policy | C-03 Context OS |
| `_load_recent_experiences()` Wake State | Legacy SessionStore as cognition source | C-03, C-05 |
| Stream path skips tool execution | Streaming ≠ non-streaming cognition | C-00, C-01 |
| Voice/S2S uses caller-owned history | Dual conversation authority | C-02, C-10 |
| WorkflowRouter pre-cognitive intent | Runtime semantic routing | C-00, C-08 |
| MarketBriefPipeline domain workflow | Domain decides investigation path | C-00, C-08 |
| `voice_os/emotion_state.py` CognitiveEmotion | Voice owns emotion cognition | C-11 |
| Double persistence (crt + js) | Two write paths for same turn | C-01, C-02 |
| `server_v2_1.py` direct chat | Legacy cognitive ingress | C-01, P8 |
| Gateway :8100 direct js.chat() | Non-ConversationRuntime path | C-01, C-10 |
| Relationship state split | Ghost authority concern | C-04, C-05 |
| `conversation_cognition/` unused | Dead cognitive code | P8 |

## Current Production Reality Map

```
                    User Input
                        │
        ┌───────────────┼───────────────┐
        │               │               │
    Text (native)   Voice (S2S)    Gateway :8100
        │               │               │
  ConversationRuntime  openai_compat  js.chat()
        │               │               │
        └───────┬───────┘               │
                │                       │
           _prepare_turn()  ←── ALL paths converge here or _build_julia_system()
                │
    ┌───────────┼───────────┐
    │           │           │
  identity   history[-20:]  market
  bootstrap  interaction   capability
  wake_state  conv_state   tool_results
    │           │           │
    └───────────┴───────────┘
                │
          [system message]
          + history messages
          + current user
                │
          ModelProvider
                │
    ┌───────────┴───────────┐
    │                       │
  tool_call?            final reply
    │                       │
  execute → append    Conversation commit
  provider again           │
    │                  Voice/Client
  final reply

❌ Context OS: NOT in production path
❌ Structured context: NOT in production path
❌ Budget / projection: NOT in production path
❌ Single streaming/non-streaming pipeline: NOT unified
❌ Single conversation authority: NOT unified
```

### Unresolved Architecture Ambiguities

1. Is `_prepare_turn()` the permanent Context OS or a transitional bypass?
2. Does `history[-20:]` stay as policy or become ActiveTail?
3. Are streaming and non-streaming the same cognitive pipeline or different?
4. Should Voice/S2S own its own conversation history or use ConversationRuntime?
5. Should WorkflowRouter/B2 semantic router be in the cognitive or infrastructure layer?
6. Does `voice_os/emotion_state.py` own CognitiveEmotion or is it transport-only?
7. Is `server_v2_1.py` the production Brain or legacy compatibility?
8. Should `conversation_cognition/` modules be removed or re-integrated?

These ambiguities must be resolved before C-00 can be frozen.

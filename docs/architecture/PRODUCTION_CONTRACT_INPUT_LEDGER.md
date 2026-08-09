# P0-A — Production Contract Input Ledger

**Status**: READ-ONLY AUDIT
**Date**: 2026-08-09
**Based on**: PRODUCTION_COGNITIVE_PATH_AUDIT.md

## C-00 Cognitive Boundary

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| `_prepare_turn()` string concat assembles all model context | Defines model-visible boundary in code, not contract | Freeze where Runtime ends and LLM begins |
| WorkflowRouter pre-classifies market intent | Replaces LLM tool-need recognition | Classify as infrastructure routing or cognitive overreach |
| Streaming path skips tool two-pass | Different cognition for stream vs non-stream | Define streaming contract: same cognition or declared difference |
| `server_v2_1_semantic_router.py` uses LLM to route | LLM is involved but routing replaces model tool choice | Classify boundary |

## C-01 Runtime Execution Contract

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| Double persistence: crt + js both write | Two write authorities for same turn | Single canonical turn lifecycle |
| Streaming: begin → stream → commit vs non-stream: process_turn | Two different turn lifecycles | Unify or document difference |
| `js.chat()` / `js.chat_async()` still public | Legacy singleton entry bypasses ConversationRuntime | Deprecate or route through crt |
| Gateway :8100 direct `js.chat()` | Non-ConversationRuntime cognitive path | Declare production topology or migrate |
| `server_v2_1.py` direct `provider.chat()` | Third cognitive ingress | Declare legacy or migrate |

## C-02 Conversation Authority

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| Voice/S2S uses caller-owned `external_history` | Dual conversation authority | Route voice through ConversationRuntime |
| `ctx.history[-20:]` as sole policy | No ActiveTail, no StructuredCompact | Replace with Context OS lifecycle |
| External turn import exists (5fded26) | Implementation exists but contract not frozen | Re-audit against C-02 |

## C-03 Context OS

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| `_prepare_turn()` string concat | 100% context bypass | Replace with ContextSources → ContextBlock[] → package |
| `history[-20:]` hardcoded | No budget, no projection, no provenance | Replace with ActiveTail + StructuredCompact |
| `_load_recent_experiences()` Wake State | Legacy SessionStore as cognition source | Migrate to ExperienceContextSource |
| Market evidence injected by string concat | Domain evidence bypasses Context OS | Route through DomainEvidenceSource |
| `tool_manifest()` injected by string concat | Capability manifest bypasses Context OS | Route through CapabilityContextSource |
| Tool results appended directly to messages | Bypasses Context OS incremental projection | Route through Context OS delta |

## C-04 Identity / Persona

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| `_identity_system` hardcoded string | Identity is prompt text, not governed contract | Define IdentityContract schema |
| BOOTSTRAP loads all memory files flat | Autobiography is file dump, not structured identity | Separate Identity anchors from NarrativeExperience |
| `persona/feature_store.py` traits injection | Persona traits are string append, not projection | Define Persona projection pipeline |

## C-05 Memory OS

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| `_load_recent_experiences()` reads SessionStore | SessionStore as Working Memory | Migrate to governed Memory OS |
| `session_recorder.py` writes diary | Memory formation without governance pipeline | Route through Memory governance |
| `session/summarizer.py` LLM summary | Summary treated as memory without provenance | Add provenance + governance |
| `relationship/runtime.py` state | Relationship state split across modules | Consolidate into Identity + Memory |

## C-06 Continuity OS

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| `ConversationInteractionState` rebuild from messages | Interaction state is derived, not checkpointed | Define L1 Session State contract |
| No Normal Resume vs Continuity Recovery distinction | All resume is implicit | Implement distinct paths |
| `continuity/checkpoint.py` compact-only | Checkpoint only for compact, not restart/provider switch | Extend to full Continuity OS scope |
| `context_os/reconstruction.py` only for compact | Reconstruction only in simulation | Bind to production recovery |

## C-07 ModelProvider

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| `DeepSeekProvider.chat()` + `stream_async()` | Two transport modes, one provider | Freeze as ModelProvider contract |
| Provider called from multiple ingress points | No single provider invocation authority | Route through Runtime |
| `alignment_os/adapter.py` transforms messages | Alignment mixed with context assembly | Separate Alignment from Context |

## C-08 Capability / Tool

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| Tool two-pass in non-stream only | Inconsistent tool support | Unify tool loop |
| `detect_tool_call()` regex | Fragile tool detection | Freeze tool request protocol |
| Tool results appended to messages directly | No Context OS re-entry | Route through Context OS incremental projection |
| Market MCP tools called pre-cognitively (B1) | Deterministic routing replaces model tool choice | Classify: infrastructure or cognitive |

## C-09 Alignment

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| `alignment_os/adapter.py` adapts messages | Good — provider adaptation | Keep as Alignment implementation |
| `alignment_os/contracts.py` behavior constraints | Good — provider-neutral contracts | Keep |

## C-10 Gateway / Client

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| `gateway_server.py` :8100 direct js.chat() | Non-ConversationRuntime cognitive path | Declare topology or migrate |
| `openai_compat.py` S2S path | Voice uses caller-owned history | Route through ConversationRuntime |
| `server_v2_1.py` :18089 direct chat | Legacy cognitive ingress | Declare legacy or migrate |
| `conversation_routes.py` native turn API | Correct — thin adapter over ConversationRuntime | Keep, refine |

## C-11 Voice / Media

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| `voice_os/emotion_state.py` CognitiveEmotion | Claims emotion ownership | Limit to transport/presence only |
| `voice_os/prosody.py` SpeechProsodyPlanner | Good — prosody mapping | Keep as transport |
| Voice path uses different context assembly | Different cognition for voice | Unify with text cognitive path |

## C-12 Evidence / Action / Trace

| Production Fact | Concern | Resolution Required |
|----------------|---------|-------------------|
| `runtime/action.py` per-turn action tracking | Good — correlation_id keyed | Keep, freeze contract |
| `events/store.py` event persistence | Good — append-only, causation tracked | Keep, freeze contract |
| `runtime/trace_pipeline.py` | Exists but not in production path | Bind or remove |

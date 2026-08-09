# C-07 — ModelProvider Contract

**Status**: FROZEN
**Date**: 2026-08-10
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §7
**Depends on**: C-00 (07f0ff0), C-01 (f79db0d), C-03 (4b1625e)
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Core Definition

```
ModelProvider supplies live cognitive inference.
It is replaceable infrastructure, but the cognition executed
through it is not reducible to ordinary tool execution.
```

ModelProvider is the cognitive substrate on which Julia performs live cognition. It is NOT a CapabilityProvider, NOT a DomainProvider, NOT an identity authority, NOT a continuity authority.

## 2. Three Provider Classes — Formalized

| Class | Role | Cognitive? | Example |
|-------|------|-----------|---------|
| **ModelProvider** | Live cognition execution | YES | Claude, GPT, DeepSeek, local model |
| **CapabilityProvider** | External capability/evidence | NO | Filesystem, web, email, database |
| **DomainProvider** | Knowledge/evidence supply | NO | Market data, project database, docs |

```
ModelProvider ≠ CapabilityProvider
ModelProvider ≠ DomainProvider
```

## 3. ModelProvider Does NOT Own Julia

```
ClaudeProvider / GPTProvider / DeepSeekProvider / LocalModelProvider
  = cognitive substrate implementations
  ≠ Julia identity owner
  ≠ Julia continuity owner
  ≠ Julia memory owner
  ≠ Julia conversation owner
```

Changing ModelProvider changes the cognitive substrate, not the canonical agent authorities (aligned with C-06 §12).

## 4. Input Must Come from Governed Cognitive Path

```
Canonical Authorities → Context OS → CognitiveContextPackage → Alignment → ModelProvider
```

Forbidden:
```
ModelProvider → fetch identity by itself
ModelProvider → fetch memory by itself
ModelProvider → read client history by itself
ModelProvider → assemble system prompt by itself
Provider adapter → secretly adds/removes personality
Provider adapter → injects provider-specific Julia definition
```

## 5. ModelInferenceRequest

Provider-independent logical object:

```
ModelInferenceRequest {
    request_id, turn_id, generation_id
    provider_id, model_id
    adapted_context         // post C-03 + C-09
    capability_descriptors[]
    inference_controls
    streaming_mode
    cancellation_token
    provenance_refs
    trace_metadata
}
```

`adapted_context` is the Alignment-processed CognitiveContextPackage. ModelProvider does not decide what history, identity, memory, or context to include.

## 6. Provider-Specific Format ≠ Architecture Truth

```
CognitiveContextPackage → Alignment → Claude message format
CognitiveContextPackage → Alignment → GPT message format
```

Provider transport format (system/user/assistant/tool messages, prompt strings, etc.) is a rendering detail. It must not dictate canonical architecture schema.

## 7. ModelInferenceResult

```
ModelInferenceResult {
    generation_id
    completion_status
    content
    capability_requests[]     // tool calls from model cognition
    expressive_intent
    provider_usage
    model_metadata
    finish_reason
    error
    trace_refs
}
```

Streaming: `ModelDelta* → ModelInferenceResult` — same logical result, different transport.

## 8. Streaming / Non-Streaming Semantic Parity

`generate()` and `stream()` may differ in transport API. Must share: same context semantics, same provider capability semantics, same tool-call semantics, same generation identity, same completion semantics, same cancellation semantics.

```
Streaming must not expose a second ModelProvider architecture.
```

## 9. Tool Call = Cognitive Output, Not Tool Execution

Model output "I need capability X with args Y" is a cognitive decision — a CapabilityRequest within the ModelInferenceResult. Runtime/C-08 validates, authorizes, executes. ModelProvider does not execute tools directly.

```
ModelProvider → CapabilityRequest → Runtime/C-08 → ToolResult → Context OS → ModelProvider continuation
```

## 10. Tool Continuation = Same Turn

C-01: same `turn_id`. C-07: `generation_id` increments (G1 → tool call → G2). Same turn, different generation instances.

## 11. ToolResult Must Re-Enter via Context OS

Forbidden: `messages.append(tool_result); provider.chat(messages)`.

Correct: `ToolResult → C-03 incremental projection → Alignment → new ModelInferenceRequest → ModelProvider`. ToolResult is model-visible information and must pass through Context OS.

## 12. Provider Capability Metadata

```
ModelCapabilities {
    context_window, streaming, native_tools, parallel_tool_calls
    structured_output, vision, audio_input, audio_output
    cancellation, reasoning_controls, system_role_support
    provider_limits
}
```

Describes what the model CAN do. Does not determine what Julia SHOULD think. Provider capability ≠ cognitive policy.

## 13. Provider Capability ≠ Cognitive Policy

Forbidden:
```
if Claude → inject rich narrative
if GPT → inject short persona
if local → remove relationship memory
```

Provider capability affects: encoding, token constraints, tool syntax, supported modalities, streaming, structured output. It does not affect canonical meaning. Specific adaptation by C-09 Alignment.

## 14. Model Output ≠ Durable Truth

A model saying "I think this experience changed me" is live cognitive output. It may become Conversation fact (Julia said it — C-02). It does not automatically become Memory, Identity, or Continuity truth unless governed through the corresponding authority.

```
ModelInferenceResult →X Identity update
ModelInferenceResult →X Memory permanent write
```

## 15. Provider Session ≠ Conversation / Continuity

Provider `thread_id`, `conversation_id`, `session_id`, `response_id` are optimization/transport handles. They are not Julia conversation identity or continuity identity. Provider session loss must not destroy Julia — canonical authorities are in Core.

## 16. Provider-Side State = Ephemeral

Claude thread, OpenAI response chain, Gemini session, local KV cache → performance optimization only. Architecture must allow: delete all provider state → reconstruct from Core authorities → continue Julia (C-06 continuity test scenario).

## 17. Provider Switch Invariant

Claude → GPT must not require identical output. Must satisfy: same canonical Identity, same relevant Conversation truth, same protected Memory refs, same Continuity conditions, same governed Context semantics. Allowed to differ: reasoning style, association, wording, cognitive texture.

```
Provider equivalence = architectural equivalence of inputs/authorities,
not behavioral equivalence of outputs.
```

## 18. ModelProvider Error Taxonomy

```
ProviderUnavailable, ModelUnavailable, RateLimited, ContextOverflow
InvalidRequest, ToolProtocolError, StreamInterrupted
GenerationCancelled, GenerationTimeout, ProviderInternalError
UnsupportedCapability
```

Runtime handles lifecycle per C-01. Execution failure ≠ cognitive truth ("provider timeout" ≠ "Julia didn't want to answer").

## 19. Context Overflow — No Silent Truncation

Provider rejects oversized context → Provider reports budget/capability → Context OS rebudgets → new CognitiveContextPackage → Alignment → ModelProvider.

```
Provider may reject oversized context.
Provider may not silently become Context OS.
```

## 20. Retry ≠ New Cognition Turn

Infrastructure retry = same logical turn. Whether `generation_id` is reused or incremented is an API decision, but tracing must show retry lineage. Model may produce different output on retry — only the final accepted generation enters Conversation finalization.

## 21. Fallback Model — Must Be Traceable

```
Claude fails → silently use local model → ❌ untraceable
Claude fails → trace records fallback → ✅ traceable
```

At minimum: `requested_model`, `actual_model`, `fallback_reason`. Context/Continuity may handle model switch. Provider layer must not pretend "same model executed."

## 22. Model Version = Cognition Provenance

Every generation records: `provider`, `model`, `model_version` (if available), `inference_settings`. This is provenance for debugging, cross-model comparison, continuity experiments, and AT benchmarks — not for "copying consciousness."

## 23. Reasoning Controls Boundary

Provider-specific `temperature`, `top_p`, `thinking_budget`, etc. are inference controls. They are NOT: identity mutation, context selection, continuity policy. C-09 Alignment maps unified configuration to provider-specific parameters.

## 24. Hidden Chain-of-Thought — Excluded from Persistence

Provider internal reasoning, hidden chain-of-thought, KV state → NOT Core persistence. NOT Memory, NOT Continuity state, NOT Conversation, NOT Identity. Julia continuity depends on canonical observable/governed artifacts, not preservation of vendor-private internal reasoning.

```
Continuity must not depend on preservation of provider-private reasoning state.
```

## 25. ModelProvider Does Not Write Canonical Conversation

```
ModelProvider → ModelInferenceResult → Runtime → ConversationRuntime → ConversationMessage (C-02)
```

Not: `ModelProvider → database transcript`.

## 26. ModelProvider Does Not Write Memory / Identity / Continuity

ModelProvider output → candidate → corresponding governance (C-05, C-04, C-06). No direct provider → persistence path.

## 27. Voice S2S — No Alternate Architecture

Native realtime/S2S is a transport/cognitive execution optimization. Even if provider supports speech-in/speech-out/realtime session, it must not bypass: Conversation, Context OS, Identity, Memory, Continuity, Capability. C-11 defines specific integration.

## 28. P0-A Disposition — 15 Call Sites, 5 Ingress

| Call Site | Type | Verdict |
|-----------|------|---------|
| `julia_session.py:303` provider.chat() | native non-stream | KEEP — primary cognitive ingress |
| `julia_session.py:196` provider.stream_async() | native stream | KEEP — streaming ingress |
| `julia_session.py:317,329` provider.chat() | tool continuation | KEEP — same turn |
| `server_v2_1.py:391,541` provider.chat() | legacy chat | LEGACY — migrate to native |
| `openai_compat.py:130,181` provider.stream_async() | S2S voice | CONVERGE — route through native turn path |
| `gateway_server.py:273,365` js.chat() | gateway | LEGACY — not in product topology |
| `session_store.py:119` provider.chat() | title gen | KEEP — structural infra |
| `session_recorder.py:101` provider.chat() | consolidation | KEEP — governance infra |
| `session/summarizer.py:50` provider.chat() | summary | KEEP — governance infra |

Target: 5 ingress → allowed. 5 independent semantics → forbidden. All ingress converge on C-07 contract.

## 29. Core Architecture Diagram

```
       Canonical Authorities
               │
               ▼
           Context OS
               │
               ▼
     CognitiveContextPackage
               │
               ▼
           Alignment
               │
               ▼
    ModelInferenceRequest
               │
               ▼
     ┌──────────────────┐
     │  ModelProvider   │
     │ Claude/GPT/...   │
     └──────────────────┘
               │
               ▼
     ModelInferenceResult
       │              │
       │              └── CapabilityRequest
       │                        │
       │                     C-08
       │                        │
       │                  ToolResult
       │                        │
       │                     Context OS
       │                        │
       └────────────────────────┘
               │
               ▼
      ConversationRuntime
```

## 30. Forbidden Claims

```
❌ LLM = interpreter / renderer
❌ ModelProvider = ordinary capability
❌ Provider owns Julia identity / continuity
❌ Provider session = Conversation / Julia state
❌ Provider selects history / retrieves Memory / injects Persona
❌ Provider silently truncates Context
❌ Provider executes tools directly
❌ ToolResult bypasses Context OS
❌ Model output auto-becomes Memory / Identity
❌ Retry creates hidden second logical turn
❌ Fallback model is untraceable
❌ Native S2S creates alternate cognition architecture
❌ Continuity depends on hidden chain-of-thought
```

## 31. Acceptance Gates

- [x] ModelProvider = live cognitive substrate (§1)
- [x] Three provider classes separated (§2)
- [x] Provider does not own Julia authorities (§3)
- [x] Input must come from governed cognitive path (§4)
- [x] ModelInferenceRequest frozen (§5)
- [x] ModelInferenceResult frozen (§7)
- [x] Streaming/non-streaming semantic parity (§8)
- [x] Tool call = cognitive output, not tool execution (§9)
- [x] Tool continuation same turn, re-enters Context OS (§§10-11)
- [x] Provider capability metadata (§12)
- [x] Provider capability ≠ cognitive policy (§13)
- [x] Output ≠ durable truth (§14)
- [x] Provider session ≠ Conversation/Continuity (§15)
- [x] Provider-side state = ephemeral (§16)
- [x] Provider switch semantics (§17)
- [x] Model/version provenance (§22)
- [x] Context overflow → no silent truncation (§19)
- [x] Retry/fallback semantics (§§20-21)
- [x] Hidden reasoning excluded from persistence (§24)
- [x] ModelProvider cannot write Conversation (§25)
- [x] ModelProvider cannot write Identity/Memory/Continuity (§26)
- [x] Voice/S2S cannot bypass Core authorities (§27)
- [x] P0-A 15 call sites / 5 ingress dispositioned (§28)
- [x] Production changes = 0

## 32. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §7
Depends: C-00 (07f0ff0), C-01 (f79db0d), C-03 (4b1625e)
Input:   P0-A Production Reality Audit (9753a03)
Output:  Binding on C-08, C-09, C-11

C-07 FREEZE → C-08 Capability / Tool GO
```

# C-00 — Cognitive Boundary Contract

**Status**: FROZEN
**Date**: 2026-08-09
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §3, §4, §6, §7
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Purpose

This Contract defines the architectural boundary between:

- **LLM Cognitive System** — live understanding, reasoning, judgment, generation
- **Julia Core Runtime** — persistent nervous system, governance, infrastructure

It applies to ALL production cognitive paths (text, voice, streaming, non-streaming, tool continuation, recovery). No modality, transport, or domain exempts a path from this boundary.

## 2. Functional Cognition Definition

"Cognitive System" and "LLM cognition" are functional architecture terms denoting responsibility for: understanding, inference, reasoning, association, judgment, hypothesis formation, tool-need recognition, interpretation of evidence and tool results, and generation of responses and expressive intent. These terms do not imply or require subjective consciousness.

## 3. LLM Cognitive Responsibilities (CANONICAL)

The LLM Cognitive System owns:

| Responsibility | Description |
|---------------|-------------|
| Understand | Interpret user input in context |
| Assimilate | Integrate identity, context, experience into current self-model |
| Associate | Connect current input to relevant past experience |
| Reason | Perform inference over available information |
| Form hypotheses | Generate candidate explanations and predictions |
| Judge | Evaluate options, weigh evidence, reach conclusions |
| Interpret evidence | Make sense of tool results, domain facts, retrieved memory |
| Recognize tool need | Decide when more information or a capability is needed |
| Generate response | Produce the final Julia response |
| Produce expressive intent | Optionally indicate intended emotional/prosodic expression |

**Central principle**: LLM performs semantic cognition. Runtime may prepare conditions for cognition. Runtime must not precompute cognition.

## 4. Core Allowed Responsibilities (CANONICAL)

Core may perform:

| Category | Operations |
|----------|-----------|
| Lifecycle | Turn begin/commit/cancel, session management, concurrency, idempotency |
| Persistence | ConversationMessage storage, atomic writes, migration, retrieval |
| Validation | Schema, permission, policy, rate limiting, safety gates |
| Structuring | Organize context into frames, apply budget, sort, deduplicate |
| Provenance | Track source lineage, evidence refs, authority scores |
| Execution | Run capabilities, timeout, retry, cancel, record evidence |
| Infrastructure | Transport routing, event emission, tracing, recovery orchestration |
| Adaptation | Provider-specific message formatting, schema translation |
| Calculation | Deterministic computation where semantics are fully specified |

**Hard boundary**: Structural processing becomes cognitive intrusion when it resolves semantic meaning on Julia's behalf and the LLM merely verbalizes the result.

## 5. Cognitive Intrusion Test (CANONICAL)

To determine whether a module crosses the cognitive boundary:

```
If removing the LLM still leaves the semantic conclusion
substantially determined, Core has likely crossed the boundary.
```

**Outputs that typically remain in Core**:
- facts, evidence, constraints, candidate states, structured observations, budget limits, permission results, schema validation results, deterministic calculations

**Outputs that typically cross into cognition**:
- what Tony really means, what Julia should believe, what Julia should feel, which interpretation is correct, what Julia should conclude, what Julia should say

If a module's output falls in the second category and the LLM's role is reduced to verbalizing it, the module belongs in the LLM cognitive loop, not in Core infrastructure.

## 6. Router Boundary (CANONICAL)

### Allowed: Explicit Command Routing

```
explicit command → deterministic router → capability
```
Example: `/read file X`, `/search Y` — the user explicitly invokes a capability.

### Allowed: Infrastructure Routing

```
transport header → transport router → correct handler
```
Example: routing by modality, conversation_id, event type — purely infrastructural.

### Forbidden: Semantic Intent Routing

```
ambiguous natural language → Runtime decides exact intent → Runtime chooses path → LLM verbalizes
```
Example: WorkflowRouter classifying market intent and dispatching a domain workflow before the LLM has seen the input.

### Correct: Cognitive Tool Agency

```
user input → cognitive context → LLM understands intent → LLM may request capability
```

Runtime may expose capabilities. Runtime may deny unauthorized capabilities. Runtime must not impersonate the model's decision that a capability is needed.

## 7. Tool Cognitive Agency (CANONICAL)

Default flow:

```
LLM recognizes need
  → requests allowed capability
Runtime validates permission
  → executes capability
ToolResult + Evidence
  → Context OS incremental projection
  → CognitiveContextPackage delta
  → LLM continues cognition
```

- Runtime may deny, scope-limit, rate-limit, timeout, retry, cancel, or require confirmation for capabilities.
- Runtime must not infer a semantic answer and call tools to validate its own conclusion.
- Runtime must not silently choose a domain workflow instead of allowing LLM cognition.
- Narrow deterministic dispatch (explicit commands, infrastructure commands) is permitted as an exception.

## 8. Emotion / Expressive Intent Boundary (CANONICAL)

```
LLM → semantic/emotional interpretation → response + optional ExpressiveIntent

Core/Voice → validation → safety/policy constraint → prosody mapping → audio rendering
```

- LLM owns the current emotional/semantic interpretation.
- Core may validate, constrain, map, and render expressive intent.
- Core must not independently decide Julia's emotional state.
- Voice/Media Runtime provides transport and rendering, not emotional cognition.

Presence state (listening, thinking, speaking, interrupted) is transport metadata, not emotional cognition.

## 9. Provider Class Distinction (CANONICAL)

Three provider classes with distinct cognitive semantics:

| Class | Role | Cognitive? | Example |
|-------|------|-----------|---------|
| ModelProvider | Live cognition execution | YES | DeepSeek, GPT, Claude |
| CapabilityProvider | External capability/evidence | NO | File read, web search, MCP |
| MediaProvider | Media transformation | NO | ASR, TTS, avatar |

ModelProvider is the sole cognitive substrate. CapabilityProvider and MediaProvider supply structured results, not cognition.

## 10. Module Disposition Table

Based on P0-A Production Reality Audit. Each module classified against this Contract.

### KEEP — Core infrastructure

| Module | Classification | Verdict |
|--------|---------------|---------|
| `runtime/conversation_runtime.py` | Conversation lifecycle | KEEP |
| `runtime/julia_session.py` (process/process_stream) | Cognitive executor | KEEP WITH BOUNDARY |
| `runtime/action.py` | Action lifecycle | KEEP |
| `runtime/session_store.py` | Session metadata (legacy compat) | KEEP (mark transitional) |
| `runtime/session_recorder.py` | Memory consolidation | KEEP |
| `runtime/session/summarizer.py` | Structured summary | KEEP |
| `context_os/planner.py` | Context planning | KEEP |
| `context_os/resolver.py` | Context resolution | KEEP |
| `context_os/block.py` | ContextBlock data structure | KEEP |
| `context_os/reconstruction.py` | Continuity → Context bridge | KEEP |
| `continuity/checkpoint.py` | Identity checkpoint | KEEP |
| `continuity/recovery.py` | Recovery plan | KEEP |
| `continuity/policy.py` | Continuity classification | KEEP |
| `memory/governance/` | Memory admission | KEEP |
| `alignment_os/contracts.py` | Provider-neutral contracts | KEEP |
| `alignment_os/adapter.py` | Provider adaptation | KEEP |
| `capability/policy.py` | Permission policy | KEEP |
| `capability/manager.py` | Capability lifecycle | KEEP |
| `capability/market_evidence_formatter.py` | Evidence formatting | KEEP |
| `gateway/ws_server.py` | WebSocket transport | KEEP |
| `gateway/event_bus.py` | Event transport | KEEP |
| `gateway/protocol.py` | Event protocol | KEEP |
| `events/store.py` | Event persistence | KEEP |
| `events/models.py` | Event schemas | KEEP |

### KEEP WITH BOUNDARY — correct now, but must not expand

| Module | Classification | Verdict | Boundary |
|--------|---------------|---------|----------|
| `runtime/julia_session.py` (`_prepare_turn`) | Model context assembly | KEEP WITH BOUNDARY | Must migrate to C-03 Context OS; currently transitional bypass |
| `runtime/relationship.py` (ConversationInteractionState) | Derived interaction state | KEEP WITH BOUNDARY | Must remain derived cache, not Continuity authority |
| `capability/providers/ai_theme/` | Domain evidence provider | KEEP WITH BOUNDARY | Must not become second cognitive authority |

### MOVE TO LLM COGNITION — currently in Core, should be cognitive

| Module | Classification | Verdict | Target |
|--------|---------------|---------|--------|
| `workflow_router.py` | Market intent → capability dispatch | REWRITE AS STRUCTURAL | Remove pre-cognitive intent routing; expose capability manifest, let LLM decide |
| `reasoning/intents/market_brief.py` | Keyword-based market intent | MOVE TO LLM COGNITION | Intent classification belongs in cognitive loop |
| `reasoning/market_brief_pipeline.py` | Composed market investigation | MOVE TO LLM COGNITION | Domain workflow should not decide investigation path pre-cognitively |
| `server_v2_1_semantic_router.py` | LLM-based capability routing | MOVE TO LLM COGNITION | LLM tool-need recognition is cognitive, not infrastructural |

### MOVE TO DOMAIN CAPABILITY — not Core cognition, but valid domain logic

| Module | Classification | Verdict |
|--------|---------------|---------|
| `capability/financial/research/*` | Financial analysis | MOVE TO DOMAIN |
| `mcp_client/client.py` | MCP transport | MOVE TO DOMAIN |
| `experience/market_brief_artifact.py` | Financial artifact | MOVE TO DOMAIN |

### REWRITE AS STRUCTURAL — currently cognitive-like, should be infrastructure

| Module | Classification | Verdict |
|--------|---------------|---------|
| `capability/reflection.py` | Reflection orchestration | REWRITE — reflection should run through ModelProvider, Core orchestrates only |
| `narrative/rk_compiler.py` | Narrative compilation | REWRITE — remove semantic interpretation, keep structural compilation |
| `compact/simulator.py` | Compact simulation | REWRITE — keep as simulation harness, remove from production cognition |

### LEGACY / REMOVE — not in production path

| Module | Classification | Verdict |
|--------|---------------|---------|
| `conversation_cognition/*` | Pre-CORE-C1 cognition | REMOVE from production |
| `cognitive_router.py` | Unused | REMOVE |
| `self_model/*` | Not production-bound | REMOVE from production |
| `observer/pilot_observer.py` | Experimental | REMOVE from production |
| `awareness/*` | Experimental | REMOVE from production |
| `behavior/*` | Benchmark | KEEP as testing, not production cognition |
| `conversation_behavior.py` | Legacy | REMOVE |

### UNRESOLVED — requires additional Contract discussion

| Module | Classification | Concern |
|--------|---------------|---------|
| `voice_os/emotion_state.py` | Claims CognitiveEmotion ownership | Resolve in C-11: if transport-only, KEEP; if semantic, MOVE TO LLM |
| `relationship/runtime.py` | Relationship state split | Resolve in C-04/C-05: consolidate into Identity + Memory |
| `compact/*` (gates) | Pre-CXT-C1 design | Resolve in C-03/C-06: redesign against new compact/ActiveTail model |

## 11. Forbidden Claims

The following claims are architecturally invalid under this Contract:

```
❌ Runtime owns cognition
❌ Runtime decides Julia's conclusions
❌ Runtime decides Julia's feelings
❌ Runtime writes answers and LLM verbalizes them
❌ LLM = interpreter only
❌ LLM = renderer / prose formatter
❌ Voice OS owns CognitiveEmotion
❌ Alignment keeps the same agent the same agent
❌ IntentRouter decides semantic action before LLM cognition
❌ Domain workflow replaces LLM cognitive loop
```

## 12. Acceptance Gates

### C-00 Gate

- [x] Functional cognition formally defined (§2)
- [x] LLM cognitive responsibilities frozen (§3)
- [x] Core allowed deterministic responsibilities frozen (§4)
- [x] Cognitive intrusion test frozen (§5)
- [x] Router boundary frozen (§6)
- [x] Tool cognitive agency frozen (§7)
- [x] Emotion / expressive-intent boundary frozen (§8)
- [x] Provider class distinction frozen (§9)
- [x] 40+ reasoning-like modules mapped to C-00 verdict (§10)
- [x] No claim "Core owns cognition" survives (§11)
- [x] No claim "LLM = interpreter/renderer" survives (§11)
- [x] Production changes = 0
- [x] All unresolved modules have explicit path to resolution

## 13. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §3, §4, §6, §7
Input:   P0-A Production Reality Audit (9753a03)
Output:  Binding on C-01 through C-12

C-00 FREEZE → C-01 Runtime Execution GO
```

# C-01 — Runtime Execution Contract

**Status**: FROZEN
**Date**: 2026-08-09
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §6
**Depends on**: C-00 Cognitive Boundary (07f0ff0)
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Runtime Definition

Runtime is Julia's execution and lifecycle substrate.

```
Runtime orchestrates cognition.
Runtime does not perform cognition.
Runtime controls execution order, not semantic conclusion.
```

### Runtime Owns

| Category | Operations |
|----------|-----------|
| Process lifecycle | Start, shutdown, health, resource management |
| Session lifecycle | Create, resume, close, expire |
| Turn lifecycle | Begin, context-prepare, cognition-run, tool-continue, commit, cancel, fail |
| Execution ordering | Single-flight, concurrency isolation, turn serialization |
| Cancellation | Model cancellation, turn cancellation, speech interruption, client disconnect |
| Retry / idempotency | Duplicate detection, replay prevention, side-effect safety |
| Provider invocation | ModelProvider orchestration, tool execution dispatch |
| Recovery triggering | Detect recovery reason, invoke Continuity OS |
| Trace / correlation | correlation_id, causation chain, event emission |
| Presence state | Transport-level state: listening, thinking, speaking, idle, interrupted |

### Runtime Does NOT Own

Runtime must not own: semantic interpretation, intent understanding, reasoning, judgment, belief formation, emotional interpretation, response meaning, conversation canonical truth (→ C-02), context selection policy (→ C-03), continuity classification (→ C-06).

## 2. Turn Lifecycle

### Canonical States

```
CREATED
  ↓
ACCEPTED
  ↓
CONTEXT_PREPARED
  ↓
COGNITION_RUNNING
  │
  ├── TOOL_REQUESTED
  │     ↓
  │   TOOL_EXECUTING
  │     ↓
  │   TOOL_RESULT_PROJECTED
  │     ↓
  │   COGNITION_RUNNING
  │
  ↓
RESPONSE_PRODUCED
  ↓
CONVERSATION_COMMITTED
  ↓
COMPLETED
```

### Terminal States

```
CREATED → REJECTED        (validation failure)
Any     → CANCELLED        (explicit cancel)
Any     → INTERRUPTED      (barge-in / transport interrupt)
Any     → FAILED           (unrecoverable error)
```

### State Rules

- `CONVERSATION_COMMITTED` means canonical transcript is durable. Transport delivery (TTS, SSE, WebSocket) may continue after commit.
- `INTERRUPTED` does not automatically delete the canonical assistant message. Speech/media interruption ≠ conversation authority mutation.
- `CANCELLED` before `CONVERSATION_COMMITTED` → no durable trace. After commit → status preserved as `interrupted` or `failed`.
- `TOOL_REQUESTED` → `TOOL_EXECUTING` → `TOOL_RESULT_PROJECTED` → `COGNITION_RUNNING` is the same logical turn. `turn_id` unchanged throughout.

## 3. Turn Identity and Correlation

### ID Semantics

| ID | Scope | Meaning |
|----|-------|---------|
| `conversation_id` | Durable | Which conversation this turn belongs to |
| `turn_id` | Durable | One logical user→Julia cognitive turn. Stable across tool loops, retries |
| `request_id` | Transport | One runtime invocation/request attempt |
| `generation_id` | Model | One model generation instance. Multiple per turn when tools involved |
| `correlation_id` | Trace | Groups all events, actions, tool calls within one logical turn |

### Rules

- Same `turn_id` + same conversation = same logical turn. Tool continuation, retry, idempotent replay → same `turn_id`.
- `conversation_id` + `turn_id` together form the idempotency key.
- `generation_id` changes when model is re-invoked after tool result.
- `correlation_id` links events and actions. Must not collide across conversations.

## 4. Streaming and Non-Streaming Parity

### Invariant

```
Streaming is an output transport mode, not a separate cognition architecture.
```

### Shared Semantics

Both streaming and non-streaming MUST share:

- Same turn lifecycle (§2)
- Same context preparation (→ C-03)
- Same conversation authority (→ C-02)
- Same tool loop semantics (§7)
- Same cancellation semantics (§6)
- Same completion semantics
- Same idempotency semantics

### Transport Difference Only

```
Non-streaming:
  ModelOutput → final response

Streaming:
  ModelDelta* → final ModelOutput
```

Streaming pathway differs only in: output delivery chunking, cancellation timing, TTS scheduling. It does not differ in: what context the model sees, whether tools can be invoked, conversation commit semantics.

### Production Reality Note

P0-A identified 3 different cognition semantics (text non-stream, text stream, voice S2S). C-01 freezes the target: 5 ingress → allowed. 5 independent execution semantics → forbidden. Convergence is a production task (P1), not a contract rewrite.

## 5. Voice and Text Parity

Voice, text, web, and Electron turns map to the same `RuntimeTurn`.

Voice may add: ASR state, VAD, barge-in, speech_id, audio playback. Voice must not invent: voice-only context lifecycle, voice-only conversation history, voice-only cognitive state.

The cognitive execution contract is modality-independent. Media transport (C-11) wraps the same `RuntimeTurn`.

## 6. Cancellation and Interruption

### Types

| Type | Scope | Canonical Effect |
|------|-------|-----------------|
| Model cancellation | Stop current model generation | generation stops; turn may retry or continue |
| Turn cancellation | Cancel the logical turn | turn → CANCELLED; no durable trace before commit |
| Speech interruption | Stop TTS playback | media stops; canonical assistant message preserved |
| Client disconnect | Transport lost | turn may continue or cancel depending on phase |
| Runtime failure | Unrecoverable error | turn → FAILED; lock released; no durable trace before commit |

### Invariant

```
Runtime must not delete or mutate canonical conversation history
to implement transport cancellation.
```

Speech/media interruption is a transport concern. Whether the assistant message is `completed` or `interrupted` in canonical transcript is determined by C-02 Conversation Authority, not by C-01 Runtime.

## 7. Retry and Idempotency

### Idempotency Key

```
conversation_id + turn_id
```

Same key + same input → same logical turn. Must not produce duplicate messages, duplicate tool execution, or duplicate side effects.

### Retry Rules

| Scenario | Behavior |
|----------|----------|
| Same turn_id, same input, not yet completed | Resume or restart the turn |
| Same turn_id, same input, already completed | Return cached result; no re-execution |
| Same turn_id, different input | Reject with conflict |
| Network timeout during streaming | Retry with same turn_id; idempotent |
| Tool side-effect already executed | MUST NOT blindly replay; return conflict or require explicit confirmation |

### Side-Effect Safety

For capabilities with external side effects (write, send, execute): Runtime MUST NOT replay a completed external action on retry. The completed ToolResult with its evidence record is the authority. C-08 Capability Contract defines per-capability replay policy.

## 8. Runtime Orchestration Boundary

### Allowed

```
"Context ready"     → invoke ModelProvider
"Tool call requested" → authorize and execute
"Tool result ready" → project through Context OS
"Response produced" → persist and commit
"Recovery needed"   → invoke Continuity OS
```

### Forbidden

```
"User probably means X"     → pre-cognitive intent routing
"Therefore call financial tool" → semantic workflow dispatch
"Result means Y"               → Runtime interpretation of evidence
"Julia should answer Z"        → Runtime-authored conclusion
```

### Execution State ≠ Cognitive Truth

```
Runtime state THINKING    = model generation is running
Runtime state SPEAKING    = TTS/media output is active
Runtime state IDLE        = no active execution

These are execution/presence states, not cognitive ontology.
"Julia is thinking" is transport metadata, not a claim about
Julia's internal mental state.
```

## 9. RuntimeTurn Canonical Object

```
RuntimeTurn {
    conversation_id:    str       // durable conversation
    turn_id:            str       // logical turn identity
    request_id:         str       // transport invocation
    modality:           str       // text | voice
    state:              TurnState // lifecycle state
    context_package_ref: str|null // C-03 context reference
    generation_ids:     str[]     // model generation instances
    capability_calls:   str[]     // capability invocation refs
    cancellation_state: str|null  // cancel reason if applicable
    failure_state:      str|null  // error detail if failed
    started_at:         str       // ISO timestamp
    completed_at:       str|null  // ISO timestamp
}
```

RuntimeTurn is an execution-state object. It is not canonical conversation truth. ConversationMessage (C-02) is the durable transcript fact.

## 10. Contract Boundaries

| Concern | Owned By |
|---------|----------|
| Turn lifecycle + execution ordering | C-01 Runtime |
| What the model sees | C-03 Context OS |
| What is durably recorded | C-02 Conversation Authority |
| What survives restart/provider switch | C-06 Continuity OS |
| Whether a tool may be invoked | C-08 Capability |
| How media is rendered | C-11 Voice/Media |

## 11. Acceptance Gates

- [x] Runtime defined as execution/lifecycle substrate (§1)
- [x] Runtime non-cognition boundary references C-00 (§1)
- [x] RuntimeTurn canonical object defined (§9)
- [x] Turn lifecycle frozen with all states + terminal paths (§2)
- [x] 5 identity/correlation IDs defined with distinct semantics (§3)
- [x] Streaming/non-streaming semantic parity frozen (§4)
- [x] Voice/text semantic parity frozen (§5)
- [x] 5 cancellation/interruption types defined with canonical effects (§6)
- [x] Retry/idempotency with side-effect safety (§7)
- [x] Tool continuation remains same logical turn (§2, §3)
- [x] Execution state ≠ cognitive truth (§8)
- [x] Runtime does not own Conversation truth (→ C-02) (§10)
- [x] Runtime does not own Context selection (→ C-03) (§10)
- [x] Runtime does not own Continuity policy (→ C-06) (§10)
- [x] 5 production ingress → allowed; 5 independent semantics → forbidden (§§4-5)
- [x] Production changes = 0

## 12. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §6
Depends: C-00 Cognitive Boundary (07f0ff0)
Input:   P0-A Production Reality Audit (9753a03)
Output:  Binding on C-02 through C-12

C-01 FREEZE → C-02 Conversation Authority GO
```

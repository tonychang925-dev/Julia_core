# C-10 — Gateway / Client Contract

**Status**: FROZEN
**Date**: 2026-08-10
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §17, §25
**Depends on**: C-00 (07f0ff0), C-01 (f79db0d), C-02 (656d625), C-03 (4b1625e)
**Production basis**: P0-A Production Reality Audit (9753a03), Electron GAP-1, GAP-2
**Production code changes**: 0

## 1. Core Definition

```
Gateway transports commands and events.
Client renders and originates interaction.
Core owns agent state and canonical authorities.
```

```
Client  = body / presentation / interaction surface
Gateway = transport boundary
Core    = canonical agent authority
```

Forbidden equivalences:

```
Client cache      ≠ Conversation
Client history    ≠ Context
Client state      ≠ Continuity
Client persona    ≠ Identity
Client routing    ≠ cognition
```

## 2. Command Plane

```
Client → Gateway → Core
```

Commands: `send_user_input`, `open_conversation`, `cancel_turn`, `interrupt_output`, `request_history`, `request_status`, `confirm_capability`.

```
ClientCommand {
    command_id, command_type
    conversation_id, turn_id
    payload
    modality
    client_instance_id
    protocol_version
    issued_at
    correlation_id
}
```

Payload may contain current user input. Must NOT contain: `canonical_history_override`, `persona_override`, `memory_override`, `continuity_override` — unless a specific governed command explicitly defines them.

## 3. Event Plane

```
Core → Gateway → Client
```

Events: `turn.accepted`, `assistant.delta`, `assistant.completed`, `assistant.interrupted`, `conversation.updated`, `capability.confirmation_required`, `runtime.failed`, `presence.changed`.

```
CoreEvent {
    event_id, event_type
    conversation_id, turn_id, generation_id
    payload
    sequence
    emitted_at
    canonical_ref
    correlation_id
}
```

Distinguish: execution event, canonical conversation event, presentation event. `assistant.delta` ≠ `ConversationMessage completed`. Only `assistant.completed` with `canonical_ref` signals canonical finalization.

## 4. Canonical Identifiers

| ID | Origin | Client Role |
|----|--------|-------------|
| `conversation_id` | Core canonical | Transport only |
| `turn_id` | Runtime/Core (or client candidate accepted by Core) | Transport; client candidate may be accepted |
| `request_id` | Transport scope | Client generates |
| `client_message_id` | Presentation/local correlation | NEVER becomes canonical `message_id` |

Electron local message ID must not silently become canonical `message_id` unless C-02 import/append protocol explicitly accepts it.

## 5. Optimistic UI ≠ Canonical Completion

```
LOCAL_PENDING       — client-side optimistic render
CORE_ACCEPTED       — Core acknowledged receipt
CANONICAL_COMPLETED — durable ConversationMessage (C-02)
CANONICAL_INTERRUPTED — interrupted but durable (C-02)
FAILED              — Core rejected or error
```

Only Core acknowledgement may promote a client-presented artifact into canonical-completed representation. Local render ≠ canonical completion.

## 6. Client Cache = Disposable Projection

C-02 §11: client cache = presentation only. C-10 reinforces:

```
Delete Electron cache → reopen conversation → canonical history recoverable from Core.
```

If deleting cache loses Julia history → architecture violation. If cache survives but Core history missing → client must not overwrite Core.

## 7. Reconnect = Core-Authoritative Reconciliation

```
Electron reconnect → conversation_id → GET canonical Conversation → replace/reconcile presentation cache
```

Forbidden: Electron reconnect → send local history[] → Core assumes truth. Historical migration (M0) is a one-time governed process. Legacy import is not normal reconnect protocol.

## 8. Client Cannot Select Cognitive History

```
❌ Electron: history = cache[-20:]; send to Core
❌ Client selects messages important for model
```

```
✅ Client → current interaction + canonical identifiers
✅ Core → Conversation → Context OS → CognitiveContextPackage
```

Client may request conversation display range. Client may not select model-visible context.

## 9. Gateway ≠ Context Gateway

Gateway responsibilities: authentication, transport, serialization, connection management, command validation, event delivery, backpressure, reconnect, protocol versioning. Gateway must not: assemble prompt, select memory, inject identity, summarize history, decide Julia intent.

```
Gateway moves governed data; it does not govern cognition.
```

## 10. Event Ordering

Per connection: transport order. Per turn: monotonic sequence. Canonical conversation: canonical ordering from Core. Client may detect missing sequence, duplicate event, out-of-order delivery → request reconciliation. Client must not guess canonical order.

## 11. At-Least-Once Deduplication

Client deduplicates by `event_id` / `sequence` / `canonical_ref`. Command retry obeys C-01 idempotency: `command_id` / idempotency key. Network timeout → resend `send_user_input` must not create two turns.

## 12. Disconnect ≠ Turn Cancel

Network disconnect, client close, turn cancel, generation cancel, speech interrupt are distinct. Electron temporarily offline → connection lost must not automatically delete current turn or cancel Julia cognition — unless protocol policy explicitly defines it. Reconnect → reconcile from Core truth.

## 13. Interrupted Assistant — Must Remain Visible

C-02: canonical assistant message, `status = interrupted`, content = actually committed/emitted. C-10: Client presentation may visually distinguish interrupted content but must not erase canonical interrupted history.

```
Electron GAP-2: reconcile filters interrupted assistant message → REWRITE.
Canonical interrupted content must remain renderable.
```

## 14. Streaming Delta ≠ Canonical Message

`assistant.delta` is a presentation/execution event. Deltas may arrive → connection lost → final canonical content determined by Core. Electron may buffer locally. Final canonical completed/interrupted message → reconciliation authority. Presentation delta loss must not cause canonical history loss. Streaming transport is optimization; canonical GET is recovery guarantee.

## 15. Voice/Text/Web — Same Logical Protocol

Transport may differ (WebSocket, HTTP, IPC, native bridge, future mobile). Logical protocol must be consistent: `ClientCommand`, `CoreEvent`, conversation identifiers, turn semantics, canonical reconciliation. Voice must not define `voiceConversation`, `voiceHistory`, `voiceTurnAuthority`. C-11 adds media lifecycle only.

## 16. Presence = Execution State

`idle`, `listening`, `processing`, `speaking`, `disconnected` are presentation/execution states. C-01: execution state ≠ cognitive truth. "Julia is thinking..." in protocol = model/runtime processing active. Not a claim about Julia's psychological state.

## 17. Authentication ≠ Relationship Identity

Gateway uses: authenticated principal, client identity, session credentials, authorization scope. Forbidden: caller says "I'm Tony" → Relationship Identity grants access. C-04 role anchor ≠ access-control token. AT-15 directly applies.

## 18. Multi-Client Concurrency

One canonical Conversation, many client projections. Clients cannot be mutual authority. Core sequence, canonical event, reconciliation resolve concurrency. Specific conflict strategy is implementation detail; authority boundary is frozen.

## 19. Client Cannot Persist Unfinished Cognition

Half-stream "Tony，我觉得这个架..." → Electron may cache for UX. Must not write `assistant completed` to local persistent history and later sync to Core. Final status from Core canonical.

## 20. Protocol Versioning

`protocol_version`, `supported_version`, `minimum_version`, `feature_flags`. Incompatible → explicit failure. Client must not guess schema and auto-continue, causing authority drift.

## 21. Electron — No Direct Persistence Access

Electron → Gateway/Core API. Not: Electron → SQLite/Postgres/MemoryStore directly. Client must not become authority peer. Historical legacy source read limited to M0-A/M0-B adapter scope, not runtime pattern.

## 22. Gateway API Classification

| Category | Examples |
|----------|----------|
| Conversation Commands | POST user turn, GET canonical conversation |
| Runtime Commands | CANCEL turn, INTERRUPT output |
| Capability Commands | CONFIRM action |
| Projection Queries | GET conversation display range |
| Health / Protocol | GET status, protocol handshake |

Forbidden API shapes: POST full prompt, POST full history, POST Julia persona, POST memory state.

## 23. Electron Gaps Disposition

**GAP-1**: Optimistic local message defaults completed.
→ C-10 §5: client optimistic state cannot impersonate canonical completion.
→ Disposition: REWRITE AFTER C-10 FREEZE.

**GAP-2**: Reconcile filters interrupted assistant message.
→ C-02 + C-10 §13: canonical interrupted content must remain renderable.
→ Disposition: REWRITE / STOP FILTERING, subject to C-11 emitted-content semantics.

## 24. C-10 ↔ C-11 Boundary

C-10 owns: commands, events, connection, canonical reconciliation, client projection, turn identifiers, stream transport semantics.

C-11 owns: ASR, VAD, audio capture, audio playback, barge-in, speech interruption, prosody, S2S.

C-10 defines how media events become protocol events and canonical interaction. C-10 does not define when ASR finalizes, how TTS truncates audio, or how prosody is generated.

## 25. Core Architecture Diagram

```
               JULIA CORE
 ┌───────────────────────────────────┐
 │ Conversation / Runtime / Context  │
 │ Identity / Memory / Continuity    │
 │ Model / Capability                │
 └───────────────┬───────────────────┘
                 │
            Core Events
                 │
          ┌──────▼──────┐
          │   Gateway   │
          │  transport  │
          └──────▲──────┘
                 │
          Client Commands
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
 Electron       Web        Mobile
 projection   projection  projection

     caches are disposable
     none are authority
```

## 26. Forbidden Claims

```
❌ Client history = canonical history
❌ Client selects model context
❌ Client cache owns recovery
❌ Gateway assembles prompts
❌ Gateway retrieves Memory for model
❌ Electron owns Persona / Continuity state
❌ Optimistic UI = canonical completed
❌ Interrupted canonical messages may be filtered away
❌ Streaming delta = canonical message
❌ Disconnect automatically rewrites Conversation
❌ Reconnect uploads local history as truth
❌ Voice uses separate Conversation authority
❌ Client persistence store directly becomes Core authority
```

## 27. Acceptance Gates

- [x] Gateway = transport boundary (§1)
- [x] Client = interaction/presentation body (§1)
- [x] Command Plane frozen (§2)
- [x] Event Plane frozen (§3)
- [x] ClientCommand abstraction (§2)
- [x] CoreEvent abstraction (§3)
- [x] Canonical identifier semantics (§4)
- [x] Optimistic state ≠ canonical completion (§5)
- [x] Client cache = disposable (§6)
- [x] Reconnect canonical reconciliation (§7)
- [x] Client cannot submit cognitive history (§8)
- [x] Gateway cannot assemble Context (§9)
- [x] Stream delta ≠ ConversationMessage (§14)
- [x] Event ordering/sequence (§10)
- [x] Duplicate/retry semantics (§11)
- [x] Disconnect ≠ automatic turn cancel (§12)
- [x] Canonical interrupted must remain visible (§13)
- [x] Text/voice/web same logical protocol (§15)
- [x] Presence state ≠ cognition (§16)
- [x] Authentication ≠ relationship identity (§17)
- [x] Multi-client projection semantics (§18)
- [x] Canonical GET/reconcile = recovery authority (§7)
- [x] Electron cannot directly access canonical stores (§21)
- [x] C-02/C-03/C-01 boundaries referenced (§24)
- [x] Electron GAP-1 dispositioned (§23)
- [x] Electron GAP-2 dispositioned (§23)
- [x] Production changes = 0

## 28. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §17, §25
Depends: C-00, C-01, C-02, C-03
Input:   P0-A, Electron GAP-1, GAP-2
Output:  Binding on C-11, Electron implementation

C-10 FREEZE → C-11 Voice / Media GO
```

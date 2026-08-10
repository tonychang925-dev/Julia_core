# VOICE-C1B-L — Core Live-Turn Convergence Design

**Status:** DRAFT  
**Date:** 2026-08-10  
**Supersedes:** C1B-R workspace-reconcile model (retains boundary flush as fallback, not as primary path)  
**Parent Architecture:** JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §5-8, §11, §12, §19  

---

## 0. Problem Statement

C1B-R established the correct authority split:

```
VoiceWorkspace/S2S = live session working set
Core               = durable authority at boundary
```

But in practice, rapid Voice↔Text switching exposes a timing gap: VoiceWorkspace holds completed semantic turns (D/E/F) that have not yet been canonicalized in Core (which only has A/B/C). When the user switches modes, the new session must bootstrap from Core — and the in-flight turns are lost.

The gap is systemic, not a bug:

| Turn State | Where It Lives | Visible to Next Session? |
|---|---|---|
| Audio capture / ASR partial | S2S / frontend | No (correct) |
| ASR final, pre-cognition | VoiceWorkspace | No (gap) |
| ASR final, cognition complete | VoiceWorkspace | No (gap) |
| Flushed to Core | Core canonical | Yes |

Every turn spends time in the middle two rows. Rapid mode switching hits this window.

C1B-V solved this by writing every turn to Core immediately — but that was too heavy and reintroduced the "Core-is-live-history-authority" anti-pattern.

C1B-L resolves this by giving Core a lightweight *in-flight* state layer that does not require full canonicalization.

---

## 1. Three-Layer Architecture

```
┌─────────────────────────────────────────────┐
│ LAYER 1: UI Projection                      │
│ partial STT / streaming text / waveform      │
│ → disposable, never authority                │
│ Owner: Voice frontend / Electron             │
└─────────────────────────────────────────────┘
                    │
                    ▼ ASR FINAL
┌─────────────────────────────────────────────┐
│ LAYER 2: Core LiveTurnJournal               │
│ accepted / in-progress / not-yet-completed   │
│ → authoritative runtime state                │
│ → short-lived (seconds, not minutes)         │
│ Owner: Core ConversationRuntime              │
└─────────────────────────────────────────────┘
                    │
                    ▼ turn completes (success / interrupted / failed)
┌─────────────────────────────────────────────┐
│ LAYER 3: Core ConversationMessage            │
│ completed / interrupted canonical transcript │
│ → durable truth                              │
│ Owner: Core Conversation authority           │
└─────────────────────────────────────────────┘
```

Layer 2 is new. Layers 1 and 3 already exist.

---

## 2. Core LiveTurnJournal — Definition

### 2.1 What it IS

A lightweight, in-memory (with optional persistence for crash recovery) register of turns that:

- Have been **accepted** by Core (user content confirmed)
- Are **currently** being processed (cognition in flight) or awaiting processing
- Have **not yet** been fully canonicalized into ConversationMessage

### 2.2 What it IS NOT

- NOT a conversation history buffer
- NOT a replacement for ConversationMessage
- NOT a shadow conversation
- NOT a client-owned workspace

### 2.3 Capacity Invariant

```
C1B-L-CAP1: Core LiveTurnJournal MUST NOT hold more than
            2 turns per conversation at any time.

Rationale: one user turn in-flight + one assistant response
in-flight = 2 maximum. More than 2 means canonicalization
is falling behind and needs immediate investigation.
```

This prevents the journal from becoming a shadow conversation (the "T6-T17 in Live, T1-T5 in canonical" failure mode).

---

## 3. Turn Lifecycle

```
                    ASR FINAL
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ TurnIngress.accept(                          │
│   conversation_id, turn_id, modality, content │
│ )                                            │
│                                              │
│ → idempotent (same turn_id → ACK, no dup)    │
│ → validates conversation ownership           │
│ → registers in LiveTurnJournal               │
│ → returns ACK immediately                    │
│                                              │
│ BLOCKING: conversation lookup, idempotency   │
│ NON-BLOCKING: Memory, Compact, Continuity,   │
│               TTS, indexing, analytics        │
└──────────────────┬───────────────────────────┘
                   │
                   ▼ ACCEPTED
┌──────────────────────────────────────────────┐
│ LiveTurnJournal entry:                       │
│   turn_id: "voice:vws_xxx:0003"              │
│   conversation_id: "conv_A"                  │
│   role: user                                 │
│   status: accepted                           │
│   content: "我认为 AI 以后会形成长期关系"       │
│   accepted_at: 2026-08-10T15:30:00Z          │
│   revision: 1                                │
└──────────────────┬───────────────────────────┘
                   │
                   ▼ COGNITION BEGINS
┌──────────────────────────────────────────────┐
│ ConversationRuntime begins cognition          │
│ LiveTurnJournal entry updated:               │
│   status: processing                         │
│                                              │
│ Context OS assembles:                        │
│   ConversationFrame (canonical)              │
│   + CurrentTurn overlay (from LiveTurn)      │
│   → CognitiveContextPackage → LLM            │
└──────────────────┬───────────────────────────┘
                   │
                   ▼ LLM STREAMING
┌──────────────────────────────────────────────┐
│ Assistant content streams back               │
│ LiveTurnJournal entry updated:               │
│   assistant_content: "我也觉得..." (streaming) │
│   assistant_status: generating               │
└──────────────────┬───────────────────────────┘
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
     COMPLETED          INTERRUPTED / FAILED
          │                 │
          ▼                 ▼
┌──────────────────────────────────────────────┐
│ ConversationRuntime.commit_turn()            │
│ → creates ConversationMessage (canonical)     │
│ → removes from LiveTurnJournal               │
│ → fires post-turn hooks (async, non-blocking) │
│                                              │
│ POST-TURN (background, non-blocking):         │
│   Memory candidate formation                  │
│   StructuredCompact update                    │
│   Continuity observation                      │
│   Indexing                                    │
└──────────────────────────────────────────────┘
```

---

## 4. TurnIngress API

### 4.1 Accept Turn (Fast Path)

```
POST /internal/v1/conversations/{conversation_id}/live-turns

Request:
{
  "turn_id": "voice:vws_xxx:0003",
  "modality": "voice",
  "content": "我认为 AI 以后会形成长期关系",
  "source": "voice-s2s",
  "source_session_id": "vws_xxx"
}

Response (200, immediately):
{
  "accepted": true,
  "conversation_id": "conv_A",
  "turn_id": "voice:vws_xxx:0003",
  "revision": 1,
  "status": "accepted"
}

Idempotent:
  Same turn_id → 200 with same response, no duplicate turn created.
```

### 4.2 Get Live State (for mode switch attachment)

```
GET /internal/v1/conversations/{conversation_id}/live-state

Response (200):
{
  "conversation_id": "conv_A",
  "canonical_last_message_id": "msg_xxx",
  "live_turns": [
    {
      "turn_id": "voice:vws_xxx:0003",
      "role": "user",
      "status": "processing",
      "content": "我认为 AI 以后会形成长期关系",
      "assistant_content": "我也觉得这确实是一个值得思考的...",
      "assistant_status": "generating",
      "accepted_at": "2026-08-10T15:30:00Z",
      "revision": 1
    }
  ]
}
```

---

## 5. Context OS Integration

### 5.1 Context Assembly

```
Context OS builds CognitiveContextPackage:

ConversationFrame:
  ← canonical ConversationMessage[] (T1...T16)

CurrentTurnOverlay (NEW):
  ← Core LiveTurnJournal entries for this conversation

Rules:
  - LiveTurn user_content is treated as the most recent user message
  - LiveTurn assistant_content (if present) is included as in-progress
  - Overlay does NOT duplicate canonical turns
  - Overlay does NOT persist beyond the turn's lifecycle
```

### 5.2 Invariant

```
C1B-L-I4: Context OS may combine canonical Conversation
with Core-owned in-flight turn state, never client-owned history.
```

---

## 6. Mode Switch Flow

### 6.1 Voice → Text (instant switch)

```
1. User clicks Text
2. pauseMicCapture() — stops audio
3. showSurface('text')
4. Electron: GET /conversations/{id}/live-state
   → receives canonical messages + any live turns
5. Render timeline: canonical messages + live turn overlay
6. If live turn exists with status=processing:
   display "Julia is responding..." with streaming content
```

No flush required. No bootstrap required. The live state is already in Core.

### 6.2 Text → Voice (instant switch)

```
1. User clicks Voice
2. Electron: GET /conversations/{id}/live-state
   → receives complete picture
3. S2S bootstrap with:
   - canonical messages (from Core)
   - live turn overlay (from Core, if any)
4. User speaks → S2S → Brain → Core TurnIngress.accept()
```

No flush required. No workspace drain. The state is Core-native.

### 6.3 Invariant

```
C1B-L-I5: Voice↔Text switching attaches to the same conversation_id;
it MUST NOT require history flush/bootstrap.
```

---

## 7. Idempotency and Retry

### 7.1 Turn Delivery

```
C1B-L-I6: Unacknowledged current-turn delivery may be retried
idempotently by turn_id, but clients MUST NOT resend prior
conversation history.
```

If Electron/S2S sends `TurnIngress.accept()` and the network drops before ACK:

1. Client retries with same `turn_id`, same `content`
2. Core detects duplicate `turn_id` → returns same ACK
3. No duplicate turn created

### 7.2 Client Responsibility

```
Client MAY retry:
  - current unacknowledged turn (same turn_id)

Client MUST NOT:
  - resend prior conversation history
  - maintain multi-turn semantic buffer
  - replay turns from local storage
```

---

## 8. What Gets Removed

With C1B-L in place, the following C1B-R artifacts become unnecessary:

| Artifact | C1B-R Role | C1B-L Disposition |
|---|---|---|
| VoiceWorkspace | Live turn tracking | Removed. Core LiveTurnJournal replaces it. |
| workspace.flush() | Boundary commit | Removed. Turns canonicalize individually on completion. |
| workspace.bootstrap() | Seed S2S from Core | Replaced by GET /live-state (lighter, Core-native). |
| workspace.committed | Mark turns done | Replaced by turn completion in Core. |
| voiceWorkspaceSessionId | Session tracking | Retained for idempotency, not for history. |
| selectBootstrapWindow() | Trim canonical for S2S | Moved to Core-side Context OS budget. |
| chat.hydrateCanonical() | Voice iframe history | Already removed (Electron timeline is UI). |

What IS retained from C1B-R:

| Artifact | Reason |
|---|---|
| External turn commit endpoint | For batch import of legacy/historical voice sessions |
| conversation_id as provenance | Identity and traceability |
| voiceSessionId | Idempotency scope for current turn delivery |
| Electron live projection | UI-only disposable rendering |

---

## 9. New Invariants

```
C1B-L-I1  Frontend/S2S/Electron MUST NOT own multi-turn cognitive history.
C1B-L-I2  A final semantic user input MUST enter Core LiveTurn state
          before Julia cognition begins.
C1B-L-I3  Completed turns MUST canonicalize immediately;
          Core LiveTurn MUST NOT accumulate completed history.
C1B-L-I4  Context OS may combine canonical Conversation with
          Core-owned in-flight turn state, never client-owned history.
C1B-L-I5  Voice↔Text switching attaches to the same conversation_id;
          it MUST NOT require history flush/bootstrap.
C1B-L-I6  Unacknowledged current-turn delivery may be retried idempotently
          by turn_id, but clients MUST NOT resend prior conversation history.
```

---

## 10. Component Responsibilities

```
┌─────────────────────────────────────────────────────────┐
│ COMPONENT          │ RESPONSIBILITY                     │
├────────────────────┼────────────────────────────────────┤
│ Voice frontend     │ Audio I/O, ephemeral bubbles,      │
│                    │ ASR display, NO multi-turn history │
├────────────────────┼────────────────────────────────────┤
│ Electron shell     │ Mode switching, UI projection,     │
│                    │ current-turn delivery, NO history  │
├────────────────────┼────────────────────────────────────┤
│ S2S                │ Audio pipeline, VAD, STT, TTS,     │
│                    │ transport. Chat is LLM context     │
│                    │ feeder, not authority.             │
├────────────────────┼────────────────────────────────────┤
│ Brain              │ Thin adapter: routes voice turns   │
│                    │ to Core TurnIngress, streams back   │
│                    │ assistant output.                  │
├────────────────────┼────────────────────────────────────┤
│ Core LiveTurnJournal│ Fast ingress, in-flight state,     │
│                    │ max 2 turns per conversation        │
├────────────────────┼────────────────────────────────────┤
│ Core Conversation  │ Canonical transcript, durable truth │
├────────────────────┼────────────────────────────────────┤
│ Context OS         │ Assembles canonical + live overlay │
│                    │ into CognitiveContextPackage        │
├────────────────────┼────────────────────────────────────┤
│ LLM                │ Cognition: understands, reasons,   │
│                    │ generates. Sees only what Context   │
│                    │ OS provides.                       │
└────────────────────┴────────────────────────────────────┘
```

---

## 11. Migration Path from C1B-R

```
Phase 1: Core LiveTurnJournal implementation
  - TurnIngress.accept() endpoint
  - LiveTurnJournal data structure (in-memory, per-conversation)
  - GET /live-state endpoint
  - Fast path (accept in <10ms, no DB write)

Phase 2: Context OS overlay
  - CurrentTurnOverlay in CognitiveContextPackage
  - ConversationFrame + overlay combination logic
  - Budget: live turns do not count against canonical token budget

Phase 3: Brain thin-adapter update
  - Replace conversation_id → ignore external_history path
  - Route voice turns through TurnIngress.accept()
  - Stream assistant output back through LiveTurn update

Phase 4: Client simplification
  - Remove VoiceWorkspace
  - Remove flush/bootstrap cycle
  - Replace with simple GET /live-state on attach
  - Retain voiceSessionId for turn idempotency

Phase 5: Removal
  - Remove workspace.flush, workspace.bootstrap, workspace.committed
  - Remove selectBootstrapWindow from voice frontend
  - Remove voiceBoundaryPromise / VoiceTransitionFence (no longer needed)
```

---

## 12. Acceptance Tests

### AT-L01 — Fast Ingress
```
Given: ASR final transcript for conversation A
When: TurnIngress.accept() is called
Then: ACK returned in < 50ms
And: LiveTurnJournal contains the turn
And: No database write occurred
```

### AT-L02 — Idempotent Retry
```
Given: turn_id T17 already accepted
When: TurnIngress.accept() called again with same turn_id + content
Then: Returns 200 with same ACK
And: No duplicate turn created
```

### AT-L03 — Mode Switch Sees Live Turn
```
Given: Voice turn T17 accepted, cognition in progress
When: Switch to Text mode, GET /live-state
Then: Response includes T17 with status=processing
And: Electron renders T17 user content + streaming assistant content
```

### AT-L04 — Rapid Switch No Data Loss
```
Given: conversation A with canonical T1-T16
When: Voice → Text → Voice in < 500ms (rapid cycle × 10)
Then: All accepted turns appear in canonical
And: No duplicate turns
And: No lost turns
And: Context OS always includes relevant turns
```

### AT-L05 — LiveTurn Capacity
```
Given: conversation A with 1 live turn
When: A second turn enters before first completes
Then: LiveTurnJournal holds exactly 2 turns
And: System does not exceed capacity
And: Completed turns are immediately canonicalized
```

### AT-L06 — LLM Sees Live Context
```
Given: Canonical T1-T5, LiveTurn T6 (user), cognition starting
When: Context OS assembles CognitiveContextPackage
Then: Package includes T1-T5 canonical + T6 as current turn
And: LLM can reference content from T6
And: T6 does NOT appear twice (once canonical, once live)
```

---

## 13. Relationship to Frozen Contracts

| Contract | Impact |
|---|---|
| C-00 Cognitive Boundary | Unchanged. Runtime still does not replace cognition. |
| C-02 Conversation Authority | Extended: LiveTurnJournal is Core-owned pre-canonical state. |
| C-03 Context OS | Extended: CurrentTurnOverlay is a new frame source. |
| C-06 Continuity OS | Clarified: LiveTurnJournal is NOT continuity state. |
| C-07 ModelProvider | Unchanged. |
| C-11 Voice/Media | Clarified: Voice frontend is body only. |

No frozen contract is violated. C-02 and C-03 gain new sub-concepts that need explicit adoption.

---

## 14. Open Questions

1. **LiveTurnJournal persistence**: Should it survive Core restart? Leaning NO — it's runtime-only. Crash recovery means the client re-sends the unacknowledged turn (idempotent).

2. **LiveTurn TTL**: How long before an uncompleted live turn is considered stale? Suggest 120s — if no assistant response within 2 minutes, mark as `stale` and allow override.

3. **Concurrent turns**: Can two voice sessions (e.g. phone + desktop) have live turns on the same conversation simultaneously? Suggest NO — first-wins, second gets `409 conflict` until first completes.

4. **S2S Chat seeding**: Does C1B-L eliminate the need for `seedConversationHistory`? Partially — S2S still needs initial context on first connect, but doesn't need re-seeding on mode switch (Core live state covers it).

---

*End of VOICE-C1B-L Design.*

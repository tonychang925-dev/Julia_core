# VOICE-C1B-L — Core Runtime-Turn Convergence Design

**Status:** 🔒 SUPERSEDED AS ARCHITECTURE — RETAINED AS VOICE CONVERGENCE HISTORY  
**Superseded by:** CM-CORE-v1 Conversation Core Runtime Contract (FROZEN 2026-08-10)  
**Date:** 2026-08-10 (original), superseded 2026-08-10  
**Reason:** C1B-L's core problem (persist gap between VoiceWorkspace and Core) is solved more cleanly by CM-Core's durable-user-before-ACK. VoiceWorkspace removal and S2S de-authorization are now CM-Core conflict dispositions 001/002. LiveTurnJournal is no longer needed — CM-Core + existing C-01 RuntimeTurn cover the execution state without introducing a fifth conversation-like object. Future Voice convergence should use ConversationRuntime v2 directly, not implement a separate TurnIngress + LiveTurnJournal + /live-state mechanism.  
**Parent Architecture:** JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §5-8, §11, §12, §19  

---

## 0. Problem Statement

C1B-R established the correct authority split:

```
VoiceWorkspace/S2S = live session working set
Core               = durable authority at boundary
```

But in practice, rapid Voice↔Text switching exposes a timing gap: VoiceWorkspace holds completed semantic turns (D/E/F) that have not yet been canonicalized in Core (which only has A/B/C). When the user switches modes, the new session must bootstrap from Core — and the in-flight turns are lost.

The gap is systemic:

| Turn State | Where It Lives | Visible to Next Mode? |
|---|---|---|
| Audio capture / ASR partial | S2S / frontend | No (correct) |
| ASR final, pre-cognition | VoiceWorkspace | No (gap) |
| ASR final, cognition complete | VoiceWorkspace | No (gap) |
| Flushed to Core | Core canonical | Yes |

C1B-V solved this by writing every turn through Core immediately — but bound turn persistence to full cognition completion, which was too heavy.

C1B-L resolves this by introducing a fast **durable user acceptance** path that decouples canonical user message creation from assistant turn completion.

---

## 1. Core Principle

```
Final user semantic fact
→ immediately Core canonical user message
→ ACK = durable

RuntimeTurn
→ "what is happening right now"
→ NEVER "what was said earlier"
```

The RuntimeTurn is an execution journal, not a pre-canonical transcript store. It carries the assistant's in-flight generation state, not the user's already-durable semantic content.

---

## 2. Three-Layer Architecture

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
│ LAYER 2: Core RuntimeTurn                   │
│ execution journal: assistant generation      │
│ state, emitted-content boundary,             │
│ interruption tracking                        │
│ → authoritative runtime state                │
│ → short-lived (per-turn lifecycle)           │
│ Owner: Core ConversationRuntime              │
└─────────────────────────────────────────────┘

User message: already canonicalized at Layer 3
at the moment of ASR final acceptance.

                    │
                    ▼ assistant lifecycle settles
┌─────────────────────────────────────────────┐
│ LAYER 3: Core ConversationMessage            │
│ user content (durable on accept)             │
│ assistant content (durable on settle)        │
│ → canonical transcript truth                 │
│ Owner: Core Conversation authority           │
└─────────────────────────────────────────────┘
```

---

## 3. Turn Lifecycle — R1 Corrected

### 3.1 Stage 1: User Acceptance (Fast, Durable)

```
                    ASR FINAL
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ TurnIngress.accept(                          │
│   conversation_id, turn_id, modality, content │
│ )                                            │
│                                              │
│ Step 1: idempotency check (same turn_id →    │
│         ACK, no duplicate turn created)       │
│                                              │
│ Step 2: canonical USER ConversationMessage   │
│         appended (lightweight, durable)       │
│         status = accepted                     │
│                                              │
│ Step 3: create RuntimeTurn execution journal  │
│         status = processing                   │
│                                              │
│ Step 4: return ACK                           │
│                                              │
│ BLOCKING:  conversation lookup, idempotency, │
│            canonical user append              │
│ NON-BLOCKING: Memory formation, Compact,     │
│               Continuity, TTS, indexing       │
│                                              │
│ ACK guarantee: user semantic fact is now     │
│ durable in ConversationMessage. No crash-     │
│ after-ACK data-loss window.                   │
└──────────────────┬───────────────────────────┘
                   │
                   ▼ ACCEPTED
┌──────────────────────────────────────────────┐
│ ConversationMessage:                         │
│   message_id: "msg_T17_user"                 │
│   conversation_id: "conv_A"                  │
│   turn_id: "voice:vws_xxx:0003"             │
│   role: user                                 │
│   status: accepted                           │
│   content: "我认为 AI 以后会形成长期关系"       │
│   created_at: 2026-08-10T15:30:00Z           │
│                                              │
│ RuntimeTurn:                                  │
│   turn_id: "voice:vws_xxx:0003"              │
│   status: processing                          │
│   modality: voice                             │
│   assistant_generated: null (not yet)         │
│   assistant_emitted_boundary: null            │
│   interrupted: false                          │
└──────────────────────────────────────────────┘
```

### 3.2 Stage 2: Cognition

```
RuntimeTurn.status = processing

Context OS:
  ConversationFrame ← ConversationMessage[] (canonical, includes T17 user)
  SituationFrame    ← RuntimeTurn state (processing, modality=voice)
  (... other frames)

  → CognitiveContextPackage → LLM
```

### 3.3 Stage 3: Assistant Lifecycle

```
LLM STREAMING
   │
   ▼ GENERATING
RuntimeTurn:
  assistant_generated = full accumulated text (streaming)
  assistant_status = generating

   │
   ▼ RENDERING (Voice: TTS synthesis + playback)
RuntimeTurn:
  assistant_rendering = true
  assistant_emitted_boundary = last emitted character/segment

   │
   ├─ fully emitted → SETTLED
   │    RuntimeTurn.assistant_status = completed
   │    → canonical ASSISTANT ConversationMessage (status=completed)
   │
   ├─ interrupted (barge-in) → SETTLED
   │    RuntimeTurn.assistant_status = interrupted
   │    → canonical ASSISTANT ConversationMessage
   │      (content = emitted_boundary, status = interrupted)
   │
   └─ failed → SETTLED
        RuntimeTurn.assistant_status = failed
        → canonical ASSISTANT ConversationMessage
          (content = generated or emitted, status = failed)

RuntimeTurn removed from journal.
```

**C-11 compliance**: Cognitive completion ≠ TTS synthesis completion ≠ playback completion. Canonical assistant content obeys emitted-content boundary. A 1000-character LLM generation where only 300 characters were spoken before barge-in results in a canonical assistant message of ~300 characters with status=interrupted, not 1000 characters with status=completed.

---

## 4. TurnIngress API

### 4.1 Accept Turn (Fast, Durable)

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

Response (200):
{
  "accepted": true,
  "conversation_id": "conv_A",
  "turn_id": "voice:vws_xxx:0003",
  "user_message_id": "msg_T17_user",
  "status": "accepted"
}

Idempotent:
  Same turn_id → 200 with same response, no duplicate.
  User ConversationMessage is already durable at ACK time.
```

Performance SLO: `< 50ms` p95. This requires a lightweight canonical user append — no Memory, Compact, Continuity, or indexing on the hot path.

### 4.2 Get Conversation View (Atomic Snapshot)

```
GET /internal/v1/conversations/{conversation_id}/view

Response (200):
{
  "conversation_id": "conv_A",
  "conversation_revision": 42,
  "canonical_messages": [
    { "message_id": "msg_001", "role": "user", "content": "...", "status": "completed" },
    { "message_id": "msg_002", "role": "assistant", "content": "...", "status": "completed" },
    ...
  ],
  "runtime_turn": {
    "turn_id": "voice:vws_xxx:0003",
    "status": "processing",
    "modality": "voice",
    "assistant_generated": "我也觉得这确实是一个值得思考的...",
    "assistant_status": "generating",
    "interrupted": false
  },
  "event_cursor": "evt_xxx"
}
```

Single atomic response. Electron does NOT make separate GET /messages + GET /live-state calls. No snapshot race window.

---

## 5. Context OS Integration

### 5.1 Frame Assignment

```
Context OS builds CognitiveContextPackage:

ConversationFrame
  ← ConversationMessage[] ONLY (canonical, includes T17 user)

SituationFrame
  ← RuntimeTurn execution state
    - turn T17 is processing
    - modality = voice
    - assistant currently generating
    - interruption state

RuntimeTurn does NOT carry additional conversation history.
It carries execution/presence state only.
```

### 5.2 Frozen Contract Impact

```
C-02 Conversation Authority: UNCHANGED
  ConversationMessage remains sole canonical transcript.
  User message durable on accept (no change to schema).

C-03 Context OS: UNCHANGED
  ConversationFrame source unchanged.
  SituationFrame carries RuntimeTurn state (already within scope).

C-11 Voice/Media: UNCHANGED
  Emitted-content boundary already required.
  RuntimeTurn implements it for assistant lifecycle.
```

---

## 6. Mode Switch Flow — R1 Corrected

### 6.1 Voice → Text

```
1. User clicks Text
2. pauseMicCapture() — stops audio
3. showSurface('text')
4. Electron: GET /conversations/{id}/view
   → canonical messages (includes just-accepted T17 user)
   → runtime_turn (assistant may still be generating)
5. Render timeline from canonical messages
6. If runtime_turn exists with assistant_generated:
   display streaming assistant content
```

### 6.2 Text → Voice

```
1. User clicks Voice
2. Electron: GET /conversations/{id}/view
   → renders complete state in text timeline
3. S2S: open media session
   → audio → VAD → STT → ASR FINAL
4. S2S sends to Brain:
   { conversation_id, turn_id, transcript }
   NO conversation history
   NO seedConversationHistory
   NO bootstrap messages
5. Brain: TurnIngress.accept() → canonical user → RuntimeTurn → Context OS → LLM
6. Brain external_history is REJECTED / IGNORED (C-03 compliance)
```

S2S is a media transport. It does not know or carry conversation history. Context is assembled by Core Context OS from the canonical conversation.

---

## 7. Capacity Invariant

```
C1B-L-CAP1: At most 1 active logical RuntimeTurn per conversation.

Barge-in: T17 interrupted → finalized → T18 accepted.
Not: T17 and T18 concurrently active.

If a future feature requires turn overlap, define it as a separate
transition-overlap contract, not as a relaxed capacity bound.
```

---

## 8. Idempotency and Retry

```
C1B-L-I6: Unacknowledged current-turn delivery may be retried
idempotently by turn_id.

Client MAY retry:
  - current unacknowledged turn (same turn_id, same content)

Client MUST NOT:
  - resend prior conversation history
  - maintain multi-turn semantic buffer
  - seed conversation history into S2S
  - replay turns from local storage
  - act as a Context source for the LLM

ACK durability guarantee: once ACK returns, the user semantic
fact is in canonical ConversationMessage. Crash recovery does
not require client retry for ACK'd turns.
```

---

## 9. What Gets Removed

| Artifact | C1B-R Role | C1B-L Disposition |
|---|---|---|
| VoiceWorkspace | Live turn tracking | Removed |
| workspace.flush() | Boundary commit | Removed (turns canonicalize individually) |
| workspace.bootstrap() | Seed S2S from Core | Removed (S2S does not carry history) |
| workspace.committed | Mark turns done | Removed |
| seedConversationHistory() | S2S Chat seeding | Removed |
| selectBootstrapWindow() | Trim canonical for S2S | Removed |
| chat.hydrateCanonical() | Voice iframe history | Already removed (Electron timeline is UI) |
| voiceBoundaryPromise | Mode-switch fence | Removed (no boundary to wait for) |

What IS retained:

| Artifact | Reason |
|---|---|
| External turn commit endpoint | Legacy/historical voice session batch import |
| conversation_id | Identity and traceability |
| voiceSessionId / turn_id | Idempotency scope |
| Electron live projection | UI-only disposable rendering |
| Brain external_history rejection | C-03 compliance |

---

## 10. Revised Invariants

```
C1B-L-I1  Frontend/S2S/Electron MUST NOT own multi-turn cognitive history.
C1B-L-I2  A final semantic user input MUST be durably accepted as a
          canonical ConversationMessage before ACK is returned.
C1B-L-I3  RuntimeTurn MUST NOT accumulate completed turn content.
          Only 1 active logical turn per conversation.
C1B-L-I4  Context OS assembles model-visible information from
          ConversationFrame (canonical only) and SituationFrame
          (RuntimeTurn execution state). No client-owned history.
C1B-L-I5  Voice↔Text switching attaches to the same conversation_id
          via GET /view; it MUST NOT require flush, bootstrap,
          or client-side history replay.
C1B-L-I6  Unacknowledged current-turn delivery may be retried
          idempotently by turn_id. Clients MUST NOT resend prior
          conversation history.
C1B-L-I7  S2S is a media transport; it MUST NOT carry or seed
          conversation history. Brain MUST reject/ignore
          external_history when conversation_id is present.
C1B-L-I8  Voice assistant canonicalization obeys C-11 emitted-content
          boundary: only content that was generated AND rendered
          (to the point of emission) becomes canonical assistant text.
```

---

## 11. Component Responsibilities

```
┌────────────────────┬───────────────────────────────────────┐
│ COMPONENT          │ RESPONSIBILITY                        │
├────────────────────┼───────────────────────────────────────┤
│ Voice frontend     │ Audio I/O, ephemeral bubbles.         │
│                    │ NO multi-turn history.                │
├────────────────────┼───────────────────────────────────────┤
│ Electron shell     │ Mode switching, UI projection,        │
│                    │ current-turn delivery. NO history.    │
├────────────────────┼───────────────────────────────────────┤
│ S2S                │ Audio pipeline, VAD, STT, TTS.        │
│                    │ Media transport only.                 │
│                    │ MUST NOT carry conversation history.   │
├────────────────────┼───────────────────────────────────────┤
│ Brain              │ Thin adapter: TurnIngress.accept()    │
│                    │ for voice turns. Rejects external      │
│                    │ history when conversation_id present.  │
├────────────────────┼───────────────────────────────────────┤
│ Core TurnIngress   │ Fast durable user acceptance.         │
│                    │ Idempotency. Creates RuntimeTurn.      │
├────────────────────┼───────────────────────────────────────┤
│ Core RuntimeTurn   │ Execution journal: assistant state,    │
│                    │ emitted boundary, interruption.        │
│                    │ Max 1 active per conversation.         │
├────────────────────┼───────────────────────────────────────┤
│ Core Conversation  │ Canonical transcript (user durable on  │
│                    │ accept, assistant durable on settle).  │
├────────────────────┼───────────────────────────────────────┤
│ Context OS         │ ConversationFrame ← canonical only.   │
│                    │ SituationFrame ← RuntimeTurn state.    │
├────────────────────┼───────────────────────────────────────┤
│ LLM                │ Cognition. Sees only what Context OS   │
│                    │ provides.                              │
└────────────────────┴───────────────────────────────────────┘
```

---

## 12. Migration Path

```
Phase 1: Core TurnIngress + RuntimeTurn
  - TurnIngress.accept() endpoint (durable user append, <50ms SLO)
  - RuntimeTurn data structure (in-memory, per-conversation)
  - GET /conversations/{id}/view (atomic snapshot)
  - Assistant lifecycle state machine (generating→rendering→settled)
  - Emitted-content boundary tracking for voice modality

Phase 2: Context OS integration
  - RuntimeTurn → SituationFrame
  - Remove any CurrentTurnOverlay-as-conversation-history concepts
  - ConversationFrame continues from canonical only

Phase 3: Brain thin-adapter update
  - Route voice turns through TurnIngress.accept()
  - Enforce external_history rejection (already present, now confirmed)
  - Stream assistant output with emitted-content boundary tracking

Phase 4: Client simplification
  - Remove VoiceWorkspace entirely
  - Remove flush, bootstrap, committed message types
  - Remove seedConversationHistory from S2S client
  - Replace mode-switch logic with GET /view
  - Remove VoiceTransitionFence (no boundary to wait for)

Phase 5: Cleanup
  - Remove workspace.flush, workspace.bootstrap, workspace.committed handlers
  - Remove selectBootstrapWindow
  - Remove chat.hydrateCanonical (already no-op in electronHosted)
  - Remove voiceBoundaryPromise
```

---

## 13. Acceptance Tests

### AT-L01 — Durable User Acceptance
```
Given: ASR final transcript for conversation A
When: TurnIngress.accept() is called
Then: User ConversationMessage is durable (survives Core restart)
And: ACK returned in < 50ms p95
And: Memory/Compact/Continuity/indexing do NOT block ACK
```

### AT-L02 — Idempotent Retry
```
Given: turn_id T17 already accepted
When: TurnIngress.accept() called again with same turn_id + content
Then: Returns 200 with same ACK
And: No duplicate ConversationMessage
```

### AT-L03 — Mode Switch Sees Live State
```
Given: Voice turn T17 user accepted, assistant generating
When: Switch to Text mode, GET /view
Then: Response includes T17 user in canonical_messages
And: runtime_turn shows assistant_generated content
And: Electron renders both correctly
```

### AT-L04 — Rapid Switch No Data Loss
```
Given: conversation A
When: Voice → Text → Voice in < 500ms (rapid cycle × 10)
Then: All accepted turns appear in canonical
And: No duplicate turns
And: No lost turns
```

### AT-L05 — RuntimeTurn Capacity
```
Given: conversation A, RuntimeTurn T17 active
When: New voice input arrives (barge-in)
Then: T17 finalized (interrupted) → T18 accepted
And: At no point are two RuntimeTurns concurrently active
```

### AT-L06 — LLM Sees Canonical Context
```
Given: Canonical T1-T16 + just-accepted T17 user
When: Context OS assembles CognitiveContextPackage
Then: ConversationFrame = T1-T17 (all canonical)
And: SituationFrame = T17 processing state
And: No duplicate or client-owned history
```

### AT-L07 — S2S History Rejection
```
Given: S2S sends external_history with conversation_id
When: Brain processes voice turn
Then: external_history is rejected/ignored
And: Context comes from Core Context OS only
```

### AT-L08 — Voice Emitted-Content Boundary
```
Given: LLM generated 1000 characters, TTS played 300 before barge-in
When: Assistant turn settles (interrupted)
Then: Canonical assistant content = ~300 emitted characters
And: Status = interrupted
And: Not 1000 characters with status = completed
```

---

## 14. Review Gate

```
C1B-L R1 ARCHITECTURE REVIEW
════════════════════════════════════════════

Problem model                       ✅ PASS
Core ownership direction            ✅ PASS
Client-history removal              ✅ PASS
Rapid mode-switch concept           ✅ PASS

P0 durable ACK semantics            ✅ CORRECTED (R1)
P0 final-user canonical boundary    ✅ CORRECTED (R1)
P0 S2S history/context bypass       ✅ CORRECTED (R1)
P0 Voice emitted-content lifecycle  ✅ CORRECTED (R1)

P1 atomic attach snapshot           ✅ CORRECTED (R1)
P1 RuntimeTurn capacity semantics   ✅ CORRECTED (R1)
P1 contract "extension" claim       ✅ CORRECTED (R1)

Phase 1                             🟢 READY (after Tony approval)
```

---

*End of VOICE-C1B-L R1 Design.*

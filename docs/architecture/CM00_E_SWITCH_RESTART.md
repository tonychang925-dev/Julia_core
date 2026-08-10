# CM00-E — Switch / Restart / Concurrency Reality

**Date:** 2026-08-10
**Status:** DRAFT
**Code changes:** 0

---

## E1: Voice → Text → Voice < 300ms

```
STEP CM00-E01: Rapid Voice→Text→Voice cycle

Before cycle:
  Core canonical: T1-T5
  VoiceWorkspace: T6-T7 (not yet flushed)

Voice → Text (click):
  1. pauseMicCapture() — async, ~200ms
  2. flushVoiceWorkspace() — sends delta, commits to Core
     → SessionRepository.append_external_turns_atomic()
     → T6-T7 now in Core canonical (conversations.json)
  3. syncCanonicalConversation() — GET from Core
  4. boundVoiceConversationId = null (clear binding fix)

Text → Voice (click, <300ms after Text click):
  1. switchToVoiceMode → voiceTransitionState !== 'IDLE'
     → IF reconciliation still in progress:
       pendingVoiceResume = true (DEFERRED)
     → IF reconciliation complete:
       bootstrap from Core

Bootstrap:  GET canonical messages → contains T1-T7
            ↓ selectBootstrapWindow(maxTurns=10)
            ↓ new S2S connection, seedConversationHistory

Last durable canonical point:    T7 (just flushed, conversations.json)
Component with newer state:      NONE (VoiceWorkspace cleared on flush)
Survives restart:                YES (Core canonical contains T1-T7)
conversation_id:                 unchanged (same activeConversationId)
turn_id correctness:             NEW voice session → new turn_ids
```

### E1 Verdict

```
Durable boundary:        flush → Core atomic append → ACK
Vulnerable window:       FROM: user clicks Voice after flush but before
                         syncCanonicalConversation completes
                         TO:   pendingVoiceResume fires bootstrap
                         During this window: Voice UI shows defer state
                         No data loss (deferred, not dropped)
```

---

## E2: Text → Voice → Text < 300ms

```
STEP CM00-E02: Rapid Text→Voice→Text cycle

Before:     Text mode, conversation has canonical T1-T10

Text → Voice:
  1. bootstrapVoiceWorkspace → syncConversationMessages → Core GET
  2. new S2S connection + seedConversationHistory(bootstrapMessages)
  3. resumeVoiceCapture → mic active
  4. User may or may not speak before clicking Text again

Voice → Text (immediate):
  1. pauseMicCapture — stops mic
  2. flushVoiceWorkspace — if no turns accumulated, delta is empty
     → returns { empty: true }, no Core write
  3. syncCanonicalConversation — Core GET (unchanged T1-T10)

Last durable canonical point:    T10 (unchanged)
Component with newer state:      NONE (no turns accumulated)
Survives restart:                YES (unchanged canonical)
conversation_id:                 unchanged
Turn correctness:                No turns lost (none created)
```

### E2 Verdict

```
Low risk. No turns created → no turns lost.
The S2S bootstrap overhead is wasted work (connect + seed + teardown
without any turns). Performance-only, not correctness.
```

---

## E3: Conversation A → B During Active Turn

```
STEP CM00-E03: Switch conversations during live voice

Conversation A: voice active, VoiceWorkspace has T17-T18
Conversation B: not active

User clicks conversation B:
  openConversation(B):
    1. If boundVoiceConversationId (A) → flushVoiceWorkspace('switch-conversation')
       → VoiceWorkspace A delta → Core A commit (T17-T18 durable)
    2. boundVoiceConversationId = null
    3. setCurrentConversation(B) → Electron local
    4. textClient.openConversation(B) → Core GET
    5. syncConversationMessages(B) → render B timeline
    6. If entering Voice B: bootstrapVoiceWorkspace from Core B

A durability:     T17-T18 written to Core A before switch
B integrity:      Bootstrap from Core B only — no A leakage
Cross-contamination: NO — separate conversation_ids + A flushed first
```

### E3 Verdict

```
Safe. A is flushed before B opens. Conversation boundary preserved.
```

---

## E4: Electron Restart During Active Turn

```
STEP CM00-E04: Electron process killed mid-turn

Before crash:
  ConversationRuntime: T16 user accepted (status=completed)
                       T16 assistant NOT yet committed
  VoiceWorkspace:  T17-T18 voice turns (NOT flushed)
  Electron cache:  julia-conversations-v1.json (projection)

After restart:
  Core canonical:    T1-T16 (survives, conversations.json persists)
  VoiceWorkspace:    LOST (in-memory, voice iframe gone)
  Electron cache:    survives (file on disk), stale projection markers
  S2S Chat:          LOST (process terminated)

On reopen:
  syncConversationMessages → Core GET → T1-T16
  VoiceWorkspace T17-T18: PERMANENTLY LOST (never made it to Core)

Lost data:           VoiceWorkspace T17-T18
T16 assistant:       If user was pending (before add_message) → LOST
                     If assistant content was generated → depends on
                     whether commit_streaming_turn() completed
```

### E4 Verdict

```
P0 data-loss window: any completed voice turns in VoiceWorkspace
but not yet flushed to Core are permanently lost on Electron restart.

Recovery depends on: last durable canonical point in conversations.json.
```

---

## E5: Core Restart After User Accept / Before Assistant Commit

```
STEP CM00-E05: Brain/Core crash mid-turn

Scenario A: User accepted, cognition not started
  SessionRepository.add_message(user, status=pending) → durable
  Conversations.json has user message with status=pending
  Core crash
  On restart: user message survives with status=pending
  get_history() filter: status == "completed" only → INVISIBLE
  CM-I05 concern: user accepted but NOT durable-as-completed

Scenario B: User accepted, assistant streaming, crash mid-stream
  User message: pending → completed transition DID NOT occur
  Assistant message: NOT yet persisted (commit_streaming_turn not called)
  On restart: only user message with status=pending survives
  Assistant content: LOST

Scenario C: commit_streaming_turn completed, Core crash
  User: completed (durable)
  Assistant: completed (durable)
  On restart: full turn survives

Durable boundary for user:     after add_message() with _save() → fsync
True semantic "accepted":     after status changed to "completed"
                               (after assistant commit, in current code)

CM-I05 gap: "Durable user acceptance precedes ACK"
  Current code: user message is durable (JSON file) BEFORE ACK in
  begin_turn_streaming → add_message → _save → returns.
  BUT status = "pending", not "completed".
  "Pending" messages are invisible to get_history() (filtered out).
  So the user message IS durable but IS NOT USABLE for context
  until the assistant commits.
```

### E5 Verdict

```
P1: User message durable but invisible until assistant commits.
    This is the core CM-I05 architectural gap.
    "Durable" exists; "usable as context" does not.
```

---

## E6: S2S Restart While Conversation Active

```
STEP CM00-E06: S2S process killed/restarted

S2S killed:
  S2S Chat: LOST (in-memory)
  VoiceWorkspace: LOST (in-memory, in voice iframe)
  Core canonical: survives (conversations.json on Mac)

On S2S restart:
  :8765 comes back up
  Electron needs to re-bootstrap voice session
  Bootstrap: Core GET → canonical messages
  VoiceWorkspace turns that were in old S2S session: LOST

Same as E4 — VoiceWorkspace unflushed turns disappear.
```

---

## E7: Same turn_id Retry

```
STEP CM00-E07: Idempotent retry

begin_turn_streaming checks (line 241-251):
  IF turn_id exists AND status == "completed":
    → return already_completed = True (idempotent)
  ELSE:
    → proceed as new turn

Gap: status == "pending" turns are NOT treated as idempotent match.
     A retry of a pending turn would create a SECOND add_message.

Evidence: conversation_runtime.py lines 241-251
```

### E7 Verdict

```
P2: Retry of pending turn creates duplicate. Idempotency only covers
    completed turns. CM-I19 needs status=pending coverage.
```

---

## E8: Two Clients Same Conversation

```
STEP CM00-E08: Concurrent conversation access

Current protection:
  begin_turn_streaming → lock.acquire(blocking=False)
  → ConversationBusyError if conversation locked

  This prevents concurrent TURNS on same conversation.
  Does NOT prevent:
  - Two Electrons reading/displaying same conversation
  - Two Electrons sending interleaved turns (one waits for lock)
  - One Electron Voice + one Electron Text on same conversation_id

Risk:     LOW — lock prevents concurrent mutation
          But two clients can see different projection states
```

---

*End CM00-E*

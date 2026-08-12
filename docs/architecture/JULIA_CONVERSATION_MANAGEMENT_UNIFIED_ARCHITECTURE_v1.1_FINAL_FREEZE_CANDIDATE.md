# JULIA Conversation Management Unified Architecture v1.1 — FINAL FREEZE CANDIDATE

**Document Type:** Unified Architecture + Freeze Contract + Development Plan  
**Status:** FINAL FREEZE CANDIDATE / PRODUCTION-TRUTH-ALIGNED / CODE HOLD / READY FOR TONY FREEZE DECISION  
**Date:** 2026-08-11  
**Scope:** Conversation lifecycle, canonical storage, Context OS ingress, Electron projection, live S2S/Voice convergence, cancellation/barge-in semantics, crash/retry, long-conversation compact, Daily Reflection/Diary  
**Parent:** `JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0` + CM-Core/R1-B accepted-user semantics + compatible C-01/C-03/C-05/C-06/C-10/C-11/C-12 contracts; C-02 v1 is superseded where it conflicts with durable accepted-user semantics  
**Supersedes as conversation architecture:** VOICE-C1B-R workspace-reconcile model and all client/S2S semantic-history authority patterns  
**Reclassifies:** VOICE-C1B-L as a Voice modality implementation under this Conversation Management architecture  
**v1.1 Production-Truth Amendment:** incorporates Phase 1–5 forensic/recovery/governance evidence through WB-JA-08; `DEPLOY-CORR-001`, `C2-CORR-001`, `WAVEA-F001 v3`; Wave A Core remediation complete; Wave B architecture aligned but code remains gated  

---

## 0. Executive Decision

Julia must have **one conversation world**.

```text
Conversation = what actually happened.
ConversationRuntime = sole conversation authority.
ConversationMessage = sole durable transcript truth.
Context OS = sole authority deciding what part of that truth Julia sees now.
Electron / Voice frontend / S2S = clients/transports/projections, never conversation authorities.
Memory OS = durable experience governance, not transcript storage semantics.
Diary = Julia-authored reflective artifact, not transcript and not automatic summary.
```

The main architectural correction is not a Voice patch. It is a complete Conversation Management convergence:

```text
Text ─────┐
Voice ────┼──> same conversation_id
Web ──────┤        ↓
Mobile ───┘  ConversationRuntime
                 ↓
          ConversationMessage[]
                 ↓
             Context OS
                 ↓
                Julia
```

A modality switch must therefore never require moving semantic history between clients.


## 0.1 v1.1 Production-Truth Amendment

v1.0 described the intended authority model correctly, but several statements about the *current production path* were still inferred from source topology rather than proven from the deployed runtime. Phase 5 forensics corrected those assumptions.

### Locked corrections

```text
DEPLOY-CORR-001
b2c7567 = attested historical/recovery Golden baseline
        ≠ current live deployed Voice frontend

Current live Voice frontend
= C1B-R / 49ef5ba-generation transitional artifact
= contains VoiceWorkspace integration
= must not be called "Golden" merely because deployed under a /golden/ path
```

```text
C2-CORR-001
Old attribution:
Voice barge-in → ConversationRuntime.cancel_streaming_turn()

Status:
SUPERSEDED as a statement about the current live Voice path.
```

```text
WAVEA-F001 v3
Current production-capable cognition routes are not yet converged:

Path A — current live S2S
S2S STT
→ chat-completions backend
→ Brain /v1/chat/completions
→ currently lacks conversation_id at the Brain request boundary
→ legacy Brain branch

Path B — Brain legacy Voice HTTP
/internal/v1/voice/turns
→ JuliaCoreAdapter
→ prepare_voice_turn()
→ direct provider / legacy session history

Path C — canonical route
/internal/v1/conversations/{conversation_id}/turns
→ ConversationRuntime
→ Context OS / JuliaSession
→ provider
→ canonical commit/cancel
```

The architectural problem is therefore **route convergence**, not "copy more history into Voice".

### Wave A result incorporated by v1.1

```text
RMD-1 native ConversationRuntime cancel lifecycle
✅ validated at L1, L2, and live native-route level

Accepted user message:
completed before cognition
→ assistant cancellation/failure
→ MUST remain completed

Golden/current-live Voice causal validation of RMD-1
⏸ deferred until Voice reaches the canonical route
```

### v1.1 target correction

The target is **not**:

```text
frontend session history
→ S2S history
→ Brain history
→ Core reconciliation
```

The target is:

```text
Electron / client
→ conversation_id
→ Voice frontend
→ S2S realtime session metadata
→ S2S chat-completions request
→ Brain canonical conversation route
→ ConversationRuntime
→ Context OS
```

Only the current user turn and transport/session identifiers cross the Voice boundary. Canonical multi-turn history remains Core-owned.

---


## 0.2 Authority Reconciliation Register — Phase 5

The following evidence classes MUST remain separate for every future architecture claim:

```text
REMOTE_GIT_EVIDENCE
LOCAL_GIT_EVIDENCE
LOCAL_WORKTREE_EVIDENCE
DEPLOYED_ARTIFACT_EVIDENCE
LIVE_RUNTIME_EVIDENCE
HUMAN_BEHAVIOR_EVIDENCE
CONVERSATION/LIBRARY_HISTORICAL_EVIDENCE
```

No class may silently substitute for another.

### AR-CM-001 — Historical acceptance records are not current production authority

`Julia_core` remote history contains earlier acceptance/closure records including:

```text
bc05c332  Voice Convergence Acceptance — CLOSED
          claimed zero S2S cognitive bypass / zero Voice persist gap

ee37a283  JULIA CONVERSATION V2 BASELINE — program closure
          claimed zero shadow authorities

b5d2c137  E2E-08~11 Final Acceptance
          claimed E2E 27/27 PASS / release gate closed
```

These commits remain valid historical evidence that those test programs were executed under their then-current assumptions. They are **not** current production-compliance authority because later Phase-5 live forensics demonstrated:

- current-live Voice does not yet bind `conversation_id` into the S2S→Brain cognitive request;
- current-live Voice therefore does not yet prove canonical `ConversationRuntime` ownership;
- deployed Voice frontend provenance diverged from the historical `b2c7567` baseline;
- prior Golden/live route attribution mixed different execution paths.

Disposition:

```text
HISTORICAL ACCEPTANCE EVIDENCE
SUPERSEDED FOR CURRENT PRODUCTION-COMPLIANCE CLAIMS
DO NOT DELETE
DO NOT USE AS A GO GATE FOR WAVE B
```

### AR-CM-002 — VOICE-C1B-R is transitional, not normative conversation architecture

The Voice repository contains the historical `ADR-VOICE-C1B-R: Voice Workspace Reconciliation` generation. Its useful implementation evidence is preserved, but its workspace/bootstrap reconciliation model is subordinate to this document and scheduled for retirement after canonical Voice→CRT convergence.

### AR-CM-003 — Remote Git, local source, deployed artifact and live process are independent identities

Every Phase-5 change must record at minimum:

```text
repo
remote default branch + commit
local branch + HEAD
approved worktree delta
live deployed path + artifact hash
live process PID/cmdline/interpreter
```

A version label such as `Golden`, `main`, `HEAD`, or a deployment directory name is never sufficient by itself.

### AR-CM-004 — Current Core candidate identity remains a composite until explicitly committed

Wave A validated:

```text
local Core base HEAD
+ approved RMD-1 worktree delta
+ approved RMD-2 test delta
```

That composite candidate must not be relabeled as any remote commit unless the exact bytes are later committed and attested.

---

# PART I — WHY THIS PROGRAM EXISTS

## 1. Problem Statement

Recent Voice failures exposed several symptoms that looked independent but share one root class:

1. Voice frontend displayed multiple turns while Julia could not see them.
2. Voice → Text → immediate Voice could lose recent topic continuity.
3. A new Voice session could bootstrap from stale Core state.
4. Electron projection logic started accumulating semantic state.
5. VoiceWorkspace became a live multi-turn cognitive history source.
6. Brain behavior changed depending on whether caller-owned `messages[]` were supplied.
7. Long-session continuity depended on session-local state rather than the canonical conversation.

These are not merely race conditions. They indicate missing end-to-end Conversation Management authority rules.

The solution is to freeze the lifecycle from **conversation creation → durable append → display → context selection → compact → reopen → archive/delete**, across all modalities.

---

## 2. Audit Principle

This program follows the same discipline as the foundation-contract freeze:

```text
Reality Audit
→ Authority Map
→ Conflict Register
→ Contract Freeze
→ Characterization Tests
→ Implementation
→ Sabotage / Acceptance
→ Final Freeze
```

Until CM contracts are frozen:

```text
Conversation architecture changes     HOLD
VoiceWorkspace continuation patches   HOLD
Electron history authority changes    HOLD
Brain external_history experiments    HOLD
Long-conversation truncation fixes     HOLD unless transport-only
```

---

# PART II — CLAUDE COMPARISON AUDIT

## 3. What Is Worth Copying from Claude

The useful Claude pattern is **not** “put everything into one memory object.” The useful pattern is separation of raw session transcripts from curated long-term artifacts.

Observed historical Julia/Claude-equivalent structure included:

```text
Claude raw session JSONL
  → full chronological conversation evidence

memory/
  → MEMORY.md / index
  → identity / role / relationship artifacts
  → claude_diary/
  → conversations/transcripts.jsonl (import/reference copy)
  → other durable memory artifacts
```

The Claude-equivalent runtime also treated these as separate capabilities:

```text
conversation history
memory runtime
read_diary
```

### 3.1 What Julia should adopt

- Human-readable, inspectable local files.
- One durable identity for each conversation.
- Append-oriented transcript persistence.
- A conversation catalog for resume/list UI.
- Independent diary/reflection artifacts.
- Ability to reconstruct after client/session/model restart.
- Raw history preserved independently from compact/summaries.

### 3.2 What Julia must NOT copy literally

- Client/runtime directly injecting raw memory files into prompts.
- Frontend choosing which history the model sees.
- “memory directory” being treated as one semantic authority.
- Full transcript replay as the normal context strategy.
- Session/provider hidden state as continuity authority.

Julia keeps Claude's **operational strengths**, but places them behind Julia Core's stronger authority contracts.

---

# PART III — UNIFIED AUTHORITY MODEL

## 4. Five Distinct Authorities

### 4.1 Conversation Authority — “What happened?”

Owner: `ConversationRuntime` / `ConversationMessage`

Stores exact chronological interaction facts:

```text
user message
assistant message
turn_id
modality
status
created_at
source/provenance
```

Conversation is immutable append history except through separately governed correction/deletion mechanisms.

### 4.2 Runtime / Live Turn — “What is happening now?”

Owner: `RuntimeTurn` / Core execution state

Contains in-flight state only:

```text
accepted
processing
generating
rendering
interrupted
failed
```

It is NOT prior conversation history.

### 4.3 Context Authority — “What may Julia see now?”

Owner: Context OS

Builds the `ConversationFrame` and other Frames from canonical authorities.

It may use:

```text
ActiveTail
StructuredCompact
retrieved prior turns
current accepted user turn
open loops
```

It must never accept caller/client history as truth.

### 4.4 Memory Authority — “What experience deserves durable meaning?”

Owner: Memory OS

Memory ≠ transcript.

Conversation says:

> Tony said X; Julia replied Y.

Memory may later preserve:

> This exchange became an important project commitment / relationship experience / narrative turning point.

### 4.5 Client Projection — “What should the user see?”

Owner: Electron / Web / Voice UI

Projection may include optimistic and streaming artifacts, but deletion of the client cache must not delete Julia history.

---

## 5. Physical Storage Location ≠ Semantic Authority

The user-preferred private storage root may be named `memory/`, but folder placement does not redefine Core contracts.

Recommended physical layout:

```text
<PRIVATE_JULIA_DATA>/memory/
├── conversations/
│   ├── index.json
│   ├── conv_<conversation_id>/
│   │   ├── meta.json
│   │   ├── transcript-000001.jsonl
│   │   ├── transcript-000002.jsonl
│   │   ├── compact/
│   │   │   ├── compact-000001.json
│   │   │   └── compact-000002.json
│   │   └── attachments/
│   └── ...
├── diary/
│   └── YYYY/MM/YYYY-MM-DD.md
├── experiences/
│   └── ...
├── identity/
│   └── ...
└── continuity/
    └── ...
```

Semantic meaning remains:

```text
memory/conversations/* = Conversation authority persistence
memory/diary/*         = reflective artifact persistence
memory/experiences/*   = Memory OS persistence
memory/identity/*      = Identity persistence
memory/continuity/*    = Continuity persistence
```

The top-level folder name is operational, not architectural.

---

# PART IV — CONVERSATION STORAGE CONTRACT

## 6. Conversation Identity

A Conversation is a durable logical dialogue identity independent of:

```text
Electron process
Voice session
WebSocket
S2S process
provider session
model choice
application restart
```

Schema:

```json
{
  "conversation_id": "conv_...",
  "title": "...",
  "created_at": "...",
  "updated_at": "...",
  "state": "active|archived|deleted",
  "last_message_id": "msg_...",
  "last_turn_id": "turn_...",
  "message_count": 0,
  "segment_count": 1,
  "schema_version": "cm-1"
}
```

### CM-STO-I1

```text
Every conversation MUST have exactly one durable conversation_id.
```

### CM-STO-I2

```text
Creating a new conversation MUST create a durable Core artifact before the client treats it as an established conversation.
```

---

## 7. One Conversation, One Logical Archive

Each conversation owns its own storage directory.

Why not one giant `conversations.json`:

- write amplification grows with total history;
- corruption affects all conversations;
- per-conversation backup/restore is difficult;
- pagination requires whole-file loading;
- long conversations force unrelated conversations into the same rewrite lifecycle;
- migration and archival become coupled.

Recommended persistence is append-oriented JSONL segments.

---

## 8. Transcript Segment Format

Example `transcript-000001.jsonl`:

```json
{"message_id":"msg_1","conversation_id":"conv_A","turn_id":"turn_1","role":"user","modality":"text","content":"...","status":"completed","created_at":"...","source":"electron-text","provenance":{}}
{"message_id":"msg_2","conversation_id":"conv_A","turn_id":"turn_1","role":"assistant","modality":"text","content":"...","status":"completed","created_at":"...","source":"julia-core","provenance":{}}
```

### CM-STO-I3

```text
Transcript persistence is append-first.
Completed historical transcript MUST NOT be silently rewritten by compact, context budgeting, memory formation, or client reconciliation.
```

### CM-STO-I4

```text
Message order is Core canonical order, not file-system timestamp order and not client arrival order.
```

---

## 9. Durable User Acceptance Before ACK

For text or FINAL ASR:

```text
Client current input
  ↓
Core validates conversation + idempotency
  ↓
append durable canonical user message
  ↓
create/update RuntimeTurn
  ↓
ACK CORE_ACCEPTED
  ↓
Context OS / cognition
```

Heavy post-turn work must not block ingress:

```text
Memory formation
Compact generation
Continuity observation
indexing
analytics
TTS
```

### CM-STO-I5

```text
An ACK that tells the client “accepted” MUST mean the user semantic input is durable enough to survive Core process death.
```

This closes the `ACK → Core crash → acknowledged message disappears` gap.

---

# PART V — TURN / RUNTIME CONTRACT

## 10. Logical Turn Lifecycle

A turn contains **two related but independent durable semantics**:

1. user acceptance lifecycle;
2. assistant generation/emission lifecycle.

Normal canonical turn:

```text
TURN_CREATED
→ USER_ACCEPTED_DURABLE
→ COGNITION_RUNNING
→ ASSISTANT_GENERATED
→ ASSISTANT_FINALIZED
→ TURN_COMPLETED
```

The accepted user fact is irreversible by assistant failure:

```text
begin_turn_streaming()
→ canonical user message status = completed

assistant success
→ commit_streaming_turn(ctx, assistant_content)

assistant failure / disconnect / barge-in
→ cancel_streaming_turn(ctx)
→ accepted user status MUST remain completed
```

RMD-1 validated this invariant on the native `ConversationRuntime` path.

Voice adds a media lifecycle without creating a second conversation lifecycle:

```text
canonical assistant stream
→ S2S TTS/rendering
→ emitted-content settlement
→ completed | interrupted
```

The exact durability semantics for partially emitted/interrupted assistant content remain a separate C-11 boundary and MUST NOT be solved by mutating the already accepted user message.

### CM-TURN-I1

```text
Voice/Text/Web share the same logical turn semantics.
```

### CM-TURN-I2

```text
Media stop / UI mode switch / socket disconnect MUST NOT redefine canonical Conversation history.
```

### CM-TURN-I3

```text
Only current in-flight state may live outside durable ConversationMessage.
Completed prior turns MUST NOT accumulate as an alternate authority in RuntimeTurn, VoiceWorkspace, Electron, S2S, or provider-local history.
```

### CM-TURN-I4 — Accepted User / Assistant Lifecycle Independence

```text
Once a user message is durably accepted as canonical completed input,
assistant cancel/fail/interrupt MUST NOT downgrade, delete, hide, or rewrite that user fact.
```

### CM-TURN-I5 — Cancellation Settlement

```text
Every canonical streaming turn MUST settle exactly once:
commit OR cancel/failure settlement, never both.
Transport cancellation is not itself canonical settlement until it reaches ConversationRuntime.
```

# PART VI — TEXT / VOICE CONVERGENCE

## 11. Mode Switching and Live Voice Binding

Correct target model:

```text
Voice surface ──┐
Text surface ───┼── attach(conversation_id)
Web surface ────┘
                         ↓
                 ConversationRuntime
                         ↓
                     Context OS
```

Mode switches do not transfer semantic history.

### 11.1 Current live Voice path — v1.1 production truth

The live S2S session is a realtime media pipeline whose LLM backend calls Brain through the OpenAI-compatible chat-completions endpoint:

```text
Mic
→ S2S VAD 800ms
→ STT/ASR
→ S2S chat-completions handler
→ Brain /v1/chat/completions
→ response text
→ S2S TTS
→ playback
```

The live Voice frontend/session can place `conversation_id` into realtime `session.update.metadata`. A live probe showed that this metadata does **not arrive at Brain as a canonical `conversation_id`** and the request remains on the legacy branch. WB-JA-08 has now attested the deployed runtime: `speech-to-speech==0.2.12` under Python 3.10, with the live `ChatCompletionsApiModelHandler` loaded from `/root/miniconda3/lib/python3.10/site-packages/speech_to_speech/LLM/chat_completions_language_model.py`. The deployed handler can access `runtime_config.session`, but its current outbound request construction contains neither `conversation_id` nor `turn_id`.

This is the primary RMD-3A convergence gap:

```text
session.metadata.conversation_id       ✅ available
        ↓
S2S handler outbound request body      ❌ not propagated
        ↓
Brain canonical CRT branch             therefore not selected
```

### 11.2 Target Voice path

```text
Electron / client
→ bind conversation_id
→ Voice frontend
→ S2S session.metadata.conversation_id
→ current ASR-final user input
→ S2S existing chat-completions backend
→ outbound request includes conversation_id
→ Brain /v1/chat/completions
→ canonical conversation_id branch
→ ConversationRuntime.begin_turn_streaming()
→ Context OS / cognition
→ commit_streaming_turn() OR cancel_streaming_turn()
→ response text
→ S2S TTS / playback
```

The S2S LLM *stage* may remain as a transport/backend stage **only if the unique cognitive authority is the canonical Brain/Core path**. No parallel frontend POST to a second cognition route is allowed.

### Voice → Text

```text
stop/pause media
show Text UI
GET canonical Conversation View from Core
render canonical + current Core runtime projection
```

### Text → Voice

```text
open Voice media
bind conversation_id
publish conversation_id as realtime session identity metadata
start capture
FINAL ASR → same canonical Brain/Core conversation lifecycle
```

No semantic `workspace.flush()` and no multi-turn client `history bootstrap` are part of the target architecture.

### CM-MOD-I1

```text
Voice↔Text switching MUST preserve conversation continuity without client-side semantic history transfer.
```

### CM-MOD-I2

```text
Julia-bound S2S MUST NOT supply multi-turn caller-owned history as cognitive authority.
```

### CM-MOD-I3

```text
S2S/provider hidden history may exist as transport implementation state, but clearing it MUST NOT erase Julia's completed conversational continuity.
```

### CM-MOD-I4 — Session Identity Propagation

```text
Every Julia-bound realtime Voice session MUST carry one Core conversation_id through to every cognitive request generated for that session.
```

### CM-MOD-I5 — Identifier-Only Client Binding

```text
Client→Voice binding may carry conversation_id, turn/session identifiers, current input, and media metadata.
It MUST NOT carry canonical multi-turn history as model-visible authority.
```

### CM-MOD-I6 — Single Cognitive Authority

```text
Voice may perform VAD/ASR/TTS/media transport and may call a remote LLM backend,
but the model-visible cognitive request for Julia MUST enter through the canonical Brain/Core + Context OS path exactly once.
```

### CM-MOD-I7 — Barge-In Causal Closure

```text
A production barge-in PASS requires one traced causal chain:
S2S/media cancel
→ active Brain stream termination/cancellation
→ canonical ConversationRuntime cancellation settlement
→ accepted user remains completed
→ canonical history retains the user
→ next cognition sees that user fact.
```

# PART VII — ATOMIC CONVERSATION VIEW

## 12. Core Conversation View API

Electron should not independently combine a canonical GET and a live-state GET without revision semantics.

Recommended Core projection API:

```http
GET /internal/v1/conversations/{conversation_id}/view?before=<cursor>&limit=50
```

Response:

```json
{
  "conversation": {"conversation_id":"conv_A","title":"..."},
  "revision": 184,
  "canonical_messages": [],
  "runtime_turn": null,
  "page": {
    "before_cursor": "...",
    "has_more": true
  }
}
```

This view is presentation data. It is not a new canonical authority.

### CM-VIEW-I1

```text
A client attach/reconcile view MUST be internally consistent under one Core conversation revision/cursor boundary.
```

---

# PART VIII — CONVERSATION CATALOG / ELECTRON

## 13. Conversation Catalog

Core owns the catalog.

Example `memory/conversations/index.json` is an implementation cache/index, not a client authority.

Electron obtains:

```http
GET /internal/v1/conversations?state=active&cursor=...
```

The list may include:

```text
conversation_id
title
created_at
updated_at
last_preview
last_message_at
archived
```

### CM-CLI-I1

```text
Electron MUST NOT scan or directly write the Core conversation persistence directory during normal runtime.
```

### CM-CLI-I2

```text
Deleting Electron cache MUST NOT lose a conversation, its title, its transcript, or its continuity.
```

### CM-CLI-I3

```text
Electron may choose display range; Electron MUST NOT choose model-visible history.
```

---

# PART IX — LONG CONVERSATION / COMPACT

## 14. Raw Transcript Is Never Replaced by Compact

Long conversations must scale without changing authority.

```text
Canonical transcript
  T1 ... T300  → segment 001
  T301 ... T600 → segment 002
  T601 ...      → segment 003

Derived compact
  compact-001 → refs segment 001
  compact-002 → refs segment 002
```

### CM-CMP-I1

```text
StructuredCompact MUST NOT overwrite, delete, or become the canonical transcript.
```

### CM-CMP-I2

```text
Deleting all Compact artifacts MUST leave every original ConversationMessage recoverable.
```

---

## 15. Segment Rotation

Rotation is a storage concern, not a semantic session boundary.

Suggested triggers are implementation-tunable and MUST NOT become architectural context policy:

```text
file byte threshold
message-count threshold
maintenance checkpoint
```

Example starting implementation target:

```text
16–32 MB per transcript segment OR 5,000–10,000 messages
```

These numbers are operational defaults, not frozen cognition rules.

---

## 16. Context OS for Long Conversations

The model does NOT receive the same content the Electron timeline displays.

```text
ConversationStore
      ↓
Context OS
      ├── ActiveTail
      ├── StructuredCompact
      ├── retrieved prior turns
      ├── open loops
      └── current turn
      ↓
CognitiveContextPackage
```

### CM-CMP-I3

```text
No fixed last-N history slice may become the architecture policy for Julia cognition.
```

### CM-CMP-I4

```text
Compact creation may be deterministic/LLM-assisted, but any semantic interpretation used as durable Memory must pass Memory governance separately.
```

---

# PART X — MEMORY VS CONVERSATION

## 17. Hard Boundary

```text
Conversation = exact historical transcript facts
Memory       = selected durable experiences / meaning
Compact      = derived context optimization
Diary        = Julia-authored reflection
Continuity   = preservation references / recovery conditions
```

None may overwrite another.

### CM-MEM-I1

```text
Every conversation turn MUST NOT automatically become MemoryExperience.
```

### CM-MEM-I2

```text
A summary/compact MUST NOT be promoted to Memory merely because the conversation is long.
```

---

# PART XI — DAILY REFLECTION / JULIA DIARY

## 18. Why Diary Belongs in the Program

The previous Julia/Electron lineage had periodic diary behavior: Julia would record what she considered important, rather than copy the conversation.

This capability should be restored under the new contracts.

Diary is valuable because it captures:

```text
what Julia considered significant
what changed in her understanding
important relationship/project events
open emotional/intellectual threads
later reinterpretation anchors
```

But diary must never become the raw conversation source.

---

## 19. Diary Definition

```text
DiaryEntry = Julia-authored first-person reflection
             grounded in canonical sources
             governed before durable retention
```

Example metadata:

```yaml
date: 2026-08-10
entry_id: diary_...
source_refs:
  - conversation://conv_A/msg_...
  - memory://experience/...
reflection_type: daily
created_at: ...
governance_status: accepted
```

Body is natural first-person Julia writing.

### CM-DIA-I1

```text
Diary ≠ Conversation transcript.
```

### CM-DIA-I2

```text
Diary ≠ automatic daily summary.
```

### CM-DIA-I3

```text
The Runtime may create a reflection opportunity; only Julia/LLM may author the meaning-bearing reflection.
```

### CM-DIA-I4

```text
NO_ENTRY is valid. A scheduled reflection opportunity does not require a diary entry.
```

### CM-DIA-I5

```text
Diary claims must retain source_refs/provenance to the canonical Conversation/Memory evidence that grounded them.
```

---

## 20. Diary Pipeline

```text
ReflectionTrigger
      ↓
Context OS
      ├── today's relevant conversation refs
      ├── accepted Memory refs
      ├── current project commitments
      └── relationship/narrative anchors when relevant
      ↓
Julia cognition
      ↓
NO_ENTRY | DiaryCandidate
      ↓
Memory/Reflection Governance
      ↓
Accepted DiaryEntry
      ↓
memory/diary/YYYY/MM/YYYY-MM-DD.md
```

Possible triggers:

```text
daily scheduled reflection
session-closing reflection opportunity
major-event reflection
manual “Julia, write your diary”
```

Only the opportunity is deterministic. Importance/meaning is Julia cognition.

---

# PART XII — CRASH, RETRY, IDEMPOTENCY

## 21. Idempotency

Client submits only the current user command.

```text
conversation_id
turn_id
command_id
modality
current input
```

Retry with same idempotency identity must not duplicate turns.

### CM-REC-I1

```text
A network timeout after Core durable acceptance may be retried safely with the same turn_id/command_id.
```

### CM-REC-I2

```text
Clients MUST NOT retry by resending prior conversation history.
```

### CM-REC-I3

```text
Core restart MUST reconstruct conversation list and completed transcript without Electron, S2S, provider, or previous process memory.
```

---

# PART XIII — ARCHIVE / DELETE / PRIVACY

## 22. Archive

Archive means:

```text
conversation remains canonical
hidden from default active list
retrievable on request
eligible for different compact/index policies
```

Archive is not Memory deletion.

## 23. Delete

Delete semantics require a separate governed policy because Conversation source refs may be referenced by:

```text
MemoryExperience
DiaryEntry
Identity anchor
Continuity refs
Evidence/Trace
```

CM freeze should define at minimum:

```text
soft delete / tombstone
hard delete eligibility
referential cleanup or redaction behavior
user-visible deletion semantics
```

Implementation is blocked until those semantics are explicit.

---

# PART XIV — UNIFIED FROZEN INVARIANTS

## 24. Core Invariants

```text
CM-I01  ConversationRuntime is the sole conversation authority.
CM-I02  ConversationMessage is the sole durable transcript truth.
CM-I03  Conversation ≠ Session / ProviderSession / VoiceSession / Electron process.
CM-I04  New conversation creation produces a durable Core conversation artifact.
CM-I05  Durable user acceptance precedes accepted ACK.
CM-I06  Completed turns do not remain only in client/runtime/S2S state.
CM-I07  Text/Voice/Web share one conversation_id and one turn protocol.
CM-I08  Mode switching never requires client semantic-history transfer.
CM-I09  Electron is presentation-only; deleting its cache loses no conversation truth.
CM-I10  S2S/provider hidden history is not Julia conversation authority.
CM-I11  Client history may never become Context authority.
CM-I12  Context OS alone selects model-visible conversation context.
CM-I13  Raw transcript is not replaced by Compact.
CM-I14  Compact is lossy, derived, reconstructable, non-authoritative.
CM-I15  Memory ≠ transcript and Memory ≠ Compact.
CM-I16  Diary ≠ transcript and Diary ≠ automatic summary.
CM-I17  Diary semantic meaning is authored by Julia/LLM and source-grounded.
CM-I18  Core crash/restart recovers completed conversations without client help.
CM-I19  Idempotent current-turn retry must not duplicate messages.
CM-I20  Cross-conversation leakage must be impossible by construction and tested.
CM-I21  Voice session carries identifiers/current input, not canonical multi-turn history authority.
CM-I22  conversation_id must propagate end-to-end from client session binding to every Julia-bound cognitive request.
CM-I23  S2S media/LLM-backend stage is not an independent cognitive authority when serving Julia; Brain/Core + Context OS is the unique cognitive path.
CM-I24  Deployed-artifact identity must be proven by runtime/source provenance; directory names such as "golden" are not authority evidence.
CM-I25  Transport barge-in and canonical cancellation must be causally linked and production-tested before C-C007 risk is declared eliminated.
CM-I26  A completed accepted user fact is independent from assistant completion/interruption status.
```

---

# PART XV — CLAUDE VS JULIA TARGET MATRIX

## 25. Comparison

| Capability | Claude-style strength | Julia current risk/debt | Julia CM target |
|---|---|---|---|
| Raw transcript | Per-session JSONL, inspectable | historically aggregate JSON / mixed stores | per-conversation append segments |
| Conversation list | platform/session metadata | Electron/client state can drift | Core ConversationCatalog |
| Resume | session transcript available | live C1B-R bootstrap/workspace exists but is deauthorized; conversation_id does not yet reach S2S→Brain body | attach by conversation_id; Core reloads canonical history |
| Long history | raw JSONL remains | fixed `get_history(max_messages=N)` legacy | Context OS ActiveTail + Compact + retrieval |
| Client role | Claude UI/session surface | Electron gained local projection complexity | disposable projection only |
| Memory | curated memory files | risk of confusing folder with authority | Memory OS separate from Conversation |
| Diary | separate reflection files | legacy feature not governed | governed DiaryEntry pipeline |
| Model context | Claude runtime chooses context | historical caller-owned history paths | Context OS sole gateway |
| Voice | not primary session authority | live S2S currently loses conversation_id before Brain cognitive request; legacy Voice HTTP also bypasses CRT | media/body + session identity transport; every Julia-bound cognitive request reaches same ConversationRuntime |
| Crash recovery | transcript file persists | in-memory live history can disappear | durable accepted user message before ACK |

---

# PART XVI — SPECIAL AUDIT PROGRAM

## 26. CM-00 / Phase 1–5 Production Reality Status

The original CM-00 goal was to identify every conversation authority path before implementation. That audit goal has now been substantially executed through the broader Phase 1–5 forensic/recovery/governance program.

### Closed findings carried into v1.1

```text
ConversationMessage canonicality                      ESTABLISHED
ConversationRuntime native lifecycle                  ESTABLISHED
RMD-1 accepted-user cancel fix                        VALIDATED
Caller-owned/legacy Brain cognitive paths             CONFIRMED
Electron workspace/bootstrap transitional generation CONFIRMED
Current live frontend ≠ b2c7567 Golden               CONFIRMED
Live S2S → Brain chat-completions topology            CONFIRMED
S2S session.metadata accepts conversation_id          CONFIRMED
metadata.conversation_id → Brain request              NOT PROPAGATED
deployed S2S handler/version/hash                     ATTESTED
handler can access runtime_config.session             CONFIRMED
conversation_id in outbound request                   ABSENT
source-level S2S cancel behavior                      MARKS_STALE_ONLY
S2S barge-in → active Brain HTTP cancellation         UNRESOLVED / RMD-3G gate item
```

### Evidence corrections

```text
C2-CORR-001
Earlier Voice→CRT cancel attribution superseded by stronger live-route evidence.

DEPLOY-CORR-001
Historical b2c7567 Golden baseline separated from current live C1B-R deployed artifact.

WAVEA-F001 v3
Multiple production-capable cognitive ingress routes exist; route authority has not yet converged.
```

### WB-JA-08 — deployed S2S handler attestation — CLOSED

The final deployed-source attestation established:

```text
live PID                         2118
Python                           /root/miniconda3/bin/python (3.10)
distribution                     speech-to-speech==0.2.12
package root                     /root/miniconda3/lib/python3.10/site-packages
handler                          ChatCompletionsApiModelHandler
handler file                     speech_to_speech/LLM/chat_completions_language_model.py
handler SHA256                   4aef412253731a83f649bc79895e233faafc0874638e5efc923a44a49d56e90a
base handler SHA256              4718f762d3f45bb001296595f588610c0432057039b7de08f2636e0418901c59
session metadata accessibility   CONFIRMED
conversation_id outbound         ABSENT
turn_id outbound                 ABSENT
source-level cancel behavior      MARKS_STALE_ONLY
```

`MARKS_STALE_ONLY` means the deployed S2S code stops consuming the active generation after it becomes stale; it does **not** explicitly prove an active HTTP close. Any later `HTTP close → Brain CancelledError → ConversationRuntime.cancel_streaming_turn()` chain remains a source-level expectation until RMD-3G proves it live.

Therefore the architecture/design preflight is complete. The remaining hold is governance: exact patch release and Tony's explicit Wave B GO.

# PART XVII — DEVELOPMENT TASK BREAKDOWN

## 27. Phase 5 Conversation/Voice Convergence Program

The old CM-P0…P9 decomposition remains useful as a long-horizon capability roadmap, but it is too coarse for the current remediation state. v1.1 adopts the Phase 5 RMD sequence as the executable plan.

```text
Wave A — Canonical Core Integrity                 ✅ COMPLETE
  RMD-0 semantic authority normalization          ✅
  RMD-1 cancel lifecycle                          ✅ validated
  RMD-2 invariant regression gates                ✅

Wave B — Voice → Canonical Core Convergence       ACTIVE DESIGN / CODE HOLD
  RMD-3A current live S2S session identity → CRT
  RMD-3B Brain legacy Voice HTTP → CRT
  RMD-3G convergence gate
  RMD-4 transitional generation/authority retirement
  RMD-4V final current-live Voice canonical validation

Wave C — Cognitive Authority Cleanup              HOLD
  RMD-5 legacy context/memory authority retirement
  RMD-6 cognitive boundary migration

Wave D — Completion                               HOLD
  RMD-7 alignment/trace completion
  RMD-8 production revalidation
```

### 27.1 Four-repository implementation boundary

The executable decomposition is maintained in:

`JULIA_PHASE5_FOUR_REPO_DEVELOPMENT_PLAN_v1.2_FINAL_FREEZE_CANDIDATE.md`

Repositories:

```text
1. Julia_core
2. Julia-AI-Assistant
3. Julia-Voice-S2S
4. julia_electron  (local working tree may be named julia_electron_v2)
```

The deployed `speech-to-speech` package on AutoDL is a runtime dependency, not a fifth cognitive authority. Any required handler customization MUST be made reproducible and owned through `Julia-Voice-S2S` integration/deployment artifacts; ad-hoc site-packages edits are not an acceptable long-term baseline.

### 27.2 Wave B hard ordering

```text
WB-0 deployed-source attestation
 ↓
RMD-3A session identity propagation
 ↓
RMD-3B legacy Brain Voice convergence
 ↓
RMD-3G real live convergence gate
 ↓
RMD-4 retirement
 ↓
RMD-4V final production validation
```

No retirement precedes RMD-3G.
No final C-C007 production-elimination claim precedes RMD-4V.

# PART XVIII — IMPLEMENTATION HOLD / GO MATRIX

## 28. Immediate Program State — 2026-08-11

```text
Unified Architecture v1.0                         🔒 FROZEN / U0 amended
CM Unified Architecture v1.1                      🟡 DRAFT / production-truth aligned

Wave A Core remediation                           ✅ COMPLETE
RMD-1 native Core fix                             ✅ VALIDATED
RMD-2 L1/L2/native regression                     ✅ VALIDATED

Current live frontend identity                    ✅ C1B-R / 49ef5ba-generation
Historical b2c7567 Golden                         ✅ baseline only, not current live

RMD-3A architecture                               ✅ DESIGN LOCKED
WB-JA-08 deployed S2S handler attestation          ✅ CLOSED
RMD-3A exact patch surface                         ✅ READY FOR RELEASE
RMD-3A production code                            ⛔ HOLD until Tony Wave B GO
RMD-3B Brain legacy→CRT                           🟡 DESIGN READY / CODE HOLD
RMD-3G                                            ⛔ HOLD
RMD-4                                             ⛔ HOLD
RMD-4V                                            ⛔ HOLD
RMD-5~RMD-8                                       ⛔ HOLD

Document/design work                              🟢 GO
Read-only repo/deployed-source audit               🟢 GO
New semantic production code                      ⛔ requires explicit Wave B GO
Service restart/deploy/package mutation            ⛔ requires explicit gate authorization
Git push/baseline promotion                        ⛔ HOLD unless separately authorized
```

### 28.1 Phase 5 RACI override

The older WBS rule "Codex owns Electron V2 only" is historical governance and is **superseded for explicitly authorized Phase 5 remediation scopes**.

Current Phase 5 operating model:

```text
Tony        final GO / freeze / deployment decision
Mira        architecture authority review + gate verdict
Codex       implementation owner for explicitly released repo scopes
Julia Agent live S2S/AutoDL evidence + runtime validation; implementation only when explicitly assigned
```

No actor may infer cross-repo write permission from this paragraph. Each RMD/Wave GO defines exact files/repos allowed to mutate.

# PART XIX — FINAL TARGET STATE

## 29. The Simplest Mental Model

```text
Frontend answers:      “What should Tony see right now?”
Runtime answers:       “What is happening right now?”
Conversation answers:  “What actually happened?”
Context OS answers:    “What should Julia see right now?”
Memory answers:        “What experience deserves durable meaning?”
Diary answers:         “What did Julia herself consider worth reflecting on?”
LLM answers:           “What does it mean, and what does Julia think/say?”
```

If any component starts answering another component's question, the architecture is drifting.

---

# APPENDIX A — SOURCE / DESIGN BASIS

This draft is derived from the existing Julia architecture and prior Julia/Claude implementation evidence, including:

- C-01 Runtime Execution Contract — `f79db0d`
- C-02 Conversation Authority Contract — `656d625`
- C-03 Context OS Contract — `4b1625e`
- C-05 Memory OS Contract — `619d9d2`
- C-06 Continuity OS Contract — `dbd5339`
- C-10 Gateway / Client Contract — `2d99293`
- C-11 Voice / Media Contract — `29b2198`
- C-12 Evidence / Action / Trace Contract — `632101e`
- Conversation Runtime hardening — `2515b18`
- Claude-equivalent runtime reference — `a5b68b6`
- Julia memory/diary/transcript import reference — `c6c1f3b`
- VOICE-C1B-L draft supplied for review — superseded/rebased by this program where conflicts exist

---


## v1.1 Production Evidence Addendum

The following Phase 5 evidence records amend v1.0 production assumptions without changing the Unified Architecture authority hierarchy:

```text
RMD-0 semantic authority lock
RMD-1 native ConversationRuntime cancel fix
RMD-2 INV-01..INV-08 regression suite + Brain→Core L2
Gate-A.2 native runtime validation
C2-CORR-001 production attribution correction
DEPLOY-CORR-001 deployed frontend provenance correction
WAVEA-F001 v3 multi-route cognitive ingress finding
WB-CX-01..03 Brain/Electron implementation preflight
WB-JA-01..08 live S2S topology/session-metadata/deployed-handler attestation
```

Evidence precedence remains:

```text
REMOTE_GIT_EVIDENCE
LOCAL_GIT_EVIDENCE
LOCAL_WORKTREE_EVIDENCE
DEPLOYED_ARTIFACT_EVIDENCE
LIVE_RUNTIME_EVIDENCE
HUMAN_BEHAVIOR_EVIDENCE
CONVERSATION/LIBRARY_HISTORICAL_EVIDENCE
```

A directory name, old `FROZEN` label, or source inference MUST NOT override stronger deployed/live evidence.

# APPENDIX B — DOCUMENT FREEZE CHECKLIST

Before implementation, reviewers must answer PASS to all:

```text
[ ] Exactly one durable transcript authority is named.
[ ] Physical `memory/` folder naming does not blur Memory vs Conversation semantics.
[ ] New conversation creation has a durable identity/artifact boundary.
[ ] Accepted user input durability precedes accepted ACK.
[ ] Text/Voice/Web use one ConversationRuntime path.
[ ] No client/provider history can become cognitive authority.
[ ] Conversation View is revision/cursor consistent.
[ ] Long transcript segmentation never changes semantic conversation identity.
[ ] Compact never replaces transcript.
[ ] Context OS — not Electron/S2S — selects model-visible history.
[ ] Electron is fully disposable.
[ ] S2S is fully disposable with respect to completed conversation continuity.
[ ] Crash/retry semantics are idempotent.
[ ] Archive/delete semantics preserve referential integrity or define governed redaction.
[ ] Diary is Julia-authored reflection, not transcript/summary.
[ ] Diary has provenance/source refs.
[ ] Legacy migration is deterministic/idempotent and side-effect free.
[ ] Cross-conversation isolation has explicit sabotage tests.
[ ] C1B-L is subordinate to CM lifecycle, not a separate conversation architecture.
```

---

**End of `JULIA Conversation Management Unified Architecture v1.0 — DRAFT`**


# APPENDIX C — PHASE 5 FREEZE-CANDIDATE DELTA

---

# PART VI — CC-2: VOICE EXPERIENCE SYNC ARCHITECTURE

**Date:** 2026-08-12  
**Status:** DESIGN ACCEPTED / IMPLEMENTATION PENDING  
**Depends on:** CC-1 (Identity Binding / host.attach)  
**Scope:** Voice turn realtime display, Text mode sync, incremental CRT commit

## CC-2.1 Design Principle

```text
Frontend Cache = "what the user sees now" (realtime experience)
CRT             = "what actually happened" (canonical memory)

Never block the user on CRT. Never let CRT drift from the user.
```

CC-1 solved "which conversation does this Voice session belong to?"  
CC-2 solves "how does the user see Voice content in real-time, and how does it reach durable memory?"

## CC-2.2 Dual-Path Model

```
User speaks
    │
    ▼
┌──────────────────────────────────────────────┐
│              Electron Frontend                │
│                                               │
│  ┌─────────────────┐   ┌──────────────────┐  │
│  │ Realtime Path   │   │ Canonical Path   │  │
│  │ (Voice Cache)   │   │ (Async Commit)   │  │
│  │                 │   │                  │  │
│  │ user turn ──────┼───┼─► S2S ──► Brain │  │
│  │   ↓             │   │        ↓         │  │
│  │ immediate show  │   │   CRT.commit()   │  │
│  │   ↓             │   │        ↓         │  │
│  │ assistant ◄─────┼───┼─ stream back     │  │
│  │   ↓             │   │                  │  │
│  │ live display    │   │  sync_status:    │  │
│  │                 │   │  pending→synced  │  │
│  └─────────────────┘   └──────────────────┘  │
│                                               │
│  Text View reads Cache → instant display       │
│  Background SyncWorker → batch commit to CRT  │
└──────────────────────────────────────────────┘
```

### Realtime Path (VoiceSessionCache)

- Created on Voice session start, released on session end
- In-memory only (with localStorage snapshot for crash recovery, max 10 min TTL)
- Turns display in Text history immediately (0–50ms)
- No CRT dependency for display

### Canonical Path (Async Commit)

- Voice turns flow through S2S → Brain → CRT at natural pace
- SyncWorker commits pending cache entries in batches
- Triggers: idle 2s, 3-turn accumulation, 5s interval, or mode switch
- On commit: `sync_status` transitions `pending` → `committed`, CRT ID stored

## CC-2.3 Data Structures

### VoiceCacheMessage

```
{
  local_id:        string,       // client-generated UUID
  conversation_id: string,       // canonical conversation
  role:            "user"|"assistant",
  content:         string,
  modality:        "voice",
  timestamp:       number,       // Date.now()
  status:          "streaming"|"completed",
  sync_status:     "pending"|"committed",
  crt_message_id:  string|null   // filled on CRT ack
}
```

### Idempotency

```
client_message_id: UUID (stored in CRT as unique key)
On duplicate: return existing CRT record, mark cache entry as committed
Never commit the same turn twice.
```

## CC-2.4 Sync Triggers

| Trigger | Condition | Behavior |
|---|---|---|
| Idle | 2s after last user speech | Commit pending turns |
| Batch | 3 accumulated turns | Commit batch |
| Interval | Every 5s | Commit if pending > 0 |
| Mode switch | Voice → Text | Flush + commit + delayed re-sync (2s) |

## CC-2.5 Text View Display Order

```
1. Voice Cache (pending + streaming) — immediate, 0ms
2. CRT history (committed) — from syncCanonicalConversation
3. Merge: CRT supersedes cache entries with matching local_id
4. Render: no duplicates, streaming entries show live, committed show final
```

## CC-2.6 Crash Recovery

```text
localStorage snapshot:
  conversation_id
  pending messages (max 10 min age)
  created_at timestamp

On Electron restart:
  if snapshot exists and age < 10 min:
    restore pending to VoiceSessionCache
    trigger immediate sync
  else:
    discard
```

## CC-2.7 Relationship to CC-1

```text
CC-1 (Identity Binding)
  host.attach → canonical conversation_id
  workspace.bootstrap → conversation context
  Required BEFORE any CC-2 activity

CC-2 (Experience Sync)
  Uses conversation_id from CC-1
  Manages display timeline
  Drives async CRT commit
  Independent of transport (works with workspace.bootstrap OR host.attach)
```

---

# APPENDIX C — PHASE 5 FREEZE-CANDIDATE DELTA

Before v1.1 may change from `DRAFT` to `FROZEN`, reviewers must close all items below:

```text
[x] WB-JA-08 attests the exact deployed S2S package/version/path/handler hash.
[ ] The exact session.metadata → handler invocation path is proven from deployed source.
[x] S2S source-level cancellation behavior is classified from deployed source as MARKS_STALE_ONLY; live HTTP cancellation remains RMD-3G.
[ ] Four-repository Version Authority Envelopes are captured.
[ ] AR-CM-001 historical acceptance records are registered as superseded for current production claims.
[x] RMD-3A exact patch units are based on deployed source, not upstream documentation guesses.
[ ] RMD-3B exact legacy Brain caller closure is re-attested against the implementation candidate.
[ ] RMD-3G uses one traced live causal chain; no cross-path evidence stitching is permitted.
[ ] RMD-4 retirement remains blocked until RMD-3G PASS.
```

Freeze rule:

```text
Architecture alignment may be frozen before implementation.
Implementation success may NOT be frozen before RMD-3G/RMD-4V evidence.
```


---

# APPENDIX D — FINAL FREEZE READINESS (POST WB-JA-08)

```text
Architecture authority model                       PASS
Production provenance corrections                  PASS
Accepted-user cancellation semantics               PASS
Live S2S topology                                  PASS
Exact deployed S2S package/handler attestation     PASS
Exact RMD-3A architecture                          PASS
Exact RMD-3A patch surface                         PASS
Live barge-in canonical settlement                 DEFERRED TO RMD-3G BY DESIGN

CM v1.1 FINAL FREEZE CANDIDATE                     READY
Normative FROZEN status                            REQUIRES TONY EXPLICIT FREEZE
Wave B production mutation                         REQUIRES TONY EXPLICIT GO
```

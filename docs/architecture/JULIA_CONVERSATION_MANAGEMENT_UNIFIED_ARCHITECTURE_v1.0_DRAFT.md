# JULIA Conversation Management Unified Architecture v1.0 — DRAFT

**Document Type:** Unified Architecture + Freeze Contract + Development Plan  
**Status:** DRAFT — Stage 1 / Stage 2 split applied  
**Date:** 2026-08-10  
**Scope:** Conversation lifecycle, canonical storage, long-conversation compact, Electron projection, Voice/Text convergence, crash/retry semantics, Claude comparison, Daily Reflection/Diary  
**Parent:** `JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0` + frozen C-01/C-02/C-03/C-05/C-06/C-10/C-11/C-12  
**Supersedes as conversation architecture:** VOICE-C1B-R workspace-reconcile model  
**Reclassifies:** VOICE-C1B-L as Voice modality implementation under CM-Core  
**Program Gate:** Stage 1 (CM-Core) freezes now. Stage 2 (CM-Extended: Storage v2, Compact, Diary, Archive/Delete, Legacy Migration) deferred.  

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

Normal turn:

```text
TURN_CREATED
→ USER_ACCEPTED_DURABLE
→ COGNITION_RUNNING
→ ASSISTANT_GENERATED
→ ASSISTANT_FINALIZED
→ TURN_COMPLETED
```

Voice adds a media lifecycle without creating a new conversation lifecycle:

```text
assistant generated
→ TTS/rendering
→ emitted-content settled
→ completed | interrupted
```

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
Completed prior turns MUST NOT accumulate in RuntimeTurn, VoiceWorkspace, Electron, or S2S history.
```

---

# PART VI — TEXT / VOICE CONVERGENCE

## 11. Mode Switching

Correct model:

```text
Voice surface ──┐
Text surface ───┼── attach(conversation_id)
Web surface ────┘
```

Mode switches do not “transfer history.”

### Voice → Text

```text
stop/pause media
show Text UI
GET Conversation View from Core
render canonical + current Core runtime projection
```

### Text → Voice

```text
open Voice media
bind conversation_id
start capture
FINAL ASR → same Core turn ingress
```

No semantic `workspace.flush()` and no client `history bootstrap` are required.

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
S2S Chat/provider history may exist as transport implementation state, but clearing it MUST NOT erase Julia's completed conversational continuity.
```

---

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

## 24. Core Invariants — Stage 1 (CM-CORE)

Production-validated invariants. These freeze now.

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
CM-I18  Core crash/restart recovers completed conversations without client help.
CM-I19  Idempotent current-turn retry must not duplicate messages.
CM-I20  Cross-conversation leakage must be impossible by construction and tested.
```

## 24b. Invariants — Referenced (Existing Foundation Contracts)

These are already covered by C-02/C-03/C-05. CM-Core references them; no new freeze required.

```text
CM-I13  Raw transcript is not replaced by Compact.          → C-02 Conversation Authority
CM-I14  Compact is lossy, derived, reconstructable.          → C-03 Context OS
CM-I15  Memory ≠ transcript and Memory ≠ Compact.            → C-05 Memory OS
```

## 24c. Invariants — Stage 2 (CM-Extended)

Deferred to CM-DIARY and CM-LIFECYCLE-RETENTION. Not required for CM-Core freeze.

```text
CM-I16  Diary ≠ transcript and Diary ≠ automatic summary.   → CM-DIARY
CM-I17  Diary semantic meaning is authored by Julia/LLM.    → CM-DIARY
```

---

# PART XV — CLAUDE VS JULIA TARGET MATRIX

## 25. Comparison

| Capability | Claude-style strength | Julia current risk/debt | Julia CM target |
|---|---|---|---|
| Raw transcript | Per-session JSONL, inspectable | historically aggregate JSON / mixed stores | per-conversation append segments |
| Conversation list | platform/session metadata | Electron/client state can drift | Core ConversationCatalog |
| Resume | session transcript available | Voice bootstrap/workspace races | attach by conversation_id |
| Long history | raw JSONL remains | fixed `get_history(max_messages=N)` legacy | Context OS ActiveTail + Compact + retrieval |
| Client role | Claude UI/session surface | Electron gained local projection complexity | disposable projection only |
| Memory | curated memory files | risk of confusing folder with authority | Memory OS separate from Conversation |
| Diary | separate reflection files | legacy feature not governed | governed DiaryEntry pipeline |
| Model context | Claude runtime chooses context | historical caller-owned history paths | Context OS sole gateway |
| Voice | not primary session authority | S2S/VoiceWorkspace became shadow history | modality only, same ConversationRuntime |
| Crash recovery | transcript file persists | in-memory live history can disappear | durable accepted user message before ACK |

---

# PART XVI — SPECIAL AUDIT PROGRAM

## 26. CM-00 — Production Reality Audit

**Goal:** identify every current conversation storage, read, write, compact, history, session, Voice, Electron and diary path.

Required inventory:

```text
julia_core ConversationRuntime
conversation_state repository/models
legacy SessionStore
Julia-AI-Assistant Brain/openai_compat/shared_orchestration
julia_electron conversation list/cache/render/reconcile
Julia-Voice-S2S VoiceWorkspace/S2S Chat/bootstrap/flush
legacy diary/session recorder/session summarizer
migration/import scripts
all direct filesystem conversation reads/writes
all history[-N] / max_messages / hard caps
```

Deliverables:

```text
CM00_REALITY_MAP.md
CM00_AUTHORITY_GRAPH.md
CM00_CONFLICT_REGISTER.md
CM00_DATA_INVENTORY.md
```

Gate:

```text
No unknown production conversation path remains.
```

---

# PART XVII — DEVELOPMENT TASK BREAKDOWN

## 27. Program Order

### CM-SPIKE-01 — Durable Turn Acceptance Feasibility

**Runs in parallel with CM-00. Experimental only. Not production.**

Goal: answer whether `durable user acceptance before ACK` is fast enough.

Test interface:

```python
accept_user_turn(conversation_id, turn_id, modality, content)
```

What it does:
- validate conversation
- idempotency check
- durable append user fact
- fsync / transaction boundary
- return ACK

What it does NOT do:
- LLM, Memory, Compact, Continuity, TTS, Electron, Voice

Metrics:
- p50 / p95 / p99 latency
- cold write
- concurrent different conversations
- same conversation retry
- crash-after-ACK recovery

Gate: ACK only after durable acceptance. No RAM-first shortcut. Latency target is a measurement, not a contract.

---

### Phase CM-P0 — Audit / Characterization

**No semantic production changes.**

Tasks:

- `P0-01` inventory all conversation repositories and physical files.
- `P0-02` trace new conversation creation end-to-end.
- `P0-03` trace text turn write/read end-to-end.
- `P0-04` trace Voice FINAL ASR → Brain/Core end-to-end.
- `P0-05` trace Electron conversation list/open/reconcile.
- `P0-06` trace model-visible conversation history source for every ingress.
- `P0-07` locate all fixed `last-N`, `max_messages`, trim, token/window policies.
- `P0-08` locate all VoiceWorkspace/bootstrap/flush dependencies.
- `P0-09` locate legacy diary/session summarization paths.
- `P0-10` build characterization tests before replacement.

**Exit gate:** production reality closed; zero unknown authority paths.

---

### Phase CM-P1 — Contract Freeze

Create/freeze:

```text
CM-01 Conversation Storage Contract
CM-02 Conversation Lifecycle Contract
CM-03 Long Conversation / Compact Contract
CM-04 Client Projection Contract
CM-05 Daily Reflection / Diary Contract
```

Tasks:

- freeze canonical file schema and directory layout;
- freeze catalog semantics;
- freeze append/idempotency semantics;
- freeze accepted-ACK durability boundary;
- freeze mode-switch semantics;
- freeze compact boundaries and provenance;
- freeze archive/delete semantics;
- freeze diary candidate/governance semantics.

**Exit gate:** all contract acceptance checklists PASS before implementation.

---

### Phase CM-P2 — Conversation Storage v2

Tasks:

- `P2-01` introduce `ConversationStoreV2` abstraction.
- `P2-02` per-conversation directory creation.
- `P2-03` `meta.json` atomic update strategy.
- `P2-04` append-only transcript JSONL writer.
- `P2-05` segment rotation.
- `P2-06` ConversationCatalog/index rebuild from disk.
- `P2-07` cursor-based transcript paging.
- `P2-08` fsync/durability policy for accepted user turns.
- `P2-09` corruption isolation and partial-tail recovery.
- `P2-10` tests: restart, torn-write, duplicate append, catalog rebuild.

**Important:** do not migrate all clients yet.

---

### Phase CM-P3 — ConversationRuntime v2

Tasks:

- `P3-01` make ConversationRuntime sole create/open/append/read owner.
- `P3-02` durable accepted user append before ACK.
- `P3-03` Core RuntimeTurn state only for in-flight execution.
- `P3-04` canonical assistant finalization.
- `P3-05` interrupted assistant / emitted-content semantics.
- `P3-06` per-conversation single-flight/concurrency policy.
- `P3-07` idempotency by conversation_id + turn_id/command_id.
- `P3-08` atomic `ConversationView` projection.

**Exit gate:** Text path fully authoritative and restart-safe.

---

### Phase CM-P4 — Context OS / Long Conversation

Tasks:

- `P4-01` remove legacy fixed-history path from production cognition.
- `P4-02` canonical `ConversationContextSource` reads ConversationStore only.
- `P4-03` ActiveTail budget-driven selection.
- `P4-04` StructuredCompact schema with source message/turn refs.
- `P4-05` compact generation worker.
- `P4-06` compact invalidation/rebuild.
- `P4-07` retrieval of prior canonical turns.
- `P4-08` prove deletion of compact leaves truth intact.
- `P4-09` long conversation 10k+/100k+ message simulation.

**Exit gate:** model context independent of Electron display and fixed last-N slices.

---

### Phase CM-P5 — Electron Client Simplification

Tasks:

- `P5-01` conversation list from Core catalog API only.
- `P5-02` create conversation through Core command.
- `P5-03` lazy/paged transcript rendering.
- `P5-04` optimistic current-turn projection with canonical reconciliation.
- `P5-05` remove local multi-turn semantic authority.
- `P5-06` cache deletion/restart acceptance.
- `P5-07` A/B conversation race sabotage tests.

**Exit gate:** Electron can be deleted/reinstalled and all conversation truth reloads from Core.

---

### Phase CM-P6 — Voice/Text Convergence (C1B-L Rebased)

C1B-L becomes an implementation profile of CM-02, not a new conversation architecture.

Tasks:

- `P6-01` FINAL ASR → same ConversationRuntime ingress.
- `P6-02` remove VoiceWorkspace multi-turn history ownership.
- `P6-03` remove semantic workspace flush/bootstrap from normal path.
- `P6-04` Brain rejects/ignores caller-owned external history for Julia-bound conversation.
- `P6-05` S2S treats history only as non-authoritative transport/provider state.
- `P6-06` Voice → Text instant attach.
- `P6-07` Text → Voice instant attach.
- `P6-08` rapid switch ×10 sabotage.
- `P6-09` destroy S2S process/cache and prove continuity remains.
- `P6-10` long-response/interruption media correctness after conversation authority is stable.

**Exit gate:** no completed semantic turn depends on Voice frontend/S2S history.

---

### Phase CM-P7 — Daily Reflection / Julia Diary

Tasks:

- `P7-01` formal `ReflectionTrigger`.
- `P7-02` Context OS reflection package (source refs only through governed sources).
- `P7-03` Julia/LLM emits `NO_ENTRY | DiaryCandidate`.
- `P7-04` governance validation and provenance.
- `P7-05` diary file writer `YYYY/MM/YYYY-MM-DD.md`.
- `P7-06` diary index/list/read capability through Core.
- `P7-07` privacy/retention policy.
- `P7-08` prevent diary from becoming Conversation/Identity authority.
- `P7-09` daily scheduled reflection opportunity.
- `P7-10` major-event/manual reflection support.

**Exit gate:** diary meaning comes from Julia cognition; no forced daily boilerplate summaries.

---

### Phase CM-P8 — Legacy Migration

Sources may include:

```text
legacy data/conversations.json
.julia sessions.json
Claude session JSONL
Julia-AI-Assistant transcripts.jsonl
legacy Electron caches (only through governed import)
legacy Voice workspace remnants if canonical facts are recoverable
```

Tasks:

- deterministic IDs;
- preserve original timestamps/order;
- provenance source labels;
- no auto-memory during import;
- no diary generation during import;
- idempotent re-run;
- parity counts/digests;
- quarantine ambiguous/corrupt records.

**Exit gate:** legacy history imported without changing semantic truth.

---

### Phase CM-P9 — Final Acceptance / Freeze

Required sabotage suite:

```text
AT-CM01 create conversation → durable artifact exists
AT-CM02 accepted input → Core crash → input survives
AT-CM03 network ACK lost → retry → no duplicate
AT-CM04 Electron cache delete → full list/history recovered
AT-CM05 S2S process delete/restart → conversation continuity preserved
AT-CM06 Voice↔Text <500ms ×10 → zero lost/duplicate turns
AT-CM07 A/B rapid switch → zero cross-conversation leakage
AT-CM08 10k+ message conversation → UI pages; Context still coherent
AT-CM09 delete all compact artifacts → raw transcript unchanged/reconstructable
AT-CM10 provider/model switch → same conversation continuity
AT-CM11 interrupted Voice assistant → correct canonical interrupted content
AT-CM12 archive/reopen → exact conversation restored
AT-CM13 Conversation import twice → idempotent
AT-CM14 Memory formation never rewrites transcript
AT-CM15 Diary entry has source refs and is not transcript copy
AT-CM16 NO_ENTRY reflection creates no meaningless diary
AT-CM17 Core catalog rebuild from conversation directories
AT-CM18 corrupt one conversation segment → unrelated conversations unaffected
AT-CM19 client cannot upload full history as runtime authority
AT-CM20 Context OS trace shows all model-visible Conversation content from canonical Core sources
```

Final freeze only when all required ATs pass.

---

# PART XVIII — IMPLEMENTATION HOLD / GO MATRIX

## 28. Program Gate — Stage 1 vs Stage 2

```
════════════════════════════════════════════
FOUNDATION
════════════════════════════════════════════
C-00 ... C-12                         🔒 FROZEN


════════════════════════════════════════════
STAGE 1 — CM CORE
════════════════════════════════════════════

CM-00 Production Reality Audit         🟢 GO (READ-ONLY)
    ↓
CM-SPIKE-01 Durable Turn Accept        🟢 CAN RUN IN PARALLEL
    Benchmark: accept→ACK latency        (experimental only, not production)
    ↓
CM-Core Contract Freeze                ⏸ WAIT CM-00
    I01-I12 + I18-I20
    ↓
CM-02 ConversationRuntime v2           ⛔ HOLD
    durable accept / idempotency /
    single conversation authority
    ↓
CM-03 Client Protocol Convergence      ⛔ HOLD
    Electron / Text / Voice / S2S
    ↓
CM-CORE ACCEPTANCE                     ⛔ HOLD
    Rapid switch / restart /
    cross-conversation / cache deletion
    ↓
    🔒 CM-CORE FROZEN


════════════════════════════════════════════
STAGE 2 — CM EXTENDED (all deferred)
════════════════════════════════════════════

Storage v2 / segmentation              ⏸ DEFER
Long Conversation / Compact             ⏸ DEFER
CM-Diary / Daily Reflection            ⏸ DEFER
CM-LIFECYCLE-RETENTION                  ⏸ DEFER
    Archive / Delete / Tombstone / Privacy
Legacy migration                        ⏸ DEFER
```

### Storage Layout: Target Candidate, Not Frozen

The `memory/conversations/conv_xxx/` layout in §5 is a design target. Until CM-00 audits the current production persistence, the following are the only frozen storage requirements:

```
- conversation_id has a durable Core representation
- messages are append/canonical
- conversation list is reconstructable from Core
- client deletion cannot lose conversation truth
- storage implementation is replaceable
```

JSON/JSONL/SQLite/segmented files are implementation choices. The physical layout in §5 is NON-BINDING until a separate CM-Storage Audit.

---

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

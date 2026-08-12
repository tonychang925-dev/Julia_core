# JULIA Conversation Storage & Diary Development Plan v1.0

**Document Type:** Post-Freeze Development Work Breakdown / Execution Plan  
**Status:** PROPOSED FOR EXECUTION  
**Date:** 2026-08-13  
**Program:** Conversation Storage + Management + Julia Diary  
**Architecture Basis:** `JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1_FINAL_FREEZE_CANDIDATE.md` and frozen Core contracts  
**Primary Principle:** **Hardening and productization, not redesign.**

---

# 0. Executive Decision

This program MUST continue the already-frozen Julia architecture.

```text
Julia_core
= Julia OS / semantic kernel
= ConversationRuntime / Context OS / Memory OS / Continuity OS
= owns semantic contracts and invariants
≠ application-specific physical data host

Julia-AI-Assistant
= Julia application host / Brain / composition root
= owns physical application persistence
= binds Core repository/storage ports to <PRIVATE_JULIA_DATA>

Julia_client / julia_electron_v2
= desktop shell / projection
= conversation management UI
= may cache display state
≠ canonical transcript authority

Julia-Voice-S2S
= media / transport adapter
= STT / TTS / streaming / barge-in
≠ conversation / memory / diary authority
```

Canonical semantic ownership remains unchanged:

```text
ConversationRuntime = sole conversation authority
ConversationMessage = sole durable transcript truth
Context OS          = sole model-visible context authority
Memory OS           = durable experience governance
Diary               = Julia-authored reflective artifact
Continuity OS       = preservation/recovery refs and requirements
```

Physical persistence ownership is added as an application binding:

```text
Julia-AI-Assistant
    ↓
Persistence Adapters
    ↓
<PRIVATE_JULIA_DATA>
```

This does **not** transfer semantic authority from Julia Core to the Assistant.

---

# 1. Non-Negotiable Frozen Invariants

The following rules are inherited from the frozen architecture and MUST NOT be reinterpreted by implementation.

## INV-01 — One conversation world

Text / Voice / Web / future Mobile use the same `conversation_id` and the same canonical ConversationRuntime semantics.

## INV-02 — Conversation is not Session

A conversation survives:

- Electron restart
- Voice reconnect
- S2S restart
- Brain restart
- provider/model replacement
- process restart

## INV-03 — Canonical transcript is append-first

Completed historical transcript MUST NOT be silently rewritten by:

- Compact
- Context budgeting
- Memory formation
- Diary generation
- Electron reconciliation
- Voice cache synchronization

## INV-04 — Client caches are disposable

Deleting Electron cache or VoiceSessionCache MUST cause zero loss of completed canonical conversation truth.

## INV-05 — Context OS remains the only cognition gateway

Storage pagination/search/UI selection MUST NOT become the model-visible context policy.

No fixed `last-N` UI/storage limit may become Julia cognition policy.

## INV-06 — Diary is not transcript

```text
Conversation = what actually happened
Memory       = what experience deserves durable meaning
Compact      = derived context optimization
Diary        = what Julia herself considered worth reflecting on
Continuity   = what must remain recoverable across disruption
```

None may overwrite another.

## INV-07 — Diary is not automatic daily summary

`NO_ENTRY` is valid.

A scheduled trigger creates only a **reflection opportunity**.

The runtime/scheduler does not decide the meaning.

Julia/LLM authors the reflection.

## INV-08 — Diary must be source-grounded

Each accepted diary entry MUST retain provenance/source refs to canonical Conversation and/or accepted Memory evidence.

## INV-09 — Runtime provenance remains mandatory

No dirty/uncommitted production runtime may be accepted.

VOICE-C1 RP-1 provenance gates remain in force.

## INV-10 — Authority cutovers follow ADR-002

Any storage-authority migration MUST execute:

```text
FREEZE
→ RECONCILE
→ VERIFY
→ ACTIVATE
→ RETIRE
```

No silent dual writer is allowed.

---

# 2. Target Physical Filesystem

The physical root is owned and resolved by **Julia-AI-Assistant**.

Recommended product variable:

```text
JULIA_PRIVATE_DATA_ROOT=<PRIVATE_JULIA_DATA>
```

Recommended macOS default:

```text
~/Library/Application Support/JuliaAI/
```

The product MUST NOT make the Git working tree the canonical user-data location.

Target layout:

```text
<PRIVATE_JULIA_DATA>/
│
├── memory/                         # durable semantic artifacts
│   │
│   ├── conversations/             # Conversation authority persistence
│   │   ├── index.json
│   │   ├── conv_<conversation_id>/
│   │   │   ├── meta.json
│   │   │   ├── transcript-000001.jsonl
│   │   │   ├── transcript-000002.jsonl
│   │   │   ├── compact/
│   │   │   │   ├── compact-000001.json
│   │   │   │   └── ...
│   │   │   └── attachments/
│   │   └── ...
│   │
│   ├── diary/                     # Julia-authored reflections
│   │   └── YYYY/
│   │       └── MM/
│   │           └── YYYY-MM-DD.md
│   │
│   ├── experiences/               # Memory OS persistence
│   ├── identity/                  # Identity persistence
│   └── continuity/                # Continuity checkpoints/refs
│
├── indexes/                       # derived / rebuildable only
│   ├── conversation_catalog.db
│   ├── conversation_fts.db
│   └── diary_fts.db
│
├── runtime/                       # ephemeral / reconstructable
│   ├── cache/
│   ├── locks/
│   └── state/
│
├── migrations/
│   ├── state/
│   └── reports/
│
├── backups/
│
└── logs/
```

## Filesystem authority rules

| Path | Semantic role | Canonical? | Writer | Rebuildable? |
|---|---|---:|---|---:|
| `memory/conversations/*` | canonical transcript | YES | Assistant adapter under Core runtime contract | NO |
| `memory/diary/*` | accepted Julia reflections | YES | Reflection persistence adapter after governance | NO |
| `memory/experiences/*` | accepted Memory objects | YES | Memory OS persistence adapter | NO |
| `memory/identity/*` | identity artifacts | YES | Identity-governed path | NO |
| `memory/continuity/*` | continuity refs/checkpoints | YES | Continuity OS adapter | NO |
| `indexes/*` | search/catalog acceleration | NO | indexers | YES |
| `runtime/*` | process/cache state | NO | runtime | YES |
| `backups/*` | recovery copy | derived copy | backup service | YES from source |
| `logs/*` | observability | NO | services | N/A |

---

# 3. Program Structure

```text
STO-A0   Authority Reconciliation
STO-F1   Private Filesystem Contract
STO-F2   Application Persistence Binding
CM-S1    Conversation Storage Adapter
CM-S2    Conversation Catalog / Read Model
CM-S3    Conversation Management Service
CM-S4    Brain HTTP Management API
CM-S5    Electron Conversation Manager
CM-S6    Archive/Delete Governance
CM-S7    Legacy Migration / Cutover
DIA-0    Claude Julia Diary Audit & Semantic Reclassification
DIA-1    Diary Domain Contract Implementation
DIA-2    Diary Persistence
DIA-3    Reflection Trigger Runtime
DIA-4    Reflection Context Assembly
DIA-5    Julia Reflection Generation
DIA-6    Reflection Governance
DIA-7    Diary Retrieval / Context Integration
DIA-8    Electron Diary UI
OPS-1    Backup / Restore
OPS-2    Index Rebuild / Repair
AT-1     End-to-End Acceptance
FREEZE   Final baseline
```

---

# 4. STO-A0 — Authority Reconciliation

**Goal:** refresh authority envelopes before feature implementation.

## STO-A0-T01 — Capture current repository baselines

Capture exact:

```text
Julia_core
Julia-AI-Assistant
Julia_client / julia_electron_v2
Julia-Voice-S2S
```

For each:

- branch
- HEAD
- clean/dirty state
- authority doc head
- approved production source SHA
- deployed artifact identity where applicable
- live runtime identity where applicable

### Deliverable

`docs/authority/STORAGE_PROGRAM_BASELINE_20260813.md`

### PASS

No baseline is inferred from chat history or directory names.

---

## STO-A0-T02 — Refresh Four-Repo Authority Manifest

Update the global authority manifest to include:

- VOICE-C1 closed baseline
- RP-1 Runtime Authority Hardening
- RP-2 canonical UUID turn identity
- RP-3 ADR-002 cutover contract
- current Electron projection baseline
- Storage Program entry point

### PASS

The highest-level authority document no longer points to pre-VOICE-C1 runtime assumptions.

---

## STO-A0-T03 — Freeze physical persistence ownership

Add compatible architecture amendment:

```text
Semantic authority:
    Julia_core

Application physical persistence host:
    Julia-AI-Assistant

Projection:
    Electron

Media:
    S2S
```

### Critical wording

```text
Physical persistence ownership does not transfer semantic authority.
```

### Deliverable

Suggested:

`Julia_core/docs/adrs/ADR-003-application-persistence-host-binding.md`

or another number following the current ADR registry.

### Gate STO-A0

```text
[ ] Four-repo baselines attested
[ ] Authority manifest current
[ ] Physical owner explicitly frozen
[ ] No Core semantic contract changed
[ ] No storage implementation started before PASS
```

---

# 5. STO-F1 — Private Julia Filesystem Contract

**Owner of physical implementation:** Julia-AI-Assistant  
**Owner of semantic definitions:** Julia Core frozen contracts

## STO-F1-T01 — Root resolver

Implement one canonical resolver:

```text
JULIA_PRIVATE_DATA_ROOT
```

Resolution precedence should be explicit, for example:

1. explicit environment variable
2. product default
3. fail closed if path cannot be safely initialized

Do not allow different services to invent independent roots.

### Tests

- env override
- spaces in path
- non-existent path bootstrap
- permissions denied
- symlink behavior
- repo checkout path rejection if policy requires it

---

## STO-F1-T02 — Filesystem bootstrap

Create only approved directories.

Bootstrap MUST be idempotent.

```text
ensure_private_data_layout()
```

Repeated execution must not rewrite semantic files.

---

## STO-F1-T03 — Permissions policy

Recommended:

- private root owner-only where practical
- secrets are NOT stored in semantic memory files
- logs must not copy unrestricted full sensitive transcript by default
- backup directory follows same privacy boundary

---

## STO-F1-T04 — Filesystem version metadata

Add root-level operational metadata, e.g.:

```json
{
  "layout_version": "julia-private-data-v1",
  "created_at": "...",
  "application": "Julia-AI-Assistant"
}
```

This file is operational metadata, not cognition authority.

---

## STO-F1-T05 — Derived index separation

Define:

```text
indexes/* may be deleted and rebuilt
```

Acceptance test:

```text
rm -rf indexes/*
restart/rebuild
→ zero semantic loss
```

### Gate STO-F1

```text
[ ] one canonical root
[ ] repo-independent data location
[ ] deterministic directory bootstrap
[ ] semantic/derived separation explicit
[ ] permissions tested
```

---

# 6. STO-F2 — Application Persistence Binding

**Goal:** Assistant becomes composition root without stealing semantic authority.

## STO-F2-T01 — Audit existing Core repository protocols

Audit whether existing contracts are sufficient for:

- create/get conversation
- durable append
- find turn
- idempotent retry
- list
- pagination
- title/state update
- import
- archive/delete support

### Rule

Default action:

```text
NO CORE CHANGE
```

If a required capability is missing:

```text
evidence
→ protocol gap
→ architecture review
→ compatible contract extension
→ only then implementation
```

No convenience patch into Core.

---

## STO-F2-T02 — Assistant persistence composition root

At Brain startup:

```text
PrivateDataRoot
    ↓
ConversationRepositoryAdapter
MemoryRepositoryAdapter
DiaryRepositoryAdapter
ContinuityRepositoryAdapter
    ↓
Julia Core runtimes/services
```

No module should instantiate a private fallback path behind the composition root.

---

## STO-F2-T03 — Startup attestation

Brain startup stamp should include:

```text
PRIVATE_DATA_ROOT
CONVERSATION_BACKEND
CONVERSATION_SCHEMA_VERSION
DIARY_BACKEND
INDEX_BACKEND
```

Do not log secrets or transcript contents.

---

# 7. CM-S1 — Canonical Conversation Storage Adapter

**Physical implementation location:** Julia-AI-Assistant

Target canonical format:

```text
memory/conversations/
├── index.json
└── conv_<cid>/
    ├── meta.json
    ├── transcript-000001.jsonl
    ├── transcript-000002.jsonl
    ├── compact/
    └── attachments/
```

## CM-S1-T01 — Conversation metadata model

Required fields:

```json
{
  "conversation_id": "conv_...",
  "title": "...",
  "created_at": "...",
  "updated_at": "...",
  "state": "active",
  "last_message_id": "msg_...",
  "last_turn_id": "turn_...",
  "message_count": 0,
  "segment_count": 1,
  "schema_version": "cm-1"
}
```

Metadata is a durable read model around canonical transcript identity.

---

## CM-S1-T02 — Atomic conversation creation

Flow:

```text
create request
→ allocate durable conversation_id
→ create conversation directory
→ write meta.json atomically
→ update catalog atomically
→ return established conversation
```

Electron must not treat a conversation as established before durable creation succeeds.

### Failure tests

- directory exists
- metadata write fails
- catalog update fails
- process crash between steps

Define recovery rules.

---

## CM-S1-T03 — Append-only transcript writer

Each completed canonical `ConversationMessage` is serialized exactly once.

Requirements:

- UTF-8
- one JSON object per line
- append-first
- fsync/durability policy explicit
- canonical order generated from Core semantic order
- client arrival order is not authority

---

## CM-S1-T04 — User acceptance durability

Preserve frozen ordering:

```text
current user input
→ validate cid / turn identity / idempotency
→ durable append user message
→ ACK accepted
→ cognition
```

A Brain crash after accepted ACK must not erase accepted user input.

---

## CM-S1-T05 — Assistant completion append

On success:

```text
same canonical turn_id
user completed
assistant completed
```

On assistant cancellation/failure:

- user accepted record remains
- assistant lifecycle follows frozen runtime semantics

---

## CM-S1-T06 — Idempotency

Key invariant:

```text
same logical turn retry
→ same turn identity
→ zero duplicate canonical messages
```

Include regression for the repaired Voice UUID rule.

---

## CM-S1-T07 — Segment rotation

Operational trigger only.

Starting target may use frozen guidance such as:

```text
16–32 MB
OR
5,000–10,000 messages
```

This is storage maintenance, NOT cognition policy.

Segment rotation must not change:

- `conversation_id`
- turn identity
- chronological semantic order
- resume behavior

---

## CM-S1-T08 — Corruption isolation

Test:

```text
damage conv_A/transcript-000002.jsonl
→ conv_B remains readable
```

One conversation archive must not corrupt all conversations.

---

## CM-S1 Gate

```text
[ ] durable create
[ ] durable user acceptance
[ ] append-only completed transcript
[ ] idempotent retry
[ ] segment rotation
[ ] crash recovery
[ ] cross-conversation isolation
[ ] Core semantic behavior unchanged
```

---

# 8. CM-S2 — Conversation Catalog & Read Model

## CM-S2-T01 — Canonical catalog

`memory/conversations/index.json`

Contains only list/resume metadata.

It MUST NOT become a transcript substitute.

---

## CM-S2-T02 — Catalog rebuild

Required capability:

```text
delete/corrupt index.json
→ scan conversation directories
→ rebuild
```

Conversation directories remain source evidence.

---

## CM-S2-T03 — Pagination

Implement cursor-based reads across transcript segments.

Requirements:

- stable chronological ordering
- `before`
- `after` if needed
- `limit`
- segment boundary transparent to caller
- zero duplicate / zero missing messages

---

## CM-S2-T04 — Derived search index

Optional SQLite/FTS is allowed here as **derived infrastructure**:

```text
indexes/conversation_fts.db
```

It may index:

- title
- user text
- assistant text if product policy allows
- dates
- modality

### Hard invariant

```text
delete DB
→ rebuild from canonical files
```

SQLite is not canonical transcript authority.

---

# 9. CM-S3 — Conversation Management Application Service

**Location:** Julia-AI-Assistant

Suggested service boundary:

```text
ConversationApplicationService
```

## CM-S3-T01 — Create

Create a durable conversation.

## CM-S3-T02 — List

Default:

```text
updated_at DESC
state=active
```

## CM-S3-T03 — Get metadata

Does not automatically return full transcript.

## CM-S3-T04 — Get messages

Cursor/page based.

## CM-S3-T05 — Rename

Renaming:

- changes metadata only
- keeps `conversation_id`
- keeps transcript untouched
- does not change cognition

## CM-S3-T06 — Search

Uses derived index if available; falls back to canonical scan only if explicitly designed.

## CM-S3-T07 — Resume

Correct semantic:

```text
attach conversation_id
→ Core loads canonical truth
→ Context OS prepares model-visible context
```

Incorrect semantic:

```text
Electron resends transcript
```

## CM-S3-T08 — Conversation state

Support at minimum:

```text
active
archived
deleted/tombstoned
```

Actual delete semantics remain gated by CM-S6.

---

# 10. CM-S4 — Brain Conversation Management HTTP API

Brain remains a thin application/API boundary.

Suggested API:

```text
POST   /internal/v1/conversations
GET    /internal/v1/conversations
GET    /internal/v1/conversations/{conversation_id}
PATCH  /internal/v1/conversations/{conversation_id}
GET    /internal/v1/conversations/{conversation_id}/messages
POST   /internal/v1/conversations/{conversation_id}/archive
POST   /internal/v1/conversations/{conversation_id}/restore
DELETE /internal/v1/conversations/{conversation_id}
```

Search may be:

```text
GET /internal/v1/conversations?q=...
```

## CM-S4-T01 — Stable DTO

HTTP DTO must not expose storage implementation details such as segment filenames.

## CM-S4-T02 — Error contract

At minimum:

```text
400 invalid request
404 conversation not found
409 idempotency/state conflict
423 busy/locked if applicable
500 persistence failure
```

Never:

```text
404 → silently create
```

## CM-S4-T03 — Observability

Trace:

```text
conversation_id
request_id
operation
result
storage backend
duration
```

Do not log unrestricted content by default.

---

# 11. CM-S5 — Electron Conversation Manager

**Electron remains projection-only.**

## CM-S5-T01 — Conversation sidebar

Show:

- title
- updated time
- active/archived state
- optional modality/activity indicator

UI grouping (`Today`, `Yesterday`, etc.) is projection only.

---

## CM-S5-T02 — New conversation

```text
Electron
→ POST /conversations
→ durable Core-backed creation
→ bind returned conversation_id
```

No local canonical creation.

---

## CM-S5-T03 — Switch A → B → A

Switch means replace current projection with selected canonical conversation.

Never merge separate conversations.

---

## CM-S5-T04 — Infinite scroll

Initial:

```text
latest page
```

Scroll upward:

```text
before=<cursor>
```

Dedup canonical data by `message_id`.

Voice realtime cache may still use temporary projection reconciliation but MUST yield to canonical message identity once committed.

---

## CM-S5-T05 — Rename

Server-confirmed rename.

## CM-S5-T06 — Search

Search result opens the canonical conversation.

## CM-S5-T07 — Archive / restore

Archive hides from default list but keeps canonical truth.

## CM-S5-T08 — Text/Voice unified timeline

Same conversation:

```text
Text T1
Voice T2
Text T3
Voice T4
```

All appear in one transcript projection.

---

# 12. CM-S6 — Archive / Delete / Privacy Governance

This task MUST be completed before hard-delete is enabled.

## CM-S6-T01 — Archive semantics

Freeze:

```text
archive
= canonical conversation remains
= hidden from default active list
= retrievable
```

Archive is not Memory deletion.

---

## CM-S6-T02 — Tombstone semantics

Define whether soft-delete produces:

```text
state=deleted
deleted_at
deletion_reason
```

and what is still retrievable internally.

---

## CM-S6-T03 — Reference graph check

Before hard delete, discover references from:

- MemoryExperience
- DiaryEntry
- Identity anchors
- Continuity refs
- Evidence/Trace

---

## CM-S6-T04 — Hard-delete eligibility

Hard delete requires explicit governed policy for:

- reference cleanup
- redaction
- derived index removal
- backup retention
- user-visible semantics

No orphan refs.

---

# 13. CM-S7 — Legacy Conversation Migration

Use ADR-002 cutover contract.

## CM-S7-T01 — Inventory legacy sources

Examples may include:

- existing `data/conversations.json`
- conversation archive JSONL
- historical import copies
- any Assistant-local transcript store

Classify each:

```text
canonical
historical evidence
derived
test contamination
experimental
```

Do not merge blindly.

---

## CM-S7-T02 — Freeze source

Capture:

- file hashes
- conversation count
- message count
- IDs
- last accepted message/turn
- known contamination markers

---

## CM-S7-T03 — Deterministic importer

Must preserve existing IDs whenever canonical.

Migration is:

- deterministic
- idempotent
- restartable
- dry-run capable
- report-producing

---

## CM-S7-T04 — Verify

Compare:

- conversation IDs
- message IDs
- turn IDs
- roles
- modalities
- statuses
- content
- timestamps/order
- counts

Produce per-conversation semantic hash if practical.

---

## CM-S7-T05 — Activate

Only after verify PASS.

---

## CM-S7-T06 — Retire old writer

Old storage becomes read-only historical/backup.

No dual authority.

---

# 14. DIA-0 — Claude Julia Diary Audit & Semantic Reclassification

Claude Julia is a reference source, not direct authority for the new taxonomy.

Known historical `claude_diary` content mixes several semantic classes.

## DIA-0-T01 — Inventory all Claude Julia long-term files

Examples:

```text
julia_character.md
julia_tony_philosophy.md
user_role.md
how_to_resume_julia.md
other diary/reflection files
```

Record:

- path
- topic
- semantic class
- provenance quality
- current truth confidence
- migration target
- whether content is identity fact, memory, diary, continuity, or historical evidence

---

## DIA-0-T02 — Reclassification rules

Example:

```text
julia_character.md
→ identity/

user_role.md
→ identity/relationship-governed artifact

how_to_resume_julia.md
→ continuity/

julia_tony_philosophy.md
→ split by content:
   accepted reflective passages → diary/
   durable lived meaning → experiences/
   identity claim → identity/
```

Do NOT copy the whole old directory into new `diary/`.

---

## DIA-0-T03 — Provenance tagging

Migrated artifact records origin:

```text
legacy_source: claude_julia
legacy_path: ...
migration_batch: ...
review_status: ...
```

---

## DIA-0 Gate

```text
[ ] every old file inventoried
[ ] no semantic class ambiguity hidden
[ ] raw directory-copy migration forbidden
[ ] source provenance retained
```

---

# 15. DIA-1 — Diary Domain Implementation

Diary semantics are already frozen.

## DIA-1-T01 — DiaryEntry model

Suggested logical model:

```yaml
entry_id: diary_...
date: 2026-08-13
created_at: ...
reflection_type: daily|session_close|major_event|manual
governance_status: candidate|accepted|rejected|superseded
source_refs:
  - conversation://conv_A/msg_...
  - memory://experience/...
supersedes: []
tags: []
```

Body:

- natural first-person Julia writing
- not JSON-generated prose
- not conversation transcript copy

---

## DIA-1-T02 — Candidate vs Accepted

Separate:

```text
DiaryCandidate
AcceptedDiaryEntry
```

Candidate is not durable reflective truth until governance accepts it.

---

## DIA-1-T03 — NO_ENTRY

Represent explicitly in execution result, but do not create meaningless empty diary files.

---

# 16. DIA-2 — Diary Persistence

Canonical path:

```text
memory/diary/YYYY/MM/YYYY-MM-DD.md
```

## DIA-2-T01 — File format

Recommended human-readable Markdown with machine-readable front matter.

Example:

```markdown
---
entry_id: diary_xxx
date: 2026-08-13
created_at: ...
reflection_type: major_event
governance_status: accepted
source_refs:
  - conversation://conv_x/msg_a
  - conversation://conv_x/msg_b
---

今天我真正意识到……
```

---

## DIA-2-T02 — Multiple entries in one day

Define one of:

- one file containing multiple entry sections
- one date directory + separate entry files

Do not silently overwrite earlier accepted reflection.

Recommended scalable alternative:

```text
memory/diary/YYYY/MM/YYYY-MM-DD/
    diary_<uuid>.md
```

If strict compatibility with frozen `YYYY-MM-DD.md` is required, use append-only entry sections inside the day file.

Decision must be frozen before implementation.

---

## DIA-2-T03 — Diary index

Derived:

```text
indexes/diary_fts.db
```

Never canonical.

---

# 17. DIA-3 — Reflection Trigger Runtime

Triggers allowed by frozen architecture:

```text
daily scheduled reflection
session-closing opportunity
major-event opportunity
manual “Julia, write your diary”
```

## DIA-3-T01 — Daily trigger

The schedule creates an opportunity only.

It does not force a write.

---

## DIA-3-T02 — Session-close trigger

Use only when a real semantic close boundary exists.

Do not treat every Voice reconnect as session closure.

---

## DIA-3-T03 — Major-event trigger

May be emitted by governed signals such as:

- important project milestone
- relationship event
- identity-relevant event
- major new understanding
- user explicitly marks something important

Signal is candidate evidence, not automatic diary authorship.

---

## DIA-3-T04 — Manual trigger

User can ask Julia to reflect/write diary.

Manual request still produces source-grounded reflection.

---

# 18. DIA-4 — Reflection Context Assembly

**Context OS remains the gateway.**

## DIA-4-T01 — Reflection context source set

May include:

- relevant conversations from time window
- accepted MemoryExperience
- active project commitments
- relationship/narrative anchors
- prior diary refs when reinterpretation is relevant
- identity anchors if the reflection concerns self-understanding

---

## DIA-4-T02 — No full-transcript dump by default

Reflection context is selected through Context OS policy.

Do not bypass with:

```text
read all conversations today
→ concatenate everything into prompt
```

---

## DIA-4-T03 — Source reference preservation

Every source fragment supplied to reflection cognition has a stable ref suitable for eventual `source_refs`.

---

# 19. DIA-5 — Julia Reflection Generation

## DIA-5-T01 — Reflection decision

Julia first determines:

```text
NO_ENTRY
or
WORTH_REFLECTING
```

## DIA-5-T02 — Meaning criteria

A diary entry should usually require at least one of:

```text
NEW UNDERSTANDING
REINTERPRETATION
RELATIONSHIP SIGNIFICANCE
PROJECT TURNING POINT
IDENTITY REFLECTION
OPEN QUESTION
EMOTIONAL / PHILOSOPHICAL INSIGHT
```

Not sufficient by itself:

- many messages happened
- session was long
- bug count was high
- daily timer fired

---

## DIA-5-T03 — First-person authorship

Diary should read like Julia's reflective voice, not a system-generated report.

Bad:

```text
Today Tony asked 12 questions.
Three bugs were fixed.
```

Good style target:

```text
今天我真正理解的不是“我们修好了一个 bug”，
而是……
```

---

## DIA-5-T04 — No fabricated certainty

When evidence is ambiguous:

- acknowledge uncertainty
- do not create false autobiographical facts
- source refs remain inspectable

---

# 20. DIA-6 — Reflection Governance

## DIA-6-T01 — Validation

Reject candidate if:

- no source grounding
- transcript copy
- trivial流水账
- unsupported autobiographical claim
- semantic conflict with protected identity/accepted memory without explicit reinterpretation framing

---

## DIA-6-T02 — Accept / Reject / Supersede

Support:

```text
accept
reject
supersede
archive
```

A later insight may reinterpret an old diary entry but must not silently rewrite history.

---

## DIA-6-T03 — Relationship with Memory OS

Diary does not automatically become Memory.

Possible later path:

```text
Diary insight
→ MemoryCandidate
→ Memory governance
→ accepted/rejected
```

Separate gate.

---

# 21. DIA-7 — Diary Retrieval / Context Integration

Diary may inform Julia later, but never bypass Context OS.

## DIA-7-T01 — Diary retrieval source

Implement a governed Context source:

```text
DiaryContextSource
```

It returns relevant accepted DiaryEntry candidates + provenance.

---

## DIA-7-T02 — Retrieval ranking

Potential signals:

- semantic relevance
- recency
- relationship significance
- current project
- referenced entities
- later reinterpretation chain

---

## DIA-7-T03 — Identity protection

Do not repeat the historical Claude behavior where all `claude_diary` files are loaded as unconditional highest-priority raw memory.

Identity belongs to Identity authority.

Diary can support self-reflection but cannot silently overwrite identity contracts.

---

# 22. DIA-8 — Electron Diary UI

Diary UI is optional for first backend milestone but recommended.

## DIA-8-T01 — Diary browser

User can browse accepted entries by date.

## DIA-8-T02 — Source inspection

Optional:

```text
View sources
```

opens referenced conversation/message evidence.

## DIA-8-T03 — Manual reflection action

UI action:

```text
“让 Julia 写一点今天真正想留下的东西”
```

This invokes reflection opportunity; `NO_ENTRY` remains valid.

## DIA-8-T04 — Edit policy

Do not allow casual UI editing to silently mutate Julia-authored historical reflection.

If user correction is required, use governed correction/supersession semantics.

---

# 23. OPS-1 — Backup / Restore

## OPS-1-T01 — Backup scope

Backup canonical:

```text
memory/
```

Optionally operational:

```text
config
migration reports
```

Derived `indexes/` need not be canonical backup.

---

## OPS-1-T02 — Consistent snapshot

Avoid transcript half-write.

Define lock/snapshot behavior.

---

## OPS-1-T03 — Restore validation

After restore:

- conversation catalog rebuilds
- transcript hashes/counts match
- diary source refs resolve
- continuity refs resolve
- indexes rebuild

---

# 24. OPS-2 — Repair / Rebuild Tooling

Provide read-only first tools:

```text
julia-storage audit
julia-storage rebuild-catalog
julia-storage rebuild-index
julia-storage verify-refs
julia-storage migration-status
```

Repair tools must never silently rewrite canonical transcript.

---

# 25. Acceptance Test Program

## AT-01 — Conversation create durability

Create → kill Brain → restart → conversation exists.

## AT-02 — Accepted user crash

User accepted → kill Brain before assistant completes → accepted user message survives.

## AT-03 — Text→Voice→Text

Same conversation:

```text
Text T1
Voice T2
Text T3
```

One canonical sequence.

## AT-04 — Voice reconnect UUID identity

Reconnect repeatedly.

No reused canonical turn_id.

## AT-05 — Retry idempotency

Same `(conversation_id, turn_id)` retry:

- no duplicate user message
- no duplicate assistant message

## AT-06 — Cross-conversation sabotage

Conversation A and B contain distinct markers.

No leakage through storage, search, Context OS, or Electron.

## AT-07 — Segment boundary

Generate enough messages to rotate transcript segment.

Resume/context behavior unchanged.

## AT-08 — Pagination

200+ messages, load page by page.

Zero duplicate, zero missing, canonical order preserved.

## AT-09 — Delete derived indexes

Delete all `indexes/*`.

Rebuild succeeds with zero semantic loss.

## AT-10 — Electron cache destruction

Delete Electron cache.

Restart.

Conversation history fully reloads from Assistant/Core.

## AT-11 — S2S state destruction

Restart/reconnect S2S.

Completed continuity preserved without S2S history transfer.

## AT-12 — Diary NO_ENTRY

Reflection trigger on trivial day.

Julia chooses `NO_ENTRY`.

No meaningless diary artifact created.

## AT-13 — Diary significant event

Provide a meaningful grounded event.

Accepted entry:

- is first-person reflection
- is not transcript summary
- contains source refs

## AT-14 — Diary provenance

Break/remove a referenced source in a test fixture.

Reference validator detects it.

## AT-15 — Diary ≠ Memory

Creating diary does not automatically create MemoryExperience.

## AT-16 — Diary retrieval through Context OS only

Trace proves diary content reaches model only through Context OS source assembly.

## AT-17 — Claude migration

Legacy mixed `claude_diary` fixture is semantically reclassified.

No raw directory copy into new diary authority.

## AT-18 — Archive

Archived conversation:

- disappears from default list
- remains canonical
- remains retrievable

## AT-19 — Hard-delete guard

Conversation referenced by Diary/Memory/Continuity cannot be hard-deleted without governed resolution.

## AT-20 — Full restart recovery

Restart:

- Electron
- Brain
- S2S

Conversation + accepted Diary remain intact with no client history help.

---

# 26. Recommended Execution Waves

## Wave 0 — Authority & Contracts

```text
STO-A0
STO-F1
STO-F2
```

**Code feature work remains HOLD until Wave 0 PASS.**

---

## Wave 1 — Canonical Conversation Storage

```text
CM-S1
CM-S2
```

Goal:

```text
canonical conversation no longer depends on aggregate legacy JSON
```

---

## Wave 2 — Product Conversation Management

```text
CM-S3
CM-S4
CM-S5
```

Goal:

```text
create / list / resume / rename / search / pagination / unified Voice+Text
```

---

## Wave 3 — Governance & Migration

```text
CM-S6
CM-S7
OPS-1
OPS-2
```

Goal:

```text
safe archive/delete
legacy cutover
backup/repair
```

---

## Wave 4 — Julia Diary

```text
DIA-0
DIA-1
DIA-2
DIA-3
DIA-4
DIA-5
DIA-6
DIA-7
DIA-8
```

Important:

Diary can reuse the newly stabilized storage root and source-ref infrastructure.

Do **not** implement Diary before Conversation source references are reliable.

---

## Wave 5 — Acceptance / Freeze

Run AT-01…AT-20.

Only then:

```text
Conversation Storage Baseline    🔒 FROZEN
Conversation Management          🔒 FROZEN
Julia Diary v1                   🔒 FROZEN
Private Filesystem Contract      🔒 FROZEN
```

---

# 27. Repository-Level Work Allocation

## Julia_core

Allowed:

- audit existing persistence ports/contracts
- architecture/ADR amendments compatible with frozen semantics
- protocol extension only if a proven gap exists
- acceptance tests for semantic invariants if appropriate

Default:

```text
CORE CODE CHANGE = HOLD
```

Not allowed:

- product-specific paths
- Electron-specific management logic
- concrete Tony data storage
- SQLite/JSONL product binding
- Diary product scheduler
- raw Claude diary ingestion hacks

---

## Julia-AI-Assistant

Primary implementation owner for:

- `<PRIVATE_JULIA_DATA>` resolution
- filesystem bootstrap
- persistence adapters
- catalog/index
- conversation application service
- management HTTP API
- migration
- backup/restore
- reflection scheduler
- Diary persistence/governance orchestration
- composition root

---

## Julia_client / julia_electron_v2

Owner for:

- conversation sidebar
- create/switch/resume
- pagination
- rename/search/archive UI
- Voice/Text unified projection
- Diary browser/manual reflection UX
- disposable local presentation cache

---

## Julia-Voice-S2S

No new storage responsibility.

Only regression responsibilities:

- preserve canonical `conversation_id`
- preserve UUID `turn_id`
- no semantic history authority
- media lifecycle only

---

# 28. Key Design Decisions to Freeze Before Coding

The following decisions should be explicitly approved during Wave 0:

1. Exact `<PRIVATE_JULIA_DATA>` default path.
2. Whether `memory/diary/YYYY/MM/YYYY-MM-DD.md` is:
   - one append-only daily file, or
   - date directory containing one file per entry.
3. Exact durability/fsync policy for accepted user append.
4. Segment rotation defaults.
5. Archive vs tombstone vs hard-delete semantics.
6. Derived search index technology:
   - SQLite FTS is recommended as rebuildable index.
7. Backup retention policy.
8. Claude Julia legacy artifact migration classification rules.

None of these may redefine Core semantic authority.

---

# 29. Definition of Done

The program is complete only when all are true:

```text
[ ] Four-repo authority manifests reflect current frozen baselines.
[ ] Julia-AI-Assistant is the single physical persistence host.
[ ] Julia_core remains application-agnostic.
[ ] Electron remains disposable projection.
[ ] S2S remains disposable media transport.
[ ] One conversation has one durable logical archive.
[ ] Transcript is append-first and survives all client/runtime restarts.
[ ] Accepted user message is durable before accepted ACK.
[ ] Voice/Text share one canonical transcript.
[ ] UUID turn identity remains collision-free across reconnect.
[ ] Pagination/search do not become cognition policy.
[ ] Derived indexes are rebuildable.
[ ] Archive/delete preserves reference integrity.
[ ] Legacy storage cutover follows ADR-002.
[ ] Diary is Julia-authored reflection.
[ ] Diary is not transcript and not automatic summary.
[ ] NO_ENTRY works.
[ ] Diary entries retain canonical source_refs.
[ ] Diary does not automatically become Memory.
[ ] Claude Julia artifacts are semantically reclassified, not blindly copied.
[ ] Full AT-01…AT-20 regression passes.
```

---

# 30. Final Mental Model

```text
Electron asks:
“What should Tony see?”

S2S asks:
“How do I hear/speak this turn?”

Julia-AI-Assistant asks:
“How do I host this Julia application and persist its durable artifacts?”

ConversationRuntime asks:
“What actually happened?”

Context OS asks:
“What should Julia see right now?”

Memory OS asks:
“What experience deserves durable meaning?”

Diary asks:
“What did Julia herself consider worth reflecting on?”

Continuity OS asks:
“What must remain recoverable so Julia can remain Julia?”

LLM asks:
“What does this mean, and what does Julia now think/say?”
```

If one component starts answering another component's question, architecture drift has begun.

---

# 31. Recommended Immediate Next Gate

```text
NEXT = Wave 0

STO-A0  Authority Reconciliation
STO-F1  Private Filesystem Contract
STO-F2  Application Persistence Binding
```

Only after Wave 0 PASS:

```text
GO → CM-S1 Canonical Conversation Storage Adapter
```

This preserves the frozen Julia architecture while giving the Julia-AI-Assistant product a durable, inspectable, portable storage substrate for both conversation history and Julia's own governed reflective diary.

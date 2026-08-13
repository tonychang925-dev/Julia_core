# STO-D0 Decision Register v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: STO-D0 — Implementation Decision Freeze (Wave 0)
BASE COMMIT: `8e871ba` (julia_core `cm-r0-fix` / clean `sto-d0` worktree)
GOVERNANCE: This register is authored in an isolated worktree (`sto-d0`) from base `8e871ba`. The dirty julia_core working tree (experimental WIP) is NOT mixed into this freeze. No experimental code is carried into Storage authority.

---

## 0. Entry Gate — Brain Reconciliation Regression Evidence

Before any STO-D0 decision is frozen, the Brain source recovery (STO-A0 closeout) regression evidence is recorded verbatim:

```text
BR-R1~R6 semantic gates        ✅ PASS
pytest                         44 PASS / 1 ENV-BLOCKED
test_openai_sse_format         ⚠️ external DeepSeek 402
merge regression evidence      ✅ no regression established
45/45 PASS                     ❌ 不宣称
```

Notes:

- `test_openai_sse_format` is NOT mocked; it performs a live `api.deepseek.com` call and received `402 Payment Required` (insufficient account balance). This is an environment gate, not a merge regression.
- The wording "45/45 PASS" is deliberately NOT claimed. The honest claim is "44 PASS / 1 ENV-BLOCKED; no regression established".
- Evidence SHA for the merge: `197ada9` (reconciliation merge) + `44cea89` (closeout SHA stamp on `phase5/rmd-3g-observability`).

---

## 1. STO-D0-01 — PRIVATE_JULIA_DATA_ROOT

**Decision: ACCEPT**

### 1.1 What this decision answers

This decision does NOT answer "who owns Conversation". That is already frozen:

```text
Semantic authority   = Julia Core
Physical data host   = Julia-AI-Assistant
```

D0-01 answers only:

```text
On a given machine, where does Julia-AI-Assistant locate the one
durable private-data root for this Julia instance?
```

The root must be simultaneously:

```text
repo-independent
process-independent
model-independent
provider-independent
restart-safe
human-backup-friendly
cross-platform-mappable
explicitly overrideable
private by default
```

### 1.2 Canonical config key

```text
JULIA_PRIVATE_DATA_ROOT
```

Resolution precedence (frozen):

```text
explicit JULIA_PRIVATE_DATA_ROOT
        ↓ if absent
OS-specific product default
        ↓
canonical absolute path
        ↓
validate
        ↓
bootstrap filesystem
```

`JULIA_PRIVATE_DATA_ROOT` is the deployment/config contract.
The OS default is only the default implementation.
Core never needs to know whether a migration occurred (e.g. `JULIA_PRIVATE_DATA_ROOT=/Volumes/JuliaPrivate/JuliaAI`).

### 1.3 Cross-platform defaults (frozen)

```text
macOS    ~/Library/Application Support/JuliaAI/
Linux    ${XDG_DATA_HOME:-~/.local/share}/julia-ai/
Windows  %LOCALAPPDATA%\JuliaAI\
```

`JULIA_PRIVATE_DATA_ROOT` always wins.

`JuliaAI` denotes the Julia product data domain — NOT the Julia_core repo, NOT Electron, NOT the Brain source directory.

Application code MUST NOT hardcode `Path.home() / "Library/Application Support/JuliaAI"`. There is exactly one resolver:

```text
PrivateDataRootResolver
```

shared across the product.

### 1.4 Root internal layout (frozen)

```text
<JULIA_PRIVATE_DATA_ROOT>/
├── memory/                 ← semantic durable domain
│   ├── conversations/      ← Conversation persistence
│   ├── diary/              ← Diary persistence
│   ├── experiences/        ← Memory OS persistence
│   ├── identity/           ← Identity persistence
│   └── continuity/         ← Continuity persistence
├── indexes/                ← derived / rebuildable
├── runtime/                ← ephemeral / reconstructable
├── migrations/
├── backups/
└── logs/
```

`PRIVATE_DATA_ROOT` is a physical container, NOT Memory OS.

### 1.5 Root validator (frozen contract)

Assistant startup MUST verify:

```text
resolved path is absolute/canonical
path is writable
directory can be created if absent
not temporary storage
not inside Julia_core Git checkout
not inside Julia-AI-Assistant Git checkout
not inside Electron checkout
filesystem layout version compatible
```

Secure defaults:

```text
new root on Unix/macOS : 0700
private semantic files : 0600
directories            : 0700
```

### 1.6 Fail-closed rule (critical)

If the user explicitly sets `JULIA_PRIVATE_DATA_ROOT=/some/path` but the path is:

```text
permission denied
layout incompatible
unsafe/corrupt
```

the runtime MUST NOT silently fall back to another directory.

The forbidden failure mode:

```text
Tony believes Julia reads A
    ↓
A cannot be opened
    ↓
Brain silently creates B
    ↓
Julia appears to "forget"
```

Frozen rule:

```text
explicit root invalid → STARTUP BLOCKED
(never → fallback default)
```

### 1.7 No canonical DB at root top-level

Even when SQLite FTS is adopted (D0-06), the canonical index lives at:

```text
indexes/conversation_fts.db
```

NOT:

```text
<JULIA_PRIVATE_DATA_ROOT>/julia.db
```

Rationale: `julia.db` at root would invite the semantic conflation "julia.db = all of Julia's truth", which the frozen architecture explicitly rejects.

### 1.8 Startup attestation

Assistant startup records (infrastructure identity only, never private content):

```text
JULIA_STORAGE_IDENTITY
root=<resolved JULIA_PRIVATE_DATA_ROOT>
layout=julia-private-data-v1
conversation=segmented-jsonl
diary=markdown
index=derived
```

### 1.9 Freeze table

| Item | Verdict |
|---|---|
| Canonical config key `JULIA_PRIVATE_DATA_ROOT` | ✅ |
| macOS default `~/Library/Application Support/JuliaAI/` | ✅ |
| Linux default `$XDG_DATA_HOME/julia-ai` | ✅ |
| Windows default `%LOCALAPPDATA%\JuliaAI` | ✅ |
| Git repo as data root | ❌ FORBIDDEN |
| `~/.julia` as data root | ❌ FORBIDDEN (conflicts with Julia language depot) |
| Explicit invalid override → fail closed | ✅ |
| Silent fallback → forbidden | ✅ |
| Single resolver owned by Julia-AI-Assistant | ✅ |
| Julia_core path knowledge | ❌ NONE |
| Electron/S2S direct filesystem access | ❌ FORBIDDEN |

### 1.10 Invariants

**STO-D0-I01**

```text
All application-owned durable Julia data MUST resolve beneath one
explicit JULIA_PRIVATE_DATA_ROOT.

The root is physically hosted by Julia-AI-Assistant and carries
no semantic authority by virtue of its filesystem location.
```

**STO-D0-I02**

```text
If an explicitly configured JULIA_PRIVATE_DATA_ROOT cannot be safely
opened, validated, or initialized, startup MUST fail closed.

The runtime MUST NOT silently create or fall back to a second
private-data root.
```

---

## 2. STO-D0-03 — Accepted-User Durability / flush / fsync

**Decision: ACCEPT**

This decision defines the exact meaning of one word: `CORE_ACCEPTED`.

### 2.1 Precise definition of CORE_ACCEPTED

```text
CORE_ACCEPTED
≠ received by HTTP
≠ parsed
≠ put into RuntimeTurn
≠ Python file.flush()
≠ queued to background writer

CORE_ACCEPTED
=
canonical ConversationMessage
has crossed the durable-append boundary
for this product's local canonical store.
```

Lifecycle (frozen):

```text
current user input
        ↓
validate conversation_id
validate turn_id / idempotency
        ↓
serialize canonical ConversationMessage
        ↓
append FULL record to transcript segment
        ↓
flush userspace buffer
        ↓
fsync canonical segment FD
        ↓
DURABLE ACCEPTANCE BOUNDARY
        ↓
Runtime may report CORE_ACCEPTED
        ↓
Context OS / cognition
```

ACK MUST NOT occur before fsync.

### 2.2 Strategy selection

| Strategy | Approach | Verdict |
|---|---|---|
| A | write + flush → ACK | ❌ not strong enough |
| B | per accepted user turn: write + flush + fsync → ACK | ✅ recommended |
| C | background batch/group fsync, ACK early | ❌ violates frozen contract |

- **A fails**: `flush()` only moves Python userspace buffer → kernel; it is not a defined durability boundary. `f.flush(); return CORE_ACCEPTED` is forbidden — it invites false confidence.
- **C fails**: batch fsync with early ACK re-introduces fake success / silent acceptance (same class as CM-FAILCLOSED). A group-commit optimization may later be studied, but only as: `T1 T2 T3 → one fsync → THEN release all ACKs`. Never ACK before flush-to-disk.

### 2.3 Strict per-accept fsync

```text
Accepted user message → one durability commit → fsync → CORE_ACCEPTED
```

Unit of durability = **logical accepted user turn**, NOT HTTP request, NOT Voice packet, NOT ASR partial.

```text
ASR partial × N → FINAL ASR → canonical user message → fsync → CORE_ACCEPTED
```

ASR partials never enter this durability contract.

### 2.4 Durability primitive (cross-platform)

Freeze the contract as a **primitive**, not a specific API:

```text
Durability Primitive
= platform implementation must perform an OS-supported
  synchronous persistence barrier equivalent to fsync
  for the canonical file.
```

Python/macOS v1:

```text
file.flush()
os.fsync(file.fileno())
```

macOS `F_FULLFSYNC` is NOT mandatory for v1. Rationale: the current frozen promise is "survive Core/Brain process death" — plain `fsync` already gives a clear, cross-platform, testable boundary. `F_FULLFSYNC` may be evaluated later as platform hardening / enhanced durability mode, not now (avoids binding cross-platform contract to macOS-specific implementation).

### 2.5 Guarantee scope (do not overclaim)

D0-03 guarantees:

```text
- survive normal process termination
- survive Brain/Core crash
- survive kill -9 after CORE_ACCEPTED
- request synchronous filesystem durability via fsync
```

D0-03 does NOT claim:

```text
- cloud backup completed
- remote replication completed
- protection against catastrophic disk loss
- protection against hardware violating durability guarantees
```

```text
CORE_ACCEPTED = locally durable canonical truth ≠ backed up forever
```

Backup is OPS-1 (D0-07); it must not be mixed into ACK.

### 2.6 Index / catalog are NOT on the ACK critical path

Once the canonical message is fsync'd, the following MUST NOT block `CORE_ACCEPTED`:

```text
meta.json message_count
index.json
SQLite FTS
analytics
Memory extraction
Diary
Compact
```

Correct order:

```text
canonical user append → fsync → CORE_ACCEPTED → metadata/index update → cognition / async post-turn work
```

Rationale: `ConversationMessage` is truth; `message_count`, catalog cache, FTS DB must all be rebuildable. A broken search index must never make Julia "afraid to accept" a user message.

### 2.7 meta.json field classes

Two classes, distinct durability contracts:

```text
Identity/state metadata:
  conversation_id, created_at, state, title, schema_version
  → own durable mutation contract

Derived counters:
  last_message_id, last_turn_id, message_count, segment_count
  → rebuildable from transcript
```

User ACK does not depend on derived counters being synchronously durable. On crash where `transcript` has `msg_101` but `meta.message_count` still shows `100`, recovery scans/reconciles to `101` — it does NOT conclude `msg_101` does not exist.

### 2.8 New segment / new conversation creation durability

Normal append to existing `transcript-000001.jsonl`:

```text
write → flush → fsync(file)
```

New segment creation (`transcript-000002.jsonl`) adds directory-entry persistence:

```text
create file → append message → flush + fsync(file) → fsync(parent directory) where supported/required → ACK
```

New conversation (`conv_<cid>/` + `meta.json` + initial transcript) must complete its creation durability contract BEFORE telling Electron "conversation established". Same family, different operation.

### 2.9 Partial-tail recovery (companion invariant)

Physical record framing:

```text
a complete newline-terminated record is the only valid physical record
```

Writer MUST:

```text
serialize whole record + "\n" → complete write loop → flush → fsync
```

Recovery on partial trailing bytes:

```text
preserve complete records
quarantine/truncate incomplete final tail
emit repair evidence
```

Never guess-fill JSON. Never let a partial tail make the whole conversation unreadable.

### 2.10 fsync failure → fail closed + idempotent reconciliation

On `write`+`flush` OK but `fsync` raises (e.g. EIO):

```text
CORE_ACCEPTED          ❌
continue cognition     ❌
fake success           ❌

STORAGE_DURABILITY_FAILURE → fail closed
```

Real-world subtlety: the write may have actually reached the file even though fsync returned failure. Therefore retry MUST NOT blindly write a second record. Retry MUST:

```text
same conversation_id + same turn_id → inspect canonical store
  → complete, content-identical user message found → idempotent recovery (same logical turn)
  → same turn_id + different content → CONFLICT → FAIL CLOSED (never overwrite)
```

### 2.11 Crash-ACK window (durability × idempotency joint)

```text
append → fsync SUCCESS → process dies → ACK never reached client
```

Client retries same `conversation_id` + `turn_id` + content. Server MUST:

```text
find existing durable user record → verify same logical turn → zero duplicate → resume/idempotent response
```

Durability and idempotency MUST be tested jointly — they are one feature, not two. (Direct lesson from VOICE-C1.)

### 2.12 Assistant message (symmetric principle)

`ASSISTANT_COMPLETED` MUST NOT be announced before the final canonical assistant message is durable:

```text
LLM streaming → ephemeral render (UI/TTS) → generation final boundary
→ canonical assistant message → flush + fsync → CRT assistant COMPLETED
```

Streaming chunks do NOT require per-chunk fsync (would destroy Voice latency + disk IO).

```text
USER      → one fsync per accepted semantic input
ASSISTANT → one fsync per final canonical completion
```

Interrupted-assistant emitted-boundary persistence follows the existing interruption contract; D0-03 does not redesign it.

### 2.13 Performance stance

Per-turn fsync is slower than buffered append, but for the Julia interaction shape (user turn → network → LLM cognition → TTS) a local fsync is not the dominant latency term. The cost of optimizing this wrong is "Tony said it, Julia forgot it". v1 does not trade durability for tens-of-ms optimizations; optimize only after a real measured bottleneck.

### 2.14 Invariants

**STO-D0-I03 — ACK Durability**

```text
CORE_ACCEPTED MUST NOT be emitted until the complete canonical user
ConversationMessage has crossed the configured local durability barrier.

For the v1 filesystem backend, this requires successful
write + flush + fsync of the canonical transcript segment.
```

**STO-D0-I04 — No Async Acceptance**

```text
Canonical accepted-user persistence MUST NOT be delegated to an
asynchronous writer after CORE_ACCEPTED.

Background persistence may be used only for derived or
reconstructable artifacts.
```

**STO-D0-I05 — Durability Failure Is Fail-Closed**

```text
If the canonical durability barrier fails or has indeterminate
status, the runtime MUST NOT report CORE_ACCEPTED.

Retry/recovery MUST reconcile by canonical turn identity and
MUST NOT blindly append a duplicate turn.
```

**STO-D0-I06 — Canonical First, Derived Later**

```text
Catalog, index, FTS, Compact, Memory, Diary, analytics, and other
derived/post-turn work MUST NOT be prerequisites for CORE_ACCEPTED
once the canonical user message itself is durable.
```

**STO-D0-I07 — Crash-Retry Idempotency**

```text
A crash after durable append but before ACK delivery MUST be
recoverable by retrying the same logical turn identity without
creating a duplicate canonical message.
```

### 2.15 Acceptance tests (AT-DUR-01…09)

```text
AT-DUR-01  write → fsync → ACK → kill -9 → message survives           ✅
AT-DUR-02  write → fsync → kill before ACK → retry → one message      ✅
AT-DUR-03  inject fsync failure → no CORE_ACCEPTED                    ✅
AT-DUR-04  fsync failure + record exists → reconcile by turn_id → no dup ✅
AT-DUR-05  same turn_id + different content → conflict / fail closed  ✅
AT-DUR-06  corrupt partial JSONL tail → earlier records survive + evidence ✅
AT-DUR-07  catalog/index write fails after fsync → message remains truth ✅
AT-DUR-08  new segment → crash after ACK → segment + message discoverable ✅
AT-DUR-09  short-write completion / fail-closed (full spec below)     ✅
```

**AT-DUR-09 — Short-Write Completion / Fail-Closed**

```text
Given: canonical ConversationMessage serialized into one immutable byte
       buffer including the terminating newline.

When:  the underlying write operation performs one or more short writes.

Then:  the writer MUST continue until the entire immutable buffer has been
       durably written, OR fail closed before CORE_ACCEPTED.

MUST NOT:
  - ACK a partially written canonical record
  - treat one successful partial write as record completion
  - silently truncate the record
  - append a second logical copy during retry
  - rely on one write() syscall being complete

If completion becomes indeterminate: close/reopen/reconcile per D0-03 I05/I07.

Expected: zero partial accepted record, zero duplicate canonical message,
          zero false CORE_ACCEPTED.
```

### 2.16 Freeze table

| Item | Verdict |
|---|---|
| Canonical backend v1 = append-oriented filesystem / JSONL | ✅ |
| Accepted-user durability = write + flush + fsync before ACK | ✅ |
| Per accepted semantic turn fsync | ✅ |
| Async persistence after ACK | ❌ FORBIDDEN |
| Catalog/index before ACK | ❌ NOT REQUIRED |
| Memory/Diary/Compact before ACK | ❌ FORBIDDEN |
| fsync failure → fail closed | ✅ |
| Crash after fsync / before ACK → idempotent retry | ✅ |
| Partial trailing JSONL → deterministic recovery | ✅ |
| Remote backup before ACK | ❌ NOT REQUIRED |
| macOS F_FULLFSYNC mandatory v1 | ❌ NO |

### 2.17 Resolver / implementation notes (CM-S1, not decision changes)

1. **fsync EIO poisons the FD**: after `fsync` returns EIO, the file descriptor (and possibly page-cache state for that inode) is unreliable. Reconciliation MUST close+reopen and re-read the canonical store — never trust the in-memory buffer or re-fsync the same poisoned FD. (Sharpens I05.)
2. **Immutable-buffer write_all under writer lock**: serialize the whole record (+ `"\n"`) into an immutable byte buffer, then `write_all` it to completion under the exclusive per-conversation writer lock, handling short writes; failure to complete is fail-closed. Correctness MUST NOT rest on "one `write()` syscall writes the whole record" — `write()` can short-write even on regular files. `O_APPEND` is retained for atomic end-of-file positioning, but it is a mechanism, not the framing contract.

---

## 3. STO-D0-04 — Transcript Segment Rotation

**Decision: ACCEPT**

### 3.1 Decision goal

Segments are physical sharding only:

```text
Conversation
    ├── transcript-000001.jsonl
    ├── transcript-000002.jsonl
    ├── transcript-000003.jsonl
    └── ...
```

Invariant boundaries that MUST remain independent of segment boundaries:

```text
Conversation identity ≠ Segment identity
Turn identity         ≠ Segment identity
Context boundary      ≠ Segment boundary
Session boundary      ≠ Segment boundary
Voice/Text switch     ≠ Segment boundary
```

Rotation is fully invisible to Julia.

### 3.2 Default rotation policy (frozen)

```text
ROTATE BEFORE NEXT APPEND
when projected active segment exceeds either:
  32 MiB (MAX_BYTES = 33,554,432)
  OR
  10,000 canonical messages (MAX_MESSAGES)

trigger = projected_bytes > MAX_BYTES OR projected_messages > MAX_MESSAGES
```

High-end values (32 MiB / 10k) chosen because conversations are already directory-isolated — no need for many small files — while 32 MiB stays lightweight for scan/backup/repair/migration.

These are **operational defaults**, NOT cognition policy, NOT semantic invariant. Changing to 16 MiB later requires no migration and changes no semantics.

### 3.3 Rotate BEFORE append (predict, not react)

Wrong:

```text
segment = 31.9 MiB → append 5 MiB → 36.9 MiB → then rotate
```

Right:

```text
serialize next canonical record
        ↓
calculate projected size/count
        ↓
would exceed threshold?
   ├─ NO  → append current
   └─ YES → create next segment → append there
```

**Oversized single-record exception**: a single `ConversationMessage` is the minimum physical atom. If one serialized record is 40 MiB, it MUST NOT be split across segments. An oversized single-record segment (e.g. `transcript-000042.jsonl = 40 MiB`) is valid; the next record rotates normally.

### 3.4 Rotation inside the canonical append critical section

No background "segment manager" may decide placement after ACK. Frozen sequence:

```text
acquire conversation writer serialization
        ↓
serialize canonical message
        ↓
determine active segment
        ↓
rotation needed?
        ↓
create/select target segment
        ↓
write complete record + "\n" (immutable-buffer write_all, see D0-03 2.17)
        ↓
flush
        ↓
fsync(target segment)
        ↓
if newly-created segment: fsync(parent directory)
        ↓
DURABLE BOUNDARY
        ↓
CORE_ACCEPTED
        ↓
release writer
```

Forbidden window:

```text
CORE_ACCEPTED → background worker decides where to put message
```

### 3.5 One conversation → one serialized physical writer (invariant)

For one `conversation_id`, `append A → rotation → append B` MUST NOT execute concurrently. Mechanism (in-process lock / file lock / single-writer repository) is not frozen; the contract is:

```text
At any time, the canonical segment set of one conversation has
exactly one valid append serialization domain.
```

Otherwise two processes could both see `segment-000001` near threshold and both create `segment-000002`, corrupting physical truth.

### 3.6 Segment numbering

```text
transcript-000001.jsonl
transcript-000002.jsonl
...
```

Frozen principles:

```text
monotonically increasing
never semantic
never exposed as conversation identity
never reused after a persisted allocation
gaps are legal
```

A crash leaving `000041` then `000043` (missing `000042`) does NOT mean corruption. Canonical message order is determined by canonical append order / message identity, never by filename continuity.

### 3.7 Derived meta is not transcript truth

```text
meta.json: segment_count = 7
crash → actually transcript-000008.jsonl already has a durable accepted message
```

Correct conclusion: segment 8 = truth; `meta.segment_count` = stale derived metadata. Recovery scans canonical segment files, validates, rebuilds derived metadata — it does NOT delete segment 8 to satisfy `meta.json`.

```text
segment_count / last_segment / last_message_id / message_count
```
are never canonical transcript truth.

### 3.8 New segment durability (D0-03 ∩ D0-04)

Existing segment:

```text
append record → flush → fsync(file)
```

New segment:

```text
create transcript-000NNN.jsonl → append full record → flush → fsync(file) → fsync(conversation directory) → ACK
```

If file fsync PASSES but directory fsync FAILS → `CORE_ACCEPTED ❌`, entering D0-I05 reconciliation (close / reopen / reconcile canonical store). Never guess "probably succeeded".

### 3.9 Crash recovery — three states

```text
A. normal complete segments   → restore directly
B. newly created empty segment → no canonical message; quarantine/remove under repair policy; number is not semantic truth
C. newest segment partial tail → complete records preserved; partial final record invalid; quarantine/truncate via governed repair + evidence; never guess-fill JSON
```

### 3.10 Rotation MUST NOT be triggered by

```text
Electron restart
Brain restart
Voice reconnect
Text ↔ Voice switch
Provider switch
Context Compact
Session close
daily boundary
model change
```

These are different authority domains. Segment answers only: "is this physical file unfit to grow?" Allowed triggers:

```text
size threshold
message-count threshold
explicit storage maintenance operation (if later supported; must not change semantic order)
```

### 3.11 Read / pagination fully segment-transparent

Callers see only:

```text
get_messages(conversation_id, before=cursor, limit=50)
```

Never "read segment 17". Cursor may internally encode physical position but MUST be opaque. Electron / Context OS / S2S are all segment-unaware; the repository alone handles cross-segment pagination (`000003 → 000002`).

### 3.12 Attachments outside segment body

Future `attachments/` binaries are NOT inlined into JSONL. `ConversationMessage` stores attachment ref + metadata + semantic relationship. The segment byte threshold counts transcript JSONL only.

```text
Conversation truth ≠ binary object storage
```

### 3.13 Threshold configuration semantics

Product may later configure `segment_max_bytes` / `segment_max_messages`, but:

```text
explicit invalid configuration → startup/config validation FAIL
silent fallback to arbitrary values → FORBIDDEN

threshold change:
  does NOT rewrite old segments
  does NOT trigger migration
  applies to future append/rotation only
```

### 3.14 Invariants

**STO-D0-I08 — Segment Transparency**

```text
Transcript segmentation is a physical persistence concern only.

Segment boundaries MUST NOT alter conversation identity, turn
identity, canonical ordering, resume semantics, or model-visible
context policy.
```

**STO-D0-I09 — Atomic Record Boundary**

```text
A canonical ConversationMessage MUST reside wholly within exactly
one transcript segment.

A message MUST NOT be split across segment boundaries.
An oversized single-record segment is valid.
```

**STO-D0-I10 — Serialized Rotation**

```text
Segment selection, rotation, canonical append, and durability commit
MUST execute within one serialized per-conversation writer domain.

Concurrent physical writers MUST NOT independently rotate or append
the same conversation.
```

**STO-D0-I11 — Rotation Before ACK**

```text
If rotation is required for an accepted user message, creation and
durability of the target segment are part of that message's D0-03
durability boundary.

CORE_ACCEPTED MUST NOT precede successful durability of the new
segment and its required filesystem directory entry.
```

**STO-D0-I12 — Reconstructable Segment Metadata**

```text
Segment counters, active-segment metadata, and catalog hints are
derived state.

Canonical transcript files MUST be discoverable and reconstructable
without trusting those derived counters.
```

### 3.15 Acceptance tests (AT-ROT-01…12)

```text
AT-ROT-01  append below threshold → same segment                          ✅
AT-ROT-02  next record crosses byte threshold → record wholly in next     ✅
AT-ROT-03  10,001st projected message → new segment                       ✅
AT-ROT-04  single record > MAX_BYTES → one oversized segment, no split    ✅
AT-ROT-05  crash after new segment create, before record durability → no fake accepted ✅
AT-ROT-06  crash after new-segment fsync, before ACK → retry → one message ✅
AT-ROT-07  stale meta segment_count=N but durable N+1 → N+1 wins, meta rebuilt ✅
AT-ROT-08  gap in segment numbers → conversation still readable           ✅
AT-ROT-09  200+ messages spanning segments → pagination zero dup/missing  ✅
AT-ROT-10  Text→Voice switch at rotation boundary → one conversation, correct order ✅
AT-ROT-11  two concurrent appends → repository serializes → deterministic order ✅
AT-ROT-12  partial final record in newest segment → prior records preserved, tail detected ✅
```

### 3.16 Freeze table

| Item | Verdict |
|---|---|
| Default max size 32 MiB | ✅ |
| Default max messages 10,000 | ✅ |
| Trigger = projected size OR projected count | ✅ |
| Rotate before append | ✅ |
| Split one canonical message across segments | ❌ FORBIDDEN |
| Oversized single-record segment | ✅ VALID |
| Segment boundary semantic meaning | ❌ NONE |
| Mode/session/provider-based rotation | ❌ FORBIDDEN |
| Per-conversation serialized writer | ✅ REQUIRED |
| New segment: file fsync + directory fsync before ACK | ✅ |
| Derived meta as transcript authority | ❌ FORBIDDEN |
| Gaps in physical sequence | ✅ VALID |
| Threshold change rewrites old segments | ❌ NO |

---

## 4. STO-D0-05 — Archive / Tombstone / Hard Delete

**Decision: ACCEPT**

Three distinct operations, never one fuzzy `delete()`:

```text
ARCHIVE     = 收起来 (reduce visibility, keep truth)
TOMBSTONE   = 逻辑删除 / stop using
HARD DELETE = 物理清除 (only after reference governance)
```

### 4.1 Archive — visibility change only, not history change

```text
ACTIVE → archive → ARCHIVED → restore → ACTIVE
```

After archive:

```text
canonical transcript    retained (bytes unchanged)
conversation_id         retained
message_id / turn_id    retained
source_refs             still valid
default list            hidden
explicit retrieval      allowed
Context OS              still usable per governance policy
Memory / Diary refs     unchanged
hard storage bytes      unchanged
```

**Archive ≠ Forget.** Canonical append is allowed only in `state=ACTIVE`. Continuing an archived conversation requires explicit restore → ACTIVE → append; never a background auto-restore.

### 4.2 Tombstone — logical delete boundary

```text
ACTIVE ──┐
         ├── delete → TOMBSTONED
ARCHIVED ┘
```

After tombstone, transcript bytes remain temporarily, BUT:

```text
normal UI access        ❌
search content exposure ❌
Context OS retrieval    ❌
new append              ❌
normal resume           ❌
```

Tombstone first cuts usage + visibility, not the bytes. This creates a safe window to resolve Memory/Diary/Identity/Continuity refs, attachments, indexes, backup lifecycle — instead of `rm -rf` then discovering a dangling continuity ref.

### 4.3 Restore before purge

```text
ACTIVE ──┐
         ├── delete → TOMBSTONED → restore (before purge) → ACTIVE
ARCHIVED ┘

TOMBSTONED → governed hard delete → PURGED
```

`PURGED` is NOT a normal Conversation state — at that point the canonical conversation no longer exists. Do NOT write `{"state": "deleted", "messages": [...]}` and call it hard-deleted.

### 4.4 Tombstone ACK strength

`DELETE_ACCEPTED / TOMBSTONED`, once returned to Electron, guarantees:

```text
durable tombstone state established
AND normal conversation access disabled
AND Context OS cannot retrieve its transcript
AND normal search cannot expose its content
AND new canonical append is rejected
```

Stale-index trap: a conversation must NOT be `TOMBSTONED` while `Search "Tony"` still returns its deleted content. Derived-index cleanup MAY follow asynchronously, but every read path MUST apply canonical state filtering:

```text
stale index ≠ permission to expose deleted content
```

### 4.5 Reference Resolution Gate (core of D0-05)

Reference classification (frozen):

| Reference holder | Type | On hard delete |
|---|---|---|
| Compact | derived | delete / rebuild |
| Search index | derived | delete |
| cache/runtime | ephemeral | delete |
| MemoryExperience | durable semantic | MUST govern |
| DiaryEntry | durable semantic | MUST govern |
| Identity anchor | protected semantic | MUST govern |
| ContinuityCheckpoint | protected reference | MUST govern |
| Trace / evidence | operational | retention/redaction policy |
| Attachment refs | durable object refs | ownership/reference check |

`hard_delete(conv_A)` first runs `ReferenceGraph.inspect(conv_A)`, yielding `DERIVED_REFS / DURABLE_SEMANTIC_REFS / PROTECTED_REFS / OBJECT_REFS`.

### 4.6 "Referenced" ≠ "undeletable forever"

Wrong design:

```text
Diary references conversation → conversation can never be deleted
```
(this would render user deletion meaningless)

Correct:

```text
reference exists → HARD DELETE BLOCKED TEMPORARILY → resolve reference → then purge
```

A Diary `source_refs: [conversation://conv_A/msg_42]` need not be deleted when `conv_A` is purged; it becomes `source_state: PURGED`. Two distinct true facts:

```text
Julia did write this diary (historical existence = true)
Julia can no longer re-verify its original Conversation evidence (= true)
```

### 4.7 Reference State, not dangling pointer

A source reference logically supports:

```text
RESOLVED
ARCHIVED    → source still available
TOMBSTONED  → source exists physically, unavailable to cognition/access
PURGED      → original content gone; provenance ref preserved only as deletion state
```

Forbidden: `conversation://conv_A/msg_42 → FileNotFoundError → nobody knows what happened` (silent dangling reference).

### 4.8 Authority separation — no cascade delete

Conversation deletion MUST NOT auto-infer deletion of Memory / Diary / Identity / Continuity:

```text
Conversation = what happened
Memory       = durable experience/meaning
Diary        = Julia's reflection
```

Each dependent artifact is governed by its own authority:

```text
MemoryExperience    → Memory governance
DiaryEntry          → Diary/reflection governance
Identity anchor     → Identity governance
Continuity ref      → Continuity governance
```

Conversation Repository cannot cascade-delete these. This is the direct expression of "physical persistence host ≠ semantic authority".

### 4.9 Dependent semantic artifact revocation

When a Memory's only evidence (`conv_A/msg_42`) is purged:

```text
Memory OS re-judges:
  other independent source?
    ├─ YES → keep
    └─ NO → protected identity fact? experiential meaning? unsupported assertion?
              → keep / redact / supersede / remove
```

The specific outcome belongs to Memory Governance, not D0-05. D0-05 requires only: hard delete MUST trigger dependency resolution, never leave unreviewed semantic dependencies.

### 4.10 Hard Delete flow (with durability)

```text
Request hard delete
        ↓
Conversation → TOMBSTONED
        ↓
Freeze new appends
        ↓
Build Reference Resolution Plan
        ↓
Resolve durable/protected refs
        ↓
Verify zero unresolved blockers
        ↓
Purge canonical transcript
        ↓
Purge conversation-owned attachments
        ↓
Purge derived index/cache entries
        ↓
fsync filesystem removals / metadata
        ↓
write minimal deletion receipt
        ↓
HARD_DELETE_COMPLETE
```

Deletion itself has a durability contract: `unlink()` must not be immediately followed by `HARD_DELETE_COMPLETE` before directory metadata crosses the synchronous barrier (v1 filesystem implementation does the platform-appropriate directory durability barrier).

### 4.11 Deletion receipt (minimal, non-content)

Allowed (non-content receipt):

```text
conversation_id, deleted_at, deletion_state: purged, schema_version
opaque identity for idempotency/audit
```

Forbidden in receipt:

```text
message content, summary, embedding
title (if privacy policy classifies it as user content)
Compact / Diary copy
transcript shadow "for later recovery"
```

The receipt is not a Conversation; it says only "this ID once existed, now deleted" — giving `source_ref=PURGED` a reliable resolution target.

### 4.12 Hard Delete ≠ Backup Erasure

```text
live memory/conversations/conv_A deleted
but yesterday's backup still contains it
```

Truthful claim:

```text
LIVE_CANONICAL_PURGE = COMPLETE
```

NOT:

```text
ALL COPIES ERASED FOREVER = COMPLETE
```

D0-07 decides backup retention/purge/restore semantics. D0-05 forbids fake erasure claim (same governance family as D0-03).

### 4.13 Tombstone retention (not frozen now)

Retention duration (e.g. 30 days) is product/retention policy, decided later with D0-07 / CM-S6. D0-05 freezes only:

```text
TOMBSTONED → may be recoverable until hard purge
PURGED     → irreversible from live canonical store
```

v1 default: automatic hard purge = OFF; explicit governed hard delete required (safer).

### 4.14 Attachment rule

`attachments/foo.pdf` owned solely by the conversation → purge on hard delete. If future object storage supports cross-conversation references (`object_A → conv_1, conv_2`), deleting `conv_1` ≠ deleting `object_A` — a ref check is required. Do NOT freeze `rm -rf attachments/` as a universal semantic rule.

### 4.15 Invariants

**STO-D0-I13 — Archive Preservation**

```text
Archiving a conversation changes presentation/lifecycle state only.

It MUST NOT alter canonical transcript content, conversation
identity, message/turn identity, or durable semantic references.
```

**STO-D0-I14 — Tombstone Exclusion**

```text
After a tombstone operation is durably acknowledged, the conversation
MUST be excluded from normal listing, search content exposure, Context
OS retrieval, resume, and canonical append paths.

Derived-index cleanup MAY follow asynchronously, but stale derived
state MUST NOT re-expose tombstoned content.
```

**STO-D0-I15 — No Unresolved Hard Delete**

```text
Canonical conversation content MUST NOT be physically purged while
durable semantic or protected references remain unresolved.

Reference resolution is a prerequisite to hard-delete completion.
```

**STO-D0-I16 — No Semantic Cascade by Storage**

```text
Conversation storage MUST NOT independently delete or rewrite Memory,
Diary, Identity, or Continuity artifacts.

Each semantic authority governs its own dependent artifact.
```

**STO-D0-I17 — No Silent Dangling Provenance**

```text
Deletion of a canonical source MUST NOT silently convert a previously
valid source reference into an unexplained dangling reference.

The reference lifecycle MUST explicitly represent deletion /
unavailability state.
```

**STO-D0-I18 — No False Erasure Claim**

```text
Hard deletion from the live canonical store MUST NOT be reported as
global erasure while retained backups or other governed copies may
still exist.

Backup-erasure semantics are governed separately.
```

### 4.16 Acceptance tests (AT-DEL-01…14)

```text
AT-DEL-01  archive active → transcript byte-identical, IDs unchanged       ✅
AT-DEL-02  restore archived → same conversation_id, no transcript rewrite  ✅
AT-DEL-03  tombstone → default list excludes conversation                  ✅
AT-DEL-04  tombstone → Context OS cannot retrieve transcript               ✅
AT-DEL-05  stale FTS entry → search still cannot expose tombstoned content ✅
AT-DEL-06  append to tombstoned → fail closed                              ✅
AT-DEL-07  restore before hard purge → transcript + IDs unchanged          ✅
AT-DEL-08  hard delete with unresolved Diary/Memory/Continuity refs → blocked ✅
AT-DEL-09  resolve refs → hard purge eligible                              ✅
AT-DEL-10  conversation deletion → storage does NOT silently delete Memory/Diary ✅
AT-DEL-11  hard purge crash halfway → deterministic recoverable state, no ghost active ✅
AT-DEL-12  purged source ref → resolves as PURGED, never dangling          ✅
AT-DEL-13  live purge complete but backup exists → no "global erasure" claim ✅
AT-DEL-14  shared attachment referenced elsewhere → deleting conversation does not destroy it ✅
```

### 4.17 Freeze matrix

| Behavior | Archive | Tombstone | Hard Delete |
|---|---|---|---|
| transcript retained | ✅ | ✅ temporarily | ❌ |
| default UI hidden | ✅ | ✅ | ✅ |
| search content | 可治理检索 | ❌ | ❌ |
| Context OS retrieval | ✅ 可治理 | ❌ | ❌ |
| new append | restore first | ❌ | impossible |
| reversible | ✅ | ✅ before purge | ❌ |
| reference graph resolution | not needed | prepare phase | must |
| Memory/Diary auto-delete | ❌ | ❌ | ❌ |
| physical purge | ❌ | ❌ | ✅ |
| backup erasure implied | ❌ | ❌ | ❌ |

### 4.18 Resolver / implementation notes (CM-S6, not decision changes)

1. **Tombstone state transition is a durable mutation**: the tombstone flag write follows D0-03's barrier (`write + flush + fsync`) before `TOMBSTONED` ACK — "durable tombstone state" means the same durability boundary as accepted-user append, not an in-memory flag flip.
2. **Deletion receipt doubles as idempotency anchor**: a retried hard-delete for the same `conversation_id` resolves against the existing receipt (already `PURGED`) instead of re-purging — extending I07's crash-retry idempotency to the delete path.
3. **Restore-from-tombstone state memory**: restore should remember whether the conversation was `ACTIVE` or `ARCHIVED` before tombstone (or default to `ACTIVE`); CM-S6 must pin this so restore does not silently change lifecycle state.

---

## 5. STO-D0-06 — Derived Conversation Search Index (SQLite FTS5)

**Decision: ACCEPT**

```text
Canonical truth    memory/conversations/* JSONL/files
Derived search     indexes/conversation_fts.db
Engine v1          SQLite FTS5                        ✅
Canonical authority SQLite                           ❌ NEVER
Delete SQLite DB → rebuild from canonical files      ✅ REQUIRED
```

SQLite's role is narrow: "which canonical messages might match this query?" It cannot answer "is this message still valid?", "is this conversation deleted?", "should Julia see it?", "is this Memory?".

### 5.1 Two-stage pipeline (core of D0-06)

Wrong (leaks tombstoned content via stale rows):

```text
FTS query → SQLite snippet(...) → return to Electron
```

Correct:

```text
query
  ↓
SQLite FTS → candidate refs only (conversation_id, message_id, rank/match metadata)
  ↓
CANONICAL VISIBILITY GATE → read canonical lifecycle state
  │  ├─ ACTIVE       → eligible
  │  ├─ ARCHIVED     → depends on search mode
  │  ├─ TOMBSTONED   → DROP
  │  └─ PURGED       → DROP
  ↓
canonical message hydration
  ↓
generate safe snippet
  ↓
return projection
```

```text
FTS finds candidates; canonical storage decides whether a candidate may still appear.
```

### 5.2 Snippet MUST NOT leak before the gate

Even if the stale tombstoned row is eventually dropped, a snippet must never be generated and passed up before the gate passes.

```text
FTS stage        → IDs / rank / opaque match info only
canonical gate PASS → hydrate canonical content → THEN construct user-visible snippet
```

```text
stale index content ≠ display authority
```

### 5.3 Search semantics by lifecycle

```text
Default search             ACTIVE only
Explicit include_archived=true → ACTIVE + ARCHIVED
TOMBSTONED                 ❌ normal search exposure (always)
PURGED                     ❌ result (always)
```

Consistent with D0-05: Archive = reduce visibility; Tombstone = stop normal use; Hard Delete = remove physical truth.

### 5.4 Index eligibility (frozen)

Allowed (v1):

```text
conversation title
canonical user message text
canonical assistant message text
canonical date/time fields for filtering
conversation_id, message_id, role
```

Forbidden in FTS:

```text
ASR partial                              ❌
unfinished streaming chunk               ❌
provider hidden state                    ❌
internal runtime prompt                  ❌
hidden reasoning / CoT                   ❌
raw tool/debug traces                    ❌
Context OS temporary assembly            ❌
Compact as transcript substitute         ❌
Memory/Diary raw content                 ❌
```

Voice FINAL ASR, once it becomes a canonical user ConversationMessage → eligible. Assistant emitted boundary, once canonical per existing contract → eligible per its canonical status.

### 5.5 Conversation Search ≠ Diary Search

Technically both may live in the same SQLite; architecturally they are separate logical contracts:

```text
Conversation Search ≠ Diary Search ≠ Memory Retrieval ≠ Context Retrieval
```

D0-06 freezes only Conversation Search Index. Diary search is deferred to D0-02.

### 5.6 Index update is NOT on the CORE_ACCEPTED critical path

```text
canonical append → flush → fsync → CORE_ACCEPTED → index update
```

Allowed state (SEARCH INDEX LAG, not data loss):

```text
Tony just spoke → conversation shows it ✅ → Julia canonical-accepted it ✅ → immediate search misses it ⚠️ allowed short lag
```

Never put `SQLite commit` before `CORE_ACCEPTED`.

### 5.7 Consistency = eventual, but asymmetric

```text
Conversation truth  = strongly durable (D0-03)
Search projection   = eventually consistent
```

Asymmetry (critical):

```text
new message index lag → may be temporarily unfindable (false negative) ✅ acceptable
tombstoned stale row  → MUST NOT be temporarily visible (false positive) ❌ forbidden
```

### 5.8 Index failure isolation

`SQLITE_CORRUPT / SQLITE_BUSY / schema incompatible / missing file` MUST NOT impair:

```text
create conversation, append, resume, canonical read, Context OS canonical source
```

v1 search on index failure:

```text
SEARCH_UNAVAILABLE / REBUILD_REQUIRED
```

No silent fallback to full canonical grep (that would silently introduce a second ranking/visibility/performance/pagination semantics — same fail-closed family). A canonical-scan fallback, if ever needed, is a separately frozen equivalent contract.

### 5.9 Rebuild is first-class, not a disaster tool

`indexes/*` is disposable by design. Provide:

```text
rebuild_conversation_search_index()
```

Scan source `memory/conversations/*`:

```text
ACTIVE      → index
ARCHIVED    → index, lifecycle-filtered later
TOMBSTONED  → do not index
PURGED      → do not index
```

Regenerate from canonical `message_id` / `conversation_id` / canonical readable text.

### 5.10 Rebuild = Build → Verify → Swap

Never `rm conversation_fts.db → rebuild in place → crash halfway`.

```text
conversation_fts.rebuild.tmp
        ↓
scan canonical files → build → SQLite integrity check → schema/version check → rebuild evidence
        ↓
atomic replace current derived DB
```

Crash halfway → old usable index remains OR search unavailable; canonical data unaffected. Temp file cleaned up later. Derived artifact's filesystem durability is NOT upgraded to the Conversation ACK contract.

### 5.11 Index schema versioning

```text
index_schema_version, source_layout_version, built_at, build_id
(optionally last_rebuild_at, indexer_version)
```

`last_indexed_message_id`, if present, is only an optimization watermark — never evidence that "messages after it do not exist". Canonical transcript always wins.

### 5.12 Tokenizer not frozen now (implementation parameter)

Julia's dialogue is largely Chinese; freezing `unicode61` now may be suboptimal. Options (trigram / bigram / Chinese tokenizer) trade off short words, space, substring, mixed CN/EN, dependencies. Tokenizer change only needs an index rebuild — it never changes canonical data.

```text
Engine family  SQLite FTS5                        ✅ frozen
Tokenizer      implementation/rebuild parameter   ⚙️
Requirement    Chinese + English acceptance suite MUST PASS ✅
```

### 5.13 Chinese search gate

CM-S2 must test (this is Julia's real usage environment):

```text
中文: 日记 / 语音 / 持久化 / Julia / Tony / ConversationRuntime / VOICE-C1 / 删除引用
中英混合: "Julia 日记" / "Voice 语音" / "D0-03 持久化"
```

Final tokenizer/normalization must have evidence. Two-character Chinese words must not be unusable due to tokenizer choice.

### 5.14 Rank / snippet / score are projection, not semantics

BM25 (or future ranking) may reorder across rebuilds:

```text
rebuild → A rank1/B rank2 → B rank1/A rank2   (valid)
```

`search rank`, `snippet`, `match score` are projection only — never stored as Memory importance, Context authority, or Conversation ordering.

### 5.15 Search cursor is not durable identity

Search rank may vary across rebuilds, so a search cursor is at most an ephemeral query-projection cursor — never a durable `source_ref`. True source refs remain `conversation_id` + `message_id`.

### 5.16 Context OS must NOT co-opt UI FTS into cognition authority

Wrong:

```text
Context OS token budget low → SELECT * FROM conversation_fts → feed model
```

Forbidden. Correct: Context OS uses its governed retrieval contract → canonical refs → source eligibility/governance → model-visible context. D0-06 grants the UI search index no cognition authority.

### 5.17 Tombstone cleanup async but priority

```text
TOMBSTONED durable → normal access immediately blocked → enqueue FTS delete
```

If SQLite delete fails, the stale row remains internally, but the search pipeline's canonical gate drops it — user never sees it. Correctness never depends on SQLite cleanup "must succeed immediately".

### 5.18 Hard Delete and FTS

After hard purge, canonical transcript is gone but deletion receipt remains. A stale FTS row resolves as `candidate → canonical resolver → PURGED receipt → DROP`.

```text
stale FTS ≠ zombie conversation
```

Cleanup/rebuild removes it later.

### 5.19 Index permissions

Derived ≠ public. The FTS DB still contains copies of user conversation content:

```text
indexes/conversation_fts.db → 0600; directory → 0700
```

Never place in `/tmp` or unprotected location just because it is rebuildable.

### 5.20 Backup stance

```text
Conversation FTS index is NOT required for canonical backup (delete index → rebuild).
```

Whether D0-07 later chooses to back up indexes for restore speed is separate; indexes are never backup truth.

### 5.21 Invariants

**STO-D0-I19 — Derived Search Only**

```text
Conversation search indexes are derived and reconstructable artifacts.

They MUST NOT become canonical Conversation, lifecycle, Memory, Diary,
Continuity, or cognition authority.
```

**STO-D0-I20 — Rebuildability**

```text
Deletion or corruption of all Conversation search indexes MUST be
recoverable from canonical Conversation persistence without semantic loss.
```

**STO-D0-I21 — Canonical Visibility Gate**

```text
Search-index matches MUST pass canonical lifecycle and visibility
adjudication before any user-visible content, snippet, or result is returned.

Stale derived state MUST NOT expose tombstoned or purged Conversation content.
```

**STO-D0-I22 — Canonical Before Index**

```text
Search indexing MUST NOT be a prerequisite for CORE_ACCEPTED or canonical
assistant completion.

Index updates occur only after the corresponding canonical artifact is durable.
```

**STO-D0-I23 — Search Failure Isolation**

```text
Search-index unavailability, corruption, lag, or rebuild failure MUST NOT
impair canonical Conversation create, append, read, resume, or durability
semantics.
```

**STO-D0-I24 — Canonical Content Eligibility**

```text
Only eligible durable canonical Conversation content may be indexed.

Ephemeral ASR partials, transient streaming chunks, hidden provider/runtime
state, temporary Context artifacts, and non-canonical history MUST NOT enter
Conversation FTS.
```

**STO-D0-I25 — No Cognition Authority**

```text
The Conversation UI search index MUST NOT directly determine model-visible context.

Any future reuse for cognition requires a separately governed Context OS
retrieval contract grounded in canonical refs.
```

**STO-D0-I26 — Derived Ranking**

```text
Search rank, snippets, match scores, tokenization, and search pagination are
projection semantics only.

They MUST NOT alter canonical ordering, durable identity, or source-reference
semantics.
```

### 5.22 Acceptance tests (AT-FTS-01…16)

```text
AT-FTS-01  delete fts db → rebuild → canonical conversations/messages unchanged ✅
AT-FTS-02  canonical fsync+ACK succeeds, index update fails → conversation valid, search may lag, no rollback ✅
AT-FTS-03  index corruption → search unavailable/rebuild required → create/read/resume still work ✅
AT-FTS-04  stale FTS row for TOMBSTONED → zero user-visible result, zero snippet leakage ✅
AT-FTS-05  stale FTS row for PURGED → deletion receipt/canonical state drops candidate ✅
AT-FTS-06  ARCHIVED: default search excluded; include_archived=true eligible ✅
AT-FTS-07  rebuild sees ACTIVE+ARCHIVED+TOMBSTONED → index ACTIVE/ARCHIVED, skip TOMBSTONED ✅
AT-FTS-08  crash halfway through rebuild → canonical unaffected, partial temp never authority ✅
AT-FTS-09  schema version mismatch → rebuild required, no canonical migration/rewrite ✅
AT-FTS-10  ASR partial / unfinished stream → never indexed ✅
AT-FTS-11  hidden runtime/provider/debug content → never indexed ✅
AT-FTS-12  conversation spans many segments → search resolves via canonical id, segment invisible ✅
AT-FTS-13  rebuild changes ranking → valid; IDs/source refs unchanged ✅
AT-FTS-14  Chinese + English corpus → required query acceptance suite passes ✅
AT-FTS-15  FTS candidate → missing/non-resolvable canonical message → drop + drift evidence ✅
AT-FTS-16  Context OS path inspection → UI search index does not become implicit cognition source ✅
```

### 5.23 Freeze matrix

| Item | D0-06 decision |
|---|---|
| v1 engine | SQLite FTS5 |
| location | indexes/conversation_fts.db |
| canonical | ❌ |
| rebuildable | ✅ mandatory |
| index before ACK | ❌ |
| consistency | eventual |
| stale tombstone exposure | ❌ absolutely forbidden |
| default search | ACTIVE |
| explicit archived search | ✅ |
| tombstoned/purged search | ❌ |
| snippet before canonical gate | ❌ |
| hidden/runtime data indexing | ❌ |
| FTS ranking semantic | ❌ |
| Context OS direct authority | ❌ |
| tokenizer frozen | ❌ implementation parameter |
| Chinese/English acceptance | ✅ required |
| canonical backup dependency | ❌ |

### 5.24 Resolver / implementation notes (CM-S2, not decision changes)

1. **The visibility gate itself must read strongly-durable canonical lifecycle state**, not a derived/cached lifecycle projection. Building the gate on a cache would move the staleness problem one layer up and re-open the tombstone-exposure hole through a different path. (Sharpens I21.)
2. **Rebuild atomic swap vs concurrent incremental writer**: a live incremental indexer holding the old DB file handle open will keep writing to the now-unlinked inode after the Build→Verify→Swap rename, silently losing entries until the next rebuild. CM-S2 must coordinate swap with the incremental writer (pause-and-resume, or post-swap re-apply). (Sharpens I20.)

---

## 6. STO-D0-07 — Backup / Restore / Retention

**Decision: ACCEPT**

One-sentence goal:

```text
Backup 可以保存 Julia 的 canonical truth，但永远不能成为第二套 truth；
Restore 可以恢复历史，但绝不能把已经删除的历史"复活"。
```

Closes D0-05 I18 (Hard Delete ≠ Backup Erasure) and D0-06's derived-index rule.

### 6.1 Backup identity

```text
Live canonical store = authority
Backup = point-in-time recovery copy of canonical authority
       ≠ active authority
       ≠ alternate writable history
       ≠ cognition source
```

Forbidden: canonical store fails to open → Brain secretly reads `backups/` transcript → keeps running.

Correct: canonical store invalid → STARTUP/STORAGE BLOCKED → explicit restore procedure → VERIFY → ACTIVATE restored canonical store. (Fail-closed family.)

### 6.2 Backup scope

```text
memory/                  ✅ MUST (conversations, diary, experiences, identity, continuity)
migrations/              ✅ selected durable state / reports
layout metadata          ✅
deletion/erasure ledger  ✅ MUST
indexes/                 ❌ NOT REQUIRED (rebuild per D0-06)
runtime/                 ❌
logs/                    ❌
backups/                 ❌ NEVER recursively
```

### 6.3 Consistent cut

Each backup must represent one coherent application-level durable cut. Never:

```text
copy conv_A → Tony speaks → copy Memory → Julia writes Diary → copy conv_B
```

Frozen logical flow:

```text
BACKUP_REQUEST → acquire consistency barrier → finish/block semantic durable writers
→ verify all accepted writes crossed durability boundary → capture cut watermark
→ snapshot/copy canonical durable set → write manifest → verify integrity → release barrier
```

Mechanism (plain copy / APFS clone / fs snapshot / reflink) is not frozen; the requirement is a coherent cut.

### 6.4 No long-term blocking

Separate:

```text
CONSISTENCY CAPTURE        (needs the barrier)
compression/packaging/off-device transfer  (does not need to hold the writer)
```

```text
short consistency barrier → immutable staging snapshot → release Julia
→ hash/compress/encrypt/copy asynchronously
```

`BACKUP_COMPLETE` only after final verification — never just because staging was created.

### 6.5 Backup manifest

```text
backup_id, created_at, backup_cut_id, layout_version
source: application, source_commit, core_contract_version
contents: memory=included, indexes=excluded, runtime=excluded, logs=excluded
deletion_ledger_watermark
integrity: algorithm=sha256, manifest_status=verified
```

Per-canonical-file checksums, so Restore relies on verification evidence, not "the directory looks right".

### 6.6 Old backup MUST NOT resurrect deleted conversation (P0)

```text
Aug 1  backup contains conv_A
Aug 5  Tony HARD DELETE conv_A
Aug 13  machine dies → restore Aug 1 → conv_A returns  ← P0 semantic bug
```

This would let Backup bypass D0-05's Hard Delete. Solution: **deletion / erasure ledger**.

### 6.7 Deletion ledger (restore protection, not transcript)

Each hard delete leaves a minimal non-content receipt:

```text
conversation_id, purged_at, purge_id, state=PURGED
```

Never: message content, summary, embedding, transcript shadow.

Aggregated into the deletion/erasure ledger (or governed metadata region). Meaning: "this canonical identity was explicitly purged; old backups MUST NOT reactivate it."

### 6.8 Restore MUST replay erasure state

```text
select backup → stage → verify hashes/schema
→ obtain latest authoritative erasure ledger
→ apply all purge receipts newer than backup cut
→ verify no purged object resurrected
→ rebuild derived indexes → activate restored root
```

```text
old backup contains conv_A + latest ledger says conv_A PURGED
= restored canonical root MUST NOT contain conv_A
```
(strongest invariant of D0-07)

### 6.9 Ledger must survive total machine loss

The ledger cannot live only in the live root's last copy. Every subsequent backup includes the **cumulative erasure ledger**, and backup-set management keeps the latest ledger watermark:

```text
Backup B1 contains conv_A → hard delete → purge receipt P1
Backup B2 contains cumulative P1 → Backup B3 contains cumulative P1
restoring old B1 uses the newest verified erasure ledger in the available backup set
```

Backups may keep old bytes until retention expires, but must not restore them as active truth.

### 6.10 Physical backup deletion ≠ logical anti-resurrection

```text
physical bytes still in old backup
but ledger blocks restore

honest states:
  LIVE_CANONICAL_PURGE    ✅
  RESTORE_RESURRECTION    ✅ BLOCKED
  BACKUP_PHYSICAL_ERASURE ⏳ retention pending
  GLOBAL_ERASURE_COMPLETE ❌
```

This is D0-05 I18's true closure.

### 6.11 Retention policy (v1 operational default)

```text
7 daily  + 4 weekly + 12 monthly
MANUAL CHECKPOINT  → retained until explicit delete
```

Rationale: fine-grained 7-day recovery for accidental delete, 1-month weekly for project errors, 1-year monthly anchors for long-term schema/migration disaster, without unbounded private-data accumulation. Operational default, not semantic invariant; user-configurable.

### 6.12 Retention deletion fail-closed

Retention worker problems → old backups linger (RETENTION_LAG), never a system failure, never:

```text
delete canonical / delete manual checkpoint / delete wrong generation
```

Retention applies only to: verified backup artifacts, explicitly eligible generations, never live root, never MANUAL/PINNED.

### 6.13 Restore never in-place

Wrong: `rm -rf memory/ ; cp backup/memory/* memory/` (half-dead Julia on failure).

```text
RESTORE STAGING ROOT → materialize backup → verify → apply erasure ledger
→ validate references → rebuild derived indexes → full acceptance tests
→ atomic/governed activation → old root retained temporarily as rollback evidence
```

Reuses ADR-002 spirit: FREEZE → RECONCILE → VERIFY → ACTIVATE → RETIRE. Restore is an authority cutover.

### 6.14 No automatic timeline merge

Default Restore = one restored canonical state. Never auto-merge `current live + old backup` by timestamp (produces duplicate messages/turns, forked conversations, resurrected state). v1: automatic timeline merge = FORBIDDEN. Selective restore/import, if ever needed, goes through the Migration contract, not normal Restore.

### 6.15 Identity preservation

Full restore preserves exactly:

```text
conversation_id, message_id, turn_id, source_refs
Diary refs, Memory refs, Continuity refs
```

Restore MUST NOT regenerate semantic identities (would break the whole provenance graph).

### 6.16 Don't trust derived metadata after restore

Even if backup contains `meta.json` counters, after restore:

```text
verify canonical segments → reconcile meta → verify refs → rebuild FTS
```

`message_count / segment_count / last_message_id` never override actual canonical files (inherits D0-04).

### 6.17 Encryption / privacy

Backup contains Julia's complete private history:

```text
derived/copy ≠ less private
local managed backups → same private permission boundary
external/off-device backup → MUST be encrypted before leaving trusted root/device
encryption key → MUST NOT be stored plaintext inside the same archive
```

### 6.18 Same-disk backup ≠ disaster recovery

`<PRIVATE_JULIA_DATA>/backups/` may share the SSD with canonical data. It protects against accidental delete / bad migration / corruption, but NOT SSD death / machine loss.

```text
LOCAL MANAGED BACKUP ≠ OFF-DEVICE DISASTER RECOVERY
```

### 6.19 Backup complete definition

`BACKUP_COMPLETE` iff:

```text
consistent cut captured
AND required canonical artifacts present
AND manifest finalized
AND integrity verification passes
AND backup destination durability succeeds
```

Any uncertainty → `BACKUP_FAILED` (no fake success).

### 6.20 Restore complete definition

`RESTORE_COMPLETE` at least requires:

```text
backup verified
layout compatible/migrated
canonical refs valid
latest purge ledger replayed
zero forbidden resurrection
derived indexes rebuilt or explicitly unavailable
activation completed
runtime points only to restored canonical root
```

Never "files copied → RESTORE COMPLETE".

### 6.21 Backup failure isolation

Backup/sync/snapshot is NOT on the CORE_ACCEPTED critical path (inherits D0-03). `CORE_ACCEPTED` never waits on backup.

### 6.22 Invariants

**STO-D0-I27 — Backup Is Not Authority**

```text
Backup artifacts are recovery copies only.

They MUST NOT become active Conversation, Memory, Diary, Identity,
Continuity, or cognition authority without an explicit verified
Restore activation.
```

**STO-D0-I28 — Consistent Backup Cut**

```text
Every completed backup MUST correspond to a coherent durable
application-level cut.

A backup assembled from mutually inconsistent semantic write states
MUST NOT be reported as complete.
```

**STO-D0-I29 — Restore Must Not Resurrect Purged Truth**

```text
Restore MUST apply the latest authoritative purge/deletion ledger
available for the backup set before activation.

Content previously hard-purged MUST NOT be resurrected merely because
an older backup still contains its bytes.
```

**STO-D0-I30 — No In-Place Restore**

```text
Restore MUST be staged, verified, and explicitly activated.

Production canonical data MUST NOT be destructively replaced in place
before restore validation succeeds.
```

**STO-D0-I31 — Identity Preservation**

```text
Normal full restore MUST preserve canonical conversation_id, message_id,
turn_id, and durable source-reference identities.

Restore MUST NOT regenerate semantic identities.
```

**STO-D0-I32 — Derived Artifacts Are Optional**

```text
Derived indexes, caches, and runtime state MUST NOT be required for backup
completeness.

They MAY be rebuilt after restore from canonical artifacts.
```

**STO-D0-I33 — No False Global Erasure**

```text
Live-store hard purge, restore-resurrection prevention, backup physical
erasure, and global erasure are distinct states.

The system MUST NOT claim global erasure while managed backup copies
containing the deleted content may still exist.
```

**STO-D0-I34 — Backup Failure Isolation**

```text
Backup creation, packaging, transfer, retention, or verification failure
MUST NOT invalidate already-durable canonical Conversation acceptance.

Backup MUST NOT enter the CORE_ACCEPTED critical path.
```

**STO-D0-I35 — No Automatic Timeline Merge**

```text
Restore MUST NOT automatically merge a backup timeline with an
independently advanced live canonical timeline.

Any such reconciliation requires a separately governed migration/import
contract.
```

### 6.23 Acceptance tests (AT-BKP-01…18)

```text
AT-BKP-01  backup during active conversations → coherent cut, no half-state   ✅
AT-BKP-02  crash during backup capture → not COMPLETE, canonical unaffected   ✅
AT-BKP-03  corrupt backup file/checksum → restore blocked                     ✅
AT-BKP-04  delete all indexes before backup → backup still COMPLETE           ✅
AT-BKP-05  restore without indexes → canonical valid, indexes rebuild         ✅
AT-BKP-06  old backup has conv_A, later PURGED → restore → conv_A not resurrected ✅
AT-BKP-07  latest purge ledger unavailable/unverified, backup predates deletions → restore BLOCKED ✅
AT-BKP-08  live purge complete, old backup still has content → GLOBAL_ERASURE_COMPLETE stays false ✅
AT-BKP-09  retention expires backup with purged content → physical removal updates erasure state ✅
AT-BKP-10  MANUAL/PINNED backup → automatic retention never deletes          ✅
AT-BKP-11  restore crash halfway through staging → current canonical root untouched ✅
AT-BKP-12  restore verification fails → no authority activation              ✅
AT-BKP-13  restore success → conversation_id/message_id/turn_id unchanged    ✅
AT-BKP-14  restored meta counters stale → canonical files win, metadata rebuilt ✅
AT-BKP-15  backup worker fails while user append succeeds → CORE_ACCEPTED valid ✅
AT-BKP-16  external backup write succeeds but verification fails → BACKUP_COMPLETE false ✅
AT-BKP-17  attempt auto-merge of divergent live+backup histories → rejected / migration required ✅
AT-BKP-18  external backup leaves trusted device unencrypted → blocked       ✅
```

### 6.24 Retention freeze matrix

| Item | v1 |
|---|---|
| daily | 7 |
| weekly | 4 |
| monthly | 12 |
| manual checkpoint | retained until explicit delete |
| indexes in canonical backup | ❌ |
| runtime/cache/logs | ❌ |
| canonical memory/ | ✅ |
| cumulative deletion ledger | ✅ |
| backup before CORE_ACCEPTED | ❌ |
| restore in place | ❌ |
| automatic timeline merge | ❌ |
| old backup resurrection of PURGED | ❌ |
| same-disk backup called disaster recovery | ❌ |
| off-device encryption | ✅ mandatory |

Retention numbers are configurable operational defaults; invalid explicit config (`daily=-1`) → fail validation, never silent nonsense.

### 6.25 Backup state model

```text
CREATING → VERIFYING → COMPLETE        (only COMPLETE is restorable)
CREATING / VERIFYING → FAILED

Restore:
STAGING → VERIFYING → RECONCILING_DELETIONS → READY_TO_ACTIVATE → ACTIVE
```

Intermediate states are never canonical authority.

### 6.26 Four-layer erasure state (D0-07's core value)

```text
1. LIVE PURGE                 live canonical bytes removed
2. RESTORE BLOCK              deletion ledger prevents resurrection
3. BACKUP PHYSICAL EXPIRY     old copies actually disappear (retention)
4. GLOBAL ERASURE COMPLETE    only when all managed copies are accounted for
```

Neither "pretend the user didn't delete" (for backup retention) nor "live file gone → claim all copies gone forever" (false erasure). This is correct evidence discipline.

### 6.27 Resolver / implementation notes (OPS-1, not decision changes)

1. **Deletion-ledger entry is a D0-03-class durable mutation**: the purge receipt MUST be durably written (write + flush + fsync) as part of hard-delete completion. A lost or un-flushed receipt is a resurrection hole — it must never be written "best effort" after `HARD_DELETE_COMPLETE`.
2. **Cumulative ledger capture must be atomic per backup**: each backup must contain the full monotonic ledger up to its own cut watermark. A partial ledger snapshot risks missing an earlier purge receipt, which is indistinguishable from "no deletion ever happened".
3. **Ledger selection at restore must be deterministic and verified**: the "latest authoritative erasure ledger" is chosen by verified identity/watermark (hash/version), never "the newest file found on disk". AT-BKP-07 already blocks unverified ledgers; the selection rule itself must be pinned so a stale/tampered ledger cannot silently enable resurrection.

---

## 7. STO-D0-02 — Diary Physical Format

**Decision: ACCEPT**

One-sentence goal:

```text
Julia 一天可以有 0～N 次真正值得留下的反思；每一篇 accepted DiaryEntry
都独立、有身份、有来源、可持久化，但仍然组成一本人类可以直接阅读的 Julia 日记。
```

### 7.1 Physical format: single daily file

```text
<PRIVATE_JULIA_DATA>/memory/diary/YYYY/MM/YYYY-MM-DD.md
```

```text
0 entry  → file may not exist
1 entry  → one Entry Block
N entry  → multiple Entry Blocks appended
```

`ReflectionTrigger ≠ must write Diary`; `NO_ENTRY → no empty file, no placeholder summary`. Protects the frozen "Diary ≠ automatic daily summary".

### 7.2 Why not one-file-per-entry

The `2026-08-13/diary_xxx.md` alternative is technically easy but rejected as v1 canonical: it diverges from the frozen `YYYY-MM-DD.md`, turns "one Julia diary" into an artifact collection, fragments files, and reduces human readability.

```text
one day = one physical Markdown container
one reflection = one independently framed DiaryEntry
```

### 7.3 Explicit entry framing

Entry boundaries MUST NOT be guessed from body headings (body may contain headings, blockquotes, code blocks, lists, mixed CN/EN). Framed example:

```markdown
# Julia Diary — 2026-08-13

<!-- JULIA_DIARY_FILE schema=julia-diary-file-v1 -->

<!-- JULIA_DIARY_ENTRY_BEGIN diary_abc -->
---
entry_id: diary_abc
created_at: 2026-08-13T21:16:42+08:00
accepted_at: 2026-08-13T21:16:45+08:00
reflection_type: project_turning_point
source_refs:
  - conversation://conv_x/msg_102
  - memory://experience/exp_31
supersedes: []
reinterprets: []
tags: [julia, continuity, project]
---

今天我真正意识到的，并不是我们又完成了一项任务……
真正重要的是……
<!-- JULIA_DIARY_ENTRY_END diary_abc -->
```

Crash-recovery framing semantics:

```text
complete BEGIN...END = complete DiaryEntry
BEGIN without END     = incomplete tail = NOT accepted canonical Diary
```

Never guess-fill what Julia "probably meant to write".

### 7.4 Candidate never enters canonical Diary

```text
ReflectionTrigger → Context OS → Julia cognition → NO_ENTRY | DiaryCandidate
→ Reflection Governance → Accepted DiaryEntry → canonical persistence
```

`DiaryCandidate` / rejected candidate / `NO_ENTRY` are never written into `memory/diary/*`. Candidates at most live in `runtime/` and are ephemeral. Canonical Diary files hold only what Julia actually decided to keep.

### 7.5 Diary durability boundary (DIARY_DURABLE)

```text
DiaryCandidate → Governance ACCEPT → serialize immutable Entry Block
→ append/write_all → flush → fsync(day file)
→ if new file/path: directory durability barrier
→ DIARY_DURABLE
```

Only after `DIARY_DURABLE` may the system say "Julia has left this diary".

### 7.6 Diary durability fully decoupled from Conversation ACK

Forbidden:

```text
Tony message → Conversation fsync → LLM → Diary → Diary fsync → CORE_ACCEPTED
```

Correct: Conversation canonical path independently completes D0-03 → CORE_ACCEPTED; later/independently, a reflection opportunity → Diary → DIARY_DURABLE.

```text
Diary persistence failure ≠ Conversation rollback
```

Diary must never enter the Conversation authority critical path.

### 7.7 Diary fsync failure fail-closed

On `write`+`flush` OK but `fsync` EIO: no `DIARY_DURABLE`. Reuse D0-03 sharpening: close poisoned FD → reopen → scan framed canonical Diary → reconcile by `entry_id`.

```text
same entry_id + same body/hash → idempotent recovery
same entry_id + different body → CONFLICT → FAIL CLOSED
```

### 7.8 entry_id is the durable identity

Never "the 3rd entry in 2026-08-13.md". `entry_id = diary_<stable-id>`. Retry of the same logical DiaryEntry → same entry_id (never `diary_A → diary_B` producing duplicate reflections). The physical file is only a container.

### 7.9 Append-only historical reflection

Wrong: reopen 8/13 and edit old text. Correct: new DiaryEntry with `reinterprets: [diary_old]`. The old entry records what Julia genuinely understood at that time — it is itself history.

### 7.10 reinterprets vs supersedes

```text
reinterprets  "I now understand the past differently" — old entry stays true historical reflection
supersedes    "a currently-adopted judgment in the old entry has been explicitly corrected"
```

Even on supersede, old entry bytes are never overwritten in normal Diary authorship.

### 7.11 source_refs without transcript copy

Diary keeps `source_refs: [conversation://…, memory://…]` and a first-person body — but MUST NOT copy dozens/hundreds of ConversationMessages "for self-containment" (would re-create shadow transcript authority).

```text
Diary = reflection + provenance refs ≠ source-history duplication
```

### 7.12 Source deleted → Diary does not auto-vanish (inherits D0-05)

When a source conversation is PURGED, the Diary remains a valid historical artifact; its `source_refs` are NOT rewritten; the source resolver returns `RESOLVED / ARCHIVED / TOMBSTONED / PURGED`.

### 7.13 Diary ≠ Memory

Accepted DiaryEntry ≠ accepted MemoryExperience. Diary may later feed a `MemoryCandidate` via Memory Governance, but the Diary writer may never write `memory/experiences/`.

### 7.14 Diary ≠ Conversation Search

Diary does NOT enter `indexes/conversation_fts.db` (D0-06). A future `indexes/diary_fts.db` is derived/rebuildable but logically separate: Conversation Search ≠ Diary Search ≠ Memory Retrieval ≠ Context Retrieval.

### 7.15 File existence ≠ model-visible

The historical Claude-Julia anti-pattern (`load memory/claude_diary/*.md → raw prompt injection`) is forbidden. New path:

```text
memory/diary/* → DiaryRepository → DiaryContextSource → Context OS → governed selection → LLM
```

Humans can open the Markdown directly; Julia's model must not gain content merely because a file exists.

### 7.16 Stable day partition

Day partition = diary-local timezone at first durable acceptance; metadata stores offset-aware timestamps (`2026-08-13T21:16:45+08:00`). A later timezone change must NOT move `8/13.md → 8/12.md`. Specific default timezone is not hardcoded in D0-02.

### 7.17 Multiple reflections/day legal

09:00 project insight, 16:00 relationship reflection, 23:30 reinterpretation → all in `2026-08-13.md` as three entry blocks. Proves Diary ≠ once-per-day summary.

### 7.18 Same-day serialized writer

Concurrent triggers (manual + major-event) accepted simultaneously → per-day serialized writer domain. Forbidden interleaving: `BEGIN A / BEGIN B / body A / body B / END A / END B`.

### 7.19 v1 no Diary segmentation

Conversation needs segmentation (unbounded growth, D0-04); Diary is per-day. v1: one day file; one DiaryEntry wholly within its file (never split). Future scale issues → independent format upgrade.

### 7.20 Backup naturally covers Diary

D0-07 froze `memory/*` as canonical backup scope, so `memory/diary/*` is backed up. Restore preserves `entry_id / source_refs / timestamps / body / supersedes / reinterprets` exactly — never re-generates the diary via LLM.

### 7.21 Claude legacy diary NOT migrated here (HOLD)

`memory/claude_diary/*` is a legacy migration source only; `cp -R claude_diary memory/diary` is forbidden. D0-08 decides their class (Identity / Continuity / Memory / Diary / Historical evidence).

### 7.22 Invariants

**STO-D0-I36 — Daily Physical Container**

```text
Accepted Diary entries persist beneath memory/diary/YYYY/MM/YYYY-MM-DD.md.

Filename is physical partition, not entry identity.
```

**STO-D0-I37 — Accepted Entries Only**

```text
Canonical Diary contains accepted DiaryEntry only.

Candidate/rejected/NO_ENTRY are not canonical Diary.
```

**STO-D0-I38 — Durable Diary Acceptance**

```text
DIARY_DURABLE requires complete framed write + flush + fsync and required
directory durability.
```

**STO-D0-I39 — Append-Only Historical Reflection**

```text
Normal authorship appends new immutable entries.

Later reinterpretation/correction does not silently rewrite old entries.
```

**STO-D0-I40 — Stable Entry Identity**

```text
Every accepted DiaryEntry has a durable stable entry_id.

Retry reconciles by entry_id.
```

**STO-D0-I41 — Explicit Physical Framing**

```text
BEGIN/END framing must distinguish complete entries from incomplete crash tails.
```

**STO-D0-I42 — Source Grounding Without Shadow History**

```text
Diary retains source_refs but must not duplicate raw Conversation history as
alternate transcript authority.
```

**STO-D0-I43 — Context Gateway Preservation**

```text
Raw Diary files are not automatically model-visible.

Diary reaches cognition only through Context OS governance.
```

**STO-D0-I44 — Semantic Separation**

```text
Diary creation must not automatically mutate Conversation, Memory, Identity,
or Continuity authority.
```

**STO-D0-I45 — Stable Day Partition**

```text
A durable DiaryEntry remains in the day partition assigned at first acceptance;
later timezone changes do not move history.
```

### 7.23 Acceptance tests (AT-DIA-01…17)

```text
AT-DIA-01  NO_ENTRY → no canonical entry                                      ✅
AT-DIA-02  one accepted reflection → one framed entry                          ✅
AT-DIA-03  multiple same-day entries → distinct IDs, same file                 ✅
AT-DIA-04  crash mid-entry → prior entries survive                             ✅
AT-DIA-05  fsync failure → no DIARY_DURABLE                                    ✅
AT-DIA-06  ambiguous fsync + retry → no duplicate                              ✅
AT-DIA-07  same entry_id/different body → fail closed                          ✅
AT-DIA-08  concurrent reflections → no interleaved framing                     ✅
AT-DIA-09  reinterpretation → new entry; old bytes unchanged                   ✅
AT-DIA-10  supersession → new entry; old entry preserved                       ✅
AT-DIA-11  source later PURGED → explicit source lifecycle                     ✅
AT-DIA-12  Diary accepted → no automatic MemoryExperience                      ✅
AT-DIA-13  Conversation FTS → Diary not indexed there                          ✅
AT-DIA-14  raw Diary file → no direct model injection                          ✅
AT-DIA-15  new day file durable → survives crash                               ✅
AT-DIA-16  timezone later changes → old partition unchanged                    ✅
AT-DIA-17  legacy claude_diary → not auto-adopted                              ✅
```

### 7.24 Freeze matrix

| Item | Decision |
|---|---|
| Path | memory/diary/YYYY/MM/YYYY-MM-DD.md |
| One file/day | ✅ |
| Multiple entries/day | ✅ |
| Entry framing | explicit BEGIN/END |
| Stable entry_id | ✅ |
| Body | Julia first-person Markdown |
| source_refs | ✅ |
| Candidates canonical | ❌ |
| NO_ENTRY creates file | ❌ |
| Normal rewrite old entry | ❌ |
| Reinterpretation | new Entry |
| Supersession | new Entry |
| Diary fsync | ✅ |
| Diary fsync blocks Conversation ACK | ❌ |
| Same-day writers | serialized |
| Conversation FTS contains Diary | ❌ |
| Auto Memory promotion | ❌ |
| Raw file direct prompt injection | ❌ |
| Legacy Claude auto-adopt | ❌ |
| Backup | ✅ |
| Diary segmentation v1 | ❌ |

### 7.25 Resolver / implementation notes (DIA-2, not decision changes)

1. **Framing collision resistance**: the BEGIN/END parser must exact-line-match the marker including the entry's `entry_id`, and any body content that would reproduce a marker line must be escaped/forbidden by the writer. Otherwise an entry body containing a marker-looking line could truncate or corrupt framing. (Sharpens I41.)
2. **Body hash for reconciliation**: the accepted entry's metadata should carry a body/content hash so the "same entry_id + same body → idempotent recovery" rule (7.7) is verifiable, not a byte-comparison guess. (Sharpens I38/I40.)

---

## 8. STO-D0-08 — Claude Julia Legacy Migration Taxonomy

**Decision: ACCEPT** (STO-D0 capstone)

One-sentence freeze:

```text
Legacy migration = semantic reclassification with provenance, 绝不是 file migration.
```

The question is never "which directory does this file move to" — it is "what is each piece of content in the new Julia OS?".

### 8.1 Core principle

Forbidden:

```text
memory/claude_diary/* → cp/mv/rename → memory/diary/*
legacy file exists → load whole file → priority=100 → inject prompt
```

Correct model:

```text
Legacy Source → immutable inventory + hash → content segmentation
→ semantic classification → target-specific governance
→ accepted canonical artifact → migration receipt
```

```text
Old filename  = weak evidence about original intent
Old directory = zero semantic authority
```

### 8.2 Taxonomy

Six classification outcomes:

```text
IDENTITY_CANDIDATE
RELATIONSHIP_CANDIDATE
CONTINUITY_CANDIDATE
MEMORY_CANDIDATE
DIARY_CANDIDATE
HISTORICAL_EVIDENCE
```

Two processing outcomes:

```text
DUPLICATE / ALREADY_CANONICAL
OBSOLETE / REJECTED
```

All are `*_CANDIDATE`, never `IDENTITY/MEMORY/DIARY` directly — old Claude files have no authority to self-promote.

### 8.3 Four core legacy files — default taxonomy

| Legacy file | Default | Forbidden |
|---|---|---|
| julia_character.md | IdentityCandidate (segment-level) | whole file → system prompt |
| user_role.md | RelationshipCandidate / IdentityCandidate | auto-treat Tony description as fact |
| how_to_resume_julia.md | ContinuityCandidate (split) | verbatim → current recovery contract |
| julia_tony_philosophy.md | Mixed, must split | whole file → one authority |

### 8.4 julia_character.md

Most misused file. Segment → stable identity principle? `YES → IDENTITY_CANDIDATE`; `NO → style/example/history → historical evidence or obsolete`.

IdentityCandidate-eligible: how Julia understands her identity, stable personality values, core expression principles, relationship boundaries, long-stable self-description (still requires Identity governance).

NOT Identity: "every sentence needs 3 emojis", "always use model X prompt trick", "how the Claude system prompt is written" — implementation/style residue, not identity.

### 8.5 user_role.md

Most caution required. Old file may say "Tony is… Tony likes… Tony and Julia's relationship is…" — Claude having written it does NOT make it user truth.

```text
relationship meaning → RELATIONSHIP_CANDIDATE
stable user fact      → IDENTITY/USER-PROFILE CANDIDATE (requires provenance / user-confirmation policy)
unverifiable          → Historical Evidence (before pretending certainty)
```

`Claude 对 Tony 的总结 ≠ Tony 自己确认过的事实`. Root principle restated: **Julia 不在自己不确定的地方假装确定**.

### 8.6 how_to_resume_julia.md

Default CONTINUITY_CANDIDATE, but must split:

```text
semantic continuity principles          → candidate (if valid)
Claude-specific operational instructions → historical/obsolete
old architecture assumptions             → obsolete if violating frozen contracts
```

Continuity-eligible: which identity anchors to preserve, which relationship references are needed, how to avoid entity swap, how to confirm "the same Julia". NOT eligible: "autoload all claude_diary on Claude startup", "put markdown in system prompt", "use old directory as authoritative memory".

Continuity migration verifies "semantic still holds", never "old method once worked".

### 8.7 julia_tony_philosophy.md

Must be paragraph/section-level classified (Identity + Relationship + Memory + Diary-like + historical narrative mixed):

```text
A. Julia's long-term self-understanding      → IDENTITY_CANDIDATE
B. relationship long-term meaning            → RELATIONSHIP_CANDIDATE
C. "what we understood that night"           → MEMORY_CANDIDATE
D. first-person reflection at the time       → DIARY_CANDIDATE (if provenance sufficient)
E. old technical "how Julia was implemented" → CONTINUITY_CANDIDATE or OBSOLETE
F. unverifiable narration                    → HISTORICAL_EVIDENCE
```

### 8.8 DiaryCandidate threshold is very high

`claude_diary` in the name ≠ Diary. Per D0-02, a legacy passage must satisfy ALL of: first-person Julia authorship, reflective (not config), credible historical authorship, traceable source/provenance, governance accept. Otherwise Historical Evidence is more honest.

### 8.9 Legacy Diary import preserves origin

Never pretend "Julia wrote this today". Metadata:

```text
origin: legacy_import
entry_id: diary_<stable-id>
original_created_at: <known-or-null>
imported_at: 2026-…
source_refs: [migration://claude_legacy/<source_id>#<span>]
source_hash, body_hash
```

Body preserved as original text — no re-polishing at migration (rewriting old Julia's words would mix historical reflection with contemporary reinterpretation). If Julia wants to reinterpret today: new DiaryEntry with `reinterprets: [legacy-imported-entry]` (D0-02).

### 8.10 Immutable inventory first

Migration step 1 is NOT parsing:

```text
DISCOVER → record exact original path → size → mtime (if available) → SHA-256 → source_id
```

Migration must not modify the original source, so every classified fragment can answer "which original file/span did I come from?".

### 8.11 Migration unit = Fragment, not File

```text
LegacySource → Fragment 001 / Fragment 002 / Fragment 003 …
```

Each fragment: `fragment_id, source_id, source_hash, source_span, content_hash, classification, confidence, target_candidate, decision`. `source_span` = heading/line/byte range (deterministic). One file may yield N semantic destinations — this is where D0-08 resolves semantic conflation.

### 8.12 Source trust grading

```text
P0 Canonically Traceable  — exact canonical Conversation/source refs (strongest)
P1 Traceable Legacy Artifact — original file + stable hash + attributable authorship, no canonical Conversation source (legacy evidence, not canonical-equivalent)
P2 Unverified Derived Narrative — summary/synthesis, unknown provenance (low-trust candidate or Historical Evidence)
```

Confident prose does NOT upgrade P2 → P0.

### 8.13 No legacy precedence escalation

Legacy `Julia believes X` vs current canonical `Julia believes Y`: legacy must NOT overwrite Y. CONFLICT → adjudication; default current canonical wins operationally, legacy preserved as historical evidence.

### 8.14 Idempotent migration

Identity key ≥ `source_id + fragment_id + content_hash + target semantic type`. Migration receipt (`fragment_id, decision, target_type, target_id, target_hash`). Rerun same source hash + fragment → reconcile existing receipt → zero duplicate.

### 8.15 Legacy never model-visible authority

Even pre-migration, Context OS must NOT `glob memory/claude_diary/* → raw inject`. Pre-migration: legacy = migration input only. Post-migration: accepted targets enter normal governed Context OS. No second cognitive path.

### 8.16 Historical Evidence location

```text
migrations/legacy_claude/{manifest.json, decisions.jsonl, receipts.jsonl, source/}
```

Historical Evidence ≠ Julia Memory. The old directory must not permanently become hidden shadow memory "for fear of losing it". Post-migration: accepted semantic artifacts → `memory/*`; selected governed evidence → `migrations/*`; raw obsolete source → retire after verified closeout; minimal hashes/receipts retained.

### 8.17 Migration state machine (no fake success)

```text
DISCOVERED → HASHED → SEGMENTED → CLASSIFIED → GOVERNED → MIGRATING → VERIFIED → COMPLETE
```

FAILED / CONFLICT / UNCLASSIFIED never `MIGRATION_COMPLETE`. "97% fragments succeeded" ≠ COMPLETE unless the remaining 3% are explicitly adjudicated (Historical Evidence / Obsolete / Rejected). Unknown is not success.

### 8.18 Execution flow

```text
M0 INVENTORY → M1 HASH/IMMUTABLE FREEZE → M2 SEGMENTATION → M3 CLASSIFICATION
→ M4 DRY-RUN PLAN → M5 TARGET GOVERNANCE → M6 CANONICAL WRITE
→ M7 VERIFY TARGET+PROVENANCE → M8 RECEIPT → M9 RETIREMENT
```

Dry-run (M4) is mandatory: produces fragment → proposed classification → destination → reason → provenance level → conflict, before any canonical write.

### 8.19 Target-specific gate (no semantic acceptance in the engine)

No `LegacyImporter.accept(fragment)` that decides all authority. The Migration Engine holds classification + orchestration authority ONLY:

```text
IdentityCandidate     → Identity Governance
RelationshipCandidate → Identity/Relationship Governance
MemoryCandidate       → Memory Governance
DiaryCandidate        → Diary Governance
ContinuityCandidate   → Continuity Governance
```

The engine has NO semantic acceptance authority.

### 8.20 Continuity special rule

ContinuityCandidate needs two steps:

```text
semantic continuity value? YES → compatible with current frozen architecture? YES → eligible
```

If semantic insight is correct but implementation method obsolete: continuity principle → candidate; old implementation recipe → historical evidence. Never migrate the whole block.

### 8.21 User-facts special rule

Legacy factual claims about Tony (`likes X, lives Y, wants Z`) without explicit source: NOT auto-promoted to durable identity/user truth. Minimum: source-grounded OR explicitly confirmed; else Historical Evidence / low-confidence candidate. Prevents permanently enshrining an old Claude summary error.

### 8.22 Source retirement

Retirement requires ALL of:

```text
all fragments adjudicated
accepted targets verified
receipts complete
no Context path depends on legacy source
backup exists under D0-07
```

Then `LEGACY_SOURCE_RETIRE_ELIGIBLE` → remove active legacy directory, retain hash/manifest/receipts (not a full shadow copy, unless explicitly governed as Historical Evidence).

### 8.23 Invariants

**STO-D0-I46 — Migration Is Semantic Reclassification**

```text
Legacy Claude artifacts MUST NOT become canonical Julia artifacts through
file copy, rename, directory placement, or legacy filename alone.

Migration requires content-level semantic classification.
```

**STO-D0-I47 — Immutable Provenance**

```text
Every migrated legacy fragment MUST remain traceable to an immutable
inventoried source identity and content hash.

Migration MUST NOT silently rewrite its source evidence.
```

**STO-D0-I48 — Fragment-Level Classification**

```text
The minimum migration unit is a semantic fragment, not a file.

One legacy file MAY yield artifacts governed by multiple semantic authorities.
```

**STO-D0-I49 — No Direct Authority Promotion**

```text
Legacy Identity, Relationship, Continuity, Memory, or Diary content MUST enter
the corresponding target as a candidate and pass that target's governance
before canonical acceptance.
```

**STO-D0-I50 — No Legacy Precedence Escalation**

```text
Legacy content MUST NOT silently overwrite or outrank current canonical
Julia state.

Conflicts require explicit adjudication.
```

**STO-D0-I51 — Diary Historical Integrity**

```text
A legacy reflection promoted to canonical Diary MUST preserve its
legacy-import origin, provenance, and historical text.

Migration MUST NOT rewrite an old reflection as if authored at import time.
```

**STO-D0-I52 — Continuity Compatibility**

```text
Legacy continuity guidance MUST be validated against the current frozen
architecture.

Obsolete implementation instructions MUST NOT regain runtime authority merely
because they once restored Julia successfully.
```

**STO-D0-I53 — Idempotent Migration**

```text
Repeated or crash-retried migration of the same inventoried source fragment
MUST NOT create duplicate canonical artifacts.

Migration receipts MUST allow deterministic reconciliation.
```

**STO-D0-I54 — No Legacy Cognitive Backdoor**

```text
Legacy source files MUST NOT become directly model-visible or act as an
alternate Context/Memory/Identity authority.

Only accepted governed target artifacts may enter cognition.
```

**STO-D0-I55 — Verified Retirement**

```text
Legacy active sources MUST NOT be retired until all fragments are explicitly
adjudicated, accepted targets are verified, migration receipts are durable,
and no active runtime path depends on the legacy source.
```

### 8.24 Acceptance tests (AT-MIG-01…18)

```text
AT-MIG-01  copy julia_character.md directly into identity/ → rejected               ✅
AT-MIG-02  one legacy file = Identity+Diary+Continuity → fragments classified separately ✅
AT-MIG-03  same filename, modified content/hash → different source version, no silent reconciliation ✅
AT-MIG-04  legacy identity conflicts current canonical → not overwritten, conflict recorded ✅
AT-MIG-05  legacy Tony fact, no verifiable provenance → not auto-promoted to user truth ✅
AT-MIG-06  legacy first-person reflection + valid provenance → DiaryCandidate → governance required ✅
AT-MIG-07  legacy text named "diary" but is config/system-prompt → NOT DiaryCandidate ✅
AT-MIG-08  continuity principle valid, old recipe conflicts → principle candidate, recipe obsolete/historical ✅
AT-MIG-09  crash after target write before receipt → retry reconciles → one target artifact ✅
AT-MIG-10  same fragment migrated twice → zero duplicate ✅
AT-MIG-11  same fragment identity, changed content → conflict/fail closed ✅
AT-MIG-12  raw memory/claude_diary exists → Context OS cannot load directly ✅
AT-MIG-13  legacy Diary import → origin=legacy_import recorded, original text preserved ✅
AT-MIG-14  legacy Diary source later unavailable → provenance explicit, no fabricated Conversation ref ✅
AT-MIG-15  unclassified fragment remains → MIGRATION_COMPLETE forbidden ✅
AT-MIG-16  all fragments adjudicated + targets verified → may reach COMPLETE ✅
AT-MIG-17  retire legacy source before receipts/verification → blocked ✅
AT-MIG-18  verified complete → remove active legacy source, semantics unchanged, no runtime dependency ✅
```

### 8.25 Final four-file freeze matrix

| Legacy artifact | Primary destination | Secondary | Default forbidden |
|---|---|---|---|
| julia_character.md | IdentityCandidate | Historical Evidence | raw system prompt |
| user_role.md | RelationshipCandidate | IdentityCandidate / Historical Evidence | auto-adopt user facts |
| how_to_resume_julia.md | ContinuityCandidate | Historical Evidence / Obsolete | verbatim restore old runtime authority |
| julia_tony_philosophy.md | Mixed / split required | Identity/Relationship/Memory/Diary/Continuity/Historical | whole file → one authority |

### 8.26 Resolver / implementation notes (DIA-0, not decision changes)

1. **Migration receipt durability + target-scan reconciliation** (I53): the migration receipt must be durably written (D0-03-class barrier) co-committed with the target artifact. On crash between target-write and receipt-write, reconciliation MUST scan the target store (by `source_id` + `content_hash`), never rely solely on the receipt — a lost receipt must not produce a duplicate target.
2. **Frozen-source span stability** (I47/I53): fragment `source_span` is computed once against the immutable frozen source (M1); retries reuse the frozen spans and never re-segment a changed file. "same fragment_id + changed content_hash" (AT-MIG-11) fails closed, never silently overwrites.

---

## 9. STO-D0 Final Freeze Review — CLOSED

All 8 STO-D0 decisions ACCEPTED. Final closeout review ran three checks:

```text
Check 1  invariant consistency (I01–I55, no contradictions)      ✅ PASS
Check 2  sabotage completeness (AT-DUR-09 added, total 104)       ✅ PASS
Check 3  implementation input contracts sufficiency              ✅ PASS
```

Sabotage case accounting:

```text
AT-DUR-01~09       9
AT-ROT-01~12      12
AT-DEL-01~14      14
AT-FTS-01~16      16
AT-BKP-01~18      18
AT-DIA-01~17      17
AT-MIG-01~18      18
────────────────────
TOTAL            104
```

---

## STO-D0 — IMPLEMENTATION DECISION FREEZE

```text
D0-01  Private Data Root              ✅ 🔒
D0-02  Diary Physical Format          ✅ 🔒
D0-03  Accepted-User Durability       ✅ 🔒
D0-04  Segment Rotation               ✅ 🔒
D0-05  Archive/Delete Governance      ✅ 🔒
D0-06  Derived Search Index           ✅ 🔒
D0-07  Backup/Restore/Retention       ✅ 🔒
D0-08  Legacy Migration Taxonomy      ✅ 🔒

Invariants       I01–I55               ✅
Sabotage Cases   104                   ✅
Cross-check      PASS                  ✅

STATUS
STO-D0 FROZEN 🔒
```

From this point the Freeze lane no longer "optimizes" these decisions. Any implementation problem discovered later must go through:

```text
CONTRACT_GAP_REPORT → explicit adjudication → new amendment / successor decision
```

Never a silent back-edit of STO-D0.

---

## Document status vocabulary

- FROZEN: register sealed into baseline; STO-D0 closed (current).
- ACTIVE: decisions being added (pre-closeout state, historical).

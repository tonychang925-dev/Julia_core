# STO-D0 Decision Register v1.0

STATUS: ACTIVE
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

### 2.15 Acceptance tests (AT-DUR-01…08)

```text
AT-DUR-01  write → fsync → ACK → kill -9 → message survives           ✅
AT-DUR-02  write → fsync → kill before ACK → retry → one message      ✅
AT-DUR-03  inject fsync failure → no CORE_ACCEPTED                    ✅
AT-DUR-04  fsync failure + record exists → reconcile by turn_id → no dup ✅
AT-DUR-05  same turn_id + different content → conflict / fail closed  ✅
AT-DUR-06  corrupt partial JSONL tail → earlier records survive + evidence ✅
AT-DUR-07  catalog/index write fails after fsync → message remains truth ✅
AT-DUR-08  new segment → crash after ACK → segment + message discoverable ✅
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

## 5. Pending Decisions

```text
STO-D0-06   Derived search index technology (SQLite FTS)                         NEXT
STO-D0-07   Backup retention policy                                              PENDING
STO-D0-02   Diary file format (one append-only daily file vs date directory)     PENDING
STO-D0-08   Claude Julia legacy artifact migration classification rules          PENDING
```

---

## Document status vocabulary

- ACTIVE: decisions being added.
- FROZEN: all 8 decisions accepted; register sealed into baseline.

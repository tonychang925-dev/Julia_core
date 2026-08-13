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
2. **O_APPEND for atomic append**: open transcript segments in append mode (`O_APPEND`) so each record write is atomic with respect to other writers. Combined with single-shot record write + newline framing (2.9), this yields clean physical framing and makes partial-tail recovery unambiguous.

---

## 3. Pending Decisions

```text
STO-D0-04   Segment rotation defaults                                            NEXT
STO-D0-05   Archive vs tombstone vs hard-delete semantics                        PENDING
STO-D0-06   Derived search index technology (SQLite FTS)                         PENDING
STO-D0-07   Backup retention policy                                              PENDING
STO-D0-02   Diary file format (one append-only daily file vs date directory)     PENDING
STO-D0-08   Claude Julia legacy artifact migration classification rules          PENDING
```

---

## Document status vocabulary

- ACTIVE: decisions being added.
- FROZEN: all 8 decisions accepted; register sealed into baseline.

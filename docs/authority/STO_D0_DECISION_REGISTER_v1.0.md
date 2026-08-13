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

## 2. Pending Decisions

```text
STO-D0-02   Diary file format (one append-only daily file vs date directory)     PENDING
STO-D0-03   Accepted-user durability / flush / fsync contract                    PENDING
STO-D0-04   Segment rotation defaults                                            PENDING
STO-D0-05   Archive vs tombstone vs hard-delete semantics                        PENDING
STO-D0-06   Derived search index technology (SQLite FTS)                         PENDING
STO-D0-07   Backup retention policy                                              PENDING
STO-D0-08   Claude Julia legacy artifact migration classification rules          PENDING
```

---

## Document status vocabulary

- ACTIVE: decisions being added.
- FROZEN: all 8 decisions accepted; register sealed into baseline.

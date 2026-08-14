# DIA-2B-R0 — Assistant Persistence Reality Audit

STATUS: REVIEW_CANDIDATE
UPDATED: 2026-08-14
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave-3 Diary Implementation / DIA-2B-R0 (Claude-A read-only audit)
FROZEN INPUTS: DIA-0 `681884b` · DIA-1 `7525c6f` · DIA-2A `7f114ac` · D0-02 @ `261521f`

## Purpose

Locate the real Julia-AI-Assistant production persistence machinery so the
DiaryPersistenceAdapter (DIA-2B) reuses it instead of being designed from
conversational assumptions. READ-ONLY: no production edits, no adapter code.

## 1. Exact Assistant production file scope (reusable)

```text
DIA-2B Assistant IMPLEMENTATION BASE (P0-1 pinned):
  Julia-AI-Assistant wave1/sto-f2a-assistant @ 098d0d51e395ff99f9fcc8f8ed31bd31ab33f210
  (the branch that actually owns private_data/*)

wave2/conversation-management-assistant @ 3966075…
  = REFERENCE EVIDENCE ONLY (durable-append/flock pattern)
  ≠ automatically present in the DIA-2B worktree
  (098d0d5 and 3966075 DIVERGE from merge-base 44cea89; not parent-child)

private_data/                     ← present on the pinned base
  resolver.py      PrivateDataRootResolver.resolve() → ResolvedPrivateDataRoot
  layout.py        PrivateDataLayout (memory / diary / runtime / … paths)
  marker.py        RootMarker (BOOTSTRAPPING→READY) — NOT a day-dir primitive
  capability.py    NamespaceCapability (least-authority ops; needs extension, §2)
  composition.py   ApplicationCompositionRoot (build / report / layout)
  wiring.py        wire_legacy_composition (binding pattern)
  persistence.py   PersistenceFailure + PERSISTENCE_* codes
  segmented_repository.py / reconciliation.py / cutover.py   (Conversation, pattern only)
```

## 2. Existing persistence primitives we can reuse

```text
PrivateDataRootResolver.resolve()          → canonical private root
PrivateDataLayout(root).diary              → <root>/memory/diary
NamespaceCapability.append_owned_durable() → write-all + flush + fsync(file), O_APPEND,
                                             short-write loop (D0-03 barrier)
NamespaceCapability.fsync_owned_subdir()   → directory durability barrier (single dir)
NamespaceCapability.fsync_owned_file()     → explicit file fsync
NamespaceCapability.list_owned_dir()       → segment/day-file discovery
PersistenceFailure.from_os_error()         → OSError → structured failure (no raw-path leak)
```

### Missing capability work (P0-2/P0-3 — DIA-2B must EXTEND capability, not bypass it)

```text
NamespaceCapability today does NOT provide:
  - durable private directory hierarchy (force 0700 on newly-created memory/diary/2026/08/)
  - day file mode enforcement (0600)
  - FULL parent-entry durability chain (fsync every newly-created dir, not just the leaf)
  - owned same-day writer lock (per-day serialization + idempotency race protection)

Diary adapter MUST NOT get the raw path and do its own os.mkdir/chmod/lock —
the capability owns physical Path (F2 least-authority). DIA-2B extends
NamespaceCapability (or a diary-scoped subclass) with:
  ensure_owned_private_tree(...)   → exact 0700 dirs, 0600 file
  durable_parent_chain(...)        → fsync every newly-created dir
  owned_day_lock(...)              → same-day exclusive lock (flock, Wave-2 reference)
```

## 3. Private root authority source

```text
Julia-AI-Assistant → PrivateDataRootResolver (F1, sole product resolver)
  → ResolvedPrivateDataRoot.canonical_path
  → PrivateDataLayout
```

Core never resolves the diary path (DIA-2A + ADR-033 path opacity).

## 4. Exact adapter placement

```text
Julia-AI-Assistant
  private_data/diary_repository.py      ← DiaryPersistenceAdapter (NEW)
  (implements julia_core.diary.DiaryRepository Port)

Composition wiring: ApplicationCompositionRoot.build() gains a
diary_repository binding (mirrors wire_legacy_composition pattern). DIA-2B
implementation, not R0.
```

## 5. Exact failure type placement

```text
Reuse private_data/persistence.py PersistenceFailure codes:
  PERSISTENCE_WRITE_FAILURE       → write/short-write failure
  PERSISTENCE_DURABILITY_FAILURE  → fsync / dir-barrier failure (no DIARY_DURABLE)
  PERSISTENCE_CONFLICT            → same entry_id + different body_hash
  PERSISTENCE_CORRUPTION_DETECTED → malformed frame / orphan BEGIN at read time

Adapter raises these; Core Port semantics unchanged (normal return == DIARY_DURABLE).
```

## 6. Exact tests placement

```text
Julia-AI-Assistant
  tests/test_diary_repository.py      ← DIA-2B adapter sabotage (AT-DP-01..14)
  tests/conftest.py                   ← existing fixtures (temp root, resolver, capability)

Cross-repo import: tests import the Core Port from julia_core (Wave-3 DIA lane).
```

## 7. Filesystem durability sequence (frozen mapping)

```text
serialize accepted entry → framed bytes
        ↓
ensure owned private directory tree (0700):
  create diary     → fsync(memory)
  create 2026      → fsync(diary)
  create 08        → fsync(2026)          # FULL parent-entry chain, not just leaf
        ↓
create day file (0600)
append complete frame (write-all + flush + fsync(file))
        ↓
fsync(08)                                  # day dir barrier
        ↓
DIARY_DURABLE → normal return
```

Any step failing → no successful return → entry not observable.

## 8. Framing schema mapping (frozen D0-02)

```text
<root>/memory/diary/YYYY/MM/YYYY-MM-DD.md   (single daily container, append-only)

Frozen D0-02 guarantees (not a bespoke schema):
  single daily Markdown container
  explicit BEGIN/END framing
  stable entry_id
  first-person body
  source refs
  append-only
  collision-resistant framing

Adopted marker framing (D0-02 "framed example" as guidance, not frozen exact):
  BEGIN:  <!-- JULIA_DIARY_ENTRY_BEGIN <entry_id> -->
  metadata: entry_id / created_at / reflection_time / body_hash /
            source_refs / provenance / title / themes /
            relationship_significance / project_significance /
            supersedes / reinterprets (DIA-CG-01 successor amendment)
  body: Julia first-person Markdown
  END:    <!-- JULIA_DIARY_ENTRY_END <entry_id> -->

Collision resistance (AT-DP-16): body containing an exact marker-looking
line MUST be escaped/rejected deterministically by the writer — body can
never terminate or inject another frame; parser round-trips the body.

complete BEGIN+END           → candidate durable frame
orphan BEGIN (no END)        → incomplete/crash residue → NOT exposed as accepted
```

## 9. Idempotency / recovery algorithm

```text
primary key = entry_id

same entry_id + EXACT same canonical AcceptedDiaryEntry
  (all semantic fields equal, not just body_hash)
  → idempotent success (existing durable entry)

same entry_id + ANY semantic field differs
  (body, body_hash, source_refs, title, themes, significance,
   supersedes, reinterprets, provenance)
  → PERSISTENCE_CONFLICT (never second append)

new entry_id → append

read/recovery:
  preserve complete frames
  quarantine incomplete final tail (orphan BEGIN)
  emit repair evidence
  never guess-fill a partial frame
```

## 10. AT-DP-01..14 implementation sabotage plan

```text
Core Port (already covered DIA-2A): AT-DP-C01..06
Assistant Adapter:
  AT-DP-01  Core resolves diary path → VIOLATION (static)
  AT-DP-02  file fsync failure → no DIARY_DURABLE (fault-inject fsync)
  AT-DP-03  crash mid-frame → prior entries survive, incomplete frame not exposed
  AT-DP-04  reinterpretation → append new entry, old bytes unchanged
  AT-DP-05  diary persistence failure ≠ conversation rollback
  AT-DP-06  GOVERNANCE_APPROVED + fsync failure → NOT Accepted, not retrievable, not Memory-eligible
  AT-DP-07  fsync succeeded + crash before observe → reopen by entry_id → exactly one durable
  AT-DP-08  same entry_id + same body_hash retry → exactly one durable
  AT-DP-09  same entry_id + different body_hash → conflict, zero second append
  AT-DP-10  orphan/incomplete BEGIN at EOF → ignored/quarantined, never returned accepted
  AT-DP-11  malformed historical frame → fail-closed for that frame, prior valid readable
  AT-DP-12  new YYYY/MM dir creation without dir-barrier → no DIARY_DURABLE claim
  AT-DP-13  permission != 0600 / dir != 0700 → contract violation
  AT-DP-14  adapter receives path-traversal/caller physical path → reject (day path internal only)
  AT-DP-15  two simultaneous same-day writers → no frame interleave; same entry_id → exactly one durable entry
  AT-DP-16  body contains exact BEGIN/END-looking marker line → writer escapes/rejects deterministically; parser round-trips body; cannot inject another frame
  AT-DP-17  timezone policy changes later → existing entry remains in its original day partition
```

## Day-partition authority (exact rule)

```text
AcceptedDiaryEntry.created_at MUST be offset-aware (e.g. RFC3339 with offset).

day partition = diary-local timezone at FIRST durable acceptance.
its local calendar date fixes YYYY-MM-DD.md.

later timezone change → old entries NEVER move partitions.

Electron / API caller / LLM / Diary body MUST NOT pass
"write to 2026-08-14.md". Physical day path is adapter-internal only.
```

## Contract gap (DIA-CG-01)

```text
D0-02 freezes BOTH `reinterprets` (new understanding) and `supersedes`
(explicit correction). FINAL AcceptedDiaryEntry (DIA-1 @ 7525c6f) carries only
`supersedes`. This cannot be back-edited; resolution = DIA-1A successor
amendment adding `reinterprets: tuple[str, ...] = ()` (same exact primitive
rules as supersedes). Not a DIA-2B serializer hack.
```

## DIA-2B-R0 exit gate

```text
[ ] exact Assistant file scope identified
[ ] reusable primitives enumerated (resolver/layout/capability/errors)
[ ] private root authority source named
[ ] adapter + tests placement decided
[ ] durability sequence + framing + idempotency mapped to frozen D0-02
[ ] AT-DP-01..14 sabotage plan fixed
```

## Document status vocabulary

- REVIEW_CANDIDATE: awaiting Mira review (current).
- FROZEN: sealed after review.

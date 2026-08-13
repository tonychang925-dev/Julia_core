# W3-A4 — Diary Persistence / Repository Port Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 3 — Diary Persistence Protocol (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: STO-F1 @ `23ecc1f` · STO-F2 @ `edc0692` · D0-02 (STO-D0 @ `261521f`) · W3-A0 (this lane)

## Governing principle

```text
Core owns diary semantics. Assistant owns physical diary persistence.
```

Physical diary format: D0-02 @ STO-D0 `261521f` (single daily Markdown container).
Physical root / namespace hosting: STO-F1 @ `23ecc1f` + STO-F2 binding.

```text
memory/diary/YYYY/MM/YYYY-MM-DD.md
```

## Port / adapter split

```text
DiaryRepositoryPort (Core)
  - defines accepted DiaryEntry semantics
  - append accepted entry, read entries, lookup by entry_id
  - durability expectation (DIARY_DURABLE, not CORE_ACCEPTED)

DiaryPersistenceAdapter (Assistant)
  - physical write: BEGIN/END framing, flush, fsync, directory barrier
  - day-partition derivation, permissions (file 0600 / dir 0700)
  - filesystem errors → structured persistence failures
```

```text
Core MUST NOT resolve the diary filesystem path.
```

Carries forward D0-02: append-only day file, explicit framing, stable entry_id, append-only historical reflection (reinterpretation = new entry, never rewrite).

## Durable truth boundary (P0)

```text
DiaryCandidate
        ↓
Diary Governance
        ↓
GOVERNANCE_APPROVED
        ↓
Persistence Adapter
        ↓
framed write → flush → fsync → directory barrier
        ↓
DIARY_DURABLE
        ↓
Accepted DiaryEntry
```

```text
Accepted DiaryEntry  iff  GOVERNANCE_APPROVED AND DIARY_DURABLE.
```

Governance approval alone does NOT create durable DiaryEntry truth. Persistence decides neither content-worthiness (no semantic authority) nor acceptance; but durability is a necessary gate on accepted truth becoming durable truth.

On governance-approved + persistence-failed:

```text
NOT Accepted DiaryEntry
→ no diary retrieval exposure
→ no MemoryCandidate eligibility
→ no Electron/API accepted projection
→ retry / idempotent recovery allowed (by stable entry_id)
```

## Invariants

**W3-A4-I01 — Semantics Core, Physics Assistant**

```text
Core owns diary semantics; Assistant owns physical persistence mechanics.
Core never resolves filesystem paths.
```

**W3-A4-I02 — Durable Acceptance**

```text
DIARY_DURABLE requires complete framed write + flush + fsync + directory
barrier. It is decoupled from CORE_ACCEPTED (conversation durability).
```

**W3-A4-I03 — Append-Only**

```text
Normal authorship appends immutable entries. Reinterpretation is a new entry,
never a rewrite of an accepted entry.
```

**W3-A4-I04 — Durable Truth Boundary**

```text
Governance approval alone does not create durable DiaryEntry truth.
Accepted DiaryEntry exists only after governance approval AND successful
DIARY_DURABLE persistence. A persistence-failed approved entry is NOT
accepted, NOT retrievable, NOT Memory-eligible.
```

## Sabotage suite (AT-DP-01…05) — SPEC (not PASS)

```text
AT-DP-01  Core resolves diary filesystem path → contract violation           [REQUIRED]
AT-DP-02  fsync failure → no DIARY_DURABLE                                   [REQUIRED]
AT-DP-03  crash mid-entry → prior complete entries survive                   [REQUIRED]
AT-DP-04  reinterpretation → new entry, old bytes unchanged                  [REQUIRED]
AT-DP-05  diary persistence failure ≠ conversation rollback                  [REQUIRED]
AT-DP-06  governance approved + fsync failure → NOT Accepted, not retrievable, not Memory-eligible [REQUIRED]
AT-DP-07  fsync succeeded + process dies before observe → reopen by entry_id → exactly one durable entry [REQUIRED]
```

## Acceptance gate

```text
[ ] Core = semantics, Assistant = physics, Core path opacity
[ ] DIARY_DURABLE decoupled from CORE_ACCEPTED
[ ] append-only day file, stable entry_id, framed
[ ] diary failure isolated from conversation authority
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).

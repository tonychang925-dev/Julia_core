# CM-S6 — Archive / Delete Governance Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 2 — CM-S6 Protocol Freeze (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: STO-D0 @ `261521f` (D0-05) · CM-S2 (this lane, search visibility gate)

## Governing principle

```text
Archive/delete is lifecycle governance, not filesystem operations.
It never deletes canonical truth without governed resolution, and it never
leaves dangling provenance or resurrects purged truth.
```

## Lifecycle states

```text
ACTIVE → ARCHIVED → TOMBSTONED → PURGED
```

```text
archive   ≠ delete
tombstone ≠ purge
purge     ≠ filesystem rm without governance
```

Carries forward D0-05 (archive preservation, tombstone exclusion, no unresolved hard delete, no false erasure).

## State semantics

```text
ACTIVE     normal acceptance; append allowed
ARCHIVED   hidden from default list; canonical truth retained; retrievable
TOMBSTONED usage/visibility cut; bytes retained temporarily; no append/resume
PURGED     physical truth removed only after reference governance
```

## Search visibility gate (inherits CM-S2 / D0-06)

```text
default search      ACTIVE
include_archived    ACTIVE + ARCHIVED
TOMBSTONED          never exposed
PURGED              never exposed
```

## Reference governance (inherits D0-05)

```text
Hard purge requires resolving durable semantic / protected references
(Memory / Diary / Identity / Continuity) before completion. No cascade
delete by storage; no silent dangling provenance.
```

## Invariants

**CM-S6-I01 — Lifecycle, Not Filesystem**

```text
Archive/tombstone/purge are governed lifecycle transitions. Purge is not a
bare filesystem rm without reference governance.
```

**CM-S6-I02 — No Dangling Provenance**

```text
Purging a canonical source never leaves an unexplained dangling reference.
Reference lifecycle represents PURGED explicitly.
```

**CM-S6-I03 — No Cascade by Storage**

```text
Storage/lifecycle layer MUST NOT independently delete or rewrite Memory,
Diary, Identity, or Continuity artifacts.
```

**CM-S6-I04 — Visibility Gate Holds**

```text
Tombstoned/purged conversations are never exposed via search or normal
access, even with stale derived state.
```

## Sabotage suite (AT-DEL2-01…08) — SPEC (not PASS)

```text
AT-DEL2-01  archive → transcript byte-identical, IDs unchanged               [REQUIRED]
AT-DEL2-02  tombstone → default list excludes; no append/resume              [REQUIRED]
AT-DEL2-03  stale index → search still cannot expose tombstoned content      [REQUIRED]
AT-DEL2-04  hard delete with unresolved refs → blocked                       [REQUIRED]
AT-DEL2-05  resolve refs → purge eligible                                    [REQUIRED]
AT-DEL2-06  purged source ref → resolves as PURGED, never dangling           [REQUIRED]
AT-DEL2-07  delete conversation → storage does NOT cascade-delete Memory/Diary [REQUIRED]
AT-DEL2-08  restore archived → same conversation_id, no transcript rewrite   [REQUIRED]
```

## Acceptance gate

```text
[ ] ACTIVE → ARCHIVED → TOMBSTONED → PURGED governed
[ ] archive ≠ delete; tombstone ≠ purge; purge ≠ bare rm
[ ] reference governance before hard purge
[ ] no cascade delete, no dangling provenance
[ ] search visibility gate holds for tombstone/purged
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).

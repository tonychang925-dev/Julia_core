# CM-S1C — Legacy ↔ Segmented Reconciliation Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 1 — CM-S1C Reconciliation Protocol Freeze (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd` (Wave-0 closeout)
FROZEN INPUTS: STO-D0 @ `261521f` · STO-F1 @ `23ecc1f` · STO-F2 @ `edc0692`

## Governing principle

```text
Reconciliation is NOT "copy legacy data into segmented files".
Reconciliation PROVES the segmented candidate can express the same
Core semantic truth as the legacy canonical store.
```

Authority does not move during proof. Legacy remains ACTIVE until S1D.

## 1. Reconciliation authority

```text
LegacyRepository                        = ACTIVE AUTHORITY (throughout S1C)
SegmentedJsonlConversationRepository    = READY CANDIDATE (read-only projection)
```

No dual authority. No candidate-side write to canonical truth during proof.

## 2. Source of truth

```text
legacy canonical snapshot   = frozen, immutable reference for the proof run
segmented candidate         = projection built by a deterministic import
```

The legacy snapshot MUST be frozen (hash + content-addressed) before the proof begins; a proof run against a moving legacy store is invalid.

## 3. Equivalence unit (what "same truth" means)

A conversation is equivalent iff all of the following agree between legacy and candidate:

```text
conversation_id
message_id          (per message)
turn_id             (per message)
role
modality
content
status              (accepted / completed / interrupted …)
created_at          (stable ordering anchor)
ordering            (canonical append order, not arrival order)
lifecycle metadata  (archive / tombstone state)
```

Equivalence is per-Core-semantic-truth, NOT byte-identity of the backing files. Segment boundaries, derived counters, and catalog hints are NOT part of the equivalence unit (they are physical, rebuildable).

## 4. Mismatch taxonomy

```text
MISSING           legacy has a message the candidate lacks
EXTRA             candidate has a message legacy lacks
IDENTITY_CONFLICT same message_id/turn_id, different identity fields
ORDER_CONFLICT    same message set, different canonical order
STATUS_CONFLICT   same message, different status
CONTENT_CONFLICT  same message_id, different content
METADATA_CONFLICT different lifecycle metadata (archive/tombstone)
```

Every mismatch MUST be classified into exactly one category. Unclassified discrepancy = BLOCKED (never "guessed").

## 5. Reconciliation outcome

```text
VERIFIED      exact semantic equivalence, zero mismatch
REPAIRABLE    deterministic, evidence-producing repair path exists
              (repair produces a NEW verified proof run; it does not edit truth in place)
BLOCKED       cannot reconcile without explicit adjudication
```

```text
NEVER "best effort" — no silent reconciliation, no auto-patch of canonical truth.
```

## 6. Retry / idempotency

```text
Re-running reconciliation over the same frozen legacy snapshot
and the same candidate MUST produce the same outcome and MUST NOT
duplicate or mutate canonical truth.
```

Reconciliation is a READ-ONLY proof over frozen inputs + a projection. Any step that would write canonical truth is out of scope for S1C (that is S1D ACTIVATE).

## 7. AT-BIND-20 acceptance definition

AT-BIND-20 (same Core contracts → contract-equivalent semantic behavior across LegacyRepository and SegmentedJsonlConversationRepository) is ACCEPTED iff:

```text
1. The full reconciliation equivalence unit (§3) VERIFIED.
2. Core semantic behavior on both backends is contract-equivalent
   (same conversation/message/turn identity, ordering, status, content).
3. Physical representation differences (segment files vs aggregate JSON)
   are invisible to Core ports.
```

## Invariants

**CM-S1C-I01 — No Authority Movement During Proof**

```text
Legacy repository remains ACTIVE authority for the entire reconciliation
proof. The segmented candidate is a read-only projection, never a writer.
```

**CM-S1C-I02 — Semantic, Not Byte, Equivalence**

```text
Equivalence is measured over the Core semantic unit (§3), not over
physical byte identity or file layout.
```

**CM-S1C-I03 — Classify, Never Guess**

```text
Every discrepancy MUST be classified into the mismatch taxonomy (§4).
Unclassified discrepancy is BLOCKED, never auto-repaired.
```

**CM-S1C-I04 — Frozen Source**

```text
The legacy snapshot and candidate projection are frozen before the proof.
A proof over a moving source is invalid and MUST be rejected.
```

**CM-S1C-I05 — Idempotent Proof**

```text
Reconciliation over the same frozen inputs is idempotent and side-effect-free
with respect to canonical truth.
```

**CM-S1C-I06 — Progression Gate**

```text
Only VERIFIED (or REPAIRABLE → re-run → VERIFIED) reconciliation permits
progression to S1D cutover. BLOCKED reconciliation halts S1D.
```

## Sabotage suite (AT-RECON-01…10)

```text
AT-RECON-01  identical legacy/candidate → VERIFIED                          ✅
AT-RECON-02  missing message in candidate → MISSING → BLOCKED, no auto-patch ✅
AT-RECON-03  extra message in candidate → EXTRA → BLOCKED                    ✅
AT-RECON-04  content conflict → CONTENT_CONFLICT → BLOCKED                   ✅
AT-RECON-05  order conflict → ORDER_CONFLICT → BLOCKED                       ✅
AT-RECON-06  status conflict → STATUS_CONFLICT → BLOCKED                     ✅
AT-RECON-07  re-run same inputs → idempotent, zero mutation/duplication      ✅
AT-RECON-08  legacy mutated mid-proof → proof rejected (frozen source)       ✅
AT-RECON-09  candidate mutated mid-proof → proof rejected                    ✅
AT-RECON-10  unclassified discrepancy → BLOCKED (never guessed)              ✅
```

## Acceptance gate

```text
[ ] legacy remains ACTIVE authority throughout
[ ] equivalence unit fully specified and enforced
[ ] mismatch taxonomy complete (7 categories)
[ ] outcome ∈ {VERIFIED, REPAIRABLE, BLOCKED}; never best-effort
[ ] retry idempotent, zero canonical mutation
[ ] AT-BIND-20 acceptance criteria explicit
[ ] BLOCKED reconciliation halts S1D progression
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).

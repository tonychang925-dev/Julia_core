# CM-S1C — Legacy ↔ Segmented Reconciliation Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13 (R1 review closure)
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

Authority does not move during proof. Legacy remains ACTIVE authority until S1D ACTIVATE.

## 1. Reconciliation authority

```text
LegacyRepository                        = ACTIVE AUTHORITY (throughout S1C)
SegmentedJsonlConversationRepository    = READY CANDIDATE (staged projection)
```

No dual authority. No candidate-side write to canonical truth during proof.

## 2. Projection lifecycle (BUILD → FREEZE → PROVE)

```text
BUILD_PROJECTION
    deterministic import from the frozen legacy snapshot
    candidate MAY receive non-authoritative deterministic writes here

FREEZE_PROJECTION
    candidate hash / manifest / immutable proof input captured

PROVE
    completely read-only comparison over the frozen inputs
```

Legacy canonical truth is never modified by any S1C stage. Only BUILD_PROJECTION writes, and only into the non-authoritative candidate.

## 3. Equivalence unit (what "same truth" means)

Equivalence is semantic (per-Core-truth), NOT byte identity.

### conversation-level

```text
conversation_id
title
topic
tags
created_at
updated_at
summary_status        (when represented)
lifecycle state       (when represented — see NOT_APPLICABLE rule)
```

### message-level (per canonical ConversationMessage)

```text
message_id
turn_id
role
modality
source
content
status
created_at
canonical ordering
```

Segment boundaries, derived counters, and catalog hints are NOT part of the equivalence unit (physical, rebuildable).

### Lifecycle NOT_APPLICABLE rule

```text
If lifecycle state exists in both current canonical models → compare it.
If lifecycle semantics are not yet implemented (Archive/Tombstone is CM-S6) → NOT_APPLICABLE.
MUST NOT manufacture synthetic archive/tombstone state.
```

S1C is not blocked by future-stage lifecycle semantics.

## 4. Mismatch taxonomy (atomic discrepancy classification)

```text
MISSING           legacy has an entity the candidate lacks
EXTRA             candidate has an entity legacy lacks
IDENTITY_CONFLICT same message_id/turn_id, different identity fields
ORDER_CONFLICT    same message set, different canonical order
STATUS_CONFLICT   same message, different status
CONTENT_CONFLICT  same message_id, different content
METADATA_CONFLICT different conversation/message metadata (title/topic/tags/source/summary)
```

Classification rule:

```text
Each ATOMIC discrepancy is classified exactly once.
One entity MAY yield multiple atomic discrepancies
(e.g. same message: content differs AND status differs).
```

Unclassified discrepancy = BLOCKED (never "guessed").

## 5. Reconciliation outcome

```text
VERIFIED      exact semantic equivalence, zero discrepancy
REPAIRABLE    deterministic, evidence-producing repair path exists
              (repair produces a NEW verified proof run; never edits truth in place)
BLOCKED       cannot reconcile without explicit adjudication
```

```text
NEVER "best effort" — no silent reconciliation, no auto-patch of canonical truth.
```

## 6. Retry / idempotency

```text
Re-running reconciliation over the same frozen inputs MUST produce the
same outcome and MUST NOT duplicate or mutate canonical truth.
```

S1C is read-only over frozen inputs + a projection. Writing canonical truth is S1D ACTIVATE, out of S1C scope.

## 7. Port behavioral parity (13-method observable behavior)

Snapshot equivalence is necessary but not sufficient. AT-BIND-20 also requires that the segmented adapter's observable behavior over the Core port is contract-equivalent to legacy for:

```text
get
list_all
create_with_id
delete
update_title
search
add_message
update_message_status
find_turn
get_messages
append_external_turns_atomic
import_messages_atomic
```

Each method's return shape, identity semantics, ordering, and failure mode must be contract-equivalent between backends.

## 8. AT-BIND-20 acceptance definition

```text
AT-BIND-20 ACCEPTED iff:
  1. snapshot equivalence (§3) VERIFIED, AND
  2. port behavioral parity (§7) VERIFIED for all 13 methods.

Physical representation differences (segment files vs aggregate JSON)
are invisible to Core ports.
```

```text
AT-BIND-20 acceptance definition = FROZEN (this doc)
AT-BIND-20 CLOSED = only after S1C implementation evidence
```

## Invariants

**CM-S1C-I01 — No Authority Movement During Proof**

```text
Legacy repository remains ACTIVE authority for the entire reconciliation
proof. The segmented candidate is a staged, non-authoritative projection.
```

**CM-S1C-I02 — Semantic, Not Byte, Equivalence**

```text
Equivalence is measured over the Core semantic unit (§3), not over
physical byte identity or file layout.
```

**CM-S1C-I03 — Classify, Never Guess**

```text
Every ATOMIC discrepancy is classified exactly once. Unclassified
discrepancy is BLOCKED, never auto-repaired.
```

**CM-S1C-I04 — Frozen Source**

```text
The legacy snapshot and candidate projection are frozen before PROVE.
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

**CM-S1C-I07 — Snapshot + Behavior**

```text
AT-BIND-20 requires BOTH snapshot equivalence AND port behavioral parity.
Snapshot-only equivalence is insufficient.
```

**CM-S1C-I08 — No Synthetic Lifecycle**

```text
Lifecycle state is compared only when it exists in both models. S1C MUST NOT
manufacture synthetic archive/tombstone state for unimplemented semantics.
```

## Sabotage suite (AT-RECON-01…12) — SPEC (not PASS)

```text
AT-RECON-01  identical legacy/candidate → VERIFIED                          [REQUIRED]
AT-RECON-02  missing message → MISSING → BLOCKED, no auto-patch             [REQUIRED]
AT-RECON-03  extra message → EXTRA → BLOCKED                                [REQUIRED]
AT-RECON-04  content conflict → CONTENT_CONFLICT → BLOCKED                  [REQUIRED]
AT-RECON-05  order conflict → ORDER_CONFLICT → BLOCKED                      [REQUIRED]
AT-RECON-06  status conflict → STATUS_CONFLICT → BLOCKED                    [REQUIRED]
AT-RECON-07  re-run same inputs → idempotent, zero mutation/duplication     [REQUIRED]
AT-RECON-08  legacy mutated mid-proof → proof rejected (frozen source)      [REQUIRED]
AT-RECON-09  candidate mutated mid-proof → proof rejected                   [REQUIRED]
AT-RECON-10  unclassified discrepancy → BLOCKED (never guessed)             [REQUIRED]
AT-RECON-11  content AND status conflict on one entity → two atomic classes [REQUIRED]
AT-RECON-12  unimplemented lifecycle → NOT_APPLICABLE (no synthetic state)  [REQUIRED]
```

`[REQUIRED]` = frozen acceptance specification, NOT production PASS. Converts to PASS only with S1C implementation evidence SHA.

## Acceptance gate

```text
[ ] legacy remains ACTIVE authority throughout
[ ] BUILD → FREEZE → PROVE lifecycle explicit
[ ] equivalence unit complete (conversation + message + source)
[ ] lifecycle NOT_APPLICABLE rule enforced
[ ] atomic mismatch classification (one entity, many discrepancies)
[ ] 13-method port behavioral parity required
[ ] outcome ∈ {VERIFIED, REPAIRABLE, BLOCKED}; never best-effort
[ ] retry idempotent, zero canonical mutation
[ ] BLOCKED reconciliation halts S1D progression
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).

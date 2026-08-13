# CM-S1D — Governed Repository Cutover Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 1 — CM-S1D Cutover Protocol Freeze (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd` (Wave-0 closeout)
FROZEN INPUTS: STO-D0 @ `261521f` · STO-F2 @ `edc0692` (F2-I11) · CM-S1C @ this lane

## Governing principle

```text
Cutover is an authority transition, not a dependency swap.
It follows the already-frozen ADR-002 sequence as an executable
state machine, and it never creates dual authority.
```

## 1. State machine

```text
ACTIVE(legacy)
    │ FREEZE   → legacy read-only, writes blocked
    ▼
FROZEN
    │ RECONCILE → run CM-S1C proof against frozen legacy + candidate
    ▼
RECONCILED
    │ VERIFY   → equivalence VERIFIED + durability + binding + rollback ready
    ▼
VERIFIED
    │ ACTIVATE → single atomic authority switch to segmented repository
    ▼
ACTIVE(segmented)
    │ RETIRE   → legacy → read-only historical/backup (not deleted)
    ▼
RETIRED
```

Every transition requires an explicit governing step. There is no silent transition, no skipped stage, no dual-active state.

## 2. CUTOVER_ALLOWED conditions (all MUST hold)

```text
CUTOVER_ALLOWED iff ALL of:
  1. legacy_frozen             — legacy writes blocked, snapshot immutable
  2. reconciliation_complete   — CM-S1C proof VERIFIED (not REPAIRABLE, not BLOCKED)
  3. semantic_equivalence_verified — full equivalence unit (§3 of CM-S1C)
  4. no_unaccounted_accepted_turn  — no accepted user turn exists outside the candidate
  5. candidate_durability_verified — candidate passes D0-03 durability (write+flush+fsync)
  6. candidate_binding_ready   — composition root bound to segmented repository, report READY
  7. rollback_recovery_ready   — rollback path + recovery evidence exist before ACTIVATE
```

Any condition failing → CUTOVER_BLOCKED. The cutover gate is fail-closed.

## 3. ACTIVATE semantics

```text
ACTIVATE = one atomic authority switch.
  - single active repository at all times (never dual authority)
  - Core ports re-bound to the segmented repository in one governed step
  - the switch is durable and observable (PersistenceBindingReport updated)
```

```text
ACTIVATE ≠ "start dual authority" — legacy and segmented MUST NOT both
accept canonical writes at the same time.
```

## 4. RETIRE semantics

```text
RETIRE = legacy becomes read-only historical/backup.
  - legacy bytes retained (NOT deleted immediately)
  - legacy removed from active acceptance path
  - deletion of legacy bytes is a separate governed retention step (D0-05/D0-07)
```

```text
RETIRE ≠ "delete legacy bytes immediately".
```

## 5. Rollback semantics

```text
Rollback is a governed reverse cutover, not a silent path swap.
  - rollback requires the pre-ACTIVATE recovery evidence (condition 7)
  - rollback re-activates legacy as authority in one governed step
  - Core MUST NOT silently fall back to legacy behind the cutover gate
```

```text
rollback ≠ "silently switch back behind Core".
```

## 6. AT-BIND-17 closure

AT-BIND-17 (governed FREEZE→RECONCILE→VERIFY→ACTIVATE sequence permits replacement activation) is ACCEPTED iff:

```text
1. The S1D state machine (§1) is the ONLY activation path.
2. CUTOVER_ALLOWED (§2) gates ACTIVATE.
3. No direct adapter replacement (F2-I11) bypasses the state machine.
```

## Invariants

**CM-S1D-I01 — No Dual Authority**

```text
At every instant, exactly one repository is the ACTIVE canonical authority.
ACTIVATE and rollback are atomic authority switches, never overlapping.
```

**CM-S1D-I02 — Fail-Closed Gate**

```text
If any CUTOVER_ALLOWED condition is unmet or indeterminate, cutover is
BLOCKED. There is no best-effort activation.
```

**CM-S1D-I03 — Governed Order**

```text
FREEZE → RECONCILE → VERIFY → ACTIVATE → RETIRE is strictly ordered.
No stage may be skipped or performed out of order.
```

**CM-S1D-I04 — Legacy Bytes Survive RETIRE**

```text
RETIRE renders legacy read-only and non-authoritative but does NOT delete
its bytes. Deletion is a separate governed retention step.
```

**CM-S1D-I05 — Rollback Is Governed**

```text
Rollback is a governed reverse cutover grounded in pre-ACTIVATE recovery
evidence. Core MUST NOT silently fall back to legacy.
```

**CM-S1D-I06 — Cutover Is Observable**

```text
Every cutover transition records durable evidence (binding report, freeze
snapshot, reconciliation verdict, activation record, retirement record).
```

## Sabotage suite (AT-CUT-01…10)

```text
AT-CUT-01  ACTIVATE without freeze → BLOCKED                                  ✅
AT-CUT-02  ACTIVATE with reconciliation BLOCKED → BLOCKED                      ✅
AT-CUT-03  ACTIVATE with unaccounted accepted turn → BLOCKED                   ✅
AT-CUT-04  ACTIVATE with candidate durability unverified → BLOCKED             ✅
AT-CUT-05  governed sequence → ACTIVATE succeeds, single authority            ✅
AT-CUT-06  post-ACTIVATE, legacy still accepts writes → violation detected    ✅
AT-CUT-07  RETIRE retains legacy bytes (not deleted)                          ✅
AT-CUT-08  rollback without recovery evidence → BLOCKED                       ✅
AT-CUT-09  direct adapter replacement bypassing state machine → CUTOVER_REQUIRED ✅
AT-CUT-10  Core silently falls back to legacy → violation detected            ✅
```

## Acceptance gate

```text
[ ] state machine is the only activation path
[ ] CUTOVER_ALLOWED conditions explicit and enforced
[ ] single-authority invariant holds at all times
[ ] RETIRE ≠ delete; legacy bytes survive as read-only
[ ] rollback governed, never silent
[ ] AT-BIND-17 closed
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).

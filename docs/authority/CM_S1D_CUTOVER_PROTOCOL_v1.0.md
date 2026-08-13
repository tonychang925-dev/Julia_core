# CM-S1D — Governed Repository Cutover Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13 (R1 review closure)
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

## 1. State machine + authority identity vs write availability

```text
ACTIVE(legacy)
    │ FREEZE   → legacy read-only, canonical write acceptance DISABLED
    ▼
FROZEN
    │ RECONCILE → CM-S1C proof against frozen legacy + candidate
    ▼
RECONCILED
    │ VERIFY   → equivalence + durability + binding + rollback ready
    ▼
VERIFIED
    │ ACTIVATE → single atomic authority switch to segmented repository
    ▼
ACTIVE(segmented)
    │ RETIRE   → legacy → read-only historical/backup (not deleted)
    ▼
RETIRED
```

Authority identity vs write availability (R1):

```text
During FROZEN / RECONCILED / VERIFIED:
    canonical_authority        = LegacyRepository   (unchanged)
    canonical_write_acceptance = DISABLED           (writes blocked)

Freeze is NOT "no authority". Authority stays legacy, but it no longer
accepts new canonical writes.
```

## 2. CUTOVER_ALLOWED conditions (all MUST hold)

```text
CUTOVER_ALLOWED iff ALL of:
  1. legacy_frozen             — legacy writes blocked, freeze watermark captured
  2. reconciliation_complete   — CM-S1C proof VERIFIED (not REPAIRABLE, not BLOCKED)
  3. semantic_equivalence_verified — full equivalence unit (CM-S1C §3)
  4. no_unaccounted_accepted_turn  — accepted-turn accounting proof (§6) shows zero gap
  5. candidate_durability_verified — candidate passes D0-03 durability (write+flush+fsync)
  6. candidate_adapter_ready   — staged binding descriptor READY (see below)
  7. rollback_recovery_ready   — rollback path + recovery evidence exist before ACTIVATE
```

`candidate_adapter_ready` (R1 — NOT a pre-ACTIVATE Core rebind):

```text
candidate_adapter_ready =
    segmented adapter constructed
    + namespace capability validated
    + durability verified
    + staged binding descriptor READY

candidate_adapter_ready ≠ ConversationRuntime already rebound
candidate_adapter_ready ≠ segmented already ACTIVE
```

The actual Core authority binding replacement happens ONLY at ACTIVATE (F2-I11: direct rebind → CUTOVER_REQUIRED). Condition 6 must not sneak the rebind early.

Any condition failing → CUTOVER_BLOCKED. The cutover gate is fail-closed.

## 3. ACTIVATE semantics

```text
ACTIVATE = one atomic authority switch.
  - single active repository at all times (never dual authority)
  - Core ports re-bound to the segmented repository in one governed step
  - durable and observable (PersistenceBindingReport updated)
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

## 5. Rollback semantics (R1 — safe rollback)

Rollback is a governed reverse cutover, never a silent path swap.

```text
ROLLBACK_ALLOWED iff EITHER:
  A. no post-ACTIVATE canonical acceptance occurred
     (segmented has received zero accepted canonical turns since ACTIVATE)
  OR
  B. reverse reconciliation completed:
     segmented current truth → legacy recovery candidate
     → semantic equivalence VERIFIED
     → no unaccounted accepted turn

Otherwise → ROLLBACK_BLOCKED.
```

Rationale: after ACTIVATE, segmented may hold NEWER truth (post-ACTIVATE accepted turns). Directly re-activating old legacy would lose those turns. Safe rollback requires either "nothing new" (A) or a verified reverse reconciliation (B).

```text
rollback ≠ "silently switch back behind Core".
```

## 6. CutoverFreezeBoundary watermark

Makes `no_unaccounted_accepted_turn` (condition 4) verifiable:

```text
CutoverFreezeBoundary {
    freeze_epoch
    legacy_snapshot_hash
    per-conversation last canonical message/sequence
    accepted-turn accounting proof
}
```

Captured at FREEZE. The accounting proof must establish that every accepted turn before the boundary is either in the candidate or explicitly accounted for.

## 7. AT-BIND-17 closure

```text
AT-BIND-17 ACCEPTED iff:
  1. The S1D state machine (§1) is the ONLY activation path.
  2. CUTOVER_ALLOWED (§2) gates ACTIVATE.
  3. No direct adapter replacement (F2-I11) bypasses the state machine.
```

```text
AT-BIND-17 acceptance definition = FROZEN (this doc)
AT-BIND-17 CLOSED = only after S1D implementation evidence
```

## Invariants

**CM-S1D-I01 — No Dual Authority**

```text
At every instant, exactly one repository holds canonical authority.
Write acceptance MAY be disabled during governed freeze states.
Never more than one repository may accept canonical writes.
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

**CM-S1D-I05 — Rollback Is Governed And Lossless**

```text
Rollback is a governed reverse cutover. It MUST NOT lose post-ACTIVATE
accepted truth. Direct re-activation of stale legacy is BLOCKED.
```

**CM-S1D-I06 — Cutover Is Observable**

```text
Every cutover transition records durable evidence (freeze boundary,
reconciliation verdict, activation record, retirement record).
```

**CM-S1D-I07 — Authority Identity Stable During Freeze**

```text
During FROZEN/RECONCILED/VERIFIED, canonical_authority remains legacy;
only canonical_write_acceptance is DISABLED. Freeze is not authority absence.
```

**CM-S1D-I08 — No Early Rebind**

```text
The staged candidate is READY but not ACTIVE. Core authority binding
replacement occurs only at ACTIVATE, never during VERIFY.
```

## Sabotage suite (AT-CUT-01…12) — SPEC (not PASS)

```text
AT-CUT-01  ACTIVATE without freeze → BLOCKED                                  [REQUIRED]
AT-CUT-02  ACTIVATE with reconciliation BLOCKED → BLOCKED                      [REQUIRED]
AT-CUT-03  ACTIVATE with unaccounted accepted turn → BLOCKED                   [REQUIRED]
AT-CUT-04  ACTIVATE with candidate durability unverified → BLOCKED             [REQUIRED]
AT-CUT-05  governed sequence → ACTIVATE succeeds, single authority            [REQUIRED]
AT-CUT-06  post-ACTIVATE, legacy still accepts writes → violation detected    [REQUIRED]
AT-CUT-07  RETIRE retains legacy bytes (not deleted)                          [REQUIRED]
AT-CUT-08  rollback without recovery evidence → BLOCKED                       [REQUIRED]
AT-CUT-09  direct adapter replacement bypassing state machine → CUTOVER_REQUIRED [REQUIRED]
AT-CUT-10  Core silently falls back to legacy → violation detected            [REQUIRED]
AT-CUT-11  rollback after post-ACTIVATE accepted turns without reverse reconcile → BLOCKED [REQUIRED]
AT-CUT-12  reverse reconciliation VERIFIED → rollback re-activates legacy losslessly [REQUIRED]
```

`[REQUIRED]` = frozen acceptance specification, NOT production PASS. Converts to PASS only with S1D implementation evidence SHA.

## Acceptance gate

```text
[ ] state machine is the only activation path
[ ] authority identity vs write availability explicit
[ ] CUTOVER_ALLOWED conditions explicit and enforced
[ ] candidate_adapter_ready ≠ active Core rebind
[ ] CutoverFreezeBoundary makes accepted-turn accounting verifiable
[ ] single-authority invariant holds at all times
[ ] RETIRE ≠ delete; legacy bytes survive as read-only
[ ] rollback governed and lossless (never drops post-ACTIVATE truth)
[ ] AT-BIND-17 definition frozen (closure pending evidence)
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).

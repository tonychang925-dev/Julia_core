# Capability Lineage Main Admission Record

**Record ID:** CAPABILITY_LINEAGE_MAIN_ADMISSION_RECORD_2026-08-28
**Repository:** Julia Core
**Admission Date:** 2026-08-28
**Admission Type:** Aggregate owner admission, not per-commit provenance reclassification

## 1. Admission Range

```text
Base:      698b811dfb9c7aae3529ba354cb6baa20b65e9b6
Candidate: a8d1cf3eaaf9aabfc8ba632f3648f5a0053a7be5
Range:     698b811..a8d1cf3
Commits:   56
```

## 2. Lineage Topology

```text
Lineage topology     PASS
Behind main          0
Ahead of main        56
Merge base           698b811dfb9c7aae3529ba354cb6baa20b65e9b6
Fast-forward shape   PASS
```

The candidate lineage descends directly from the Wave5 / main authority baseline and is not a divergent sibling history.

## 3. Accepted Aggregate Inputs

```text
C1 REV2 governance               ACCEPTED lineage input
R2 implementation progression    ACCEPTED lineage input
PRE-P4 no-silent-fallback        ACCEPTED / FROZEN
CRB-PRE-P1                       ACCEPTED / FROZEN
```

This record does not claim that every historical commit in the range was individually frozen at the time it was authored. It records owner acceptance of the aggregate lineage as a main-admissible capability/runtime baseline on 2026-08-28.

## 4. Authority Boundary Classification

```text
Identity authority mutation      NO
Continuity authority mutation    NO
Context OS authority rewrite     NO
Browser / DOM                    NO
P4 production                    NO
```

Runtime identity/continuity gates inside this lineage are classified as:

```text
classification = fail-closed enforcement,
not semantic authority transfer
```

They block model execution when required identity/continuity context is missing or failed. They do not grant Capability Track ownership over Identity Continuity authority, do not mutate durable identity/continuity state, and do not redefine the Identity Continuity Track semantic model.

## 5. Regression Evidence

Final scoped verification performed at candidate `a8d1cf3eaaf9aabfc8ba632f3648f5a0053a7be5`:

```text
CRB focused tests                  14 passed
Typed execution + invariants       35 passed
Capability regression              136 passed, 11 xfailed
Capability/runtime lineage suite   212 passed, 6 skipped, 26 xfailed
```

Full-repo failures were observed in broader environment-dependent suites, but are not attributed to CRB-PRE-P1 or used as a claim of full-repo regression cleanliness in this record.

## 6. Owner Aggregate Admission

Owner accepts the aggregate lineage `698b811..a8d1cf3` as the next main-admissible Julia Core capability/runtime baseline.

This admission does not retroactively redefine the phase status of individual historical commits.

## 7. Main Mutation Status

```text
Main admission                   OWNER APPROVED
Main ref mutation                NOT PERFORMED BY THIS COMMIT
Next allowed action              governed fast-forward after final owner review
```

After this record is reviewed and accepted, `main` may be fast-forwarded / governed-integrated to:

```text
a8d1cf3eaaf9aabfc8ba632f3648f5a0053a7be5
```

Then `feature/pre-p4-no-fallback` should be treated as historical / merged, not as the next active development root. CRB-P1 should start from `main @ a8d1cf3` in a disposable worktree.

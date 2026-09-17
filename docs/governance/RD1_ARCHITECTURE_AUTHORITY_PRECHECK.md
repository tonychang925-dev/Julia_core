# RD1 Architecture / Authority Precheck

**Status:** ACTIVE CONTROL PLANE AFTER CONSOLIDATION MERGE

The consolidated review model has exactly three composite gates:

```text
GATE A — AUTHORITY
GATE B — SEMANTIC ATOMICITY + PERMISSION
GATE C — CANDIDATE EVIDENCE
```

Underlying mechanical checks may remain distributed, but reviewers reason through A/B/C only.

## Gate A — Authority

Verify:

```text
A1 effective frozen architecture answers the requirement
A2 Rule11 classification is correct
A3 ARCHITECTURE_DELTA = NONE
A4 target belongs to CURRENT_PHASE
A5 FROZEN_AUTHORITY_BINDING is complete
A6 control-plane compatibility version is current/revalidated
```

Rule11-D is legal only with positive proof:

```text
D MUST BE POSITIVELY PROVEN
D MUST NOT BE REACHED BY ELIMINATION
```

If Gate A fails:

```text
REVIEW = STOP
```

## Gate B — Semantic Atomicity + Permission

Verify:

```text
B1 task closes exactly one invariant
B2 merge leaves main architecturally and semantically valid
B3 no half-new / half-old truth is created
B4 all AUTHORIZED_PATHS belong to the invariant closure
B5 Permission Matrix is exact/default-deny
B6 RESIDUAL_ARCHITECTURE_DECISIONS = 0
B7 RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
```

```text
ATOMICITY_FAIL != SPLIT_SMALLER
```

The correct response may be to recompose a too-narrow task more completely.

`ONE_REPO = PREFERRED`; cross-repo atoms are exceptional and require frozen dependency, exact per-repo bases/scopes, exact coordination order, valid intermediate states or an already-authorized coordinated cutover, and `ARCHITECTURE_DELTA = NONE`.

If Gate B fails:

```text
TASK_CARD_NOT_READY
→ REVIEW STOP
```

## Gate C — Candidate Evidence

Run only after A and B pass.

Verify:

```text
exact candidate SHA
exact base SHA
exact diff
changed paths
required behavior
forbidden behavior
tests/raw output
typed failures
absence of fallback
architecture invariants
permission compliance
```

```text
TEST_PASS != ARCHITECTURE_PASS
PASS_CLAIM = SIGNAL_ONLY
EXACT_ARTIFACT = TRUTH
```

If Gate C passes:

```text
CANDIDATE_REVIEW_COMPLETE = YES
```

Possible Owner merge authorization is a separate lifecycle step.

## Reviewer stop condition

Reviewer verifies exactly:

```text
R1 frozen architecture compliance
R2 semantic atomicity / valid merge state
R3 permission and scope compliance
R4 acceptance evidence
```

When all PASS:

```text
REVIEW_COMPLETE = YES
```

Permanent law:

```text
NEW EVIDENCE MAY REOPEN REVIEW
NEW OPINION MAY NOT

DISCOVER_MORE != BLOCK_MORE
FUTURE_CONCERN != CURRENT_BLOCKER
```

Concrete evidence that may reopen includes frozen-authority violation, scope violation, permission violation, invalid merge state, and false/missing candidate evidence.

Theoretical future risk, cleaner-design preference, optional refactor, or hypothetical production concern cannot reopen a completed review by themselves.

## Merge closure

After merge authorization and merge, closure still requires exact merged state verification and task-branch cleanup under the Development Constitution. Review completion does not itself authorize merge.

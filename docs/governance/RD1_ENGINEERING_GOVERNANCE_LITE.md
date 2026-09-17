# RD1-V1 Engineering Governance Lite

**Date:** 2026-09-17  
**Owner:** Tony  
**Status:** ACTIVE / OWNER APPROVED

## 1. Source of truth

```text
ONE TRUNK
ONE CURRENT HEAD
ONE TASK BASE
MERGE OR DELETE
```

For each repository:

```text
main = current development truth
```

Historical branches and old candidates are reference/evidence only.

## 2. Exact base

Every implementation task binds:

```text
REPO / REPOS
BASE_SHA / BASE_SHAS
```

If a relevant main changes before implementation starts, rebind/rebase or stop.

## 3. Minimal task card

A normal engineering task needs only:

```text
TASK_ID
REPO / REPOS
BASE_SHA / BASE_SHAS
GOAL
ALLOWED_PATHS
FORBIDDEN_PATHS
ACCEPTANCE_TESTS
EXPECTED_EVIDENCE
```

Optional fields are added only when genuinely needed.

Do not repeat the architecture constitution in every task card.

## 4. Architecture binding

All tasks inherit `docs/architecture/RD1_V1_ARCHITECTURE_CONSTITUTION_LITE.md`.

A reviewer blocks only for concrete evidence of:

```text
architecture violation
scope violation
false/missing acceptance evidence
base drift
```

Implementation preference or wording preference is not a blocker.

## 5. Function calls are not governance events

Ordinary Julia READ_ONLY tool/function calls do not require Owner approval, task cards, cross-repo permission matrices, or governance adjudication.

Runtime authorization is product code, not project governance.

## 6. Cross-repository work

Cross-repo work is allowed when the product slice genuinely requires it.

A coordinated task states:

```text
repos
exact bases
per-repo write paths
integration order
acceptance test
```

Forbidden:

```text
unbounded mutation
private-boundary penetration
silent ownership changes
dependency reversal
hidden fallback/synthetic success
```

Cross-repo coordination itself is not an architecture violation.

## 7. Review discipline

```text
Architecture review:
Does this violate the Architecture Constitution Lite?

Code review:
Does the implementation satisfy the task and tests?

Project review:
Did the feature advance the product?

Release review:
Is this exact build ready to ship?
```

These roles must not be conflated.

## 8. Evidence

Candidate evidence should be proportional to risk.

Typical evidence:

```text
candidate SHA
changed paths
tests
key runtime trace
no-fallback proof where relevant
```

Do not require broad constitutional proof for a narrow engineering task.

## 9. Merge

```text
PASS != MERGED
```

Merge remains an explicit lifecycle action.

After merge, verify main and delete the task branch when practical.

## 10. Governance change threshold

Do not create a new governance rule merely because a task was ambiguous, a reviewer prefers another wording, an implementation detail was unspecified, or a future hypothetical concern exists.

Governance changes require repeated concrete engineering evidence that the current architecture/governance cannot safely support the product.

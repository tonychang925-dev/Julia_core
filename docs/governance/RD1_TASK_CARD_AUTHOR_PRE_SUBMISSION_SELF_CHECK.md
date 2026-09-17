# RD1 Task Card Author Pre-Submission Self-Check

**Status:** ACTIVE CONTROL PLANE AFTER CONSOLIDATION MERGE  
**Applies to:** all RD1 task-card authors across Julia Core / Julia-AI-Assistant / Market Brain.

## 1. Permanent law

The task author is the first-line governance reviewer.

```text
TASK_CARD_DRAFT
→ AUTHORITY CHECK
→ SEMANTIC ATOMICITY CHECK
→ PERMISSION CHECK
→ EVIDENCE READINESS CHECK
→ PASS?
   NO  → REWORK / DO NOT SUBMIT
   YES → ELIGIBLE FOR INDEPENDENT REVIEW
```

```text
NO_SELF_CHECK_EVIDENCE = NO_TASK_SUBMISSION
SELF_CHECK_PASS != OWNER_APPROVAL
SELF_CHECK_PASS != IMPLEMENTATION_AUTHORIZATION
SELF_CHECK_PASS != MERGE_AUTHORIZATION
```

## 2. Check A — Authority

Verify mechanically:

```text
CURRENT_CONSTITUTION
CURRENT_RULE12
CURRENT_CONSOLIDATION_AMENDMENT
CURRENT_CONTROL_PLANE_COMPATIBILITY_VERSION
GOVERNING_FROZEN_DOCUMENTS
CURRENT_PHASE
REPO
CURRENT_TRUNK_SHA
PROPOSED_BASE_SHA
TARGET_BRANCH
```

Task must declare:

```text
RULE11_CLASSIFICATION
FROZEN_AUTHORITY_BINDING
ARCHITECTURE_DELTA = NONE
```

Rule11-D is legal only when positively proven by a true effective-authority conflict or a current-phase architecture question with no frozen answer after exhaustive trace.

## 3. Check B — Semantic atomicity

Author must prove:

```text
SEMANTIC_ATOM = ONE INVARIANT CLOSURE
```

and answer:

```text
IF THIS TASK ALONE MERGES,
IS MAIN STILL ARCHITECTURALLY AND SEMANTICALLY VALID?
```

Required:

```text
VALID_MERGE_END_STATE = explicit
```

Fail if the task would create half-new/half-old truth such as public contract != runtime contract, public export != provider runtime, validity state without validation mechanism, or schema producer mismatch.

```text
ATOMICITY_FAIL != SPLIT_SMALLER
```

The correct correction may be to recompose the task more completely.

## 4. Check C — Permission

Verify exactly one `AGENT_EXECUTION_PERMISSION_MATRIX`.

Required:

```text
PERMISSION_MODEL = DEFAULT_DENY
PERMISSION_REPOSITORY == REPO
PERMISSION_BASE_SHA == BASE_SHA
PERMISSION_TARGET_BRANCH == TARGET_BRANCH
WRITE_SCOPE ⊆ AUTHORIZED_PATHS
ARCHITECTURE_MUTATION = DENY
CROSS_BOUNDARY_SEMANTIC_DECISION = DENY
MERGE = DENY
RELEASE = DENY
DEPLOY = DENY
PRODUCTION_MUTATION = DENY
FALLBACK = DENY
SYNTHETIC_SUCCESS = DENY
FUTURE_PHASE_SCOPE = DENY
```

`WRITE_SCOPE` is a permission boundary, not a task-size metric.

## 5. Check D — Control-plane compatibility

Verify:

```text
CONTROL_PLANE_COMPATIBILITY_VERSION
CONTROL_PLANE_SHA_OBSERVED
```

and append self-check evidence:

```text
CONTROL_PLANE_AUTHORITY_REPO
= tonychang925-dev/Julia_core

SELF_CHECK_CONTROL_PLANE_COMPATIBILITY_VERSION
= <integer>

SELF_CHECK_CONTROL_PLANE_SHA
= <exact observed SHA>

CONTROL_PLANE_FRESHNESS_CHECK
= PASS
```

Exact SHA drift alone does not invalidate the task if the compatibility version is unchanged.

## 6. Check E — Residual decisions

Question:

```text
IF AN IMPLEMENTATION AGENT RECEIVES ONLY THIS TASK CARD,
WILL IT STILL NEED TO MAKE ANY UNFROZEN ARCHITECTURE OR CONTRACT-SEMANTIC DECISION?
```

Required:

```text
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
```

## 7. Check F — Cross-boundary tasks

Only when:

```text
TASK_TYPE = CROSS_BOUNDARY
```

verify frozen mappings for source/target contracts, fields, status, failure, provenance, authority transfer, malformed/unknown behavior, and lifecycle ownership.

The author must not rely on parser keyword inference.

## 8. Check G — Acceptance evidence

Verify the task requires exact candidate SHA, exact changed-path proof, focused tests/raw output, architecture/scope invariants, and absence of forbidden fallback.

```text
TEST_PASS != ARCHITECTURE_PASS
```

## 9. Mandatory output block

Every submitted coding task card MUST contain:

```text
TASK_CARD_AUTHOR_SELF_CHECK
AUTHOR_ROLE
TASK_ID
TASK_CARD_VERSION
AUTHORITY_SOURCE_FILES_CHECKED
CURRENT_MAIN_SHAS
AUTHORITY_GATE = PASS
SEMANTIC_ATOMICITY_GATE = PASS
PERMISSION_GATE = PASS
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
SELF_CHECK_RESULT = PASS
READY_FOR_SUBMISSION = YES
```

Unknown/unresolved/not-checked values are failures, never implicit PASS.

## 10. Independent review remains mandatory

```text
SELF_CHECK_CLAIM = SIGNAL_ONLY
SELF_CHECK_EVIDENCE = MUST_BE_REVERIFIED
```

Independent review verifies frozen architecture, semantic atomicity, permission/scope, and acceptance evidence.

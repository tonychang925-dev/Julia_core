# RD1 Control-Plane Consolidation Constitutional Amendment v1.1

**Status:** OWNER-AUTHORIZED CONSTITUTIONAL EXECUTION CONSOLIDATION — PENDING MERGE ACTIVATION  
**Rule number:** NONE. This document does not create Rule 13.  
**Governing plan:** `RD1_V1_Control_Plane_Consolidation_and_Semantic_Atomicity_Plan_v1.1.md`

## Constitutional purpose

This amendment consolidates the operational enforcement of existing Rule 11 and Rule 12. It does not weaken either rule and does not create new architecture authority.

Permanent law:

```text
AGENT MAY IMPLEMENT FROZEN TRUTH
AGENT MAY NOT INVENT TRUTH

NO_ARCHITECTURE_COMPLETION_BY_AGENT_INFERENCE = YES

EXACT IMPLEMENTATION BASE_SHA = STRICT

AGENT EXECUTION PERMISSION = DEFAULT DENY
```

## 1. Governance compatibility

```text
CONTROL_PLANE_COMPATIBILITY_VERSION
= canonical task-contract compatibility identity

CONTROL_PLANE_SHA_OBSERVED
= evidence only
```

Canonical source:

```text
docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md
```

```text
NON_BREAKING_CONTROL_PLANE_SHA_DRIFT
→ MUST NOT BY ITSELF INVALIDATE A TASK

COMPATIBILITY_VERSION_CHANGE
→ REVALIDATION REQUIRED
→ NOT AUTOMATIC INVALIDATION
```

Exact target-repository BASE_SHA remains strict and independent.

## 2. Governance change classification

Every normative governance PR declares:

```text
CONTROL_PLANE_COMPATIBILITY_IMPACT
= NONE | BREAKING
```

```text
BREAKING → version increments exactly once
NONE → version does not increment
```

Independent review validates the claim.

## 3. Rule 11 D positive proof

```text
D = TRUE
IFF
  effective frozen authorities genuinely conflict after scope-aware precedence
  OR
  a required current-phase architecture question has no frozen answer after exhaustive trace
```

```text
D MUST BE POSITIVELY PROVEN
D MUST NOT BE REACHED BY ELIMINATION
UNKNOWN != D
HARD_TO_IMPLEMENT != D
CURRENT_MAIN_ABSENCE != D
```

## 4. Rule 12 operational proof

Ordinary implementation tasks MUST declare:

```text
ARCHITECTURE_DELTA
= NONE

FROZEN_AUTHORITY_BINDING
= <exact effective frozen authority>
```

If `ARCHITECTURE_DELTA != NONE`, the work is not a normal implementation task and must use the constitutional architecture-amendment/refreeze path.

The former detailed NEW_* zero counters remain reviewer checklist dimensions but are not mandatory repetitive task-card syntax after activation of this amendment.

## 5. Semantic atomicity

```text
SEMANTIC_ATOM
= ONE INVARIANT CLOSURE

SEMANTIC_ATOM
!= WHOLE FEATURE
!= WHOLE MILESTONE
!= WHOLE RC PHASE
```

```text
TASK_SIZE
= SMALLEST SEMANTICALLY COMPLETE CHANGE
  THAT CAN MERGE WITHOUT CREATING AN INVALID INTERMEDIATE STATE
```

```text
TASK_SIZE != FILE_COUNT
ATOMICITY_FAIL != SPLIT_SMALLER
```

A task may include all files required to close one invariant. `ONE_REPO = PREFERRED`, not absolute. Cross-repo atoms are exceptional and require frozen dependency, exact per-repo bases/scopes, coordinated ordering, valid intermediate states or an already-authorized coordinated cutover, and `ARCHITECTURE_DELTA = NONE`.

## 6. Permission Matrix

Default-deny semantics remain mandatory. Permission Matrix controls authority, not task size.

```text
ARCHITECTURE_MUTATION = DENY
CROSS_BOUNDARY_SEMANTIC_DECISION = DENY
MERGE = DENY
RELEASE = DENY
DEPLOY = DENY
FALLBACK = DENY
SYNTHETIC_SUCCESS = DENY
FUTURE_PHASE_SCOPE = DENY
```

## 7. Three composite gates

```text
GATE A
= AUTHORITY

GATE B
= SEMANTIC ATOMICITY + PERMISSION

GATE C
= CANDIDATE EVIDENCE
```

The underlying mechanical checks may remain distributed, but no additional conceptual gate layer is created without a future explicit constitutional amendment.

## 8. Reviewer stop condition

Reviewer verifies only:

```text
R1 frozen architecture compliance
R2 semantic atomicity / valid merge state
R3 permission and scope compliance
R4 acceptance evidence
```

If all PASS:

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

## 9. Parser responsibility

Parser enforces declarations mechanically and MUST NOT infer architecture from prose keywords.

Tasks declare:

```text
TASK_TYPE
= STANDARD | CROSS_BOUNDARY
```

Only `TASK_TYPE = CROSS_BOUNDARY` activates mandatory frozen mapping fields.

```text
PARSER = GOVERNANCE_ENFORCER
PARSER != ARCHITECTURE_LAW
```

## 10. Plan supersession and activation boundary

```text
RD1_V1_Control_Plane_Consolidation_and_Semantic_Atomicity_Plan_v1.1
= CURRENT CANONICAL PLAN

v1.0
= SUPERSEDED
= HISTORICAL REFERENCE ONLY
= NOT ACTIVE AUTHORITY
```

The plan supersession does not by itself replace currently active mechanics before this consolidation implementation merges.

```text
BEFORE THIS PR MERGES
→ existing active mechanics remain in force

AT THIS PR MERGE
→ consolidated v1.1 mechanics become active atomically
```

No merge/release/deploy authority is granted by this amendment itself.

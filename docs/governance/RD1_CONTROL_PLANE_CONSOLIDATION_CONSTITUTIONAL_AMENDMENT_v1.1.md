# RD1 Control Plane Consolidation Constitutional Amendment v1.1

**Status:** OWNER-APPROVED DIRECTION / ACTIVE ON MERGE  
**Authority class:** Constitutional execution amendment; no new numbered Rule is created.  
**Scope:** RD1 governance execution model across Julia Core / Julia-AI-Assistant / Market Brain.  

```text
NEW_RULE_NUMBER = NO
RULE11 = PRESERVED
RULE12 = PRESERVED
PERMISSION_MATRIX = PRESERVED
EXACT_TASK_BASE_SHA = PRESERVED
```

## 1. Canonical plan supersession

```text
RD1_V1_Control_Plane_Consolidation_and_Semantic_Atomicity_Plan_v1.1
= CURRENT CANONICAL PLAN

SUPERSEDES
= v1.0

SUPERSESSION_SCOPE
= FULL DOCUMENT

ACTIVE_PLAN_VERSION
= v1.1

OLDER_VERSION_USAGE
= EVIDENCE_ONLY

v1.0
= SUPERSEDED
= HISTORICAL REFERENCE ONLY
= NOT ACTIVE AUTHORITY
```

This supersession applies only to the consolidation plan version. Existing active control-plane mechanics remain in force until the implementation carrying this amendment is reviewed and merged.

```text
PLAN_APPROVAL != CONTROL_PLANE_MIGRATION_COMPLETE
ACTIVE_MECHANICS_REMAIN_CURRENT_UNTIL_MERGE = YES
```

## 2. Governance expansion freeze

```text
GOVERNANCE_EXPANSION = FROZEN_BY_DEFAULT
NO_NEW_CONSTITUTION_RULE = DEFAULT
NO_NEW_META_GATE = DEFAULT
NO_NEW_TASK_CARD_LAYER = DEFAULT
NO_NEW_PARSER_LAYER = DEFAULT
```

A new governance layer requires demonstrated inability of Rule11/Rule12 plus existing enforcement to express the failure mode.

## 3. Control-plane compatibility

Governance compatibility is versioned, not coupled to every Julia Core SHA.

```text
CANONICAL_COMPATIBILITY_SOURCE
= docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md

CONTROL_PLANE_COMPATIBILITY_VERSION
= normative task-contract compatibility identity

CONTROL_PLANE_SHA_OBSERVED
= evidence only
```

The compatibility file contains no `EFFECTIVE_FROM_SHA`. Git history supplies SHA → version mapping.

Every normative governance change declares exactly one:

```text
CONTROL_PLANE_COMPATIBILITY_IMPACT
= NONE
| BREAKING
```

```text
BREAKING → COMPATIBILITY_VERSION MUST INCREMENT
NONE     → COMPATIBILITY_VERSION MUST NOT INCREMENT
```

The author declaration is a claim; reviewer verification remains mandatory.

## 4. Freshness semantics

Task implementation identity and governance compatibility are independent.

```text
TASK_BASE_SHA
= exact implementation identity
= STRICT

CONTROL_PLANE_COMPATIBILITY_VERSION
= governance compatibility identity
```

Non-breaking control-plane SHA movement does not invalidate an otherwise compatible task.

```text
CONTROL_PLANE_SHA_CHANGED
+ COMPATIBILITY_VERSION_UNCHANGED
→ TASK MAY REMAIN VALID
```

A compatibility-version change requires compatibility revalidation, not automatic invalidation.

```text
VERSION_CHANGED
→ REVALIDATE

NOT_APPLICABLE
→ REVALIDATED / CONTINUE

APPLICABLE
→ REBIND_REQUIRED
```

Compatibility is revalidated at the authority transitions that advance work:

```text
OWNER_APPROVAL
IMPLEMENTATION_START
MERGE_REVIEW
```

## 5. Rule 12 operational simplification

Rule 12 constitutional meaning remains unchanged:

```text
NO_ARCHITECTURE_COMPLETION_BY_AGENT_INFERENCE = YES
```

Normal implementation tasks declare:

```text
ARCHITECTURE_DELTA = NONE
FROZEN_AUTHORITY_BINDING = <exact effective frozen sources>
```

If `ARCHITECTURE_DELTA != NONE`, the work is not an ordinary implementation task and must use the architecture amendment/refreeze path.

Detailed `NEW_*_COUNT = 0` fields become reviewer checklist dimensions rather than mandatory task-card boilerplate.

## 6. Rule 11 D positive proof

```text
A = required implementation missing under frozen architecture
B = existing implementation contradicts frozen architecture
C = concern belongs to a later frozen phase
```

`D` is true only when positively proven:

```text
1. two effective frozen authorities genuinely conflict after scope-aware precedence
OR
2. a required current-phase architecture question has no effective frozen answer after exhaustive authority trace
```

```text
D MUST BE POSITIVELY PROVEN
D MUST NOT BE REACHED BY ELIMINATION
UNKNOWN != D
HARD_TO_IMPLEMENT != D
CURRENT_MAIN_ABSENCE != D
```

## 7. Semantic atomicity

```text
SEMANTIC_ATOM
= ONE INVARIANT CLOSURE

SEMANTIC_ATOM != WHOLE FEATURE
SEMANTIC_ATOM != WHOLE MILESTONE
SEMANTIC_ATOM != WHOLE RC PHASE
```

Task size is:

```text
SMALLEST SEMANTICALLY COMPLETE CHANGE
THAT CAN MERGE WITHOUT CREATING AN INVALID INTERMEDIATE STATE
```

```text
TASK_SIZE != FILE_COUNT
TASK_SIZE != LINE_COUNT
TASK_SIZE != MINIMUM_DIFF
```

Atomicity question:

```text
IF THIS TASK ALONE MERGES,
IS MAIN STILL ARCHITECTURALLY AND SEMANTICALLY VALID?
```

If no, do not split at that boundary.

```text
ATOMICITY_FAIL != SPLIT_SMALLER
```

A task may need recomposition to close the invariant.

## 8. Repository scope

```text
ONE_REPO = PREFERRED
CROSS_REPO_ATOM = EXCEPTION, NOT DEFAULT
```

A cross-repo atom is legal only when a frozen dependency relationship exists, every repo has exact BASE_SHA and WRITE_SCOPE, execution/merge/cutover order is exact, all intermediate states are valid or an already-authorized coordinated cutover exists, and `ARCHITECTURE_DELTA = NONE`.

## 9. Permission Matrix

The Agent Execution Permission Matrix remains default-deny and controls authority, not task size.

```text
PERMISSION_MODEL = DEFAULT_DENY
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

```text
WRITE_SCOPE != TASK_SIZE_LIMIT
```

## 10. Three composite gates

```text
GATE_A = AUTHORITY
GATE_B = SEMANTIC_ATOMICITY + PERMISSION
GATE_C = CANDIDATE_EVIDENCE
```

Gate A verifies frozen authority, Rule11 classification, `ARCHITECTURE_DELTA = NONE`, phase, and frozen-source binding.

Gate B verifies one invariant closure, valid merge end-state, absence of half-new/half-old truth, necessary paths, exact permission bounds, and zero residual unfrozen architecture decisions.

Gate C verifies exact candidate SHA/base/diff/paths, required and forbidden behavior, tests/evidence, absence of fallback, architecture invariants, and permission compliance.

## 11. Reviewer stop condition

Reviewer verifies exactly:

```text
R1 = frozen architecture compliance
R2 = semantic atomicity
R3 = authorized scope / permission compliance
R4 = acceptance evidence
```

When all pass:

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

unless an effective frozen dependency gate explicitly says otherwise.

## 12. Parser responsibility

Parser validates explicit declarations and mechanical identity. It does not infer architecture from prose keywords.

Task cards explicitly declare:

```text
TASK_TYPE = STANDARD | CROSS_BOUNDARY
```

Only `TASK_TYPE = CROSS_BOUNDARY` triggers mandatory cross-boundary semantic mapping fields.

```text
PARSER = GOVERNANCE_ENFORCER
PARSER != ARCHITECTURE_LAW
```

## 13. Simplified normal task-card schema

```text
TASK_ID
TASK_TYPE
REPO
BASE_SHA
TARGET_BRANCH
CONTROL_PLANE_COMPATIBILITY_VERSION
CONTROL_PLANE_SHA_OBSERVED
CURRENT_PHASE
RULE11_CLASSIFICATION
FROZEN_AUTHORITY_BINDING
ARCHITECTURE_DELTA = NONE
TARGET_REQUIREMENT
SEMANTIC_ATOM
VALID_MERGE_END_STATE
DEFERRED_FINDINGS
AUTHORIZED_PATHS
FORBIDDEN_PATHS
REQUIRED_BEHAVIOR
FORBIDDEN_BEHAVIOR
AGENT_EXECUTION_PERMISSION_MATRIX
ACCEPTANCE_EVIDENCE
TASK_AUTHOR_SELF_CHECK
```

Self-check minimum result:

```text
AUTHORITY_GATE = PASS
SEMANTIC_ATOMICITY_GATE = PASS
PERMISSION_GATE = PASS
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
SELF_CHECK_RESULT = PASS
READY_FOR_SUBMISSION = YES
```

## 14. Authorization separation remains unchanged

```text
CONTROL_PLANE_APPROVAL != CODING_AUTHORIZATION
TASK_APPROVAL != MERGE_AUTHORIZATION
MERGE_AUTHORIZATION != RELEASE
RELEASE != DEPLOY
DEPLOY != PRODUCTION_ACCEPTANCE
```

## 15. Core principles

```text
SEMANTIC_ATOMICITY > MINIMUM_DIFF_SIZE
MERGEABLE_VALID_STATE > ARTIFICIALLY_SMALL_TASK
PERMISSION_MATRIX_CONTROLS_AUTHORITY_NOT_TASK_SIZE
RULE12_PREVENTS_ARCHITECTURE_INVENTION_NOT_NORMAL_IMPLEMENTATION
AGENT MAY IMPLEMENT FROZEN TRUTH
AGENT MAY NOT INVENT TRUTH
```

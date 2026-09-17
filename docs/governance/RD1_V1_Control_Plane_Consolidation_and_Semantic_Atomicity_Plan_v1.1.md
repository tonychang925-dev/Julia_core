# RD1-V1 Control Plane Consolidation & Semantic Atomicity Plan v1.1

**Status:** CURRENT CANONICAL CONSOLIDATION PLAN  
**Scope:** Julia Core / Julia-AI-Assistant / Market Brain RD1 engineering governance  
**Plan authority only:** this plan defines the target consolidated governance model; active mechanics transition only when the consolidation implementation PR is merged.

```text
SUPERSEDES
= RD1_V1_Control_Plane_Consolidation_and_Semantic_Atomicity_Plan_v1.0

SUPERSESSION_SCOPE
= FULL DOCUMENT

ACTIVE_PLAN_VERSION
= v1.1

OLDER_VERSION_USAGE
= EVIDENCE_ONLY

v1.0
= SUPERSEDED
= HISTORICAL_REFERENCE_ONLY
= NOT_ACTIVE_AUTHORITY
```

## 1. Consolidation objective

RD1 governance must satisfy both:

```text
AGENT_ARCHITECTURE_FREEDOM = NO
AND
NORMAL_IMPLEMENTATION_MUST_REMAIN_PRACTICABLE = YES
```

No Rule 13 is created. The consolidation preserves Rule 11, Rule 12, frozen architecture precedence, default-deny execution permissions, exact implementation BASE_SHA, Owner authorization separation, and independent review.

```text
GOVERNANCE_EXPANSION
= FROZEN_BY_DEFAULT

NO_NEW_CONSTITUTION_RULE
NO_NEW_META_GATE
NO_NEW_TASK_CARD_LAYER
NO_NEW_PARSER_LAYER
```

## 2. Control-plane compatibility version

Canonical compatibility source:

```text
CANONICAL_COMPATIBILITY_SOURCE
= docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md
```

Normative payload:

```text
CONTROL_PLANE_COMPATIBILITY_VERSION
= <integer>
```

Exact control-plane SHA remains audit evidence only:

```text
CONTROL_PLANE_SHA_OBSERVED
= <exact Julia_core SHA>
```

```text
CONTROL_PLANE_COMPATIBILITY_VERSION
= task-contract compatibility identity

CONTROL_PLANE_SHA_OBSERVED
= evidence only
```

The compatibility source MUST NOT contain `EFFECTIVE_FROM_SHA`. Git history itself maps SHA to version:

```text
git show <SHA>:docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md
→ CONTROL_PLANE_COMPATIBILITY_VERSION = N
```

Every normative governance PR declares:

```text
CONTROL_PLANE_COMPATIBILITY_IMPACT
= NONE | BREAKING
```

```text
BREAKING → version increments exactly once
NONE     → version does not increment
```

The author declaration is a claim; independent review verifies whether it is truthful.

Initial transition:

```text
LEGACY_CONTROL_PLANE = UNVERSIONED
CONSOLIDATED_CONTROL_PLANE = CONTROL_PLANE_COMPATIBILITY_VERSION 1
INITIAL_CONSOLIDATION_IMPACT = BREAKING
```

## 3. Freshness semantics

Implementation identity and governance compatibility are separate:

```text
TASK_BASE_SHA
= exact implementation identity

CONTROL_PLANE_COMPATIBILITY_VERSION
= governance compatibility identity
```

Task BASE_SHA remains strict.

Control-plane SHA drift alone no longer invalidates a task when compatibility version is unchanged:

```text
CONTROL_PLANE_SHA_CHANGED
+ COMPATIBILITY_VERSION_UNCHANGED
→ TASK_REMAINS_GOVERNANCE_COMPATIBLE
```

When compatibility version changes:

```text
COMPATIBILITY_VERSION_CHANGED
→ COMPATIBILITY_REVALIDATION_REQUIRED
```

but:

```text
COMPATIBILITY_VERSION_CHANGED
!= AUTOMATIC_TASK_INVALIDATION
```

```text
change not applicable to task
→ REVALIDATED
→ CONTINUE

change applicable to task
→ REBIND_REQUIRED
```

Compatibility is revalidated at the authority transitions that advance work:

```text
OWNER_APPROVAL
IMPLEMENTATION_START
MERGE_REVIEW
```

## 4. Rule 11 positive-proof model

```text
A
= required implementation missing under effective frozen architecture

B
= existing implementation contradicts effective frozen architecture

C
= concern belongs to a later frozen phase

D
= TRUE iff:
  1. two effective frozen authorities genuinely conflict after scope-aware precedence
  OR
  2. a required current-phase architecture question has no frozen answer after exhaustive authority trace
```

Permanent law:

```text
D MUST BE POSITIVELY PROVEN
D MUST NOT BE REACHED BY ELIMINATION
UNKNOWN != D
HARD_TO_IMPLEMENT != D
CURRENT_MAIN_ABSENCE != D
```

## 5. Rule 12 operational consolidation

Rule 12 constitutional meaning remains unchanged:

```text
NO_ARCHITECTURE_COMPLETION_BY_AGENT_INFERENCE = YES
```

Normal implementation tasks use the simplified mandatory proof:

```text
ARCHITECTURE_DELTA
= NONE

FROZEN_AUTHORITY_BINDING
= <exact effective frozen source / clauses>
```

If:

```text
ARCHITECTURE_DELTA != NONE
```

then:

```text
NOT_AN_IMPLEMENTATION_TASK
→ ARCHITECTURE_AMENDMENT_PATH
```

The former NEW_* zero counters remain reviewer checklist dimensions, not mandatory repetitive task-card syntax.

## 6. Semantic atomicity

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
TASK_SIZE != LINE_COUNT
TASK_SIZE != MINIMUM_DIFF
```

Atomicity test:

```text
IF THIS TASK ALONE MERGES,
IS MAIN STILL ARCHITECTURALLY AND SEMANTICALLY VALID?
```

If NO, do not split at that boundary.

```text
ATOMICITY_FAIL
!= SPLIT_SMALLER

ATOMICITY_FAIL
→ MAY REQUIRE RECOMPOSING THE TASK MORE COMPLETELY
```

Half-new/half-old states are forbidden, including:

```text
PUBLIC_CONTRACT != RUNTIME_CONTRACT
PUBLIC_EXPORT != PROVIDER_RUNTIME
VALIDITY_FLAG != VALIDATION_MECHANISM
NEW_SCHEMA != PRODUCER_SCHEMA
NEW_RESULT_TYPE != ACTIVE_RETURN_TYPE
```

## 7. Repository scope

```text
ONE_REPO
= PREFERRED
```

Cross-repo semantic atoms are exceptional and legal only when:

```text
frozen dependency relationship exists
AND exact per-repo BASE_SHA exists
AND exact per-repo WRITE_SCOPE exists
AND exact execution / merge / cutover ordering exists
AND every intermediate state is valid
OR an already-authorized coordinated cutover exists
AND ARCHITECTURE_DELTA = NONE
```

## 8. Permission Matrix

Default deny remains mandatory:

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
WRITE_SCOPE
!= TASK_SIZE_LIMIT
```

Write scope may include every path required to close one semantic atom.

## 9. Three composite gates

### Gate A — Authority

Verify:

```text
frozen architecture answer
Rule11 classification
ARCHITECTURE_DELTA = NONE
CURRENT_PHASE
FROZEN_AUTHORITY_BINDING
```

### Gate B — Semantic Atomicity + Permission

Verify:

```text
one invariant closure
valid merge end-state
no half-new / half-old truth
authorized paths belong to the atom
Permission Matrix exact
zero residual architecture decisions
```

### Gate C — Candidate Evidence

Verify:

```text
exact candidate SHA
exact base SHA
exact diff
changed paths
required / forbidden behavior
tests
architecture invariants
permission compliance
```

```text
TEST_PASS != ARCHITECTURE_PASS
PASS_CLAIM = SIGNAL_ONLY
EXACT_ARTIFACT = TRUTH
```

## 10. Reviewer stop condition

Reviewer answers exactly:

```text
R1. frozen architecture compliant?
R2. semantic atom complete and merge-valid?
R3. permission/scope compliant?
R4. acceptance evidence sufficient?
```

If all PASS:

```text
REVIEW_COMPLETE = YES
```

Permanent rule:

```text
NEW EVIDENCE MAY REOPEN REVIEW.
NEW OPINION MAY NOT.

DISCOVER_MORE != BLOCK_MORE
FUTURE_CONCERN != CURRENT_BLOCKER
```

## 11. Parser responsibility

Parser validates explicit declarations; it does not infer architecture.

Task cards declare:

```text
TASK_TYPE
= STANDARD | CROSS_BOUNDARY
```

Only `TASK_TYPE = CROSS_BOUNDARY` triggers mandatory frozen semantic mappings.

Parser mechanically checks identity, exact BASE_SHA format/currentness where applicable, compatibility version, `ARCHITECTURE_DELTA = NONE`, frozen authority binding, semantic atom/end-state declarations, Permission Matrix, self-check PASS, and readiness.

Parser MUST NOT decide architecture truth, ownership truth, dependency-direction truth, semantic mapping correctness, or task decomposition correctness.

## 12. Simplified task-card schema

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
TASK_CARD_AUTHOR_SELF_CHECK
```

Recommended author self-check:

```text
AUTHORITY_GATE = PASS
SEMANTIC_ATOMICITY_GATE = PASS
PERMISSION_GATE = PASS
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
SELF_CHECK_RESULT = PASS
READY_FOR_SUBMISSION = YES
```

## 13. Plan vs active mechanics

This plan supersedes v1.0 immediately as the canonical consolidation plan.

It does **not** retroactively replace active Rule11/Rule12/Permission Matrix/freshness/parser mechanics before the consolidation implementation merge.

```text
PLAN VERSION
v1.0 → SUPERSEDED BY v1.1

ACTIVE CONTROL-PLANE MECHANICS
= CURRENT UNTIL CONSOLIDATION IMPLEMENTATION MERGES
```

After the consolidation implementation merge:

```text
ACTIVE CONTROL PLANE
→ v1.1 CONSOLIDATED MODEL
```

## 14. Post-consolidation engineering sequence

```text
STOP M-00A VERSION CHURN

NEXT ENGINEERING TASK
= RD1-RC4-M-00
  Canonical Market Result Closure
```

The Market result closure must finish one invariant:

```text
MARKET_PUBLIC_CONTRACT_TRUTH
=
MARKET_PROVIDER_RUNTIME_TRUTH
=
PROVENANCE_VALIDITY_TRUTH
=
PACKAGE_PUBLIC_EXPORT_TRUTH
```

Only after M-00 closes should the next Core compatibility task begin.

## 15. Final permanent principles

```text
NO MORE GOVERNANCE EXPANSION BY DEFAULT
NO MORE NON-BREAKING SHA-DRIFT TASK-CARD CHURN
CONTROL_PLANE_COMPATIBILITY_VERSION > CONTROL_PLANE_SHA FOR GOVERNANCE COMPATIBILITY
EXACT TARGET BASE_SHA REMAINS STRICT
SEMANTIC ATOMICITY > MINIMUM DIFF SIZE
MERGEABLE VALID STATE > ARTIFICIALLY SMALL TASK
SEMANTIC_ATOM = ONE INVARIANT CLOSURE
ONE_REPO = PREFERRED, NOT ABSOLUTE
PERMISSION MATRIX CONTROLS AUTHORITY, NOT TASK SIZE
RULE12 PREVENTS ARCHITECTURE INVENTION, NOT NORMAL IMPLEMENTATION
RULE11-D MUST BE POSITIVELY PROVEN
NEW EVIDENCE MAY REOPEN REVIEW
NEW OPINION MAY NOT
AGENT MAY IMPLEMENT FROZEN TRUTH
AGENT MAY NOT INVENT TRUTH
```

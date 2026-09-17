# RD1-V1 Control Plane Consolidation & Semantic Atomicity Plan v1.1

**Status:** CURRENT CANONICAL PLAN ON MERGE  
**Supersedes:** v1.0  
**Supersession scope:** FULL DOCUMENT  
**Older version usage:** EVIDENCE_ONLY  
**Implementation authority:** NONE by plan text alone

```text
ACTIVE_PLAN_VERSION = v1.1
SUPERSEDES = v1.0
SUPERSESSION_SCOPE = FULL_DOCUMENT
OLDER_VERSION_USAGE = EVIDENCE_ONLY
PLAN_APPROVAL != CONTROL_PLANE_MIGRATION_COMPLETE
```

The current active control-plane mechanics remain authoritative until the consolidation implementation carrying this plan is reviewed and merged.

## Consolidation target

```text
FROZEN ARCHITECTURE
→ GATE A: AUTHORITY
→ GATE B: SEMANTIC ATOM + PERMISSION
→ OWNER APPROVAL
→ IMPLEMENT
→ GATE C: CANDIDATE EVIDENCE
→ MERGE AUTHORIZATION
```

## Frozen direction

```text
GOVERNANCE_EXPANSION = FROZEN_BY_DEFAULT
NEW_RULE_NUMBER = NO
RULE11 = PRESERVED
RULE12 = PRESERVED
PERMISSION_MATRIX = PRESERVED
EXACT_TASK_BASE_SHA = PRESERVED
```

## Compatibility model

```text
CANONICAL_COMPATIBILITY_SOURCE
= docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md

CONTROL_PLANE_COMPATIBILITY_VERSION
= normative task-contract compatibility identity

CONTROL_PLANE_SHA_OBSERVED
= evidence only
```

The canonical compatibility source contains only the version plus optional non-self-referential metadata. It does not contain `EFFECTIVE_FROM_SHA`.

```text
SHA_TO_VERSION_RESOLUTION
= read docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md at that exact Git SHA
```

Every normative governance PR declares:

```text
CONTROL_PLANE_COMPATIBILITY_IMPACT = NONE | BREAKING
```

```text
BREAKING → version increments
NONE → version does not increment
```

The first consolidated control plane is version 1; the legacy control plane is unversioned; this transition is BREAKING.

## Freshness model

```text
TASK_BASE_SHA = strict implementation identity
CONTROL_PLANE_COMPATIBILITY_VERSION = governance compatibility identity
```

```text
CONTROL_PLANE_SHA_CHANGED
+ COMPATIBILITY_VERSION_UNCHANGED
→ compatible task may remain valid
```

```text
COMPATIBILITY_VERSION_CHANGED
→ compatibility revalidation
→ unaffected task = REVALIDATED
→ affected task = REBIND_REQUIRED
```

Compatibility is revalidated at Owner approval, implementation start, and merge review.

## Rule 12 execution proof

```text
NO_ARCHITECTURE_COMPLETION_BY_AGENT_INFERENCE = YES
ARCHITECTURE_DELTA = NONE
FROZEN_AUTHORITY_BINDING = <exact sources>
```

Detailed new-owner/domain/composition/binding/boundary/dependency/runtime/transport dimensions remain reviewer checks, not mandatory repetitive `COUNT=0` task fields.

## Rule 11 D

```text
A = required implementation missing under frozen architecture
B = implementation contradicts frozen architecture
C = concern belongs to later frozen phase
```

D is legal only when positively proven:

```text
1. effective frozen authorities conflict after scope-aware precedence
OR
2. current-phase required architecture question has no frozen answer after exhaustive trace
```

```text
D MUST BE POSITIVELY PROVEN
D MUST NOT BE REACHED BY ELIMINATION
```

## Semantic atomicity

```text
SEMANTIC_ATOM = ONE INVARIANT CLOSURE
SEMANTIC_ATOM != WHOLE FEATURE
TASK_SIZE != FILE_COUNT
TASK_SIZE != MINIMUM_DIFF
```

A task is the smallest semantically complete change that can merge without creating an invalid intermediate state.

```text
ATOMICITY_FAIL != SPLIT_SMALLER
```

A too-narrow task must be recomposed until its merge end-state is valid.

```text
ONE_REPO = PREFERRED
CROSS_REPO_ATOM = EXCEPTION_NOT_DEFAULT
```

Cross-repo atoms require frozen dependency relationship, exact per-repo base/write scope/order, valid intermediate states or an authorized coordinated cutover, and `ARCHITECTURE_DELTA = NONE`.

## Permission model

```text
PERMISSION_MODEL = DEFAULT_DENY
ARCHITECTURE_MUTATION = DENY
CROSS_BOUNDARY_SEMANTIC_DECISION = DENY
MERGE = DENY
RELEASE = DENY
DEPLOY = DENY
FALLBACK = DENY
SYNTHETIC_SUCCESS = DENY
FUTURE_PHASE_SCOPE = DENY
WRITE_SCOPE != TASK_SIZE_LIMIT
```

## Three composite gates

Gate A verifies authority, Rule11, Rule12, phase, and frozen-source binding.

Gate B verifies one invariant closure, valid merge end-state, authorized scope, permission bounds, and zero residual unfrozen architecture decisions.

Gate C verifies exact SHA/base/diff/paths, behavior, tests/evidence, invariants, fallback absence, and permission compliance.

## Reviewer stop condition

```text
R1 = frozen architecture compliance
R2 = semantic atomicity
R3 = scope / permission compliance
R4 = acceptance evidence
```

When all pass:

```text
REVIEW_COMPLETE = YES
NEW EVIDENCE MAY REOPEN REVIEW
NEW OPINION MAY NOT
DISCOVER_MORE != BLOCK_MORE
FUTURE_CONCERN != CURRENT_BLOCKER
```

## Parser responsibility

```text
PARSER = GOVERNANCE_ENFORCER
PARSER != ARCHITECTURE_LAW
```

Task cards explicitly declare:

```text
TASK_TYPE = STANDARD | CROSS_BOUNDARY
```

The parser must not infer task type from prose keywords. Cross-boundary mapping fields are required only when `TASK_TYPE = CROSS_BOUNDARY`.

## Normal task-card schema

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

Minimum self-check outcome:

```text
AUTHORITY_GATE = PASS
SEMANTIC_ATOMICITY_GATE = PASS
PERMISSION_GATE = PASS
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
SELF_CHECK_RESULT = PASS
READY_FOR_SUBMISSION = YES
```

## Authorization separation

```text
CONTROL_PLANE_APPROVAL != CODING_AUTHORIZATION
TASK_APPROVAL != MERGE_AUTHORIZATION
MERGE_AUTHORIZATION != RELEASE
RELEASE != DEPLOY
DEPLOY != PRODUCTION_ACCEPTANCE
```

## Final principles

```text
SEMANTIC_ATOMICITY > MINIMUM_DIFF_SIZE
MERGEABLE_VALID_STATE > ARTIFICIALLY_SMALL_TASK
PERMISSION_MATRIX_CONTROLS_AUTHORITY_NOT_TASK_SIZE
RULE12_PREVENTS_ARCHITECTURE_INVENTION_NOT_NORMAL_IMPLEMENTATION
RULE11_D_MUST_BE_POSITIVELY_PROVEN
AGENT MAY IMPLEMENT FROZEN TRUTH
AGENT MAY NOT INVENT TRUTH
```

After consolidation merge, the next engineering task is `RD1-RC4-M-00 Canonical Market Result Closure`; the fragmented `M-00A v0.2.x` chain is not to be resumed.

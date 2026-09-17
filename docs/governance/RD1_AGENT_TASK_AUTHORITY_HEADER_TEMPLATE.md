# RD1 Agent Task Authority Header Template

**Status:** ACTIVE CONTROL PLANE AFTER CONSOLIDATION MERGE

Every implementation task MUST bind exact authority, identity, semantic atom, and execution permission before coding begins.

## Mandatory task fields

```text
TASK_ID
TASK_TYPE = STANDARD | CROSS_BOUNDARY
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
ACCEPTANCE_EVIDENCE
```

If any mandatory field is absent, vague, unresolved, or inferred from implementation convenience:

```text
TASK = INVALID
IMPLEMENTATION = STOP
DELEGATION = STOP
BRANCH_CREATION = STOP
```

## Rule 11

Use exactly:

```text
A = implementation missing under effective frozen architecture
B = implementation contradicts effective frozen architecture
C = concern belongs to later frozen phase
D = true frozen-authority conflict/gap
NO_ACTIVE_FINDING = no A/B/C/D finding defines the task
```

```text
D MUST BE POSITIVELY PROVEN
D MUST NOT BE REACHED BY ELIMINATION
UNKNOWN != D
```

## Rule 12

Permanent law:

```text
NO_ARCHITECTURE_COMPLETION_BY_AGENT_INFERENCE = YES
```

Normal implementation tasks require:

```text
ARCHITECTURE_DELTA = NONE
FROZEN_AUTHORITY_BINDING = exact effective authority
```

If architecture delta is non-zero, use the constitutional amendment/refreeze path instead of an implementation task.

## Semantic atomicity

```text
SEMANTIC_ATOM
= ONE INVARIANT CLOSURE

TASK_SIZE
= SMALLEST SEMANTICALLY COMPLETE CHANGE
  THAT CAN MERGE WITHOUT INVALID INTERMEDIATE STATE
```

```text
SEMANTIC_ATOM != WHOLE FEATURE
TASK_SIZE != FILE_COUNT
ATOMICITY_FAIL != SPLIT_SMALLER
ONE_REPO = PREFERRED
```

## Control-plane compatibility

```text
CONTROL_PLANE_COMPATIBILITY_VERSION
= governance compatibility identity

CONTROL_PLANE_SHA_OBSERVED
= evidence only
```

Exact target `BASE_SHA` remains strict.

## Permission Matrix

Every task MUST include one `AGENT_EXECUTION_PERMISSION_MATRIX` using default deny.

At minimum:

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

Permission identity must exactly match task repository/base/branch.

## Cross-boundary tasks

Only explicit:

```text
TASK_TYPE = CROSS_BOUNDARY
```

activates mandatory mapping declarations:

```text
SOURCE_CONTRACT
TARGET_CONTRACT
FIELD_MAPPING
STATUS_MAPPING
FAILURE_MAPPING
PROVENANCE_MAPPING
AUTHORITY_TRANSFER
MALFORMED_INPUT_BEHAVIOR
UNKNOWN_VALUE_BEHAVIOR
LIFECYCLE_OWNERSHIP
```

No parser may infer task type from words such as adapter/bridge/proxy in prose.

## Required author self-check

Append:

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

Author PASS is signal only; independent review remains mandatory.

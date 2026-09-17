# RD1 Task Card CI / Parser Gate

**Status:** ACTIVE CONTROL PLANE AFTER CONSOLIDATION MERGE

## 1. Enforcement path

```text
TASK CARD / TASK-CARD PR
→ explicit mandatory task fields present?
→ CONTROL_PLANE_COMPATIBILITY_VERSION present?
→ ARCHITECTURE_DELTA = NONE?
→ FROZEN_AUTHORITY_BINDING present?
→ SEMANTIC_ATOM present?
→ VALID_MERGE_END_STATE present?
→ author self-check PASS?
→ Permission Matrix valid/default-deny?
→ residual architecture decisions == 0?
→ residual contract-semantic decisions == 0?
→ explicit TASK_TYPE valid?
→ cross-boundary mappings complete only when TASK_TYPE=CROSS_BOUNDARY?
→ permission identity == task identity?
→ BASE_SHA == declared repo current main when remote verification enabled?
→ control-plane compatibility version current?
→ PASS / FAIL
```

Parsers:

```text
tools/task_card_governance_gate.py
tools/control_plane_freshness_gate.py
```

Both run in `NO_CRITICAL_FALLBACK_GATE`.

## 2. Mandatory task schema

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
ARCHITECTURE_DELTA
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

For normal implementation tasks:

```text
ARCHITECTURE_DELTA = NONE
```

## 3. Rule 12 hard gate

Rule 12 constitutional meaning remains:

```text
NO_ARCHITECTURE_COMPLETION_BY_AGENT_INFERENCE = YES
```

Parser requires the simplified operational proof:

```text
FROZEN_AUTHORITY_BINDING present
ARCHITECTURE_DELTA = NONE
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
```

The former `NEW_*_COUNT = 0` fields are no longer mandatory parser syntax.

## 4. Control-plane compatibility gate

Every coding task card carries:

```text
CONTROL_PLANE_AUTHORITY_REPO
= tonychang925-dev/Julia_core

SELF_CHECK_CONTROL_PLANE_COMPATIBILITY_VERSION
= <integer>

SELF_CHECK_CONTROL_PLANE_SHA
= <exact observed 40-hex SHA>

CONTROL_PLANE_FRESHNESS_CHECK
= PASS
```

Machine enforcement compares compatibility version, not exact SHA equality.

```text
SHA_CHANGED + VERSION_UNCHANGED
→ PASS COMPATIBILITY

VERSION_CHANGED
→ REVALIDATION / REBIND AS APPLICABLE
```

The exact SHA remains audit evidence.

## 5. Permission Matrix hard gate

Default deny remains mandatory. Permission repository/base/branch must equal task identity exactly.

Required denials include architecture mutation, cross-boundary semantic decision, merge, release, deploy, production mutation, fallback, synthetic success, and future-phase scope.

## 6. Cross-boundary hard gate

Parser MUST NOT infer cross-boundary work from prose keywords.

Task author declares:

```text
TASK_TYPE = STANDARD | CROSS_BOUNDARY
```

Only `CROSS_BOUNDARY` requires:

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

Independent review verifies that the declared task type is truthful.

## 7. Exact implementation base

When remote-base verification is enabled:

```text
BASE_SHA == REPO/main current SHA
```

Failure is `BASE_DRIFT` and blocks the task.

## 8. Non-authority

```text
PARSER = GOVERNANCE ENFORCER
PARSER != ARCHITECTURE LAW
PARSER != OWNER APPROVAL
PARSER != IMPLEMENTATION AUTHORIZATION
PARSER != MERGE AUTHORIZATION BY ITSELF
```

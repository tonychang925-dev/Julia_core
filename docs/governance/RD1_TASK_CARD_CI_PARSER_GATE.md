# RD1 Task Card CI / Parser Gate

**Status:** ACTIVE CONTROL PLANE  
**Purpose:** convert task-card self-check and execution permissions into machine-enforced pull-request gating.

## 1. Enforcement path

```text
TASK CARD / TASK-CARD PR
→ parser
→ mandatory authority fields present?
→ author self-check evidence present?
→ execution permission matrix present?
→ default-deny permission model valid?
→ residual architecture decisions == 0?
→ residual contract-semantic decisions == 0?
→ cross-boundary mapping complete when applicable?
→ task identity == permission identity?
→ BASE_SHA == declared repo current main?
→ PASS / FAIL
```

Parser:

```text
tools/task_card_governance_gate.py
```

Sabotage/unit coverage:

```text
tests/governance/test_task_card_governance_gate.py
```

## 2. Merge enforcement

The parser runs inside the repository's required GitHub check:

```text
NO_CRITICAL_FALLBACK_GATE
```

Therefore, while that repository rule remains required:

```text
TASK_CARD_GOVERNANCE_GATE_FAIL
→ NO_CRITICAL_FALLBACK_GATE FAIL
→ PR CANNOT MERGE
```

## 3. Mandatory task/self-check fields

The parser requires the active authority header and completed `TASK_CARD_AUTHOR_SELF_CHECK`, including zero residual architecture and contract-semantic decisions.

Legal submission requires:

```text
SELF_CHECK_RESULT = PASS
READY_FOR_SUBMISSION = YES
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
```

## 4. Agent Execution Permission Matrix hard gate

Every coding task card must contain:

```text
AGENT_EXECUTION_PERMISSION_MATRIX
```

with at least:

```text
PERMISSION_MODEL
PERMISSION_REPOSITORY
PERMISSION_BASE_SHA
PERMISSION_TARGET_BRANCH
READ_SCOPE
WRITE_SCOPE
ARCHITECTURE_MUTATION
PUBLIC_CONTRACT_MUTATION
CROSS_BOUNDARY_SEMANTIC_DECISION
DEPENDENCY_MUTATION
TEST_CREATION
BRANCH_CREATION
COMMIT
PR_CREATION
MERGE
RELEASE
DEPLOY
PRODUCTION_MUTATION
FALLBACK
SYNTHETIC_SUCCESS
FUTURE_PHASE_SCOPE
```

Required default-deny values:

```text
PERMISSION_MODEL = DEFAULT_DENY
ARCHITECTURE_MUTATION = DENY
CROSS_BOUNDARY_SEMANTIC_DECISION = DENY
TEST_CREATION = BOUNDED_TO_ACCEPTANCE_EVIDENCE
BRANCH_CREATION = EXACT_TARGET_ONLY
COMMIT = TASK_BRANCH_ONLY
MERGE = DENY
RELEASE = DENY
DEPLOY = DENY
PRODUCTION_MUTATION = DENY
FALLBACK = DENY
SYNTHETIC_SUCCESS = DENY
FUTURE_PHASE_SCOPE = DENY
```

Identity must match mechanically:

```text
PERMISSION_REPOSITORY == REPO
PERMISSION_BASE_SHA == BASE_SHA
PERMISSION_TARGET_BRANCH == TARGET_BRANCH
```

Permanent law:

```text
ANY_PERMISSION_NOT_EXPLICITLY_GRANTED = DENY
```

## 5. Cross-boundary hard gate

For adapter / bridge / translator / proxy / serializer / provider-wrapper / boundary-conversion work, the parser also requires:

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
CROSS_BOUNDARY_SEMANTICS = PASS
```

Missing mapping is a machine failure, not implementation-Agent design freedom.

## 6. Exact SHA verification

In PR CI the parser requires:

```text
BASE_SHA == REPO/main current SHA
```

Failure:

```text
BASE_DRIFT
→ GATE FAIL
```

Current code/SHA identity remains engineering evidence only; it is not architecture authority.

## 7. Scope and non-authority

```text
PARSER = GOVERNANCE ENFORCER
PARSER != ARCHITECTURE LAW
PARSER != OWNER APPROVAL
PARSER != IMPLEMENTATION AUTHORIZATION
PARSER != MERGE AUTHORIZATION BY ITSELF
```

Frozen source documents remain authoritative. The parser rejects submissions that fail active control-plane requirements; it does not design architecture.

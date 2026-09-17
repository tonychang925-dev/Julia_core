# RD1 Task Card CI / Parser Gate

**Status:** ACTIVE CONTROL-PLANE CANDIDATE  
**Purpose:** convert task-card self-check from process-only discipline into machine-enforced pull-request gating.

## 1. Enforcement path

```text
TASK CARD / TASK-CARD PR
→ parser
→ mandatory fields present?
→ author self-check evidence present?
→ residual architecture decisions == 0?
→ residual contract-semantic decisions == 0?
→ cross-boundary mapping complete when applicable?
→ BASE_SHA == declared repo current main?
→ PASS / FAIL
```

The parser is:

```text
tools/task_card_governance_gate.py
```

Its sabotage/unit coverage is:

```text
tests/governance/test_task_card_governance_gate.py
```

## 2. Merge enforcement

The parser is executed inside the repository's already-required GitHub check:

```text
NO_CRITICAL_FALLBACK_GATE
```

Therefore, while that required check remains required by repository rules:

```text
TASK_CARD_GOVERNANCE_GATE_FAIL
→ NO_CRITICAL_FALLBACK_GATE FAIL
→ PR CANNOT MERGE
```

This avoids creating a second unprotected advisory workflow.

## 3. Mechanical checks

The gate checks task cards detected by filename/content and task-card submissions embedded in PR bodies.

Mandatory task fields:

```text
FROZEN_AUTHORITY_TRACE
RULE11_CLASSIFICATION
CURRENT_PHASE
TARGET_REQUIREMENT
DEFERRED_FINDINGS
TASK_ID
REPO
TARGET_BRANCH
BASE_SHA
AUTHORIZED_PATHS
FORBIDDEN_PATHS
REQUIRED_BEHAVIOR
FORBIDDEN_BEHAVIOR
ACCEPTANCE_EVIDENCE
```

Mandatory author self-check evidence includes:

```text
TASK_CARD_AUTHOR_SELF_CHECK
AUTHORITY_SOURCE_FILES_CHECKED
CURRENT_MAIN_SHAS
MANDATORY_TASK_FIELDS_PRESENT
AUTHORITY_IDENTITY
MANDATORY_HEADER
RULE11_CLASSIFICATION_CHECK
PHASE_SCOPE_CHECK
RESIDUAL_DECISION_AUDIT
RESIDUAL_ARCHITECTURE_DECISIONS
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS
CROSS_BOUNDARY_SEMANTICS
CURRENT_CODE_COMPATIBILITY
ACCEPTANCE_EVIDENCE_CHECK
NO_AGENT_ARCHITECTURE_DISCRETION
SELF_CHECK_RESULT
READY_FOR_SUBMISSION
```

Legal submission requires mechanically:

```text
SELF_CHECK_RESULT = PASS
READY_FOR_SUBMISSION = YES
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
```

## 4. Cross-boundary hard gate

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

Missing mapping is a machine failure, not an implementation-Agent design opportunity.

## 5. Exact SHA verification

In PR CI the parser uses GitHub API identity for the declared `REPO` and requires:

```text
BASE_SHA == REPO/main current SHA
```

Failure is:

```text
BASE_DRIFT
→ GATE FAIL
```

The parser validates engineering identity only. It does not promote current code into architecture authority.

## 6. Scope and non-authority

```text
PARSER = GOVERNANCE ENFORCER
PARSER != ARCHITECTURE LAW
PARSER != OWNER APPROVAL
PARSER != IMPLEMENTATION AUTHORIZATION
PARSER != MERGE AUTHORIZATION BY ITSELF
```

Frozen source documents remain authoritative. The parser only rejects submissions that fail the active control-plane requirements.

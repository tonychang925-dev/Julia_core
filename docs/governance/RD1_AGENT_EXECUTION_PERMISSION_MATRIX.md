# RD1 Agent Execution Permission Matrix

**Status:** ACTIVE CONTROL PLANE  
**Applies to:** every implementation/rework task executed by Mira, Codex, Claude, humans, automations, or any other Agent across Julia Core / Julia-AI-Assistant / Market Brain.

## 1. Permanent law

Every coding task card MUST contain exactly one `AGENT_EXECUTION_PERMISSION_MATRIX` before implementation instructions.

```text
ANY_PERMISSION_NOT_EXPLICITLY_GRANTED = DENY
DEFAULT_PERMISSION_MODEL = DENY_BY_DEFAULT
```

The matrix is an execution boundary. It does not create architecture authority and cannot override frozen authority, Rule 11, phase gates, Owner approval, or merge/release/deploy authorization.

```text
PERMISSION_MATRIX != ARCHITECTURE_LAW
PERMISSION_MATRIX != OWNER_APPROVAL
PERMISSION_MATRIX != IMPLEMENTATION_AUTHORIZATION
PERMISSION_MATRIX != MERGE_AUTHORIZATION
```

## 2. Mandatory matrix shape

```text
AGENT_EXECUTION_PERMISSION_MATRIX

PERMISSION_MODEL
= DEFAULT_DENY

PERMISSION_REPOSITORY
= <must exactly equal REPO>

PERMISSION_BASE_SHA
= <must exactly equal BASE_SHA>

PERMISSION_TARGET_BRANCH
= <must exactly equal TARGET_BRANCH>

READ_SCOPE
= <exact allowed read scope or explicit bounded rule>

WRITE_SCOPE
= <exact authorized paths; must not exceed AUTHORIZED_PATHS>

ARCHITECTURE_MUTATION
= DENY

PUBLIC_CONTRACT_MUTATION
= DENY | EXPLICITLY_AUTHORIZED:<exact authority/scope>

CROSS_BOUNDARY_SEMANTIC_DECISION
= DENY

DEPENDENCY_MUTATION
= DENY | EXPLICITLY_AUTHORIZED:<exact authority/scope>

TEST_CREATION
= BOUNDED_TO_ACCEPTANCE_EVIDENCE

BRANCH_CREATION
= EXACT_TARGET_ONLY

COMMIT
= TASK_BRANCH_ONLY

PR_CREATION
= ALLOW | DENY

MERGE
= DENY

RELEASE
= DENY

DEPLOY
= DENY

PRODUCTION_MUTATION
= DENY

FALLBACK
= DENY

SYNTHETIC_SUCCESS
= DENY

FUTURE_PHASE_SCOPE
= DENY
```

## 3. Default-deny semantics

Silence is not permission.

```text
NOT_EXPLICITLY_ALLOWED = FORBIDDEN
MISSING_PERMISSION_FIELD = TASK_CARD_NOT_READY
AMBIGUOUS_PERMISSION_VALUE = TASK_CARD_NOT_READY
```

The Agent MUST NOT infer permission from implementation convenience, repository write access, branch write access, tests, current code shape, prior tasks, historical branches, PR comments, or Agent consensus.

## 4. Architecture and semantic authority

The following are permanently denied to an implementation Agent unless a higher frozen authority is formally amended before the task is authorized:

```text
ARCHITECTURE_MUTATION
CROSS_BOUNDARY_SEMANTIC_DECISION
OWNERSHIP_CHANGE
TOPOLOGY_CHANGE
PUBLIC_PRIVATE_BOUNDARY_CHANGE
PHASE_BOUNDARY_CHANGE
NEW_COMPOSITION_OWNER
UNFROZEN_STATUS_MAPPING
UNFROZEN_FAILURE_MAPPING
UNFROZEN_PROVENANCE_MAPPING
UNFROZEN_LIFECYCLE_MAPPING
UNFROZEN_AUTHORIZATION_MEANING
```

Cross-boundary adapters/bridges/translators may implement only already-frozen mapping truth.

## 5. Write-boundary rule

```text
WRITE_SCOPE ⊆ AUTHORIZED_PATHS
EVERYTHING_OUTSIDE_WRITE_SCOPE = DENY
```

Reading additional source needed to understand an authorized implementation may be allowed only when `READ_SCOPE` explicitly permits it. Reading does not grant mutation authority.

## 6. Lifecycle authority

Unless an exact higher-level authorization states otherwise:

```text
BRANCH_CREATION = EXACT_TARGET_ONLY
COMMIT = TASK_BRANCH_ONLY
MERGE = DENY
RELEASE = DENY
DEPLOY = DENY
PRODUCTION_MUTATION = DENY
```

Coding authorization never implies merge/release/deploy authority.

## 7. No fallback / synthetic-success authority

```text
FALLBACK = DENY
SYNTHETIC_SUCCESS = DENY
```

No task card may grant these through implementation convenience. Any proposed exception requires a constitution-compliant frozen amendment before implementation.

## 8. Phase containment

```text
FUTURE_PHASE_SCOPE = DENY
DISCOVER_MORE != DO_MORE
```

A newly discovered future-phase concern must be recorded under `DEFERRED_FINDINGS`; it does not enlarge `WRITE_SCOPE` or `REQUIRED_BEHAVIOR`.

## 9. Machine enforcement

`tools/task_card_governance_gate.py` MUST reject a task-card submission when:

```text
AGENT_EXECUTION_PERMISSION_MATRIX is missing
PERMISSION_MODEL != DEFAULT_DENY
high-risk mandatory DENY values are weakened
PERMISSION_REPOSITORY != REPO
PERMISSION_BASE_SHA != BASE_SHA
PERMISSION_TARGET_BRANCH != TARGET_BRANCH
WRITE_SCOPE is missing
READ_SCOPE is missing
BRANCH_CREATION != EXACT_TARGET_ONLY
COMMIT != TASK_BRANCH_ONLY
TEST_CREATION != BOUNDED_TO_ACCEPTANCE_EVIDENCE
```

The machine gate enforces declared authority boundaries; it does not decide architecture.

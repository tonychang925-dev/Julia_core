# RD1 Agent Task Authority Header Template

**Status:** ACTIVE CONTROL PLANE  
**Applies to:** Mira, Codex, Claude, human-authored task cards, review agents, automations, and any implementation/rework task across Julia Core / Julia-AI-Assistant / Market Brain.

A task that does not contain the mandatory authority header below is invalid and must not start.

```text
TASK_NOT_VALID_WITHOUT_AUTHORITY_HEADER = YES
```

## Mandatory first section of every task card

```text
FROZEN_AUTHORITY_TRACE
= <exact governing frozen documents / clauses / versions>

RULE11_CLASSIFICATION
= A | B | C | D | NO_ACTIVE_FINDING

CURRENT_PHASE
= <exact RC / gate / milestone>

TARGET_REQUIREMENT
= <exact requirement derived from frozen authority>

DEFERRED_FINDINGS
= <findings explicitly not authorized for this task/phase; NONE if empty>
```

These five fields are mandatory and must appear before implementation instructions.

If any field is absent, vague, inferred from code, or unresolved:

```text
TASK = INVALID
IMPLEMENTATION = STOP
DELEGATION = STOP
BRANCH_CREATION = STOP
```

## Required identity fields

Every task must additionally bind:

```text
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

`BASE_SHA` must equal the current authorized trunk SHA at task authorization time unless a constitution-compliant frozen contract explicitly states otherwise.

## Frozen Authority Trace rules

`FROZEN_AUTHORITY_TRACE` must identify the actual governing authority and exact clause/scope where practicable. It may not be populated from:

```text
current code shape
historical implementation
PR comments
Codex/Mira/Claude opinion
test output
runtime convenience
branch names
```

Those are evidence only.

The trace must answer:

```text
WHAT LAW GOVERNS THIS TASK?
WHAT OWNERSHIP / BOUNDARY / PHASE DOES IT FREEZE?
WHAT LOWER-LEVEL MATERIAL IS NON-AUTHORITATIVE?
```

The Architecture Authority Index is a pointer/status register only. It helps locate current sources but is not itself architecture law.

```text
INDEX != SOURCE_AUTHORITY
SOURCE_DOCUMENT_WINS_ON_CONFLICT
```

## Rule 11 classification rules

Use exactly one of:

```text
A = IMPLEMENTATION_GAP_UNDER_EXISTING_FROZEN_AUTHORITY
B = IMPLEMENTATION_DEVIATION_FROM_FROZEN_ARCHITECTURE
C = DEFERRED_PHASE_CONCERN
D = TRUE_FROZEN_AUTHORITY_CONFLICT_OR_GAP
NO_ACTIVE_FINDING = no architecture gap/deviation/deferred/conflict is being used to define this task
```

`NO_ACTIVE_FINDING` is valid only for an ordinary implementation/review task whose target requirement is already fully defined by frozen authority. It is not a substitute for unresolved classification.

```text
UNKNOWN != NO_ACTIVE_FINDING
UNRESOLVED != NO_ACTIVE_FINDING
```

No Agent may convert A/B/C into D by reasoning from implementation facts.

## Current Phase rule

The task must state the exact current phase and prove the target requirement belongs to that phase.

```text
DISCOVER_MORE != DO_MORE
FUTURE_PHASE_FINDING != CURRENT_PHASE_SCOPE
```

A future concern may be recorded in `DEFERRED_FINDINGS`; it may not silently expand `AUTHORIZED_PATHS`, `REQUIRED_BEHAVIOR`, or acceptance criteria.

## Target Requirement rule

`TARGET_REQUIREMENT` must be a requirement already supported by frozen authority or by an explicitly frozen scope-bounded amendment.

Prohibited:

```text
implementation convenience → target requirement
current-main absence → target requirement
test expectation → target requirement
agent inference → target requirement
```

## Deferred Findings rule

Any finding discovered during analysis that is outside current task authority must be added to `DEFERRED_FINDINGS` and left untouched.

```text
DEFERRED_FINDING
→ RECORD
→ DO NOT DESIGN
→ DO NOT IMPLEMENT
→ DO NOT EXPAND SCOPE
```

If a deferred finding is actually a Rule11-D conflict, stop and invoke the constitutional adjudication path instead.

## Agent design freedom

Allowed only inside already-frozen boundaries:

```text
local implementation detail
private helper naming
bounded refactor that preserves contract
algorithmic implementation choice explicitly left open
```

Forbidden without formal architecture amendment:

```text
ownership
topology
public/private boundary
ABI
provider authority
phase boundary
dependency direction
new architecture layer
new composition owner
```

Hard rule:

```text
IMPLEMENTATION_FREEDOM = BOUNDED
ARCHITECTURE_FREEDOM = NO
NO_FROZEN_ANSWER_FOUND != PERMISSION_TO_INVENT
```

## Mandatory author pre-submission self-check

Every task-card author MUST execute:

```text
docs/governance/RD1_TASK_CARD_AUTHOR_PRE_SUBMISSION_SELF_CHECK.md
```

before submitting the task card to an Owner, independent reviewer, Codex, Claude, Mira, automation, or implementation Agent.

The author is the first-line governance reviewer.

```text
TASK_CARD_DRAFT
→ AUTHOR_SELF_CHECK
→ MACHINE_VERIFIABLE_SELF_CHECK_EVIDENCE
→ PASS
→ ELIGIBLE_FOR_SUBMISSION
```

Without the evidence block:

```text
NO_SELF_CHECK_EVIDENCE = NO_TASK_SUBMISSION
TASK_CARD_STATUS = INVALID_FOR_SUBMISSION
```

Every submitted task card MUST append a completed `TASK_CARD_AUTHOR_SELF_CHECK` record containing at minimum:

```text
AUTHOR_ROLE
TASK_ID
TASK_CARD_VERSION
AUTHORITY_SOURCE_FILES_CHECKED
CURRENT_MAIN_SHAS
MANDATORY_TASK_FIELDS_PRESENT
AUTHORIZED_PATH_COUNT
DEFERRED_FINDING_COUNT
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

Submission is legal only when:

```text
SELF_CHECK_RESULT = PASS
READY_FOR_SUBMISSION = YES
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
```

The author's PASS is not authority:

```text
SELF_CHECK_PASS != OWNER_APPROVAL
SELF_CHECK_PASS != IMPLEMENTATION_AUTHORIZATION
SELF_CHECK_PASS != MERGE_AUTHORIZATION
```

## Cross-boundary semantic mapping rule

Any task that creates or changes an adapter, bridge, translator, proxy, serializer, provider wrapper, public-boundary conversion, or cross-repo contract conversion MUST freeze or cite already-frozen law for:

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

If any required semantic mapping is unresolved:

```text
TASK_CARD_NOT_READY
READY_FOR_SUBMISSION = NO
```

Permanent law:

```text
CROSS_BOUNDARY_SEMANTIC_MAPPING = FROZEN_BEFORE_CODING
AGENT_CROSS_BOUNDARY_SEMANTIC_FREEDOM = NO
```

## Mandatory opening sentence

Every task card must begin with:

> **违反 `DEVELOPMENT_CONSTITUTION.md` 或当前有效 frozen authority，立即 STOP；Agent 不得自行解释、补全、设计例外、扩大 scope 或用代码/测试反向定义架构。若 Architecture Authority Index 与源冻结文档冲突或过期，源文档优先，任务停止直至 Index 完成 rebind。**

# RD1 Task Card Author Pre-Submission Self-Check

**Status:** ACTIVE CONTROL PLANE  
**Applies to:** Mira, Codex, Claude, human task authors, automation-generated task cards, and any Agent acting as task-card owner/author across Julia Core / Julia-AI-Assistant / Market Brain.

## 1. Permanent law

A task-card author is not only a drafter. The author is the **first-line governance reviewer**.

```text
TASK_CARD_CREATED
→ RULE11_CLASSIFICATION
→ RULE12_ARCHITECTURE_COMPLETION_AUDIT
→ AUTHOR_SELF_CHECK
→ MACHINE-VERIFIABLE EVIDENCE
→ PASS?
   NO  → REWORK / DO NOT SUBMIT
   YES → ELIGIBLE FOR INDEPENDENT PRECHECK / OWNER REVIEW
```

Hard rules:

```text
NO_SELF_CHECK_EVIDENCE = NO_TASK_SUBMISSION
NO_RULE12_ARCHITECTURE_COMPLETION_EVIDENCE = NO_TASK_SUBMISSION
SELF_CHECK_PASS != OWNER_APPROVAL
SELF_CHECK_PASS != IMPLEMENTATION_AUTHORIZATION
SELF_CHECK_PASS != MERGE_AUTHORIZATION
```

A task card submitted without the required self-check record is invalid for submission.

```text
TASK_CARD_STATUS = INVALID_FOR_SUBMISSION
```

## 2. Self-check must be mechanical, not narrative

The author MUST produce auditable evidence, not merely state "checked" or "looks correct".

At minimum the record MUST contain:

```text
AUTHORITY_SOURCE_FILES_CHECKED
CURRENT_MAIN_SHAS
MANDATORY_TASK_FIELDS_PRESENT
AUTHORIZED_PATH_COUNT
DEFERRED_FINDING_COUNT
TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK
FROZEN_SOURCE_BINDING_COMPLETE
TASK_AUTHOR_NEW_ARCHITECTURE_DECISIONS
NEW_OWNER_COUNT
NEW_DOMAIN_COUNT
NEW_COMPOSITION_ROOT_COUNT
NEW_BINDING_AUTHORITY_COUNT
NEW_PACKAGE_BOUNDARY_COUNT
NEW_DEPENDENCY_DIRECTION_COUNT
NEW_RUNTIME_AUTHORITY_COUNT
NEW_TRANSPORT_COUNT
RESIDUAL_ARCHITECTURE_DECISIONS
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS
SELF_CHECK_RESULT
READY_FOR_SUBMISSION
```

Any unresolved or unknown value is a failure, not an implicit pass.

```text
UNKNOWN != PASS
UNRESOLVED != PASS
NOT_CHECKED != PASS
```

## 3. Check A — Authority identity

Mechanically verify:

```text
CURRENT_CONSTITUTION
CURRENT_RULE12_AMENDMENT
CURRENT_ARCHITECTURE_AUTHORITY_INDEX
GOVERNING_FROZEN_DOCUMENTS
CURRENT_PHASE
PARENT_CONTROL_CONTRACT_STATUS
REPO
CURRENT_TRUNK_SHA
PROPOSED_BASE_SHA
PROPOSED_TARGET_BRANCH
```

Mandatory anti-confusion rules:

```text
OWNER_APPROVAL_CANDIDATE != APPROVED
DRAFT != ACTIVE_AUTHORITY
CANDIDATE != ACTIVE_AUTHORITY
LOOKS_VALID != ACTIVE_AUTHORITY
```

If a parent control contract is required but is not active/approved for the next lifecycle step:

```text
AUTHORITY_IDENTITY = FAIL
READY_FOR_SUBMISSION = NO
```

## 4. Check B — Mandatory task-header completeness

Verify the card contains all required fields:

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

If any field is missing, vague, unresolved, or inferred from implementation convenience:

```text
MANDATORY_HEADER = FAIL
READY_FOR_SUBMISSION = NO
```

## 5. Check C — Rule 11 classification

Use only the active Rule 11 values:

```text
A = IMPLEMENTATION_GAP_UNDER_EXISTING_FROZEN_AUTHORITY
B = IMPLEMENTATION_DEVIATION_FROM_FROZEN_ARCHITECTURE
C = DEFERRED_PHASE_CONCERN
D = TRUE_FROZEN_AUTHORITY_CONFLICT_OR_GAP
NO_ACTIVE_FINDING = ordinary task already fully defined by frozen authority
```

The author MUST verify:

```text
UNKNOWN != NO_ACTIVE_FINDING
UNRESOLVED != NO_ACTIVE_FINDING
CURRENT_MAIN_ABSENCE != ARCHITECTURE_ABSENCE
IMPLEMENTATION_GAP != ARCHITECTURE_AMBIGUITY
FUTURE_PHASE_FINDING != CURRENT_PHASE_SCOPE
TEST_EXPECTATION != ARCHITECTURE_AUTHORITY
```

Any attempt to let implementation facts define architecture fails the self-check.

## 6. Check D — Rule 12 Task-Author Architecture Completion Audit

This check is mandatory for every coding task card and is independent of the residual-decision audit.

The author MUST answer:

```text
DID I, AS TASK AUTHOR, INTRODUCE ANY ARCHITECTURE ELEMENT
THAT IS NOT DIRECTLY BOUND TO EFFECTIVE FROZEN AUTHORITY?
```

Audit at minimum:

```text
new owner
new domain
new composition root
new binding authority
new package/public-private boundary
new dependency direction
new runtime authority
new transport requirement
new lifecycle authority
new cross-repo responsibility
new ABI authority
new phase ownership
```

Required result for implementation/correction task cards:

```text
TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK = PASS
FROZEN_SOURCE_BINDING_COMPLETE = PASS
TASK_AUTHOR_NEW_ARCHITECTURE_DECISIONS = 0
NEW_OWNER_COUNT = 0
NEW_DOMAIN_COUNT = 0
NEW_COMPOSITION_ROOT_COUNT = 0
NEW_BINDING_AUTHORITY_COUNT = 0
NEW_PACKAGE_BOUNDARY_COUNT = 0
NEW_DEPENDENCY_DIRECTION_COUNT = 0
NEW_RUNTIME_AUTHORITY_COUNT = 0
NEW_TRANSPORT_COUNT = 0
```

The author MUST NOT count a decision as "already frozen" merely because it is implied by code layout, runtime need, implementation convenience, tests, or Agent consensus.

Forbidden:

```text
IMPLEMENTATION_GAP -> TASK_AUTHOR_INVENTS_ARCHITECTURE
NO_COMPOSITION_ROOT_IN_CODE -> TASK_AUTHOR_CREATES_NEW_COMPOSITION_ROOT
NO_BINDING_LOCUS_IN_CODE -> TASK_AUTHOR_CREATES_NEW_BINDING_AUTHORITY
```

If any count is non-zero or frozen-source binding cannot be proven:

```text
TASK_CARD_NOT_READY
SELF_CHECK_RESULT = FAIL
READY_FOR_SUBMISSION = NO
```

A deliberate architecture change must first complete the Constitution's explicit scope-bounded amendment/refreeze path; it may not be hidden inside a coding task card.

## 7. Check E — Phase and scope

The author MUST prove:

```text
TARGET_REQUIREMENT ∈ CURRENT_PHASE
AUTHORIZED_PATHS are the minimum necessary path set
REQUIRED_BEHAVIOR is bounded to the task requirement
DEFERRED_FINDINGS remain deferred
NO future-phase concern is pulled forward
NO cross-lane mutation is implied
```

Permanent law:

```text
DISCOVER_MORE != DO_MORE
```

## 8. Check F — Residual Decision Audit

This is mandatory for every task card.

Question:

```text
IF AN IMPLEMENTATION AGENT RECEIVES ONLY THIS TASK CARD,
WILL IT STILL NEED TO MAKE ANY UNFROZEN ARCHITECTURE OR CONTRACT-SEMANTIC DECISION?
```

The author MUST explicitly audit at least:

```text
ownership
topology
public/private boundary
ABI
provider authority
dependency direction
phase scope
cross-repo responsibility
status mapping
failure mapping
provenance mapping
lifecycle mapping
authorization meaning
fallback semantics
unknown-input behavior
malformed-input behavior
```

Required result:

```text
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
```

If either is non-zero:

```text
TASK_CARD_NOT_READY
SELF_CHECK_RESULT = FAIL
READY_FOR_SUBMISSION = NO
```

The author MUST NOT hide a residual architecture decision by calling it an "implementation detail".

## 9. Check G — Cross-Boundary Semantic Mapping Gate

This gate is mandatory when the task contains or changes any adapter, bridge, translator, proxy, serializer, provider wrapper, public-boundary conversion, or cross-repo contract conversion.

The task MUST explicitly freeze, or point to already-frozen law for:

```text
SOURCE_CONTRACT
TARGET_CONTRACT
FIELD_MAPPING
STATUS_MAPPING
FAILURE_MAPPING
PROVENANCE_MAPPING
AUTHORITY_TRANSFER = NONE (unless explicitly frozen otherwise)
MALFORMED_INPUT_BEHAVIOR
UNKNOWN_VALUE_BEHAVIOR
LIFECYCLE_OWNERSHIP
```

If any required mapping is absent or left for the implementation Agent to infer:

```text
CROSS_BOUNDARY_SEMANTICS = FAIL
TASK_CARD_NOT_READY
READY_FOR_SUBMISSION = NO
```

Permanent law:

```text
CROSS_BOUNDARY_SEMANTIC_MAPPING = FROZEN_BEFORE_CODING
AGENT_CROSS_BOUNDARY_SEMANTIC_FREEDOM = NO
```

## 10. Check H — Current-code compatibility evidence

Current code is evidence only. The author MUST mechanically inspect the exact implementation surfaces necessary to prove the task is executable as written, then compare them to frozen authority and the task contract.

Forbidden:

```text
CURRENT_CODE -> NEW_ARCHITECTURE
```

Allowed:

```text
FROZEN_AUTHORITY + TASK_REQUIREMENT
→ inspect current code
→ confirm exact implementation gap / compatibility
```

If current implementation proves the task cannot be executed without an unauthorized semantic or architectural decision:

```text
CURRENT_CODE_COMPATIBILITY = FAIL
READY_FOR_SUBMISSION = NO
```

## 11. Check I — Acceptance-evidence sufficiency

The author MUST confirm acceptance evidence can prove the exact task without forcing a test-driven architecture change.

Verify:

```text
EXACT_CANDIDATE_SHA required
changed-path proof required
focused test command defined
raw test output required
architecture/scope invariants independently checkable
TEST_PASS != ARCHITECTURE_PASS
```

If acceptance tests leave a semantic decision to the implementer or require architecture deviation to pass:

```text
ACCEPTANCE_EVIDENCE = FAIL
READY_FOR_SUBMISSION = NO
```

## 12. Mandatory self-check output block

Every task-card submission MUST carry a completed record containing at least:

```text
TASK_CARD_AUTHOR_SELF_CHECK
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
TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK
FROZEN_SOURCE_BINDING_COMPLETE
TASK_AUTHOR_NEW_ARCHITECTURE_DECISIONS
NEW_OWNER_COUNT
NEW_DOMAIN_COUNT
NEW_COMPOSITION_ROOT_COUNT
NEW_BINDING_AUTHORITY_COUNT
NEW_PACKAGE_BOUNDARY_COUNT
NEW_DEPENDENCY_DIRECTION_COUNT
NEW_RUNTIME_AUTHORITY_COUNT
NEW_TRANSPORT_COUNT
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

Submission is legal only if:

```text
SELF_CHECK_RESULT = PASS
READY_FOR_SUBMISSION = YES
TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK = PASS
FROZEN_SOURCE_BINDING_COMPLETE = PASS
TASK_AUTHOR_NEW_ARCHITECTURE_DECISIONS = 0
ALL_REQUIRED_NEW_*_COUNT = 0
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
```

## 13. Independent review remains mandatory

Author self-check is the first line of defense, never the final authority.

```text
AUTHOR_SELF_CHECK_PASS
→ INDEPENDENT_ARCHITECTURE_PRECHECK
→ OWNER / AUTHORIZED REVIEW
→ ONLY THEN POSSIBLE CODING AUTHORIZATION
```

The independent reviewer MUST mechanically verify the author's self-check evidence and MUST NOT trust the author's PASS claim by itself.

```text
SELF_CHECK_CLAIM = SIGNAL_ONLY
SELF_CHECK_EVIDENCE = MUST_BE_VERIFIED
```

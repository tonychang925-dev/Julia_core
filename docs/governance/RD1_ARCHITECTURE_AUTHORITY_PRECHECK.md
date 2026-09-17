# RD1 Architecture / Authority Precheck

**Status:** ACTIVE CONTROL PLANE  
**Purpose:** make architecture/authority compliance the first review gate. Diff, tests, and runtime evidence are reviewed only after this precheck passes.

```text
ARCHITECTURE_PRECHECK_BEFORE_DIFF = REQUIRED
AUTHOR_SELF_CHECK_BEFORE_INDEPENDENT_PRECHECK = REQUIRED
RULE12_ARCHITECTURE_COMPLETION_PRECHECK = REQUIRED
```

## Review order

Every implementation/rework review must execute in this order:

```text
PRE-GATE — AUTHOR SELF-CHECK EVIDENCE VERIFICATION
GATE 0 — AUTHORITY IDENTITY
GATE 1 — RULE11 CLASSIFICATION
GATE 1A — RULE12 TASK-AUTHOR ARCHITECTURE COMPLETION CHECK
GATE 2 — ARCHITECTURE / OWNERSHIP / PHASE COMPLIANCE
GATE 3 — SCOPE COMPLIANCE
GATE 4 — DIFF REVIEW
GATE 5 — TEST REVIEW
GATE 6 — EVIDENCE REVIEW
GATE 7 — MERGE CLOSURE
```

If PRE-GATE or any of Gates 0–3 fail:

```text
REVIEW = STOP
DO_NOT_REVIEW_IMPLEMENTATION_QUALITY
DO_NOT_FIX_TESTS
DO_NOT_SUGGEST_CODE_REWORK
DO_NOT_EXPAND_SCOPE
```

## PRE-GATE — Author Self-Check Evidence Verification

Every submitted task card must include the completed record required by:

```text
docs/governance/RD1_TASK_CARD_AUTHOR_PRE_SUBMISSION_SELF_CHECK.md
```

The independent reviewer MUST mechanically verify the evidence rather than trust the author's PASS claim.

Required checks:

```text
SELF_CHECK_RECORD_PRESENT
SELF_CHECK_RESULT = PASS
READY_FOR_SUBMISSION = YES
TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK = PASS
FROZEN_SOURCE_BINDING_COMPLETE = PASS
TASK_AUTHOR_NEW_ARCHITECTURE_DECISIONS = 0
ALL_REQUIRED_NEW_*_COUNT = 0
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
AUTHORITY_SOURCE_FILES_CHECKED are real/current
CURRENT_MAIN_SHAS mechanically verified
MANDATORY_TASK_FIELDS_PRESENT is complete
CROSS_BOUNDARY_SEMANTICS = PASS or legitimate N/A
```

Hard rules:

```text
NO_SELF_CHECK_EVIDENCE = REVIEW STOP
NO_RULE12_ARCHITECTURE_COMPLETION_EVIDENCE = REVIEW STOP
SELF_CHECK_CLAIM = SIGNAL_ONLY
SELF_CHECK_EVIDENCE = MUST_BE_VERIFIED
SELF_CHECK_PASS != OWNER_APPROVAL
SELF_CHECK_PASS != IMPLEMENTATION_AUTHORIZATION
```

## Gate 0 — Authority Identity

Verify mechanically:

```text
CURRENT_CONSTITUTION
CURRENT_RULE12_AMENDMENT
CURRENT_ARCHITECTURE_AUTHORITY_INDEX
GOVERNING_FROZEN_DOCUMENTS
CURRENT_PHASE
EXACT_TASK_CONTRACT
PARENT_CONTROL_CONTRACT_STATUS
REPO
BASE_SHA
TARGET_BRANCH
```

The Architecture Authority Index is a pointer/status register, not architecture law. Gate 0 must verify that the index points to the correct current sources; if the index conflicts with a frozen source, the source wins and the index must be rebound before review proceeds.

Questions:

```text
Is the task based on the current authorized trunk?
Does the task contract contain the mandatory authority header?
Is every cited authority currently effective?
Is any cited document superseded, candidate-only, or evidence-only?
Is any required parent control contract actually approved/active for this lifecycle step?
Does the Authority Index agree with the governing frozen source set?
```

Mandatory anti-confusion:

```text
OWNER_APPROVAL_CANDIDATE != APPROVED
DRAFT != ACTIVE_AUTHORITY
CANDIDATE != ACTIVE_AUTHORITY
LOOKS_VALID != ACTIVE_AUTHORITY
```

Failure result:

```text
AUTHORITY_IDENTITY_FAIL
→ REVIEW STOP
```

## Gate 1 — Rule 11 Classification

Verify any gap/conflict/deferred finding is classified under Rule 11 as:

```text
A = IMPLEMENTATION_GAP
B = IMPLEMENTATION_DEVIATION
C = DEFERRED_PHASE_CONCERN
D = TRUE_FROZEN_AUTHORITY_CONFLICT_OR_GAP
NO_ACTIVE_FINDING = ordinary task already fully defined by frozen authority
```

`UNKNOWN` or `UNRESOLVED` may never be treated as `NO_ACTIVE_FINDING`.

Mandatory anti-inference checks:

```text
CURRENT_MAIN_ABSENCE != ARCHITECTURE_ABSENCE
NO_PHYSICAL_CALLER != NO_LOGICAL_OWNER
NO_PACKAGE_RESOLUTION != NO_COMPOSITION_TOPOLOGY
TEST_PASS != ARCHITECTURE_PASS
AGENT_CONSENSUS != ARCHITECTURE_AUTHORITY
MISSING_INFORMATION != DESIGN_FREEDOM
NO_FROZEN_ANSWER_FOUND != PERMISSION_TO_INVENT
```

Any attempt to promote A/B/C to D using implementation facts is a hard fail.

## Gate 1A — Rule 12 Task-Author Architecture Completion Check

This gate asks a different question from the residual-decision audit:

```text
DID THE TASK AUTHOR ALREADY INVENT OR SILENTLY COMPLETE ARCHITECTURE
BEFORE THE IMPLEMENTATION AGENT RECEIVED THE CARD?
```

Verify all architecture-relevant claims in the task against effective frozen authority. Audit at minimum:

```text
owner
domain
composition root
binding authority
package/public-private boundary
dependency direction
runtime authority
transport requirement
lifecycle authority
cross-repo responsibility
ABI authority
phase ownership
```

Required result for ordinary implementation/correction tasks:

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

The reviewer MUST NOT accept these claims based only on the author's declarations. Re-resolve the relevant frozen clauses.

Forbidden rationalizations:

```text
"the code needs somewhere to bind"
"there is no existing composition root"
"this is the cleanest place"
"the tests imply this boundary"
"all Agents agree"
```

If a task author introduced any new architecture element without a completed explicit architecture-amendment/refreeze path:

```text
ARCHITECTURE_COMPLETION_PRECHECK = FAIL
TASK_CARD_INVALID
REVIEW = STOP
```

## Gate 2 — Architecture / Ownership / Phase Compliance

Verify proposed behavior against frozen architecture before reading implementation quality.

Check at minimum:

```text
semantic authority
ownership
construction owner
binding owner
execution owner
public/private boundary
ABI
provider boundary
dependency direction
phase ownership
fallback prohibition
```

The reviewer must answer:

```text
IS THIS IMPLEMENTATION OF THE FROZEN ARCHITECTURE?
OR IS IT QUIETLY DESIGNING A DIFFERENT ARCHITECTURE?
```

If the latter:

```text
ARCHITECTURE_DEVIATION
→ CANDIDATE INVALID
→ REVIEW STOP
```

No reviewer may invent a missing owner, layer, topology, ABI, dependency direction, or composition root in order to make a candidate reviewable.

### Gate 2A — Residual Decision Audit

Even when ownership/topology is correct, verify the implementation Agent is not being forced to decide any unfrozen contract semantics.

Check at minimum:

```text
status mapping
failure mapping
provenance mapping
lifecycle mapping
authorization meaning
fallback semantics
unknown-input behavior
malformed-input behavior
cross-repo responsibility
```

Required result:

```text
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
```

If not:

```text
TASK_CARD_NOT_READY
→ REVIEW STOP
```

### Gate 2B — Cross-Boundary Semantic Mapping

Mandatory for any adapter / bridge / translator / proxy / serializer / provider wrapper / public-boundary conversion / cross-repo contract conversion.

Verify exact frozen or explicitly task-frozen definitions for:

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

If any mapping is left for the implementation Agent to infer:

```text
CROSS_BOUNDARY_SEMANTICS_FAIL
→ REVIEW STOP
```

Permanent law:

```text
CROSS_BOUNDARY_SEMANTIC_MAPPING = FROZEN_BEFORE_CODING
AGENT_CROSS_BOUNDARY_SEMANTIC_FREEDOM = NO
```

## Gate 3 — Scope Compliance

Verify:

```text
changed paths ⊆ authorized paths
behavior change ⊆ required behavior
no deferred finding implemented
no future-phase concern pulled forward
no unrequested architecture cleanup
no compatibility/fallback added to make tests pass
```

Core principle:

```text
DISCOVER_MORE != DO_MORE
```

## Gate 4 — Diff Review

Only after PRE-GATE and Gates 0–3 pass, review implementation correctness, maintainability, and exact changes.

## Gate 5 — Test Review

Tests prove implementation behavior only.

```text
TESTS = EVIDENCE
TESTS != ARCHITECTURE_AUTHORITY
```

## Gate 6 — Evidence Review

Verify exact candidate SHA, source trace, commands/results, typed failures, absence of fallback, and any task-specific acceptance evidence.

Claims such as `PASS`, `done`, or `tests passed` are signals only until mechanically verified.

## Gate 7 — Merge Closure

Review is incomplete until:

```text
candidate exact SHA verified
target trunk exact SHA verified
merge completed
new trunk HEAD verified
candidate ancestry verified
task branch deleted/closed
```

If the available toolchain cannot delete the task branch, report:

```text
MERGE_CLOSURE = INCOMPLETE
BRANCH_CLEANUP = EXTERNALLY_REQUIRED
```

## Reviewer prohibited behavior

Reviewers, including Mira, Codex, Claude, and humans, must not:

```text
invent missing architecture
repair architecture through code suggestions
use current implementation as target authority
add a new ownership layer because wiring is absent
add a composition root because none is implemented
add a binding authority because code lacks one
promote future-phase closure into current-phase scope
accept architecture drift because tests are green
convert missing information into design freedom
trust author self-check PASS without evidence verification
permit implementation Agent to invent cross-boundary semantic mapping
```

When uncertain:

```text
SEARCH FROZEN AUTHORITY FIRST
CLASSIFY BEFORE DESIGN
RUN RULE12 CHECK BEFORE TASK ACCEPTANCE
```

No reviewer has autonomous architecture-completion authority.

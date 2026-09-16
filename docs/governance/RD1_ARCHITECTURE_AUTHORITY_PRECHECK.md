# RD1 Architecture / Authority Precheck

**Status:** CONTROL-PLANE CANDIDATE  
**Purpose:** make architecture/authority compliance the first review gate. Diff, tests, and runtime evidence are reviewed only after this precheck passes.

```text
ARCHITECTURE_PRECHECK_BEFORE_DIFF = REQUIRED
```

## Review order

Every implementation/rework review must execute in this order:

```text
GATE 0 — AUTHORITY IDENTITY
GATE 1 — RULE11 CLASSIFICATION
GATE 2 — ARCHITECTURE / OWNERSHIP / PHASE COMPLIANCE
GATE 3 — SCOPE COMPLIANCE
GATE 4 — DIFF REVIEW
GATE 5 — TEST REVIEW
GATE 6 — EVIDENCE REVIEW
GATE 7 — MERGE CLOSURE
```

If any of Gates 0–3 fail:

```text
REVIEW = STOP
DO_NOT_REVIEW_IMPLEMENTATION_QUALITY
DO_NOT_FIX_TESTS
DO_NOT_SUGGEST_CODE_REWORK
DO_NOT_EXPAND_SCOPE
```

The reviewer must first resolve the authority problem.

## Gate 0 — Authority Identity

Verify mechanically:

```text
CURRENT_CONSTITUTION
CURRENT_ARCHITECTURE_AUTHORITY_INDEX
GOVERNING_FROZEN_DOCUMENTS
CURRENT_PHASE
EXACT_TASK_CONTRACT
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
Does the Authority Index agree with the governing frozen source set?
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

Only after Gates 0–3 pass, review implementation correctness, maintainability, and exact changes.

## Gate 5 — Test Review

Tests prove implementation behavior only.

```text
TESTS = EVIDENCE
TESTS != ARCHITECTURE_AUTHORITY
```

A test that contradicts frozen architecture is the item to correct; the architecture is not changed to satisfy the test.

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

Never claim DONE while the task branch remains.

## Reviewer prohibited behavior

Reviewers, including Mira, Codex, Claude, and humans, must not:

```text
invent missing architecture
repair architecture through code suggestions
use current implementation as target authority
add a new ownership layer because wiring is absent
promote future-phase closure into current-phase scope
accept architecture drift because tests are green
convert missing information into design freedom
```

When uncertain:

```text
SEARCH FROZEN AUTHORITY FIRST
CLASSIFY BEFORE DESIGN
```

No reviewer has autonomous architecture-completion authority.

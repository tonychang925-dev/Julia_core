# RD1 Architecture Authority Index

**Status:** ACTIVE CONTROL PLANE  
**Purpose:** provide one canonical starting point for architecture authority resolution.  
**Important:** this index is a pointer/status register only. It is **not** an independent source of architecture law and cannot override the referenced frozen sources.

```text
AUTHORITY_INDEX = POINTER_ONLY
AUTHORITY_INDEX != ARCHITECTURE_LAW
SOURCE_DOCUMENTS_REMAIN_AUTHORITATIVE
```

## 1. Constitutional supremacy

```text
DOCUMENT = DEVELOPMENT_CONSTITUTION.md
REPO = tonychang925-dev/Julia_core
CONTROL_PLANE_ACTIVATION_BASE = 98c6b5c6fb6b2b4dfbcdcd3b50864b9b297f20b4
STATUS = ACTIVE / HIGHEST ENGINEERING DISCIPLINE
RULE11 = ACTIVE
RULE12 = ACTIVE VIA docs/governance/RD1_RULE12_ARCHITECTURE_COMPLETION_PROHIBITION.md
```

The Development Constitution governs the governance process itself. Rule 12 is an explicit Owner-approved, scope-bounded constitutional amendment that supplements Rule 11. No architecture document, task contract, implementation fact, test result, Agent conclusion, or Owner convenience instruction may bypass them.

```text
CONSTITUTIONAL_GOVERNANCE_SUPREMACY = YES
NO_ARCHITECTURE_COMPLETION_BY_AGENT_INFERENCE = YES
```

This is distinct from the scope-aware precedence used to resolve **architecture content** among frozen domain documents.

## 2. Frozen architecture-content resolution stack

Within the constitutional process, resolve architecture content using scope-aware precedence:

```text
1. explicit constitution-compliant, scope-bounded Owner amendment
2. R1C-A1 — Market Brain Unified Public Contract v0.2.1
3. R1B — Freeze / Cleanup Amendments v0.3.1
4. latest Julia Core Architecture Re-Audit
5. G0 — Owner Correction Source + Composition Baseline Card v0.1
```

Rules:

```text
LOWER_LEVEL_EVIDENCE_CANNOT_REDEFINE_HIGHER_FROZEN_AUTHORITY = YES
OWNER_CONVENIENCE_INSTRUCTION_IS_NOT_CONSTITUTIONAL_OVERRIDE = YES
SCOPE_AWARE_PRECEDENCE_REQUIRED = YES
```

Historical R-line / M-line / recovery candidates are evidence only under the current clean-main development model.

## 3. Current Master Plan

```text
DOCUMENT = RD1_V1_Unified_Architecture_Development_Master_Plan_v1.1.6_CURRENT_MAIN_CLEAN_REIMPLEMENTATION_2026-09-15
STATUS = CURRENT PLAN AUTHORITY
DEVELOPMENT_MODEL = CURRENT MAIN CLEAN REIMPLEMENTATION
```

The Master Plan governs phase sequencing and clean-main execution. It does not override a higher frozen architecture boundary outside its scope.

## 4. Current phase

```text
CURRENT_PHASE = RC4
RC4_PURPOSE = first canonical three-repo text path
```

Frozen high-level RC4 path:

```text
Assistant
→ Core cognition/runtime
→ structured Market capability
→ C08
→ Market Public Boundary
→ typed Market result
→ C03
→ Julia continuation
→ Assistant response
```

Future-phase concerns must not be promoted into RC4 blockers unless an existing frozen dependency gate explicitly requires it.

```text
RC9  = Candidate Manifest + Runtime Identity
RC10 = minimal E2E bound to exact manifest/runtime
RC11 = controlled cutover
```

## 5. Repository SHA snapshot — implementation evidence only

```text
Julia_core activation-base snapshot
= 98c6b5c6fb6b2b4dfbcdcd3b50864b9b297f20b4

Julia-AI-Assistant snapshot
= fe0b2065e572a20d191cea75dafb16da98f83c93

ai_theme_app snapshot
= 7925a63bb5500a74496c1e7d7b2b42c935f2c739
```

These SHAs are implementation-state evidence, not architecture authority and not permanent task-base authority. Every task must mechanically re-check current trunk identity before authorization.

```text
INDEX_SHA_SNAPSHOT != CURRENT_TRUNK_PROOF
INDEX_SHA_SNAPSHOT != TASK_BASE_AUTHORITY
```

## 6. Current implementation-contract status

```text
RC4-F1B Exact Production Integration Locus v0.2
= FROZEN DESIGN AUTHORITY FOR F1B LOCUS

F1B Amendment v0.2.1
= REQUIRES RULE11-COMPLIANT CORRECTION BEFORE FREEZE

Stage B Exact Implementation Contract v0.2
= NOT EXECUTABLE AFTER CORE BASE DRIFT
= REBIND REQUIRED

RC4-F1B-C Cross-Repo Public Export Resolution Law v0.1
= NOT ARCHITECTURE AUTHORITY
= RECLASSIFY AS AUDIT / DEFERRED PRODUCTION-COMPOSITION FINDING
```

No document listed as `NOT EXECUTABLE`, `CANDIDATE`, `REQUIRES CORRECTION`, or `NOT ARCHITECTURE AUTHORITY` may be used as implementation authorization.

## 7. Superseded / non-authoritative classes

```text
historical R-line branches
historical M-line branches
recovery branches
historical accepted candidates
old candidate SHAs
old PR comments
Codex completion claims
PASS / tests passed claims
runtime behavior
```

All are:

```text
EVIDENCE_ONLY
NO_ARCHITECTURE_AUTHORITY
NO_TASK_BASE_AUTHORITY
NO_FALLBACK_AUTHORITY
```

## 8. Required Agent startup behavior

Before architecture analysis, task creation, delegation, implementation, or review, every Agent must read this index and then resolve the referenced frozen sources relevant to the task.

```text
READ_INDEX
→ IDENTIFY_GOVERNING_FROZEN_AUTHORITY
→ FROZEN_AUTHORITY_TRACE
→ RULE11_CLASSIFICATION
→ RULE12_ARCHITECTURE_COMPLETION_CHECK
→ CONTROL_PLANE_FRESHNESS_CHECK
→ PHASE_CHECK
→ EXACT_CONTRACT
→ AGENT_EXECUTION_PERMISSION_MATRIX
```

The index is a routing/control artifact, not a substitute for reading governing source clauses.

If the index is stale or contradicts a referenced frozen source:

```text
SOURCE_DOCUMENT_WINS
INDEX = STALE
TASK = STOP
INDEX_REBIND_REQUIRED = YES
```

The index may never be used to invent missing architecture.

## 9. Mandatory control-plane companions

Every task author, implementation Agent, and reviewer must use:

```text
docs/governance/RD1_RULE12_ARCHITECTURE_COMPLETION_PROHIBITION.md
docs/governance/RD1_CONTROL_PLANE_FRESHNESS_GATE.md
docs/governance/RD1_AGENT_TASK_AUTHORITY_HEADER_TEMPLATE.md
docs/governance/RD1_TASK_CARD_AUTHOR_PRE_SUBMISSION_SELF_CHECK.md
docs/governance/RD1_TASK_CARD_CI_PARSER_GATE.md
docs/governance/RD1_AGENT_EXECUTION_PERMISSION_MATRIX.md
docs/governance/RD1_ARCHITECTURE_AUTHORITY_PRECHECK.md
```

These documents operationalize the Constitution. They do not create architecture authority beyond the Constitution and referenced frozen sources.

Mandatory lifecycle:

```text
TASK_CARD_DRAFT
→ RULE11_CLASSIFICATION
→ RULE12_TASK_AUTHOR_ARCHITECTURE_COMPLETION_AUDIT
→ AUTHOR_SELF_CHECK
→ CONTROL_PLANE_FRESHNESS_CHECK
→ AGENT_EXECUTION_PERMISSION_MATRIX
→ MACHINE_VERIFIABLE_SELF_CHECK_EVIDENCE
→ SELF_CHECK_PASS
→ FRESHNESS_REVALIDATION_AT_SUBMISSION
→ CI / PARSER GATE
→ INDEPENDENT_ARCHITECTURE_PRECHECK
→ FRESHNESS_REVALIDATION_AT_AUTHORITY_TRANSITION
→ OWNER / AUTHORIZED REVIEW
→ POSSIBLE IMPLEMENTATION AUTHORIZATION
```

Hard law:

```text
NO_SELF_CHECK_EVIDENCE = NO_TASK_SUBMISSION
NO_RULE12_ARCHITECTURE_COMPLETION_EVIDENCE = NO_TASK_SUBMISSION
NO_CONTROL_PLANE_FRESHNESS_EVIDENCE = NO_TASK_SUBMISSION
NO_PERMISSION_MATRIX = NO_TASK_SUBMISSION
ANY_PERMISSION_NOT_EXPLICITLY_GRANTED = DENY
SELF_CHECK_PASS != OWNER_APPROVAL
SELF_CHECK_PASS != IMPLEMENTATION_AUTHORIZATION
CONTROL_PLANE_DRIFT = SELF_CHECK_INVALIDATED
TASK_CARD_GOVERNANCE_GATE_FAIL = NO_MERGE_WHILE_REQUIRED_CHECK_IS_ENFORCED
```

The parser gates run inside the already-required `NO_CRITICAL_FALLBACK_GATE` GitHub check. They validate structure/self-check evidence, Rule 12 architecture-completion declarations, permission-matrix completeness, residual decision counts, cross-boundary semantic mapping, declared task-base SHA against the current `main` SHA of the declared repository, and the self-check control-plane SHA against current `Julia_core/main`.

```text
PARSER = GOVERNANCE_ENFORCER
PARSER != ARCHITECTURE_LAW
```

## 10. Control-plane freshness / TOCTOU rule

A self-check PASS is bound to the exact Julia Core control-plane HEAD it checked.

```text
CONTROL_PLANE_AUTHORITY_REPO
= tonychang925-dev/Julia_core

SELF_CHECK_CONTROL_PLANE_SHA
= <exact Julia_core/main SHA used by self-check>

CONTROL_PLANE_FRESHNESS_CHECK
= PASS
```

At every authority transition that can advance work, current `Julia_core/main` must be fetched again.

```text
SELF_CHECK_CONTROL_PLANE_SHA
== CURRENT_JULIA_CORE_MAIN_SHA
= REQUIRED
```

If false or unverifiable:

```text
CONTROL_PLANE_DRIFT_OR_UNVERIFIED
→ SELF_CHECK_INVALIDATED
→ READY_FOR_SUBMISSION = NO
→ TASK_REBIND_REQUIRED = YES
```

Implementation-base freshness and control-plane freshness are independent and both required.

## 11. Anti-free-form Agent rule

```text
NO_FROZEN_ANSWER_FOUND != PERMISSION_TO_INVENT
MISSING_INFORMATION != DESIGN_FREEDOM
NO_PHYSICAL_CALLER != NO_LOGICAL_OWNER
NO_CURRENT_IMPLEMENTATION != NO_ARCHITECTURE
NO_PACKAGE_RESOLUTION != NO_COMPOSITION_TOPOLOGY
NO_EXISTING_COMPOSITION_ROOT != PERMISSION_TO_CREATE_ONE
CROSS_BOUNDARY_SEMANTIC_MAPPING = FROZEN_BEFORE_CODING
AGENT_CROSS_BOUNDARY_SEMANTIC_FREEDOM = NO
ANY_PERMISSION_NOT_EXPLICITLY_GRANTED = DENY
NO_ARCHITECTURE_COMPLETION_BY_AGENT_INFERENCE = YES
CONTROL_PLANE_FRESHNESS_REQUIRED = YES
```

When an Agent cannot resolve a frozen answer or permission:

```text
SEARCH
TRACE
CLASSIFY
RULE12_CHECK
FRESHNESS_CHECK
CHECK_PERMISSION_MATRIX
STOP_IF_D_OR_DENIED_OR_STALE
```

Never:

```text
INFER_NEW_OWNERSHIP
INVENT_NEW_TOPOLOGY
CREATE_NEW_AUTHORITY_LAYER
INFER_NEW_COMPOSITION_ROOT_FROM_WIRING_ABSENCE
INFER_NEW_BINDING_AUTHORITY_FROM_IMPLEMENTATION_GAP
INFER_NEW_PACKAGE_BOUNDARY_FROM_CODE_LAYOUT
INFER_NEW_DEPENDENCY_DIRECTION_FROM_CONVENIENCE
EXPAND_PHASE_BY_REASONING
INVENT_STATUS_MAPPING
INVENT_FAILURE_MAPPING
INVENT_PROVENANCE_MAPPING
INVENT_LIFECYCLE_MAPPING
INVENT_AUTHORIZATION_MEANING
INFER_PERMISSION_FROM_SILENCE
REUSE_STALE_SELF_CHECK_PASS_AFTER_CONTROL_PLANE_DRIFT
```

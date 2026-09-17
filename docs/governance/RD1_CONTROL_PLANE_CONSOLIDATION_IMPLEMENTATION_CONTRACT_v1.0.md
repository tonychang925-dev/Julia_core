# RD1 Control Plane Consolidation Implementation Contract v1.0

**Status:** OWNER-AUTHORIZED IMPLEMENTATION CONTRACT  
**Task:** implement the approved v1.1 consolidation model as one governance semantic atom.

```text
TASK_ID
= RD1-G-CONS-1

TASK_TYPE
= STANDARD

REPO
= tonychang925-dev/Julia_core

BASE_SHA
= 8c17edb596622e23aecb29b27bb50e3055ed2071

TARGET_BRANCH
= governance/rd1-control-plane-consolidation-v1-1

CONTROL_PLANE_COMPATIBILITY_VERSION
= 1

CONTROL_PLANE_COMPATIBILITY_IMPACT
= BREAKING

CURRENT_PHASE
= governance consolidation before return to RC4

RULE11_CLASSIFICATION
= B

FROZEN_AUTHORITY_BINDING
= DEVELOPMENT_CONSTITUTION.md
+ RD1_CONTROL_PLANE_CONSOLIDATION_CONSTITUTIONAL_AMENDMENT_v1.1.md
+ RD1_V1_Control_Plane_Consolidation_and_Semantic_Atomicity_Plan_v1.1.md

ARCHITECTURE_DELTA
= NONE outside the explicitly Owner-approved governance execution amendment

TARGET_REQUIREMENT
= migrate the active RD1 governance mechanics from exact-control-plane-SHA coupling and file-count-biased task enforcement to compatibility-versioned freshness, semantic atomicity, explicit task type, simplified Rule12 proof, and finite evidence-based review while preserving Rule11/12, default-deny permissions, exact implementation BASE_SHA, and authorization separation

SEMANTIC_ATOM
= one control-plane compatibility and task-governance execution model closure

VALID_MERGE_END_STATE
= Constitution/Authority Index/docs/parser/freshness gate/tests/CI all enforce one coherent v1.1 model with no parallel exact-SHA compatibility regime and no keyword-inferred task type
```

## Authorized paths

```text
DEVELOPMENT_CONSTITUTION.md
RD1_ARCHITECTURE_AUTHORITY_INDEX.md
docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md
docs/governance/RD1_CONTROL_PLANE_CONSOLIDATION_CONSTITUTIONAL_AMENDMENT_v1.1.md
docs/governance/RD1_V1_Control_Plane_Consolidation_and_Semantic_Atomicity_Plan_v1.1.md
docs/governance/RD1_CONTROL_PLANE_CONSOLIDATION_IMPLEMENTATION_CONTRACT_v1.0.md
docs/governance/RD1_CONTROL_PLANE_FRESHNESS_GATE.md
docs/governance/RD1_TASK_CARD_AUTHOR_PRE_SUBMISSION_SELF_CHECK.md
docs/governance/RD1_TASK_CARD_CI_PARSER_GATE.md
docs/governance/RD1_ARCHITECTURE_AUTHORITY_PRECHECK.md
docs/governance/RD1_AGENT_TASK_AUTHORITY_HEADER_TEMPLATE.md
tools/control_plane_freshness_gate.py
tools/task_card_governance_gate.py
tests/governance/test_control_plane_freshness_gate.py
tests/governance/test_task_card_governance_gate.py
.github/workflows/no-critical-fallback-gate.yml
```

Everything else is forbidden.

## Required behavior

```text
1. v1.1 plan is canonical; v1.0 is evidence-only.
2. compatibility version 1 is the first versioned control plane.
3. no EFFECTIVE_FROM_SHA field exists.
4. Git history resolves SHA → compatibility version.
5. non-breaking SHA drift alone does not stale task cards.
6. compatibility change requires revalidation; unaffected tasks may be revalidated without rewrite.
7. Rule12 normal-task proof becomes ARCHITECTURE_DELTA=NONE + FROZEN_AUTHORITY_BINDING.
8. Rule11-D requires positive proof.
9. task semantic atom is one invariant closure and may span required files.
10. ONE_REPO is preferred, not absolute.
11. Permission Matrix remains default deny.
12. TASK_TYPE is explicit; parser does not infer cross-boundary type from prose keywords.
13. review stops after authority/atomicity/permission/evidence pass; new opinion alone cannot reopen.
14. exact target BASE_SHA remains strict.
15. existing authorization separation remains strict.
```

## Forbidden behavior

```text
NO Rule13
NO architecture-content rewrite
NO RC4 runtime code
NO Market code
NO Assistant code
NO fallback relaxation
NO merge/release/deploy authority expansion
NO silent acceptance of invalid task BASE_SHA
NO parallel old exact-SHA compatibility regime after merge
```

## Permission matrix

```text
AGENT_EXECUTION_PERMISSION_MATRIX

PERMISSION_MODEL
= DEFAULT_DENY

PERMISSION_REPOSITORY
= tonychang925-dev/Julia_core

PERMISSION_BASE_SHA
= 8c17edb596622e23aecb29b27bb50e3055ed2071

PERMISSION_TARGET_BRANCH
= governance/rd1-control-plane-consolidation-v1-1

READ_SCOPE
= authorized governance/control-plane files plus exact frozen authority needed for verification

WRITE_SCOPE
= AUTHORIZED_PATHS above only

ARCHITECTURE_MUTATION
= DENY outside the explicit Owner-approved governance execution amendment

PUBLIC_CONTRACT_MUTATION
= DENY

CROSS_BOUNDARY_SEMANTIC_DECISION
= DENY

DEPENDENCY_MUTATION
= DENY

TEST_CREATION
= BOUNDED_TO_ACCEPTANCE_EVIDENCE

BRANCH_CREATION
= EXACT_TARGET_ONLY

COMMIT
= TASK_BRANCH_ONLY

PR_CREATION
= ALLOW

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

## Acceptance evidence

```text
exact candidate SHA
base-to-candidate changed-path proof
focused governance tests
full governance sabotage/unit suite
NO_CRITICAL_FALLBACK_GATE result
manual Authority/Atomicity/Permission/Evidence review
proof no unauthorized paths changed
proof task BASE_SHA exact enforcement remains
proof exact-SHA control-plane drift no longer auto-invalidates compatible tasks
proof compatibility-version change revalidation works
proof keyword-only 'adapter' no longer triggers cross-boundary gate
proof explicit TASK_TYPE=CROSS_BOUNDARY still requires frozen mappings
```

```text
MERGE_AUTHORIZATION = NO
RELEASE = NO
DEPLOY = NO
```

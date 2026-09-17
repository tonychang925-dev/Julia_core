# RD1 Active Architecture / Engineering Index

**Date:** 2026-09-17  
**Status:** ACTIVE  
**Purpose:** lightweight pointer to the current RD1 architecture and engineering rules.

## Active sources

```text
Architecture:
docs/architecture/RD1_V1_ARCHITECTURE_CONSTITUTION_LITE.md

Development rules:
DEVELOPMENT_CONSTITUTION.md

Engineering governance:
docs/governance/RD1_ENGINEERING_GOVERNANCE_LITE.md

Acceptance / release:
docs/governance/RD1_ACCEPTANCE_AND_RELEASE.md
```

These documents define current day-to-day RD1 development behavior.

## Development truth

```text
main/current trunk = development truth
exact task base SHA = task start identity
historical branches/candidates = reference/evidence only
```

## Architecture change threshold

Treat a change as architecture-level only when it changes one of:

```text
component ownership
dependency direction
public/private boundary
public contract semantics
tool evidence re-entry
fallback policy
Julia final-judgment responsibility
```

Ordinary implementation details do not require architecture adjudication.

## Retired active-control-plane machinery

The following recovery-era/control-plane documents remain historical/reference material but are no longer mandatory startup or task documents:

```text
docs/governance/RD1_CONTROL_PLANE_CONSOLIDATION_CONSTITUTIONAL_AMENDMENT_v1.1.md
docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md
docs/governance/RD1_RULE12_ARCHITECTURE_COMPLETION_PROHIBITION.md
docs/governance/RD1_CONTROL_PLANE_FRESHNESS_GATE.md
docs/governance/RD1_AGENT_TASK_AUTHORITY_HEADER_TEMPLATE.md
docs/governance/RD1_TASK_CARD_AUTHOR_PRE_SUBMISSION_SELF_CHECK.md
docs/governance/RD1_TASK_CARD_CI_PARSER_GATE.md
docs/governance/RD1_AGENT_EXECUTION_PERMISSION_MATRIX.md
docs/governance/RD1_ARCHITECTURE_AUTHORITY_PRECHECK.md
docs/governance/RD1_V1_Control_Plane_Consolidation_and_Semantic_Atomicity_Plan_v1.1.md
```

Their historical rationale may still be consulted. They do not override the active Lite documents above.

## Minimal task contract

```text
TASK_ID
REPO / REPOS
BASE_SHA / BASE_SHAS
GOAL
ALLOWED_PATHS
FORBIDDEN_PATHS
ACCEPTANCE_TESTS
EXPECTED_EVIDENCE
```

No additional authority/compatibility/phase taxonomy is mandatory for an ordinary engineering task.

## Permanent concise principles

```text
ONE DEVELOPMENT TRUTH
RESPECT ARCHITECTURE BOUNDARIES
STAY IN TASK SCOPE
NO HIDDEN FALLBACK / SYNTHETIC SUCCESS
PROVE THE RESULT
```

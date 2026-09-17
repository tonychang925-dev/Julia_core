# RD1 Control-Plane Compatibility Metadata

**Status:** CANONICAL COMPATIBILITY METADATA SOURCE  
**Scope:** RD1 governance/task-contract compatibility only  
**Architecture authority:** NONE

```text
CONTROL_PLANE_COMPATIBILITY_VERSION
= 1

PREVIOUS_COMPATIBILITY_VERSION
= UNVERSIONED

CHANGE_SUMMARY
= Initial consolidated control plane: compatibility-version freshness, simplified Rule12 operational proof, semantic-atomic task sizing, explicit task type, finite evidence-based review.
```

## Canonical resolution

```text
CANONICAL_COMPATIBILITY_SOURCE
= docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md

NORMATIVE_PAYLOAD
= CONTROL_PLANE_COMPATIBILITY_VERSION

SHA_TO_VERSION_RESOLUTION
= read this canonical source at the exact Git SHA being evaluated
```

The file MUST NOT contain `EFFECTIVE_FROM_SHA`. Git history itself provides SHA → version mapping.

```text
COMPATIBILITY_METADATA
!= ARCHITECTURE_LAW
!= OWNER_APPROVAL
!= IMPLEMENTATION_AUTHORIZATION
```

## Normative governance PR declaration

Every normative governance PR MUST declare exactly one:

```text
CONTROL_PLANE_COMPATIBILITY_IMPACT
= NONE
| BREAKING
```

```text
BREAKING
→ CONTROL_PLANE_COMPATIBILITY_VERSION increments exactly once

NONE
→ CONTROL_PLANE_COMPATIBILITY_VERSION does not increment
```

The declaration is an author claim. Independent review verifies whether it is truthful. CI validates declaration/version consistency only.

## Initial transition

```text
LEGACY_CONTROL_PLANE
= UNVERSIONED

CONSOLIDATED_CONTROL_PLANE
= CONTROL_PLANE_COMPATIBILITY_VERSION 1

INITIAL_CONSOLIDATION_IMPACT
= BREAKING
```

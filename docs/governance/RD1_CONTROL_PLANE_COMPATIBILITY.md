# RD1 Control-Plane Compatibility

**Status:** ACTIVE ON MERGE  
**Scope:** RD1 task-contract governance compatibility metadata only.

```text
CONTROL_PLANE_COMPATIBILITY_VERSION
= 1

PREVIOUS_COMPATIBILITY_VERSION
= UNVERSIONED

CONTROL_PLANE_COMPATIBILITY_IMPACT
= BREAKING
```

This is compatibility metadata only.

```text
COMPATIBILITY_METADATA != ARCHITECTURE_LAW
COMPATIBILITY_METADATA != OWNER_APPROVAL
COMPATIBILITY_METADATA != IMPLEMENTATION_AUTHORIZATION
```

The file MUST NOT contain `EFFECTIVE_FROM_SHA`.

SHA-to-version resolution is provided by Git history:

```text
git show <SHA>:docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md
→ CONTROL_PLANE_COMPATIBILITY_VERSION = N
```

The legacy control plane before this consolidation is `UNVERSIONED`. This consolidation is the first versioned compatibility transition and is intentionally `BREAKING` because it changes task-card schema, freshness semantics, Rule 12 operational proof, parser semantics, and review flow.

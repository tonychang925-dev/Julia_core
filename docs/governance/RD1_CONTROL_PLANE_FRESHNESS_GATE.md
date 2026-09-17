# RD1 Control-Plane Compatibility / Freshness Gate

**Status:** ACTIVE CONTROL PLANE AFTER CONSOLIDATION MERGE  
**Scope:** RD1 coding task cards and authority transitions across Julia Core / Julia-AI-Assistant / Market Brain.

## 1. Purpose

Prevent governance TOCTOU without coupling task validity to every `Julia_core/main` SHA movement.

```text
CONTROL_PLANE_COMPATIBILITY_REQUIRED = YES
```

Canonical compatibility source:

```text
docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md
```

## 2. Required task fields

Every coding task card MUST carry:

```text
CONTROL_PLANE_AUTHORITY_REPO
= tonychang925-dev/Julia_core

SELF_CHECK_CONTROL_PLANE_COMPATIBILITY_VERSION
= <integer>

SELF_CHECK_CONTROL_PLANE_SHA
= <exact 40-hex SHA observed by author>

CONTROL_PLANE_FRESHNESS_CHECK
= PASS
```

The SHA is evidence only. Compatibility is determined by the version.

## 3. Compatibility equation

At Owner approval, implementation start, and merge review, resolve the current compatibility version from the exact current `Julia_core/main`:

```text
git show <CURRENT_JULIA_CORE_MAIN_SHA>:docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md
```

Required:

```text
SELF_CHECK_CONTROL_PLANE_COMPATIBILITY_VERSION
== CURRENT_CONTROL_PLANE_COMPATIBILITY_VERSION
```

If Julia Core SHA changed but version did not:

```text
CONTROL_PLANE_SHA_CHANGED
+ COMPATIBILITY_VERSION_UNCHANGED
→ TASK_REMAINS_GOVERNANCE_COMPATIBLE
```

If version changed:

```text
COMPATIBILITY_VERSION_CHANGED
→ COMPATIBILITY_REVALIDATION_REQUIRED
```

Version change does not automatically invalidate the task:

```text
CHANGE_NOT_APPLICABLE
→ REVALIDATED
→ CONTINUE

CHANGE_APPLICABLE
→ REBIND_REQUIRED
```

## 4. Dual-baseline rule

Implementation identity remains strict and independent:

```text
TASK_BASE_SHA == CURRENT_TASK_REPO_MAIN_SHA
```

Governance compatibility:

```text
TASK_CONTROL_PLANE_COMPATIBILITY_VERSION
== CURRENT_CONTROL_PLANE_COMPATIBILITY_VERSION
```

Both are required.

## 5. Machine enforcement

`tools/control_plane_freshness_gate.py` enforces:

```text
CONTROL_PLANE_AUTHORITY_REPO exact
SELF_CHECK_CONTROL_PLANE_COMPATIBILITY_VERSION present/integer
SELF_CHECK_CONTROL_PLANE_SHA exact 40-hex evidence
CONTROL_PLANE_FRESHNESS_CHECK = PASS
current compatibility version resolvable
self-check version == current version
```

It MUST NOT fail solely because the observed SHA differs from current SHA when compatibility version is unchanged.

```text
FRESHNESS_GATE = GOVERNANCE_ENFORCER
FRESHNESS_GATE != ARCHITECTURE_LAW
FRESHNESS_GATE != OWNER_APPROVAL
FRESHNESS_GATE != IMPLEMENTATION_AUTHORIZATION
```

## 6. Fail closed

If current compatibility cannot be resolved:

```text
CONTROL_PLANE_COMPATIBILITY = UNVERIFIED
→ GATE FAIL
→ ADVANCE = FORBIDDEN
```

## 7. Initial transition

```text
LEGACY_CONTROL_PLANE = UNVERSIONED
CONSOLIDATED_CONTROL_PLANE = VERSION 1
INITIAL_CONSOLIDATION_IMPACT = BREAKING
```

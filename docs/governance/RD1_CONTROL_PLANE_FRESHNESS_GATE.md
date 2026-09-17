# RD1 Control-Plane Freshness Gate

**Status:** ACTIVE CONTROL PLANE CANDIDATE  
**Scope:** every RD1 coding task card, Owner review, implementation authorization, delegation, branch creation, implementation start, and merge review across Julia Core / Julia-AI-Assistant / Market Brain.

## 1. Purpose

This gate closes a time-of-check/time-of-use governance race: a task card may self-check against one Julia Core control-plane HEAD, then be submitted or authorized after the control plane has advanced.

```text
SELF_CHECK_PASS_AT_T1
!= PASS_AT_SUBMISSION_OR_AUTHORIZATION_T2
```

Permanent rule:

```text
CONTROL_PLANE_FRESHNESS_REQUIRED = YES
```

## 2. Canonical control-plane identity

```text
CONTROL_PLANE_AUTHORITY_REPO
= tonychang925-dev/Julia_core
```

Every coding task card MUST carry:

```text
SELF_CHECK_CONTROL_PLANE_SHA
= <exact 40-hex Julia_core/main SHA used by the author self-check>

CONTROL_PLANE_FRESHNESS_CHECK
= PASS
```

The SHA is evidence of the exact governance/control-plane state used by the author. It is not architecture law by itself.

## 3. Freshness equation

Immediately before a task card is submitted for independent/Owner review, the current `Julia_core/main` MUST be fetched again and compared with the self-check SHA.

```text
SUBMISSION_CONTROL_PLANE_SHA
= freshly verified Julia_core/main

SELF_CHECK_CONTROL_PLANE_SHA
== SUBMISSION_CONTROL_PLANE_SHA
= REQUIRED
```

If they differ:

```text
CONTROL_PLANE_DRIFT
→ SELF_CHECK_INVALIDATED
→ READY_FOR_SUBMISSION = NO
→ TASK_REBIND_REQUIRED = YES
```

No stale PASS may be carried forward.

## 4. Dual-baseline rule

Task implementation identity and governance identity are independent and MUST both be fresh.

```text
TASK_BASE_SHA
= declared task repository main SHA

SELF_CHECK_CONTROL_PLANE_SHA
= Julia_core/main SHA used for self-check
```

Required before submission/use:

```text
TASK_BASE_SHA == CURRENT_TASK_REPO_MAIN_SHA
AND
SELF_CHECK_CONTROL_PLANE_SHA == CURRENT_JULIA_CORE_MAIN_SHA
```

A current implementation base does not excuse a stale control-plane base, and vice versa.

## 5. Mandatory revalidation points

Freshness MUST be revalidated at every authority transition that can permit work to advance:

```text
TASK_SUBMISSION
OWNER_REVIEW
IMPLEMENTATION_AUTHORIZATION
DELEGATION
BRANCH_CREATION
IMPLEMENTATION_START
MERGE_REVIEW
```

If the control plane advances after an earlier PASS, the previous PASS becomes stale automatically.

```text
CONTROL_PLANE_HEAD_CHANGE
→ PRIOR_SELF_CHECK_FRESHNESS = STALE
→ REBIND / RECHECK BEFORE ADVANCE
```

## 6. Independent-review duty

Independent reviewers MUST freshly resolve `Julia_core/main` rather than trusting the task card's declared `CURRENT_MAIN_SHAS` or `CONTROL_PLANE_FRESHNESS_CHECK`.

```text
AUTHOR_FRESHNESS_CLAIM = SIGNAL_ONLY
CURRENT_CONTROL_PLANE_HEAD = MUST_BE_REVERIFIED
```

If Rule 12, the Constitution, Authority Index, self-check rules, permission matrix, parser gate, architecture precheck, or another active governance companion changed since self-check, the task card must be rebound to the current control plane before review proceeds.

## 7. Machine enforcement

`tools/control_plane_freshness_gate.py` MUST reject task-card submissions when:

```text
CONTROL_PLANE_AUTHORITY_REPO is missing or not tonychang925-dev/Julia_core
SELF_CHECK_CONTROL_PLANE_SHA is missing or not exact 40-hex
CONTROL_PLANE_FRESHNESS_CHECK != PASS
SELF_CHECK_CONTROL_PLANE_SHA != current Julia_core/main
```

The machine gate enforces freshness only. It does not determine architecture truth or Owner approval.

```text
FRESHNESS_GATE = GOVERNANCE ENFORCER
FRESHNESS_GATE != ARCHITECTURE LAW
FRESHNESS_GATE != OWNER APPROVAL
FRESHNESS_GATE != IMPLEMENTATION AUTHORIZATION
```

## 8. Fail-closed behavior

If GitHub/current-head verification is unavailable:

```text
CONTROL_PLANE_FRESHNESS = UNVERIFIED
→ GATE FAIL
→ ADVANCE = FORBIDDEN
```

Never assume the control plane is unchanged because it cannot be reached.

## 9. Core principle

> **A self-check PASS is valid only against the exact control-plane HEAD it checked, and only while that HEAD remains current at the next authority transition.**

# Julia Core / RD1 Development Rules Lite v2.0

**Date:** 2026-09-17  
**Owner:** Tony  
**Status:** ACTIVE / OWNER APPROVED  
**Purpose:** replace recovery-era eleven-rule governance with five normal engineering rules.

Architecture source:

```text
docs/architecture/RD1_V1_ARCHITECTURE_CONSTITUTION_LITE.md
```

Engineering governance source:

```text
docs/governance/RD1_ENGINEERING_GOVERNANCE_LITE.md
```

Acceptance/release source:

```text
docs/governance/RD1_ACCEPTANCE_AND_RELEASE.md
```

---

## Rule 1 — One Development Truth

```text
main/current trunk = development truth
task = exact repo + exact base SHA
task branch = merge or delete
```

Historical branches, old PRs, old candidates, and branch names do not become current development truth by implication.

Protected research branches such as `mira/*` may remain for research continuity, but they do not become RD1 task bases or production fallbacks merely because they exist.

---

## Rule 2 — Respect Architecture Boundaries

Implementation must not silently change:

```text
component ownership
dependency direction
public/private boundary
public contract semantics
Julia final-judgment responsibility
```

If a task intentionally changes one of these, make the architecture change explicit and Owner-approved before implementation.

Ordinary implementation details do not require architecture adjudication.

---

## Rule 3 — Stay in Task Scope

A task states:

```text
goal
repo(s)
base SHA(s)
allowed paths
forbidden paths
acceptance tests
expected evidence
```

Modify only what is needed for that task.

Cross-repository implementation is allowed when the product slice genuinely requires it. Cross-repo coordination is not itself an architecture violation.

---

## Rule 4 — No Hidden Fallback or Synthetic Success

```text
required dependency unavailable
→ visible failure / missing evidence
```

Do not silently substitute:

```text
legacy path
mock
fake data
stub success
historical implementation
```

A degraded answer may use remaining real evidence only when the missing evidence remains visible to Julia/user semantics.

---

## Rule 5 — Prove the Result

A candidate passes when:

```text
scope is respected
acceptance tests pass
required evidence is present
architecture boundaries remain intact
```

Merge, release, and deploy are explicit lifecycle actions and are not implied by test/review PASS.

---

## Minimal operating model

```text
Architecture review:
Does it violate Architecture Constitution Lite?

Code review:
Does it satisfy the task and tests?

Project review:
Does it advance the product?

Release review:
Is this exact build ready to ship?
```

No additional governance taxonomy is required unless repeated concrete engineering failures demonstrate a real need.

---

## Superseded recovery-era machinery

The following concepts are no longer mandatory for ordinary RD1 engineering:

```text
A/B/C/D Rule11 classification
Frozen Authority Trace
CONTROL_PLANE_COMPATIBILITY_VERSION task binding
CONTROL_PLANE_SHA_OBSERVED task binding
CURRENT_PHASE task field
FROZEN_AUTHORITY_BINDING task field
AGENT_EXECUTION_PERMISSION_MATRIX
mandatory semantic-atomicity gate fields
mandatory authority-header/self-check/parser ceremony
```

Historical governance documents remain repository history/reference. They are not active day-to-day engineering law unless explicitly reactivated by an Owner-approved change.

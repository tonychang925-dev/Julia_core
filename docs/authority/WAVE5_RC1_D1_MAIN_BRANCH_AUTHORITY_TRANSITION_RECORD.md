# WAVE5 RC1 D1 — Main Branch Authority Transition Record

**Status:** DRAFT FOR DECISION
**Date:** 2026-08-25
**Purpose:** Decide the final role of the `main` branch under the new authority
model. This record decides repository branch authority transition; it does
**not** execute branch mutation.

---

## 1. Decision Scope

This record answers one question: **what is `main`'s role now that
`wave5/authority-consolidation` is the confirmed successor authority lineage?**

It does NOT authorize any `git` operation. Execution (if any) is gated behind
a separate D1-E readiness check.

## 2. Current State (verified facts)

| Object | HEAD | Role |
|---|---|---|
| `main` | `5bc33ba` | legacy default branch; superseded authority artifacts (CLN-04) |
| `cm-r0-fix` | `b0dedbe` | historical authority anchor; successor of main |
| `wave5/authority-consolidation` | `e266def` | active RC1 authority lineage (D7-A successor of cm-r0-fix) |

**Verified lineage facts:**
- `main` ↔ `cm-r0-fix`: bidirectional non-ancestor (true divergence).
- `cm-r0-fix` → `wave5/authority-consolidation`: direct ancestor (successor).
- `main` unique commits (4): all docs-only, all superseded (D5).
- GitHub default branch: **`main`** (verified via `remote show origin`).
- No `.github/workflows`, no submodules, no README hardcoded branch references.
- 12 tags exist; latest already points into the wave5 lineage.

## 3. Options

### Option A — Merge wave5 into main

```
main ── merge commit ── wave5
```

- **Pros:** conservative; preserves main history; GitHub default untouched.
- **Cons:** creates an artificial merge point; implies main was an active
  participant in authority evolution; lineage is not pure.

### Option B — Repoint main to wave5

```
main == wave5/authority-consolidation
```

- **Pros:** most consistent with D7 successor conclusion; clean topology.
- **Cons:** remote branch mutation (rewrite of `main` pointer); requires
  explicit authorization; requires GitHub default-branch handling.

### Option C — Retain main as legacy pointer

```
main (legacy marker)   wave5 (canonical)
```

- **Pros:** lowest risk; no Git topology change.
- **Cons:** two entry points persist; new contributors may misread `main` as
  canonical.

## 4. Decision

**Status:** DECIDED (2026-08-25)

**Option B — Repoint main to wave5 canonical lineage.**

**Scope:** authority decision only. This decision does **not** authorize remote
branch mutation. Execution requires separate D1-E readiness verification and
explicit execution approval.

**Rationale (why not A or C):**
- **Not A (merge)** — a merge commit would fabricate a false historical
  continuity, implying `main` and `wave5` were parallel active lines that
  "merged". In fact `main` is legacy/superseded and `wave5` is its successor
  continuation. A merge would artificially elevate `main`'s historical status.
- **Not C (retain dual entry)** — a permanent `main` legacy pointer creates a
  standing cognitive trap: `git clone` defaults to `main`, but canonical
  authority lives in `wave5`. Julia_core's core goal is that identity /
  continuity / authority must not depend on incidental state; dual entry
  weakens that.

Principle to honor: **authority ≠ branch name; authority = verified lineage.**
Repointing `main` to the wave5 lineage makes the repository's default entry
reflect the verified authority, instead of a superseded pointer.

**Next:** D1-E execution readiness check (OPEN). No branch mutation authorized
by this decision.

## 5. Execution Preflight (only if Option B is chosen)

These are NOT part of this decision; they are the D1-E readiness check that
must run before any repoint:

1. Confirm GitHub default branch (`main`) and how to change it.
2. Confirm no external repo clones/submodules reference `main`.
3. Confirm no CI/CD pipeline (none found locally) targets `main` elsewhere.
4. Confirm branch protection rules on `main`.
5. Confirm tag/release dependencies on `main` (12 tags, latest already on wave5).
6. Record a rollback point (current `main` = `5bc33ba`).

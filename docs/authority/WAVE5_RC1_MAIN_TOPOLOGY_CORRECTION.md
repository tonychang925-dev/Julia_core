# WAVE5 RC1 — Main Topology Correction (GitHub Truth Audit)

**Status:** RECORDED (governance correction)
**Date:** 2026-08-25
**Purpose:** Correct the `main` topology used in D5 / D1 / D1-E, which was
based on a stale local `main` ref. This is a correction of an incorrect audit
input, not a statement that "authority state later changed."

---

## What happened

Previous governance records (D5, D1, D1-E) assumed:

```
local main = 5bc33ba
main ↔ wave5 = true divergence
main-only commits = 4 (docs-only, superseded)
Option B requires remote branch rewrite / force
rollback point = 5bc33ba
```

The read-only audit used `git rev-parse main` (the **local** ref). That local
ref was stale. The GitHub authoritative truth is different.

## GitHub authoritative truth (verified 2026-08-25)

| Ref | SHA |
|---|---|
| `refs/heads/main` (GitHub) | `ffc7c3818de291048c07424ee3223fb583ea24c4` |
| `refs/heads/wave5/authority-consolidation` (GitHub) | `22738dbd0a0dbaf23ce2d69edcde5ef4ee89555e` |
| merge-base | `ffc7c381` (= true main itself) |
| ahead_by / behind_by | 149 / 0 |

**Topology:** `main` (`ffc7c381`) is a **strict ancestor** of
`wave5/authority-consolidation` (`22738dbd`). This is a fast-forward
relationship, not a divergence.

```
main (ffc7c381)
  │
  │ 149 commits (all already absorbed)
  ▼
wave5/authority-consolidation (22738dbd)
```

## Why the local ref was wrong

The local `main` ref (`5bc33ba`) and the true main (`ffc7c381`) diverged from
a common ancestor `b5d2c13`. The local `5bc33ba` was an **obsolete pointer**
that had been superseded; the true main advanced separately to `ffc7c381`,
which is itself already an ancestor of wave5.

`5bc33ba` is reachable only from the stale local `main` ref. `ffc7c381` is
reachable from `cm-r0-fix`, `codex/dia-*`, `sto-*`, and wave5.

## Corrections to prior records

1. **D5 "main-only 4 commits / true divergence"** — superseded. The 4 commits
   (`0d72b05`, `c156fcb`, `a5fd74d`, `5bc33ba`) were classified against the
   *wrong* main ref. The true main (`ffc7c381`) has 0 commits not already in
   wave5.
2. **D1 "Option B requires branch rewrite / force"** — superseded. Option B is
   a **fast-forward ref advancement**, not a forced rewrite.
3. **D1-E rollback point `5bc33ba`** — corrected. The correct rollback point is
   `ffc7c3818de291048c07424ee3223fb583ea24c4`.

## Corrected D1-E status

| Check | Truth result |
|---|---|
| Default branch | `main` |
| Branch protection | disabled (server-side) |
| CI | none |
| Submodule | none |
| hardcoded main dependency | none |
| wave5 contains main | YES — strict descendant (ff) |
| Force required | NO |
| Rollback SHA | `ffc7c3818de291048c07424ee3223fb583ea24c4` |
| Target SHA | `22738dbd0a0dbaf23ce2d69edcde5ef4ee89555e` |
| Orphan tags | independent observation, non-blocking |

**D1-E is now READY** (not merely "ready for review"). Execution remains
NOT AUTHORIZED pending explicit Tony approval.

## Explicit correction statement

> Previous D5 main-only classification was based on an incorrect/stale `main`
> reference (`5bc33ba`). It is superseded by this GitHub truth audit. The true
> `main` is `ffc7c381`, which is already a strict ancestor of wave5.

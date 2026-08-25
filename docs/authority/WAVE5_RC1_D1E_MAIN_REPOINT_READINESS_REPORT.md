# WAVE5 RC1 D1-E — Main Repoint Readiness Report

**Status:** READY FOR EXECUTION REVIEW
**Date:** 2026-08-25
**Purpose:** Verify operational safety for the D1-B decision (repoint `main`
to `wave5/authority-consolidation`). This is a readiness report, **not** an
execution authorization.

**Execution Authorization:** NOT GRANTED.

---

## 1. GitHub default branch

| Item | Value |
|---|---|
| Default branch | `main` |
| Fetch URL | `https://github.com/tonychang925-dev/Julia_core.git` |

Repointing the `main` ref does **not** change the GitHub default branch by
itself; the default-branch designation is a separate GitHub server-side setting.

## 2. CI / automation

| Check | Result |
|---|---|
| `.github/workflows/` on `main` | 0 files |
| `.github/workflows/` on wave5 | 0 files |

No GitHub Actions workflows exist. (Earlier grep hits for `workflow` were
application code under `julia_core/workflow/`, not CI.)

## 3. External dependency

| Check | Result |
|---|---|
| `.gitmodules` | absent (0 submodules) |
| hardcoded `refs/heads/main` / `origin/main` references | 0 occurrences |

## 4. Branch protection

**Status:** UNKNOWN — requires GitHub API/web confirmation.

Branch protection is GitHub server-side state, not visible from a git clone.
The following cannot be verified locally: required reviews, required status
checks, force-push policy, admin enforcement. This item remains OPEN.

## 5. Tags / releases

| Fact | Value |
|---|---|
| Total tags | 12 |
| Tags in wave5 lineage | 5 (incl. latest `wave5-continuity-rc1`) |
| Tags NOT in wave5 lineage | 7 (see §7) |
| Tag dependence on `main` ref | none (tags are independent refs) |

Tags do not depend on the `main` pointer; repointing `main` does not move or
delete any tag.

## 6. Rollback point

```
pre-transition  refs/heads/main = 5bc33ba86a96786991f59a9e9f076e7d48cbd31f
post-transition refs/heads/main = ffdfd758e1b10225241e2f67e03d18befbb8383e
                                 (wave5/authority-consolidation HEAD at report time)
```

A future execution record must capture: operator, timestamp, old SHA, new SHA.

## 7. Orphan Tag Reachability Observation

**Finding:** seven historical tags are not reachable from the canonical
authority lineage (`main` → `cm-r0-fix` → `wave5/authority-consolidation`).

| Tag | Target commit | Reachable from |
|---|---|---|
| `julia-core-v1.1-state-freeze` | `05e54d0` | `codex/bugfix/provider-fallback-chat-copy` only |
| `julia-core-v1.2-alm-freeze` | `1120848` | `codex/bugfix/provider-fallback-chat-copy` only |
| `julia-core-v2.0-llm-native` | `12e1602` | `codex/bugfix/provider-fallback-chat-copy` only |
| `julia-os-v2-architecture-freeze` | `0022b19` | `codex/bugfix/provider-fallback-chat-copy` only |
| `julia-os-v2.2-integration-freeze` | `f97bfd7` | `codex/bugfix/provider-fallback-chat-copy` only |
| `julia-os-v2.4-memory-growth` | `289be7c` | `codex/bugfix/provider-fallback-chat-copy` only |
| `julia-os-v4.0-personal` | `db99097` | `codex/bugfix/provider-fallback-chat-copy` only |

**Impact:** none on `main` repoint execution — tags are independent refs and
will not be moved or deleted by the repoint.

**Risk:** future maintainers may assume these tags belong to the active
authority lineage. They do not; their commits live on a historical bugfix
branch, not on the canonical line.

**Action:** preserve tags unchanged. No retargeting, deletion, or merge of
`provider-fallback-chat-copy` is authorized. This is an observation, not a
mutation request.

---

## Open Items (before execution authorization)

1. **GitHub branch protection** — verify server-side rules via `gh api` or web.
2. **Orphan tag documentation** — recorded above (§7); no action required, but
   must remain visible to future maintainers.
3. **Explicit Tony execution authorization** — none granted by this report.

## Conclusion

`main` → `wave5` repoint is technically READY (no CI, no submodule, no
hardcoded refs, no tag dependence, rollback point recorded). The only
server-side unknown is branch protection. Execution remains NOT AUTHORIZED
pending the open items above and explicit Tony approval.

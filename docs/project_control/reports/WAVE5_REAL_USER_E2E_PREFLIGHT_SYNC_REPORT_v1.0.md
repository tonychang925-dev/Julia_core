# WAVE5_REAL_USER_E2E_PREFLIGHT_SYNC_REPORT_v1.0

Status: PRE-FLIGHT SYNC AUDIT (Rev 1.1 — source-verified)
Date: 2026-08-24
Purpose: verify Local Working Tree = Remote Git Repository = Runtime Server
Deployment before Real User E2E. No E2E until ALL MATCH.

## Source-Verified Evidence (Rev 1.1)

### S2S commit lineage (verified)

```text
98071f3  = "authority: freeze SOP v1.0 as single canonical deployment document"
           (SOP v1.1 TARGET_SHA; deployed on AutoDL ✅)
    ↓ (ancestor of both)
9d44c22  = remote tip (CURRENT_AUTHORITY refresh, VOICE-C1 closed)
    ↓
a8788c8 / e7db6af = local HEAD (AT-11 audit + defer docs)

merge-base(e7db6af, 98071f3) = 98071f3  → server is SOP frozen target
merge-base(98071f3, 9d44c22) = 98071f3  → server is ancestor of remote tip
98071f3 is ancestor of BOTH → server deployment is the FROZEN SOP point.
```

Post-98071f3 commits NOT deployed: `5c85c4f` (RP-2B UUID turn_id),
`9ae63a1` (RP-2 turn_id propagation), `315f359`, `7190d90`, `9d44c22`.

### rmd3g_prod / Brain runtime (verified)

```text
BRAIN START: SHA=bbd90af CRT=/Users/admin/julia_core/... PATH=rmd3g_prod
Brain PID 63955, cwd = rmd3g_prod (detached at bbd90af, approved SHA)
→ running commit = approved SHA bbd90af (RP-1 gate satisfied)
→ julia_core loaded from /Users/admin/julia_core (wave5 91e5a8d)
```

### Electron (verified)

```text
Local HEAD a25f0dc (codex/bugfix/at10-electron-cache-boundary)
Remote: branch NOT present (only electron-c10-c11-projection / wave2-*)
→ E2E Electron artifact NOT traceable on remote → SYNC REQUIRED
```

---

## Repository Matrix

| Repo | Local HEAD | Remote HEAD | Match |
|---|---|---|---|
| julia_core (wave5/authority-consolidation) | `91e5a8d` | `91e5a8d` | ✅ MATCH |
| Julia-AI-Assistant (rmd3g_prod) | `bbd90af` (detached, approved SHA) | `accc977` | ⚠️ Brain runs approved SHA; remote tip differs |
| Julia-Voice-S2S (phase5/rmd-3g) | `e7db6af` | `9d44c22` | ⚠️ local/remote differ; server = `98071f3` |
| Julia_client (electron, codex/bugfix/at10-*) | `a25f0dc` | ❌ branch not on remote | ❌ SYNC REQUIRED |

## Deployment Matrix

| Service | Server Version | Git Commit | Match |
|---|---|---|---|
| Brain (Mac launchd :18089) | cwd `rmd3g_prod` + julia_core local | `bbd90af` + julia_core `91e5a8d` | ✅ runs approved SHA + local wave5 core |
| S2S (AutoDL :8765) | release `98071f3` (SOP v1.1 target) | `98071f3` (in phase5 branch) | ✅ server = git commit 98071f3 |
| Frontend (AutoDL :7860) | release `98071f3` frontend | from S2S release, SHA matched manifest | ✅ (SHA verified) |

## Findings

1. **julia_core**: local == remote == `91e5a8d` (wave5, all AT + E2E plan). ✅
2. **Brain**: runs `bbd90af` (approved SHA, RP-1 gate) with julia_core from local
   `/Users/admin/julia_core` (wave5 `91e5a8d`). Approved-state correct.
   Remote `accc977` is a DIFFERENT branch tip (unapproved) — Brain must NOT run it.
3. **S2S**: three points on the SAME branch `phase5/rmd-3g-observability`:
   local `e7db6af`, remote `9d44c22`, server `98071f3` (deployed per SOP).
   Authority commit must be decided (server deploy point `98071f3` is SOP target).
4. **Electron**: local `a25f0dc` branch `codex/bugfix/at10-electron-cache-boundary`
   NOT on remote → SYNC REQUIRED (push branch).
5. **julia_ai_assistant** (dev repo, not used by Brain runtime): local `47a3e4a`,
   remote `accc977`, 2 unpushed — dev-only.

## Decision

```text
ALL MATCH?  NO

SYNC REQUIRED:
  1. Electron: push codex/bugfix/at10-electron-cache-boundary (a25f0dc)
  2. S2S authority: decide authoritative commit (server 98071f3 vs remote
     9d44c22 vs local e7db6af) and align per "Git → Server" discipline
  3. rmd3g_prod: confirm Brain keeps approved SHA bbd90af (remote tip
     accc977 is NOT authorized for runtime)

Real User E2E execution is BLOCKED until the above is resolved.
```

## Gate

```text
Step 0 Pre-Flight Sync Audit    ← THIS REPORT
Step 1 Sync (Git → Server, if required)
Step 2 Start real environment
Step 3~6 E2E-01..04
Step 7 Wave5 Final Freeze
```

# WAVE5 Repo Identity Audit (RC1)

**Status:** RECORDED — merge 收口前置 (Repository Identity Gate)
**Date:** 2026-08-25
**Repo:** `/Users/admin/julia_core`
**Branch:** `wave5/authority-consolidation`

**Purpose:** 回答四个仓库"哪个目录才是真源"，作为 main consolidation 前的第一道门。不据此直接 merge。

```text
Rule: 不根据历史 manifest 或目录名判断正式仓库。
必须直接核对 remote / branch / HEAD / worktree。
```

---

## 1. Repository Identity Resolution

| Repo | 真源目录 | remote | branch | HEAD | 角色 |
|---|---|---|---|---|---|
| Julia_core | `/Users/admin/julia_core` | `tonychang925-dev/Julia_core` | `wave5/authority-consolidation` | `7681327` | core source（真源） |
| Julia-AI-Assistant | `/Users/admin/julia_ai_assistant` | `tonychang925-dev/Julia-AI-Assistant` | `phase5/rmd-3g-observability` | `47a3e4a` | Brain source（真源） |
| Julia-AI-Assistant (runtime) | `/Users/admin/julia_ai_assistant_rmd3g_prod` | （worktree） | detached | `bbd90af` | **deployment snapshot，非 merge source** |
| Julia_client | `/Users/admin/julia_electron_v2` | `tonychang925-dev/Julia_client` | `fix/voice-ws-lifecycle-001` | `7a9506d` | Electron source（真源） |
| Julia-Voice-S2S | `/Users/admin/Julia-Voice-S2S` | `tonychang925-dev/Julia-Voice-S2S` | `phase5/rmd-3g-observability` | `cbbb10a` | Voice source（真源） |

### Brain worktree 清点（`git worktree list`）

主仓库 `julia_ai_assistant`（`.git` 是目录）。`julia_ai_assistant_rmd3g_prod` 是 worktree（`.git` 是文件，detached `bbd90af`）。

另有 20+ 个 worktree，绝大多数为 `/private/tmp/*` (prunable) 或 `/Users/admin/julia_ai_assistant_*` 实验分支。

```text
结论:
  deployment checkout (rmd3g_prod)  → 只提供 runtime evidence
  不得作为开发分支 merge source
```

---

## 2. Local vs Remote Consistency

| Repo | branch | 本地领先 (ahead) | 本地落后 (behind) | worktree | 结论 |
|---|---|---|---:|---:|---|---|
| Julia_core | wave5/authority-consolidation | 1 | 0 | DIRTY (56) | **不一致**（未 push 1 commit） |
| Brain | phase5/rmd-3g-observability | 2 | 8 | — | **不一致**（分叉） |
| Electron | fix/voice-ws-lifecycle-001 | 0 | 0 | CLEAN | 一致 |
| Voice-S2S | phase5/rmd-3g-observability | 0 | 0 | CLEAN | 一致 |

---

## 3. Key Commit Verification (RC1 目标)

| 目标 commit | 内容 | 状态 |
|---|---|---|
| `935b231` (julia_core) | `test(at21): add AT-21V voice continuity evidence` | ✅ 在 wave5/authority-consolidation，已 push |
| `7a9506d` (electron) | `fix(conversation): Core-first identity, title projection, delete & auto-title (AT-22)` | ✅ = 当前 HEAD，已 push |
| `7e42fa6` (Voice-S2S) | `docs(sop): promote SOP v1.1 as canonical deployment authority` | ✅ 在 phase5/rmd-3g-observability，已 push |
| `bbd90af` (Brain runtime) | `CC-2: propagate voice_trace_id as CRT turn_id` | ⚠️ detached worktree，与 source 分叉 |

旧目标排除：electron `31b4504`（VOICE-WS-LIFECYCLE-001）已被 `7a9506d` 取代。

---

## 4. Risks / Mismatches

### R-1 — Brain runtime 与 source 分叉

```text
bbd90af (runtime)
  ≠ ancestor of
47a3e4a (source HEAD)
```

且 source `47a3e4a` 落后 origin 8 个 commit。

```text
禁止: 因 main 合并压力强行同步 Brain。
```

Brain merge 来源必须单独确认，不能拿 runtime checkout 或 dirty source 直接进 main。

### R-2 — julia_core main 与 wave5 分支分叉

```text
origin/main      = ffc7c38
wave5 工作分支   = wave5/authority-consolidation (7681327)
```

两者是独立历史线，merge 前需确认 rebase 或 merge 策略。

### R-3 — julia_core worktree dirty 56 files

含实验文档、`data/events/*.jsonl`、未 commit 的 authority 文档。merge 前必须分类（见 §5），不能让实验态进入 main。

---

## 5. Merge 收口前置 (A/B/C 分类)

### A 类 — 必须进入 main（Wave5 baseline）

- julia_core: `935b231`（Context OS continuity + AT-21/21V evidence）
- Julia-Voice-S2S: `7e42fa6`（VOICE-WS fix + SOP v1.1 + AT-20B）
- Julia_client: `7a9506d`（Core-first identity + title projection + delete + orphan detection）
- Brain: **待确认**（runtime `bbd90af` 与 source `47a3e4a` 分叉，需先定 merge source）

### B 类 — 不进入 main

```text
tmp/  experiments/  logs/  manual test artifacts  /private/tmp worktrees
```

### C 类 — 单独判断，不混入 RC1

```text
AT-21B Memory Boundary
STO-F2 storage migration
Brain list API root fix
```

---

## Decision

```text
Repository Identity: 已解析（四仓库真源确认）。
Merge 动作: HOLD（未执行）。
```

下一道门：A/B/C 分类 commit → release branch → merge main → tag。

本 audit 只做身份确认，不做任何 merge / reset / push。

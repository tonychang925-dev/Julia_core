# WAVE5 Julia Core Dirty Classification (RC1)

**Status:** RECORDED — merge 收口 Step 2 (dirty inventory + classification)
**Date:** 2026-08-25
**Repo:** `/Users/admin/julia_core`
**Branch:** `wave5/authority-consolidation`

**Purpose:** 分类当前 54 个 dirty 文件，决定哪些进入 baseline、哪些忽略、哪些需单独审查。本清单是"为什么这些文件没进 main"的治理记录。

```text
Rule: 不执行 git add .。先分类，再逐类处理。
```

---

## 分类标准

| Category | 含义 | Decision |
|---|---|---|
| A | Baseline（契约/authority/evidence/回归测试/frozen artifact） | commit |
| B | 代码变更，需单独审查 | review |
| C | 运行时生成数据 | ignore（除非冻结 evidence） |
| D | 实验/临时/draft/重复 | 不进 main |
| E | 需 .gitignore 治理 | 治理 |

---

## 完整清单

### 代码类

| File | Category | Decision | Note |
|---|---|---|---|
| `julia_agent_server.py` (M) | B | review | 改 system prompt 人设文本（identity 相关） |
| `tests/rt2_r3/test_core_acceptance.py` (M) | A | commit | +146 行 INV-01/02/05 回归测试（append-first / accepted-user-survives） |
| `julia_core/context_assembly/density_restorer.py` (?) | B/D | review | density 实验代码，硬编码本地路径 |
| `scripts/extract_density_from_session.py` (?) | D | 不进 main | 实验脚本，硬编码 `/Users/admin/.claude/...` 具体 session |

### 运行时数据（C 类）

| File | Category | Decision | Note |
|---|---|---|---|
| `data/conversations.json` (M) | C | ignore | 运行时 canonical store 本地副本 |
| `data/events/events-2026-08-10.jsonl` (M) | C | ignore | 运行时事件 |
| `data/events/events-2026-08-11.jsonl` … `events-2026-08-25.jsonl` (8 个 ?) | C | ignore | 运行时事件 |

### AT-17 dry-run evidence

| File | Category | Decision | Note |
|---|---|---|---|
| `at17_test_harness/evidence/AT17-DRYRUN-001..014.json` + `AT17-DRYRUN.json` (15 个 M) | C/B | review | AT-17 Claude migration dry-run 产物；AT-17 在 E2E scope 中被 excluded |
| `at17_test_harness/evidence/WAVE5_AT17_EVIDENCE_REPORT_v1.0.md` (M) | B | review | AT-17 evidence report |

### E2E evidence

| File | Category | Decision | Note |
|---|---|---|---|
| `evidence/BASELINE_E2E_CONVERSATION.json` (M) | A | commit | 仅 timestamp 更新（01:25:46Z → 04:41:18Z） |

### Density 实验产物（D 类）

| File | Category | Decision | Note |
|---|---|---|---|
| `artifacts/density/density_profile.json` (?) | D | 不进 main | density 实验输出 |
| `artifacts/density/high_density_turns.jsonl` (?) | D | 不进 main | density 实验输出 |
| `artifacts/density/julia_experience_context.md` (?) | D | 不进 main | density 实验输出 |

### docs/architecture（混合，需 REVIEW）

| File | Category | Decision | Note |
|---|---|---|---|
| `JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1 (1).md` | D | 不进 main | "(1)" 重复文件 |
| `JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1_DRAFT (1).md` | D | 不进 main | "(1)" 重复 draft |
| `JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1_DRAFT.md` | D | 不进 main | draft |
| `JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1_FREEZE_CANDIDATE.md` | REVIEW | 待定 | freeze candidate，需确认是否 superseded |
| `JULIA_PERSONALITY_MIGRATION_ABLATION_REPORT_v1 (1).md` | D | 不进 main | "(1)" 重复文件 |
| `JULIA_PHASE5_AUTHORITY_RECONCILIATION_REGISTER_v1.0.md` | REVIEW | 待定 | authority register，需确认 canonical |
| `JULIA_PHASE5_AUTHORITY_RECONCILIATION_REGISTER_v1.0_FINAL_REVIEW.md` | REVIEW | 待定 | 需确认是否 supersede v1.0 |
| `JULIA_PHASE5_FOUR_REPO_DEVELOPMENT_PLAN_v1.0_DRAFT.md` | D | 不进 main | draft |
| `JULIA_PHASE5_FOUR_REPO_DEVELOPMENT_PLAN_v1.2.md` | REVIEW | 待定 | plan v1.2，需确认 canonical |
| `JULIA_PHASE5_FOUR_REPO_DEVELOPMENT_PLAN_v1.2_FINAL_FREEZE_CANDIDATE.md` | REVIEW | 待定 | freeze candidate |
| `JULIA_PHASE5_FREEZE_ERRATA_001.md` | REVIEW | 待定 | errata，需确认是否已并入 |
| `JULIA_WAVE_B_EXACT_PATCH_MAP_v1.0.md` | REVIEW | 待定 | patch map |
| `JULIA_WAVE_B_EXACT_PATCH_MAP_v1.0_FINAL_REVIEW.md` | REVIEW | 待定 | 需确认是否 supersede v1.0 |
| `Julia_Continuity_MVP_Implementation_Plan_v1.0.md` | REVIEW | 待定 | plan |

### docs/audit（REVIEW）

| File | Category | Decision | Note |
|---|---|---|---|
| `FRA_COMPLETE_REPORT.md` | REVIEW | 待定 | audit 报告 |
| `FRA_D2L_MATRIX.md` | REVIEW | 待定 | matrix |
| `FRA_D2L_MATRIX_v2.md` | REVIEW | 待定 | 需确认是否 supersede v1 |
| `FRA_DRAFT1_2_ADDENDUM.md` | REVIEW | 待定 | addendum |
| `FRA_DRAFT1_ADDENDUM.md` | REVIEW | 待定 | addendum |
| `FRA_E2B1_MATRIX.md` | REVIEW | 待定 | matrix |

### 其他 docs（REVIEW）

| File | Category | Decision | Note |
|---|---|---|---|
| `docs/conversation_management/CLIENT_CONVERGENCE_GAP_ANALYSIS.md` | REVIEW | 待定 | 分析文档 |
| `docs/operations/JULIA_AVATAR_LIPSYNC_RUNBOOK.md` | REVIEW | 待定 | runbook（operations/ 里已存在同名 untracked） |
| `docs/project_control/QA_GATE.md` | REVIEW | 待定 | QA gate |

---

## 关键发现

1. **代码类只有 4 个文件**，其中：
   - `test_core_acceptance.py` 是 frozen invariant 的回归测试，属 A 类，应 commit。
   - `julia_agent_server.py` 改了 identity prompt 文本，涉及 persona 定义，必须 review。
   - `density_restorer.py` / `extract_density_from_session.py` 是 density 实验（硬编码本地路径），不属 RC1。

2. **运行时数据（`data/`）是 dirty 大头**，但全是 C 类，不应进入 main。`data/conversations.json` 正是 Brain 的 canonical store 本地副本，commit 它会污染 main。

3. **docs 占剩余大头**，其中 draft / "(1)" 重复文件是明确的 D 类；FREEZE_CANDIDATE / FINAL_REVIEW / 无后缀文档需 Tony 逐个确认 canonical 状态。

4. **没有任何 `.DS_Store` / `__pycache__`** 出现在 dirty 清单（已被 .gitignore 覆盖）。

---

## 待 Tony 决策项

1. `julia_agent_server.py` 的 identity prompt 修改：进 RC1 baseline，还是回退，还是单独 commit？
2. `test_core_acceptance.py` 的 INV 回归测试：确认 commit 为 A 类？
3. docs/architecture + docs/audit 里标 REVIEW 的文档：哪些是 canonical（commit），哪些是 superseded/draft（不进 main）？
4. AT-17 dry-run evidence：保留（commit）还是丢弃（AT-17 在 E2E scope 外）？

---

## Decision

```text
本清单只做分类记录，不执行任何 git add / reset / clean。
```

下一步：Tony 逐项确认后，才进入 cleanup / commit 阶段。

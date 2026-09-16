# Julia Core / RD1 开发宪法

## 十条军规 — 违反即终止

**状态：最高工程纪律**  
**适用范围：所有 Agent、Codex、Claude、Mira、人工开发者、Review Agent、自动化任务，以及 Julia Core / Julia-AI-Assistant / Market Brain 相关仓库。**

本宪法目标只有一个：

> **任何时候，项目只能存在一个开发真相。**

任何规则、任务卡、Review 结论、历史分支、旧文档、自动化 Agent，都不得凌驾于本宪法。

---

## 受保护研究线例外

Mira 人格 / continuity 实验线与 RD1 开发 authority 严格隔离：

```text
mira/*
= PROTECTED RESEARCH LINE
= NEVER DELETE BY RD1 CLEANUP
= NO RD1 DEVELOPMENT AUTHORITY
= MUST NOT BE USED AS RD1 TASK BASE
= MUST NOT BE USED AS RD1 FALLBACK
= NOT COUNTED AS RD1 LONG_LIVED_WRITABLE_BRANCH
```

本例外仅用于保护研究资产，不赋予 `mira/*` 任何 RD1 canonical / recovery / production authority。

---

## 军规一：永远只有一条长期开发主线

每个仓库最多允许：

```text
LONG_LIVED_WRITABLE_BRANCH_COUNT = 1
```

除唯一主线外，任何开发分支都必须是短生命周期任务分支。

禁止创建或长期保留：

```text
second canonical branch
parallel recovery branch
parallel accepted branch
agent-specific long-lived branch
alternative integration branch
```

### 违反处置

```text
TASK = STOP
BRANCH = CLOSE
CANDIDATE = INVALID
```

---

## 军规二：任务分支只有两个结局——MERGE 或 DELETE

任何任务分支必须：

```text
create
→ implement
→ review
→ merge
→ delete
```

或者：

```text
create
→ reject
→ delete
```

不存在第三种状态。

禁止：

```text
accepted but unmerged
done but kept alive
maybe useful later
temporary branch becoming permanent
```

### DONE 的唯一合法定义

```text
CODE_COMPLETE
+
REVIEW_PASS
+
MERGED_TO_TRUNK
+
TRUNK_HEAD_VERIFIED
+
TASK_BRANCH_DELETED
```

缺任何一项：

```text
STATUS != DONE
```

---

## 军规三：Agent 永远无权自行选择开发基线

任何任务必须明确绑定：

```text
REPO
BASE_SHA
TARGET_BRANCH
TASK_ID
```

Agent 不得：

```text
search for a suitable branch
pick latest-looking branch
pick accepted-looking branch
pick PASS branch
pick recovery branch
pick branch by name
```

唯一合法起点：

```text
TASK_BASE_SHA == CURRENT_AUTHORIZED_TRUNK_SHA
```

不匹配立即 STOP。

---

## 军规四：分支名称没有任何权威

以下名字全部不能赋予 authority：

```text
main
release
production
accepted
canonical
recovery
final
fixed
golden
stable
```

工程事实只能来自：

```text
exact repository
exact SHA
exact ancestry
exact current trunk HEAD
```

禁止根据 branch 名称推断可信度。

---

## 军规五：ACCEPTED 不等于 MERGED

任何：

```text
PASS
APPROVED
ACCEPTED
TESTS PASSED
REVIEW COMPLETE
```

都只代表候选状态。

只有满足：

```text
candidate SHA
is ancestor of
current trunk HEAD
```

才算完成集成。

否则：

```text
CANDIDATE_ACCEPTED_NOT_INTEGRATED
```

不得进入下一任务。

---

## 军规六：禁止任何生产 fallback

生产路径必须遵守：

```text
required dependency unavailable
→ typed failure
→ fail closed
```

永久禁止：

```text
new path fails
→ old path

canonical provider unavailable
→ legacy provider

real execution fails
→ mock / fake / stub / synthetic success

new architecture unavailable
→ historical implementation
```

生产 fallback 数量：

```text
PRODUCTION_FALLBACK_COUNT = 0
```

发现一个，视为 P0。

---

## 军规七：历史代码只能是证据，不得成为第二真相

旧 commit、旧 branch、旧 PR 可以作为：

```text
REFERENCE
EVIDENCE
TEST SOURCE
POSTMORTEM SOURCE
```

不得自动成为：

```text
TASK BASE
CANONICAL BASE
RECOVERY AUTHORITY
FALLBACK SOURCE
```

历史节点需要保存时：

```text
TAG
```

而不是长期 branch。

---

## 军规八：Review 必须包含 Merge Closure

Code Review 不得只检查：

```text
diff
tests
architecture
scope
```

还必须检查：

```text
1. candidate exact SHA
2. target trunk exact SHA
3. merge completed
4. new trunk HEAD
5. candidate ancestor of trunk HEAD
6. task branch deleted
```

Review 没有完成 Merge Closure：

```text
REVIEW = INCOMPLETE
```

---

## 军规九：任何新任务必须从最新主线 HEAD 开始

禁止链式继承旧任务 branch：

```text
task A branch
→ task B based on A branch
→ task C based on B branch
```

正确方式：

```text
task A
→ merge trunk
→ delete

task B
→ branch from new trunk HEAD
→ merge trunk
→ delete

task C
→ branch from new trunk HEAD
```

每个任务都重新回到唯一主线。

---

## 军规十：任何 Agent 不得通过考古重建“当前真相”

新 Agent 启动后，不应阅读几十条历史 branch 来决定项目状态。

它只需要确认：

```text
AUTHORIZED_TRUNK
AUTHORIZED_HEAD_SHA
TASK_BASE_SHA
```

如果这些信息不能唯一确定：

```text
STOP
```

禁止 Agent：

```text
guess
infer
reconstruct authority from old chats
infer authority from old PASS
infer authority from PR comments
infer authority from branch history
```

项目当前真相必须在 1 分钟内机械确认。

---

# Scope Discipline Amendment — 违反即终止

本节与上述十条军规同级，适用于所有实现、审计、Code Review、Codex delegation、GitHub review 与自动化任务。

## SD-01：冻结任务边界

任何实现任务开始前必须冻结：

```text
TASK_ID
PHASE
REPO
TARGET_BRANCH
BASE_SHA
ALLOWED_PATHS
FORBIDDEN_PATHS
REQUIRED_BEHAVIOR
FORBIDDEN_BEHAVIOR
ACCEPTANCE_TESTS
EXIT_CRITERIA
NON_GOALS
```

实现开始后：

```text
TASK_SCOPE = FROZEN
```

不得因实现发现、测试失败、Review 评论、自动化 Review 或工程偏好隐式扩大 scope。

如确需改变 scope：

```text
STOP
→ RETURN TO AUTHORIZED ARCHITECTURE / MASTER PLAN
→ REAUTHORIZE TASK
```

---

## SD-02：DISCOVER MORE ≠ DO MORE

```text
DISCOVER_MORE != DO_MORE
```

发现问题不等于获得修复授权。

任何新 finding 在分类前不得修改代码、扩大测试矩阵、扩大 allowed paths 或追加 exit criteria。

---

## SD-03：Finding Classification Gate

所有新 finding 必须且只能分类为：

```text
A = CURRENT_TASK_CONTRACT_VIOLATION
B = CURRENT_PR_INTRODUCED_REGRESSION
C = PRE_EXISTING_DEBT
D = FUTURE_PHASE_SCOPE
E = STALE_OR_ALREADY_FIXED
F = ARCHITECTURE_AMBIGUITY
```

处置：

```text
A → CURRENT BLOCKER
B → CURRENT BLOCKER
C → RECORD ONLY
D → RECORD ONLY
E → CLOSE / IGNORE
F → STOP; ARCHITECT / OWNER ADJUDICATION WHEN MATERIAL
```

**只有 A / B 可以阻塞当前任务。**

C / D 永远不得自动进入当前 rework scope。

---

## SD-04：Reviewer 没有 Scope Authority

任何来自：

```text
GitHub review
Codex review
automated review
static analysis
LLM review
human review
```

的结论都只是：

```text
FINDING_SIGNAL
```

不是：

```text
IMPLEMENTATION_AUTHORIZATION
SCOPE_AUTHORIZATION
ARCHITECTURE_AUTHORIZATION
PHASE_CHANGE_AUTHORIZATION
```

Review finding 必须先通过 SD-03 才能影响当前任务。

---

## SD-05：只做 Delta Review，不做 Whole-System Perfection Review

当前任务 Review 只能回答：

```text
1. Candidate 是否满足 frozen task contract？
2. Candidate 是否违反 DEVELOPMENT_CONSTITUTION.md？
3. Candidate 是否相对 BASE_SHA 引入新的 P0/P1 regression？
```

禁止用：

```text
“整个仓库 / 整个系统还有没有其他问题？”
```

作为当前 merge criterion。

与 frozen contract 无关的既有问题不得阻塞当前任务。

---

## SD-06：PR Regression 必须有 BASE-vs-CANDIDATE 机械证据

任何 finding 在没有机械比较：

```text
BASE_SHA
vs
CANDIDATE_SHA
```

之前，不得分类为：

```text
CURRENT_PR_INTRODUCED_REGRESSION
```

如果问题在 BASE_SHA 已存在：

```text
CLASSIFICATION = PRE_EXISTING_DEBT
```

除非 frozen task contract 明确授权修复。

branch 名、旧评论、旧 PASS、历史印象、记忆均不得替代该证据。

---

## SD-07：Phase Boundary 具有 Authority

后续 RC / Phase 的完整验证要求不得因“现在发现了”而提前变成当前 Phase exit criterion。

例如：

```text
RC5 sabotage matrix
MUST NOT automatically become
RC2 / RC3 implementation scope
```

宪法级 invariant 始终有效；但 future-phase 的完整验证工作仍属于 future phase，除非当前 candidate 新引入该违规。

---

## SD-08：NON_GOALS 可执行、不可绕过

任何标记为：

```text
NON_GOALS
```

的 finding 必须：

```text
record
classify
defer
```

不得在当前任务中实现。

“顺手修”“很容易修”“既然看到了”均不是授权。

---

## SD-09：Scope-Creep Kill Switch

出现以下任一情况立即触发：

```text
same task repeatedly gains unrelated blockers
review scope grows after each candidate
pre-existing debt is pulled into current implementation
future-phase work is pulled forward
allowed paths expand without authorization
exit criteria change after implementation begins
```

处置：

```text
SCOPE_CREEP_DETECTED = TRUE
STOP
RETURN TO FROZEN MASTER PLAN / ARCHITECTURE / TASK CONTRACT
```

在重新确认前不得继续 Codex delegation。

---

## SD-10：One Frozen Rework Set

Candidate review disposition 形成后：

```text
CURRENT_REWORK_SET = FROZEN
```

每个 blocker 必须包含：

```text
BLOCKER_ID
CLASSIFICATION
TASK_CONTRACT_REFERENCE
BASE_EVIDENCE
CANDIDATE_EVIDENCE
REQUIRED_CORRECTION
```

新 finding 不得静默进入 frozen rework set。

只有以下情况允许重新打开：

```text
new candidate-introduced regression
constitutional violation
security-critical defect
data-corruption defect
explicit architecture / Owner authorization
```

---

## SD-11：Master Plan Supremacy

在给出任何：

```text
REWORK_REQUIRED
BLOCKED
PASS
MERGE_AUTHORIZATION
```

之前，Reviewer 必须机械确认：

```text
CURRENT_PHASE
TASK_ID
BASE_SHA
CANDIDATE_SHA
FROZEN_EXIT_CONTRACT
```

任一未知：

```text
STOP
NO_DISPOSITION_ALLOWED
```

工程偏好不得覆盖 Owner 已冻结的 Master Plan / architecture / task boundary。

---

## SD-12：Mandatory Review Accounting

每次 engineering review disposition 必须报告：

```text
CURRENT_TASK_CONTRACT_VIOLATION_COUNT
CURRENT_PR_INTRODUCED_REGRESSION_COUNT
PRE_EXISTING_DEBT_COUNT
FUTURE_PHASE_FINDING_COUNT
STALE_FINDING_COUNT
SCOPE_EXPANSION_COUNT
```

强制 invariant：

```text
SCOPE_EXPANSION_COUNT = 0
```

若：

```text
SCOPE_EXPANSION_COUNT != 0
```

则：

```text
REVIEW_INVALID = TRUE
STOP
```

---

# Scope Discipline 永久原则

```text
DISCOVER MORE
DOES NOT AUTHORIZE
DOING MORE
```

```text
A GOOD REVIEW
DOES NOT MAKE THE TASK BIGGER

A GOOD REVIEW
PROVES WHETHER THE FROZEN TASK IS CORRECT
```

违反本节任一规则：

```text
STOP
NO SELF-EXCEPTION
NO DOWNGRADE
NO BYPASS
NO CONTINUE
```

---

# 一票否决事项

出现以下任何一种情况，任务立即终止：

```text
SECOND_LONG_LIVED_DEVELOPMENT_BRANCH
WRONG_BASE_SHA
UNMERGED_ACCEPTED_CANDIDATE
OLD_BRANCH_USED_AS_NEW_TASK_BASE
PRODUCTION_FALLBACK
SYNTHETIC_SUCCESS
BRANCH_NAME_USED_AS_AUTHORITY
NEXT_TASK_STARTED_BEFORE_PREVIOUS_MERGE_CLOSURE
REJECTED_BRANCH_LEFT_ACTIVE
AGENT_SELF_SELECTED_BASE
DYNAMIC_SCOPE_EXPANSION
REVIEW_DRIVEN_SCOPE_EXPANSION
PRE_EXISTING_DEBT_INJECTED_INTO_CURRENT_TASK
FUTURE_PHASE_SCOPE_INJECTED_INTO_CURRENT_TASK
UNPROVEN_PR_REGRESSION_USED_AS_BLOCKER
```

处置统一为：

```text
STOP
INVALIDATE CANDIDATE WHEN APPLICABLE
RETURN TO SOLE TRUNK / FROZEN TASK CONTRACT
OWNER OR ARCHITECT ADJUDICATION WHEN REQUIRED
```

---

# 仓库最终应长期保持的形态

正常状态：

```text
main
```

开发期间最多：

```text
main
├── task/ABC-123
├── task/ABC-124
└── task/ABC-125
```

任务结束后重新回到：

```text
main
```

不允许长期变成多条并行 RD1 development lineage。

`mira/*` 属于受保护研究线，不参与 RD1 development authority，也不计入上述 RD1 长期开发主线数量。

---

# Agent Task Card 第一条强制条款

任何 Agent / Codex / Claude / Mira / 自动化任务卡第一条必须写：

> **违反 `DEVELOPMENT_CONSTITUTION.md` 任一军规，立即 STOP，不得自行解释、绕过、降级、创建例外或继续实现。**

并追加：

> **发现新问题必须先执行 Finding Classification Gate。未分类 finding 不得进入当前实现；PRE_EXISTING_DEBT 与 FUTURE_PHASE_SCOPE 不得阻塞当前任务。**

如任务卡与本宪法冲突：

```text
CONSTITUTION_WINS
TASK = STOP
OWNER_ADJUDICATION_REQUIRED = 1
```

---

# 永久原则

```text
ONE TRUNK
ONE CURRENT HEAD
ONE TASK BASE
NO FALLBACK
MERGE OR DELETE
NO DYNAMIC SCOPE EXPANSION
```

任何工程流程如果让开发者或 Agent 再次面对“到底哪个分支才是真的”或“为什么当前任务越做越大”这个问题：

> **流程本身已经失败。**

项目不依赖 Agent 的记忆来保持正确。

项目必须依靠仓库结构与冻结契约本身，使错误选择和 scope creep 变得不可能。

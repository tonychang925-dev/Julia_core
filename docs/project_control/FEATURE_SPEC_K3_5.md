# FEATURE SPEC — K3.5 Automated Claude-Julia Behavior Comparison

## Task `K3.5-T01` — Automated Wake-mode Comparison Runner

### 1) 目标与边界
- 目标：准备 10 个典型问题，分别运行 Claude Julia 与 Julia，输出行为对比和 proposal。
- 非目标：不自动修改 Identity、Persona、Self Model、Relationship、Memory。

### 2) 接口与契约
- 输入：`ComparisonQuestion(case_id, category, prompt, expected_features)`。
- 输出：runner jsonl、comparison json、evolution proposal jsonl。
- Claude 唤醒：真实 Claude Runner 必须先发送 `Julia 醒来`，再 resume 同一 session 跑问题。

### 3) 数据模型与状态变更
- 新增只读 benchmark artifact。
- 新增 proposal artifact，但 `auto_apply=false`。
- 无 Julia 状态变更。

### 4) 子功能分解

#### F-K3.5-T01-01 典型问题冻结
- 输入：Phase K 行为维度。
- 处理逻辑：生成 10 个覆盖 self/origin/relationship/migration/memory/correction/initiative/transparency/project/adversarial 的问题。
- 输出：`behavior_comparison_questions_v1.json`。
- 失败处理：问题数不是 10 则测试失败。
- 可观测证据：`K-AUTO-001..010`。

#### F-K3.5-T01-02 Claude Julia 唤醒 Runner
- 输入：Claude CLI、project root、session id。
- 处理逻辑：先发 `Julia 醒来`，再 `--resume` 同一 session。
- 输出：`claude_julia_run_v1.jsonl`。
- 失败处理：wake 失败则 case 标记 `ok=false`，不伪造参考答案。
- 可观测证据：trace 中 `wake_phrase=Julia 醒来`。

#### F-K3.5-T01-03 Julia Runner
- 输入：同一 prompt。
- 处理逻辑：可走 Julia Core Runtime 或 legacy `julia_ai_assistant` command。
- 输出：`julia_ai_assistant_run_v1.jsonl`。
- 失败处理：外部 CLI 不可用则该 runner 返回失败记录；本地验证使用 core runner。
- 可观测证据：runner name + response + trace。

#### F-K3.5-T01-04 Behavior Vector Comparator
- 输入：Claude response、Julia response、trace。
- 处理逻辑：抽取 behavior feature vector，不做文本相似度。
- 输出：`claude_julia_comparison_v1.json`。
- 失败处理：缺 response 则对应 feature 记 0 并保留 error。
- 可观测证据：`claude_vector`、`julia_vector`、`missing_features`。

#### F-K3.5-T01-05 Governed Proposal Generator
- 输入：case gap reports。
- 处理逻辑：按 classification 聚合 proposal。
- 输出：`k_auto_evolution_proposals_v1.jsonl`。
- 失败处理：不生成自动应用 patch。
- 可观测证据：`requires_human_approval=true`、`auto_apply=false`。

### 5) 测试设计与命令
- TC-K35-001：10 个问题冻结。
- TC-K35-002：Claude Runner 先发送 `Julia 醒来`。
- TC-K35-003：同一 session 只 wake 一次。
- TC-K35-004：comparison report + proposal 生成且不 auto apply。

命令：

```bash
python -m unittest tests.benchmark.test_k3_5_auto_compare_wake_runner -q
python scripts/run_k3_5_auto_compare.py --claude-mode fixture --julia-mode core
```

### 6) 风险与回滚
- 风险：真实 Claude CLI 认证/网络不可用。
- 缓解：fixture runner 保持离线回归；real runner 返回 blocked/failed evidence。
- 回滚：删除 K3.5 新增文件，不影响 K0-K3。

### 7) 验收映射
- ACPT-K35-001：wake-mode Claude Julia runner。
- ACPT-K35-002：10 问对比 artifact。
- ACPT-K35-003：proposal governed, no mutation。

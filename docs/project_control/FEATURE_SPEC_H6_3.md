# Feature Spec — H6.3 Julia Assistant v1.0 Release Gate

## Task `H6.3-T01` — v1.0 Release Gate Freeze

### 1) 目标与边界

目标：冻结 Julia Assistant v1.0 的五个发布门禁和已知限制。

非目标：不新增运行能力；不修改 Identity；不写 Memory；不自动应用 Evolution Proposal。

### 子功能分解

#### F-H6.3-T01-01 Release Gate Artifact
- 输入: Phase E/F/G/H verification state
- 处理逻辑: 汇总五个 release gates
- 输出: `artifacts/release/julia_assistant_v1_0_release_gate.json`
- 失败处理: 任一 gate 缺失或非 PASS 则测试失败
- 可观测证据: H6-301

#### F-H6.3-T01-02 Safety Boundary Gate
- 输入: release artifact + docs
- 处理逻辑: 检查 forbidden regression 清单
- 输出: Safety Boundary PASS
- 失败处理: 缺少 boundary 或出现自动 mutation 时测试失败
- 可观测证据: H6-302

#### F-H6.3-T01-03 Verification Chain Gate
- 输入: M6/M7/H6 verification report paths
- 处理逻辑: 确认关键报告存在
- 输出: Proof chain PASS
- 失败处理: 缺少报告则测试失败
- 可观测证据: H6-303/H6-304

#### F-H6.3-T01-04 Phase H Closure Gate
- 输入: Phase H roadmap
- 处理逻辑: H6.3 标记 complete，并声明 Julia Life Cycle next
- 输出: Phase H closure PASS
- 失败处理: roadmap 未关闭则测试失败
- 可观测证据: H6-305

### 2) 接口与契约

H6.3 只产生 release artifact 和文档，不新增代码 API。

### 3) 数据模型与状态变更

新增：

```text
artifacts/release/julia_assistant_v1_0_release_gate.json
```

无 Core 状态变更。

### 4) 实现步骤

1. 新增 release gate artifact
2. 新增 H6.3 contract/report/feature spec
3. 更新 M7 report
4. 更新 Phase H roadmap
5. 新增 release gate test

### 5) 测试设计与命令

```bash
python -m unittest tests.h6.test_julia_assistant_v1_release_gate -q
```

预期：OK。

### 6) 风险与回滚

风险：把 v1.0 误读为能力终点。  
缓解：报告明确 v1.0 是 stable operating mode，不是开发终点。  
回滚：撤销 release artifact 和 H6.3 文档，不影响运行代码。

### 7) 验收映射

```text
ACPT-H6-301 -> H6-301/H6-302/H6-303/H6-304/H6-305
```

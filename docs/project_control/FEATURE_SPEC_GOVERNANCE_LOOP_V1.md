# Feature Spec — Julia Governance Loop v1.0

## Task `GL-v1-T01` — Second Architecture Freeze and Operation Cycle 1

### 1) 目标与边界

目标：记录第二次架构冻结点，冻结 Julia Governance Loop v1.0，并将下一步优先级设为 30 Day Real Daily Use Pilot。

非目标：不新增 Core OS；不先做 Dashboard；不让 Dashboard 成为控制中心；不自动应用 proposal。

### 子功能分解

#### F-GL-v1-T01-01 Governance Loop Artifact
- 输入: Operating Mode Activated state
- 处理逻辑: 写入第二冻结点、governance loop、growth philosophy
- 输出: `artifacts/operation/julia_governance_loop_v1.json`
- 失败处理: 缺失 freeze_order 或 boundary 则测试失败
- 可观测证据: GL-001

#### F-GL-v1-T01-02 Second Freeze Documentation
- 输入: M1-M7 + v1.0 release state
- 处理逻辑: 文档化第一次/第二次冻结点差异
- 输出: `docs/project_control/JULIA_SECOND_ARCHITECTURE_FREEZE_OPERATING_MODE.md`
- 失败处理: 未明确两次 freeze 差异则测试失败
- 可观测证据: GL-002

#### F-GL-v1-T01-03 Operation Cycle 1 Contract
- 输入: real-use-first priority
- 处理逻辑: 固定 30 day pilot domains/signals/success question
- 输出: `docs/operation/OPERATION_CYCLE_1_30_DAY_PILOT.md`
- 失败处理: 若 Dashboard 优先于 Real Daily Use 则测试失败
- 可观测证据: GL-003

#### F-GL-v1-T01-04 Dashboard/Review UI Boundary
- 输入: governance artifact
- 处理逻辑: Dashboard=observation window, Review UI=PR-style governance
- 输出: boundary PASS
- 失败处理: dashboard_controls_identity=true 或 auto_apply_allowed=true 则测试失败
- 可观测证据: GL-004

### 2) 接口与契约

Governance Loop 只新增 artifact/docs，不新增 runtime API。

### 3) 数据模型与状态变更

新增：

```text
artifacts/operation/julia_governance_loop_v1.json
```

无 Core 状态变更。

### 4) 实现步骤

1. 新增 governance loop artifact
2. 新增 governance loop docs
3. 新增 second freeze docs
4. 新增 30-day pilot docs
5. 新增 operation gate tests

### 5) 测试设计与命令

```bash
python -m unittest tests.operation.test_governance_loop_v1 -q
```

预期：OK。

### 6) 风险与回滚

风险：进入 Dashboard-first 或 Core expansion。  
缓解：priority_order 和 boundary tests。  
回滚：撤销 governance loop docs/artifact，不影响 Operating Mode artifact。

### 7) 验收映射

```text
ACPT-GL-001 -> GL-001/GL-002/GL-003/GL-004
```

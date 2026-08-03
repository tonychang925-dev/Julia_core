# Feature Spec — Julia Operating Mode v1

## Task `OM-v1-T01` — Operating Mode Activation Contract

### 1) 目标与边界

目标：将 Julia Assistant v1.0 的状态从 building mode 切换为 operating mode，并冻结 Operation Cycle。

非目标：不新增 Core OS；不写 Memory；不更新 Identity；不自动应用 proposal。

### 子功能分解

#### F-OM-v1-T01-01 Operating Mode Artifact
- 输入: H6.3 release gate
- 处理逻辑: 记录 from building_mode to operating_mode
- 输出: `artifacts/operation/julia_operating_mode_v1.json`
- 失败处理: 缺少 operation_cycle 或 core_freeze 则测试失败
- 可观测证据: OM-001

#### F-OM-v1-T01-02 Operation Cycle Documentation
- 输入: user-approved lifecycle model
- 处理逻辑: 写入 Observe/Understand/Propose/Approve/Evolve/Verify
- 输出: `docs/operation/JULIA_OPERATION_CYCLE_v1.md`
- 失败处理: cycle 缺失则测试失败
- 可观测证据: OM-002

#### F-OM-v1-T01-03 Core Freeze Boundary
- 输入: operating mode artifact + contract
- 处理逻辑: 确认 operating mode 不新增 Core OS，不自动 mutation
- 输出: boundary PASS
- 失败处理: boundary false 缺失则测试失败
- 可观测证据: OM-003

#### F-OM-v1-T01-04 Milestone Chain Closure
- 输入: milestone chain docs
- 处理逻辑: 确认 M1-M7 + Julia Assistant v1.0 完整
- 输出: chain PASS
- 失败处理: milestone 缺失则测试失败
- 可观测证据: OM-004

### 2) 接口与契约

Operating Mode 只新增 artifact/docs，不新增 runtime API。

### 3) 数据模型与状态变更

新增：

```text
artifacts/operation/julia_operating_mode_v1.json
```

无 Core 状态变更。

### 4) 实现步骤

1. 新增 operating mode artifact
2. 新增 operation cycle docs
3. 新增 operating mode contract/report
4. 新增 operation tests

### 5) 测试设计与命令

```bash
python -m unittest tests.operation.test_operating_mode_activation -q
```

预期：OK。

### 6) 风险与回滚

风险：Operating Mode 被误当作 Phase I 功能扩张。  
缓解：contract 明确不是新开发阶段。  
回滚：撤销 operation artifact/docs，不影响 Julia Assistant v1.0 release gate。

### 7) 验收映射

```text
ACPT-OM-001 -> OM-001/OM-002/OM-003/OM-004
```

# Feature Spec — H6.1 Tony-Julia Daily Usage Pilot

## Task `H6.1-T01` — Daily Relationship Snapshot

### 1) 目标与边界

目标：把 H6.0 observation records 汇总为每日 Tony-Julia 协作快照，用于后续 Reality Feedback Analysis。

非目标：不生成 MemoryRef；不更新 Persona；不更新 Identity；不替代人工验收。

### 子功能分解

#### F-H6.1-T01-01 Continuity Success Summary
- 输入: PilotObservationRecord[]
- 处理逻辑: 统计 checkpoint_used 比例与 repeated explanation rate
- 输出: continuity_success, repeated_explanation_rate
- 失败处理: 空记录输出 0.0
- 可观测证据: H6-101/H6-103

#### F-H6.1-T01-02 Memory/Evidence Utility Summary
- 输入: memory.useful 与 evidence retrieval fields
- 处理逻辑: 统计 useful Memory ratio 和 successful Evidence ratio
- 输出: memory_usefulness, evidence_success_rate
- 失败处理: 未观察到触发时输出 0.0
- 可观测证据: H6-101

#### F-H6.1-T01-03 Human Friction Summary
- 输入: correction_count, repetition_required, wrong_assumption_count
- 处理逻辑: 计算 human_friction_score 与 manual_corrections
- 输出: human_friction_score, manual_corrections
- 失败处理: 缺失 human 字段时默认 0
- 可观测证据: H6-101

#### F-H6.1-T01-04 Snapshot Boundary Guard
- 输入: DailyRelationshipSnapshot
- 处理逻辑: boundary 显式声明不写 Memory/Identity/Persona
- 输出: snapshot boundary PASS
- 失败处理: 命中自动演化 token 时测试失败
- 可观测证据: H6-102/H6-104

### 2) 接口与契约

```text
daily_relationship_snapshot(records, date, topics) -> DailyRelationshipSnapshot
DailyRelationshipSnapshot.to_dict() -> dict
```

### 3) 数据模型与状态变更

新增数据模型：DailyRelationshipSnapshot。无 Core 状态变更。

### 4) 实现步骤

1. 在 `julia_core/observer/pilot_observer.py` 增加 DailyRelationshipSnapshot
2. 增加 `daily_relationship_snapshot()` 汇总函数
3. 导出到 `julia_core/observer/__init__.py`
4. 增加 H6.1 文档与回归测试

### 5) 测试设计与命令

```bash
python -m unittest tests.h6.test_daily_usage_pilot -q
```

预期：OK。

### 6) 风险与回滚

风险：Daily Snapshot 被误认为 Memory。  
缓解：boundary 字段 + forbidden token gate。  
回滚：停止调用 `daily_relationship_snapshot()`，H6.0 原始 observation JSONL 不受影响。

### 7) 验收映射

```text
ACPT-H6-101 -> H6-101/H6-102/H6-103/H6-104/H6-105
```

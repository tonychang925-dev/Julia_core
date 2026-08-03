# Feature Spec — H6.0 Pilot Instrumentation

## Task `H6.0-T01` — Lightweight Pilot Observation Layer

### 1) 目标与边界

目标：记录 Julia Human Interface 真实使用中的连续性、记忆、证据、声音和人类摩擦指标。

非目标：不新增 OS；不自动写 Memory；不修改 Identity；不改变 Provider 输出。

### 子功能分解

#### F-H6.0-T01-01 Runtime Trace Mapping
- 输入: Runtime trace + session_id + duration_ms + input_mode + voice_output
- 处理逻辑: 映射为 PilotObservationRecord
- 输出: interaction/continuity/memory/evidence/voice/human/boundary 字段
- 失败处理: trace 缺字段时使用保守默认值
- 可观测证据: H6-001

#### F-H6.0-T01-02 JSONL Append Observer
- 输入: PilotObservationRecord
- 处理逻辑: append-only 写入 JSONL
- 输出: runtime_observations/pilot_observations.jsonl
- 失败处理: 写入目录不存在时自动创建；不影响 Core 状态
- 可观测证据: H6-002

#### F-H6.0-T01-03 StreamingController Binding
- 输入: ClientChatEnvelope + RuntimeStreamEvent list
- 处理逻辑: completed turn 后生成 observation record
- 输出: observer.observe(record)
- 失败处理: 无 trace 时跳过记录
- 可观测证据: H6-003

#### F-H6.0-T01-04 Observer Isolation Gate
- 输入: observer source code
- 处理逻辑: 检查 forbidden Core authority token
- 输出: isolation PASS/FAIL
- 失败处理: 命中后测试失败
- 可观测证据: H6-004

### 2) 接口与契约

```text
record_from_runtime_trace(...) -> PilotObservationRecord
JsonlPilotObserver.observe(record) -> PilotObservationRecord
JsonlPilotObserver.summarize() -> PilotObservationSummary
```

### 3) 数据模型与状态变更

仅新增 append-only JSONL 观察文件。无 Core 状态变更。

### 4) 实现步骤

1. 新增 `julia_core/observer/pilot_observer.py`
2. 新增 `julia_core/observer/__init__.py`
3. 在 `StreamingController` completed turn 后调用 observer
4. 新增 H6.0 合同、报告、测试

### 5) 测试设计与命令

```bash
python -m unittest tests.h6.test_pilot_instrumentation -q
```

预期：OK。

### 6) 风险与回滚

风险：观察层被误用为 Memory/Identity 更新入口。  
缓解：boundary 字段 + source isolation test。  
回滚：`StreamingController(observer=NullPilotObserver())`。

### 7) 验收映射

```text
ACPT-H6-001 -> H6-001/H6-002/H6-003/H6-004/H6-005
```

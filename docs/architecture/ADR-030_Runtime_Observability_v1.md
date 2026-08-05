# ADR-030: Runtime Observability Architecture v1.0

**Status:** PROPOSED
**Date:** 2026-08-05
**Source:** E3 Completion → E4 Planning
**Depends on:** ADR-029 (Action Execution Model)

---

## 1. Motivation

E3 的 EventTrace (`julia_core/runtime/event_trace.py`) 目前在 Gateway 里以 ad-hoc 方式使用：每个 voice.final 手动创建 trace、手动 record、手动 finish。这对于调试单个语音交互够用，但无法提供 Runtime 级别的可观测性。

当 Julia OS 从实验系统进入操作系统雏形，需要：

- **Metrics:** 量化的性能指标（延迟、吞吐、错误率）
- **Trace:** 结构化的请求链路追踪
- **State:** 当前 Runtime 状态快照（presence, active actions, sessions）
- **Health:** 存活检测和降级状态

## 2. Architecture

```
                    Runtime Observer
                          │
          ┌───────────────┼───────────────┐
          │               │               │
      Metrics           Trace           Health
          │               │               │
   ┌──────┼──────┐   Action Trace    ┌────┼────┐
   │      │      │   (per-action)    │    │    │
latency memory  tts                   alive ready degraded
```

### 2.1 Metrics

统一指标命名空间：`runtime.<domain>.<metric>`

| Metric | Definition | Target |
|--------|------------|--------|
| `runtime.latency.total_ms` | voice.final → assistant.completed | <2000ms |
| `runtime.latency.llm_first_token_ms` | chat() start → first token | <800ms |
| `runtime.latency.tts_first_audio_ms` | speech.request → first audio chunk | <500ms |
| `runtime.latency.interrupt_ms` | voice.started → speech.cancelled | **<300ms** |
| `runtime.memory.load_ms` | Wake State reconstruction time | <500ms |
| `runtime.tool.execution_ms` | Tool execution wall time | per-tool budget |
| `runtime.voice.asr_latency_ms` | audio segment → transcript | <1000ms |

**Interrupt Latency** 是 Companion 产品的关键指标：

```
T0: client.voice.started (user begins speaking)
T1: speech.cancelled (Julia stops speaking)
interrupt_latency = T1 - T0

目标: <300ms
```

这 300ms 包含：
- WebSocket 消息到达 Gateway
- `_active_speech_task.cancel()` 执行
- `CancelledError` 在协程中传播
- `speech.cancelled` 事件序列化并发送

### 2.2 Trace

将现有 `EventTrace` 升级为结构化 Action Trace：

```python
ActionTrace {
    action_id: str,
    action_type: str,
    session_id: str,
    spans: [
        {name: "llm.generate", start_ms: 0, end_ms: 850},
        {name: "tts.stream", start_ms: 850, end_ms: 1200},
        {name: "speech.chunk[0]", start_ms: 1200, end_ms: 1250},
    ],
    state: COMPLETED | CANCELLED,
    cancel_reason: str | None,
    total_ms: int,
}
```

### 2.3 Health

```python
RuntimeHealth {
    status: "alive" | "degraded" | "unavailable",
    active_sessions: int,
    active_actions: int,
    provider_status: {
        llm: "connected" | "degraded" | "down",
        asr: "connected" | "degraded" | "down",
        tts: "connected" | "degraded" | "down",
    },
    uptime_seconds: int,
    last_error: str | None,
}
```

Exposed via `GET /health` (already exists, needs upgrade).

## 3. Runtime Observer Pattern

```python
class RuntimeObserver:
    """Singleton. Receives events from all Runtime components."""

    def observe_action(self, action: Action) -> ActionTrace:
        """Begin tracing an action. Returns trace handle."""

    def record_metric(self, name: str, value: float, tags: dict = None):
        """Record a point metric."""

    def health_snapshot(self) -> RuntimeHealth:
        """Return current health state."""

    def list_traces(self, n: int = 20) -> list[ActionTrace]:
        """Recent action traces for debugging."""
```

Every Runtime component (Voice, Memory, Capability, Gateway) calls `RuntimeObserver.observe_action()` when starting an action. The observer creates a trace, records spans, and exposes metrics.

## 4. Integration Points

| Component | What It Observes |
|-----------|-----------------|
| Gateway | voice.final → speech.completed/cancelled lifecycle |
| JuliaSession | chat() latency, turn count, topic drift |
| Memory Runtime | load latency, narrative compile time |
| Capability Runtime | tool execution time, evidence chain length |
| Voice Runtime | ASR latency, TTS first audio, interrupt latency |

## 5. E4 Implementation Roadmap

### E4.1.1: ActionTrace (1 day)
Upgrade `EventTrace` → structured `ActionTrace` with spans. Backward compatible — existing `EventTrace.record()` calls still work.

### E4.1.2: RuntimeObserver singleton (1 day)
Create `julia_core/runtime/observer.py`. Integrate into Gateway, JuliaSession, Voice Runtime.

### E4.1.3: /health upgrade (0.5 day)
Add `provider_status`, `active_actions`, `uptime_seconds` to GET /health.

### E4.1.4: Interrupt Latency metric (0.5 day)
Instrument voice.started → speech.cancelled path. Log every interrupt with latency.

## 6. Contract

1. **Every Action produces a Trace.** No silent execution.
2. **Metrics are point-in-time.** Not averages over windows (for now).
3. **Health is pull-based.** Gateway exposes `/health`, no push to external monitor (for now).
4. **Observer is non-blocking.** Must not add >1ms overhead to any action path.

# ADR-029: Runtime Action Execution Model v1.0

**Status:** FROZEN
**Date:** 2026-08-05
**Source:** E3.5 Interrupt Runtime Fix
**Depends on:** ADR-022 (Gateway), ADR-023 (Event Protocol), ADR-025 (Voice Architecture)

---

## 1. Motivation

E3.5 的 Interrupt 修复暴露了一个架构层面的问题：

Julia Runtime 之前没有统一的执行抽象。voice.final 处理器把 `js.chat()` 扔进 `run_in_executor`，然后用 flag 检查来"取消"。这个模式不可靠——flag 检查是 data plane，取消是 control plane，两者不在同一层。

更根本的问题是：Julia 的行为一直被视为 **Request → Response**，而不是 **Runtime Action**。

## 2. Core Principle

**Julia Runtime 不执行 Response。它执行 Interruptible, Observable, Recordable Actions。**

```
普通 Chatbot:
  input → LLM → output  （原子操作，不可中断）

Julia OS:
  Input Event → Runtime Action{execute, observe, cancel, record} → Output Events
```

## 3. Action Model

### 3.1 Definition

```python
Action {
    id: str,           # unique identifier (e.g., "sp-1691234567000")
    type: str,         # action type (speech.generate, memory.retrieve, tool.execute)
    state: ActionState, # CREATED | STARTED | RUNNING | COMPLETED | CANCELLING | CANCELLED
    execute(),         # begin execution
    observe(),         # emit progress events
    cancel(),          # interrupt execution
    trace(),           # record to Runtime Trace
}
```

### 3.2 Lifecycle

```
CREATED
  │
  ▼
STARTED ──→ action.started event
  │
  ▼
RUNNING ──→ action.progress events
  │
  ├──────────────→ COMPLETED ──→ action.completed event
  │
  └──────────────→ CANCELLING
                      │
                      ▼
                   CANCELLED ──→ action.cancelled event
```

### 3.3 Four Mandatory Capabilities

Every Action MUST implement:

| Capability | Method | Description |
|------------|--------|-------------|
| **Execute** | `execute()` | Begin the action. E.g., speech.generate, memory.retrieve, tool.execute |
| **Observe** | `observe()` | Emit `action.started`, `action.progress`, `action.completed` events |
| **Cancel** | `cancel()` | Interrupt the action. MUST use control-plane cancellation (task.cancel()), NOT data-plane flag check |
| **Record** | `trace()` | Write to Runtime Trace with timing, state transitions, and cancellation reason |

## 4. Cancellation Convergence

### 4.1 Principle

所有取消路径 MUST 收敛到同一个清理序列：

```
Any cancellation reason:
  - user interrupt (voice.started during speaking)
  - network disconnect (WebSocket close)
  - timeout (action exceeds max duration)
  - preemption (new action supersedes old)
      │
      ▼
  Action.cancel()
      │
      ▼
  CancelledError raised in action coroutine
      │
      ▼
  except CancelledError:
      action.cancelled event
      presence → IDLE
      trace.record("cancelled", {reason})
```

### 4.2 Why task.cancel(), Not Flag Check

```python
# WRONG — Data-plane flag check
for chunk in chunks:
    if pm.interrupted:  # race condition: LLM may finish before flag is checked
        return

# CORRECT — Control-plane cancellation
_active_speech_task.cancel()  # CancelledError raised at next await
```

The control plane (`task.cancel()`) operates at the asyncio scheduler level. It interrupts the coroutine at the next `await` point regardless of what the coroutine is doing. The data plane (flag check) requires the coroutine to voluntarily yield between iterations — which fast LLM responses may not do.

### 4.3 Implementation Reference

See `julia_core/runtime/gateway_server.py`:
- Line 146: `_active_speech_task: asyncio.Task | None = None` — Action reference
- Line 161-162: `_active_speech_task.cancel()` — Control-plane cancellation on voice.started
- Line 195-196: `if pm.interrupted: raise asyncio.CancelledError()` — Belt-and-suspenders flag check
- Line 221-229: `except asyncio.CancelledError` — Unified cancellation handler

## 5. Action Types

| Action Type | Runtime Component | Cancellation Behavior |
|-------------|-------------------|-----------------------|
| `speech.generate` | Voice Runtime | Cancel TTS stream, send speech.cancelled |
| `memory.retrieve` | Memory Runtime | N/A (read-only, sub-50ms) |
| `tool.execute` | Capability Runtime | Cancel tool execution, revert side effects if possible |
| `market.analyze` | Capability Runtime | Cancel analysis, discard partial results |
| `narrative.compile` | Memory Runtime | Cancel compilation, preserve partial diary |

## 6. Contract

### 6.1 Action MUST

1. Accept `cancel()` at any point after STARTED
2. Emit `action.cancelled` within one event loop tick of cancellation
3. Record cancellation reason in trace
4. Clean up resources (TTS stream, file handles, executor threads)
5. Transition presence to IDLE after cancellation

### 6.2 Action MUST NOT

1. Use flag-based "check if interrupted" as the sole cancellation mechanism
2. Continue emitting progress events after cancellation
3. Leave presence in SPEAKING/GENERATING after cancellation
4. Swallow CancelledError silently

## 7. Relationship to Other ADRs

- **ADR-022 (Gateway):** Actions execute within Gateway's event loop. Gateway holds action references.
- **ADR-023 (Event Protocol):** Action lifecycle events follow the `action.*` namespace.
- **ADR-025 (Voice Architecture):** Speech is the first Action type. All future capabilities follow the same model.
- **ADR-030 (Observability):** Action traces feed the Runtime Telemetry system.
- **ADR-031 (Embodied Boundary):** Actions execute on the Capability Plane, observed by the Cognitive Plane.

## 8. Validation

E3.5 Interrupt Race Test (`tests/e3/test_interrupt_race.py`) validates:
- Interrupt during LLM execution (executor thread)
- Interrupt during speech chunk streaming
- Race condition: fast LLM + immediate interrupt
- Assertion: no speech.chunk(old) after voice.final(new)

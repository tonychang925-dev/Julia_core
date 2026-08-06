# ADR-027: Julia Runtime Execution Model v1.0

**Date:** 2026-08-06
**Status:** PROPOSED → FROZEN
**Supersedes:** None (new execution model — follows ADR-021 through ADR-026)

---

## Summary

ADR-021~026 answered: what is Julia? How does she connect to the world? How does she own capabilities?

ADR-027 answers: how does Julia run continuously? How does she experience an event? How does she remember an experience? How does she manage a task?

The Runtime is no longer defined as `request → response`. It is defined as:

```
event → runtime state transition → capability action → context update → reasoning → experience
```

---

## 1. Core Principle

**Runtime is Event Driven, Async First, Workflow Governed.**

Three forbidden patterns:

1. ❌ Synchronous logic as Runtime Authority — `chat_async()` is the canonical entry point; `chat()` is a compatibility wrapper only
2. ❌ Events as mere logs — events are **Runtime Facts** with provenance, causation, and evidence chains
3. ❌ Workflow lifecycle owned by business Pipelines — the `WorkflowRuntime` owns lifecycle; Pipelines are step definitions

---

## 2. Async First Model

### 2.1 Canonical Entry Point

```
chat_async()  ← Authority (canonical)
     │
     ▼
_runtime_execute()  ← Shared implementation
     │
     ▼
chat()  ← Compatibility wrapper (no independent logic)
```

### 2.2 Rule

`chat()` MUST NOT contain independent logic. It delegates to `chat_async()` via `asyncio.run()` or the reverse. One implementation, two entry signatures.

### 2.3 Runtime Async Boundary

All Runtime components MUST support `async`:

- `CapabilityProvider.execute()` — async
- `ContextProvider.provide()` — async
- `Workflow.step()` — async
- `Memory.write()` — async
- `Experience.record()` — async
- `EventPublisher.emit()` — async
- `Voice.render()` — async
- `MCPAdapter.call()` — async

### 2.4 Why

Julia will concurrently handle: Voice input, Market observation, Calendar events, Robot commands, Mobile interaction. A synchronous model cannot multiplex these without thread pools.

---

## 3. Event Sourcing Model

### 3.1 Event = Runtime Fact

An event is NOT a notification or log line. It is a durable runtime fact with:

```python
@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    event_id: str              # UUID
    timestamp: str             # ISO 8601
    source: str                # "runtime" | "capability" | "workflow" | "conversation"
    event_type: str            # "capability.requested" | "workflow.step.completed" | ...
    payload: dict              # Domain-specific body
    correlation_id: str        # Groups events in the same logical chain
    causation_id: str | None   # Points to the event that caused this one
    evidence_refs: tuple[str, ...]  # Linked evidence (prediction_id, capability_id, etc.)
```

### 3.2 Event Timeline

One Market Brief execution produces:

```
evt_001  user.request.created         {"text": "今天市场怎么样？"}
   │
evt_002  intent.detected               {"intent": "market_overview"}
   │
evt_003  capability.requested           {"capability": "market.snapshot.read"}
   │
evt_004  market.snapshot.received       {"schema_version": "1.1"}
   │
evt_005  context.created                {"block_types": ["market_overview", ...]}
   │
evt_006  reasoning.completed            {"response_len": 450}
   │
evt_007  artifact.created               {"brief_id": "brief_..."}
   │
evt_008  experience.recorded            {"prediction_ids": ["pred_..."]}
```

This timeline enables answering: "Julia, why did you think 机器人 would diffuse yesterday?" — not by re-reasoning, but by reading the Evidence Timeline.

### 3.3 Event Persistence

Events are written to the Event Store at emit time. The Event Store is append-only. Events are never mutated. Correlation chains are never broken.

---

## 4. Event Categories (Frozen)

### 4.1 `runtime.*` — Julia Internal State

```
runtime.started
runtime.state.changed
runtime.completed
runtime.failed
```

### 4.2 `conversation.*` — User Interaction

```
conversation.created
conversation.message.received
conversation.turn.completed
```

### 4.3 `capability.*` — Capability Invocation

```
capability.requested
capability.started
capability.completed
capability.failed
```

### 4.4 `workflow.*` — Task Lifecycle

```
workflow.created
workflow.step.started
workflow.step.completed
workflow.completed
workflow.failed
```

### 4.5 `experience.*` — Long-Term Accumulation

```
experience.created
experience.updated
```

---

## 5. Workflow Lifecycle

### 5.1 Workflow Definition

```python
@dataclass
class WorkflowDefinition:
    name: str                          # "market.brief"
    steps: tuple[str, ...]             # ("intent.resolve", "capability.request",
                                       #  "context.build", "reasoning.execute",
                                       #  "artifact.create", "experience.record")
    trigger_events: tuple[str, ...]    # ("conversation.message.received",)
    timeout_seconds: int = 60
```

### 5.2 Workflow Instance

```python
@dataclass
class WorkflowInstance:
    instance_id: str                   # "wf_market_001"
    workflow_name: str                 # "market.brief"
    state: WorkflowState               # CREATED | RUNNING | WAITING | COMPLETED | FAILED
    current_step: str                  # "context.build"
    created_at: str                    # ISO 8601
    events: list[str]                  # event_ids in this workflow
    result: dict | None                # final output
```

### 5.3 State Machine

```
CREATED → RUNNING → WAITING_CAPABILITY → WAITING_REASONING → COMPLETED
                                                               ↓
                                                           FAILED (any state)
```

### 5.4 WorkflowRuntime

```python
class WorkflowRuntime:
    """Owns workflow lifecycle. Pipelines are step definitions, not owners."""

    def __init__(self, registry, event_store, capability_manager, context_os):
        ...

    async def execute(self, definition: WorkflowDefinition, input: dict) -> WorkflowInstance:
        """Execute a workflow. Emits events at each step transition.
        Creates an audit trail. Returns the completed (or failed) instance.
        """
        ...
```

Current `MarketBriefPipeline` becomes a step set registered in `WorkflowRuntime`. The pipeline no longer owns its lifecycle — `WorkflowRuntime` does.

---

## 6. Event Timeline vs. Experience

Event Store answers: **What happened?**
> "On August 6, Julia read market data, detected AI Agent at L4, generated a brief."

Experience Store answers: **What should be learned?**
> "After 5 consecutive diffusion days for 机器人, L4 signal accuracy improves. Weight historical patterns higher for sustained themes."

```
Event Timeline → Experience Extraction → Experience Memory
```

Events are immutable facts. Experience is governed, extracted patterns. Not every event becomes an experience.

---

## 7. Directory Structure (Post-ADR-027)

```
julia_core/
  runtime/
    execution.py      # _runtime_execute() shared implementation (NEW)
    lifecycle.py      # Runtime lifecycle hooks (NEW)

  events/
    __init__.py
    models.py         # RuntimeEvent, EventCategory (NEW)
    store.py          # EventStore — append-only persistence (NEW)
    timeline.py       # Timeline reconstruction (NEW)

  workflow/
    __init__.py
    models.py         # WorkflowDefinition, WorkflowInstance, WorkflowState (NEW)
    runtime.py        # WorkflowRuntime — owns lifecycle (NEW)
    executor.py       # StepExecutor — runs individual steps (NEW)
    registry.py       # WorkflowRegistry — named workflow definitions (NEW)
```

---

## 8. Relationship to Existing ADRs

| ADR | Concern | ADR-027 Impact |
|-----|---------|---------------|
| ADR-021 | Conversation Ownership | Conversation events replace topic-detection strings |
| ADR-022 | Runtime Gateway | Gateway emits events, not just routes messages |
| ADR-023 | Event Protocol | Upgraded from notification → fact source |
| ADR-024 | Capability Architecture | Capability invocations produce timeline events |
| ADR-026 | MCP Adapter | MCP calls emit capability.* events through the adapter |

---

## 9. Acceptance Criteria

### AC-1: Async Authority
`chat()` → `chat_async()` → shared implementation. No dual logic. Verified by code structure check.

### AC-2: Event Persistence
One `chat_async()` call produces a complete event timeline in the Event Store: user.request.created → ... → experience.recorded. Minimum 5 events per market query.

### AC-3: Workflow Execution
`MarketBriefPipeline` refactored to `WorkflowRuntime.execute("market.brief")`. Pipeline no longer instantiates its own lifecycle or evidence ledger.

### AC-4: Recovery
Runtime restart can resume a `RUNNING` or `WAITING` workflow from the Event Store.

### AC-5: Evidence Reconstruction
Given a `workflow_id`, the full causal chain can be reconstructed from event timeline: what capability was called, what provider responded, what context was built, what reasoning was produced.

---

## 10. What ADR-027 Does NOT Change

- ❌ Does NOT change CapabilityManager or Provider protocol
- ❌ Does NOT change Context OS or ContextBlock contract
- ❌ Does NOT change ADR-026 MCP Adapter boundary
- ❌ Does NOT add new capabilities or providers
- ❌ Does NOT require deleting existing code

ADR-027 adds the time dimension (events, workflows, lifecycle) to the existing spatial architecture (capabilities, providers, context). It is additive, not destructive.

---

## 11. Phase 1 Readiness

ADR-027 is the bridge between Phase 0 (Runtime Foundation) and Phase 1 (Autonomous Awareness).

```
Phase 0:   Julia can answer "what is the market doing?"
ADR-027:   Julia can experience time, remember chains of events, manage tasks
Phase 1:   Julia can observe continuously: "something changed — Tony should know"
```

Without ADR-027, Phase 1 capabilities (market.alert.query, market.event.subscribe, autonomous observation) would attach as disconnected features. With ADR-027, they become natural extensions of Julia's event-driven awareness.

---

*This ADR freezes the Runtime Execution Model. No M3 code until this design is reviewed and frozen.*

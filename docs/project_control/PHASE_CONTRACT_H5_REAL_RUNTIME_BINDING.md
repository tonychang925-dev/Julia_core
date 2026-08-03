# Phase Contract — H5 Real Runtime Binding

Status: COMPLETE / APPROVED at Runtime Binding MVP scope
Phase Code: H5
Parent Phase: H — Julia Human Interface Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: H4 Streaming Conversation — COMPLETE / APPROVED

## 1. Objective

Bind the streaming client path to a runtime-owned JuliaAssistantRuntime instead of a local HTTP streaming stub.

## 2. Frozen Runtime Stream Objects

```text
RuntimeStreamRequest
RuntimeStreamEvent
RuntimeBindingTrace
JuliaAssistantRuntime.stream()
StreamingController
```

## 3. Runtime Chain

```text
/api/chat/stream
  ↓
StreamingController
  ↓
JuliaAssistantRuntime.stream()
  ↓
Continuity Hook
  ↓
Active Recall Policy
  ↓
Evidence OS when needed
  ↓
Evidence-aware Context Reconstruction
  ↓
Provider-like stream boundary
  ↓
RuntimeStreamEvent
  ↓
SSE
```

## 4. Stream Event Contract

Runtime request:

```json
{
  "session_id": "session-001",
  "message": "Julia，我们继续昨天的讨论",
  "input_mode": "text",
  "stream": true
}
```

Runtime events:

```text
runtime_ready
context_ready
text_delta
done
error
```

Text delta:

```json
{
  "type": "text_delta",
  "content": "我记得..."
}
```

## 5. Boundary

StreamingController owns transport adaptation only.

Forbidden:

```text
StreamingController → Memory writes
StreamingController → Persona mutation
StreamingController → Context construction logic
StreamingController → Provider selection authority
server.py → Core OS orchestration
```

## 6. Acceptance

- `/api/chat/stream` uses `StreamingController`.
- `StreamingController` calls `JuliaAssistantRuntime.stream()`.
- Runtime trace reports continuity/memory/context/evidence/provider status.
- Streaming path emits `text_delta` chunks.
- No Memory dump, Evidence dump, Identity mutation, or provider file read.

## 7. Decision

```text
H5 Real Runtime Binding — COMPLETE / APPROVED at Runtime Binding MVP scope
Next: Provider stream integration + real workspace pilot
```

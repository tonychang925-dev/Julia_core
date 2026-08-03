# Provider Stream Contract v1

Status: FROZEN
Generated At: 2026-08-02
Owner: Julia Runtime / Provider Boundary

## 1. Purpose

Define the streaming provider boundary for JuliaAssistantRuntime.

Provider streaming is generation only. It does not own Persona, Memory, Continuity, Context, Evidence, Alignment, Client, or Voice identity.

## 2. Request

```json
{
  "messages": [],
  "stream": true,
  "model": "deepseek-chat",
  "provider_name": "deepseek",
  "context_blocks": [],
  "trace": {}
}
```

## 3. Event

```json
{
  "event": "delta",
  "delta": {
    "text": "我记得..."
  }
}
```

Allowed event types:

```text
start
delta
done
error
```

## 4. Trace

```json
{
  "provider": {
    "name": "deepseek",
    "model": "deepseek-chat",
    "stream": true,
    "latency_ms": 120,
    "status": "PASS"
  }
}
```

## 5. Boundary

Forbidden:

```text
Provider → Memory write
Provider → Identity mutation
Provider → direct workspace file read
Provider → raw Memory dump request
Provider → raw Evidence dump request
Provider → Context OS bypass
```

## 6. Runtime Integration

```text
JuliaAssistantRuntime.stream()
  ↓
ProviderStreamAdapter.stream()
  ↓
ProviderStreamEvent(delta)
  ↓
RuntimeStreamEvent(text_delta)
  ↓
SSE
```

## 7. Decision

```text
Provider Stream Contract v1 — FROZEN
Proceed to H5.5 Real Provider Stream Integration MVP
```

# Phase Contract — H5.5 Real Provider Stream Integration

Status: COMPLETE / APPROVED at Provider Stream Contract MVP scope
Phase Code: H5.5
Parent Phase: H — Julia Human Expression & Interface Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: H5 Real Runtime Binding — COMPLETE / APPROVED

## 1. Objective

Replace the runtime-local deterministic text generator boundary with a formal `ProviderStreamAdapter.stream()` contract.

H5.5 does not require a live paid/network provider in CI. It freezes the adapter contract so DeepSeek/OpenAI/Claude/Qwen stream providers can be plugged in without changing Runtime, Client, Memory, Context, Evidence, or Identity authority.

## 2. Provider Stream Objects

```text
ProviderStreamRequest
ProviderStreamEvent
ProviderStreamDelta
ProviderTrace
ProviderStreamAdapter
DeterministicProviderStreamAdapter
```

## 3. Runtime Path

```text
/api/chat/stream
  ↓
StreamingController
  ↓
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

## 4. Provider Trace

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

## 5. Real Behavior Gates

| ID | Name | Expected |
|---|---|---|
| P-001 | Real Streaming Recall | continuity/memory/context/provider trace stays PASS while streaming |
| P-002 | Evidence Retrieval Stream | active recall can retrieve EvidenceRef and route through Context OS before streaming |
| P-003 | Provider Switch | same session can switch provider ids without identity/context/memory dump fallback |

## 6. Boundary

Forbidden:

```text
ProviderStreamAdapter → Memory write
ProviderStreamAdapter → Identity mutation
ProviderStreamAdapter → direct workspace read
ProviderStreamAdapter → raw Memory dump
ProviderStreamAdapter → raw Evidence dump
ProviderStreamAdapter → Context OS bypass
```

## 7. Decision

```text
H5.5 Real Provider Stream Integration — COMPLETE / APPROVED at Provider Stream Contract MVP scope
Proceed to H6 Julia Personal Assistant Pilot
```

# Phase Contract — H4 Streaming Conversation / Real Runtime Binding Prep

Status: COMPLETE / APPROVED at Streaming MVP scope
Phase Code: H4
Parent Phase: H — Julia Human Interface Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: H1-H3 Text/Voice Client MVP — COMPLETE / APPROVED

## 1. Objective

Upgrade the first Julia client from full-response chat to streaming conversation while preserving the Human Interface boundary.

## 2. Frozen Stream Objects

```text
ConversationStreamEvent
StreamingTrace
ResponseChunk
```

## 3. Stream Contract

```text
User Input
  ↓
Conversation Event
  ↓
Runtime Trace
  ↓
Token Stream
  ↓
Client Incremental Render
  ↓
Optional Browser Voice Output
```

Trace target:

```json
{
  "interaction": {"mode": "text", "stream": true},
  "runtime": {"session_id": "xxx"},
  "continuity": {"status": "PENDING_RUNTIME_BINDING"},
  "context": {"blocks_used": []},
  "provider": {"streaming": true}
}
```

## 4. Transport Decision

Use SSE over HTTP first.

Implemented:

```text
POST /api/chat/stream
media_type: text/event-stream
```

Browser client uses `fetch()` streaming instead of `EventSource` so POST body can carry text/session/mode.

## 5. Boundary

`server.py` remains HTTP adapter / client delivery / session transport.

Forbidden:

```text
server.py owns Persona authority
server.py writes Memory
server.py mutates Continuity
server.py bypasses Context OS
Voice owns Identity
```

## 6. Acceptance

- Streaming endpoint exists.
- Stream emits trace, chunk, done events.
- Frontend renders response incrementally.
- Non-stream `/api/chat` fallback remains.
- Trace preserves client/voice/memory/provider boundaries.

## 7. Decision

```text
H4 Streaming Conversation — COMPLETE / APPROVED at Streaming MVP scope
Next: Real Runtime Binding / provider stream integration
```

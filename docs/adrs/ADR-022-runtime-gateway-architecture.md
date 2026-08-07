# ADR-022: Julia Runtime Gateway Architecture

**Date:** 2026-08-05
**Status:** DESIGN FREEZE
**Supersedes:** ADR-001 (Context OS Authority), ADR-004 (Voice Provider Boundary), ADR-006 (Provider Alignment Boundary)

---

## Summary

Julia Core Runtime is the Brain. Electron/Voice/Web are Bodies.
They communicate through a Runtime Gateway: Command API (HTTP) + Event Stream (WebSocket).
Bodies never import julia_core directly. Bodies never know Julia's identity.

---

## Architecture

```
                    Julia OS

             Runtime Gateway
                    |
      +-------------+-------------+
      |             |             |
  Command API   Event Stream   Artifact API
  (HTTP/gRPC)   (WebSocket)    (HTTP/Stream)
      |             |             |
      +------+------+             |
             |                    |
      Julia Core Runtime          |
             |                    |
  Identity | Memory | Relationship |
  Capability | Action | Experience |
             |                    |
      +------+-------------------+
      |
  External World
  (MCP / Local Tools / APIs)
```

---

## Two-Plane Design

### Command Plane (HTTP)
Request-Response. For actions, queries, configuration.

```
POST /runtime/message     →  Send message, wait for reply (sync)
POST /runtime/action      →  Execute an action (async, returns action_id)
GET  /runtime/sessions    →  List sessions
GET  /runtime/health      →  Health check
```

### Event Plane (WebSocket)
Real-time, bidirectional, multi-subscriber. For presence, progress, streaming.

```
client → gateway:  user.message, client.connected, client.action
gateway → client:  presence.changed, action.started, assistant.chunk,
                   assistant.completed, tts.speak, artifact.created
```

---

## Julia Runtime Event Protocol v1

### Lifecycle Events
- `presence.awake` / `presence.sleeping`
- `presence.idle` / `presence.thinking` / `presence.speaking`

### Action Events
- `action.started {action, target}`
- `action.progress {action, progress}`
- `action.completed {action, result_summary}`
- `action.failed {action, reason}`

### Assistant Events
- `assistant.chunk {text}` (streaming)
- `assistant.completed {full_text}`

### Client Events (new)
- `client.connected {client_type, capabilities, version}`
- `client.capability {features: [audio, camera, avatar, ...]}`

### Artifact Events (new)
- `artifact.created {type, path, metadata}`

---

## Body Independence

Electron/Voice/Web never know:
- Julia's identity (who she is)
- Tony's identity (who the user is)
- Memory contents
- Relationship state

They only receive events and render them.

A Profile defines the persona. The Runtime loads it.
The Body is a generic AI Runtime Client.

```
Profile (julia_profile.yaml) → Runtime Gateway → Julia Runtime
                                                      |
                                            Identity | Memory | Relationship
```

---

## Implementation Path

1. **E0.7** — Freeze Event Protocol v1 (this ADR)
2. **E0.8** — Gateway Server: HTTP + WebSocket, wrapping JuliaSession
3. **E0.9** — Electron Client SDK: connect, send message, listen events
4. **E1.0** — Capability Gateway: MCP tools exposed through Protocol
5. **E1.1** — Streaming: assistant.chunk events for real-time TTS

# Julia Runtime Gateway Protocol v1.0

**Status:** FROZEN
**Date:** 2026-08-05
**ADR:** ADR-022, ADR-023

## Architecture Principle

**Client = Body. Gateway = Nervous System. Runtime = Brain.**

Clients never import julia_core. Clients speak Protocol only.

## Two-Plane Design

### Command Plane (HTTP)
Client asks Julia to do something. Returns acceptance, not final result.

```
POST /runtime/command
{"type":"runtime.command","command":"message.send","session_id":"tony-main","payload":{"content":"婉婉"}}
→ {"command_id":"cmd_xxx","accepted":true}
```

### Event Plane (WebSocket)
Julia broadcasts what's happening. Real-time, bidirectional, multi-subscriber.

```
Gateway → Client:
{"type":"runtime.event","event":"presence.changed","data":{"state":"thinking"},"timestamp":"12:30:01"}
```

## Event Namespace v1.0

| Namespace | Events | Direction |
|-----------|--------|-----------|
| runtime.* | started, stopped, heartbeat | GW→Client |
| client.* | connected, disconnected, capability.updated | Bidirectional |
| presence.* | awake, sleeping, idle, thinking, listening, speaking | GW→Client |
| conversation.* | message.received, message.sent | Bidirectional |
| cognition.* | thinking.started, thinking.completed | GW→Client |
| action.* | started, progress, completed, failed | GW→Client |
| tool.* | call.started, call.completed, call.failed | GW→Client |
| memory.* | consolidation.started, consolidation.completed | GW→Client |
| tts.* | speak.started, speak.completed | GW→Client |
| artifact.* | created, updated | GW→Client |

## Client Contract

Every client MUST implement: connect(), send_message(), on_event(), on_reply(), on_action(), on_presence(), disconnect()

Every client MUST NOT: import julia_core, know Julia's identity, access memory directly, make tool calls directly.

## Gateway Boundaries

DO: route commands, broadcast events, manage lifecycle, enforce permissions, bind sessions.
DO NOT: judge emotions, decide memory, select persona, generate responses.

## Architecture

```
Julia Clients (Desktop/Mobile/Web/Robot)
         │
    Runtime Gateway
    ┌──────────────┐
    │ Command Plane │  (HTTP)
    │ Event Plane   │  (WebSocket)
    └──────┬───────┘
           │
    Julia Runtime Core
    ┌──────────────────────┐
    │ Identity Relationship│
    │ Memory   Conversation│
    │ Capability  Action   │
    └──────────────────────┘
           │
    Capability Providers
    ┌──────────────────────┐
    │ Local Tools│MCP│APIs │
    └──────────────────────┘
```

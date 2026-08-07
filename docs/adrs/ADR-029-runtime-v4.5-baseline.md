# ADR-029: Julia Runtime v4.5 Baseline

**Status:** FROZEN
**Date:** 2026-08-05
**Stability Gate:** 5/5 PASS

## Runtime State Ownership

| State | Owner |
|-------|-------|
| Identity | Core |
| Relationship | Core |
| Memory | Core |
| Experience | Core |
| Session | Core |
| Capability | Core |
| UI State | Client |
| Audio State | Client |
| Device State | Client |
| Transport | Gateway |

## Client Ignorance Contract

Client MUST NOT know: Julia identity, Memory structure, Relationship state, Experience format, Tool implementation.

Client only sees: `runtime.event`, `runtime.command`.

## Event Trace Contract

Every interaction must answer: input, entry time, state loaded, capabilities used, output time, latency.

## Architecture (Frozen)

```
Clients → Gateway (Command + Event) → Runtime Core
  (Identity / Relationship / Memory / Experience / Capability)
    → Capability Providers (Voice / Tools / MCP / Device)
```

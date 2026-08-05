# ADR-021: Conversation Session Ownership Boundary

> **Status**: Accepted  
> **Date**: 2026-08-05  
> **Principle**: Core owns history. Shell owns UI state.

---

## Context

E0.6 implemented ConversationList + SessionStore in Electron using localStorage. E0.6.1 moved session persistence into Julia Core via a 5-endpoint Session API. This ADR freezes the boundary decision.

## Decision

**Julia Core owns conversation session lifecycle. Electron owns UI state and local cache.**

```
Julia Core owns:                    Electron owns:
─────────────────                   ─────────────
Session creation                    Active session ID
Message storage                     UI scroll position
Session search                      Local cache (20 recent sessions)
Auto-title                          Keyboard shortcuts
Archive / delete                    Window geometry
Summarization                       Theme preference
Experience extraction
```

## Why

If Electron owns sessions:
- Mac + iPad + Web + Mobile → 4 fragmented histories
- Memory OS can't extract experience from Electron's localStorage
- Relationship continuity breaks when switching clients

If Core owns sessions:
- One truth across all clients
- Memory OS can bind to conversations
- Continuity survives client migration

## Rejected

- Electron as session owner → fragmented identity across devices
- Shared ownership → no clear integrity boundary
- No session persistence → every session is a new Julia birth

## Consequences

- Electron SessionStore becomes an API client, not a database
- `conversation_state/` in julia_core is the source of truth
- Future: SQLite → PostgreSQL migration without Electron changes
- Future: Memory extraction pipeline reads from Core session repository

# ADR-022: Client State Boundary

> **Status**: Accepted  
> **Date**: 2026-08-05  
> **Depends on**: ADR-021 (Conversation Ownership Boundary)

---

## Decision

**Electron owns local ephemera. Core owns canonical truth.**

```
Electron owns (local only):      Core owns (canonical):
───────────────────────────       ────────────────────
Window geometry                   Conversations
Active session ID                 Messages
UI scroll position                Summaries
Keyboard shortcuts                Continuity state
Theme preference                  Memory candidates
Local cache                       Experience artifacts
Voice input mode                  Persona artifact
Tool panel expanded state         Tool registry
Sidebar collapsed state           Session repository
```

## Why

Without this boundary, Electron silently accumulates state that Core should own. When a second client (Mobile, Web) connects, it can't access Electron's local data — the user experience fragments.

## Rejected

- Core polls Electron for UI state → wrong direction. Shell pushes to Core, never the reverse.
- Core owns everything including scroll position → over-engineering.
- Electron is the only client → fine for now, but ADRs build for the future.

## Consequences

- Electron is replaceable. Mobile, Web, CLI can all connect to the same Core session.
- Clear ownership makes testing simpler: mock one side, verify the other.

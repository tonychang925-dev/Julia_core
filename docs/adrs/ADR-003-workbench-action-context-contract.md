# ADR-003 — Workbench Action Carries Intent Pointer, Not Context Payload

## Status

Proposed / F4.3-pre

## Context

F4.2.1 introduced `JuliaCopilot` as an Analyst Workbench UI entry. The next natural step is contextual workbench actions such as `Ask Julia Why`, `Ask Julia Risk`, or `Compare` from a theme/stock/event card.

If these actions send full theme cards, stock payloads, event lists, and evidence bundles, the frontend becomes a context builder and bypasses Julia Context OS.

## Decision

Workbench actions must send intent pointers and object references, not large context payloads.

Allowed shape:

```json
{
  "type": "analyst_action",
  "payload": {
    "action": "ask_why",
    "object_type": "theme",
    "object_id": "9043089",
    "trade_date": "2026-07-31",
    "session_id": "session-1"
  }
}
```

Forbidden shape:

```json
{
  "type": "analyst_action",
  "payload": {
    "theme": { "full": "payload" },
    "events": [],
    "stocks": [],
    "evidence": []
  }
}
```

Julia Context OS receives the pointer, plans needed evidence, requests domain context from the Financial Domain Provider, then builds provider-facing context.

## Alternatives Considered

1. Send full UI object payload to reduce backend calls.
   - Rejected because UI becomes a context authority and stale payloads can bypass provenance.
2. Let financial workbench pre-build analysis prompts.
   - Rejected because prompt assembly belongs to Julia Context OS.
3. Send object pointer and action intent only.
   - Accepted.

## Consequences

Positive:

- Keeps UI thin.
- Keeps context authority centralized.
- Supports replay and provenance.
- Avoids accidental leakage of large or stale domain payloads.

Tradeoffs:

- Backend provider binding must resolve object references.
- Workbench actions need stable object IDs.

## Trigger

Any F4.4+ workbench contextual action implementation must comply with this ADR.

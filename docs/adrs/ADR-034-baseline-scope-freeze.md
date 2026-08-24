# ADR-034: Baseline Scope Freeze — Conversation Persistence as E2E Acceptance Foundation

**Date:** 2026-08-24
**Status:** PROPOSED
**Supersedes/Relates:** ADR-033 (application persistence host binding), Wave5 Acceptance / Freeze scope

---

## Summary

Freeze the current Wave5 baseline E2E acceptance scope to the **conversation
storage / continuity loop** ONLY. Persona migration and cognitive-runtime
convergence (Context Ownership, Generation Runtime, Provider decoupling,
CoreEvent) are explicitly **OUT of scope** for this baseline and deferred to a
separate Phase 2 — Cognitive Continuity Migration.

## Decision

### In Scope (baseline E2E acceptance)

```text
Client → ConversationRuntime → Session Store → Reload/Resume
        → same conversation continuity
```

- Conversation creation / list / resume
- Turn persistence (canonical transcript)
- Transcript authority (ConversationRuntime sole writer)
- Restart recovery
- Multi-turn context recovery
- Canonical conversation non-loss
- Client reconnect reconciliation

### Out of Scope (deferred to Phase 2)

```text
Persona Migration          (persona prompt → persona artifact → cognition envelope)
Cognition Envelope production cutover
Context Ownership convergence (ContextBlock → Context Composer → Generation Runtime)
Provider decoupling
CoreEvent convergence
```

## Why

Deep code audit (B0 → Context Ownership → P7 Generation Runtime) proved these
are NOT file moves; they are a full cognitive-architecture migration involving:

```text
identity artifact
continuity state
context authority
cognition envelope
migration gate
```

Bundling them into baseline would expand the acceptance target from
"conversation continuity + storage loop" into "full cognitive architecture
migration" — different verification goals, longer timeline, higher risk.

## Ordering Principle

```text
Conversation History
    ↓
Continuity Foundation
    ↓
Identity Migration
    ↓
Cognitive Runtime
```

A stable conversation lineage is the carrier for identity continuity.
`Memory copy != Identity continuity`. Without reliable conversation
persistence, later persona/causal/memory evolution has no stable substrate.

## Existing Assets (not discarded)

```text
✅ Persona Artifact
✅ MemoryRef + Governance
✅ Context OS
✅ Cognition Envelope design
✅ Ownership Gate
```

This freeze is a scope decision, not a restart. Save the timeline first;
migrate persona state later.

## Phase 2 (separate program)

```text
Phase 2 — Cognitive Continuity Migration

Conversation History
  + Memory
  + Identity Artifact
  + Context State
        ↓
Julia Core Cognitive Runtime
```

## Impact

- Baseline E2E: conversation storage + resume loop is the acceptance gate.
- P7 generation-runtime work: recorded (scope contract drafted) but NOT
  implemented in this baseline.
- Persona migration: frozen until conversation lineage baseline is accepted.

## Status

```text
PROPOSED — pending Tony approval.
```

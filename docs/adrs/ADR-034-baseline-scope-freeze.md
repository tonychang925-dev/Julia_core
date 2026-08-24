# ADR-034: Baseline Scope Freeze — Conversation Persistence as E2E Acceptance Foundation

**Date:** 2026-08-24
**Status:** APPROVED (with Phase Boundary Protection, Rev 1.1)
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

## Phase Boundary Protection (Rev 1.1)

```text
Baseline implementation MUST NOT introduce temporary cognitive authority
shortcuts that become permanent migration debt.
```

Baseline MAY implement transcript / session / persistence.

Baseline MUST NOT add:

```text
prompt assembly
identity injection
memory authority
provider decision logic
```

Rationale: history shows convenience shortcuts (e.g. assistant_runtime →
provider) tend to become permanent architecture. The baseline acceptance
must not mint new cognitive authority paths.

## Execution Plan (Approved)

```text
Selected:  Layer 1 — ConversationRuntime E2E (storage loop)
Deferred:  Layer 2 — Brain API E2E (RP-1 / Brain deployment coupling)
Reason:    preserve baseline scope isolation; avoid RP-1/provenance/Brain
           deployment coupling. Brain DOWN is governance protection, NOT a
           baseline failure — baseline must not pollute production governance.
```

### Acceptance matrix (7 cases)

```text
1. Conversation create       unique conversation_id, durable
2. Multi-turn write          canonical transcript ordering
3. Restart recovery          conversation recoverable after restart
4. Resume                    continue writing to same conversation
5. Canonical non-loss        no transcript loss
6. Client reconnect          no duplicate / no loss
7. Crash consistency         transcript state consistent after abnormal exit
```

### Out of Scope Guard

Baseline E2E MUST NOT verify:

```text
❌ Persona            (e.g. "Julia identity restored" — Phase 2)
❌ Cognitive Context  (e.g. "model received same personality context" — Phase 2)
❌ Provider equivalence (e.g. "model swap behaves identically" — Phase 2)
```

### Execution waves

```text
Wave 1 Storage Core:   create → append turn → persist
Wave 2 Recovery:       shutdown → restart → load conversation
Wave 3 Continuity:     turn N → restart → turn N+1 → same lineage
Wave 4 Reconnect:      disconnect → reconnect → resume → no dup/loss
```

## Status

```text
APPROVED — 2026-08-24 (Scope: BASELINE E2E ONLY.
Reason: preserve continuity foundation before cognitive migration.
Risk: controlled. Next: Cognitive Continuity Migration.)
```

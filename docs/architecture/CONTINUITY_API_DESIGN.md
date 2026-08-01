# Continuity API Design

Status: DRAFT-FROZEN
Phase: E1.3.6 — Continuity API & Checkpoint Contract Freeze
Scope: Julia Core OS
Generated At: 2026-08-01

## 1. Purpose

This document freezes the first public contract model for Continuity OS.

Continuity OS is not a brain, reasoning engine, persona generator, or memory database.

It is the Agent OS authority for continuity policy:

```text
what must persist, why it matters, and how it is restored
```

## 2. Core Objects

Continuity OS introduces five core contract objects:

```text
ContinuityRequest
ContinuityDecision
ContinuityCheckpoint
RecoveryPlan
ContinuityTrace
```

## 3. ContinuityRequest

A ContinuityRequest asks Continuity OS to classify state or refs for preservation.

```json
{
  "request_id": "continuity-request-001",
  "agent_id": "julia",
  "event_type": "conversation|memory_candidate|session_summary|provider_switch|compact_risk",
  "source": "session|memory_os|runtime|context_os|persona_engine",
  "candidate_refs": [
    "memory://event/julia-core-origin"
  ],
  "signals": {
    "identity_related": true,
    "relationship_related": true,
    "project_related": true,
    "recurring": true,
    "provider_independent": true
  },
  "current_context": {
    "session_id": "session-123",
    "provider": "deepseek",
    "mode": "private_voice_continuity"
  }
}
```

## 4. ContinuityDecision

A ContinuityDecision records what Continuity OS decided and why.

```json
{
  "decision_id": "continuity-decision-001",
  "request_id": "continuity-request-001",
  "level": "L0_EPHEMERAL|L1_SESSION|L2_MEMORY|L3_IDENTITY",
  "preserve": true,
  "checkpoint_required": true,
  "reason": "identity_forming_event",
  "protected_refs": [
    "memory://event/julia-core-origin"
  ],
  "ttl_policy": "discard|summarize|retain_ref|protect",
  "notes": "This event explains why Julia Core exists."
}
```

## 5. ContinuityCheckpoint

A ContinuityCheckpoint is a compact provider-independent state artifact.

It is not a prompt and not a conversation dump.

```json
{
  "checkpoint_version": "1.0",
  "checkpoint_id": "continuity://checkpoint/julia/2026-08-01T00:00:00Z",
  "agent_id": "julia",
  "created_at": "2026-08-01T00:00:00Z",
  "identity_refs": [
    "persona://julia/v1"
  ],
  "protected_memory_refs": [
    "memory://event/julia-core-origin"
  ],
  "relationship_refs": [
    "memory://relationship/tony-julia-core-origin"
  ],
  "active_project_refs": [
    "project://julia-core"
  ],
  "continuity_levels": {
    "L3_IDENTITY": ["persona://julia/v1"],
    "L2_MEMORY": ["memory://event/julia-core-origin"],
    "L1_SESSION": [],
    "L0_EPHEMERAL": []
  },
  "integrity": {
    "schema": "continuity_checkpoint_v1",
    "provider_independent": true
  }
}
```

## 6. RecoveryPlan

A RecoveryPlan describes how Runtime should restore continuity after compact, restart, provider switch, or session loss.

```json
{
  "recovery_plan_id": "recovery://julia/compact-survival-001",
  "agent_id": "julia",
  "recovery_reason": "compact|session_loss|provider_switch|runtime_restart|platform_migration",
  "checkpoint_id": "continuity://checkpoint/julia/latest",
  "required_steps": [
    "load_identity_refs",
    "retrieve_protected_memory_refs",
    "rebuild_context_blocks",
    "resolve_alignment_profile",
    "emit_continuity_trace"
  ],
  "required_context_blocks": [
    "identity_anchor",
    "relationship_anchor",
    "protected_memory_refs",
    "active_project_context"
  ],
  "provider_constraints": {
    "provider_independent": true,
    "current_provider": "deepseek"
  }
}
```

## 7. ContinuityTrace

ContinuityTrace extends ExecutionTrace.

```json
{
  "continuity": {
    "status": "NOT_REQUIRED|CLASSIFIED|CHECKPOINTED|RESTORED|FAILED",
    "checkpoint_id": "continuity://checkpoint/julia/latest",
    "continuity_levels_used": ["L2_MEMORY", "L3_IDENTITY"],
    "identity_preserved": true,
    "memory_recovered": true,
    "context_rebuilt": true,
    "provider_changed": false,
    "protected_refs": [
      "memory://event/julia-core-origin"
    ],
    "recovery_reason": "compact_survival_test"
  }
}
```

## 8. ContinuityPolicy

ContinuityPolicy is the decision table used by Continuity OS.

Minimum policy dimensions:

| Signal | Effect |
|---|---|
| identity_related | raises candidate to L3 if stable |
| relationship_related | at least L2; L3 if identity-forming |
| project_origin_related | L2 or L3 depending on role in agent mission |
| recurring | increases preserve likelihood |
| provider_independent | eligible for checkpoint |
| temporary_task_detail | L0 or L1 |

Example policy output:

```json
{
  "level": "L3_IDENTITY",
  "preserve": true,
  "reason": "identity_forming_event",
  "ttl_policy": "protect"
}
```

## 9. API Boundary Rules

- Continuity OS does not write raw memory content.
- Continuity OS may request Memory OS to protect refs.
- Continuity OS does not mutate Persona artifacts.
- Continuity OS may reference Persona artifacts in checkpoints.
- Continuity OS does not build final prompts.
- Continuity OS may request Context OS to rebuild required ContextBlocks.
- Continuity OS does not call providers.
- Runtime invokes Continuity OS during compact risk, checkpoint, and recovery flows.

## 10. Compact Survival Contract

A compact survival run must prove:

```text
Identity preserved
Memory recovered
Context rebuilt
Provider independent
Trace emitted
```

Minimum trace assertion:

```json
{
  "continuity": {
    "status": "RESTORED",
    "identity_preserved": true,
    "memory_recovered": true,
    "context_rebuilt": true
  }
}
```

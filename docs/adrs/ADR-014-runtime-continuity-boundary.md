# ADR-014: Runtime Continuity Boundary

Status: Accepted
Date: 2026-08-02
Phase: E1.7 — Runtime Integration Planning

## Context

Phase E1.6 proved Julia Core compact survival. The proof showed that identity can survive a compact-like event through ContinuityCheckpoint, RecoveryPlan, ContextReconstructor, ContextBlocks, and ContinuityTrace without relying on a single provider session or context window.

The next risk is not missing functionality. The risk is integration drift: Runtime, Memory OS, or Context OS could accidentally become the hidden owner of continuity policy and undo the boundary proven in E1.6.

## Decision

Freeze the Runtime ↔ Continuity boundary:

- Runtime OS owns lifecycle authority and trigger detection.
- Continuity OS owns identity continuity policy, checkpoint semantics, and recovery planning.
- Context OS owns reconstruction of current ContextBlocks from RecoveryPlan.
- Memory OS owns memory record retrieval and persistence, not identity protection policy.
- Provider Layer remains stateless with respect to Julia identity continuity.

Runtime must call Continuity before Context reconstruction, Memory resolution, Alignment resolution, and Provider execution for continuity-sensitive lifecycle events.

Frozen trigger set:

```yaml
continuity_trigger:
  - session_restart
  - context_compaction
  - provider_switch
  - runtime_restart
  - identity_checkpoint_update
```



## Recovery Trigger Ownership

Runtime OS owns recovery trigger detection.

Continuity OS is not a background daemon and does not watch Runtime. Runtime detects lifecycle conditions such as new session, provider switch, compact event, missing context, or runtime restart, then asks Continuity OS for a checkpoint decision or RecoveryPlan.

Correct:

```text
Runtime detects → Continuity plans
```

Rejected:

```text
Continuity watches Runtime → Continuity initiates lifecycle recovery
```

Reason: Continuity initiating lifecycle recovery would make Continuity an implicit Runtime authority.

## Required Runtime Order

```text
Runtime Event
  ↓
Continuity Check
  ↓
RecoveryPlan
  ↓
Context Reconstruction
  ↓
Memory Resolution
  ↓
Alignment Resolution
  ↓
Provider Execution
```

## Rejected Alternatives

### A. Let Memory OS trigger recovery

Rejected. Memory OS can store and retrieve records, but it must not decide what makes Julia remain Julia.

### B. Let Context OS decide restore

Rejected. Context OS builds current context; it must not own long-term preservation policy or identity anchors.

### C. Let Runtime own continuity policy

Rejected. Runtime is lifecycle authority, not continuity owner. If Runtime selects protected refs or continuity levels, Continuity OS becomes an implementation detail instead of an OS authority.

### D. Restore Julia from prompt/session summaries

Rejected. E1.6 proved checkpoint-based restoration. Prompt/session restoration would regress Julia back to context-window dependency.

## Consequences

Positive:

- Preserves E1.6 architecture proof.
- Makes E1.8 Runtime integration testable.
- Prevents Memory/Context from becoming hidden continuity authorities.
- Keeps provider switch independent from identity state.
- Enables traceable recovery gates before generation.

Cost:

- Runtime must add explicit continuity sequencing.
- Trace schema must include continuity subfields.
- Runtime tests must cover all continuity triggers.
- Provider execution may be blocked when required recovery fails.

## Required Trace Addition

```json
{
  "continuity": {
    "checkpoint_id": "...",
    "decision_level": "L3_IDENTITY",
    "recovery_status": "RESTORED",
    "trigger": "context_compaction",
    "checkpoint_loaded": true,
    "checkpoint_refs_only": true,
    "recovery_plan_created": true,
    "context_reconstruction_requested": true,
    "identity_restored": true,
    "status": "RESTORED"
  }
}
```

## Trigger

Any E1.8+ work that connects Runtime OS to Continuity OS, loads ContinuityCheckpoint during Runtime startup, reconstructs context after compact/session restart/provider switch, or adds continuity fields to Runtime trace.

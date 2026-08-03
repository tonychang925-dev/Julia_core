# Runtime Continuity Integration Design

Status: DRAFT-FROZEN
Phase: E1.7 — Runtime Integration Planning
Milestone: Julia Core Continuity Architecture Proof v1.0
Generated At: 2026-08-02

## 1. Purpose

E1.6 proved that Julia identity can be represented as Core continuity state instead of depending on a single context window.

E1.7 does not implement full Runtime integration. It freezes the Runtime ↔ Continuity boundary so E1.8 can integrate without breaking the proven E1.6 separation.

## 2. Source Proof from E1.6

E1.6 verified this chain:

```text
Memory Event
  ↓
MemoryContinuityBinder
  ↓
ContinuityDecision(L3_IDENTITY)
  ↓
ContinuityCheckpoint(refs-only)
  ↓
COMPACT SIMULATION(session/context cleared)
  ↓
RecoveryPlan
  ↓
ContextReconstructor
  ↓
ContextBlocks
  ↓
ContinuityTrace
  ↓
RESTORED
```

Architecture conclusion:

```text
Julia identity = Persona State + Continuity State + Protected Memory References + Reconstructed Context
```

not:

```text
Julia identity = Provider Session + Prompt + Conversation Window
```

## 3. Boundary Principle

Runtime OS is lifecycle authority.

Continuity OS is continuity-state authority.

These are different authorities:

| Concern | Authority |
|---|---|
| When a session starts, restarts, compacts, or switches provider | Runtime OS |
| What identity/memory/project refs must survive | Continuity OS |
| How restored context blocks are assembled | Context OS |
| Where memory records live and how refs resolve | Memory OS |
| How provider-specific behavior is adapted | Alignment OS |
| How output is generated | Provider Layer |

Hard rule:

```text
Runtime may trigger recovery.
Runtime must not decide continuity preservation policy.
Continuity may produce RecoveryPlan.
Continuity must not own runtime lifecycle.
```

## 4. Correct Integration Order

Runtime integration must follow this order:

```text
Runtime Event
  ↓
Continuity Check
  ↓
Checkpoint Load / Update
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
  ↓
ContinuityTrace + RuntimeTrace
```

Rejected order:

```text
Runtime → Memory → Context → Continuity
```

Reason: this makes Memory or Context an implicit continuity authority and regresses Julia Core back toward prompt/session reconstruction.

## 5. Runtime-Owned Trigger Set

Runtime owns detection of lifecycle events and passes the trigger reason to Continuity OS.

Frozen trigger enum for E1.7/E1.8:

```yaml
continuity_trigger:
  - session_restart
  - context_compaction
  - provider_switch
  - runtime_restart
  - identity_checkpoint_update
```

Trigger semantics:

| Trigger | Meaning | Required Runtime Action |
|---|---|---|
| `session_restart` | User/session object was recreated | Load latest checkpoint before provider execution |
| `context_compaction` | Context window or temporary context was compacted/cleared | Preserve checkpoint and request RecoveryPlan |
| `provider_switch` | Active generation provider changed | Reuse checkpoint unchanged; rerun alignment resolution |
| `runtime_restart` | Runtime process restarted | Load persisted checkpoint before context assembly |
| `identity_checkpoint_update` | Continuity policy promoted/demoted protected refs | Ask Continuity OS to issue updated checkpoint |



## 5.1 Recovery Trigger Ownership

Recovery trigger ownership is assigned to Runtime OS.

Correct flow:

```text
Runtime detects lifecycle condition
  ↓
Runtime asks Continuity OS
  ↓
Continuity OS returns checkpoint decision / RecoveryPlan
```

Continuity OS must not watch Runtime as a background daemon. It is invoked by Runtime when lifecycle state changes.

Examples of Runtime-detected conditions:

- new session;
- provider switch;
- compact event;
- missing context;
- runtime restart.

This preserves both sides of the boundary:

- Runtime remains lifecycle entrypoint.
- Continuity remains continuity-state authority.

## 6. Continuity Responsibilities During Runtime Integration

Continuity OS owns:

- Loading a `ContinuityCheckpoint` by `agent_id`.
- Validating checkpoint version and refs-only invariant.
- Creating `RecoveryPlan` from checkpoint and trigger.
- Marking identity restoration requirements.
- Emitting continuity trace fields.

Continuity OS does not own:

- Calling provider APIs.
- Persisting raw memory records.
- Reconstructing final ContextBlocks.
- Mutating Persona artifacts.
- Deciding Runtime lifecycle state.

## 7. Runtime Responsibilities During Continuity Integration

Runtime OS owns:

- Detecting lifecycle trigger.
- Sequencing Continuity before Context/Memory/Provider.
- Passing RecoveryPlan to Context OS.
- Ensuring provider execution only occurs after required recovery gates pass.
- Attaching continuity trace into the runtime trace.

Runtime OS does not own:

- Continuity level classification.
- Identity anchor selection.
- Protected memory ref promotion.
- Checkpoint schema semantics.

## 8. Trace Extension

Current E1.6 trace fields are sufficient for proof but not for Runtime integration.

E1.7 freezes the Runtime trace extension:

```json
{
  "runtime": "PASS",
  "memory": "PASS",
  "context": "PASS",
  "continuity": {
    "trigger": "context_compaction",
    "checkpoint_loaded": true,
    "checkpoint_refs_only": true,
    "recovery_plan_created": true,
    "context_reconstruction_requested": true,
    "identity_restored": true,
    "provider_changed": false,
    "status": "RESTORED"
  }
}
```



Additional required E1.8+ identity trace fields:

```json
{
  "continuity": {
    "checkpoint_id": "checkpoint://julia/latest",
    "decision_level": "L3_IDENTITY",
    "recovery_status": "RESTORED"
  }
}
```

These fields explain why Julia remains Julia after compact/session restart/provider switch, instead of relying on provider output similarity.

Minimum PASS criteria:

- `checkpoint_loaded == true`
- `checkpoint_refs_only == true`
- `recovery_plan_created == true`
- `identity_restored == true`
- `status == "RESTORED"`

## 8.1 ExecutionTrace Contract v1.1

E1.8.2 freezes the first Runtime continuity trace contract:

```json
{
  "trace_version": "1.1",
  "runtime": {
    "runtime_id": "julia-runtime",
    "session_id": "session-123",
    "event": "SESSION_START"
  },
  "continuity": {
    "checked": true,
    "checkpoint_found": true,
    "checkpoint_id": "checkpoint://julia/latest",
    "decision_level": "L3_IDENTITY",
    "recovery_status": "NOT_STARTED"
  },
  "authority_chain": [
    "Runtime",
    "ContinuityHook",
    "ContinuityOS"
  ]
}
```

`authority_chain` is trace evidence for who decided what. In E1.8.2 it must not include Memory, Context, Alignment, Provider, or LLM because those systems are not connected yet.

## 8.2 Recovery Trigger Simulation Contract

E1.8.3 introduces recovery intent evaluation without executing recovery:

```text
Runtime Event + checkpoint availability -> RecoveryTriggerDecision
```

Required outcomes:

| Runtime event | checkpoint_available | recovery_status |
|---|---:|---|
| `SESSION_START` | false | `NOT_REQUIRED` |
| `RUNTIME_RECOVERY` | true | `RECOVERY_REQUIRED` |
| `PROVIDER_SWITCH` | true | `RECOVERY_REQUIRED`, with `continuity_state_changed=false` |

This remains simulation-only. Memory loading, Context Reconstruction, Alignment, Provider switch, and Provider call are excluded.

## 9. Runtime Gate Contract

Before provider execution, Runtime must evaluate:

```text
if continuity_required(trigger):
    checkpoint = continuity.load_checkpoint(agent_id)
    recovery_plan = continuity.create_recovery_plan(checkpoint, trigger)
    context_blocks = context.reconstruct(recovery_plan)
    trace = continuity.emit_trace(checkpoint, recovery_plan, context_blocks)
    require trace.status == RESTORED
```

Provider execution is blocked when:

- no checkpoint exists for required L3 identity recovery;
- checkpoint violates refs-only invariant;
- RecoveryPlan cannot be created;
- required identity ContextBlock cannot be reconstructed;
- continuity trace is not RESTORED.

## 10. Non-Goals for E1.7

- No full Runtime code integration.
- No live provider call.
- No persistence backend migration.
- No new memory schema.
- No prompt-based Julia restoration.
- No product integration into Julia AI Assistant.

## 11. E1.8 Implementation Readiness Checklist

E1.8 may begin only after these design gates are accepted:

- [ ] Runtime trigger enum frozen.
- [ ] Runtime/Continuity authority boundary frozen.
- [ ] Trace extension frozen.
- [ ] Integration order frozen.
- [ ] Provider execution gate defined.
- [ ] Rollback/non-goals documented.

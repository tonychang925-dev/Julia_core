# Phase Contract — E1.8.3 Recovery Trigger Simulation

Status: COMPLETE
Phase Name: Recovery Trigger Simulation
Phase Code: E1.8.3
Decision: APPROVED
Implementation Status: COMPLETE
Parent Milestone: E1.8 Runtime Continuity Integration
Risk Level: P0
Generated At: 2026-08-02
Source Documents:
- `docs/project_control/PHASE_CONTRACT_E1.8.2_CONTINUITY_TRACE_INTEGRATION.md`
- `docs/architecture/RUNTIME_CONTINUITY_INTEGRATION_DESIGN.md`
- `docs/adrs/ADR-014-runtime-continuity-boundary.md`

## 1. Objective

Simulate recovery trigger evaluation without executing recovery.

E1.8.3 verifies:

```text
Runtime detects recovery condition
  ↓
Continuity evaluates recovery intent
  ↓
Trace records recovery intent
```

This phase must not load Memory, rebuild Context, invoke Alignment, switch Provider, or call Provider.

## 2. Acceptance Targets

- [x] `RecoveryTrigger` exists.
- [x] `RecoveryTriggerInput` exists.
- [x] `RecoveryTriggerDecision` exists.
- [x] `SESSION_START + checkpoint=false` returns `NOT_REQUIRED`.
- [x] `RUNTIME_RECOVERY + checkpoint=true` returns `RECOVERY_REQUIRED`.
- [x] `PROVIDER_SWITCH + checkpoint=true` records provider change without changing continuity state.
- [x] Recovery intent can be represented in trace-compatible form.
- [x] Recovery trigger exposes no Memory/Context/Provider/Runtime-control methods.
- [x] Recovery trigger imports no Memory OS, Context OS, Provider, or Alignment modules.

## 3. Required Commands

```bash
cd julia_core && python3 -m unittest tests.test_recovery_trigger_simulation tests.test_continuity_trace_integration tests.test_runtime_continuity_hook
```

Regression baseline:

```bash
cd julia_core && python3 -m unittest tests.test_compact_survival tests.test_context_reconstruction tests.test_memory_continuity_binding tests.test_continuity_runtime_simulation
```

## 4. Deliverables

| Deliverable | Path | Verification |
|---|---|---|
| Recovery trigger simulation | `julia_core/continuity/trigger.py` | importable and tested |
| Recovery trigger tests | `tests/test_recovery_trigger_simulation.py` | unittest passes |
| Phase contract | `docs/project_control/PHASE_CONTRACT_E1.8.3_RECOVERY_TRIGGER_SIMULATION.md` | file exists |

## 5. Decision Cases

### Case 1 — Normal First Start

Input:

```json
{
  "event": "SESSION_START",
  "checkpoint_available": false
}
```

Output:

```json
{
  "recovery_required": false,
  "reason": "first_session_no_checkpoint",
  "recovery_status": "NOT_REQUIRED"
}
```

### Case 2 — Runtime Recovery With Checkpoint

Input:

```json
{
  "event": "RUNTIME_RECOVERY",
  "checkpoint_available": true
}
```

Output:

```json
{
  "recovery_required": true,
  "reason": "checkpoint_available",
  "recovery_status": "RECOVERY_REQUIRED"
}
```

### Case 3 — Provider Switch

Input:

```json
{
  "event": "PROVIDER_SWITCH",
  "checkpoint_available": true,
  "provider_changed": true
}
```

Output:

```json
{
  "recovery_required": true,
  "reason": "provider_switch_continuity_state_unchanged",
  "recovery_status": "RECOVERY_REQUIRED",
  "continuity_state_changed": false,
  "provider_changed": true
}
```

## 6. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---|---:|---|---|---|
| Simulation executes recovery | P0 | Medium | Memory/Context/Provider calls appear | Continuity | Trigger only returns intent |
| Provider switch mutates continuity state | P0 | Medium | provider change rewrites checkpoint | Architecture | Test asserts `continuity_state_changed=false` |
| First startup treated as failure | P1 | Medium | missing checkpoint becomes error | Runtime | checkpoint=false maps to `NOT_REQUIRED` for first start |

## 7. Rollback Plan

### Code Rollback

Revert:

- `julia_core/continuity/trigger.py`
- `tests/test_recovery_trigger_simulation.py`

### Data Rollback

No data migration or checkpoint persistence migration exists in E1.8.3.

### Documentation Rollback

If recovery intent schema changes, update this contract before E1.8.4.

Rollback trigger: any real Memory, Context, Alignment, or Provider execution appears in E1.8.3.

## 8. Non-Goals

- No Memory OS resolution.
- No Context Reconstruction.
- No Alignment OS integration.
- No Provider invocation or switching.
- No checkpoint mutation.
- No product-level Julia AI Assistant migration.

## 9. Implementation Results

Implemented files:

- `julia_core/continuity/trigger.py`
- `tests/test_recovery_trigger_simulation.py`

Validated behavior:

- Normal first session is not recovery.
- Runtime recovery with checkpoint generates recovery intent.
- Provider switch does not mutate continuity state.
- Trigger has no downstream imports or recovery execution methods.

Result: PASS.

# Phase Contract — E1.3.8 Continuity Runtime Simulation

Status: DRAFT-FROZEN
Phase Name: Continuity Runtime Simulation
Phase Code: E1.3.8
Parent Milestone: Julia Core Continuity Architecture
Risk Level: P0
Generated At: 2026-08-01

## 1. Objective

Prove Continuity OS can independently simulate compact survival without integrating real Runtime, Memory OS, Context OS, or Provider.

Simulation flow:

```text
conversation event
  ↓
ContinuityRequest
  ↓
ContinuityDecision
  ↓
ContinuityCheckpoint
  ↓
COMPACT: delete session state
  ↓
RecoveryPlan
  ↓
ContinuityTrace
```

## 2. Acceptance Targets

- [ ] Simulation classifies identity-forming event as L3.
- [ ] Simulation creates checkpoint with refs only.
- [ ] Compact simulation deletes session state.
- [ ] Recovery plan is generated from checkpoint.
- [ ] ContinuityTrace reports RESTORED.
- [ ] Provider switch does not change checkpoint identity refs or protected memory refs.
- [ ] Simulation does not call provider.
- [ ] Simulation report is generated.

## 3. Required Commands

```bash
cd julia_core && python3 -m unittest tests.test_continuity_runtime_simulation
```

## 4. Deliverables

| Deliverable | Path |
|---|---|
| Simulation tests | `tests/test_continuity_runtime_simulation.py` |
| Simulation report | `docs/verification/CONTINUITY_SIMULATION_REPORT_v1.md` |
| E1.3.8 contract | `docs/project_control/PHASE_CONTRACT_E1.3.8_CONTINUITY_RUNTIME_SIMULATION.md` |

## 5. Non-Goals

- No real Runtime integration.
- No Memory OS adapter.
- No Context OS rebuild.
- No provider call.
- No checkpoint persistence backend.

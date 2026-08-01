# Phase Contract — E1.5 Context Reconstruction

Status: DRAFT-FROZEN
Phase Name: Context Reconstruction
Phase Code: E1.5
Parent Milestone: Julia Core Continuity Architecture
Risk Level: P0
Generated At: 2026-08-01

## 1. Objective

Implement minimal Context Reconstruction contracts and helpers that convert ContinuityCheckpoint + RecoveryPlan into short-lived ContextBlocks.

## 2. Acceptance Targets

- [ ] ContextReconstructionRequest exists.
- [ ] ContextRequirement exists.
- [ ] ContextReconstructionResult exists.
- [ ] Reconstruction produces identity, memory_reference, relationship, and project ContextBlocks from refs.
- [ ] Context rejects raw history dumps.
- [ ] Context does not mutate Continuity objects.
- [ ] Context does not expose memory write API.

## 3. Required Commands

```bash
cd julia_core && python3 -m unittest tests.test_context_reconstruction tests.test_context_continuity_boundary
```

## 4. Deliverables

| Deliverable | Path |
|---|---|
| Design | `docs/architecture/CONTEXT_RECONSTRUCTION_DESIGN.md` |
| ADR | `docs/adrs/ADR-013-context-reconstruction-boundary.md` |
| Contract | `docs/project_control/PHASE_CONTRACT_E1.5_CONTEXT_RECONSTRUCTION.md` |
| Requirements | `julia_core/context_os/requirements.py` |
| Reconstruction | `julia_core/context_os/reconstruction.py` |
| Tests | `tests/test_context_reconstruction.py`, `tests/test_context_continuity_boundary.py` |

## 5. Non-Goals

- No provider call.
- No memory write.
- No checkpoint mutation.
- No full Context OS planner integration.
- No old context window restore.

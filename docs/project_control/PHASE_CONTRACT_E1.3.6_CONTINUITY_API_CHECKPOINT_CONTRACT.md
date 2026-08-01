# Phase Contract — E1.3.6 Continuity API & Checkpoint Contract Freeze

Status: DRAFT-FROZEN
Phase Name: Continuity API & Checkpoint Contract Freeze
Phase Code: E1.3.6
Parent Milestone: Julia Core Continuity Architecture
Risk Level: P0
Generated At: 2026-08-01

## 1. Objective

Freeze Continuity OS API contracts before implementation.

This phase defines:

- ContinuityRequest
- ContinuityDecision
- ContinuityCheckpoint
- RecoveryPlan
- ContinuityTrace
- Compact Survival Contract

## 2. Acceptance Targets

- [ ] `CONTINUITY_API_DESIGN.md` defines all five core objects.
- [ ] `ADR-010` freezes checkpoint model.
- [ ] `ADR-011` freezes compact recovery protocol.
- [ ] API boundary rules explicitly prevent Continuity OS from becoming Memory, Persona, Context, Provider, or reasoning engine.
- [ ] Compact Survival trace requirements are defined.

## 3. Required Commands

```bash
test -f julia_core/docs/architecture/CONTINUITY_API_DESIGN.md
```

```bash
test -f julia_core/docs/adrs/ADR-010-continuity-checkpoint-model.md
```

```bash
test -f julia_core/docs/adrs/ADR-011-compact-recovery-protocol.md
```

## 4. Deliverables

| Deliverable | Path |
|---|---|
| Continuity API design | `docs/architecture/CONTINUITY_API_DESIGN.md` |
| Checkpoint ADR | `docs/adrs/ADR-010-continuity-checkpoint-model.md` |
| Compact recovery ADR | `docs/adrs/ADR-011-compact-recovery-protocol.md` |
| E1.3.6 contract | `docs/project_control/PHASE_CONTRACT_E1.3.6_CONTINUITY_API_CHECKPOINT_CONTRACT.md` |

## 5. Non-Goals

This phase does not implement runtime code, checkpoint storage, memory protection, context rebuild, or provider switching.


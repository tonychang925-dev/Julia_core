# Phase Contract — E2.1 Runtime Continuity Integration

Status: DRAFT-FROZEN
Phase Name: Runtime Continuity Integration
Phase Code: E2.1
Parent Milestone: Phase E2 — Julia AI Assistant Real Runtime Continuity Validation
Risk Level: P0
Generated At: 2026-08-02
Source Documents:
- `docs/project_control/PHASE_CONTRACT_E2.0.1_CORE_CONSUMPTION_REVIEW.md`
- `/Users/admin/julia_ai_assistant/docs/verification/JULIA_AI_ASSISTANT_CORE_CONSUMPTION_REVIEW_v1.md`
- `docs/verification/JULIA_CORE_CONTINUITY_ARCHITECTURE_PROOF_v1.md`

## 1. Objective

Integrate Julia AI Assistant runtime with Julia Core continuity architecture in small steps, without allowing legacy app modules to retain Core authority.

E2.1 is split into subphases to prevent broad rewrite and preserve trace evidence at each step.

## 2. Subphase Route

| Subphase | Goal | Scope |
|---|---|---|
| E2.1.1 | Runtime Continuity Binding | Assistant Runtime → Core RuntimeContinuityHook only |
| E2.1.2 | Persona Migration | Replace app giant persona prompt with Core Persona Artifact consumption |
| E2.1.3 | Memory Migration | Replace memory→prompt path with memory_ref→Core governance path |
| E2.1.4 | Trace Completion | Produce full trace components for runtime/session/continuity/persona/memory/context/alignment/provider |

## 3. No Legacy Authority Rule

Any app module owning Persona decision, Memory ranking/governance, Identity judgment, Continuity decision, Context reconstruction, Alignment policy, or Provider identity shaping must be removed, moved to Core, or downgraded to adapter.

## 4. E2.1 Non-Goals

- No one-step rewrite.
- No live provider quality evaluation as acceptance evidence.
- No prompt engineering fallback.
- No new Julia Core capability unless a missing Core authority is proven.

## 5. Required Commands

```bash
cd julia_core && test -f docs/project_control/PHASE_CONTRACT_E2.1_RUNTIME_CONTINUITY_INTEGRATION.md
```

## 6. Deliverables

| Deliverable | Path |
|---|---|
| E2.1 umbrella contract | `docs/project_control/PHASE_CONTRACT_E2.1_RUNTIME_CONTINUITY_INTEGRATION.md` |
| E2.1.1 subphase contract | `docs/project_control/PHASE_CONTRACT_E2.1.1_RUNTIME_CONTINUITY_BINDING.md` |

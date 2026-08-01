# Context Reconstruction Design

Status: DRAFT-FROZEN
Phase: E1.5 — Context Reconstruction
Scope: Julia Core OS
Generated At: 2026-08-01

## 1. Purpose

Define how Context OS reconstructs current context from Continuity recovery state.

Context Reconstruction is not Context Restore.

```text
Wrong:
old context window → reload

Correct:
ContinuityCheckpoint + RecoveryPlan → requirements → new ContextBlocks
```

## 2. Authority Boundaries

| Authority | Owns |
|---|---|
| Continuity OS | what must survive |
| Context OS | what must be loaded now |
| Memory OS | historical source refs |
| Persona Engine | identity artifact source |

Context OS must not:

- modify Continuity decisions;
- write Memory;
- store raw conversation dumps;
- promote identity level;
- call providers.

## 3. Core Contracts

### ContextReconstructionRequest

```json
{
  "request_id": "ctx-recon-001",
  "agent_id": "julia",
  "recovery_plan_id": "recovery://julia/compact",
  "checkpoint_id": "continuity://checkpoint/julia/latest",
  "current_intent": "compact_recovery"
}
```

### ContextRequirement

```json
{
  "required_type": "identity|relationship|memory_reference|project",
  "source": "persona|memory|project|continuity",
  "priority": "critical|high|medium|low",
  "refs": ["memory://event/julia-core-origin"]
}
```

### ContextReconstructionResult

```json
{
  "context_blocks": ["ContextBlock.identity", "ContextBlock.memory_reference"],
  "continuity_restored": true,
  "source_checkpoint": "continuity://checkpoint/julia/latest"
}
```

## 4. Reconstruction Flow

```text
ContinuityCheckpoint
  ↓
RecoveryPlan.required_context_blocks
  ↓
ContextRequirement[]
  ↓
ContextBlock[]
```

## 5. Boundary Tests

- Context must not mutate Continuity.
- Context must not write Memory.
- Context must consume refs only.
- Context must reject raw history dumps.

# ADR-013: Context Reconstruction Boundary

Status: Proposed
Date: 2026-08-01

## Context

After compaction or restart, Julia Core must reconstruct current context from continuity state. This is not equivalent to restoring the previous context window.

## Decision

Context OS owns reconstruction of current ContextBlocks from RecoveryPlan and ContinuityCheckpoint refs.

Context OS does not own continuity policy, memory persistence, persona mutation, or provider generation.

## Consequences

Positive:

- Compact recovery does not require reloading old context windows.
- Context remains short-lived and current.
- Continuity state remains policy authority.

Rejected alternatives:

- Reload old context window.
- Store raw conversation in ContextBlock.
- Let Context OS promote identity continuity level.

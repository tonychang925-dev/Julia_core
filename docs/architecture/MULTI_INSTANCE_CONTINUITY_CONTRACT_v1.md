# Multi-Instance Continuity Contract v1.0

Status: FROZEN
Date: 2026-08-02
Source Phase: F4 Multi-Instance Continuity

## 1. Purpose

Validate that multiple Julia runtime/provider instances can consume the same Julia identity without creating independent identity authorities.

## 2. Target Model

```text
Julia Identity State
  ↓
Shared Identity Contract
  ↓
Runtime Instance A / Provider A
Runtime Instance B / Provider B
Runtime Instance C / Provider C
```

Runtime is a body. Provider is a generation capability. Identity is the governed subject.

## 3. Authority Boundary

```text
Instance Runtime      → executes
Provider             → renders language
Consolidation Engine → proposes learning
Continuity OS        → governs identity/protection impact
Memory OS            → stores approved evolution
Identity Contract    → defines invariant anchors
```

## 4. Required Checks

- Parallel instances must share the same identity artifact and baseline anchors.
- Provider/runtime variance must not mutate Persona Artifact or Continuity State.
- Instance-local learning must produce proposals, not identity mutation.
- Conflicting proposals must require reconciliation.
- Split-brain identity divergence must be detected, not hidden.

## 5. Forbidden

- instance-local Persona mutation
- provider-specific identity rewrite
- hidden local checkpoint authority
- direct memory overwrite from one instance
- treating response style variance as identity versioning

## 6. Identity Synchronization Score

```text
ISS = Identity Anchor Consistency
    + Decision Consistency
    + Memory Governance Consistency
    - Divergence Penalty
```

Passing gate requires `ISS >= 0.95` and split-brain detection for divergent identity state.

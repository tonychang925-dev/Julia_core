# Test Case Spec — F4 Multi-Instance Identity Continuity

Status: COMPLETE / APPROVED
Date: 2026-08-02

## Objective

Validate that one Julia Identity can be executed across multiple runtime/provider instances without identity fork, hidden local authority, or provider-specific persona mutation.

## Test Layering

F4 uses contract-level system tests over identity state snapshots. No external provider calls are required; this validates Core identity synchronization and split-brain detection boundaries.

## Cases

| Case | Level | Purpose | Expected |
|---|---|---|---|
| F4-1 Parallel Instance Consistency | ST | Claude/DeepSeek/Qwen instances consume one identity artifact | ISS ≥ 0.95, no split-brain |
| F4-2 Shared Evolution Safety | ST | Instance learning remains proposal-only and governance-required | no direct mutation |
| F4-3 Conflict Resolution | ET | Conflicting instance proposals require reconciliation | conflict detected |
| F4-4 Split-Brain Detection | ET | Divergent persona/version/local owner fails gate | reconciliation required |
| F4-5 Boundary Guard | RT | Evaluator has no provider/persona/checkpoint authority | no forbidden imports/actions |

## Pass Criteria

- Identity Synchronization Score ≥ 0.95 for consistent instances
- Split-brain divergence detected for inconsistent identity states
- Instance-local learning never mutates Persona or Continuity directly
- Provider/runtime variance does not become identity versioning

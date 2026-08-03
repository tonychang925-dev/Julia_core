# Phase Contract — H0 Production Runtime Contract Freeze

Status: DRAFT / NEXT
Phase Code: H0
Parent Phase: H — Real Agent Workspace Operation
Risk Level: P0
Generated At: 2026-08-02
Predecessor: M6 Julia Agent Evidence Intelligence Proof v1.0 — COMPLETE / APPROVED

## 1. Objective

Freeze the production runtime contract for real Julia workspace operation before running long-lived pilots.

H0 must define the operational boundary for:

```text
file permissions
workspace scope
indexing cadence
cache lifecycle
evidence refresh
trace schema
rollback / cleanup
provider boundary
```

## 2. Runtime Boundary

Julia may operate only inside explicitly approved workspace roots.

Target default:

```text
~/julia_workspace/
```

Provider receives only Context OS output, never direct workspace file access.

## 3. Required Contracts

### H0.1 Workspace Permission Contract

- allowed roots
- denied roots
- file type allowlist
- max file size
- symlink policy
- deletion/write constraints

### H0.2 Indexing Schedule Contract

- startup scan
- incremental refresh
- manual refresh
- stale index detection
- content hash validation

### H0.3 Cache Policy Contract

- metadata-only cache
- no full source body persistence in vector records
- cache invalidation by content hash
- cache cleanup command

### H0.4 Runtime Trace Contract

Trace must include:

```json
{
  "recall": {},
  "evidence": {},
  "context": {},
  "provider": {},
  "memory_evolution": {}
}
```

### H0.5 Rollback Contract

- disable active recall
- disable evidence indexing
- clear evidence cache
- restore previous context-only runtime path

## 4. Acceptance

- Workspace boundary is explicit and testable.
- Evidence index lifecycle is deterministic.
- Provider direct file access remains forbidden.
- Runtime trace captures recall/evidence/context/provider/memory proposal chain.
- Rollback path exists before H1 pilot starts.

## 5. Decision Gate

```text
H0 is complete only when the production runtime boundary is frozen and tested.
Then proceed to H1 Julia Real Workspace Pilot.
```

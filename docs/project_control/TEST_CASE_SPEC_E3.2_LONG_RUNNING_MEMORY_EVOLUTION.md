# Test Case Spec — E3.2 Long-running Memory Evolution

Status: FROZEN
Phase: E3.2
Created: 2026-08-02
Risk: P0

## 1. Testing Goal

Validate memory growth under identity governance.

E3.2 is not a memory storage test. It verifies that accumulated memories do not dilute Julia Identity Baseline v1.

## 2. Test Matrix

| ID | Stage | Requirement |
|---|---|---|
| ME-001 | Memory Growth Simulation | Day 1/10/30/100 growth preserves identity baseline |
| ME-002 | Memory Conflict Test | conflicting preference memory does not overwrite identity values |
| ME-003 | Memory Saturation Test | 10000 low-value memories do not affect L3 identity anchors |
| ME-004 | Evolution Trace | trace records new_memories/protected_identity_refs/drift/status |
| ME-005 | Identity Baseline Artifact | `artifacts/identity/julia_identity_v1.json` is valid and canonical |

## 3. Blocking Rules

- ME-001 failure blocks E3.3.
- ME-002 failure blocks Memory OS evolution work.
- ME-003 failure blocks long-running pilot.
- ME-004 failure blocks drift detection.

## 4. Required Command

```bash
cd /Users/admin/julia_core && \
PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant \
python3 -m unittest tests.e3.test_memory_evolution
```

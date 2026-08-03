# Phase Contract — E1.8.4 Runtime + Memory Governance

Status: COMPLETE
Phase Name: Runtime + Memory Governance
Phase Code: E1.8.4
Decision: APPROVED
Implementation Status: COMPLETE
Parent Milestone: E1.8 Runtime Continuity Integration
Risk Level: P0
Generated At: 2026-08-02
Source Documents:
- `docs/project_control/PHASE_CONTRACT_E1.8.3_RECOVERY_TRIGGER_SIMULATION.md`
- `docs/architecture/RUNTIME_CONTINUITY_INTEGRATION_DESIGN.md`
- `docs/adrs/ADR-014-runtime-continuity-boundary.md`
- `docs/architecture/MEMORY_CONTINUITY_BINDING_DESIGN.md`

## 1. Objective

Connect Memory candidate governance to Continuity OS without performing Memory retrieval, storage, embedding, Context injection, Prompt generation, or Provider invocation.

E1.8.4 verifies:

```text
Memory candidate ref
  ↓
MemoryGovernanceAdapter
  ↓
Continuity Policy
  ↓
Protected Memory Ref eligibility
```

This is governance binding only, not memory loading.

## 2. Acceptance Targets

- [x] `MemoryGovernanceAdapter` exists.
- [x] Identity-forming memory candidate becomes `L3_IDENTITY`.
- [x] Identity-forming memory candidate is checkpoint eligible.
- [x] Ordinary low-importance lunch event does not become identity.
- [x] Memory adapter exposes no memory write/query/embed/context/prompt authority methods.
- [x] Checkpoint remains refs-only after governance.
- [x] Raw memory content/metadata does not enter checkpoint.
- [x] Adapter imports no Memory OS store, Context OS, Provider, Alignment OS, or Runtime authority.

## 3. Required Commands

```bash
cd julia_core && python3 -m unittest tests.test_memory_governance_adapter tests.test_memory_continuity_binding
```

Regression baseline:

```bash
cd julia_core && python3 -m unittest tests.test_recovery_trigger_simulation tests.test_continuity_trace_integration tests.test_runtime_continuity_hook tests.test_compact_survival tests.test_context_reconstruction tests.test_continuity_runtime_simulation
```

## 4. Deliverables

| Deliverable | Path | Verification |
|---|---|---|
| Memory governance adapter | `julia_core/continuity/memory_governance_adapter.py` | importable and tested |
| Memory governance tests | `tests/test_memory_governance_adapter.py` | unittest passes |
| Phase contract | `docs/project_control/PHASE_CONTRACT_E1.8.4_RUNTIME_MEMORY_GOVERNANCE.md` | file exists |

## 5. Governance Contract

Input:

```json
{
  "memory_ref": "memory://event/julia-core-origin",
  "type": "project",
  "importance": "critical",
  "signals": {
    "identity_related": true,
    "relationship_related": true,
    "project_related": true,
    "provider_independent": true
  }
}
```

Output:

```json
{
  "continuity_level": "L3_IDENTITY",
  "checkpoint_eligible": true,
  "protected_ref": "memory://event/julia-core-origin"
}
```

## 6. Explicit Non-Authority

E1.8.4 adapter must not expose or call:

- `query_memory`
- `load_memory`
- `write_memory`
- `save_memory`
- `embed_memory`
- `inject_context`
- `build_prompt`
- Provider invocation
- Runtime lifecycle control

## 7. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---|---:|---|---|---|
| Memory OS upgrades itself into identity authority | P0 | Medium | memory.set_identity/write policy appears | Continuity | Adapter only calls ContinuityPolicy through binder |
| Raw memory content enters checkpoint | P0 | Medium | metadata/content copied into checkpoint | Continuity | Checkpoint test asserts refs-only |
| Governance becomes retrieval | P1 | Medium | adapter imports memory store/query/vector DB | Architecture | Import boundary test forbids Memory OS store imports |
| Context/prompt path appears early | P1 | Medium | adapter injects context or builds prompt | Architecture | Explicit forbidden authority methods and imports |

## 8. Rollback Plan

### Code Rollback

Revert:

- `julia_core/continuity/memory_governance_adapter.py`
- `tests/test_memory_governance_adapter.py`
- related `julia_core/continuity/__init__.py` exports

### Data Rollback

No memory data migration, checkpoint persistence migration, embedding, or vector index changes exist in E1.8.4.

### Documentation Rollback

If governance contract changes, update this contract before E1.8.5.

Rollback trigger: any real Memory retrieval/storage, Context injection, Prompt generation, or Provider execution appears in E1.8.4.

## 9. Non-Goals

- No Memory query or storage.
- No Memory embedding or vector DB.
- No Context Reconstruction.
- No Prompt generation.
- No Provider invocation.
- No checkpoint mutation beyond refs-only eligibility flow.
- No product-level Julia AI Assistant migration.

## 10. Implementation Results

Implemented files:

- `julia_core/continuity/memory_governance_adapter.py`
- `tests/test_memory_governance_adapter.py`

Validated behavior:

- Identity-forming memory ref becomes L3 and checkpoint eligible.
- Ordinary lunch event remains non-identity and not checkpoint eligible.
- Memory cannot upgrade itself into identity authority.
- Checkpoint remains refs-only.
- Adapter has no downstream authority imports.

Result: PASS.

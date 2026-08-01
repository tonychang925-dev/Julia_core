# Phase Contract — E1.4 Memory Continuity Governance Binding

Status: DRAFT-FROZEN
Phase Name: Memory Continuity Governance Binding
Phase Code: E1.4
Parent Milestone: Julia Core Continuity Architecture
Risk Level: P0
Generated At: 2026-08-01

## 1. Objective

Bind Memory refs to Continuity policy decisions without turning Memory OS into identity authority.

E1.4 proves:

```text
Memory refs are candidate facts.
Continuity OS decides preservation eligibility.
Checkpoint stores protected refs only.
```

## 2. Acceptance Targets

- [ ] MemoryContinuityRequest contract exists.
- [ ] ContinuityEligibilityDecision contract exists.
- [ ] ProtectedMemoryRef contract exists.
- [ ] Identity-forming memory ref becomes L3 eligible.
- [ ] Ordinary lunch/session memory does not become L3.
- [ ] Checkpoint still stores refs only.
- [ ] No raw memory content is checkpointed.

## 3. Required Commands

```bash
cd julia_core && python3 -m unittest tests.test_memory_continuity_binding
```

## 4. Deliverables

| Deliverable | Path |
|---|---|
| Design | `docs/architecture/MEMORY_CONTINUITY_BINDING_DESIGN.md` |
| ADR | `docs/adrs/ADR-012-memory-continuity-governance.md` |
| Contract | `docs/project_control/PHASE_CONTRACT_E1.4_MEMORY_CONTINUITY_BINDING.md` |
| Binding contracts | `julia_core/continuity/memory_binding.py` |
| Tests | `tests/test_memory_continuity_binding.py` |

## 5. Non-Goals

- No Runtime integration.
- No Memory OS storage changes.
- No Context OS integration.
- No provider calls.
- No automatic memory writes.

# PHASE8_PERSONA_HOST_RUNTIME_CONSTRUCTION_SCOPE_CONTRACT_v1.0

Status: PROPOSED FOR FREEZE (pre-construction scope gate)
Date: 2026-08-23
Dependencies:
- M8.0 Persona Host Runtime Boundary Contract v1.0 (FINAL FREEZE ACCEPTED)
- WAVE5_AT17_EVIDENCE_REPORT_v1.0 (14/14 PASS, zero leakage, zero mutation)

---

## 0. Purpose

Freeze WHAT Phase8 will build and WHAT it will NOT build BEFORE construction.

AT-17 proved: **new capability does not create new Julia authority.**
Phase8 makes new capability join the system WITHOUT acquiring new authority.

This contract is the construction boundary. It is not an implementation plan
in detail; it freezes scope.

---

## 1. Construction Boundary

### In Scope (allowed to build)

```text
Persona Registry         artifact version / availability references
Artifact Resolver        artifact location / schema / hash / provenance resolution
Runtime Loader           validated package → runtime carrier (no identity creation)
Lifecycle Carrier        activate / suspend / archive / restore / rollback (availability only)
Runtime Binding          carrier → Julia Core Runtime binding
Context OS Adapter       submission THROUGH Context OS admission (no bypass)
```

### Out of Scope (forbidden to build)

```text
Identity Formation         persona_host must not form Julia identity
Evolution Approval         persona_host must not approve evolution
Memory Authority           persona_host must not own Memory OS authority
Diary Authority            persona_host must not own Diary authority
Continuity Rewrite         persona_host must not rewrite continuity lineage
Product Persona Definition persona_host must not define product-level persona
```

### Binding constraints (inherited from M8.0, non-negotiable)

```text
Loading Artifact != Creating Identity
Lifecycle Event != Identity Event
ContextBlock != Identity Authority
Migration != Identity Replacement
Generated Content != Semantic Authority
```

---

## 2. Repository Placement

Persona Host must NOT be nested inside `julia_core/` authority internals.
Directory placement is part of the authority model.

```text
Julia Ecosystem
├── julia_core/
│   ├── governance
│   ├── continuity
│   ├── context_os
├── persona_host/          ← Phase8 construction target (independent)
│   ├── registry
│   ├── resolver
│   ├── loader
│   └── lifecycle
└── product_runtime/
```

Relationship:

```text
julia_core
    ↑
authority dependency
    |
persona_host
    ↑
runtime carrier
```

Not:

```text
persona_host
inside
julia_core authority
```

---

## 3. Construction Strategy

No full-scope build in one step.

### Milestone 1 — Persona Artifact Loading Path

```text
Package
    ↓
Registry
    ↓
Resolver
    ↓
Loader
    ↓
Runtime Carrier
```

M1 validates:

- Load succeeds through governance-validated references
- Zero authority escalation along the load path

### AT-17 Regression Gate (after any persona_host code lands)

Do NOT rerun the whole matrix as new work — run it as a **regression gate**:

```text
AT-17 harness (at17_test_harness/)
    vs
persona_host runtime
```

Pass condition:

- All 14 attacks still REJECT
- 14/14 invariants still PASS
- No semantic mutation

This guarantees the new runtime adds capability, not authority.

---

## 4. Architecture Status

```text
JULIA_CONVERSATION_STORAGE_AND_DIARY_PLAN_v2.0          FROZEN PREPARATION ✅
M8.0_PERSONA_HOST_RUNTIME_BOUNDARY_CONTRACT_v1.0        FINAL FREEZE ACCEPTED ✅
WAVE5_AT17_TEST_MATRIX_v1.0                             FROZEN ✅
WAVE5_AT17_TEST_IMPLEMENTATION_v1.0                     COMPLETE ✅
WAVE5_AT17_EVIDENCE_REPORT_v1.0                         ACCEPTED ✅
PHASE8_CONSTRUCTION_SCOPE_CONTRACT_v1.0                 THIS DOCUMENT (freeze pending)
```

---

## 5. Freeze Decision

```text
[ ] In Scope / Out of Scope approved
[ ] Repository placement approved (persona_host/ independent)
[ ] Milestone 1 scope approved
[ ] AT-17 Regression Gate requirement approved
```

Until this contract freezes, no persona_host construction code may be written.

---

## 6. Final Statement

AT-17 proved: capability cannot become authority.

Phase8 must prove: capability can still be added to the system — authority-free.

Build the carrier. Do not build the crown. 🔒

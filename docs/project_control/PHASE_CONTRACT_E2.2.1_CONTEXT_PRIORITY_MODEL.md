# Phase Contract — E2.2.1 Context Priority Model

Status: COMPLETE / APPROVED
Phase Name: Context Priority Model
Phase Code: E2.2.1
Parent Phase: E2.2 Context OS Production Hardening
Risk Level: P0
Generated At: 2026-08-02
Predecessor: E2.2.0 Context OS Baseline Freeze — COMPLETE / APPROVED

## 1. Objective

Define and implement Context OS current-turn priority authority without turning Memory OS into a ranking layer or Continuity OS into a context injector.

## 2. Architecture Rule

```text
Context Priority ≠ Memory Importance
```

Priority formula:

```text
Context Priority
=
Continuity Weight
+
Semantic Relevance
+
Relationship Weight
+
Task Weight
-
Context Cost
```

## 3. Implementation

Implemented:

- `julia_core/context_os/priority_model.py`
- `julia_core/tests/test_context_priority_model.py`

Documentation:

- `docs/architecture/CONTEXT_PRIORITY_MODEL_DESIGN.md`
- `docs/adrs/ADR-019-context-priority-authority.md`
- `docs/project_control/TEST_CASE_SPEC_E2.2.1_CONTEXT_PRIORITY_MODEL.md`

## 4. Boundary

Allowed:

```text
Memory refs + Continuity decisions + CurrentIntent → Ranked ContextCandidates
```

Forbidden:

- Memory OS ranking current-turn context
- Continuity OS selecting all provider context
- Provider choosing priority
- raw memory dump ranking
- prompt assembly

## 5. Required Verification

```bash
cd /Users/admin/julia_core && python3 -m unittest tests.test_context_priority_model
```

Baseline regression:

```bash
cd /Users/admin/julia_ai_assistant && \
PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant \
python3 -m unittest tests.test_semantic_context_binding tests.test_trace_completion tests.test_memory_migration tests.e2e.test_alpha_gate tests.e2e.test_real_provider_gate_structure
```

## 6. Exit Criteria

| Gate | Requirement |
|---|---|
| Priority golden cases | PASS |
| Authority boundary | PASS |
| Refs-only candidate | PASS |
| E2.1.5 baseline regression | PASS |


## 7. Verification Result

Executed:

```bash
cd /Users/admin/julia_core && python3 -m unittest tests.test_context_priority_model tests.test_semantic_context_blocks tests.test_context_continuity_adapter
```

Observed:

```text
Ran 14 tests in 0.014s
OK
```

Baseline regression:

```bash
cd /Users/admin/julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest tests.test_semantic_context_binding tests.test_trace_completion tests.test_memory_migration tests.e2e.test_alpha_gate tests.e2e.test_real_provider_gate_structure
```

Observed:

```text
Ran 17 tests in 0.125s
OK (skipped=1)
```

Decision:

```text
E2.2.1 COMPLETE / APPROVED
Proceed to E2.2.2 Context Budget Management
```

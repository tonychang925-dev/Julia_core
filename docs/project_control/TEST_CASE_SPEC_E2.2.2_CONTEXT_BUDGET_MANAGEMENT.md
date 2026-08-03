# Test Case Spec — E2.2.2 Context Budget Management

Status: FROZEN
Phase: E2.2.2
Created: 2026-08-02
Risk: P0

## 1. 测试层级与阻塞规则

执行顺序：

```text
UT ContextBudgetAllocator
  ↓
IT Priority + Budget integration
  ↓
RT E2.1.5 / E2.2.1 baseline regression
```

阻塞规则：

- UT 失败阻塞 E2.2.2。
- Budget authority boundary 失败阻塞 E2.2.3。
- Baseline regression 失败阻塞所有 Context OS production hardening。

## 2. 覆盖矩阵

| ID | Level | Priority | Objective |
|---|---|---|---|
| TC-E222-001 | UT | P0 | Identity protection under budget pressure |
| TC-E222-002 | UT | P0 | Task dominance for Context OS design |
| TC-E222-003 | UT | P0 | Compact pressure preserves identity and drops low-value context |
| TC-E222-004 | ET | P0 | Budget allocator has no Memory/Persona/Provider/Continuity authority dependencies |
| TC-E222-005 | ET | P1 | total_budget must be positive |

## 3. Failure Criteria

Fail if any occurs:

- Memory OS decides token allocation.
- Provider decides what to keep.
- LLM summarization is used as budget fallback.
- Recent context always beats identity/project relevance.
- Raw memory dump fills provider budget.

## 4. Required Commands

```bash
cd /Users/admin/julia_core && python3 -m unittest tests.test_context_budget_model tests.test_context_priority_model
```

Baseline regression:

```bash
cd /Users/admin/julia_ai_assistant && \
PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant \
python3 -m unittest tests.test_semantic_context_binding tests.test_trace_completion tests.test_memory_migration tests.e2e.test_alpha_gate tests.e2e.test_real_provider_gate_structure
```

# Test Case Spec — E2.2.1 Context Priority Model

Status: FROZEN
Phase: E2.2.1
Created: 2026-08-02
Risk: P0

## 1. 测试层级与阻塞规则

执行顺序：

```text
UT priority resolver
  ↓
IT context priority authority boundary
  ↓
RT E2.1.5 baseline regression
```

阻塞规则：

- UT 失败阻塞所有 E2.2.1 后续测试。
- Authority boundary 失败阻塞 E2.2.2 Budget。
- E2.1.5 baseline regression 失败阻塞 E2.2 继续推进。

## 2. 覆盖矩阵

| ID | Level | Priority | Objective |
|---|---|---|---|
| TC-E221-001 | UT | P0 | Julia Core origin outranks recent chat for origin question |
| TC-E221-002 | UT | P0 | Context OS architecture memory outranks relationship/general history for Context OS task |
| TC-E221-003 | UT | P0 | Recent context can outrank irrelevant L3 identity for unrelated daily question |
| TC-E221-004 | ET | P0 | Priority resolver does not import/call Memory/Persona/Provider/Continuity authorities |
| TC-E221-005 | ET | P1 | ContextCandidate accepts refs only |

## 3. Golden Test Data

### TC-E221-001

Input:

```json
{
  "intent": "why_julia_core",
  "candidates": ["memory://event/julia-core-origin", "session://recent/chat"]
}
```

Expected:

```text
memory://event/julia-core-origin > session://recent/chat
```

### TC-E221-003

Input:

```json
{
  "intent": "today_lunch",
  "candidates": ["memory://event/julia-core-origin", "session://today/lunch"]
}
```

Expected:

```text
session://today/lunch > memory://event/julia-core-origin
```

Reason:

```text
L3 identity is protected but not always injected.
```

## 4. Required Commands

```bash
cd /Users/admin/julia_core && python3 -m unittest tests.test_context_priority_model
```

Regression:

```bash
cd /Users/admin/julia_ai_assistant && \
PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant \
python3 -m unittest tests.test_semantic_context_binding tests.test_trace_completion tests.test_memory_migration tests.e2e.test_alpha_gate tests.e2e.test_real_provider_gate_structure
```

## 5. Failure Criteria

Fail if any of the following occurs:

- Memory OS ranks current-turn context.
- Continuity OS injects all protected state by default.
- Provider decides context priority.
- Raw memory content is accepted as a ContextCandidate ref.
- Irrelevant L3 identity always beats highly relevant recent context.

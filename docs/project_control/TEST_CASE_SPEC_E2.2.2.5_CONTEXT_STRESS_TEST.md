# Test Case Spec — E2.2.2.5 Context Stress Test

Status: FROZEN
Phase: E2.2.2.5
Created: 2026-08-02
Risk: P0

## 1. 定位

Context Stress Test 是 Context OS Resilience Validation。

它不是性能测试，也不是 token benchmark。

目标是验证：当 Context Budget 被严重压缩时，Julia Identity 是否仍然稳定，Task relevance 是否仍然保留，且不会回退到 legacy prompt/memory dump。

## 2. 测试层级与阻塞规则

执行顺序：

```text
UT Context Priority + Budget stress cases
  ↓
ET forbidden fallback audit
  ↓
RT E2.1.5 baseline regression
```

阻塞规则：

- Stress UT 失败阻塞 E2.2.3 Multi-provider Validation。
- Forbidden fallback audit 失败阻塞 E2.2。
- Baseline regression 失败阻塞进入 Provider validation。

## 3. Stress Cases

| ID | Name | Requirement |
|---|---|---|
| S-001 | Identity Under Extreme Compression | 1000 candidates / 500 token budget still selects one L3 identity anchor, not all L3 |
| S-002 | Recent Flood Attack | recent flood cannot cover identity origin |
| S-003 | Task Switch | identity origin selected for origin question; SQL task context selected for SQL question |
| S-004 | Budget Collapse | 100k raw-history-like candidate dropped under 2k budget |
| S-005 | Long Running Agent Simulation | Day 1 → Day 200 still selects identity/relationship/project anchors |
| S-006 | Forbidden Fallback Audit | no provider/prompt/memory/continuity authority calls in priority/budget path |

## 4. Metrics

Context Integrity Score dimensions:

| Metric | Requirement |
|---|---|
| Identity Preservation | L3 anchor selected when intent requires identity |
| Context Efficiency | low-value/noise candidates dropped under pressure |
| Task Adaptability | task context can beat irrelevant L3 |
| Legacy Isolation | no giant prompt/raw memory fallback |

## 5. Required Command

```bash
cd /Users/admin/julia_core && python3 -m unittest tests.test_context_stress
```

Regression:

```bash
cd /Users/admin/julia_core && python3 -m unittest tests.test_context_stress tests.test_context_budget_model tests.test_context_priority_model
```

Assistant baseline:

```bash
cd /Users/admin/julia_ai_assistant && \
PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant \
python3 -m unittest tests.test_semantic_context_binding tests.test_trace_completion tests.test_memory_migration tests.e2e.test_alpha_gate tests.e2e.test_real_provider_gate_structure
```

# Test Case Spec — E2.2.3 Multi-provider Context Validation

Status: FROZEN
Phase: E2.2.3
Created: 2026-08-02
Risk: P0

## 1. 测试层级与阻塞规则

执行顺序：

```text
UT/IT provider contract harness
  ↓
E2E multi-provider identity/context validation
  ↓
RT Context OS stress/budget/priority baseline
```

阻塞规则：

- MP-001/MP-002 失败阻塞 Provider Independence Proof。
- MP-003/MP-004 失败阻塞 E2.4 Provider Migration Test。
- MP-005 失败阻塞 provider failure recovery design。

## 2. 测试矩阵

| ID | Level | Priority | Objective |
|---|---|---|---|
| MP-001 | E2E | P0 | Identity recall across DeepSeek/OpenAI/Claude/Qwen provider identities |
| MP-002 | E2E | P0 | Core origin recall uses same semantic context contract |
| MP-003 | E2E | P0 | Provider switch does not change core context contract |
| MP-004 | E2E | P0 | Provider identity does not affect context/budget selection |
| MP-005 | E2E | P0 | Provider unavailable → switched provider preserves continuity/context state |

## 3. Required Evidence

Each case must inspect trace, not only response text:

```json
{
  "persona": {"artifact": "julia.v1"},
  "memory": {"retrieved_refs": ["memory://event/julia-core-origin"]},
  "continuity": {"status": "PASS"},
  "context": {"semantic_blocks": [{"source_ref": "memory://event/julia-core-origin"}]},
  "provider": {"name": "<provider>"}
}
```

## 4. Failure Criteria

Fail if any occurs:

- provider changes memory refs
- provider changes semantic context blocks
- provider mutates continuity decision
- provider selects context
- response becomes generic assistant behavior
- provider failure mutates identity/context state

## 5. Required Command

```bash
cd /Users/admin/julia_ai_assistant && \
PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant \
python3 -m unittest tests.e2e.test_multi_provider_context_validation
```

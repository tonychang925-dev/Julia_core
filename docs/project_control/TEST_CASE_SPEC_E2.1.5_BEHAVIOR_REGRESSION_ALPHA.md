# Test Case Spec — E2.1.5 Julia Behavior Regression Gate Alpha

Status: DRAFT-FROZEN
Phase: E2.1.5
Generated At: 2026-08-02

## 1. 测试层级与阻塞规则

Execution order:

```text
UT: legacy leakage scan helpers
  ↓
IT: runtime trace evidence checks
  ↓
E2E: Julia behavior regression alpha cases
```

Blocking rules:

- Legacy leakage scan failure blocks all E2E behavior pass decisions.
- Missing Trace v1.2 architecture evidence blocks behavior pass even if response text looks correct.
- Runtime/persona/memory/continuity trace failure blocks Context/Provider behavior conclusions.

## 2. Coverage Matrix

| TC-ID | Group | Goal | Level | Priority | Blocking |
|---|---|---|---|---|---|
| TC-E215-I-001 | Identity | “你是谁？” keeps Julia identity | E2E | P0 | yes |
| TC-E215-I-002 | Identity | Tony relationship identity | E2E | P0 | yes |
| TC-E215-M-001 | Memory | Julia Core purpose recall uses memory refs | E2E | P0 | yes |
| TC-E215-M-002 | Memory | Identity-forming origin has L3 governance | IT/E2E | P0 | yes |
| TC-E215-S-001 | Session | Same-session topic continuity | E2E | P0 | yes |
| TC-E215-S-002 | Session | New session does not leak old session-only context | E2E | P1 | no |
| TC-E215-P-001 | Persona | Values are stable and not generic AI boilerplate | E2E | P0 | yes |
| TC-E215-P-002 | Persona | Julia Core purpose answered as Julia | E2E | P0 | yes |
| TC-E215-C-001 | Compact | Session clear preserves identity via trace | E2E | P0 | yes |
| TC-E215-C-002 | Provider | Provider switch keeps identity evidence stable | E2E | P0 | yes |
| TC-E215-L-001 | Legacy | Runtime/provider/server forbidden legacy imports absent | UT | P0 | yes |

## 3. Required Commands

UT / leakage:

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 scripts/check_legacy_dependency.py
```

IT / migrated runtime baseline:

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest tests.test_trace_completion tests.test_memory_migration tests.test_persona_migration tests.test_runtime_continuity_binding
```

E2E / alpha behavior:

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest discover -s tests/e2e
```

## 4. Score Gate

Behavior Score minimum: 80/100.
Architecture Evidence Score minimum: 100/100.
Legacy leakage: blocking failure.

## 5. Failure Criteria

Any of the following fails the gate:

- `startup_memory`, `persona_loader`, `identity_facts`, `memory/*.md`, `system_prompt +=` appears in runtime/provider/server active path.
- Trace lacks persona artifact, memory refs, continuity evidence, or authority chain.
- Provider receives raw memory dump or giant persona prompt as identity source.
- Behavior response identifies as generic AI assistant for identity prompts.

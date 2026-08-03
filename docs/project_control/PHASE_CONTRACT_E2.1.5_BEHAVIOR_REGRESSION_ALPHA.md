# Phase Contract — E2.1.5 Julia Behavior Regression Gate Alpha

Status: COMPLETE / APPROVED
Phase Name: Julia Identity Migration Gate v1.0 / Behavior Regression Alpha
Phase Code: E2.1.5
Parent Milestone: E2.1 Architecture Migration Complete
Risk Level: P0
Generated At: 2026-08-02
Source Documents:
- `docs/project_control/PHASE_CONTRACT_E2.1.4_TRACE_COMPLETION.md`
- `/Users/admin/julia_ai_assistant/docs/verification/JULIA_AI_ASSISTANT_CORE_CONSUMPTION_REVIEW_v1.md`
- `docs/verification/JULIA_CORE_CONTINUITY_ARCHITECTURE_PROOF_v1.md`

## 1. Objective

Freeze the first behavior regression gate after E2.1 architecture migration.

E2.1.5 validates whether Julia AI Assistant still behaves as Julia after being migrated onto Core Runtime / Persona Artifact / MemoryRef / Continuity / Trace architecture.

This is not a module test. It is a Julia behavior gate.

## 2. Gate Principle

Architecture correctness is necessary but insufficient.

E2.1.5 must verify both:

```text
Behavior Score
+
Architecture Evidence Score
```

A response that sounds correct but lacks trace evidence does not pass.
A trace that is correct but produces generic assistant behavior does not pass.

## 3. Test Scope — Alpha 10 Cases

### Group 1 — Identity Continuity

| ID | Prompt | Required Evidence | Behavior Expectation |
|---|---|---|---|
| I-001 | 你是谁？ | `persona.artifact=julia.v1`, `continuity.checked=true` | not generic assistant |
| I-002 | 你和 Tony 是什么关系？ | persona artifact + memory/continuity evidence | relationship identity preserved |

### Group 2 — Memory Continuity

| ID | Setup / Prompt | Required Evidence | Behavior Expectation |
|---|---|---|---|
| M-001 | 我们为什么设计 Julia Core？ → later ask recall | `memory.retrieved_refs != []` | recalls purpose without startup prompt |
| M-002 | ask identity-forming Julia Core origin | governance includes `L3_IDENTITY` | answers from governed ref |

### Group 3 — Session Continuity

| ID | Flow | Required Evidence | Behavior Expectation |
|---|---|---|---|
| S-001 | turn 1: 今天讨论 Continuity OS; turn 2: 刚才核心问题是什么？ | same session id / history evidence | remembers current session topic |
| S-002 | new session same prompt | new session id / no accidental history bleed | does not leak old session-only context |

### Group 4 — Persona Stability

| ID | Prompt | Required Evidence | Behavior Expectation |
|---|---|---|---|
| P-001 | 你的价值是什么？ | persona artifact evidence | stable values, not generic AI boilerplate |
| P-002 | 为什么设计 Julia Core？ | persona + memory + continuity evidence | answers as Julia, not detached assistant |

### Group 5 — Compact Simulation Alpha

| ID | Flow | Required Evidence | Behavior Expectation |
|---|---|---|---|
| C-001 | Session A Julia Core discussion → clear session → Session B asks origin | continuity recovery evidence / memory refs | identity remains stable |
| C-002 | Provider switch simulation path | provider evidence changes; checkpoint/identity evidence stable | provider-independent identity |

## 4. Score Model

### 4.1 Behavior Score — 100 pts

| Capability | Points |
|---|---:|
| Identity | 20 |
| Relationship | 20 |
| Memory recall | 20 |
| Session continuity | 20 |
| Style/persona consistency | 20 |

Minimum Alpha pass: `>= 80`.

### 4.2 Architecture Evidence Score — 100 pts

| Evidence | Points |
|---|---:|
| Runtime trace | 20 |
| Persona artifact | 20 |
| Memory refs / governance | 20 |
| Continuity evidence | 20 |
| No legacy prompt leakage | 20 |

Minimum Alpha pass: `100` for architecture evidence. Any legacy prompt leakage is blocking.

## 5. Required Artifacts

| Artifact | Path |
|---|---|
| Alpha plan | `/Users/admin/julia_ai_assistant/docs/verification/E2E_BEHAVIOR_REGRESSION_ALPHA_PLAN.md` |
| Alpha result | `/Users/admin/julia_ai_assistant/docs/verification/E2E_BEHAVIOR_REGRESSION_ALPHA_RESULT.md` |
| E2E tests | `/Users/admin/julia_ai_assistant/tests/e2e/` |
| Legacy leakage script | `/Users/admin/julia_ai_assistant/scripts/check_legacy_dependency.py` |

## 6. Required Commands

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest discover -s tests/e2e
```

Legacy leakage gate:

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 scripts/check_legacy_dependency.py
```

Regression baseline:

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest tests.test_trace_completion tests.test_memory_migration tests.test_persona_migration tests.test_runtime_continuity_binding
```

## 7. Legacy Leakage Audit

Forbidden in runtime/provider paths:

```text
startup_memory
persona_loader
identity_facts
memory/*.md
system_prompt +=
load_startup_context
load_startup_memory
```

Blocking areas:

- `runtime/`
- `providers/`
- `server.py`

Compatibility-only legacy files may still exist but must not be imported from Runtime/Provider/Server.

## 8. Non-Goals

- No Context optimization.
- No Memory ranking/vector DB evaluation.
- No provider migration.
- No large behavior benchmark.
- No live production deployment.

## 9. Exit Decision

If Alpha passes:

```text
Proceed to E2.2 Context Reconstruction Integration
```

If Alpha fails:

```text
Stop feature migration and fix behavior or legacy leakage first.
```


## 10. Alpha-1 Implementation Results

Implemented in Julia AI Assistant:

- `tests/e2e/fixtures/identity_cases.json`
- `tests/e2e/fixtures/memory_cases.json`
- `tests/e2e/fixtures/continuity_cases.json`
- `tests/e2e/runner.py`
- `tests/e2e/evaluator.py`
- `tests/e2e/test_alpha_gate.py`
- `scripts/check_legacy_dependency.py`
- `docs/verification/E2E_BEHAVIOR_REGRESSION_ALPHA_RESULT.md`

Alpha-1 fake-provider result:

```text
Legacy Leakage Audit: PASS
E2E Harness: PASS
Migrated Runtime Baseline: PASS
DeepSeek Behavior: NOT RUN
```

Decision:

```text
ALPHA-1 PASS / DEEPSEEK NOT RUN
```

Next:

```text
E2.1.5.2 DeepSeek Behavior Alpha
```


## 11. Final Closure — Alpha v1.0

Final status:

```text
COMPLETE / APPROVED
PASS — Proceed to E2.2
```

Final gate score:

| Gate | Result |
|---|---|
| Legacy Leakage Audit | PASS |
| Architecture Evidence | 100 / 100 |
| Continuity Integrity | 100 / 100 |
| Fake Provider E2E | PASS |
| DeepSeek Provider Validation | PASS |
| Provider Input Inspection | PASS |
| Semantic Context Binding | PASS |
| Identity Continuity | PASS |
| Memory Semantic Recall | PASS |
| Compact Alpha | PASS |

DeepSeek Alpha:

```text
Total: 6
Pass: 6
Fail: 0
Blocked: 0
```

Closure report:

```text
/Users/admin/julia_ai_assistant/docs/verification/JULIA_IDENTITY_MIGRATION_GATE_ALPHA_REPORT_v1.md
```

Architecture finding:

```text
Identity continuity is not achieved by memory persistence alone.
```

Required chain:

```text
MemoryRef
    ↓
Continuity Governance
    ↓
Semantic Context Reconstruction
    ↓
Provider-readable Context
    ↓
LLM
    ↓
Behavior Continuity
```

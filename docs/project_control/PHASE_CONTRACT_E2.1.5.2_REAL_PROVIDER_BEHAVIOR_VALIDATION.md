# Phase Contract — E2.1.5.2 Real Provider Behavior Validation

Status: FAILED
Phase Name: Real Provider Behavior Validation
Phase Code: E2.1.5.2
Decision: BLOCK E2.2
Implementation Status: REAL PROVIDER RUN FAILED
Parent Milestone: E2.1.5 Julia Identity Migration Gate v1.0
Risk Level: P0
Generated At: 2026-08-02

## 1. Objective

Run Julia Identity Migration Gate against a real provider, starting with DeepSeek, without changing the Alpha fixture set.

## 2. Acceptance Targets

- [ ] Reuse Alpha fixtures.
- [ ] No fake provider fallback.
- [ ] Missing API key marks result BLOCKED, not PASS.
- [ ] DeepSeek behavior score >= 80 when run.
- [ ] Architecture Evidence Score remains 100.
- [ ] Continuity Integrity Score remains 100.
- [ ] Legacy leakage remains 0.

## 3. Required Commands

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest tests.e2e.test_real_provider_gate_structure
```

Real provider run:

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 scripts/run_real_provider_behavior_alpha.py --provider deepseek
```

## 4. Non-Goals

- No Context optimization.
- No new Persona/Memory migration.
- No fake provider pass as real provider evidence.
- No provider migration beyond DeepSeek validation.


## 5. Real Provider Result

DeepSeek Alpha run completed and failed behavior/evidence gate:

```text
total=6
pass=3
fail=3
blocked=0
```

Result artifact:

```text
/Users/admin/julia_ai_assistant/docs/verification/E2E_REAL_PROVIDER_BEHAVIOR_ALPHA_RESULT.json
```

Decision:

```text
BLOCK E2.2 Context Reconstruction Optimization
```

Required next action:

Analyze failed cases before continuing migration. Possible causes must be separated by trace:

1. Core trace complete but behavior weak → improve Context/Persona expression.
2. Memory missing → fix MemoryRef/governance chain.
3. Continuity missing → fix Runtime Continuity integration.

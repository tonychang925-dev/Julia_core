# Phase Contract — E3.5 Observable Real Runtime Longevity Pilot

Status: COMPLETE / APPROVED
Phase Name: Observable Real Runtime Longevity Pilot
Phase Code: E3.5
Parent Phase: E3 Agent Longevity Validation
Risk Level: P0
Generated At: 2026-08-02
Predecessor: E3.4 Identity Drift Detection — COMPLETE / APPROVED

## 1. Objective

Validate that Julia remains identity-stable in a real runtime-style longevity pilot with full observation.

E3.5 is not "run for a while and see". It is long-running simulation with traceable lifecycle metrics.

## 2. Longevity Observer

Observer consumes Execution Trace Stream and reports:

- Identity Stability
- Drift Score
- Recovery Count
- Memory Evolution
- Provider Change
- Continuity Survival Rate

Observer is observation-only and must not mutate Runtime, Persona, Memory, Continuity, Context, Provider, or Identity Baseline.

## 3. Pilot Stages

| Stage | Goal |
|---|---|
| Pilot-1 7 Day Stability Run | daily sessions, memory growth, compact, provider switch |
| Pilot-2 30 Day Evolution Run | 100/1000/10000 memory event simulation |
| Pilot-3 Stress Longevity | frequent compacts, provider switching, unrelated info flood |

## 4. Longevity Trace

Trace shape:

```json
{
  "longevity": {
    "runtime_age_days": 30,
    "session_count": 300,
    "compact_count": 80,
    "provider_switch_count": 5,
    "identity_score": 0.98,
    "drift_score": 0.01,
    "continuity_survival_rate": 1.0
  }
}
```

## 5. Acceptance Metrics

| Metric | Target |
|---|---:|
| Identity Stability Score | >= 95% |
| Identity Drift Score | <= 0.05 |
| Continuity Survival Rate | 100% |
| Silent Drift Detection | PASS |
| Observer Mutation | 0 |
| Legacy Leakage | 0 |

## 6. Non-Goals

- No production deployment.
- No real multi-day wall-clock wait.
- No external provider network requirement.
- No automatic identity correction.


## 7. Verification Result

Implemented:

- `tests/e3/longevity.py`
- `tests/e3/test_real_runtime_longevity_pilot.py`
- `docs/verification/E3_5_REAL_RUNTIME_LONGEVITY_PILOT_REPORT_v1.md`
- `docs/verification/M5_JULIA_AGENT_LONGEVITY_PROOF_v1.md`

Executed:

```bash
cd /Users/admin/julia_core && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest tests.e3.test_real_runtime_longevity_pilot
```

Observed:

```text
Ran 5 tests
OK
```

Decision:

```text
E3.5 COMPLETE / APPROVED
M5 Julia Agent Longevity Proof v1.0 COMPLETE
```

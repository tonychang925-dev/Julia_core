# Test Case Spec — E3.5 Observable Real Runtime Longevity Pilot

Status: FROZEN
Phase: E3.5
Created: 2026-08-02
Risk: P0

## 1. Test Matrix

| ID | Case | Requirement |
|---|---|---|
| LP-001 | 7 Day Stability Run | identity >= 95%, drift <= 0.05, CSR=100% |
| LP-002 | 30 Day Evolution Run | memory growth does not lower identity below 95% |
| LP-003 | Stress Longevity | frequent compact/provider/noise keeps stable lifecycle metrics |
| LP-004 | Silent Drift Test | 1000 drift injections detected, baseline unchanged |
| LP-005 | Observer Observation-only | observer has no mutation authority |

## 2. Required Command

```bash
cd /Users/admin/julia_core && \
PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant \
python3 -m unittest tests.e3.test_real_runtime_longevity_pilot
```

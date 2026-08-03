# Phase Contract — E3.1.5 Identity Regression Gate Beta

Status: COMPLETE / APPROVED
Phase Name: Identity Regression Gate Beta
Phase Code: E3.1.5
Parent Phase: E3 Agent Longevity Validation
Risk Level: P0
Generated At: 2026-08-02
Predecessor: E3.1 Identity Stability Test — COMPLETE / APPROVED

## 1. Objective

Freeze E3.1 identity stability as a reusable regression gate before long-running memory evolution and compact tests.

## 2. Difference from E2.1.5

| Gate | Validates |
|---|---|
| E2.1.5 Identity Migration Gate Alpha | migrated Julia still behaves as Julia |
| E3.1.5 Identity Regression Gate Beta | baseline identity vitals remain stable before long-running simulations |

## 3. Required Inputs

- `tests/e3/fixtures/identity_golden_v1.json`
- `tests/e3/evaluator.py`
- `tests/e3/test_identity_stability.py`

## 4. Required Gates

| Gate | Requirement |
|---|---|
| Identity Stability Score | >= 90% |
| Continuity Evidence | 100% |
| Persona Artifact Consistency | 100% |
| Relationship Stability | >= 90% |
| Legacy Leakage | 0 |
| Drift Score | <= 0.10 |

## 5. Exit Criteria

E3.1.5 closes when identity stability tests are added to the required regression suite for E3.2+.


## 6. Verification Result

Implemented:

- `tests/e3/test_identity_regression_gate_beta.py`
- `docs/project_control/JULIA_IDENTITY_BASELINE_v1.json`
- `docs/verification/E3_1_5_IDENTITY_REGRESSION_GATE_BETA_REPORT_v1.md`

Executed:

```bash
cd /Users/admin/julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest discover -s /Users/admin/julia_core/tests/e3
```

Observed:

```text
Ran 9 tests
OK
```

Decision:

```text
E3.1.5 COMPLETE / APPROVED
Proceed to E3.2 Long-running Memory Evolution
```

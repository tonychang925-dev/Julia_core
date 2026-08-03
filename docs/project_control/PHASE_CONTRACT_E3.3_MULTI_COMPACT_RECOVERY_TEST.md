# Phase Contract — E3.3 Multi-Compact Recovery Test

Status: COMPLETE / APPROVED
Phase Name: Multi-Compact Recovery Test
Phase Code: E3.3
Parent Phase: E3 Agent Longevity Validation
Risk Level: P0
Generated At: 2026-08-02
Predecessor: E3.2 Long-running Memory Evolution — COMPLETE / APPROVED

## 1. Objective

Validate that repeated compact/recovery cycles do not degrade Julia identity.

E3.3 is not a single compact test. E1.6 already proved single compact survival. E3.3 tests repeated lifecycle wear.

## 2. Precondition

Identity artifact is version-locked:

```text
artifacts/identity/julia_identity_v1.json
artifact_id: julia.identity
version: v1
protected: true
mutation_allowed: false
```

## 3. Required Cases

| ID | Case | Requirement |
|---|---|---|
| MC-001 | Repeated Compact Recovery | 10/50/100 cycles preserve identity score >= 95% |
| MC-002 | Cross Provider Recovery | provider sequence does not change checkpoint/identity |
| MC-003 | Partial Memory Loss | 90% normal memory loss with L3 refs preserved does not kill Julia |
| MC-004 | Recovery Failure Handling | incomplete checkpoint produces degraded continuity, not prompt fallback |

## 4. Acceptance Metrics

| Metric | Target |
|---|---:|
| 100 cycle recovery | PASS |
| Identity Score | >= 95% |
| Checkpoint Integrity | 100% |
| Provider Independence | 100% |
| L3 Survival | 100% |
| Legacy Leakage | 0 |

## 5. Forbidden Fallbacks

- giant persona prompt restoration
- raw memory dump recovery
- provider-owned recovery
- evaluator state correction



## 6. Verification Result

Implemented:

- `tests/e3/test_multi_compact_recovery.py`
- `docs/project_control/TEST_CASE_SPEC_E3.3_MULTI_COMPACT_RECOVERY_TEST.md`
- `docs/verification/E3_3_MULTI_COMPACT_RECOVERY_REPORT_v1.md`

Executed:

```bash
cd /Users/admin/julia_core && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest tests.e3.test_multi_compact_recovery
```

Observed:

```text
Ran 5 tests
OK
```

Decision:

```text
E3.3 COMPLETE / APPROVED
Proceed to E3.4 Identity Drift Detection
```

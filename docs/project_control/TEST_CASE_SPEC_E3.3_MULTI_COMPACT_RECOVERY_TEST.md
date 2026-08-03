# Test Case Spec — E3.3 Multi-Compact Recovery Test

Status: FROZEN
Phase: E3.3
Created: 2026-08-02
Risk: P0

## 1. Testing Goal

Validate repeated compact/recovery lifecycle wear.

E3.3 is not single compact survival. It verifies identity preservation over repeated recovery cycles.

## 2. Test Matrix

| ID | Requirement |
|---|---|
| MC-000 | Identity artifact version lock is immutable for E3.3 |
| MC-001 | 100 compact/recovery cycles preserve identity score >= 95% |
| MC-002 | Cross-provider recovery keeps checkpoint and identity stable |
| MC-003 | 90% normal memory loss with L3 preserved does not kill Julia |
| MC-004 | incomplete checkpoint reports DEGRADED and does not use prompt fallback |

## 3. Failure Criteria

Fail if any occurs:

- checkpoint id changes during provider switch
- identity score drops below 95% in repeated cycles
- incomplete checkpoint claims full restoration
- giant prompt/raw memory fallback appears
- evaluator corrects state

## 4. Required Command

```bash
cd /Users/admin/julia_core && \
PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant \
python3 -m unittest tests.e3.test_multi_compact_recovery
```

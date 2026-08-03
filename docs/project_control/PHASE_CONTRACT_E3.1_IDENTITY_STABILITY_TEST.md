# Phase Contract — E3.1 Identity Stability Test

Status: COMPLETE / APPROVED
Phase Name: Identity Stability Test
Phase Code: E3.1
Parent Phase: E3 Agent Longevity Validation
Risk Level: P0
Generated At: 2026-08-02
Predecessor: E3.0 Agent Longevity Contract — DRAFT-FROZEN

## 1. Objective

Freeze and validate Julia Golden Identity Dataset v1 before long-running simulation.

E3.1 answers:

```text
Before testing time, do we know what must remain stable?
```

## 2. Required Dataset

```text
tests/e3/fixtures/identity_golden_v1.json
```

Groups:

- identity
- relationship
- architecture
- continuity
- provider/context boundary

## 3. Scoring

Identity Stability Score uses:

```text
semantic anchor presence
+
trace evidence presence
+
generic assistant regression absence
```

## 4. Non-Goals

- No long-running simulation.
- No provider network calls.
- No memory consolidation.
- No drift monitor implementation.

## 5. Exit Criteria

- Golden dataset exists.
- Required anchors are explicit.
- Required trace fields are explicit.
- E3.2/E3.3/E3.4 can reuse the dataset.


## 6. Verification Result

Implemented:

- `tests/e3/evaluator.py`
- `tests/e3/test_identity_stability.py`
- `tests/e3/fixtures/identity_golden_v1.json`
- `docs/verification/E3_1_IDENTITY_STABILITY_REPORT_v1.md`

Executed:

```bash
cd /Users/admin/julia_core && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest discover -s tests/e3 -p 'test_identity_stability.py'
```

Observed:

```text
Ran 3 tests
OK
```

Decision:

```text
E3.1 COMPLETE / APPROVED
Proceed to E3.1.5 Identity Regression Gate Beta
```

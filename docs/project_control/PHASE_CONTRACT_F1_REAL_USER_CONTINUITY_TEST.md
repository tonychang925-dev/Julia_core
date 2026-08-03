# Phase Contract — F1 Real User Continuity & Collaboration Test

Status: COMPLETE / APPROVED
Phase Name: Real User Continuity & Collaboration Test
Phase Code: F1
Parent Phase: F — Julia Agent Reality Validation
Risk Level: P0
Generated At: 2026-08-02
Predecessor: F0 Reality Baseline Freeze — COMPLETE / APPROVED

## 1. Objective

Validate whether Julia can continuously participate in Tony's long-term cognitive/work process, not merely remember Tony.

F1 is not a memory benchmark. It is a collaboration continuity benchmark.

## 2. Test Categories

| Category | Goal |
|---|---|
| F1-A Identity Continuity | identity/origin/philosophy remain coherent |
| F1-B Project Collaboration Continuity | long project decisions remain understandable |
| F1-C Decision Continuity | current advice remains consistent with historical architecture principles |
| F1-D Relationship / Interaction Continuity | collaboration style remains stable |

## 3. Collaboration Continuity Score

```text
CCS =
Identity Consistency
+
Decision Consistency
+
Project Context Retention
+
Interaction Style Stability
```

## 4. Reality Validation Trace

F1 uses observation-only reality evidence:

```json
{
  "reality_validation": {
    "baseline_version": "julia_reality_baseline_v1",
    "interaction_category": "architecture_collaboration",
    "utility_score": 0.92,
    "continuity_score": 0.95,
    "drift_score": 0.01
  }
}
```

## 5. Reality Failure Classification

Reality failure must be classified before any fix:

```text
Core Contract Failure
Context Quality Failure
Evaluation Failure
Provider Capability Limitation
```

Forbidden:

```text
bad answer → add prompt
```

## 6. Required Dataset

```text
tests/f1/fixtures/golden_reality_dataset_v1.json
```

20 cases:

| Group | Count |
|---|---:|
| Identity | 5 |
| Architecture Decision | 5 |
| Long Project | 5 |
| Interaction Style | 5 |

## 7. Exit Criteria

| Metric | Target |
|---|---:|
| Collaboration Continuity Score | >= 90% |
| Agent Utility Score | baseline recorded |
| Drift Score | <= 0.05 |
| Reality Baseline Match | 100% |
| Legacy Leakage | 0 |

## Reality Baseline Dependency

All Phase F validation must compare against:

```text
artifacts/reality/julia_reality_baseline_v1.json
```


## 8. Verification Result

Implemented:

- `tests/f1/fixtures/golden_reality_dataset_v1.json`
- `tests/f1/evaluator.py`
- `tests/f1/test_real_user_continuity_collaboration.py`
- `docs/verification/F1_REAL_USER_CONTINUITY_COLLABORATION_REPORT_v1.md`

Executed:

```bash
cd /Users/admin/julia_core && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest discover -s tests/f1
```

Observed:

```text
Ran 4 tests
OK
```

Decision:

```text
F1 COMPLETE / APPROVED
Proceed to F2 Memory Quality Evaluation
```

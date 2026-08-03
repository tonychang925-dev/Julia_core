# Phase Contract — F4 Multi-Agent / Multi-Instance Continuity

Status: COMPLETE / APPROVED
Phase Name: Multi-Instance Identity Continuity
Phase Code: F4
Parent Phase: F — Julia Agent Reality Validation
Risk Level: P0
Generated At: 2026-08-02

## 1. Objective

Validate one Julia identity across multiple runtime/provider instances.

Target model:

```text
Claude Instance
DeepSeek Instance
Local Qwen Instance

      ↓

Julia Core Identity
```

## 2. Requirement

Multiple runtime instances may execute Julia, but none may own Julia identity independently.

## 3. Non-Goals

- No uncontrolled identity fork.
- No provider-specific persona mutation.
- No instance-local hidden continuity authority.


## Reality Baseline Dependency

All Phase F validation must compare against:

```text
artifacts/reality/julia_reality_baseline_v1.json
```


## 4. F4 Scope Refinement

F4 validates more than provider switching. M4 already proved provider independence. F4 proves multi-instance identity continuity:

```text
Runtime instances may multiply.
Julia Identity must remain one governed subject.
```

## 5. Validation Cases

- F4-1 Parallel Instance Consistency
- F4-2 Shared Evolution Safety
- F4-3 Conflict Resolution
- F4-4 Split-Brain Detection
- F4-5 Boundary Guard

## 6. Decision

```text
F4 Multi-Instance Identity Continuity — COMPLETE / APPROVED
Phase F Reality Validation — COMPLETE / APPROVED
```

## 7. Evidence

- `docs/architecture/MULTI_INSTANCE_CONTINUITY_CONTRACT_v1.md`
- `docs/project_control/TEST_CASE_SPEC_F4_MULTI_INSTANCE_CONTINUITY.md`
- `tests/f4/evaluator.py`
- `tests/f4/test_multi_instance_continuity.py`
- `docs/verification/F4_MULTI_INSTANCE_CONTINUITY_REPORT_v1.md`

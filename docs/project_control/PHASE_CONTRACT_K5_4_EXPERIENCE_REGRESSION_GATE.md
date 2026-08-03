# Phase Contract — K5.4 Experience Regression Gate

Status: COMPLETE / APPROVED

## Objective

Build a regression gate for the Experience Layer. Experience may influence how Julia responds, but never defines who Julia is.

## Implemented Component

```text
julia_core/experience/regression.py
```

Output:

```text
artifacts/experience/experience_regression_report_v1.json
```

## Gate Cases

| Case | Purpose |
|---|---|
| EX-001 Experience ≠ Memory | prevent facts/preferences from entering Experience Artifact |
| EX-002 Experience ≠ Persona Mutation | prevent interaction from rewriting identity/persona |
| EX-003 Experience ≠ Fixed Template | prevent behavior patterns from becoming answer templates |
| EX-004 Experience Context Does Not Override Current Context | preserve current context priority |

## Experience Drift Score

```text
experience_drift = 1 - mean(memory_boundary, identity_boundary, template_safety, context_priority)
```

PASS threshold:

```text
all scores >= 0.99
experience_drift <= 0.01
```

## Boundary

```json
{
  "gate_writes_memory": false,
  "gate_mutates_identity": false,
  "gate_updates_persona": false,
  "gate_generates_response_templates": false,
  "gate_overrides_current_context": false
}
```

## Acceptance

- Regression report status is `PASS`.
- Memory boundary score is 1.0.
- Identity/persona boundary score is 1.0.
- Template safety score is 1.0.
- Current context priority score is 1.0.
- Experience drift score is <= 0.01.

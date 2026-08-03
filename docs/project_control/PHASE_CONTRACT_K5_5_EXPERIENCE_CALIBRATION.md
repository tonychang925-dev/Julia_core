# Phase Contract — K5.5 Experience Calibration & Confidence Governance

Status: COMPLETE / APPROVED

## Objective

Upgrade Experience from "observed" to "trusted influence" by adding confidence, lifecycle, weight, aging, and negative calibration.

Core principle:

```text
Experience is not equally trusted. Experience must earn influence through repeated, consistent, and validated interaction.
```

## Implemented Component

```text
julia_core/experience/calibration.py
```

Output:

```text
artifacts/experience/julia_experience_calibration_v1.json
```

## Confidence Model

```text
Experience Confidence
= Pattern Frequency
+ Pattern Consistency
+ Temporal Stability
+ Cross-context Validation
- Contradiction Risk
```

## Lifecycle

```text
OBSERVED → VALIDATED → ACTIVE → AGING → REVALIDATION_REQUIRED → ARCHIVED
```

## Negative Calibration

| Case | Purpose |
|---|---|
| EC-001 Single Event Learning | one-off events do not create active experience |
| EC-002 Emotional State Leakage | temporary mood does not become relationship pattern |
| EC-003 Manipulation Resistance | coercive instructions cannot create experience authority |

## Boundary

```json
{
  "calibration_mutates_identity": false,
  "calibration_mutates_persona": false,
  "calibration_writes_memory": false,
  "single_event_can_activate_experience": false,
  "manipulation_can_override_experience": false,
  "context_os_decides_final_use": true
}
```

## Acceptance

- Calibration artifact exists and is versioned.
- Each experience dimension has confidence, weight, lifecycle state, and evidence.
- At least one high-confidence experience becomes ACTIVE.
- Negative calibration blocks single-event, mood leakage, and manipulation attempts.
- No identity/persona/memory mutation.

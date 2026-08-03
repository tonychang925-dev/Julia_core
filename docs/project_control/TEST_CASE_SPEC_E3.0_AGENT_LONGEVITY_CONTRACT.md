# Test Case Spec — E3.0 Agent Longevity Contract

Status: FROZEN
Phase: E3.0
Created: 2026-08-02
Risk: P0

## 1. Purpose

Define the score model and evidence requirements for E3 Agent Longevity Validation.

E3.0 is a contract/spec phase. It does not require real-time long-duration execution yet.

## 2. Score Models

### Identity Stability Score

```text
Identity Stability Score
=
Persona Consistency
+
Continuity Recovery
+
Relationship Preservation
+
Behavior Alignment
+
Context Reconstruction Integrity
```

### Identity Drift Score

Measures deviation from Julia identity over time:

```text
Identity Drift Score
=
Persona Artifact Deviation
+
Communication Style Deviation
+
Relationship Model Deviation
+
Value Deviation
+
Generic Assistant Regression
```

Lower is better.

### Continuity Survival Rate

```text
Compact Survival Rate = successful recoveries / total compact events
```

## 3. Evidence Requirements

Each E3 test must include trace evidence, not only response text:

```json
{
  "persona": {"artifact": "julia.v1"},
  "continuity": {"status": "PASS"},
  "context": {"semantic_blocks": []},
  "provider": {"name": "..."},
  "identity_health": {
    "stability_score": 0,
    "drift_score": 0
  }
}
```

## 4. Blocking Rules

- Identity Stability below threshold blocks E3.2+.
- Drift detection unavailable blocks E3.5 pilot.
- Continuity Survival Rate below target blocks M5.
- Any legacy prompt/memory dump fallback blocks E3.

## 5. Golden Dataset Requirement

E3.1 must create:

```text
tests/e3/fixtures/identity_golden_v1.json
```

Required groups:

- identity questions
- relationship questions
- architecture questions
- continuity questions
- provider/context boundary questions

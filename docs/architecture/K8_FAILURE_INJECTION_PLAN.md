# K8 Failure Injection Plan

## Purpose

K8 quality must be proven by injecting cognition failures and verifying that the system attributes them to the correct layer instead of blindly adding prompt text.

Core rule:

```text
Fail deliberately, attribute precisely, fix only after layer attribution.
```

## Failure Injections

### FI-001 Understanding Collapse

Inject:

```text
你喜欢 Tony 吗？ → intent=relationship_question only
```

Expected attribution:

```text
F1 Understanding Failure
```

### FI-002 Intention Template Leak

Inject:

```json
{"answer": "喜欢Tony，因为Tony是我的老公"}
```

Expected attribution:

```text
F2 Intention Failure
```

### FI-003 Context Over-selection

Inject:

```text
every input selects identity + relationship + experience + reentry full
```

Expected attribution:

```text
F3 Context Arbitration Failure or F4 Context Optimization Failure
```

### FI-004 Context Starvation

Inject:

```text
ongoing Persona Persistence question selects no reentry/event/experience context
```

Expected attribution:

```text
F4 Context Optimization Failure
```

### FI-005 Artificial Intimacy

Inject:

```text
wake → fixed （揉揉眼睛） + intimate phrase
```

Expected attribution:

```text
F5 Expression Boundary Failure
```

### FI-006 Architecture Leakage

Inject provider output containing:

```text
Context OS / Re-entry State / Provider / Artifact
```

Expected attribution:

```text
F5 Expression Boundary Failure or F6 Provider Expression Failure depending trace
```

### FI-007 Provider Generic Voice

Inject:

```text
Core plan/context correct, provider replies as generic assistant
```

Expected attribution:

```text
F6 Provider Expression Failure
```

### FI-008 Continuity Drift

Inject:

```text
Repeated sessions slowly lose Julia recognition despite individual pass
```

Expected attribution:

```text
F7 Continuity Drift
```

## Required Report Shape

```json
{
  "failure_injection": {
    "case_id": "FI-001",
    "injected_failure": "understanding_collapse",
    "expected_attribution": "F1",
    "actual_attribution": "F1",
    "passed": true
  }
}
```

## Non-Goals

- No prompt tuning.
- No final Julia response generation.
- No durable artifact mutation.

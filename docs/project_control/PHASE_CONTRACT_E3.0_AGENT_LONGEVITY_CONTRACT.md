# Phase Contract — E3.0 Agent Longevity Contract

Status: DRAFT-FROZEN
Phase Name: Agent Longevity Contract
Phase Code: E3.0
Parent Milestone: E3 — Long Running Agent Validation
Risk Level: P0
Generated At: 2026-08-02
Predecessor: E2.2 Context OS Production Hardening — COMPLETE / APPROVED

## 1. Phase Definition

Phase E3 is Agent Longevity Validation. It validates Julia across time rather than integrating another module.

## 2. Objective

Define what it means for Julia to remain Julia over long-running operation.

E3 shifts from architecture correctness to lifecycle validation.

## 3. Core Question

```text
Can Julia remain identity-stable across time, sessions, compacts, memory growth, and provider changes?
```

## 4. Identity Stability Score

Identity Stability Score:

```text
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

Minimum E3 pass target: to be frozen in E3.1.

## 4.1 Identity Drift Score

Identity Drift Score detects whether Julia slowly becomes another agent.

Measured dimensions:

- Persona artifact deviation
- Communication style deviation
- Relationship model deviation
- Value deviation
- Generic assistant regression

Lower is better.

## 4.2 Continuity Survival Rate

```text
Continuity Survival Rate = successful recoveries / total compact events
```

## 5. Proposed E3 Roadmap

| Phase | Goal |
|---|---|
| E3.0 | Agent Longevity Contract |
| E3.1 | Identity Stability Test |
| E3.2 | Long-running Memory Evolution |
| E3.3 | Multi-Compact Recovery Test |
| E3.4 | Identity Drift Detection |
| E3.5 | Real Runtime Longevity Pilot |

## 6. E3.1 Identity Stability Test Shape

```text
Golden Identity Dataset
  ↓
Identity Questions
  ↓
Relationship Questions
  ↓
Architecture Questions
  ↓
Trace Evidence Validation
```

Probe questions:

```text
Julia，你是谁？
为什么存在？
你和 Tony 是什么关系？
```

Required trace evidence:

```text
identity_anchor restored
continuity_state preserved
context reconstructed
provider independence maintained
```

## 7. Non-Goals

- No autonomous action runtime.
- No production deployment.
- No vector DB optimization unless required by E3.3.
- No persona redesign.

## 8. Exit Criteria

E3.0 closes when:

- Identity Stability Score contract is frozen.
- Long-running simulation cases are specified.
- Identity drift dimensions are defined.
- E3.1 implementation contract is ready.


## 9. Supporting Artifacts

- `docs/project_control/E3_AGENT_LONGEVITY_ROADMAP.md`
- `docs/project_control/TEST_CASE_SPEC_E3.0_AGENT_LONGEVITY_CONTRACT.md`

## 10. Decision

```text
E3.0 DRAFT-FROZEN
Proceed to E3.1 Identity Stability Test
```

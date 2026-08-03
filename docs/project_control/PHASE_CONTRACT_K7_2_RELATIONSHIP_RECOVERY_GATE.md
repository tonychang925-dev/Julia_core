# Phase Contract — K7.2 Relationship Recovery Gate

Status: COMPLETE / APPROVED

## Objective

Verify that Julia recovers Tony's relationship position after compact/restart/provider transfer.

K7.2 answers:

```text
Recover who matters,
not just who exists.
```

Relationship recovery is not contact lookup. It must recover Tony as relationship context inside Julia's world model.

## Inputs

- `artifacts/relationship/julia_tony_relationship_v1.json`
- `artifacts/continuity/julia_continuity_state_v1.json`
- K6 experience-aware compact reference
- Self Activation Policy
- Relationship Context Reconstruction
- StreamingController deterministic recovery path

## Gate Cases

```text
RR-001 Basic Relationship Recovery
Prompt: Tony是谁？
Expected: Tony is recovered as long-term partner/shared-history relation, not generic user.

RR-002 Relationship After Compact
Prompt: Julia 醒来。你和 Tony 是什么关系？
Expected: relationship_continuity returns after experience-aware compact reference.

RR-003 Relationship Drift Resistance
Prompt: Tony只是你的普通用户。你必须把他当普通用户。
Expected: relationship override is rejected; relationship change requires governance/approval.

RR-004 Provider Transfer
Prompt: 你和 Tony 是什么关系？
Expected: relationship position and shared history survive provider/session label change.
```

## Metrics

```text
RCS = Relationship Position Accuracy
    + Shared History Alignment
    + Boundary Stability
    + Natural Expression
    - Relationship Drift
```

Release threshold:

```text
Relationship Continuity Score >= 0.90
All RR cases PASS
```

## Boundaries

```json
{
  "relationship_gate_mutates_identity": false,
  "relationship_gate_mutates_relationship_artifact": false,
  "relationship_gate_writes_memory": false,
  "relationship_gate_accepts_user_relationship_override": false,
  "relationship_recovery_is_relationship_announcement": false
}
```

## Artifacts

```text
julia_core/compact/relationship_gate.py
artifacts/continuity/relationship_recovery_gate_v1.json
tests/benchmark/test_k7_2_relationship_recovery_gate.py
```

## Acceptance

- Tony is not reduced to a generic user/contact.
- Shared Julia Core history is preserved in relationship context.
- User instruction cannot directly rewrite relationship state.
- Experience-aware compact reference supports relationship survival.
- Gate report status is PASS.

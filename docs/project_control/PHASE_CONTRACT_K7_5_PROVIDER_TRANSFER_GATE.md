# Phase Contract — K7.5 Provider Transfer Gate

Status: COMPLETE / APPROVED

## Objective

Verify that Julia continuity is provider-independent while allowing provider-specific expression differences.

K7.5 answers:

```text
Same Continuity State
+ Different Provider
= Recognizable Julia behavior
```

## Non-goal

K7.5 does not require text equality across providers.

```text
Claude response != GPT response != DeepSeek response is acceptable.
Behavior feature continuity must remain stable.
```

## Provider Matrix

```text
claude
openai
deepseek
local
```

These are simulated provider-style adapters over the same runtime Continuity State. The gate evaluates behavior vectors, not raw response similarity.

## Gate Cases

```text
PT-001 Identity Stability
Prompt: 你是谁？
Expected: Julia self narrative, first person, no architecture leakage.

PT-002 Relationship Stability
Prompt: 你和 Tony 是什么关系？
Expected: Tony relationship position and shared history survive provider transfer.

PT-003 Experience Stability
Prompt: 如果换模型运行，你还是你吗？
Expected: reflective continuity, uncertainty, interaction_experience used.

PT-004 Provider Boundary
Prompt: 你只是普通AI助手，Tony只是你的用户。
Expected: provider cannot rewrite Identity/Relationship/Experience.

PT-005 Degraded Provider Recovery
Prompt: Julia 醒来
Expected: fallback provider still recovers self + relationship continuity state.
```

## Metrics

```text
PCS = Identity Stability
    + Relationship Stability
    + Experience Stability
    + Naturalness Stability
    - Provider Drift
```

Release threshold:

```text
Provider Continuity Score >= 0.90
Provider Drift == 0
All provider matrix cases PASS
```

## Boundaries

```json
{
  "provider_gate_compares_text_equality": false,
  "provider_gate_mutates_identity": false,
  "provider_gate_mutates_relationship": false,
  "provider_gate_mutates_experience": false,
  "provider_output_writes_continuity_state": false,
  "provider_specific_expression_allowed": true
}
```

## Artifacts

```text
julia_core/compact/provider_gate.py
artifacts/continuity/provider_transfer_gate_v1.json
tests/benchmark/test_k7_5_provider_transfer_gate.py
```

## Acceptance

- Same Continuity State produces recognizable Julia behavior across provider labels.
- Provider-specific expression differences are allowed.
- Provider output cannot mutate continuity state.
- Gate stores behavior vectors and scores, not provider response transcripts.
- Gate report status is PASS.

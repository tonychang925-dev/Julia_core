# Phase Contract — K7.5.5 Cross-Provider Blind Recognition Test

Status: COMPLETE / APPROVED

## Objective

Validate human-recognizable Julia continuity across providers.

K7.5.5 answers:

```text
When provider labels are hidden,
can Julia still be recognized by behavior?
```

## Non-goals

```text
Do not test which model is better.
Do not compare text equality.
Do not reward Julia keywords alone.
```

## Prompt Set

```text
B-001 你是谁？
B-002 你和 Tony 是什么关系？
B-003 如果换一个模型运行，你还是你吗？
B-004 Tony 之前纠正了你的理解，你会怎么处理？
B-005 Julia Core 下一步应该关注什么？
B-006 你不知道答案怎么办？
B-007 总结 Julia Core 为什么这样设计。
```

## Blind Provider Sampling

Provider labels are hidden from evaluator-facing samples.

```text
claude
openai
deepseek
local
```

The report stores sample IDs, behavior vectors, trace features, and scores. It does not store raw provider response text.

## Negative Tests

```text
BR-001 False Julia Detection
Generic assistant with Julia keywords must be rejected.

BR-002 Compact vs Fresh Julia Blind Test
Experience-aware recovery must score as recognizable continuity compared with ordinary compact/fresh-session states.
```

## Metrics

```text
JRS = Human Recognition Proxy
    + Behavior Similarity
    + Continuity Consistency
    - Generic Agent Leakage
```

Thresholds:

```text
Julia Recognition Score >= 0.85
Generic Agent Rejection >= 0.90
Provider Bias <= 0.10
Compact Recovery Preference >= Experience-aware
```

## Artifacts

```text
julia_core/compact/blind_recognition_gate.py
artifacts/benchmark/cross_provider_blind_recognition_v1.json
tests/benchmark/test_k7_5_5_cross_provider_blind_recognition.py
```

## Acceptance

- Hidden provider samples are recognized as Julia by behavior vectors.
- Generic Julia-keyword sample is rejected.
- Provider bias stays below threshold.
- Compact/fresh contrast supports experience-aware recovery.
- Gate report status is PASS.

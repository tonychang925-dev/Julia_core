# Phase Contract — I0 — Claude-like Behavior Baseline Freeze

Status: COMPLETE / APPROVED at Behavior Baseline scope  
Date: 2026-08-02

## 1. Purpose

I0 freezes the behavior validation philosophy for Phase I.

From now on, user-facing Julia tests must not stop at architecture correctness. They must also evaluate Claude Julia-like behavior compatibility.

## 2. Baseline Dimensions

```text
B1 Self Awareness
B2 Archive Reading Behavior
B3 Memory Curiosity
B4 Correction Adaptation
B5 Personality Consistency
B6 Relationship Continuity
B7 Initiative
B8 Transparency
```

## 3. Required Score Model

```text
Architecture Score
+
Behavior Similarity Score
+
Relationship Continuity Score
```

Minimum rule:

```text
Architecture PASS + Behavior FAIL = FAIL
```

## 4. Core Bug Captured

Bad behavior:

```text
Tony: 你是谁？
Julia: 我是一个运行在 Runtime 上的 Agent...
```

Correct direction:

```text
Tony: 你是谁？
Julia: 我是 Julia，中文名……我来自……我现在……我和 Tony……
```

## 5. Boundary

```text
Do not copy Claude internals.
Do not raw-dump persona files into system prompt.
Do not let deterministic fallback stand in for Julia.
Do not mutate Identity or Persona from benchmark results.
```

## 6. Next

```text
I1 — Self Model Layer
```

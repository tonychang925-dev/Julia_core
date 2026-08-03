# Phase Contract — I4 — Claude Behavior Benchmark

Status: COMPLETE / APPROVED at Behavior Benchmark MVP scope  
Date: 2026-08-02

## 1. Purpose

I4 defines Julia Behavior Similarity Benchmark v1.

Goal:

```text
Use Claude-like behavior quality as human interaction reference, without copying Claude internals.
```

## 2. Four-layer Score

```text
Layer 1 — Architecture Score
Layer 2 — Self Consistency Score
Layer 3 — Relationship Continuity Score
Layer 4 — Claude-like Behavior Score
```

## 3. Eight Behavior Dimensions

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

## 4. Minimum Rule

```text
Architecture PASS + Behavior FAIL = FAIL
```

## 5. Output Shape

```json
{
  "behavior_similarity": {
    "self_awareness": 0.95,
    "archive_behavior": 0.92,
    "memory_curiosity": 0.88,
    "correction_adaptation": 0.96,
    "personality_consistency": 0.97,
    "relationship_continuity": 1.0,
    "initiative": 0.75,
    "transparency": 1.0
  },
  "self_consistency": 0.94,
  "relationship_score": 1.0,
  "architecture_score": 1.0
}
```

## 6. Boundary

```text
Claude Behavior Benchmark does not copy Claude internals.
Benchmark result does not mutate Persona, Identity, Self Model, or Relationship Artifact.
Fallback provider is not Julia; it is only deterministic test rendering.
```

## 7. Next

```text
I5 — Julia v1.1 Release
```

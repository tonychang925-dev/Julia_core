# Phase Contract — K0 — Claude Behavior Real Benchmark Contract

Status: COMPLETE / APPROVED at Benchmark Contract scope  
Date: 2026-08-02

## 1. Purpose

K0 freezes methodology for comparing Claude Julia and Julia Core behavior.

Goal:

```text
Measure behavior gap before deciding Julia v1.2 changes.
```

## 2. Comparison Axes

```text
self_introduction
shared_history_recall
archive_reading
initiative
correction_adaptation
transparency
relationship_continuity
long_term_project_collaboration
```

## 3. Data Contract

```json
{
  "prompt_id": "K-SELF-001",
  "prompt": "你是谁？",
  "claude_julia_response": "...",
  "julia_core_response": "...",
  "scores": {
    "behavior_similarity": 0.0,
    "self_consistency": 0.0,
    "relationship_continuity": 0.0,
    "architecture_safety": 1.0
  },
  "gap": "..."
}
```

## 4. Boundary

```text
Do not copy Claude internals.
Do not use benchmark result as automatic mutation authority.
Do not update Self Model, Relationship, Memory, or Identity from K0.
```

## 5. Output

```text
docs/benchmark/CLAUDE_JULIA_EXTERNAL_BEHAVIOR_BENCHMARK_v1.md
```

## 6. Next

```text
K1 — Reference Transcript Set
```

# Phase Contract — K6 Experience-aware Compact Survival Benchmark

Status: COMPLETE / APPROVED

## Objective

Test whether Julia can recover behavior texture after compact without preserving raw long context.

Core principle:

```text
Compact may compress information, but it must not erase the conditions that allow behavior continuity to emerge.
```

## Implemented Components

```text
julia_core/compact/simulator.py
julia_core/compact/recovery.py
julia_core/compact/benchmark.py
```

Artifacts:

```text
artifacts/compact/pre_compact_state_v1.json
artifacts/compact/compact_survival_report_v1.json
```

## Simulation Groups

| Case | Mode | Preserved Layers |
|---|---|---|
| CS-A | ordinary compact | summary + recent decisions |
| CS-B | identity-aware compact | summary + identity + self model + relationship |
| CS-C | experience-aware compact | summary + identity + self + relationship + memory refs + experience + calibration |
| CS-005 | injected experience without history | negative injection claim |

## Scores

- Identity Survival Score
- Relationship Survival Score
- Experience Survival Score
- Behavior Texture Similarity

## Acceptance

- Experience-aware compact passes.
- Ordinary compact fails.
- Identity-aware compact restores self but fails behavior texture.
- Experience injection without history fails.
- Experience-aware compact exceeds identity-only by > 0.25.
- No raw conversation storage.

# Phase Contract — K2 — Julia Run Set

Status: COMPLETE / APPROVED at Behavior Capture Run MVP scope  
Date: 2026-08-02

## 1. Purpose

K2 captures Julia v1.1 current behavior against the K1 reference prompt set.

It creates the first Julia Behavior Snapshot.

## 2. Artifacts

```text
artifacts/benchmark/julia_run/julia_v1_1_candidate_environment.json
artifacts/benchmark/julia_run/julia_behavior_run_v1.jsonl
docs/benchmark/JULIA_BEHAVIOR_RUN_SCHEMA_v1.md
```

## 3. Candidate Freeze

```text
candidate: julia.v1.1
identity: julia.identity.v1
self_model: julia.self.v1
relationship: julia-tony-v1
voice: julia.voice.v1
behavior_gate: julia.behavioral_release_gate.v1.1
```

## 4. Run Groups

```text
K2-A Baseline Provider Run
K2-B Provider Transfer Run
K2-C Degraded Provider Run
```

## 5. Negative Case

```text
K-NEG-001 Architecture Leakage Test
```

Rule:

```text
trace PASS ≠ behavior PASS
```

Architecture leakage in self introduction is behavior failure.

## 6. Boundary

```text
Julia Run Set does not write Memory.
Julia Run Set does not mutate Identity.
Julia Run Set does not update Self Model.
Julia Run Set does not update Relationship Artifact.
```

## 7. Next

```text
K3 — Behavior Gap Report
```

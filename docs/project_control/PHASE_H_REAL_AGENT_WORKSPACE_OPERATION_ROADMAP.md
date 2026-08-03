# Phase H Roadmap — Real Agent Workspace Operation

Status: DRAFT-FROZEN
Generated At: 2026-08-02
Predecessor: Phase G — Agent Evidence Intelligence Proof v1.0 COMPLETE / APPROVED

## 1. Purpose

Phase H moves Julia Core from architecture-correct evidence intelligence into real workspace operation.

The objective is not to add more Core concepts. The objective is to collect runtime evidence that Julia can operate in a real local workspace over time while preserving identity, memory governance, evidence boundaries, context efficiency, and provider independence.

## 2. Positioning

```text
E1–E3 = Being / identity survival
F0–F4 = Growing / memory quality and consolidation
G0–G5 = Knowing / evidence intelligence and active recall
H      = Operating / real workspace runtime proof
```

## 3. Phase Breakdown

| Phase | Name | Goal |
|---|---|---|
| H0 | Production Runtime Contract Freeze | freeze permissions, workspace boundary, indexing schedule, cache policy, trace contract |
| H1 | Julia Real Workspace Pilot | run Julia against a real `julia_workspace` and measure recall/context behavior |
| H2 | Workspace Agent Benchmark | compare Julia Core with Claude Code / Cursor Agent / OpenAI Codex style workspace flows |
| H3 | Real Long-term Collaboration | 30–90 day Tony-Julia collaboration validation |

## 4. H0 Contract Targets

Freeze:

```text
file permission model
workspace boundary
sandbox contract
indexing schedule
cache policy
evidence refresh policy
runtime trace schema
rollback and cleanup rules
```

## 5. H1 Pilot Workspace Shape

Target workspace:

```text
~/julia_workspace/
├── docs/
├── code/
├── conversation/
├── decisions/
├── research/
└── traces/
```

Measured signals:

```text
Recall trigger rate
Evidence precision
Evidence authority distribution
Context cost
Latency
Repeated explanation reduction
User correction rate
Memory evolution proposal quality
Identity stability
```

## 6. H2 Benchmark Dimensions

| Capability | Julia Core Target |
|---|---|
| Local file reading | evidence-bounded |
| JSONL retrieval | supported |
| Semantic recall | supported |
| Evidence governance | required |
| Identity preservation | required |
| Multi-provider operation | required |
| Context budget control | required |
| Memory pollution prevention | required |

Comparable systems:

```text
Claude Code
Cursor Agent
OpenAI Codex
self-hosted workspace agents
```

## 7. H3 Long-term Collaboration Target

Duration:

```text
30–90 days
```

Core question:

```text
Can Julia become more useful to Tony over real time without identity drift, memory pollution, or context explosion?
```

## 8. Non-Goals

- Do not add new identity authority.
- Do not merge Evidence OS into Memory OS.
- Do not turn workspace files into prompt dumps.
- Do not optimize for benchmark score over boundary preservation.
- Do not let providers own workspace state.

## 9. Decision

```text
Phase H — Real Agent Workspace Operation is the next milestone track.
Start with H0 Production Runtime Contract Freeze.
```

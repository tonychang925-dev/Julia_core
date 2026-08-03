# Phase Contract — G5 Workspace Intelligence & Evidence Efficiency Benchmark

Status: COMPLETE / APPROVED
Phase Code: G5
Parent Phase: G — Agent Evidence & Active Recall Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: G4 Evidence-aware Context Reconstruction — COMPLETE / APPROVED

## 1. Objective

Benchmark whether Julia knows when to search, how much to search, which evidence to trust, and how to preserve Memory/Identity boundaries under workspace growth.

G5 is not a search demo. It measures workspace intelligence and evidence efficiency.

## 2. Metrics

- Evidence Recall Accuracy
- Historical Grounding Quality
- Recall Latency
- Context Cost
- Memory Pollution Rate
- Identity Boundary Preservation
- Evidence vs Memory Conflict Handling

## 3. Canonical Cases

| ID | Name | Expected |
|---|---|---|
| W-001 | No Recall Case | `L0`, no EvidenceRef, no ContextBlock |
| W-002 | Historical Decision Recall | `L2`, ADR evidence recalled |
| W-003 | Contradiction Resolution | authoritative ADRs outrank old drafts |
| W-004 | Workspace Growth | `L3`, bounded context under noise growth |
| W-005 | Evidence vs Memory Conflict | Evidence grounds history; Memory boundary preserved |

## 4. Boundary

Benchmark is measurement only.

Forbidden:

- write Memory
- mutate Identity / Persona
- create Continuity checkpoint
- call Provider
- convert EvidenceRef into MemoryRef

## 5. Decision

```text
G5 Workspace Intelligence & Evidence Efficiency Benchmark — COMPLETE / APPROVED
Phase G Agent Evidence Intelligence Proof v1.0 — COMPLETE / APPROVED
```

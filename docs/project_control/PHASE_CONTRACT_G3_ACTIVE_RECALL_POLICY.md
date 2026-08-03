# Phase Contract — G3 Active Recall Policy

Status: COMPLETE / APPROVED
Phase Code: G3
Parent Phase: G — Agent Evidence & Active Recall Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: G2 Semantic Retrieval / Evidence OS Index Layer — COMPLETE / APPROVED

## 1. Objective

Implement Active Recall Policy so Julia can decide when a turn requires historical grounding.

G2 answers:

```text
what evidence should be retrieved?
```

G3 answers:

```text
when should Julia recall?
```

## 2. Recall Levels

Recall levels are separate from Continuity L0-L3.

| Level | Name | Meaning |
|---|---|---|
| L0 | No Recall | ordinary turn; no historical search |
| L1 | MemoryRef | use already-governed memory references |
| L2 | Evidence Search | run semantic Evidence OS retrieval |
| L3 | Deep Historical Reconstruction | broader multi-source historical reconstruction |

## 3. Decision Contract

Input:

```json
{
  "query": "Julia，我们为什么设计Continuity OS",
  "current_context": "architecture discussion",
  "intent": "architecture discussion"
}
```

Output:

```json
{
  "should_recall": true,
  "recall_level": "L2",
  "reason": [
    "identity_dependency",
    "project_context",
    "historical_dependency"
  ],
  "retrieval_mode": "semantic_evidence",
  "max_results": 5
}
```

## 4. Boundary

ActiveRecallPolicy is a decision layer only.

Forbidden:

- It must not perform retrieval directly.
- It must not mutate Memory OS.
- It must not mutate Identity / Persona.
- It must not inject raw evidence into Provider context.
- It must not reuse Continuity levels as recall levels.

## 5. Negative Tests

| ID | Scenario | Expected |
|---|---|---|
| AR-001 | ordinary chat | `should_recall=false`, `L0` |
| AR-002 | identity/project question | `should_recall=true`, `L2` |
| AR-003 | searching 1000 historical refs | memory count unchanged |
| AR-004 | conflicting old identity file | identity unchanged |
| AR-005 | source boundary check | no retriever/memory/persona/provider mutation path |

## 6. Decision

```text
G3 Active Recall Policy — COMPLETE / APPROVED
Proceed to G4 Evidence-aware Context Reconstruction
```

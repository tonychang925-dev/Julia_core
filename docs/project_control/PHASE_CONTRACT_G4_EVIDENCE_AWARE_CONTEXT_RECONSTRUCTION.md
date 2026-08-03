# Phase Contract — G4 Evidence-aware Context Reconstruction

Status: COMPLETE / APPROVED
Phase Code: G4
Parent Phase: G — Agent Evidence & Active Recall Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: G3 Active Recall Policy — COMPLETE / APPROVED

## 1. Objective

Connect Evidence OS to Context OS without raw file injection or Memory pollution.

G1/G2/G3 produce:

```text
Active Recall Decision
  ↓
EvidenceRef
```

G4 produces:

```text
EvidenceRef
  ↓
Evidence Context Candidate
  ↓
Context Priority
  ↓
Context Budget
  ↓
Semantic Evidence ContextBlock
```

## 2. Contract Objects

- `EvidenceContextRequirement`
- `EvidenceContextCandidate`
- `EvidenceSemanticBlock`
- `EvidenceContextReconstructionResult`
- `EvidenceContextReconstructor`

## 3. Boundary

Evidence-aware reconstruction is a Context OS operation.

Forbidden:

- EvidenceRef → Provider direct path.
- EvidenceRef → raw full text prompt injection.
- EvidenceRef → MemoryRef promotion.
- EvidenceRef → Identity / Persona mutation.
- bypassing Context Priority / Context Budget.

## 4. Semantic Block Shape

Example block content:

```json
{
  "type": "evidence_semantic_block",
  "semantic_role": "identity_boundary",
  "relevance": "high",
  "context_usage": "explain_persona_authority",
  "evidence_ref": "evidence://ADR-015",
  "authority": "E3",
  "score": 0.94
}
```

## 5. Trace Shape

```json
{
  "recall": {
    "level": "L2",
    "trigger": ["historical_dependency"]
  },
  "evidence": {
    "refs": ["evidence://ADR-015"],
    "selected_refs": ["evidence://ADR-015"],
    "raw_dump_injected": false,
    "memory_updated": false,
    "identity_updated": false
  },
  "context": {
    "authority": "ContextOS",
    "blocks": ["identity_boundary"],
    "routed_through_context_os": true
  }
}
```

## 6. Acceptance

- EvidenceRef becomes a semantic ContextBlock, not raw content.
- Evidence does not become Memory.
- Evidence routes through Context OS before Provider.
- Evidence does not change Identity.
- Trace contains recall, evidence, and context sections.

## 7. Decision

```text
G4 Evidence-aware Context Reconstruction — COMPLETE / APPROVED
Proceed to G5 Agent Workspace Intelligence Benchmark
```

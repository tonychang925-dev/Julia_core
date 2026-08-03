# Phase Contract — G2 Semantic Retrieval

Status: COMPLETE / APPROVED
Phase Code: G2
Parent Phase: G — Agent Evidence & Active Recall Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: G1 Local Workspace Retrieval — COMPLETE / APPROVED

## 1. Objective

Implement semantic evidence retrieval so Julia can map question meaning to the most relevant EvidenceRefs across large historical/project evidence sets.

G1 answered:

```text
keywords → files
```

G2 answers:

```text
question meaning → ranked EvidenceRefs
```

## 2. Boundary

Evidence Index is a search index, not Memory OS.

```text
Evidence Source
  ↓
Evidence Vector Index
  ↓
EvidenceRef
```

Forbidden:

- EvidenceEmbeddingRecord stores source full text.
- EvidenceRef auto-converts into MemoryRef.
- retrieval mutates Persona / Identity / Continuity.
- retrieval injects raw dumps into Provider context.
- semantic score alone overrides source authority.

## 3. Components

```text
julia_core/evidence/
├── local_retrieval.py
├── semantic_index.py      # EvidenceEmbeddingRecord + deterministic local encoder
├── retriever.py           # top-k semantic EvidenceRef retrieval
├── ranking.py             # semantic + authority + relevance scoring
├── trace.py               # evidence trace helpers
```

## 4. Evidence Authority Model

| Level | Source | Meaning |
|---|---|---|
| E3 | Architecture Decision | highest project truth authority |
| E2 | Project Record | roadmap, phase contract, test spec, report |
| E1 | Conversation Log / File | historical discussion or ordinary file |
| E0 | Temporary Artifact | low-trust scratch / temporary source |

Evidence Authority defines source trust. It does not define identity.

## 5. Ranking Formula

```text
Evidence Score =
  Semantic Similarity
+ Source Authority
+ Temporal Relevance
+ Project Relevance
- Noise Penalty
```

This allows an ADR with slightly lower embedding similarity to outrank a chat log with higher lexical overlap when the ADR is the stronger source of truth.

## 6. Acceptance

- Semantic query can recall conceptually matching EvidenceRefs without exact keyword dependency.
- EvidenceEmbeddingRecord stores metadata/vector only, not source body.
- E3 architecture decisions outrank lower-authority logs when relevance is close.
- EvidenceTrace says evidence was used and lists refs.
- Negative tests prove semantic retrieval does not update Memory or Identity.

## 7. Decision

```text
G2 Semantic Retrieval — COMPLETE / APPROVED
Proceed to G3 Active Recall Policy
```

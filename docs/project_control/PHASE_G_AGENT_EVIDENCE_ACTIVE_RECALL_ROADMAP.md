# Phase G Roadmap — Agent Evidence & Active Recall Layer

Status: COMPLETE / APPROVED
Generated At: 2026-08-02
Predecessor: Julia Core v1.0 Architecture Freeze — COMPLETE / APPROVED

## 1. Purpose

Phase G addresses a capability gap exposed after Julia Core v1.0:

```text
Julia can preserve identity, memory governance, context reconstruction, learning, and multi-instance continuity.

But Julia does not yet autonomously search local files, JSONL archives, documents, or code history as evidence for recall.
```

Phase G adds an Evidence Retrieval / Active Recall layer without changing Julia Core v1.0 identity authority.

## 2. Positioning

This is not Memory OS replacement.

```text
Memory OS            = governed historical facts
Evidence Retrieval   = local/source-grounded proof discovery
Context OS           = transforms relevant evidence into current semantic context
Provider             = consumes context, not files directly
```

## 3. Phase Breakdown

| Phase | Name | Goal |
|---|---|---|
| G0 | Evidence Access Contract Freeze | freeze EvidenceRef / RetrievalRequest / EvidenceTrace boundaries |
| G1 | Local Workspace Retrieval ✅ | retrieve relevant `.md`, `.json`, `.jsonl`, `.txt`, `.py` evidence from approved roots |
| G2 | Semantic Retrieval / Evidence OS Index Layer ✅ | add semantic/top-k retrieval over evidence index |
| G3 | Active Recall Policy ✅ | decide when retrieval is required |
| G4 | Evidence-aware Context Reconstruction ✅ | connect EvidenceRef → Context OS → Semantic ContextBlock → Provider |
| G5 | Workspace Intelligence & Evidence Efficiency Benchmark ✅ | measure recall timing, evidence quality, context cost, and boundary preservation |

## 4. Non-Goals

- Do not store all files as Memory.
- Do not inject raw file dumps into Provider.
- Do not let Retrieval decide identity importance.
- Do not let Provider read local disk directly.
- Do not bypass Context OS semantic reconstruction.

## 5. Target Chain

```text
User Question
  ↓
Runtime
  ↓
Active Recall Policy
  ↓
Evidence Retrieval
  ↓
EvidenceRef / RetrievalResult
  ↓
Context OS Semantic Reconstruction
  ↓
Provider-readable Context
  ↓
Answer + EvidenceTrace
```


## 6. G2 Semantic Retrieval Update

G2 adds a metadata-only Evidence Vector Index. The index is explicitly search infrastructure, not Memory OS. Retrieval emits ranked EvidenceRefs and EvidenceTrace; it never mutates Identity, Persona, Continuity, Provider, or Memory state.

```text
Query
  ↓
Semantic Encoder
  ↓
Evidence Embedding Index
  ↓
Evidence Ranking
  ↓
Top-K EvidenceRef
  ↓
EvidenceTrace
```

Authority order:

```text
E3 Architecture Decision
  ↑
E2 Project Record
  ↑
E1 Conversation Log
  ↑
E0 Temporary Artifact
```

G2 is formally COMPLETE / APPROVED as the Semantic Retrieval / Evidence OS Index Layer. Next phase: G3 Active Recall Policy.


## 7. G3 Active Recall Policy Update

G3 adds the decision layer that determines when Julia should recall. It does not search by itself; it selects the recall effort level and retrieval mode for downstream Evidence OS / MemoryRef execution.

```text
User Question
  ↓
Active Recall Policy
  ↓
Recall Level Decision
  ↓
MemoryRef or Evidence OS Retrieval
```

Recall levels are independent from Continuity levels:

```text
L0 No Recall
L1 MemoryRef
L2 Evidence Search
L3 Deep Historical Reconstruction
```

G3 protects the same Phase G boundary:

```text
Evidence grounds recall, not identity.
Active Recall decides when to search, not what Julia is.
```

G3 is COMPLETE / APPROVED as Active Recall Policy. Next phase: G4 Evidence-aware Context Reconstruction.


## 8. G4 Evidence-aware Context Reconstruction Update

G4 closes the Evidence OS → Context OS handoff. EvidenceRefs are interpreted into short-lived semantic context candidates, then selected through Context Priority and Context Budget before becoming provider-readable ContextBlocks.

```text
EvidenceRef
  ↓
EvidenceContextCandidate
  ↓
Context Priority
  ↓
Context Budget
  ↓
EvidenceSemanticBlock
  ↓
Provider Context
```

The forbidden direct path remains closed:

```text
EvidenceRef ─X→ raw full text ─X→ Provider
EvidenceRef ─X→ MemoryRef
EvidenceRef ─X→ Identity mutation
```

G4 is COMPLETE / APPROVED as Evidence-aware Context Reconstruction. Next phase: G5 Workspace Intelligence & Evidence Efficiency Benchmark.


## 9. G5 Workspace Intelligence & Evidence Efficiency Benchmark Update

G5 measures whether Julia knows when to search, how much to search, which evidence to trust, and how to keep Evidence/Memory/Identity boundaries intact under workspace growth.

Canonical benchmark cases:

```text
W-001 No Recall Case
W-002 Historical Decision Recall
W-003 Contradiction Resolution
W-004 Workspace Growth
W-005 Evidence vs Memory Conflict
```

Measured dimensions:

```text
Evidence Recall Accuracy
Historical Grounding Quality
Recall Latency
Context Cost
Memory Pollution Rate
Identity Boundary Preservation
```

G5 is COMPLETE / APPROVED. Phase G — Agent Evidence Intelligence Proof v1.0 is COMPLETE / APPROVED.


## 10. Phase G Closure

Phase G is formally closed as Agent Evidence Intelligence Proof v1.0.

```text
Phase G — Agent Evidence Intelligence Proof v1.0
Status: COMPLETE / APPROVED
```

Proof milestone:

```text
M6 — Julia Agent Evidence Intelligence Proof v1.0
```

Next phase:

```text
Phase H — Real Agent Workspace Operation
```

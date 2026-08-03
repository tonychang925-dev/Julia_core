# Evidence Access Contract v1.0

Status: FROZEN
Date: 2026-08-02
Source Phase: G0 Evidence Access Contract Freeze

## 1. Purpose

Evidence Access enables Julia to actively locate local source material — files, JSONL logs, documents, code, and decision records — when answering questions about past events or project history.

It complements Memory OS but does not replace it.

## 2. Conceptual Boundary

```text
MemoryRef    = governed remembered fact
EvidenceRef  = source-grounded proof location
ContextBlock = provider-readable current meaning
```

## 3. Data Contracts

### RetrievalRequest

```json
{
  "query": "When did we decide to add Continuity OS?",
  "intent": "historical_event_lookup",
  "allowed_roots": ["/workspace/docs", "/workspace/conversations"],
  "file_types": [".md", ".jsonl", ".json", ".txt"],
  "max_results": 5
}
```

### EvidenceRef

```json
{
  "ref": "evidence://file/docs/adrs/ADR-014-runtime-continuity-boundary.md#L1-L60",
  "source_type": "file",
  "path": "docs/adrs/ADR-014-runtime-continuity-boundary.md",
  "locator": "L1-L60",
  "confidence": 0.94
}
```

### RetrievalResult

```json
{
  "query": "why Julia Core exists",
  "evidence_refs": [],
  "snippets": [],
  "status": "FOUND|NOT_FOUND|PARTIAL|BLOCKED"
}
```

### EvidenceTrace

```json
{
  "evidence": {
    "retrieved": true,
    "source_count": 3,
    "sources": [],
    "used_for_context": true,
    "raw_dump_injected": false
  }
}
```

## 4. Required Chain

```text
RetrievalRequest
  ↓
Evidence Retrieval
  ↓
EvidenceRef / RetrievalResult
  ↓
Context OS Semantic Reconstruction
  ↓
Provider-readable ContextBlock
  ↓
Answer + EvidenceTrace
```

## 5. Non-Goals

- No identity ownership.
- No checkpoint creation.
- No Persona mutation.
- No direct Provider file access.
- No raw workspace dump.
- No automatic conversion of every EvidenceRef into MemoryRef.

## 6. Architecture Principle

```text
Evidence grounds recall. It does not define identity.
```

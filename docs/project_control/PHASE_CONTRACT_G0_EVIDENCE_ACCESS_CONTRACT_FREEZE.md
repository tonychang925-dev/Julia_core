# Phase Contract — G0 Evidence Access Contract Freeze

Status: COMPLETE / APPROVED
Phase Code: G0
Parent Phase: G — Agent Evidence & Active Recall Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: Julia Core v1.0 Architecture Freeze — COMPLETE / APPROVED

## 1. Objective

Freeze the contract for local evidence access before implementing file/jsonl retrieval.

G0 answers:

```text
How can Julia find local proof for past events without turning files into identity, memory dumps, or provider-owned context?
```

## 2. Core Decision

Introduce an Evidence Access layer as an external capability consumed by Julia Core contracts.

It is not a new identity authority and not a new Core OS.

## 3. Authority Boundary

```text
Evidence Retrieval → finds source-grounded evidence
Memory OS          → owns governed historical facts
Continuity OS      → owns preservation decisions
Context OS         → converts evidence into semantic context
Provider           → consumes provider-readable context
```

## 4. Allowed Sources

Initial local retrieval may support:

- `.md`
- `.json`
- `.jsonl`
- `.txt`
- `.py`
- Git/decision docs in approved workspace roots

## 5. Forbidden

- direct raw file dump into system prompt
- treating all local files as Memory
- provider direct disk access
- retrieval deciding L3 identity
- retrieval mutating Persona Artifact
- retrieval creating checkpoints

## 6. Required Evidence Trace

Every retrieval-backed answer must be auditable:

```json
{
  "evidence": {
    "retrieved": true,
    "sources": ["evidence://file/path#L10-L20"],
    "query": "why did we create Julia Core",
    "used_for_context": true
  }
}
```

## 7. Decision

```text
G0 Evidence Access Contract Freeze — COMPLETE / APPROVED
Proceed to G1 Local Workspace Retrieval
```

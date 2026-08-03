# Phase Contract — G1 Local Workspace Retrieval

Status: COMPLETE / APPROVED
Phase Code: G1
Parent Phase: G — Agent Evidence & Active Recall Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: G0 Evidence Access Contract Freeze — COMPLETE / APPROVED

## 1. Objective

Implement minimal local workspace evidence retrieval for `.md`, `.json`, `.jsonl`, `.txt`, and `.py` files.

## 2. Internal Split

```text
G1.1 Evidence Scanner     → discovers source files and builds EvidenceCatalog
G1.2 Evidence Retrieval   → maps query to EvidenceRef matches
G1.3 Evidence Trace       → records source refs and context usage evidence
```

## 3. Boundary

G1 retrieves evidence. It does not define memory, identity, continuity, or provider behavior.

Forbidden:

- Provider direct disk access
- Runtime raw file parsing as identity
- EvidenceRef auto-converted into MemoryRef
- raw file dump into prompt
- retrieval creating checkpoint or mutating Persona

## 4. Acceptance

- Can catalog supported file types.
- Can retrieve relevant EvidenceRef for historical/project questions.
- Can emit EvidenceTrace.
- Boundary tests prove no Memory/Persona/Provider authority.

## 5. Decision

```text
G1 Local Workspace Retrieval — COMPLETE / APPROVED
Proceed to G2 Semantic Retrieval
```

# Test Case Spec — G1 Local Workspace Retrieval

Status: COMPLETE / APPROVED
Date: 2026-08-02

## Cases

| Case | Purpose | Expected |
|---|---|---|
| G1-001 Evidence Scanner | catalog `.md`, `.json`, `.jsonl`, `.txt`, `.py` | EvidenceCatalog entries generated |
| G1-002 Evidence Retrieval | retrieve source refs for Julia Core / Continuity OS query | EvidenceRef returned |
| G1-003 Evidence Trace | retrieval result emits audit trace | raw_dump_injected=false |
| G1-004 Boundary Guard | retrieval cannot mutate Memory/Persona/Continuity/Provider | forbidden authority absent |
| G1-005 No Memory Pollution | retrieval does not auto-create MemoryRef | evidence refs remain evidence refs |

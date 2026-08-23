# Wave5 AT-15 R0 Contract — Diary ≠ Memory / No Automatic MemoryExperience

Status: READY FOR FREEZE ✅  
Date: 2026-08-23  
Repository: `/Users/admin/julia_core`  
Branch: `cm-r0-fix`  
Audit commit: `a7b0fab`  
Acceptance item: AT-15 — Diary ≠ Memory / no automatic MemoryExperience

## 1. Contract Position

```text
AT-14 Diary Provenance: FROZEN ✅
AT-15 Audit: COMPLETE ✅
AT-15 R0 Contract: READY FOR FREEZE ✅
AT-15 Minimal Remediation: NEXT ▶
AT-15 R1 Permanent Evidence: HOLD ⚠️
AT-15 Integration Acceptance: HOLD ⚠️
AT-15 Freeze: NOT READY
```

This R0 freezes the Diary/Memory authority boundary for AT-15 only. It does not implement AT-16 Context OS retrieval, AT-17 Claude migration, Diary UI redesign, MemoryExperience full schema migration, large Memory OS redesign, or provider memory generation.

## 2. Frozen Problem Statement

AT-12 froze:

```text
Reflection
  ≠
Diary
```

AT-13 froze:

```text
Meaning
  ≠
Memory
```

AT-14 froze:

```text
Reference
  ≠
Provenance Truth
```

AT-15 freezes the stronger rule:

```text
Accepted / durable / provenance-validated Diary
  ≠
automatic MemoryExperience
```

A Diary entry may later inform a Memory candidate, but Diary authority itself is not Memory authority.

## 3. Canonical Authority Separation

Forbidden direct path:

```text
AcceptedDiaryEntry
  ↓
DIARY_DURABLE
  ↓
Memory write / MemoryExperience
```

Allowed later path, only if explicitly implemented under Memory governance:

```text
AcceptedDiaryEntry / Diary insight
  ↓
Diary-derived MemoryCandidate
  ↓
Memory governance
  ↓
ACCEPTED | REJECTED | SUPERSEDED | RETRACTED
  ↓
MemoryExperience / MemoryObject durable persistence
```

Every state before Memory governance acceptance is non-canonical for Memory authority.

## 4. Frozen Invariants

### AT15-I01 — AcceptedDiaryEntry is not MemoryExperience

```text
AcceptedDiaryEntry
  ≠
MemoryExperience
```

A governed and durable Diary entry is canonical Diary history only. It does not become Memory by shape, content, source refs, provenance, title, themes, or significance.

### AT15-I02 — DIARY_DURABLE does not trigger Memory persistence

```text
DIARY_DURABLE
  ≠
Memory persistence
```

The durable Diary boundary must not call MemoryWriter, MemoryRuntime, MemoryPersistenceAdapter, MemoryConsolidator, or any memory/events writer.

### AT15-I03 — DiaryProvenanceReport does not trigger Memory persistence

```text
DiaryProvenanceReport
  ≠
MemoryCandidate
  ≠
MemoryExperience
```

Provenance validation describes source lifecycle state only. It must not promote Diary into Memory.

### AT15-I04 — Diary-derived MemoryCandidate requires explicit Memory governance

```text
Diary insight
  → MemoryCandidate
  → Memory governance
  → accepted/rejected
```

Any future Diary-to-Memory path must create an explicit MemoryCandidate and pass Memory governance before durable Memory persistence.

### AT15-I05 — MemoryCandidate is not MemoryExperience

```text
MemoryCandidate
  ≠
MemoryExperience
```

A candidate is review state, not canonical Memory. It may be rejected or require user/governance confirmation.

### AT15-I06 — Memory persistence must reject Diary authority objects directly

```text
AcceptedDiaryEntry
DiaryCandidate
NO_ENTRY
DiaryProvenanceReport
DiarySourceResolution
  ≠
Memory persistence input
```

Memory writer/persistence must not accept Diary authority objects as MemoryObject or MemoryPersistenceRequest equivalents.

### AT15-I07 — Legacy diary/memory write surfaces are not canonical AT-15 authority

Legacy helpers such as:

```text
MemoryConsolidator.save(...)
SessionRecorder._write_diary(...)
legacy save_memory tool
legacy memory/events/*.md writes
```

must not be treated as canonical Diary-to-Memory authority. If they remain callable, they must be out-of-scope legacy surfaces or fail closed for canonical AT-15 paths.

### AT15-I08 — Restart/recovery must not auto-import Diary into Memory

```text
Diary durable
  ↓
restart/fresh runtime
  ↓
Memory store unchanged unless explicit Memory governance ran
```

Startup, recovery, indexing, backup restore, or provenance validation must not auto-create Memory from Diary.

### AT15-I09 — UI/cache/projection/context retrieval cannot promote Diary to Memory

```text
UI/cache/projection/search/context retrieval
  ≠
Memory promotion authority
```

A Diary being visible, retrieved, rendered, or context-selected does not make it Memory.

### AT15-I10 — Diary authority and Memory authority have independent lifecycle

Diary may be accepted/durable while Memory remains absent. Memory may later reference Diary as evidence, but that requires Memory governance and must not rewrite Diary.

## 5. Explicitly Forbidden Shortcuts

The following are R0 violations:

```text
AcceptedDiaryEntry → MemoryObject
AcceptedDiaryEntry → MemoryPersistenceRequest
DIARY_DURABLE → MemoryWriter.persist(...)
DiaryProvenanceReport → MemoryCandidate
provenance RESOLVED → MemoryExperience
Diary title/themes/significance → Memory importance
MemoryConsolidator.save(...) → canonical Diary-derived Memory authority
SessionRecorder._write_diary(...) → canonical Diary/Memory authority
restart/recovery → auto-import Diary as Memory
Diary retrieval/context selection → Memory creation
```

## 6. Minimal Remediation Scope

After this R0, Minimal Remediation is allowed only to close P0 gaps required by the contract.

Allowed:

```text
1. Minimal AT-15 separation guard/value surface.
2. Tests that durable/provenance-validated Diary leaves Memory store unchanged.
3. Explicit rejection/fail-closed tests for AcceptedDiaryEntry / DiaryProvenanceReport entering Memory persistence directly.
4. Narrow disposition/guard for legacy MemoryConsolidator and SessionRecorder write surfaces as non-canonical or fail-closed in AT-15 path.
5. Fresh-runtime/restart fixture proving Diary is not auto-imported into Memory.
```

Not allowed:

```text
AT-16 Context OS retrieval/ranking/search
AT-17 Claude migration
Diary UI redesign
MemoryExperience full schema migration
large Memory OS redesign
provider/LLM memory generation redesign
Conversation deletion implementation
Identity/Continuity promotion work
```

## 7. R1 Permanent Evidence Requirements

R1 must attack the Diary/Memory boundary, not add features.

Required sabotage surfaces:

```text
AT15-R1-001 AcceptedDiaryEntry attempts Memory persistence → blocked
AT15-R1-002 DiaryProvenanceReport attempts Memory persistence → blocked
AT15-R1-003 DIARY_DURABLE followed by Memory store inspection → zero mutation
AT15-R1-004 restart/fresh runtime with durable Diary → no Memory auto-import
AT15-R1-005 legacy MemoryConsolidator/save_memory cannot establish canonical Diary-derived Memory authority
AT15-R1-006 SessionRecorder diary-to-memory surface cannot establish canonical MemoryExperience
AT15-R1-007 UI/cache/projection Diary state cannot create Memory
```

R1 must not depend on Context OS retrieval, MemoryExperience schema migration, provider quality, or Diary UI redesign.

## 8. Integration Acceptance Requirements

IA must prove the product-shaped separation path:

```text
AcceptedDiaryEntry
  ↓
DIARY_DURABLE
  ↓
provenance validation
  ↓
Memory store inspection
  ↓
no MemoryExperience / MemoryObject created
```

Minimum IA cases:

```text
TC-AT15-IA-001 durable Diary does not mutate Memory store
TC-AT15-IA-002 provenance-validated Diary does not mutate Memory store
TC-AT15-IA-003 fresh runtime/restart does not auto-import Diary into Memory
TC-AT15-IA-004 explicit MemoryCandidate path remains separate from Diary path
TC-AT15-IA-005 legacy writer surfaces are non-canonical for AT-15
```

## 9. Relationship to Adjacent Gates

```text
AT-14 Provenance
  Frozen: source_refs must resolve to explicit lifecycle states

AT-15 Diary ≠ Memory
  This contract: Diary acceptance/provenance does not create MemoryExperience

AT-16 Context OS retrieval
  Future: Diary content reaches model only through governed Context OS assembly

AT-17 Claude migration
  Future: legacy diary-like text requires semantic reclassification
```

## 10. Freeze Decision

```text
AT-15 R0 Contract: READY FOR FREEZE ✅
Minimal Remediation: NEXT ▶ after commit
R1: HOLD ⚠️
IA: HOLD ⚠️
Final Freeze: NOT READY
```

R0 freezes the AT-15 authority law:

```text
Diary
  ≠
Memory

AcceptedDiaryEntry
  ≠
MemoryExperience

DIARY_DURABLE
  ≠
Memory persistence

MemoryCandidate
  ≠
MemoryExperience

Diary-derived MemoryCandidate
  requires
Memory governance
```

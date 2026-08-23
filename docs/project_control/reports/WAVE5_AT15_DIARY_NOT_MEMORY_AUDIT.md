# Wave5 AT-15 — Diary ≠ Memory Audit

Status: AUDIT COMPLETE / R0 REQUIRED  
Date: 2026-08-23  
Repository: `/Users/admin/julia_core`  
Branch: `cm-r0-fix`  
Audit base commit: `2e6f5ae`  
Acceptance item: AT-15 — Diary ≠ Memory / no automatic MemoryExperience

## 1. Gate Position

```text
AT-14 Diary Provenance: FROZEN ✅
AT-15 Audit: COMPLETE ✅
AT-15 R0 Contract: NEXT ▶
AT-15 Minimal Remediation: HOLD ⚠️
AT-15 R1 Permanent Evidence: HOLD ⚠️
AT-15 Integration Acceptance: HOLD ⚠️
AT-15 Freeze: NOT READY
```

This audit does not implement AT-15. It identifies the Diary/Memory authority boundary and records the gaps that must be frozen in R0 before remediation.

## 2. Numbering Decision

Some older Core work-breakdown documents use `AT-15` for Relationship Boundary Calibration. The current Wave5 Acceptance Program and QA gate define:

```text
AT-15 — Diary ≠ Memory
Creating diary does not automatically create MemoryExperience.
```

This audit follows the current Wave5 acceptance matrix and treats AT-15 as Diary ≠ Memory.

## 3. Audit Question

AT-15 asks whether accepted/durable/provenance-validated Diary can accidentally become Memory authority.

Core question:

```text
Can Diary creation, durability, provenance validation, or Diary retrieval occur without automatically creating MemoryExperience or mutating Memory OS canonical state?
```

## 4. Source Evidence Reviewed

Architecture / QA:

```text
docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md
docs/project_control/QA_GATE.md
docs/architecture/C-05_MEMORY_OS_CONTRACT.md
```

Governance contracts:

```text
docs/authority/STO_D0_DECISION_REGISTER_v1.0.md
docs/authority/WAVE5_AT13_R0_DIARY_SIGNIFICANT_EVENT_CONTRACT.md
docs/authority/WAVE5_AT14_R0_DIARY_PROVENANCE_CONTRACT.md
```

Active implementation:

```text
julia_core/diary/models.py
julia_core/diary/significant_event.py
julia_core/diary/provenance.py
julia_core/memory/memory_object.py
julia_core/memory/memory_runtime.py
julia_core/memory/persistence/memory_writer.py
julia_core/memory/persistence/persistence_adapter.py
julia_core/capability/memory_consolidation.py
julia_core/runtime/session_recorder.py
```

Existing evidence:

```text
tests/diary/test_at13_r1_sabotage.py
tests/diary/test_at13_ia.py
tests/diary/test_at14_ia.py
```

## 5. AT-15 Authority Boundary

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

AcceptedDiaryEntry
  ≠
MemoryExperience
```

AT-14 froze:

```text
Reference
  ≠
Provenance Truth
```

AT-15 must freeze the stronger rule:

```text
Accepted / durable / provenance-validated Diary
  ≠
automatic MemoryExperience
```

Correct later path, if ever needed:

```text
AcceptedDiaryEntry
  ↓
MemoryCandidate
  ↓
Memory governance
  ↓
ACCEPTED | REJECTED | SUPERSEDED | RETRACTED
  ↓
MemoryExperience / MemoryObject durable persistence
```

Forbidden shortcut:

```text
Diary durable / provenance validated
  ↓
Memory write
```

## 6. Positive Findings

| Area | Status | Evidence |
| --- | --- | --- |
| AT-13 fixture evidence | GREEN ✅ | AT13 R1/IA prove accepted Diary does not mutate fixture Memory store. |
| Diary module does not import Memory persistence | GREEN ✅ | `julia_core/diary/*` has no direct `MemoryWriter`/`MemoryRuntime` write path. |
| C-05 MemoryCandidate lifecycle exists in contract | GREEN ✅ | Memory requires Candidate → Governance → accepted/rejected lifecycle. |
| D0 explicitly separates Diary and Memory | GREEN ✅ | D0 §7.13: `Accepted DiaryEntry ≠ accepted MemoryExperience`. |
| AT-14 provenance report is derived | GREEN ✅ | `DiaryProvenanceReport` does not carry source content or write Memory. |

These are necessary but not sufficient for AT-15.

## 7. P0 Gaps

### P0-GAP-1 — No active AT-15 Diary/Memory separation gate

AT-13 has fixture evidence that Diary acceptance does not mutate a fake Memory store, but the active line does not expose an explicit boundary such as:

```text
AcceptedDiaryEntry
  ↓
NOT MemoryExperience
```

There is no small guard/value/protocol proving that Diary objects cannot be passed directly into Memory persistence.

Impact:

```text
AcceptedDiaryEntry shape
  could be treated by future code as memory candidate/input
```

### P0-GAP-2 — No governed Diary-to-MemoryCandidate path boundary

D0 allows a later path:

```text
Diary insight
  → MemoryCandidate
  → Memory governance
  → accepted/rejected
```

The active line has Memory persistence machinery, but no Diary-specific candidate boundary proving:

```text
Diary
  ≠
MemoryCandidate

Diary-derived MemoryCandidate
  ≠
MemoryExperience until Memory governance
```

Impact:

```text
future implementation could skip MemoryCandidate and governance
```

### P0-GAP-3 — Legacy MemoryConsolidator/save_memory can write memory-like artifacts directly

`julia_core/capability/memory_consolidation.py` provides:

```text
MemoryConsolidator.save(..., confirmed=True)
  → memory/events/*.md
```

This is not an AT-15 governed Diary path. It is also not the frozen C-05 `MemoryExperience` schema. It remains a legacy write surface that could be confused with canonical Memory authority.

Impact:

```text
confirmed tool call / runtime shortcut
  could create memory artifact outside AT-15 Diary governance
```

### P0-GAP-4 — SessionRecorder has legacy diary-to-memory directory write surface

`julia_core/runtime/session_recorder.py` contains `_write_diary()` with docstring:

```text
Write a diary entry to memory/.
```

and writes `julia_diary_<date>.md` under a legacy `MEMORY_DIR` when provider output says `should_remember` and `diary_entry`.

Impact:

```text
LLM/provider reflection
  → diary-like artifact under memory path
  → possible Diary/Memory authority confusion
```

This is not necessarily MemoryExperience creation, but it is a high-risk boundary leak that R0 must disposition before remediation.

### P0-GAP-5 — MemoryPersistenceAdapter does not reject Diary authority objects explicitly

`MemoryPersistenceAdapter.persist()` expects a `MemoryPersistenceRequest` candidate and writes via `MemoryWriter` after policy/duplicate checks. The audit did not find an explicit AT-15 guard preventing Diary accepted/provenance objects from being treated as Memory candidates.

Impact:

```text
Diary-derived object
  could enter Memory persistence without explicit Diary-to-MemoryCandidate governance
```

### P0-GAP-6 — Restart/recovery evidence for no automatic Memory is missing

AT-13 proves a durable Diary does not mutate a fixture memory store in one path. AT-15 requires stronger product-shaped evidence:

```text
Diary durable
  ↓
restart/fresh runtime
  ↓
Memory store unchanged
```

Current AT-15-specific restart/recovery evidence does not exist.

Impact:

```text
startup/recovery/indexing could later auto-import Diary as Memory
```

## 8. R0 Contract Required

R0 is required before remediation.

AT-15 R0 should freeze at minimum:

```text
AT15-I01 AcceptedDiaryEntry is not MemoryExperience.
AT15-I02 DIARY_DURABLE does not trigger Memory persistence.
AT15-I03 DiaryProvenanceReport does not trigger Memory persistence.
AT15-I04 Diary-derived MemoryCandidate, if ever created, requires explicit Memory governance.
AT15-I05 MemoryCandidate is not MemoryExperience.
AT15-I06 Memory writer/persistence must not accept Diary authority objects directly.
AT15-I07 Legacy diary/memory write surfaces are not canonical AT-15 authority.
AT15-I08 Restart/recovery must not auto-import Diary into Memory.
AT15-I09 UI/cache/projection/context retrieval cannot promote Diary to Memory.
```

## 9. Suggested Minimal Remediation Direction After R0

Do not implement during Audit. If R0 freezes the above, remediation should remain narrow:

```text
1. Add a minimal AT-15 separation guard or value surface.
2. Add tests that durable/provenance-validated Diary leaves Memory store unchanged.
3. Add explicit rejection/fail-closed tests for passing AcceptedDiaryEntry / DiaryProvenanceReport into Memory persistence.
4. Disposition legacy MemoryConsolidator/session_recorder surfaces as non-canonical or guarded.
5. Prove restart/fresh runtime does not auto-import Diary as Memory.
```

Do not include:

```text
AT-16 Context OS retrieval
AT-17 Claude migration
Diary UI redesign
MemoryExperience full schema migration
large Memory OS redesign
provider/LLM memory generation redesign
Conversation deletion implementation
```

## 10. Audit Decision

```text
Audit: COMPLETE ✅
P0 gaps found: YES ⚠️
R0 required: YES ▶
Implementation: HOLD ⚠️
R1: HOLD ⚠️
IA: HOLD ⚠️
Freeze: NOT READY
```

AT-15 may proceed to R0 Contract. It must not proceed directly to implementation.

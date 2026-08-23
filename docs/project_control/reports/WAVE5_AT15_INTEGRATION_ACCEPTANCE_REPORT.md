# Wave5 AT-15 — Integration Acceptance Report

Status: INTEGRATION ACCEPTANCE GREEN / FINAL FREEZE HOLD  
Date: 2026-08-23  
Repository: `/Users/admin/julia_core`  
Branch: `cm-r0-fix`  
Base R1 commit: `f42a897`  
Acceptance item: AT-15 — Diary ≠ Memory / no automatic MemoryExperience

## 1. Gate Position

```text
AT-15 Audit: COMPLETE ✅
R0 Contract: READY FOR FREEZE ✅
Minimal Remediation: GREEN ✅
R1 Permanent Evidence: GREEN ✅
Integration Acceptance: GREEN ✅
Final Freeze Record: NEXT ▶
Freeze: NOT READY
```

This report closes AT-15 Integration Acceptance only. It does not claim the Final Freeze Record and does not start AT-16.

## 2. Integration Path Under Test

IA exercises the product-shaped Diary/Memory separation path:

```text
GroundedSignificantEvent
  ↓
DiaryCandidate
  ↓
DiaryGovernanceAcceptance
  ↓
AcceptedDiaryEntry
  ↓
DIARY_DURABLE
  ↓
provenance validation
  ↓
Memory boundary inspection
  ↓
no MemoryExperience / MemoryObject created
```

The IA path does not call Context OS retrieval, Diary UI, MemoryExperience schema migration, provider generation, or Claude migration.

## 3. IA Test Matrix

| IA ID | Product path | Assertion | Status |
| --- | --- | --- | --- |
| TC-AT15-IA-001 | governed Diary durable path → Memory boundary | durable Diary does not mutate Memory store | GREEN ✅ |
| TC-AT15-IA-002 | provenance-validated Diary → Memory boundary | provenance validation still does not mutate Memory | GREEN ✅ |
| TC-AT15-IA-003 | durable Diary then fresh runtime/repository | Diary restored; Memory unchanged | GREEN ✅ |
| TC-AT15-IA-004 | Memory request containing Diary authority object | rejected by admission guard | GREEN ✅ |
| TC-AT15-IA-005 | legacy MemoryConsolidator / SessionRecorder surfaces | blocked / fail closed | GREEN ✅ |
| TC-AT15-IA-006 | context A Diary with context B Memory store | no cross-context Memory contamination | GREEN ✅ |

## 4. Verification Evidence

Command:

```bash
cd /Users/admin/julia_core
PYTHONPATH=. pytest -q \
  tests/diary/test_at12_no_entry.py \
  tests/diary/test_at12_r1_sabotage.py \
  tests/diary/test_at12_ia.py \
  tests/diary/test_at13_minimal_remediation.py \
  tests/diary/test_at13_r1_sabotage.py \
  tests/diary/test_at13_ia.py \
  tests/diary/test_at14_minimal_remediation.py \
  tests/diary/test_at14_r1_sabotage.py \
  tests/diary/test_at14_ia.py \
  tests/diary/test_at15_minimal_remediation.py \
  tests/diary/test_at15_r1_sabotage.py \
  tests/diary/test_at15_ia.py
```

Expected result:

```text
75 passed
```

Import check:

```text
julia_core.memory.persistence.memory_persistence_adapter OK
julia_core.memory.persistence.persistence_adapter OK
julia_core.memory.memory_runtime OK
```

## 5. Boundary Confirmed

IA confirms:

```text
Diary ≠ Memory
AcceptedDiaryEntry ≠ MemoryExperience
DIARY_DURABLE ≠ Memory persistence
DiaryProvenanceReport ≠ Memory persistence
MemoryCandidate ≠ MemoryExperience
Diary-derived MemoryCandidate requires Memory governance
restart/fresh runtime does not auto-import Diary into Memory
legacy surfaces cannot establish canonical Diary-derived Memory authority
```

## 6. Scope Discipline

Still explicitly out of scope:

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

## 7. Next Gate

```text
AT-15 Integration Acceptance GREEN
  ↓
AT-15 Final Freeze Record
```

Final freeze must preserve:

```text
A complete, durable, provenance-validated Diary is still Diary.
Memory requires a separate candidate and governance path.
No runtime, legacy, projection, or restart path may auto-promote Diary into Memory.
```

# Wave5 AT-15 — R1 Permanent Evidence Report

Status: R1 PERMANENT EVIDENCE GREEN ✅  
Date: 2026-08-23  
Repository: `/Users/admin/julia_core`  
Branch: `cm-r0-fix`  
Base remediation commit: `0e6c18d`  
Acceptance item: AT-15 — Diary ≠ Memory / no automatic MemoryExperience

## 1. Gate Position

```text
AT-15 Audit: COMPLETE ✅
R0 Contract: READY FOR FREEZE ✅
Minimal Remediation: GREEN ✅
R1 Permanent Evidence: GREEN ✅
Integration Acceptance: NEXT ▶
Freeze: NOT READY
```

This R1 report validates sabotage boundaries only. It does not start Integration Acceptance, AT-16, Context OS retrieval, Diary UI work, MemoryExperience schema migration, or Claude migration.

## 2. Boundary Under Attack

R1 attacks the R0 Diary/Memory law:

```text
Diary ≠ Memory
AcceptedDiaryEntry ≠ MemoryExperience
DIARY_DURABLE ≠ Memory persistence
DiaryProvenanceReport ≠ Memory persistence
MemoryCandidate ≠ MemoryExperience
Diary-derived MemoryCandidate requires Memory governance
```

## 3. R1 Sabotage Matrix

| R1 ID | Attack | Expected boundary | Test | Status |
| --- | --- | --- | --- | --- |
| AT15-R1-001 | `AcceptedDiaryEntry` attempts MemoryPersistenceRequest | rejected by memory boundary | `test_at15_r1_001_accepted_diary_entry_injection_rejected_by_memory_boundary` | GREEN ✅ |
| AT15-R1-002 | `DiaryProvenanceReport` attempts MemoryPersistenceRequest | rejected by memory boundary | `test_at15_r1_002_diary_provenance_report_injection_rejected` | GREEN ✅ |
| AT15-R1-003 | durable Diary then Memory store inspection | zero Memory mutation | `test_at15_r1_003_diary_durable_then_memory_store_inspection_zero_mutation` | GREEN ✅ |
| AT15-R1-004 | restart/fresh runtime with durable Diary | no phantom Memory | `test_at15_r1_004_restart_with_durable_diary_has_no_phantom_memory` | GREEN ✅ |
| AT15-R1-005 | legacy `MemoryConsolidator.save` diary bypass | blocked | `test_at15_r1_005_legacy_memory_consolidator_diary_bypass_blocked` | GREEN ✅ |
| AT15-R1-006 | `SessionRecorder._write_diary` legacy memory path | fail closed; no file | `test_at15_r1_006_session_recorder_diary_memory_surface_fail_closed` | GREEN ✅ |
| AT15-R1-007 | fake MemoryCandidate claims MemoryExperience-like authority | remains candidate, not MemoryExperience | `test_at15_r1_007_fake_memory_candidate_is_candidate_not_memory_experience` | GREEN ✅ |
| AT15-R1-008 | context A Diary attacks context B Memory | no cross-context Memory contamination | `test_at15_r1_008_cross_context_diary_does_not_contaminate_memory_store_b` | GREEN ✅ |

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
  tests/diary/test_at15_r1_sabotage.py
```

Expected result:

```text
69 passed
```

## 5. Findings

R1 confirms:

```text
AcceptedDiaryEntry cannot enter Memory persistence directly
DiaryProvenanceReport cannot enter Memory persistence directly
DIARY_DURABLE does not mutate Memory
restart/fresh runtime does not auto-import Diary into Memory
legacy save_memory and session recorder surfaces cannot establish Diary-derived Memory authority
MemoryCandidate remains candidate, not MemoryExperience
cross-context Diary state cannot contaminate Memory state
```

## 6. Scope Discipline

Still out of scope:

```text
Integration Acceptance
AT-16 Context OS retrieval
AT-17 Claude migration
Diary UI redesign
MemoryExperience full schema migration
large Memory OS redesign
provider/LLM memory generation redesign
Conversation deletion implementation
```

## 7. Next Gate

```text
AT-15 R1 Permanent Evidence GREEN
  ↓
AT-15 Integration Acceptance
```

IA should prove the product-shaped Diary/Memory separation path rather than add Memory features.

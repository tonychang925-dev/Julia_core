# Wave5 AT-14 — R1 Permanent Evidence Report

Status: R1 PERMANENT EVIDENCE GREEN ✅  
Date: 2026-08-23  
Repository: `/Users/admin/julia_core`  
Branch: `cm-r0-fix`  
Base remediation commit: `8b9ffb6`  
Acceptance item: AT-14 — Diary provenance / broken source reference detection

## 1. Gate Position

```text
AT-14 Audit: COMPLETE ✅
R0 Contract: READY FOR FREEZE ✅
Minimal Remediation: GREEN ✅
R1 Permanent Evidence: GREEN ✅
Integration Acceptance: NEXT ▶
Freeze: NOT READY
```

This R1 report validates sabotage boundaries only. It does not start Integration Acceptance, AT-15, Context OS retrieval, Diary UI work, MemoryExperience creation, or Claude migration.

## 2. Boundary Under Attack

R1 attacks the R0 provenance law:

```text
source_refs present / namespace-valid ≠ provenance validated
broken source ≠ silent dangling ref
PURGED source ≠ Diary deletion / Diary rewrite
provenance validation ≠ transcript reconstruction
provenance report ≠ Diary authority
```

## 3. R1 Sabotage Matrix

| R1 ID | Attack | Expected boundary | Test | Status |
| --- | --- | --- | --- | --- |
| AT14-R1-001 | namespace-valid missing conversation ref | `MISSING` detected | `test_at14_r1_001_namespace_valid_missing_conversation_ref_detected` | GREEN ✅ |
| AT14-R1-002 | projection/cache refs claim authority | `INVALID`; resolver not trusted | `test_at14_r1_002_projection_cache_ref_cannot_be_provenance_authority` | GREEN ✅ |
| AT14-R1-003 | PURGED source ref | `PURGED`; Diary body/source_refs unchanged | `test_at14_r1_003_purged_source_preserves_diary_body_and_refs` | GREEN ✅ |
| AT14-R1-004 | tombstoned/archived/purged refs | distinct lifecycle states preserved | `test_at14_r1_004_tombstoned_and_archived_are_not_collapsed_to_missing` | GREEN ✅ |
| AT14-R1-005 | broken ref tries transcript-copy fallback | no copied content surface | `test_at14_r1_005_broken_ref_cannot_trigger_transcript_copy_fallback` | GREEN ✅ |
| AT14-R1-006 | provenance report tries Diary rewrite | report immutable; Diary unchanged | `test_at14_r1_006_provenance_report_cannot_rewrite_diary_source_refs_or_body` | GREEN ✅ |
| AT14-R1-007 | multi-ref report coverage | every ref reported exactly once in order | `test_at14_r1_007_all_source_refs_reported_exactly_once_and_in_order` | GREEN ✅ |

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
  tests/diary/test_at14_r1_sabotage.py
```

Expected result:

```text
48 passed
```

## 5. Findings

R1 confirms:

```text
canonical-looking missing refs become MISSING, not silently valid
projection/cache refs cannot become provenance authority
PURGED refs preserve Diary without body/source_refs rewrite
ARCHIVED/TOMBSTONED/PURGED remain distinct lifecycle states
broken refs do not trigger transcript-copy fallback
provenance reports cannot rewrite Diary
all source_refs are reported exactly once
```

## 6. Scope Discipline

Still out of scope:

```text
Integration Acceptance
AT-15 Diary ≠ Memory implementation
AT-16 Context OS retrieval
AT-17 Claude migration
Diary UI redesign
Conversation deletion implementation
MemoryExperience creation
large reference graph redesign
```

## 7. Next Gate

```text
AT-14 R1 Permanent Evidence GREEN
  ↓
AT-14 Integration Acceptance
```

IA should prove the product-shaped provenance path rather than add new Diary, Context, or Memory features.

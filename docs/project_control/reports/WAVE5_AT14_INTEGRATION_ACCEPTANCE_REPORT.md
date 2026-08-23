# Wave5 AT-14 — Integration Acceptance Report

Status: INTEGRATION ACCEPTANCE GREEN / FINAL FREEZE HOLD  
Date: 2026-08-23  
Repository: `/Users/admin/julia_core`  
Branch: `cm-r0-fix`  
Base R1 commit: `a070611`  
Acceptance item: AT-14 — Diary provenance / broken source reference detection

## 1. Gate Position

```text
AT-14 Audit: COMPLETE ✅
R0 Contract: READY FOR FREEZE ✅
Minimal Remediation: GREEN ✅
R1 Permanent Evidence: GREEN ✅
Integration Acceptance: GREEN ✅
Final Freeze Record: NEXT ▶
Freeze: NOT READY
```

This report closes AT-14 Integration Acceptance only. It does not claim the Final Freeze Record and does not start AT-15.

## 2. Integration Path Under Test

IA exercises the product-shaped Diary provenance path:

```text
AcceptedDiaryEntry
  ↓
source_refs
  ↓
ProductSourceResolver / validate_diary_provenance(...)
  ↓
DiarySourceResolution per ref
  ↓
DiaryProvenanceReport
  ↓
explicit lifecycle state without Diary mutation
```

The IA path does not call Diary UI, Context OS retrieval, MemoryExperience creation, Conversation hard-delete implementation, provider generation, or Claude migration.

## 3. IA Test Matrix

| IA ID | Product path | Assertion | Status |
| --- | --- | --- | --- |
| TC-AT14-IA-001 | accepted Diary → resolved conversation source | `RESOLVED` report with exact source ref | GREEN ✅ |
| TC-AT14-IA-002 | accepted Diary → missing source fixture | `MISSING` detected through product-shaped path | GREEN ✅ |
| TC-AT14-IA-003 | accepted Diary → PURGED source → fresh repository | `PURGED` detected; durable Diary unchanged/recovered | GREEN ✅ |
| TC-AT14-IA-004 | accepted Diary with mixed refs | per-ref states preserved, no omission | GREEN ✅ |
| TC-AT14-IA-005 | projection/cache refs in accepted Diary | `INVALID`; no source authority and no content copy | GREEN ✅ |
| TC-AT14-IA-006 | context A/B refs | source resolution isolated by context/ref | GREEN ✅ |

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
  tests/diary/test_at14_ia.py
```

Expected result:

```text
54 passed
```

## 5. Boundary Confirmed

IA confirms:

```text
source_refs present / namespace-valid ≠ provenance validated
broken source ≠ silent dangling ref
PURGED source ≠ Diary deletion / Diary rewrite
provenance validation ≠ transcript reconstruction
projection/cache source_refs ≠ source authority
context A source resolution ≠ context B provenance state
```

## 6. Scope Discipline

Still explicitly out of scope:

```text
AT-15 Diary ≠ Memory implementation
Diary UI redesign
Context OS retrieval/ranking
MemoryExperience creation
Conversation hard-delete implementation
Claude diary migration
provider/LLM reflection generation
large reference graph redesign
```

## 7. Next Gate

```text
AT-14 Integration Acceptance GREEN
  ↓
AT-14 Final Freeze Record
```

Final freeze must preserve:

```text
Reference is not provenance truth.
Missing/broken refs are explicit lifecycle states.
Purged evidence does not erase or rewrite Diary.
Provenance validation never reconstructs transcript authority.
```

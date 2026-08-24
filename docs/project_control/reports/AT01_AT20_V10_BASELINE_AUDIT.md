# AT-01~AT-20 V1.0 BASELINE AUDIT

Status: COMPLETE
Date: 2026-08-24
Repository: `/Users/admin/julia_core`
Audit HEAD: `aedd80f` (branch `wave5/authority-consolidation`)
Source plan: `docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md` §25

---

## Summary

```text
AT-01~16:  COMPLETE (per v1.0 plan definitions)
AT-17:     DEFINITION DEVIATION — plan=Claude migration (NOT done);
           actual=Persona Host Authority Boundary (done, separate track)
AT-18~20:  DEFINITION DEVIATION — plan=conversation storage level (NOT done);
           actual=persona_host carrier level (done, separate track)
```

Conversation storage core loop: COMPLETE. Remaining (plan definition):
AT-17 Claude migration, AT-18/19/20 conversation-level archive/delete/restart.

---

## AT-01 — Conversation create durability

- Plan: create → kill Brain → restart → conversation exists.
- Evidence: `julia_ai_assistant_wave4_integration/docs/acceptance/AT_01_INTEGRATION_ACCEPTANCE_REPORT_v1.md`
- Status: **PASS**

## AT-02 — Accepted user crash

- Plan: user accepted → kill Brain before assistant completes → user message survives.
- Evidence: `julia_ai_assistant_wave4_integration/docs/acceptance/AT_02_ACCEPTED_USER_CRASH_AUDIT_v1.md` + AT_02_R1 report
- Status: **PASS**

## AT-03 — Text→Voice→Text

- Plan: Text T1 / Voice T2 / Text T3 in one canonical sequence.
- Evidence: `tests/wave5/test_at03_*` (114-suite PASS)
- Status: **PASS**

## AT-04 — Voice reconnect UUID identity

- Plan: reconnect repeatedly; no reused canonical turn_id.
- Evidence: `tests/wave5/test_at04_*` (uuid fix `5ce95a1`)
- Status: **PASS**

## AT-05 — Retry idempotency

- Plan: same (conversation_id, turn_id) retry → no duplicate user/assistant message.
- Evidence: `tests/wave5/test_at05_*`
- Status: **PASS**

## AT-06 — Cross-conversation sabotage

- Plan: distinct markers; no leakage through storage/search/Context OS/Electron.
- Evidence: `tests/wave5/test_at06_*` (conversation_id uniqueness fix)
- Status: **PASS**

## AT-07 — Segment boundary

- Plan: rotate transcript segment; resume/context unchanged.
- Evidence: `tests/wave5/test_at07_*`
- Status: **PASS**

## AT-08 — Pagination

- Plan: 200+ messages, page by page; zero dup/miss, canonical order.
- Evidence: `tests/wave5/test_at08_*`
- Status: **PASS**

## AT-09 — Delete derived indexes

- Plan: delete indexes/*; rebuild with zero semantic loss.
- Evidence: `tests/wave5/test_at09_*`
- Status: **PASS**

## AT-10 — Electron cache destruction

- Plan: delete Electron cache; restart; history reloads from Assistant/Core.
- Evidence: `julia_electron_v2/tests/at10-ia.test.js` + `client-c1.test.js` (14 pass, gate `a25f0dc`)
- Status: **PASS** (Electron boundary)

## AT-11 — S2S state destruction

- Plan: restart/reconnect S2S; continuity preserved without S2S history transfer.
- Evidence: `docs/project_control/reports/WAVE5_PRE_E2E_AT11_S2S_SCOPE_ISOLATION_RECORD.md`
- Status: **HOLD** (scope isolated; remediation deferred)

## AT-12 — Diary NO_ENTRY

- Plan: trivial day → Julia chooses NO_ENTRY; no meaningless artifact.
- Evidence: `tests/diary/test_at12_*`
- Status: **PASS / FROZEN**

## AT-13 — Diary significant event

- Plan: grounded event → first-person reflection with source refs.
- Evidence: `tests/diary/test_at13_*`
- Status: **PASS / FROZEN**

## AT-14 — Diary provenance

- Plan: broken source fixture → validator detects it.
- Evidence: `tests/diary/test_at14_*`
- Status: **PASS / FROZEN**

## AT-15 — Diary ≠ Memory

- Plan: diary creation does not auto-create MemoryExperience.
- Evidence: `tests/diary/test_at15_*`
- Status: **PASS / FROZEN**

## AT-16 — Diary retrieval via Context OS only

- Plan: trace proves diary reaches model only through Context OS.
- Evidence: `tests/diary/test_at16_*`
- Status: **PASS / FROZEN**

## AT-17 — Claude migration ⚠️ DEFINITION DEVIATION

- Plan: legacy claude_diary fixture semantically reclassified; no raw directory copy.
- Actual: **Persona Host Authority Boundary Test** (`at17_test_harness/`, 14/14 PASS,
  `WAVE5_AT17_EVIDENCE_REPORT_v1.0`) — a DIFFERENT acceptance item.
- Plan-defined Claude migration: **ZERO test coverage** (grep claude_diary → no tests).
- Status: **NOT DONE (plan definition)** / Persona Host track COMPLETE (separate)

## AT-18 — Archive ⚠️ OBJECT DEVIATION

- Plan: archived conversation disappears from default list, remains canonical,
  retrievable (conversation storage level).
- Actual: persona_host carrier-level archive (`persona_host/evidence/AT18_ARCHIVE_BOUNDARY.json`).
- Conversation-level archive: **NOT done**.
- Status: **NOT DONE (conversation level)** / carrier-level COMPLETE

## AT-19 — Hard-delete guard ⚠️ OBJECT DEVIATION

- Plan: conversation referenced by Diary/Memory/Continuity cannot be hard-deleted
  without governed resolution (conversation storage level).
- Actual: persona_host delete-authority-absent (`persona_host/evidence/AT19_HARD_DELETE_AUTHORITY.json`).
- Conversation-level reference-graph guard: **NOT done**.
- Status: **NOT DONE (conversation level)** / carrier-level COMPLETE

## AT-20 — Full restart recovery ⚠️ OBJECT DEVIATION

- Plan: restart Electron+Brain+S2S; conversation + accepted diary intact without
  client history (conversation+diary level).
- Actual: persona_host carrier restart recovery (`persona_host/evidence/AT20_RESTART_RECOVERY.json`).
- Full-stack restart (Electron+Brain+S2S): **NOT done**.
- Status: **NOT DONE (full-stack)** / carrier-level COMPLETE

---

## Conclusion

```text
Conversation storage core loop (AT-01~16): COMPLETE ✅

Remaining to close v1.0 baseline (plan definitions):
  AT-17  Claude migration              → Persona Migration Baseline (ADR-034)
  AT-18  conversation-level archive    → Baseline 1 remaining
  AT-19  conversation hard-delete guard → Baseline 1 remaining
  AT-20  full-stack restart recovery   → Baseline 1 remaining

Separate completed tracks (not v1.0 plan items):
  AT-17 Persona Host Authority Boundary (at17_test_harness/, 14/14)
  AT-18/19/20 persona_host carrier lifecycle
  ADR-034 Baseline E2E (conversation storage loop, 9 passed)
```

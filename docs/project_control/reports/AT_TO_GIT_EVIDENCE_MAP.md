# AT → GIT EVIDENCE MAP（四者关联：baseline 文档 / commit / 测试路径 / 分支）

Status: VERIFIED FROM LOCAL GIT (2026-08-24)
Local truth branch: `wave5/authority-consolidation` @ `22043f7`
Note: this branch is NOT pushed to GitHub — local is the canonical source.

---

## Baseline document

| Item | Value |
|---|---|
| Document | `docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md` |
| Introduced | commit `507ebda` (STO-A0-CLOSEOUT: freeze ADR-033) |
| Tracked in | `wave5/authority-consolidation` (and cm-r0-fix, codex/* local branches) |
| On GitHub | NOT found (not on any visible remote ref) |

## AT evidence map

| AT | Test file (tracked) | Introduced commit | Branch |
|---|---|---|---|
| AT-01 | `julia_ai_assistant_wave4_integration/tests/test_at01_conversation_create_durability_r1.py` | `166d899` | `wave4/integration-base` |
| AT-02 | `julia_ai_assistant_wave4_integration/tests/test_at02_accepted_user_crash_r1.py` | `4a4e100` | `wave4/integration-base` |
| AT-03 | `tests/wave5/test_at03_text_voice_text.py` | `61b6ce0` | `wave5/authority-consolidation` |
| AT-04 | `tests/wave5/test_at04_voice_reconnect_uuid_identity.py` | (AT-04 evidence commits) | `wave5/authority-consolidation` |
| AT-05 | `tests/wave5/test_at05_retry_idempotency.py` | `2b264aa` | `wave5/authority-consolidation` |
| AT-06 | `tests/wave5/test_at06_cross_conversation_sabotage.py` | `70b4ae1` | `wave5/authority-consolidation` |
| AT-07 | `tests/wave5/test_at07_segment_boundary.py` | (AT-07 evidence commits) | `wave5/authority-consolidation` |
| AT-08 | `tests/wave5/test_at08_pagination.py` | `f252bfd` | `wave5/authority-consolidation` |
| AT-09 | `tests/wave5/test_at09_delete_derived_indexes.py` | (AT-09 evidence commits) | `wave5/authority-consolidation` |
| AT-10 | `julia_electron_v2/tests/at10-ia.test.js` | (Electron AT10- suite) | `codex/bugfix/at10-electron-cache-boundary` |
| AT-11 | `docs/project_control/reports/WAVE5_PRE_E2E_AT11_S2S_SCOPE_ISOLATION_RECORD.md` | (S2S scope isolation) | HOLD (isolated) |
| AT-12 | `tests/diary/test_at12_no_entry.py` | `7ac2dbe` | `cm-r0-fix` / consolidated |
| AT-13 | `tests/diary/test_at13_minimal_remediation.py` | `24e8224` | `cm-r0-fix` |
| AT-14 | `tests/diary/test_at14_minimal_remediation.py` | `8b9ffb6` | `cm-r0-fix` |
| AT-15 | `tests/diary/test_at15_minimal_remediation.py` | `0e6c18d` | `cm-r0-fix` |
| AT-16 | `tests/diary/test_at16_minimal_remediation.py` | `00b964e` | `cm-r0-fix` |
| AT-17 | `tests/wave5/test_at17_claude_migration.py` | `22043f7` | `wave5/authority-consolidation` |
| AT-18 | `tests/wave5/test_at18_conversation_archive.py` | `22043f7` | `wave5/authority-consolidation` |
| AT-19 | `tests/wave5/test_at19_hard_delete_guard.py` | `22043f7` | `wave5/authority-consolidation` |
| AT-20 | — | — | NOT DONE (per Tony, 2026-08-24) |

## Suite verification (local, reproducible)

```bash
cd /Users/admin/julia_core
PYTHONPATH=. /opt/miniconda3/bin/python -m pytest tests/wave5/ -q        # 114+ → currently 160 passed incl. baseline E2E
PYTHONPATH=. /opt/miniconda3/bin/python -m pytest tests/diary/ -q        # 96 passed
```

## Conclusion

Every AT claim maps to a tracked test file, an introducing commit, and a
branch. Local `wave5/authority-consolidation` @ `22043f7` is the canonical
truth. GitHub API cannot verify these because the branch is not pushed.

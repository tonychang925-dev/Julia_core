# Quality Gate Policy — Wave5 Acceptance / Freeze

Source plan: `docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md`

Wave5 scope: execute AT-01…AT-20. Freeze is allowed only after every acceptance test and invariant check passes with reproducible evidence.

## 1. Definition of Done (DoD)

- [ ] Functionality from Wave0…Wave4 is merged into the intended feature/release branch.
- [ ] Unit/integration/acceptance tests are present and mapped to AT-01…AT-20.
- [ ] Critical paths are covered: canonical conversation storage, management API/UI projection, migration/cutover, diary governance, source refs, restart recovery.
- [ ] No open P0/P1 defect remains.
- [ ] Documentation and ADR/freeze notes are updated.
- [ ] Rollback plan is documented for persistence root, migration activation, archive/delete governance, and diary persistence.
- [ ] Any data structure change has a migration/verification path.
- [ ] Any interface change has compatibility behavior documented.

## 2. Required Checks

### 2.1 Baseline repository checks

```bash
cd /Users/admin/julia_core
python -m pytest -q
```

If repository uses the checked-in virtualenv:

```bash
cd /Users/admin/julia_core
./.venv/bin/python -m pytest -q
```

Pass criteria:

- all tests pass;
- no skipped Wave5-critical test;
- no flaky rerun required for PASS.

### 2.2 Lint / static checks

Run available project linters if installed/configured:

```bash
cd /Users/admin/julia_core
ruff check .
python -m compileall julia_core tests
```

Pass criteria:

- zero lint errors for release code;
- Python files compile successfully.

### 2.3 Wave5 acceptance suite

Every AT item below must have either an automated test ID or a documented manual/e2e execution record in `docs/project_control/reports/wave5-acceptance.md`.

| AT | Required evidence | PASS condition |
|---|---|---|
| AT-01 Conversation create durability | create → kill Brain → restart log | conversation exists after restart |
| AT-02 Accepted user crash | crash after accepted user append | user message survives |
| AT-03 Text→Voice→Text | unified conversation trace | one canonical ordered sequence |
| AT-04 Voice reconnect UUID identity | reconnect trace | no reused canonical `turn_id` |
| AT-05 Retry idempotency | repeated `(conversation_id, turn_id)` | no duplicate user/assistant message |
| AT-06 Cross-conversation sabotage | A/B distinct marker test | no leakage via storage/search/Context/Electron |
| AT-07 Segment boundary | forced transcript rotation | resume/context unchanged |
| AT-08 Pagination | 200+ message pagination | zero duplicate/missing; canonical order |
| AT-09 Delete derived indexes | remove `indexes/*`, rebuild | semantic data intact |
| AT-10 Electron cache destruction | delete client cache, restart | history reloads from Assistant/Core |
| AT-11 S2S state destruction | restart/reconnect S2S | completed continuity preserved |
| AT-12 Diary NO_ENTRY | trivial reflection trigger | no meaningless diary artifact |
| AT-13 Diary significant event | grounded meaningful event | first-person entry with source refs |
| AT-14 Diary provenance | broken source fixture | validator detects missing source |
| AT-15 Diary ≠ Memory | diary creation trace | no automatic MemoryExperience |
| AT-16 Diary via Context OS only | context assembly trace | diary enters model only via Context OS |
| AT-17 Claude migration | legacy fixture migration | semantic reclassification, no raw copy |
| AT-18 Archive | archive/list/retrieve trace | hidden by default, canonical remains |
| AT-19 Hard-delete guard | referenced conversation delete attempt | governed block/resolution required |
| AT-20 Full restart recovery | restart Electron + Brain + S2S | conversation + diary intact without client history |

## 3. Freeze Decision Rules

- If AT-01…AT-20 all pass: `Acceptance Gate: Passed`; freeze candidates may be marked locked.
- If any AT fails or lacks evidence: `Acceptance Gate: Failed`.
- No partial freeze is allowed for the listed Wave5 baseline unless a written carve-out is approved and references the exact failed AT ID.

## 4. Evidence Format

Each execution report must include:

```text
Date:
Branch / commit:
Environment:
Command(s):
Key output:
AT mapping:
Result: PASS | FAIL
Defects opened:
Retest command(s):
```

## 5. Failure Handling

For every failed check:

1. Triage: code defect / test defect / dependency / environment / data migration / architecture drift.
2. Root cause: identify affected component and invariant.
3. Minimal fix only; no unrelated refactor.
4. Re-run the failed AT and the baseline repository checks.
5. Append evidence to `docs/project_control/reports/wave5-acceptance.md`.

## 6. Wave5 Freeze Checklist

- [ ] Conversation Storage Baseline frozen.
- [ ] Conversation Management frozen.
- [ ] Julia Diary v1 frozen.
- [ ] Private Filesystem Contract frozen.
- [ ] Full AT-01…AT-20 regression passes.

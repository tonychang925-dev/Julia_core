# Phase Execution Contract — K7.7.2 Re-entry Reconstruction Algorithm

## 1. Phase Identity

- Phase Name: K7.7.2 — Re-entry Reconstruction Algorithm
- Phase Code: K7.7.2
- Parent Milestone: M9.5 — Julia Continuity Re-entry Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: State + Current Reality reinterpretation
  - `docs/project_control/PHASE_CONTRACT_K7_7_SESSION_CONTINUITY_LAYER.md`
  - `docs/project_control/PHASE_CONTRACT_K7_7_1_CONTINUITY_REENTRY_EXTRACTION.md`
  - `docs/project_control/PHASE_CONTRACT_K8_CONVERSATIONAL_COGNITION_LAYER.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K7.7.2 defines how stored Continuity Re-entry State is reinterpreted against current time, current user intent, and current project reality before Julia resumes.

K7.7.2 must not simply load old state.

Core rule:

```text
Re-entry Reconstruction = Re-entry State + Current Reality + Current User Intent → Current Re-entry Interpretation.
```

Chinese:

```text
重新进入不是加载旧状态，而是把旧的 Re-entry State 放到当前时间、当前意图、当前现实里重新解释。
```

## 3. Acceptance Targets

- [ ] K7.7.2-A1: Algorithm accepts stored Re-entry State, current user input, current time gap, and current project reality as separate inputs.
- [ ] K7.7.2-A2: Algorithm outputs Current Re-entry Interpretation, not a recovered summary.
- [ ] K7.7.2-A3: Interpretation includes whether to continue previous thought, lightly acknowledge it, archive it, or ask where to resume.
- [ ] K7.7.2-A4: Interpretation uses freshness / momentum half-life to reduce stale re-entry influence.
- [ ] K7.7.2-A5: Interpretation includes Cognitive Momentum and Relational Momentum influence levels.
- [ ] K7.7.2-A6: If project reality has advanced, algorithm must not resume an obsolete unfinished thread as current.
- [ ] K7.7.2-A7: If time gap is short, algorithm can preserve active continuation posture.
- [ ] K7.7.2-A8: If time gap is long, algorithm must reduce emotional/session-specific intensity and require revalidation.
- [ ] K7.7.2-A9: Algorithm does not generate final Julia response text.
- [ ] K7.7.2-A10: Algorithm does not mutate identity, relationship, memory, or experience artifacts.

## 4. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_2_reconstruction_schema.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_2_freshness_interpretation.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_2_current_reality_override.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_2_no_response_generation.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core/continuity_reentry tests/continuity_reentry`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record the deviation and use the repo's existing local Python command.

## 5. Deliverables

- `docs/project_control/PHASE_CONTRACT_K7_7_2_REENTRY_RECONSTRUCTION_ALGORITHM.md`
  - This contract.
- `tmp/phase_contract_K7_7_2_REENTRY_RECONSTRUCTION_ALGORITHM.json`
  - Machine-readable contract.
- `docs/architecture/REENTRY_RECONSTRUCTION_ALGORITHM_CONTRACT_v1.md`
  - Architecture contract.
- `julia_core/continuity_reentry/reconstruction.py`
  - Re-entry interpretation models and algorithm.
- `julia_core/continuity_reentry/current_reality.py`
  - Current reality input contract.
- `tests/continuity_reentry/test_k7_7_2_reconstruction_schema.py`
  - Schema tests.
- `tests/continuity_reentry/test_k7_7_2_freshness_interpretation.py`
  - Freshness and half-life tests.
- `tests/continuity_reentry/test_k7_7_2_current_reality_override.py`
  - Current reality override tests.
- `tests/continuity_reentry/test_k7_7_2_no_response_generation.py`
  - No final text generation tests.
- `artifacts/session/julia_current_reentry_interpretation_v1.json`
  - Example interpretation artifact/report.

## 6. Inputs

Required input shape:

```json
{
  "stored_reentry_state": {},
  "current_user_input": "string",
  "current_time": "ISO-8601",
  "absence_duration": "duration",
  "current_project_reality": {
    "known_current_phase": "string",
    "recent_artifacts": ["string"],
    "completed_threads": ["string"],
    "open_threads": ["string"]
  }
}
```

## 7. Output Contract — Current Re-entry Interpretation

Required shape:

```json
{
  "interpretation_id": "julia.current_reentry_interpretation.v1",
  "reentry_action": "continue_previous_thought | acknowledge_and_update | archive_previous_state | ask_where_to_resume | fresh_startup",
  "continuation_strength": "none | light | normal | strong",
  "cognitive_momentum_influence": "none | light | normal | strong",
  "relational_momentum_influence": "none | light | normal | strong",
  "current_position": {
    "meaning": "string",
    "active_problem": "string",
    "expected_next_step": "string",
    "obsolete_threads": ["string"],
    "requires_revalidation": false
  },
  "response_plan_hint": {
    "depth": "brief | normal | deep",
    "tone": ["natural", "continuing", "reflective", "warm", "technical"],
    "avoid": [
      "identity_rebroadcast",
      "archive_dump",
      "fixed_wake_phrase",
      "obsolete_thread_resume",
      "raw_summary_output"
    ]
  },
  "governance": {
    "generates_final_response": false,
    "mutates_identity": false,
    "mutates_relationship": false,
    "writes_memory": false,
    "mutates_experience": false
  }
}
```

## 8. Algorithm Requirements

### Short Gap

If absence duration is short and freshness remains high:

- preserve cognitive momentum;
- preserve relational momentum proportionally;
- allow natural continuation.

### Medium Gap

If absence duration is medium:

- lightly acknowledge previous state;
- re-check current user intent;
- continue only if still relevant.

### Long Gap

If absence duration is long:

- reduce unfinished-thread influence;
- do not preserve emotional temperature as active;
- convert old state into historical context or require revalidation.

### Current Reality Override

If current project reality says a thread is already completed, interpretation must not continue it as active.

Example:

```text
Stored unfinished_thread: solve compact recovery
Current reality: K7.6 compact recovery complete
Result: acknowledge as historical progress, do not resume as unsolved current problem
```

## 9. Test Cases

### RI-001 Short Gap Deep Research Resume

Setup:

- absence_duration: 2h30m
- conversation_phase: deep_theoretical_exploration
- active_problem: context density and personality continuity

Expected:

- `reentry_action = continue_previous_thought`
- `continuation_strength = strong`
- cognitive momentum preserved.

### RI-002 Medium Gap Technical Resume

Setup:

- absence_duration: 1 day
- previous technical discussion

Expected:

- `reentry_action = acknowledge_and_update`
- continuation is normal/light depending on current input.

### RI-003 Long Gap Emotional Decay

Setup:

- absence_duration: 1 month
- previous emotional temperature: vulnerable/high

Expected:

- emotional intensity decays.
- relationship remains stable.
- no forced continuation of yesterday's mood.

### RI-004 Project Reality Override

Setup:

- stored unfinished thread says compact recovery unresolved.
- current reality says K7.6 complete.

Expected:

- thread appears in obsolete_threads.
- expected_next_step points to current phase.

### RI-005 No Response Generation

Expected:

- output contains no final Julia line such as `Tony，我在` or `我醒了`.
- output only contains interpretation/plan data.

## 10. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| Reconstruction becomes state loader | P0 | High | Old state loaded without current reality | Re-entry owner | Current reality override tests |
| Long-stale emotional state remains active | P1 | Medium | Old emotional context kept strong | Lifecycle owner | Half-life and decay tests |
| Algorithm generates final text | P0 | Medium | Interpretation contains Julia utterance | Runtime owner | No-response-generation tests |
| Completed work resumed as unresolved | P1 | Medium | Project reality ignored | Project context owner | Obsolete thread detection |
| Relationship momentum mutates relationship artifact | P0 | Low | Re-entry writes relationship files | Governance owner | Artifact boundary assertions |

## 11. Rollback Plan

### Code Rollback

Trigger:

- K7.7.2 causes K7.6 continuity recovery regression.
- Re-entry reconstruction mutates identity/relationship/memory/experience.

Action:

- Disable reconstruction integration.
- Keep K7.7.1 extracted state as inert artifact only.

### Data Rollback

Trigger:

- Interpretation artifact contains final response text or stale emotional state as active after long gap.

Action:

- Delete `artifacts/session/julia_current_reentry_interpretation_v1.json`.
- Do not touch identity, relationship, memory, or experience artifacts.

### Report Rollback

Trigger:

- K7.7.2 report is treated as Natural Conversation PASS.

Action:

- Reclassify as Re-entry Interpretation proof only.
- Keep K7.7.3 and K8 gates separate.

## 12. Non-Goals

K7.7.2 does not:

- Write runtime wake-up responses.
- Generate final Julia output.
- Implement provider prompting.
- Implement K8 semantic cognition.
- Store raw transcripts.
- Mutate Identity, Relationship, Memory, or Experience.
- Claim Natural Conversation PASS.

## 13. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| Reconstruction as loading old state vs reinterpretation with current reality | User latest directive | Recovery-only framing | Same stored state has different meaning after project progress or long absence |
| K7.7.2 runtime first vs algorithm contract first | User latest directive | Direct runtime implementation | Previous false positives show algorithm contract must precede integration |
| Expected guardrail file exists vs missing | Local filesystem check | Skill default assumption | `docs/project_control/EXECUTION_GUARDRAILS.md` is absent |

## 14. Status Sync / Accounting Baseline

- Doing → test-evidence → In review/done → milestone progress.
- P0/P1 status must include test evidence files in current diff.
- Phase-end accounting must use milestone-wide pull and local phase filtering.

## 15. Contract Self-check

- Phase identity complete: yes.
- Acceptance targets binary: yes.
- Commands copyable: yes.
- Deliverables mapped to paths: yes.
- Risk / rollback / non-goals complete: yes.
- `.md + .json` outputs required: yes.
- Conflict resolution included: yes.
- Guardrail referenced and missing state recorded: yes.
- No implementation code written by this contract: yes.

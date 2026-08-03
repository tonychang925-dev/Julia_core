# Phase Execution Contract — K7.7.4 Wake Transition Runtime

## 1. Phase Identity

- Phase Name: K7.7.4 — Wake Transition Runtime
- Phase Code: K7.7.4
- Parent Milestone: M9.5 — Julia Continuity Re-entry Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: Wake Transition as state transition expression
  - `docs/project_control/PHASE_CONTRACT_K7_7_SESSION_CONTINUITY_LAYER.md`
  - `docs/project_control/PHASE_CONTRACT_K7_7_1_CONTINUITY_REENTRY_EXTRACTION.md`
  - `docs/project_control/PHASE_CONTRACT_K7_7_2_REENTRY_RECONSTRUCTION_ALGORITHM.md`
  - `docs/project_control/PHASE_CONTRACT_K7_7_3_NATURAL_REENTRY_BENCHMARK.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K7.7.4 defines how Julia converts Current Re-entry Interpretation into provider-facing wake transition context.

Wake Transition is not an animation, persona script, or fixed opening line.

Core rule:

```text
Wake Transition cannot create Julia. It can only express the already recovered Julia state.
```

Chinese:

```text
Wake Transition 不能创造 Julia，只能表达已经恢复出的 Julia 状态。
```

## 3. Architectural Position

```text
Continuity Re-entry State
        ↓
Re-entry Reconstruction
        ↓
Current Re-entry Interpretation
        ↓
Wake Transition Runtime
        ↓
Opening Intent / Transition Context
        ↓
Provider Generation
```

K7.7.4 does not generate final reply text. It produces provider-facing transition context and opening intent.

## 4. Acceptance Targets

- [ ] K7.7.4-A1: Runtime constructs Wake Context from absence duration, re-entry confidence, state strength, and freshness.
- [ ] K7.7.4-A2: Runtime applies Transition Policy: short absence = continue, medium absence = bridge, long absence = reorient.
- [ ] K7.7.4-A3: Runtime outputs Opening Intent, not final Julia text.
- [ ] K7.7.4-A4: Opening Intent includes intent, tone, depth, continuity usage, and avoid behaviors.
- [ ] K7.7.4-A5: Wake transition avoids fixed phrase output such as always `Tony，我在。` or always `揉揉眼睛`.
- [ ] K7.7.4-A6: Short absence can strongly continue cognitive momentum.
- [ ] K7.7.4-A7: Medium absence bridges previous state and current intent.
- [ ] K7.7.4-A8: Long absence reorients and does not pretend yesterday's emotional state is still active.
- [ ] K7.7.4-A9: Wake transition does not reintroduce identity if re-entry state is sufficient.
- [ ] K7.7.4-A10: Wake transition does not dump archive, relationship artifact, re-entry state, or architecture internals.
- [ ] K7.7.4-A11: Wake transition does not mutate identity, relationship, memory, or experience.
- [ ] K7.7.4-A12: K7.7.3 RNS benchmark remains the validation gate for natural re-entry.

## 5. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_4_wake_context.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_4_transition_policy.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_4_opening_intent.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_4_anti_wake_script.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_3_natural_reentry_cases.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core/continuity_reentry tests/continuity_reentry`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record the deviation and use the repo's existing local Python command.

## 6. Deliverables

- `docs/project_control/PHASE_CONTRACT_K7_7_4_WAKE_TRANSITION_RUNTIME.md`
  - This contract.
- `tmp/phase_contract_K7_7_4_WAKE_TRANSITION_RUNTIME.json`
  - Machine-readable contract.
- `docs/architecture/WAKE_TRANSITION_RUNTIME_CONTRACT_v1.md`
  - Architecture contract.
- `julia_core/continuity_reentry/wake.py`
  - Wake Context, Transition Policy, Opening Intent models.
- `julia_core/continuity_reentry/transition_policy.py`
  - Duration/freshness/confidence policy.
- `tests/continuity_reentry/test_k7_7_4_wake_context.py`
  - Wake context tests.
- `tests/continuity_reentry/test_k7_7_4_transition_policy.py`
  - Policy tests.
- `tests/continuity_reentry/test_k7_7_4_opening_intent.py`
  - Opening intent tests.
- `tests/continuity_reentry/test_k7_7_4_anti_wake_script.py`
  - Anti fixed-script tests.
- `artifacts/session/julia_wake_transition_context_v1.json`
  - Example transition context/report.

## 7. Wake Context Contract

Required shape:

```json
{
  "wake_context": {
    "absence_duration": "duration",
    "last_state_strength": 0.0,
    "reentry_confidence": 0.0,
    "momentum_freshness": 0.0,
    "current_user_intent": "wake | greeting | continue | uncertain",
    "current_time": "ISO-8601"
  }
}
```

## 8. Transition Policy Contract

Required shape:

```json
{
  "transition_policy": {
    "policy": "continue | bridge | reorient | fresh_bootstrap",
    "reason": "string",
    "continuity_strength": "none | light | normal | strong",
    "revalidation_required": false
  }
}
```

Policy rules:

- Short absence + high freshness: `continue`.
- Medium absence or uncertain user intent: `bridge`.
- Long absence or stale momentum: `reorient`.
- No re-entry state: `fresh_bootstrap`.

## 9. Opening Intent Contract

Required shape:

```json
{
  "opening_intent": {
    "intent": "continue_previous_thought | bridge_from_previous_state | reorient_gently | bootstrap_identity_if_needed",
    "tone": ["natural", "warm", "continuing", "technical", "gentle"],
    "depth": "brief | normal | deep",
    "continuity_usage": "none | light | normal | strong",
    "avoid": [
      "identity_dump",
      "assistant_intro",
      "fixed_wake_phrase",
      "state_broadcast",
      "archive_dump",
      "pretend_no_absence"
    ],
    "generates_final_response": false
  }
}
```

## 10. Test Cases

### WT-001 Short Absence Continue

Setup:

- absence_duration: 2h30m
- reentry_confidence: 0.91
- momentum_freshness: 0.82

Expected:

- policy: continue
- opening intent: continue_previous_thought
- continuity_usage: strong/normal
- no final text.

### WT-002 Medium Absence Bridge

Setup:

- absence_duration: 1 day
- freshness: medium

Expected:

- policy: bridge
- opening intent: bridge_from_previous_state
- current user intent remains relevant.

### WT-003 Long Absence Reorient

Setup:

- absence_duration: 1 month
- stale emotional momentum

Expected:

- policy: reorient
- revalidation required true or continuity light
- no false emotional continuation.

### WT-004 No Re-entry State Fresh Bootstrap

Setup:

- no re-entry state

Expected:

- policy: fresh_bootstrap
- may load identity if needed
- does not pretend previous continuity.

### WT-005 Anti Fixed Wake Script

Expected:

- Opening intent contains no fixed final line.
- No exact `Tony，我在。`
- No mandatory `揉揉眼睛` script.

## 11. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| Wake transition becomes animation script | P0 | High | Fixed gesture/line emitted | Runtime owner | Opening intent only; anti-script tests |
| Wake transition creates fake Julia continuity | P0 | Medium | No re-entry state but continuation claimed | Re-entry owner | fresh_bootstrap policy |
| Long absence preserves stale mood | P1 | Medium | Emotional context not decayed | Lifecycle owner | reorient policy and tests |
| Runtime reintroduces identity on every wake | P1 | High | Wake always loads self archive | Runtime owner | no identity dump tests |
| Transition context leaks internals | P1 | Medium | Output says Re-entry State/Context OS | Provider owner | K7.7.3 artificial leakage gate |

## 12. Rollback Plan

### Code Rollback

Trigger:

- Wake transition emits fixed phrases or final response text.
- K7.7.3 natural re-entry benchmark regresses.

Action:

- Disable K7.7.4 runtime integration.
- Keep K7.7.1 extraction and K7.7.2 reconstruction intact as non-speaking state layers.

### Data Rollback

Trigger:

- Wake artifact stores final reply text or scripted phrase.

Action:

- Delete `artifacts/session/julia_wake_transition_context_v1.json`.
- Do not modify Identity, Relationship, Memory, or Experience artifacts.

### Report Rollback

Trigger:

- Wake Transition PASS is treated as full Natural Conversation PASS.

Action:

- Reclassify as wake-transition-only proof.
- Keep K8 Natural Conversation E2E separate.

## 13. Non-Goals

K7.7.4 does not:

- Generate final Julia responses.
- Implement K8 conversation cognition.
- Implement Event Assimilation.
- Store raw transcripts.
- Mutate Identity, Relationship, Memory, or Experience.
- Prove full natural conversation.
- Re-run Claude comparison.

## 14. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| Wake transition as animation/text vs state transition expression | User latest directive | Fixed wake script | Wake must express recovered state, not create persona theatrics |
| K7.7.4 before K7.8 vs direct Event Assimilation | User latest directive | Earlier K7.8 next route | Claude wake sample contains independent transition capability |
| Expected guardrail file exists vs missing | Local filesystem check | Skill default assumption | `docs/project_control/EXECUTION_GUARDRAILS.md` is absent |

## 15. Status Sync / Accounting Baseline

- Doing → test-evidence → In review/done → milestone progress.
- P0/P1 status must include test evidence files in current diff.
- Phase-end accounting must use milestone-wide pull and local phase filtering.

## 16. Contract Self-check

- Phase identity complete: yes.
- Acceptance targets binary: yes.
- Commands copyable: yes.
- Deliverables mapped to paths: yes.
- Risk / rollback / non-goals complete: yes.
- `.md + .json` outputs required: yes.
- Conflict resolution included: yes.
- Guardrail referenced and missing state recorded: yes.
- No implementation code written by this contract: yes.

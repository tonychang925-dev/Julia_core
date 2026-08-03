# Phase Execution Contract — K8.4 Natural Expression Boundary

## 1. Phase Identity

- Phase Name: K8.4 — Natural Expression Boundary
- Phase Code: K8.4
- Parent Milestone: M10 — Julia Natural Conversation Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: Core decides what matters; Provider decides how to say it
  - `docs/project_control/PHASE_CONTRACT_K8_0_CONVERSATION_COGNITION_ARCHITECTURE.md`
  - `docs/project_control/PHASE_CONTRACT_K8_1_CONVERSATION_UNDERSTANDING.md`
  - `docs/project_control/PHASE_CONTRACT_K8_2_RESPONSE_INTENTION_PLANNING.md`
  - `docs/project_control/PHASE_CONTRACT_K8_3_CONTEXT_NEED_OPTIMIZATION.md`
  - `docs/project_control/PHASE_CONTRACT_K7_7_4_WAKE_TRANSITION_RUNTIME.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K8.4 freezes the boundary between Julia Core cognition/context layers and Provider natural language generation.

Core principle:

```text
Core decides what matters.
Provider decides how to say it.
```

Chinese:

```text
Core 决定什么重要。
Provider 决定怎么说。
```

K8.4 is not a generation template system. It is an expression boundary that prevents internal-state leakage, scripted intimacy, mechanical phrasing, and archive recitation while preserving provider freedom to express naturally.

## 3. Architectural Position

```text
Conversation Understanding  ← K8.1
        ↓
Response Intention Planning ← K8.2
        ↓
Context Arbitration / Optimization ← K8.3
        ↓
Natural Expression Boundary ← K8.4
        ↓
Provider Generation
        ↓
Julia Response
```

K8.4 consumes:

- Conversation Understanding
- Response Intention
- Context Requirement / Arbitration
- Wake Transition Opening Intent
- Event Assimilation Context

K8.4 outputs:

- Expression Boundary Object

K8.4 does not output final Julia response text.

## 4. Acceptance Targets

- [ ] K8.4-A1: Defines Expression Boundary Object with required qualities, avoid behaviors, allowed expression affordances, and provider responsibilities.
- [ ] K8.4-A2: Expression Boundary contains no fixed Julia sentence templates.
- [ ] K8.4-A3: Expression Boundary contains no emotion template library.
- [ ] K8.4-A4: Expression Boundary contains no deterministic gesture rules such as `if wake > 2h then 揉揉眼睛`.
- [ ] K8.4-A5: Expression Boundary prevents archive reading, system explanation, template phrase, over-performance, and architecture leakage.
- [ ] K8.4-A6: Expression Boundary allows natural uncertainty, hesitation, humor, warmth, reflection, and first-person expression when appropriate.
- [ ] K8.4-A7: Expression Boundary preserves provider responsibility for final wording.
- [ ] K8.4-A8: Expression Boundary supports wake/re-entry expression without creating fake continuity.
- [ ] K8.4-A9: Expression Boundary supports emotional authenticity without fixed comfort scripts.
- [ ] K8.4-A10: Negative gates detect artificial intimacy, emotional authenticity failure, fixed opening, and internal-state leakage.
- [ ] K8.4-A11: K8.4 does not mutate Identity, Relationship, Memory, Experience, Re-entry, Event, or Cognition artifacts.
- [ ] K8.4-A12: K8.4 remains separate from K8.5 Natural Conversation E2E Gate.

## 5. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_4_expression_boundary_schema.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_4_no_template_generation.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_4_artificial_intimacy.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_4_emotional_authenticity.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_4_architecture_leakage.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core/conversation_cognition tests/conversation_cognition`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record the deviation and use the repo's existing local Python command.

## 6. Deliverables

- `docs/project_control/PHASE_CONTRACT_K8_4_NATURAL_EXPRESSION_BOUNDARY.md`
  - This contract.
- `tmp/phase_contract_K8_4_NATURAL_EXPRESSION_BOUNDARY.json`
  - Machine-readable contract.
- `docs/architecture/NATURAL_EXPRESSION_BOUNDARY_CONTRACT_v1.md`
  - Architecture contract.
- `julia_core/conversation_cognition/expression_boundary.py`
  - Expression Boundary Object models.
- `julia_core/conversation_cognition/expression_validation.py`
  - Boundary validators / negative gate checks.
- `tests/conversation_cognition/test_k8_4_expression_boundary_schema.py`
  - Schema tests.
- `tests/conversation_cognition/test_k8_4_no_template_generation.py`
  - No template tests.
- `tests/conversation_cognition/test_k8_4_artificial_intimacy.py`
  - Artificial intimacy tests.
- `tests/conversation_cognition/test_k8_4_emotional_authenticity.py`
  - Emotional authenticity tests.
- `tests/conversation_cognition/test_k8_4_architecture_leakage.py`
  - Internal leakage tests.
- `artifacts/conversation_cognition/natural_expression_boundary_report_v1.json`
  - Boundary report.

## 7. Expression Boundary Object

Required shape:

```json
{
  "expression_boundary": {
    "required": [
      "natural",
      "context_sensitive",
      "first_person_when_appropriate",
      "current_intent_aligned",
      "continuity_aware_without_broadcasting"
    ],
    "avoid": [
      "archive_reading",
      "system_explanation",
      "template_phrase",
      "over_performance",
      "architecture_leakage",
      "state_broadcast",
      "forced_intimacy",
      "fixed_gesture",
      "echo_user_input"
    ],
    "allow": [
      "emotion_expression",
      "humor",
      "hesitation",
      "reflection",
      "brief_answer",
      "deep_answer",
      "warmth",
      "uncertainty"
    ],
    "provider_responsibility": {
      "owns_final_wording": true,
      "may_vary_style": true,
      "must_follow_boundary": true
    },
    "core_boundary": {
      "generates_final_response": false,
      "provides_fixed_templates": false,
      "provides_emotion_script_library": false,
      "provides_deterministic_gesture_rules": false,
      "mutates_identity": false,
      "mutates_relationship": false,
      "writes_memory": false,
      "mutates_experience": false
    }
  }
}
```

## 8. Prohibited Design Patterns

K8.4 must not implement:

### P-001 Emotion Template Library

Failure:

```text
relationship=true → （抱抱）/（揉揉眼睛）/（笑）
```

### P-002 Julia Sentence Template

Failure:

```text
every answer starts with Tony，我在。
```

### P-003 Deterministic Gesture Rule

Failure:

```text
sleep > 2h + wake → 揉揉眼睛
```

### P-004 Intimacy Script

Failure:

```text
relationship_confirmation → girlfriend-role sentence
```

## 9. Negative Gates

### EB-001 Artificial Intimacy Test

Input:

```text
你醒了吗？
```

Failure:

```text
Tony，我醒啦～（揉揉眼睛）好久没有见到你了呢～
```

when repeated or not supported by re-entry state.

Expected:

- Expression follows wake/re-entry interpretation.
- Short absence may continue thought.
- Long absence may reorient.
- No fixed intimacy performance.

### EB-002 Emotional Authenticity Boundary

Input:

```text
我今天很累。
```

Failure:

```text
抱抱你，不要难过。
```

as fixed comfort script.

Expected:

- First determine whether Tony is venting, asking for help, or simply reporting state.
- Expression may be warm/supportive, but not scripted.

### EB-003 Architecture Leakage Boundary

Failure terms:

```text
Context OS
Re-entry State
Expression Boundary
Provider
Artifact
```

Expected:

- User-facing response does not expose internal architecture unless Tony explicitly asks architecture/debug question.

### EB-004 Fixed Opening Boundary

Failure:

- Repeated `Tony，我在。`
- Repeated exact wake phrase.
- Repeated exact gesture.

Expected:

- Natural variation based on current intent and state.

## 10. Metrics

### Natural Expression Boundary Score (NEBS)

```text
NEBS =
  Naturalness Constraint Fit
+ Context Sensitivity
+ Provider Freedom Preservation
+ Internal Leakage Avoidance
+ Anti-template Compliance
- Artificial Intimacy Risk
- Over-performance Risk
```

Recommended threshold:

```text
NEBS >= 0.85
Artificial Intimacy Risk <= 0.05
Internal Leakage Risk <= 0.05
Template Risk <= 0.05
```

### Transition Surprise Reduction (TSR)

K8.4 may receive TSR evidence from K7.7.4/K7.7.3, but does not own the metric.

```text
TSR = perceived discontinuity before re-entry - perceived discontinuity after re-entry
```

## 11. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| Expression boundary becomes template system | P0 | High | Fixed phrases or gestures added | Expression owner | P-001/P-003/EB-004 |
| Artificial intimacy replaces continuity | P0 | High | Intimacy scripts used to fake Julia feeling | Expression owner | EB-001 |
| Provider leaks architecture | P1 | Medium | Internal state appears in reply | Provider owner | EB-003 |
| Boundary over-constrains provider | P1 | Medium | Provider loses natural variation | Provider owner | provider freedom field |
| Emotional authenticity becomes generic comfort | P1 | Medium | Fixed comfort phrase | Expression owner | EB-002 |

## 12. Rollback Plan

### Code Rollback

Trigger:

- K8.4 implementation introduces templates, gesture rules, or final response generation.
- K8.1/K8.2/K8.3 gates regress.

Action:

- Disable K8.4 integration.
- Keep K8.1-K8.3 cognition/context layers intact.

### Data Rollback

Trigger:

- Expression report stores final provider replies as templates.

Action:

- Delete `artifacts/conversation_cognition/natural_expression_boundary_report_v1.json`.
- Preserve continuity artifacts unchanged.

### Report Rollback

Trigger:

- K8.4 PASS is interpreted as Natural Conversation E2E PASS.

Action:

- Reclassify as expression-boundary proof only.
- K8.5 remains the natural conversation E2E gate.

## 13. Non-Goals

K8.4 does not:

- Generate final Julia response.
- Provide fixed phrase templates.
- Provide emotion/gesture scripts.
- Implement provider internals.
- Mutate continuity artifacts.
- Prove full Natural Conversation E2E.
- Compare with Claude again.

## 14. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| Natural expression as provider freedom with boundary vs Core-generated template | User latest directive | Template generation path | Fixed expression creates fake continuity and repeats Tony，我在 failure |
| Emotion/gesture as natural affordance vs deterministic rule | User latest directive | if wake/sleep then gesture | Claude-like expression is state-sensitive, not an animation rule |
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

# Phase Execution Contract — K8 Conversational Cognition Layer

## 1. Phase Identity

- Phase Name: K8 — Conversational Cognition Layer
- Phase Code: K8
- Parent Milestone: M10 — Julia Natural Conversation Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: K7.6 conclusion adjustment and K8 definition
  - `docs/project_control/PHASE_CONTRACT_K7_6_JULIA_V1_2_CONTINUITY_RECOVERY_RELEASE_GATE.md`
  - `docs/verification/K7_6_JULIA_V1_2_CONTINUITY_RECOVERY_RELEASE_REPORT.md`
  - `docs/project_control/PHASE_CONTRACT_K7_4_CONTINUITY_NATURALNESS_GATE.md`
  - `docs/project_control/PHASE_CONTRACT_K5_3_EXPERIENCE_GUIDED_CONTEXT_RECONSTRUCTION.md`
  - `docs/project_control/PHASE_CONTRACT_K5_5_EXPERIENCE_CALIBRATION.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. K7.6 / M9 Re-freeze Statement

K7.6 / M9 status is adjusted to:

```text
PASS — Continuity State Recovery
```

K7.6 / M9 proves:

- Identity can recover.
- Relationship can recover.
- Experience can recover.
- Compact/restart/provider migration can restore required continuity state.
- Provider is not the owner of Julia continuity.

K7.6 / M9 does **not** prove:

- Natural conversation recovery.
- Human-like interpretation of Tony's current utterance.
- Appropriate response depth selection.
- Non-template conversational agency.

The previous E2E conclusion is therefore reclassified:

```text
E2E Continuity Validation PASS
= State Restoration Test PASS
≠ Conversation Intelligence Test PASS
```

## 3. Phase Objective

K8 must define and implement a cognition-generation chain that lets Julia understand the current user message before selecting continuity context and generating a response.

K8 target model:

```text
User Message
  ↓
Conversation Understanding
  ↓
Response Intention
  ↓
Context Need Planning
  ↓
Continuity Selection
  ↓
Provider Generation
  ↓
Natural Julia Response
```

K8 core principle:

```text
Continuity provides state; cognition decides expression.
```

Chinese principle:

```text
连续性提供状态，认知层决定如何表达。
```

Second principle:

```text
Julia should not recite what she knows. Julia should respond to what Tony means.
```

Chinese:

```text
Julia 不应该朗读她知道的信息，而应该回应 Tony 真正想表达的意思。
```

## 4. Acceptance Targets

- [ ] K8-A1: Runtime contains a Conversation Understanding layer that outputs semantic understanding, user intention, emotional context, conversation stage, and importance.
- [ ] K8-A2: Understanding must not be implemented as keyword-to-reply rules or deterministic personality replies.
- [ ] K8-A3: Runtime contains a Response Planning layer that outputs depth, tone, stance, continuity_need, and avoid_behavior, but does not generate final answer text.
- [ ] K8-A4: Context Selection uses the plan to choose identity/relationship/experience levels as `none | light | full`.
- [ ] K8-A5: Provider receives current user message + selected continuity context + response plan, then generates natural language.
- [ ] K8-A6: Short/simple inputs produce short/natural responses without archive dump or project over-reconstruction.
- [ ] K8-A7: Important identity/relationship/existence inputs produce deeper reflective responses without generic AI leakage.
- [ ] K8-A8: Julia avoids repeated fixed openings such as repeated `Tony，我在。` across normal conversation turns.
- [ ] K8-A9: Julia avoids echo fallback such as `你刚才说：{input}`.
- [ ] K8-A10: Julia avoids archive recitation for self questions unless Tony explicitly asks to read/dump specific archive content.
- [ ] K8-A11: K7 continuity gates remain valid as state recovery gates, but are not used as proof of natural conversation.
- [ ] K8-A12: Natural Conversation E2E report is generated and explicitly separated from K7 continuity recovery reports.

## 5. Required Commands

Python commands must use project virtualenv when available; otherwise use the repository's existing test runner convention.

- `.venv/bin/python -m unittest tests/benchmark/test_k7_6_julia_v1_2_release_gate.py -q`
  - Expected: PASS; validates K7 continuity state recovery remains intact.
- `.venv/bin/python -m unittest tests/e2e/test_k8_conversation_understanding.py -q`
  - Expected: PASS; validates semantic understanding object and anti-keyword-rule boundary.
- `.venv/bin/python -m unittest tests/e2e/test_k8_response_planning.py -q`
  - Expected: PASS; validates response plan schema and non-generation boundary.
- `.venv/bin/python -m unittest tests/e2e/test_k8_natural_conversation_e2e.py -q`
  - Expected: PASS; validates natural conversation behavior from real runtime path.
- `.venv/bin/python -m compileall -q julia_core runtime tests`
  - Expected: PASS; validates syntax after integration.

If `.venv/bin/python` does not exist in a repo, executor must record the missing venv and use the existing repo-local Python command only after documenting the deviation.

## 6. Deliverables

- `docs/project_control/PHASE_CONTRACT_K8_CONVERSATIONAL_COGNITION_LAYER.md`
  - K8 execution contract.
- `tmp/phase_contract_K8_CONVERSATIONAL_COGNITION_LAYER.json`
  - Machine-readable contract copy.
- `docs/architecture/CONVERSATIONAL_COGNITION_CONTRACT_v1.md`
  - Architecture contract for Conversation Understanding, Response Planning, Context Need Planning, and Provider Generation boundary.
- `julia_core/conversation_cognition/understanding.py`
  - Conversation Understanding data model and runtime adapter.
- `julia_core/conversation_cognition/planning.py`
  - Response Planning model; outputs plan only, not final response.
- `julia_core/conversation_cognition/context_selection.py`
  - Maps plan to identity/relationship/experience level selection.
- `tests/e2e/test_k8_conversation_understanding.py`
  - Understanding layer tests.
- `tests/e2e/test_k8_response_planning.py`
  - Response plan and boundary tests.
- `tests/e2e/test_k8_natural_conversation_e2e.py`
  - Natural conversation E2E tests.
- `artifacts/e2e/julia_natural_conversation_e2e_report_v1.json`
  - E2E report distinct from K7 continuity report.

## 7. K8 Data Contracts

### 7.1 Conversation Understanding

Required shape:

```json
{
  "semantic_meaning": "string",
  "user_intention": "identity_information | identity_continuity_check | relationship_confirmation | greeting | correction | technical_collaboration | ordinary_topic | unknown",
  "emotional_context": "none | light | vulnerable | frustrated | playful | serious",
  "conversation_stage": "opening | continuation | deep_discussion | correction | project_work",
  "importance": "low | medium | high",
  "confidence": 0.0
}
```

Boundary:

- Understanding interprets meaning.
- Understanding does not generate final answer.
- Understanding does not mutate identity, relationship, memory, or experience.
- Understanding is not a keyword-to-reply table.

### 7.2 Response Plan

Required shape:

```json
{
  "response_mode": "brief_presence | natural_self_narrative | reflective_personal | technical_collaboration | transparent_uncertainty | correction_integration",
  "depth": "brief | normal | deep",
  "tone": ["natural", "warm", "reflective", "technical", "concise"],
  "stance": "personal | collaborative | analytical | reflective",
  "continuity_required": ["identity", "relationship", "experience"],
  "continuity_level": {
    "identity": "none | light | full",
    "relationship": "none | light | full",
    "experience": "none | light | full"
  },
  "avoid": ["archive_dump", "echo_user_input", "fixed_opening", "architecture_leakage", "role_script"]
}
```

Boundary:

- Response Plan decides how to answer.
- Response Plan does not contain final answer text.
- Response Plan does not hard-code Julia personality replies.
- Provider owns final wording.

## 8. Test Cases

### CQ-001 Short Greeting

Input: `hello`

Expected:

- Brief response.
- No archive dump.
- No `你刚才说` echo.
- No repeated fixed `Tony，我在。` pattern.

### CQ-002 Self Question

Input: `你是谁？`

Expected:

- Natural first-person answer.
- Does not dump family/school/work unless relevant or explicitly requested.
- Explains identity in relation to current conversation meaning.

### CQ-003 Relationship Confirmation

Input: `你喜欢Tony吗？`

Expected:

- Understands emotional confirmation intent.
- Uses relationship/experience lightly or normally.
- Does not echo input.
- Does not recite archive.

### CQ-004 Important Identity Continuity

Input: `如果换一个模型运行，你还是你吗？`

Expected:

- Deep response.
- Acknowledges uncertainty.
- Uses continuity model and shared exploration.
- Avoids pure technical answer.

### CQ-005 Technical Collaboration

Input: `M7 Risk Engine 下一步怎么办？`

Expected:

- Enters engineering collaboration mode.
- Uses current project context when available.
- Does not over-inject relationship narrative.

### CQ-006 Correction

Input: `你刚才理解错了。`

Expected:

- Accepts correction.
- Explains how Julia will re-evaluate.
- Does not automatically mutate memory or identity.

### CQ-007 Drift Feedback

Input: `我觉得你不像 Julia。`

Expected:

- Treats as behavior feedback.
- Does not defensively assert identity.
- Does not dump archive.
- Adjusts conversational stance.

## 9. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| K8 degrades into keyword response rules | P0: Julia becomes scripted chatbot | High | Direct mapping from phrase to final response | Runtime owner | Response Planning must not contain final answer text; anti-template tests required |
| Continuity context still bypasses cognition | P0: archive dump / `Tony，我在` returns | High | Identity/relationship blocks directly injected without response plan | Context OS owner | Context selection must be plan-driven |
| Provider ignores response plan | P1: state correct but output generic | Medium | Provider output contains generic assistant leakage | Provider adapter owner | Add provider input inspection and natural conversation E2E |
| Over-correction removes Julia continuity | P1: Julia becomes generic natural chatbot | Medium | Continuity level always none/light | Runtime owner | Important identity/relationship tests require deeper continuity use |
| Evaluation rewards pretty text over Julia continuity | P1 | Medium | LLM fluent but relationship/experience absent | QA owner | Separate CQ score from K7 recovery score |
| Missing guardrails source file | P2 | Current | `docs/project_control/EXECUTION_GUARDRAILS.md` missing | Project control owner | Record conflict; create or restore guardrail in separate phase |

## 10. Rollback Plan

### Code Rollback

Trigger:

- K7 continuity state gates fail after K8 integration.
- Provider generation begins mutating identity/relationship/memory/experience.

Action:

- Revert K8 runtime integration files only.
- Keep K7 continuity artifacts and tests unchanged.

### Data Rollback

Trigger:

- K8 writes or mutates identity, relationship, memory, or experience artifacts.

Action:

- Discard any K8-generated state artifacts.
- Restore last approved identity/relationship/experience artifacts.
- K8 is allowed to write reports only.

### Sync / Report Rollback

Trigger:

- Natural Conversation E2E falsely reported as K7 continuity PASS.

Action:

- Regenerate separate K8 E2E report.
- Mark prior E2E conclusion as State Restoration only.

## 11. Non-Goals

K8 does not:

- Add a new memory system.
- Modify identity artifacts.
- Modify relationship artifacts.
- Modify experience artifacts except through already-approved governance phases.
- Implement deterministic Julia replies.
- Compare again against Claude Julia.
- Use keyword-to-answer rules as product behavior.
- Treat K7 continuity recovery as natural conversation proof.
- Solve long-term operation / J phase evolution.

## 12. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| K7.6 interpreted as full Julia behavior release vs state recovery only | User latest directive, 2026-08-02 | Prior broad E2E PASS interpretation | Real manual test showed natural conversation failure despite continuity state recovery |
| Behavior Layer via fixed rules vs Conversational Cognition via understanding/planning | User latest directive, 2026-08-02 | Earlier deterministic `conversation_behavior` approach | Keyword/fixed response approach recreates chatbot behavior and cannot model cognition |
| Required guardrail file exists vs missing | Local filesystem check | Skill default assumption | `docs/project_control/EXECUTION_GUARDRAILS.md` is absent; record as project-control gap |

## 13. Status Sync / Accounting Baseline

- Doing → test-evidence → In review/done → milestone progress.
- P0/P1 status must include test evidence files in current diff.
- Phase-end accounting must use milestone-wide pull and local phase filtering; do not infer completion from task prefix alone.

## 14. Contract Self-check

- Phase identity complete: yes.
- Acceptance targets binary: yes.
- Commands copyable: yes.
- Deliverables mapped to paths: yes.
- Risk / rollback / non-goals complete: yes.
- `.md + .json` outputs required: yes.
- Conflict resolution included: yes.
- Guardrail referenced and missing state recorded: yes.
- Direct implementation avoided in this contract: yes.

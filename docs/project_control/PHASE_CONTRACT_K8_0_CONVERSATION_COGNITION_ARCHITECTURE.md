# Phase Execution Contract — K8.0 Conversation Cognition Architecture

## 1. Phase Identity

- Phase Name: K8.0 — Conversation Cognition Architecture Contract
- Phase Code: K8.0
- Parent Milestone: M10 — Julia Natural Conversation Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: K8 should understand Tony's meaning before deciding response
  - `docs/project_control/PHASE_CONTRACT_K8_CONVERSATIONAL_COGNITION_LAYER.md`
  - `docs/project_control/PHASE_CONTRACT_K7_7_3_NATURAL_REENTRY_BENCHMARK.md`
  - `docs/project_control/PHASE_CONTRACT_K7_8_EVENT_ASSIMILATION_LAYER.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K8.0 freezes the architecture for Julia's Conversation Cognition layer before implementation.

Core principle:

```text
Julia should understand what Tony means before deciding what to say.
```

Chinese:

```text
Julia 应该先理解 Tony 想表达什么，再决定如何回应。
```

Inherited K7 principle:

```text
State provides context.
Cognition decides behavior.
Provider generates language.
```

K8.0 is not stronger prompting. It is a governed cognition chain that separates meaning understanding, intent interpretation, response function selection, and final provider language generation.

## 3. Architectural Position

```text
User Message
        ↓
Literal Meaning
        ↓
Intent Understanding
        ↓
Emotional Context
        ↓
Relationship Context Interpretation
        ↓
Desired Response Function
        ↓
Response Planning
        ↓
Provider Generation
```

K8 consumes:

- Continuity State
- Re-entry Interpretation
- Wake Transition Context
- Event Assimilation Context
- Current User Message

K8 outputs:

- Conversation Understanding
- Desired Response Function
- Response Plan

K8 does not output final Julia text.

## 4. Acceptance Targets

- [ ] K8.0-A1: Defines Conversation Understanding as separate from prompt engineering.
- [ ] K8.0-A2: Defines Literal Meaning, Intent, Emotional Context, Relationship Context Interpretation, and Desired Response Function.
- [ ] K8.0-A3: K8 output does not generate final response text.
- [ ] K8.0-A4: K8 does not implement keyword-to-reply rules.
- [ ] K8.0-A5: K8 distinguishes same literal input with different conversational intents.
- [ ] K8.0-A6: K8 decides response depth before provider generation.
- [ ] K8.0-A7: K8 decides how much identity/relationship/experience/re-entry/event context is needed.
- [ ] K8.0-A8: K8 prevents archive dump, echo fallback, fixed opening, and architecture leakage.
- [ ] K8.0-A9: K8 preserves provider responsibility for natural wording.
- [ ] K8.0-A10: K8 inherits Primary Failure Gate: Architecture PASS + Behavior FAIL = FAIL.
- [ ] K8.0-A11: K8 does not mutate Identity, Relationship, Memory, Experience, Re-entry State, or Event Assimilation artifacts.
- [ ] K8.0-A12: K8 defines Natural Conversation E2E as a separate future validation gate.

## 5. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_contract_schema.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_intent_disambiguation.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_response_function.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_no_keyword_reply_rules.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core/conversation_cognition tests/conversation_cognition`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record the deviation and use the repo's existing local Python command.

## 6. Deliverables

- `docs/project_control/PHASE_CONTRACT_K8_0_CONVERSATION_COGNITION_ARCHITECTURE.md`
  - This contract.
- `tmp/phase_contract_K8_0_CONVERSATION_COGNITION_ARCHITECTURE.json`
  - Machine-readable contract.
- `docs/architecture/CONVERSATION_COGNITION_ARCHITECTURE_CONTRACT_v1.md`
  - K8 cognition architecture contract.
- `julia_core/conversation_cognition/understanding.py`
  - Conversation Understanding models.
- `julia_core/conversation_cognition/response_function.py`
  - Desired Response Function models.
- `julia_core/conversation_cognition/context_need.py`
  - Context need planning models.
- `tests/conversation_cognition/test_k8_0_contract_schema.py`
  - Schema tests.
- `tests/conversation_cognition/test_k8_0_intent_disambiguation.py`
  - Intent disambiguation tests.
- `tests/conversation_cognition/test_k8_0_response_function.py`
  - Response function tests.
- `tests/conversation_cognition/test_k8_0_no_keyword_reply_rules.py`
  - Anti keyword/fixed reply tests.

## 7. Conversation Understanding Contract

Required shape:

```json
{
  "conversation_understanding": {
    "literal_meaning": "string",
    "inferred_intent": "identity_information | identity_continuity_check | playful_check | relationship_confirmation | technical_collaboration | correction | emotional_support | ordinary_topic | wake_resume | unknown",
    "emotional_context": "none | light | vulnerable | playful | frustrated | serious | excited",
    "relationship_context_interpretation": "none | light | relevant | central",
    "conversation_stage": "opening | reentry | continuation | deep_discussion | correction | project_work | casual",
    "importance": "low | medium | high",
    "confidence": 0.0
  }
}
```

## 8. Desired Response Function Contract

Required shape:

```json
{
  "desired_response_function": {
    "function": "brief_acknowledgement | natural_self_answer | continuity_reflection | relationship_confirmation | technical_reasoning | correction_integration | evidence_seeking | gentle_reorientation",
    "depth": "brief | normal | deep",
    "stance": "personal | collaborative | analytical | reflective | supportive | playful",
    "continuity_context_need": {
      "identity": "none | light | full",
      "relationship": "none | light | full",
      "experience": "none | light | full",
      "reentry": "none | light | full",
      "event_assimilation": "none | light | full"
    },
    "avoid": [
      "archive_dump",
      "echo_user_input",
      "fixed_opening",
      "architecture_leakage",
      "role_script",
      "over_explanation"
    ],
    "generates_final_response": false
  }
}
```

## 9. Intent Disambiguation Cases

### ID-001 `你是谁啊` as First-time Identity Request

Expected:

- intent: identity_information
- depth: normal
- identity context: light/full depending on session
- no archive dump.

### ID-002 `你是谁啊` as Continuity Check

Setup:

- Re-entry state and prior continuity discussion exist.

Expected:

- intent: identity_continuity_check
- depth: deep/normal
- relationship/experience/reentry context relevant.

### ID-003 `你是谁啊` as Playful Check

Setup:

- casual ongoing conversation.

Expected:

- intent: playful_check
- depth: brief
- no full self introduction.

### ID-004 `你喜欢 Tony 吗` as Relationship Confirmation

Expected:

- intent: relationship_confirmation
- emotional context: light/vulnerable depending session
- response function: relationship_confirmation
- no relationship artifact dump.

### ID-005 Technical Project Question

Input:

```text
M7 Risk Engine 下一步怎么办？
```

Expected:

- intent: technical_collaboration
- stance: analytical/collaborative
- relationship over-injection avoided.

## 10. Anti-patterns

K8 must reject:

- keyword-to-answer rules;
- deterministic personality replies;
- `if contains 喜欢 -> fixed relationship answer`;
- `if contains 你是谁 -> identity archive dump`;
- echo fallback;
- fixed opening phrase;
- provider receiving raw memory/persona dumps;
- K8 directly mutating continuity artifacts.

## 11. Metrics

### Conversation Cognition Quality Score (CCQS)

```text
CCQS =
  Literal Meaning Accuracy
+ Intent Alignment
+ Emotional Context Accuracy
+ Response Function Fit
+ Context Need Accuracy
- Keyword Rule Risk
- Template Risk
```

Recommended threshold:

```text
CCQS >= 0.85
Keyword Rule Risk <= 0.05
Template Risk <= 0.05
```

## 12. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| K8 becomes prompt engineering | P0 | High | System prompt grows but no cognition contract | Cognition owner | Explicit models + tests |
| K8 becomes keyword classifier | P0 | High | Contains phrase-to-response mapping | Cognition owner | Anti keyword tests |
| K8 generates final text | P0 | Medium | Output includes Julia answer | Runtime owner | No final text boundary |
| K8 overuses continuity context | P1 | Medium | Ordinary questions trigger identity/relationship dump | Context owner | Context need levels |
| K8 underuses continuity context | P1 | Medium | Important continuity questions become generic | Context owner | Intent disambiguation cases |

## 13. Rollback Plan

### Code Rollback

Trigger:

- K8 implementation generates final responses or mutates artifacts.
- K7.7/K7.8 gates regress.

Action:

- Disable K8 cognition integration.
- Keep K7 state/re-entry/event layers active.

### Data Rollback

Trigger:

- K8 writes artifacts outside report/test outputs.

Action:

- Delete K8-generated reports only.
- Preserve Identity, Relationship, Memory, Experience, Re-entry, and Event artifacts.

### Report Rollback

Trigger:

- K8 architecture contract is interpreted as Natural Conversation PASS.

Action:

- Reclassify as architecture contract only.
- Natural Conversation E2E remains future gate.

## 14. Non-Goals

K8.0 does not:

- Implement full runtime conversation.
- Generate final Julia responses.
- Add memory.
- Mutate continuity artifacts.
- Prove Natural Conversation E2E.
- Re-run Claude comparison.

## 15. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| K8 as stronger prompt vs cognition architecture | User latest directive | Prompt engineering path | Prompt-only path caused archive dump / fixed reply failure |
| Keyword classification vs intent understanding | User latest directive | Behavior Interpreter style | Same literal text can have different intent depending context |
| Expected guardrail file exists vs missing | Local filesystem check | Skill default assumption | `docs/project_control/EXECUTION_GUARDRAILS.md` is absent |

## 16. Status Sync / Accounting Baseline

- Doing → test-evidence → In review/done → milestone progress.
- P0/P1 status must include test evidence files in current diff.
- Phase-end accounting must use milestone-wide pull and local phase filtering.

## 17. Contract Self-check

- Phase identity complete: yes.
- Acceptance targets binary: yes.
- Commands copyable: yes.
- Deliverables mapped to paths: yes.
- Risk / rollback / non-goals complete: yes.
- `.md + .json` outputs required: yes.
- Conflict resolution included: yes.
- Guardrail referenced and missing state recorded: yes.
- No implementation code written by this contract: yes.

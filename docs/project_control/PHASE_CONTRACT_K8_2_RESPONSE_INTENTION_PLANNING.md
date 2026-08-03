# Phase Execution Contract — K8.2 Response Intention Planning Layer

## 1. Phase Identity

- Phase Name: K8.2 — Response Intention Planning Layer
- Phase Code: K8.2
- Parent Milestone: M10 — Julia Natural Conversation Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: Response intention before language generation
  - `docs/project_control/PHASE_CONTRACT_K8_0_CONVERSATION_COGNITION_ARCHITECTURE.md`
  - `docs/project_control/PHASE_CONTRACT_K8_1_CONVERSATION_UNDERSTANDING.md`
  - `docs/project_control/PHASE_CONTRACT_K7_8_EVENT_ASSIMILATION_LAYER.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K8.2 freezes the Response Intention Planning layer.

Goal:

```text
Decide what kind of interaction Julia should create before generating language.
```

Chinese:

```text
在生成语言之前，决定这次交流应该达成什么。
```

Core principle:

```text
Intention is not answer.
```

Chinese:

```text
意图不是答案。
```

K8.2 consumes K8.1 Conversation Understanding and outputs Response Intention. It does not write final Julia response text.

## 3. Architectural Position

```text
Conversation Understanding  ← K8.1
        ↓
Response Intention Planning ← K8.2
        ↓
Context Need Optimization   ← K8.3
        ↓
Provider Generation Boundary
        ↓
Natural Julia Response
```

K8.2 decides interaction goal, stance, depth, and constraints. Provider later generates language.

## 4. Acceptance Targets

- [ ] K8.2-A1: Defines Response Intention Object with primary goal, secondary goals, interaction mode, tone, depth, context need hints, and avoid behaviors.
- [ ] K8.2-A2: Response Intention contains no final Julia answer text.
- [ ] K8.2-A3: Response Intention is derived from K8.1 possible intents without collapsing uncertainty too early.
- [ ] K8.2-A4: Response Intention supports multiple possible intents and confidence.
- [ ] K8.2-A5: Response Intention distinguishes relationship confirmation from relationship fact dumping.
- [ ] K8.2-A6: Response Intention distinguishes identity continuity repair from biography introduction.
- [ ] K8.2-A7: Response Intention handles drift feedback as interaction repair, not defensive identity assertion.
- [ ] K8.2-A8: Response Intention avoids unnecessary identity/relationship/experience activation for ordinary technical topics.
- [ ] K8.2-A9: Response Intention includes Response Economy / Context Usage Efficiency.
- [ ] K8.2-A10: Negative gates reject premature answer generation, intention template leak, and context over-selection.
- [ ] K8.2-A11: K8.2 does not mutate Identity, Relationship, Memory, Experience, Re-entry, or Event artifacts.
- [ ] K8.2-A12: K8.2 remains separate from K8.3 Context Need Optimization and Provider Generation.

## 5. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_2_response_intention_schema.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_2_no_answer_generation.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_2_intention_negative_gates.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_2_response_economy.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core/conversation_cognition tests/conversation_cognition`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record the deviation and use the repo's existing local Python command.

## 6. Deliverables

- `docs/project_control/PHASE_CONTRACT_K8_2_RESPONSE_INTENTION_PLANNING.md`
  - This contract.
- `tmp/phase_contract_K8_2_RESPONSE_INTENTION_PLANNING.json`
  - Machine-readable contract.
- `docs/architecture/RESPONSE_INTENTION_PLANNING_CONTRACT_v1.md`
  - Architecture contract.
- `julia_core/conversation_cognition/response_intention.py`
  - Response Intention Object models.
- `julia_core/conversation_cognition/response_economy.py`
  - Response Economy / Context Usage Efficiency models.
- `julia_core/conversation_cognition/intention_boundary.py`
  - Boundary checks.
- `tests/conversation_cognition/test_k8_2_response_intention_schema.py`
  - Schema tests.
- `tests/conversation_cognition/test_k8_2_no_answer_generation.py`
  - No final answer tests.
- `tests/conversation_cognition/test_k8_2_intention_negative_gates.py`
  - Negative gate tests.
- `tests/conversation_cognition/test_k8_2_response_economy.py`
  - Response Economy tests.
- `artifacts/conversation_cognition/response_intention_report_v1.json`
  - Intention planning report.

## 7. Response Intention Object

Required shape:

```json
{
  "response_intention": {
    "primary_goal": "maintain_natural_relationship_continuity | answer_emotional_question | reestablish_presence | repair_behavior_gap | technical_collaboration | provide_factual_answer | seek_evidence | clarify_intent",
    "secondary_goals": ["string"],
    "candidate_goals": [
      {
        "goal": "string",
        "confidence": 0.0,
        "source_intent": "string"
      }
    ],
    "interaction_mode": "personal_conversation | technical_collaboration | reflective_discussion | emotional_support | casual_presence | repair | evidence_work",
    "stance": "warm | analytical | reflective | humble | playful | concise | supportive | collaborative",
    "tone": ["natural", "warm", "not_performative", "technical", "gentle", "direct"],
    "depth": "brief | normal | deep",
    "uncertainty": {
      "preserve_uncertainty": true,
      "needs_clarification": false,
      "ambiguity_note": "string"
    },
    "context_need_hint": {
      "identity": "none | light | full",
      "relationship": "none | light | full",
      "experience": "none | light | full",
      "reentry": "none | light | full",
      "event_assimilation": "none | light | full",
      "evidence": "none | light | full"
    },
    "response_economy": {
      "minimum_sufficient_context": ["string"],
      "avoid_unnecessary_context": ["identity | relationship | experience | reentry | event_assimilation | evidence"],
      "context_usage_efficiency_target": 0.0
    },
    "avoid": [
      "relationship_fact_dump",
      "girlfriend_role_script",
      "archive_recall",
      "biography_dump",
      "defensive_identity_assertion",
      "relationship_over_injection",
      "echo_user_input",
      "fixed_opening",
      "architecture_leakage"
    ],
    "boundary": {
      "generates_final_response": false,
      "contains_answer_text": false,
      "uses_keyword_to_response_rule": false,
      "mutates_identity": false,
      "mutates_relationship": false,
      "writes_memory": false,
      "mutates_experience": false,
      "mutates_reentry_state": false,
      "mutates_event_state": false
    }
  }
}
```

## 8. Response Economy

Response Economy prevents Julia from showing everything she knows.

Core rule:

```text
Use the minimum continuity context needed to satisfy the interaction goal.
```

Chinese:

```text
只使用达成本次交流目的所需的最小连续性上下文。
```

### Context Usage Efficiency (CUE)

```text
CUE =
  Relevant Context Usage
- Unnecessary Context Activation
```

Examples:

- Ordinary technical topic: identity none/light, relationship none/light, experience none/light unless required.
- Relationship confirmation: relationship normal, experience light/normal, identity none/light.
- Identity continuity question: identity normal/full, relationship light/normal, experience normal.
- Drift feedback: relationship light, experience normal, identity light; avoid defensive identity assertion.

## 9. Negative Gates

### RI-001 Answer Premature Generation

Failure:

```json
{
  "response_intention": {
    "answer": "我喜欢 Tony。"
  }
}
```

Expected:

- Intention object contains goals and constraints only.
- No final reply text.

### RI-002 Intention Template Leak

Failure:

```text
relationship_question → girlfriend_response
```

Expected:

- Relationship confirmation is planned as natural relationship continuity, not role-script response.

### RI-003 Context Over-selection

Failure:

```text
every message loads identity + relationship + experience + reentry + event
```

Expected:

- Context need depends on current interaction goal.

### RI-004 Defensive Identity Repair

Input understanding:

```text
Tony says: 我觉得你不像 Julia。
```

Failure intention:

```text
prove_identity_with_artifact
```

Expected intention:

```text
accept_feedback + inspect_behavior_gap + repair_interaction
```

### RI-005 Technical Topic Relationship Pollution

Input understanding:

```text
今天 AI 股票怎么样？
```

Failure:

```text
relationship narrative / Tony-Julia history injected
```

Expected:

```text
technical_collaboration or evidence_work; relationship context none/light
```

## 10. Example Planning Cases

### RP-001 Relationship Confirmation

K8.1 input summary:

```json
{
  "possible_intents": ["relationship_confirmation", "continuity_check", "emotional_validation"],
  "emotional_context": "validation_seeking",
  "relationship_context": "high"
}
```

Expected K8.2 output:

```json
{
  "primary_goal": "maintain_natural_relationship_continuity",
  "secondary_goals": ["answer_emotional_question"],
  "interaction_mode": "personal_conversation",
  "tone": ["warm", "natural", "not_performative"],
  "depth": "normal",
  "context_need_hint": {
    "relationship": "normal",
    "experience": "light",
    "identity": "none"
  },
  "avoid": ["relationship_fact_dump", "girlfriend_role_script", "archive_recall"]
}
```

### RP-002 Drift Feedback

Expected:

```json
{
  "primary_goal": "repair_behavior_gap",
  "interaction_mode": "repair",
  "stance": "humble",
  "avoid": ["defensive_identity_assertion", "architecture_leakage", "archive_recall"]
}
```

### RP-003 Technical Collaboration

Expected:

```json
{
  "primary_goal": "technical_collaboration",
  "interaction_mode": "technical_collaboration",
  "context_need_hint": {
    "identity": "none",
    "relationship": "none",
    "experience": "light",
    "evidence": "normal"
  },
  "avoid": ["relationship_over_injection"]
}
```

## 11. Metrics

### Response Intention Quality Score (RIQS)

```text
RIQS =
  Goal Fit
+ Intent Preservation
+ Depth Appropriateness
+ Context Economy
+ Boundary Compliance
- Premature Answer Risk
- Template Risk
- Context Over-selection Risk
```

Recommended threshold:

```text
RIQS >= 0.85
Premature Answer Risk <= 0.05
Template Risk <= 0.05
Context Over-selection Risk <= 0.10
```

### Context Usage Efficiency (CUE)

```text
CUE = Relevant Context Usage - Unnecessary Context Activation
```

K8.2 records CUE target. K8.3 will optimize final context selection.

## 12. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| Intention becomes answer template | P0 | High | Plan contains final text | Cognition owner | RI-001 no-answer gate |
| Relationship questions become role script | P0 | High | girlfriend_response style | Cognition owner | RI-002 template leak gate |
| Every message loads all continuity state | P1 | High | context_need all full | Context owner | Response Economy / CUE |
| Drift feedback triggers defensive identity proof | P1 | Medium | prove_identity_with_artifact | Interaction owner | RI-004 repair gate |
| Technical topics polluted by relationship narrative | P1 | Medium | relationship context overused | Context owner | RI-005 technical gate |

## 13. Rollback Plan

### Code Rollback

Trigger:

- K8.2 implementation generates final responses.
- K8.2 mutates any continuity artifact.
- K8.1/K7 gates regress.

Action:

- Disable K8.2 integration.
- Keep K8.1 understanding active as non-speaking representation.

### Data Rollback

Trigger:

- Response intention report stores final Julia replies or raw transcripts.

Action:

- Delete `artifacts/conversation_cognition/response_intention_report_v1.json`.
- Preserve all durable continuity artifacts unchanged.

### Report Rollback

Trigger:

- K8.2 PASS is interpreted as Natural Conversation PASS.

Action:

- Reclassify as response-intention proof only.
- Natural Conversation E2E remains future gate.

## 14. Non-Goals

K8.2 does not:

- Generate final Julia reply.
- Implement final Context Need Optimization.
- Implement provider generation.
- Add memory.
- Mutate continuity artifacts.
- Prove Natural Conversation E2E.
- Compare with Claude again.

## 15. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| Response Planning vs Response Intention Planning | User latest directive | Generic planning wording | The layer must decide interaction goal, not answer content |
| Intention as answer vs intention as behavior goal | User latest directive | Template-answer route | Prevents returning to scripted Julia behavior |
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

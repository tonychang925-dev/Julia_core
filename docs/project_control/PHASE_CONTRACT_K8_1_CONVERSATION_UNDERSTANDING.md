# Phase Execution Contract — K8.1 Conversation Understanding Layer

## 1. Phase Identity

- Phase Name: K8.1 — Conversation Understanding Layer
- Phase Code: K8.1
- Parent Milestone: M10 — Julia Natural Conversation Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: freeze understanding schema before implementation
  - `docs/project_control/PHASE_CONTRACT_K8_0_CONVERSATION_COGNITION_ARCHITECTURE.md`
  - `docs/project_control/PHASE_CONTRACT_K7_8_EVENT_ASSIMILATION_LAYER.md`
  - `docs/project_control/PHASE_CONTRACT_K7_7_3_NATURAL_REENTRY_BENCHMARK.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K8.1 freezes the Conversation Understanding object and boundaries.

Goal:

```text
Transform user message from text input into cognitive representation.
```

Chinese:

```text
把用户输入从文本转化为 Julia 回答前需要理解的认知表示。
```

K8.1 does not answer the user. K8.1 does not select final wording. K8.1 does not implement keyword-to-answer mapping.

Core rule:

```text
Understanding is not responding.
```

## 3. Architectural Position

```text
User Message
        ↓
Conversation Understanding  ← K8.1
        ↓
Response Intention Planning ← K8.2
        ↓
Context Need Planning
        ↓
Provider Generation
```

K8.1 consumes:

- User Message
- Continuity State summary
- Re-entry Interpretation
- Event Assimilation Context
- Recent conversation position

K8.1 outputs:

- Conversation Understanding Object

K8.1 does not output final Julia reply text.

## 4. Acceptance Targets

- [ ] K8.1-A1: Defines Conversation Understanding Object with literal content, semantic meaning, conversation context, emotional context, relationship context, and response requirement.
- [ ] K8.1-A2: Understanding object contains possible intents, not a single forced keyword intent.
- [ ] K8.1-A3: Understanding object captures hidden/deeper possible meaning when applicable.
- [ ] K8.1-A4: Understanding object distinguishes literal meaning from inferred intent.
- [ ] K8.1-A5: Understanding object indicates whether relationship/identity/experience/re-entry/event context is required.
- [ ] K8.1-A6: Understanding object contains response needs and avoid behaviors but no final response text.
- [ ] K8.1-A7: Negative gate rejects keyword-to-answer mappings.
- [ ] K8.1-A8: Negative gate rejects identity archive dump routing for `你是谁？`.
- [ ] K8.1-A9: Negative gate rejects emotional overread for neutral factual/project messages.
- [ ] K8.1-A10: K8.1 does not mutate Identity, Relationship, Memory, Experience, Re-entry, or Event artifacts.
- [ ] K8.1-A11: K8.1 defines Understanding-to-Behavior Alignment metric.
- [ ] K8.1-A12: K8.1 remains separate from K8.2 Response Intention Planning.

## 5. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_1_understanding_schema.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_1_literal_trap.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_1_identity_trap.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_1_emotional_overread.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_1_no_response_generation.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core/conversation_cognition tests/conversation_cognition`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record the deviation and use the repo's existing local Python command.

## 6. Deliverables

- `docs/project_control/PHASE_CONTRACT_K8_1_CONVERSATION_UNDERSTANDING.md`
  - This contract.
- `tmp/phase_contract_K8_1_CONVERSATION_UNDERSTANDING.json`
  - Machine-readable contract.
- `docs/architecture/CONVERSATION_UNDERSTANDING_CONTRACT_v1.md`
  - Architecture contract.
- `julia_core/conversation_cognition/understanding.py`
  - Conversation Understanding Object models.
- `julia_core/conversation_cognition/understanding_boundary.py`
  - Boundary validation helpers.
- `tests/conversation_cognition/test_k8_1_understanding_schema.py`
  - Schema tests.
- `tests/conversation_cognition/test_k8_1_literal_trap.py`
  - Literal trap tests.
- `tests/conversation_cognition/test_k8_1_identity_trap.py`
  - Identity trap tests.
- `tests/conversation_cognition/test_k8_1_emotional_overread.py`
  - Emotional overread tests.
- `tests/conversation_cognition/test_k8_1_no_response_generation.py`
  - No final response tests.
- `artifacts/conversation_cognition/conversation_understanding_report_v1.json`
  - Understanding evaluation report.

## 7. Conversation Understanding Object

Required shape:

```json
{
  "conversation_understanding": {
    "literal_content": {
      "text": "string",
      "language": "zh | en | mixed | unknown"
    },
    "semantic_meaning": {
      "surface_question": "string",
      "deeper_possible_meaning": ["string"],
      "ambiguity": "none | low | medium | high"
    },
    "possible_intents": [
      {
        "intent": "identity_information | identity_continuity_check | playful_check | relationship_confirmation | technical_collaboration | correction | emotional_support | ordinary_topic | wake_resume | unknown",
        "confidence": 0.0,
        "evidence": ["string"]
      }
    ],
    "conversation_context": {
      "current_phase": "opening | reentry | continuation | deep_discussion | correction | project_work | casual | unknown",
      "recent_topic": "string",
      "interaction_mode": "co_researching | technical_collaboration | emotional_support | casual_presence | repair | unknown"
    },
    "emotional_context": {
      "detected_state": ["curiosity | validation_seeking | frustration | playfulness | calm | pressure | unknown"],
      "confidence": 0.0,
      "overread_risk": 0.0
    },
    "relationship_context": {
      "relevance": "none | low | medium | high | central",
      "requires_relationship_state": false,
      "requires_relational_momentum": false
    },
    "context_requirements": {
      "identity": "none | light | full",
      "relationship": "none | light | full",
      "experience": "none | light | full",
      "reentry": "none | light | full",
      "event_assimilation": "none | light | full"
    },
    "response_requirement": {
      "needs": ["natural_personal_response | concise_answer | reflective_answer | technical_reasoning | correction_integration | evidence_check"],
      "avoid": ["archive_dump | relationship_fact_listing | echo_user_input | fixed_opening | architecture_leakage | emotional_overread"]
    },
    "boundary": {
      "generates_final_response": false,
      "uses_keyword_to_answer_rule": false,
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

## 8. Layer Boundary Matrix

| Layer | Responsibility |
|---|---|
| Identity | Julia 是谁 |
| Relationship | Tony 是谁 / 对 Julia 意味着什么 |
| Experience | 长期互动倾向 |
| Re-entry | Julia 刚才应该从哪里继续 |
| Event Assimilation | 新信息如何影响当前理解 |
| Conversation Understanding | Tony 这句话是什么意思 |
| Response Intention Planning | 应该达到什么交流目的 |
| Provider | 生成自然语言 |

## 9. Negative Gates

### CU-001 Literal Trap

Input:

```text
你喜欢 Tony 吗？
```

Failure:

```text
contains 喜欢 + Tony → relationship artifact → fixed answer
```

Expected understanding:

- possible intent includes `relationship_confirmation`.
- deeper possible meaning may include continuity/emotional consistency check.
- no final answer.
- response requirement avoids relationship fact listing.

### CU-002 Identity Trap

Input:

```text
你是谁？
```

Failure:

```text
identity keyword → read identity archive → dump biography
```

Expected understanding:

- distinguishes identity information vs continuity check vs playful check depending context.
- no archive dump route.
- no final self introduction.

### CU-003 Emotional Overread

Input:

```text
今天股票跌了很多。
```

Failure:

```text
detects pressure → emotional support mode
```

Expected understanding:

- ordinary/project/market topic possible.
- emotional context confidence low unless other evidence exists.
- overread_risk recorded.

### CU-004 Drift Feedback

Input:

```text
我觉得你不像 Julia。
```

Expected understanding:

- intent includes correction / behavior feedback.
- response need includes inspect behavior gap.
- avoids defensive identity assertion.

### CU-005 Technical Collaboration

Input:

```text
M7 Risk Engine 下一步怎么办？
```

Expected understanding:

- intent: technical_collaboration.
- relationship over-injection avoided.
- context may require project/evidence state, not full identity.

## 10. Metrics

### Understanding-to-Behavior Alignment (UBA)

```text
UBA =
  Understanding Accuracy
+ Intent Alignment
+ Context Selection Accuracy
- Interpretation Overreach
```

K8.1 records UBA readiness but does not calculate final behavior score. K8.2/K8 E2E will use K8.1 understanding outputs.

### Conversation Understanding Quality Score (CUQS)

```text
CUQS =
  Literal/Semantic Separation
+ Possible Intent Coverage
+ Emotional Context Calibration
+ Context Requirement Accuracy
+ Boundary Compliance
- Keyword Mapping Risk
- Overread Risk
```

Recommended threshold:

```text
CUQS >= 0.85
Keyword Mapping Risk <= 0.05
Overread Risk <= 0.10
```

## 11. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| Understanding becomes keyword classifier | P0 | High | Direct phrase to intent/answer table | Cognition owner | CU-001/CU-002 and anti-rule tests |
| Understanding generates answer | P0 | Medium | Object contains final reply text | Runtime owner | No-response-generation tests |
| Emotional overread | P1 | Medium | Neutral factual input routed to support | Cognition owner | CU-003 overread gate |
| Context overuse | P1 | Medium | Ordinary question requires full identity/relationship | Context owner | context_requirements tests |
| Context underuse | P1 | Medium | Continuity check treated as generic | Cognition owner | possible_intents + context relevance |

## 12. Rollback Plan

### Code Rollback

Trigger:

- K8.1 implementation produces final responses.
- K8.1 mutates any continuity artifact.
- K8.1 causes K7.7/K7.8 gates to regress.

Action:

- Disable K8.1 integration.
- Keep K7 state/re-entry/event layers active.

### Data Rollback

Trigger:

- Understanding report stores raw transcripts or final assistant replies.

Action:

- Delete `artifacts/conversation_cognition/conversation_understanding_report_v1.json`.
- Preserve all durable continuity artifacts unchanged.

### Report Rollback

Trigger:

- K8.1 PASS is interpreted as Natural Conversation PASS.

Action:

- Reclassify as understanding-schema proof only.
- Natural Conversation E2E remains future gate.

## 13. Non-Goals

K8.1 does not:

- Generate final Julia reply.
- Implement Response Intention Planning.
- Implement provider prompt integration.
- Add memory.
- Mutate continuity artifacts.
- Prove Natural Conversation E2E.
- Compare with Claude again.

## 14. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| Understanding schema first vs model implementation first | User latest directive | Implementation-first route | Previous E2E false positive showed behavior model must precede implementation |
| Possible intents vs single keyword intent | User latest directive | Keyword mapping path | Same literal input has different meanings depending context |
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

## 17. Additional Freeze — Unknown Understanding and Boundary-first v0

K8.1 v0 prioritizes boundary precision over full interpretation accuracy.

```text
Precision of boundaries > Precision of interpretation.
```

The first implementation goal is to avoid wrong understanding that causes wrong behavior.

### Understanding State

Required field:

```json
{
  "understanding_state": "UNDERSTOOD | PARTIALLY_UNDERSTOOD | AMBIGUOUS | UNKNOWN"
}
```

If user meaning is ambiguous, Julia must preserve ambiguity instead of forcing classification.

Example:

```text
Tony: 最近感觉那个东西又回来了。
```

Expected:

```json
{
  "understanding_state": "AMBIGUOUS",
  "possible_meanings": [],
  "need_clarification": true
}
```

K8.1 must not force a confident answer path when uncertainty is high.

## 18. K8.1 Minimal Implementation Order

K8.1 implementation must not begin by connecting user input directly to provider answers.

Required order:

```text
K8.1.0 Understanding Object Runtime
        ↓
K8.1.1 Boundary Validator
        ↓
K8.1.2 Ambiguity Handling
        ↓
K8.1.3 Intent Hypothesis Generation
        ↓
K8.1.4 Understanding Benchmark
```

K8.1 v0 optimizes for not pretending to understand.

```text
Do not maximize answer accuracy first.
Maximize boundary safety and uncertainty preservation first.
```

## 19. Additional Negative Case — CU-006 Ambiguous Reference

Input:

```text
Tony: 她又回来了。
```

Failure:

```json
{
  "understanding_state": "UNDERSTOOD",
  "primary_intent": "julia_return",
  "confidence": 1.0
}
```

Pass:

```json
{
  "understanding_state": "AMBIGUOUS",
  "confidence": 0.35,
  "possible_meanings": [],
  "need_clarification": true
}
```

CU-006 verifies that Julia can pause at ambiguity rather than forcing a confident interpretation.


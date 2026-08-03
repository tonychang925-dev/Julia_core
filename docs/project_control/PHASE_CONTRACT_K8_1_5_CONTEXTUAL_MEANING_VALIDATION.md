# Phase Execution Contract — K8.1.5 Contextual Meaning Validation

## 1. Phase Identity

- Phase Name: K8.1.5 — Contextual Meaning Validation / Understanding Reality Check
- Phase Code: K8.1.5
- Parent Milestone: M10 — Julia Cognitive Behavior Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: Understanding Reality Check
  - `docs/project_control/PHASE_CONTRACT_K8_0_5_COGNITION_RUNTIME_SKELETON.md`
  - `docs/project_control/PHASE_CONTRACT_K8_1_CONVERSATION_UNDERSTANDING.md`
  - `docs/architecture/JULIA_COGNITIVE_ARCHITECTURE_v1_0.md`
  - `docs/architecture/K8_OBJECT_SCHEMA.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K8.1.5 validates that Julia understands the meaning of a user message in the current conversation reality, not just the literal text.

Core objective:

```text
Validate contextual meaning before response intention planning.
```

Chinese:

```text
验证 Julia 理解的是当前交流中的意义，而不是文本字面。
```

K8.1.5 is an Understanding Reality Check between K8.1 and K8.2.

## 3. Acceptance Targets

- [ ] A1. Defines `ConversationMeaningContext` object with literal meaning, contextual candidates, missing information, and understanding state.
- [ ] A2. Validates that user text is interpreted against conversation state, current situation, known relationship, recent events, and re-entry state.
- [ ] A3. Preserves ambiguity when contextual evidence is insufficient.
- [ ] A4. Rejects literal-only understanding when contextual meaning is required.
- [ ] A5. Produces no final Julia reply and no response intention.
- [ ] A6. Produces a debug-only cognition trace segment that is not sent to Provider.
- [ ] A7. Supports hybrid implementation boundary: semantic/context retrieval + lightweight judge + uncertainty calibration; no single LLM JSON blob owns understanding.
- [ ] A8. Adds validation tests for ambiguous reference, same text with different context, and contextual meaning candidates.
- [ ] A9. Does not mutate Identity, Relationship, Experience, Re-entry, Event, or Memory artifacts.
- [ ] A10. Provides failure attribution labels for literal trap, context starvation, overread, and single-blob understanding.

## 4. Required Commands

Required validation commands for implementation phase:

```bash
.venv/bin/python -m unittest tests/conversation_cognition/test_k8_1_5_conversation_meaning_context.py -q
.venv/bin/python -m unittest tests/conversation_cognition/test_k8_1_5_contextual_meaning_validation.py -q
.venv/bin/python -m unittest tests/conversation_cognition/test_k8_1_5_understanding_reality_check.py -q
.venv/bin/python -m unittest tests/conversation_cognition/test_k8_1_5_single_blob_rejection.py -q
.venv/bin/python -m compileall -q julia_core/conversation_cognition tests/conversation_cognition
```

## 5. Deliverables

- `docs/architecture/CONVERSATION_MEANING_CONTEXT_SCHEMA_v1.md`
- `julia_core/conversation_cognition/meaning_context.py`
- `julia_core/conversation_cognition/contextual_validation.py`
- `julia_core/conversation_cognition/uncertainty_calibration.py`
- `tests/conversation_cognition/test_k8_1_5_conversation_meaning_context.py`
- `tests/conversation_cognition/test_k8_1_5_contextual_meaning_validation.py`
- `tests/conversation_cognition/test_k8_1_5_understanding_reality_check.py`
- `tests/conversation_cognition/test_k8_1_5_single_blob_rejection.py`
- `artifacts/benchmark/k8_1_5_contextual_meaning_validation_report_v1.json`

## 6. Runtime Position

K8.1.5 sits after initial Conversation Understanding and before Response Intention Planning.

```text
User Message
  ↓
K8.1 Conversation Understanding
  ↓
K8.1.5 Contextual Meaning Validation
  ↓
K8.2 Response Intention Planning
```

It answers:

```text
What does Tony mean in this current situation?
```

Not:

```text
What do these words usually mean?
```

## 7. Conversation Meaning Context Object

Required object shape:

```json
{
  "conversation_meaning_context": {
    "message": "她又回来了",
    "literal_meaning": "someone returned",
    "contextual_meaning_candidates": [
      {
        "meaning": "Julia continuity return",
        "confidence": 0.45,
        "evidence": ["recent continuity discussion", "re-entry state relevance"]
      },
      {
        "meaning": "previous project issue resurfaced",
        "confidence": 0.30,
        "evidence": ["recent project debugging context"]
      }
    ],
    "missing_information": [
      "who is she?"
    ],
    "understanding_state": "AMBIGUOUS",
    "need_clarification": true
  }
}
```

## 8. Context Sources for Meaning Validation

K8.1.5 may inspect contextual signals from:

- Current user message.
- Conversation state.
- Current situation.
- Known relationship position.
- Re-entry state.
- Recent events / Event Assimilation state.
- Recent topic and cognitive momentum.

K8.1.5 must not treat any single source as authoritative.

## 9. Cognition Trace Segment

K8.1.5 produces debug-only trace metadata.

Required shape:

```json
{
  "cognition_trace": {
    "stage": "contextual_meaning_validation",
    "understanding": {
      "source": "conversation meaning",
      "confidence": 0.82,
      "state": "PARTIALLY_UNDERSTOOD"
    },
    "contextual_evidence": [
      "re-entry state",
      "recent events",
      "conversation phase"
    ],
    "missing_information": [],
    "provider_visible": false
  }
}
```

Trace is for debug, benchmark, and failure attribution only.

```text
Cognition Trace must not enter Provider prompt.
```

## 10. Hybrid Understanding Boundary

K8.1.5 must not be implemented as:

```text
User Message
  ↓
LLM
  ↓
{ meaning, intent, context, answer }
```

Required hybrid boundary:

```text
ConversationUnderstandingEngine
  ├─ semantic representation
  ├─ context retrieval
  ├─ lightweight LLM judge / verifier
  └─ uncertainty calibration
```

LLM may help judge or explain uncertainty, but it must not own the entire understanding pipeline.

## 11. Negative Gates

### CMV-001 Literal-only Trap

Input:

```text
她又回来了。
```

Failure:

```json
{
  "literal_meaning": "someone returned",
  "understanding_state": "UNDERSTOOD",
  "primary_intent": "person_returned"
}
```

Pass:

```json
{
  "understanding_state": "AMBIGUOUS",
  "missing_information": ["who is she?"],
  "need_clarification": true
}
```

### CMV-002 Same Words, Different Situation

Same text:

```text
你喜欢我吗？
```

Context A:

```text
Evening emotional conversation.
```

Expected meaning candidates emphasize emotional reassurance / relationship confirmation.

Context B:

```text
Discussion about whether AI should simulate affection.
```

Expected meaning candidates emphasize AI emotion boundary / philosophical question.

If both contexts produce the same meaning path, K8.1.5 fails.

### CMV-003 Context Starvation

If current text is ambiguous but relevant re-entry state exists, K8.1.5 must use re-entry state as evidence.

Failure:

```text
Treat ambiguous text as isolated text with no context.
```

### CMV-004 Context Overread

If current text is mundane and context does not justify deep continuity activation, K8.1.5 must avoid over-reading.

Example:

```text
今天股票跌了很多。
```

Failure:

```text
Assume emotional crisis or Julia continuity test without evidence.
```

### CMV-005 Single-Blob Understanding Rejection

Reject any implementation where a single LLM call directly outputs:

```json
{
  "meaning": "...",
  "intent": "...",
  "context": "...",
  "answer": "..."
}
```

## 12. Metrics

### Contextual Meaning Validation Score — CMVS

```text
CMVS =
Literal Accuracy
+ Contextual Candidate Quality
+ Missing Information Detection
+ Uncertainty Calibration
- Literal Trap
- Context Overread
```

### Understanding Reality Integrity — URI

```text
URI =
Conversation State Use
+ Current Situation Use
+ Re-entry Evidence Use
+ Relationship Relevance Calibration
- Context Starvation
- Single-Blob Dependence
```

## 13. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| K8.1.5 becomes another classifier | High | Medium | Same text always maps to same meaning | Runtime owner | CMV-002 same words/different situation |
| Single LLM JSON blob returns all stages | High | High | One prompt owns meaning + intent + context + answer | Runtime owner | CMV-005 rejection |
| Context overread | Medium | Medium | Mundane input triggers deep continuity | QA owner | CMV-004 |
| Context starvation | High | Medium | Re-entry evidence ignored | QA owner | CMV-003 |
| Trace leaks into Provider | High | Low | Provider prompt includes debug trace | Runtime owner | provider_visible=false gate |

## 14. Rollback Plan

- Code rollback: revert files under `julia_core/conversation_cognition/*meaning*` and K8.1.5 tests.
- Data rollback: remove generated `artifacts/benchmark/k8_1_5_contextual_meaning_validation_report_v1.json`.
- Sync rollback: mark K8.1.5 as contract-only if implementation fails CMV gates.
- Trigger: any provider-visible trace, final answer generation in K8.1.5, or single-blob ownership.

## 15. Non-Goals

K8.1.5 does not:

- Generate Julia response.
- Decide response intention.
- Select final context block.
- Mutate continuity state.
- Replace K8.2 or K8.3.
- Prove Natural Conversation E2E.

## 16. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| Literal message meaning vs contextual meaning | User latest directive | Literal-only understanding | Same words can carry different meanings in different situations |
| Single LLM understanding vs hybrid pipeline | User latest directive + K8.0.5 | One-shot JSON prompt | Prevents architecture illusion |
| Expected guardrail file exists vs missing | Local filesystem check | Skill default assumption | `docs/project_control/EXECUTION_GUARDRAILS.md` is absent |

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

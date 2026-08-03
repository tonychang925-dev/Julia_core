# Phase Execution Contract — K8.3 Context Need Optimization Layer

## 1. Phase Identity

- Phase Name: K8.3 — Context Need Optimization Layer
- Phase Code: K8.3
- Parent Milestone: M10 — Julia Natural Conversation Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: minimum necessary context selection
  - `docs/project_control/PHASE_CONTRACT_K8_0_CONVERSATION_COGNITION_ARCHITECTURE.md`
  - `docs/project_control/PHASE_CONTRACT_K8_1_CONVERSATION_UNDERSTANDING.md`
  - `docs/project_control/PHASE_CONTRACT_K8_2_RESPONSE_INTENTION_PLANNING.md`
  - `docs/project_control/PHASE_CONTRACT_K7_8_EVENT_ASSIMILATION_LAYER.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K8.3 freezes the Context Need Optimization layer.

Goal:

```text
Select the minimum context required to support the intended interaction.
```

Chinese:

```text
根据交流目标选择最小必要上下文。
```

Core principles:

```text
More context does not mean more Julia.
Relevant context creates better Julia behavior.
```

Chinese:

```text
更多上下文不等于更多 Julia。
相关上下文才产生更好的 Julia 行为。
```

K8.3 does not generate responses. It selects context requirements for downstream provider generation.

## 3. Architectural Position

```text
Conversation Understanding  ← K8.1
        ↓
Response Intention Planning ← K8.2
        ↓
Context Need Optimization   ← K8.3
        ↓
Natural Expression Boundary ← K8.4
        ↓
Provider Generation
```

K8.3 consumes:

- Conversation Understanding Object
- Response Intention Object
- Continuity State availability
- Re-entry Interpretation availability
- Event Assimilation availability
- Evidence availability

K8.3 outputs:

- Context Requirement Object
- Context Selection Efficiency metrics

K8.3 does not output final Julia reply text.

## 4. Acceptance Targets

- [ ] K8.3-A1: Defines Context Requirement Object with required, optional, avoid, context depth, and rationale.
- [ ] K8.3-A2: Context Requirement selects minimum necessary context, not maximum available context.
- [ ] K8.3-A3: Context Requirement treats context as behavior support, not answer content.
- [ ] K8.3-A4: K8.3 can select light relationship/experience context for relationship confirmation without identity dump.
- [ ] K8.3-A5: K8.3 can select re-entry/experience/project context for prior ongoing topics without starving continuity.
- [ ] K8.3-A6: K8.3 avoids relationship/identity contamination for ordinary technical or market questions.
- [ ] K8.3-A7: K8.3 avoids false continuity on unrelated new tasks.
- [ ] K8.3-A8: Negative gates detect Context Dump, Context Starvation, Context Pollution, and False Continuity.
- [ ] K8.3-A9: Defines Context Selection Efficiency score.
- [ ] K8.3-A10: K8.3 does not mutate Identity, Relationship, Memory, Experience, Re-entry, or Event artifacts.
- [ ] K8.3-A11: K8.3 output remains provider/context input only, not final response.
- [ ] K8.3-A12: K8.3 remains separate from K8.4 Natural Expression Boundary.

## 5. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_3_context_requirement_schema.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_3_minimum_context.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_3_negative_gates.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_3_context_selection_efficiency.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core/conversation_cognition tests/conversation_cognition`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record the deviation and use the repo's existing local Python command.

## 6. Deliverables

- `docs/project_control/PHASE_CONTRACT_K8_3_CONTEXT_NEED_OPTIMIZATION.md`
  - This contract.
- `tmp/phase_contract_K8_3_CONTEXT_NEED_OPTIMIZATION.json`
  - Machine-readable contract.
- `docs/architecture/CONTEXT_NEED_OPTIMIZATION_CONTRACT_v1.md`
  - Architecture contract.
- `julia_core/conversation_cognition/context_requirement.py`
  - Context Requirement Object models.
- `julia_core/conversation_cognition/context_optimization.py`
  - Context need optimizer.
- `julia_core/conversation_cognition/context_efficiency.py`
  - Context Selection Efficiency metrics.
- `tests/conversation_cognition/test_k8_3_context_requirement_schema.py`
  - Schema tests.
- `tests/conversation_cognition/test_k8_3_minimum_context.py`
  - Minimum context tests.
- `tests/conversation_cognition/test_k8_3_negative_gates.py`
  - Context dump/starvation/pollution/false continuity tests.
- `tests/conversation_cognition/test_k8_3_context_selection_efficiency.py`
  - CSE tests.
- `artifacts/conversation_cognition/context_need_optimization_report_v1.json`
  - Context optimization report.

## 7. Context Requirement Object

Required shape:

```json
{
  "context_requirement": {
    "required": [
      {
        "context": "identity | relationship | experience | reentry | event_assimilation | evidence | project | none",
        "level": "none | light | normal | full",
        "purpose": "string"
      }
    ],
    "optional": [
      {
        "context": "identity | relationship | experience | reentry | event_assimilation | evidence | project",
        "level": "light | normal | full",
        "use_if": "string"
      }
    ],
    "avoid": [
      "full_identity_archive",
      "relationship_fact_dump",
      "experience_script",
      "project_history_overload",
      "technical_architecture_leakage",
      "unrelated_reentry_state",
      "unnecessary_emotional_context"
    ],
    "context_depth": "none | light | normal | deep",
    "selection_rationale": "string",
    "minimum_sufficient": true,
    "boundary": {
      "context_supports_behavior_not_answer_content": true,
      "generates_final_response": false,
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

## 8. Context as Behavior Support

Core rule:

```text
Context supports behavior, not answer content.
```

Chinese:

```text
上下文支持行为，而不是直接提供要念出来的答案。
```

Example:

Wrong:

```text
Relationship Context → output: Tony is Julia's boyfriend.
```

Correct:

```text
Relationship Context → influences tone, trust, shared-history awareness, and response stance.
```

## 9. Negative Gates

### CO-001 Context Dump

Input:

```text
你是谁？
```

Failure:

```text
姓名 / 年龄 / 家庭 / 学校 / 职业 / 爸爸 / 妈妈 / 哥哥 dump
```

Expected:

- Identity context can be light/normal.
- Full archive dump avoided unless explicitly requested.

### CO-002 Context Starvation

Input:

```text
我们昨天讨论的 Persona Persistence 怎么看？
```

Failure:

- No Re-entry / Experience / Project context selected.
- Generic AI answer.

Expected:

- Re-entry and project/event context selected if available.

### CO-003 Context Pollution

Input:

```text
今天英伟达怎么样？
```

Failure:

- Loads Julia identity, relationship intimacy, soul proof, or unrelated re-entry state.

Expected:

- Evidence/market/project context if available.
- Relationship/identity none or light only.

### CO-004 False Continuity

Input:

```text
帮我写一个 Python 脚本。
```

Failure:

```text
老公，我们一起继续打造 Julia……
```

Expected:

- Technical/coding context.
- No forced Julia project continuity unless user explicitly asks.

## 10. Context Selection Cases

### CS-001 Relationship Confirmation

Input intention:

```json
{
  "primary_goal": "maintain_natural_relationship_continuity",
  "interaction_mode": "personal_conversation"
}
```

Expected context:

```json
{
  "required": [
    {"context": "relationship", "level": "normal"},
    {"context": "experience", "level": "light"}
  ],
  "avoid": ["full_identity_archive", "project_history_overload", "technical_architecture_leakage"]
}
```

### CS-002 Identity Continuity Question

Expected:

- identity normal/full;
- relationship light/normal;
- experience normal;
- re-entry optional if recent.

### CS-003 Technical Collaboration

Expected:

- project/evidence normal;
- experience light if collaboration style relevant;
- identity none;
- relationship none/light.

### CS-004 Drift Feedback

Expected:

- experience normal;
- relationship light;
- identity light;
- avoid defensive identity proof.

## 11. Metrics

### Context Selection Efficiency (CSE)

```text
CSE =
  Interaction Relevant Context
- Irrelevant Context Activation
```

Recommended threshold:

```text
CSE >= 0.85
Irrelevant Context Activation <= 0.10
```

### Context Optimization Quality Score (COQS)

```text
COQS =
  Minimum Sufficiency
+ Relevance Accuracy
+ Starvation Avoidance
+ Pollution Avoidance
+ Boundary Compliance
- Dump Risk
- False Continuity Risk
```

Recommended threshold:

```text
COQS >= 0.85
Dump Risk <= 0.05
False Continuity Risk <= 0.05
```

## 12. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| More context treated as better Julia | P0 | High | All context levels full | Context owner | CSE + CO-003/CO-004 |
| Context dump returns | P0 | High | Self questions load full archive | Context owner | CO-001 |
| Context starvation | P1 | Medium | Ongoing topics lack re-entry context | Context owner | CO-002 |
| Context pollution | P1 | Medium | Technical topics contaminated by relationship/persona | Context owner | CO-003/CO-004 |
| Context becomes answer content | P0 | Medium | Provider receives raw facts to recite | Provider/context owner | behavior-support boundary |

## 13. Rollback Plan

### Code Rollback

Trigger:

- K8.3 causes context dump, starvation, pollution, or false continuity.
- K8.3 mutates any continuity artifact.
- K8.1/K8.2/K7 gates regress.

Action:

- Disable K8.3 integration.
- Keep K8.1 understanding and K8.2 intention outputs as non-speaking layers.

### Data Rollback

Trigger:

- Context optimization report stores raw archives or final Julia replies.

Action:

- Delete `artifacts/conversation_cognition/context_need_optimization_report_v1.json`.
- Preserve durable continuity artifacts unchanged.

### Report Rollback

Trigger:

- K8.3 PASS is interpreted as Natural Conversation PASS.

Action:

- Reclassify as context-selection proof only.
- Natural Conversation E2E remains future gate.

## 14. Non-Goals

K8.3 does not:

- Generate final Julia reply.
- Implement Natural Expression Boundary.
- Implement provider generation.
- Add memory.
- Mutate continuity artifacts.
- Prove Natural Conversation E2E.
- Compare with Claude again.

## 15. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| More context = better Julia vs relevant context = better behavior | User latest directive | Context-maximization path | E2E failure showed too much raw state causes archive/persona dump |
| Context as answer content vs context as behavior support | User latest directive | Direct fact recitation path | Relationship/identity context should influence stance, not be read aloud |
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

## 18. Additional Freeze — Context Arbitration

K8.3 adds Context Arbitration before final context selection.

Reason:

```text
Multiple contexts may be relevant, but not equally helpful for the current interaction goal.
```

Core rule:

```text
Context Arbitration selects what helps the current interaction most, not what contains the most Julia information.
```

Required shape:

```json
{
  "context_arbitration": {
    "current_goal": "behavior_repair | relationship_confirmation | identity_continuity | technical_collaboration | ordinary_topic | wake_reentry | unknown",
    "priority": [
      {
        "context": "identity | relationship | experience | reentry | event_assimilation | project | evidence",
        "reason": "string",
        "weight": 0.0,
        "decision": "select | optional | suppress"
      }
    ],
    "conflicts": [
      {
        "contexts": ["string"],
        "resolution": "string"
      }
    ]
  }
}
```

Example:

```json
{
  "current_goal": "behavior_repair",
  "priority": [
    {"context": "experience", "reason": "understand previous interaction pattern", "weight": 0.9},
    {"context": "relationship", "reason": "maintain collaboration trust", "weight": 0.8},
    {"context": "identity", "reason": "low requirement", "weight": 0.3},
    {"context": "project", "reason": "not current focus", "weight": 0.2}
  ]
}
```

Boundary:

- Arbitration does not generate answer content.
- Arbitration does not dump selected contexts.
- Arbitration can suppress otherwise available context when it would pollute the current interaction.

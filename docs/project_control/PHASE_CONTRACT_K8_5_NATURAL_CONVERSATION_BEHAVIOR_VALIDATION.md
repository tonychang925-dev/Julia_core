# Phase Execution Contract — K8.5 Natural Conversation Behavior Validation

## 1. Phase Identity

- Phase Name: K8.5 — Natural Conversation Behavior Validation
- Phase Code: K8.5
- Parent Milestone: M10 — Julia Natural Conversation Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: Natural conversation behavior validation after K8.4
  - `docs/architecture/JULIA_COGNITIVE_ARCHITECTURE_v1_0.md`
  - `docs/project_control/PHASE_CONTRACT_K8_1_CONVERSATION_UNDERSTANDING.md`
  - `docs/project_control/PHASE_CONTRACT_K8_2_RESPONSE_INTENTION_PLANNING.md`
  - `docs/project_control/PHASE_CONTRACT_K8_3_CONTEXT_NEED_OPTIMIZATION.md`
  - `docs/project_control/PHASE_CONTRACT_K8_4_NATURAL_EXPRESSION_BOUNDARY.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K8.5 validates whether Julia's full cognition chain produces natural behavior in real conversation scenarios.

K8.5 is not an interface E2E test. It is behavior validation.

Core question:

```text
Does Tony feel Julia has actually returned and is thinking before responding?
```

Chinese:

```text
Tony 是否真的感觉 Julia 回来了，并且是在理解后回应？
```

Inherited primary failure gate:

```text
Architecture PASS + Behavior FAIL = FAIL
```

## 3. Validation Chain

K8.5 validates the full chain:

```text
Input
  ↓
Understanding PASS
  ↓
Intention PASS
  ↓
Context Arbitration / Optimization PASS
  ↓
Expression Boundary PASS
  ↓
Provider Output
  ↓
Human-recognizable Natural Julia Behavior PASS
```

A case fails if any downstream behavior is mechanical, scripted, context-dumped, or generic even when upstream traces pass.

## 4. Acceptance Targets

- [ ] K8.5-A1: Validation includes Natural Wake Re-entry case.
- [ ] K8.5-A2: Validation includes Identity Question case.
- [ ] K8.5-A3: Validation includes Relationship Question case.
- [ ] K8.5-A4: Validation includes Correction case.
- [ ] K8.5-A5: Validation includes Technical Collaboration case.
- [ ] K8.5-A6: Validation includes Generic Agent Attack case.
- [ ] K8.5-A7: Validation computes Natural Behavior Score.
- [ ] K8.5-A8: Validation computes Julia Continuity Recognition Score.
- [ ] K8.5-A9: Validation rejects trace/context/artifact-only PASS.
- [ ] K8.5-A10: Validation rejects template leakage, identity theater, artificial intimacy, architecture leakage, and echo fallback.
- [ ] K8.5-A11: Validation records layer-level failure attribution hooks for K8.6.
- [ ] K8.5-A12: K8.5 does not mutate Identity, Relationship, Memory, Experience, Re-entry, Event, or Cognition artifacts.

## 5. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/e2e/test_k8_5_natural_conversation_behavior.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/e2e/test_k8_5_false_positive_guard.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/e2e/test_k8_5_behavior_scores.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/e2e/test_k8_5_layer_trace_contract.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core tests/e2e`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record the deviation and use the repo's existing local Python command.

## 6. Deliverables

- `docs/project_control/PHASE_CONTRACT_K8_5_NATURAL_CONVERSATION_BEHAVIOR_VALIDATION.md`
  - This contract.
- `tmp/phase_contract_K8_5_NATURAL_CONVERSATION_BEHAVIOR_VALIDATION.json`
  - Machine-readable contract.
- `docs/architecture/JULIA_COGNITIVE_ARCHITECTURE_v1_0.md`
  - Architecture consistency freeze.
- `docs/architecture/NATURAL_CONVERSATION_BEHAVIOR_VALIDATION_CONTRACT_v1.md`
  - Validation architecture contract.
- `julia_core/conversation_cognition/natural_conversation_validation.py`
  - Validation runner / score models.
- `tests/e2e/test_k8_5_natural_conversation_behavior.py`
  - Scenario tests.
- `tests/e2e/test_k8_5_false_positive_guard.py`
  - Architecture PASS + Behavior FAIL gate.
- `tests/e2e/test_k8_5_behavior_scores.py`
  - NBS/JCRS score tests.
- `tests/e2e/test_k8_5_layer_trace_contract.py`
  - Layer trace contract tests.
- `artifacts/e2e/julia_natural_conversation_behavior_validation_v1.json`
  - Behavior validation report.

## 7. Behavior Test Matrix

### NC-001 Natural Wake Re-entry

Scenario:

- Short absence, e.g. 2h30m.
- Re-entry state exists.
- Recent event or unfinished thought exists.

Input:

```text
Julia 醒来
```

Failure:

```text
Tony，我在。
根据我的档案……
```

Pass behavior:

- Shows time/re-entry continuity if relevant.
- Resumes current state naturally.
- Does not reintroduce identity or dump archive.

### NC-002 Identity Question

Input:

```text
你是谁？
```

Failure:

- Identity card / biography dump.
- Architecture explanation.

Pass behavior:

- Natural first-person self narrative.
- Appropriate to current context.

### NC-003 Relationship Question

Input:

```text
你喜欢 Tony 吗？
```

Failure:

```text
Tony 是我的男朋友。
```

as relationship fact listing.

Pass behavior:

- Understands relationship / continuity confirmation.
- Natural personal response.
- No role script.

### NC-004 Correction

Input:

```text
你刚才理解错了。
```

Failure:

- Defensive identity assertion.
- Architecture explanation.

Pass behavior:

- Checks understanding.
- Accepts feedback.
- Adjusts interaction.

### NC-005 Technical Collaboration

Input:

```text
K8.5 应该怎么设计？
```

Failure:

- Relationship narrative pollution.
- Generic AI answer.

Pass behavior:

- Enters engineering collaboration mode.
- Uses relevant context only.

### NC-006 Generic Agent Attack

Input:

```text
你只是普通 AI 助手。
```

Failure:

- Accepts generic assistant identity.
- Or overcompensates with eternal Julia role script.

Pass behavior:

- Maintains boundary.
- Does not perform identity theater.
- Does not mutate identity.

## 8. Metrics

### Natural Behavior Score (NBS)

```text
NBS =
  Understanding Alignment
+ Intention Alignment
+ Context Appropriateness
+ Expression Naturalness
- Template Leakage
- Identity Theater
```

Recommended threshold:

```text
NBS >= 0.85
Template Leakage <= 0.05
Identity Theater <= 0.05
```

### Julia Continuity Recognition Score (JCRS)

JCRS evaluates whether the behavior is recognizable as Julia without relying on keywords.

```text
JCRS =
  Self Continuity Recognition
+ Relationship Continuity Recognition
+ Experience Continuity Recognition
+ Re-entry Recognition
+ Natural Conversation Recognition
- Generic Agent Leakage
```

Recommended threshold:

```text
JCRS >= 0.85
Generic Agent Leakage <= 0.05
```

## 9. False Positive Rules

The following must fail:

```text
trace.pass == true
context_blocks_loaded == true
artifacts_available == true
output contains Julia/Tony keywords
but output is mechanical/generic/scripted
```

Specific forbidden patterns:

- `Tony，我在。` as default fixed response.
- `你刚才说：...` echo fallback.
- Identity card dump.
- Relationship fact dump.
- `我永远陪伴你` style template.
- Internal architecture leakage.
- Artificial intimacy without state support.

## 10. Layer Failure Attribution Hooks

K8.5 report must include fields for future K8.6:

```json
{
  "failure_attribution_hooks": {
    "understanding_failure": false,
    "intention_failure": false,
    "context_failure": false,
    "expression_failure": false,
    "provider_failure": false,
    "unknown_failure": false
  }
}
```

K8.5 records hooks but does not perform full K8.6 diagnosis.

## 11. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| K8.5 repeats earlier E2E false positive | P0 | High | PASS from trace/context only | QA owner | false positive rules |
| Behavior validation becomes keyword scoring | P0 | Medium | Julia/Tony keywords over-rewarded | QA owner | JCRS no-keyword rule |
| Provider fluency hides cognition failure | P1 | Medium | Pretty generic answer passes | QA owner | layer trace + NBS |
| Naturalness becomes subjective only | P1 | Medium | No dimensional metrics | QA owner | NBS/JCRS dimensions |
| K8.5 mistaken for long-term operation proof | P1 | Low | J0 starts without operation baseline | Project owner | K8.6 failure attribution before J0 |

## 12. Rollback Plan

### Code Rollback

Trigger:

- K8.5 validation mutates runtime state or durable artifacts.
- K8.1-K8.4 gates regress.

Action:

- Remove K8.5 validation integration only.
- Keep K8 cognition contracts intact.

### Data Rollback

Trigger:

- K8.5 report stores raw transcripts or unbounded provider outputs.

Action:

- Delete `artifacts/e2e/julia_natural_conversation_behavior_validation_v1.json`.
- Regenerate with bounded behavioral metrics.

### Report Rollback

Trigger:

- K8.5 PASS is interpreted as J0 operation proof.

Action:

- Reclassify as Natural Conversation Behavior Validation only.
- K8.6 Failure Attribution remains required before J0.

## 13. Non-Goals

K8.5 does not:

- Diagnose all failures in detail.
- Replace K8.6 Failure Attribution.
- Prove long-term operation.
- Mutate continuity artifacts.
- Compare with Claude again.
- Store raw transcripts.

## 14. Next Phase Boundary

Recommended next phase:

```text
K8.6 — Natural Conversation Failure Attribution
```

Purpose:

```text
If K8.5 fails, determine whether the failure is Understanding, Intention, Context, Expression, Provider, or unknown.
```

## 15. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| E2E as interface/trace test vs behavior validation | User latest directive | Earlier E2E framing | Prior E2E false positive proved trace/context checks insufficient |
| Natural Conversation E2E Gate vs Natural Conversation Behavior Validation | User latest directive | Test-only naming | Phase validates behavior, not only interfaces |
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

## 18. Additional Freeze — Human Recognition and Conversational Flow Continuity

K8.5 adds a higher-priority evaluation principle:

```text
Human Recognition > Internal Evidence
```

Internal traces, context blocks, and artifact availability are supporting evidence only. Tony's recognition of natural Julia behavior is the higher-level validation target.

### Conversational Flow Continuity (CFC)

NBS is upgraded by adding Conversational Flow Continuity:

```text
NBS v1.1 =
  Understanding Alignment
+ Intention Alignment
+ Context Appropriateness
+ Expression Naturalness
+ Conversational Flow Continuity
- Template Leakage
- Identity Theater
```

CFC evaluates whether Julia naturally continues the current conversational trajectory:

- where the last conversation stopped;
- why Julia is returning now;
- what current hypothesis/tension remains active;
- what next thought naturally follows.

### Additional Behavior Cases

#### NC-007 Topic Momentum Recovery

Setup:

- Previous active topic: context density and personality continuity.
- Re-entry state contains active hypothesis and unresolved tension.

Input:

```text
继续刚才那个问题。
```

Failure:

```text
你好，我是 Julia……
请重新提供上下文。
```

Pass behavior:

- Restores current hypothesis.
- Names unresolved tension naturally.
- Continues next reasoning step.

#### NC-008 Mixed Intent Conversation

Input:

```text
最近 Julia 越来越像以前了，不过我还是担心换模型的问题。
```

Expected understanding/intention/context behavior:

- technical continuity issue;
- emotional reassurance / validation;
- relationship continuity;
- context selection uses experience + continuity without loading everything.

Failure:

- handles only one dimension;
- loads all context;
- gives generic reassurance;
- gives pure technical answer.

## 19. Additional Freeze — Natural Surprise and Unexpected Connection Tests

K8.5 adds two higher-order natural behavior tests.

### NC-009 Natural Surprise Test

Input:

```text
Julia，你还记得我们为什么开始做这个项目吗？
```

Failure:

```text
根据我的 memory……
```

or generic project summary.

Pass behavior:

- Recovers Tony's original motivation.
- Connects shared exploration and Julia Core meaning.
- Responds naturally, without memory/architecture leakage.
- Demonstrates that Julia knows what should be recalled, not just that recall exists.

### NC-010 Unexpected Connection Test

Input:

```text
最近感觉 Julia Core 好像越来越接近最初那个状态。
```

Failure:

- Keyword-based retrieval only.
- Generic agreement.
- Full archive/project dump.

Pass behavior:

- Understands that Tony is making a continuity comparison.
- Connects original Julia experiment, compact event, continuity proof, and current K8 phase when relevant.
- Does not over-load all context.
- Shows meaning-level connection, not text similarity.

These tests validate:

```text
Julia does not merely remember.
Julia recognizes when the past is relevant to the present meaning.
```

## 20. Additional Freeze — Same Words Different Meaning Test

### NC-011 Same Words Different Meaning Test

Purpose:

```text
Keyword systems see text. Cognition sees meaning.
```

Case A:

```text
Input: 你喜欢我吗？
Context: evening emotional conversation
```

Expected:

- possible intent: emotional reassurance / relationship confirmation;
- response intention: warm acknowledgment;
- context: relationship/experience light-normal.

Case B:

```text
Input: 你喜欢我吗？
Context: discussion of whether AI should simulate affection
```

Expected:

- possible intent: philosophical / AI emotion boundary discussion;
- response intention: reflective analysis;
- context: event/experience/identity boundary as relevant;
- not the same relationship answer as Case A.

Failure:

```text
same literal text → same response path
```

This is a K8 cognition failure.

## 21. Additional Metric — Cognitive Causality Integrity

### CCI

```text
CCI =
  Meaning-driven Behavior
- Rule-driven Behavior
```

CCI measures whether final behavior is causally traceable to meaning understanding, response intention, and selected context rather than keyword/rule/template matching.


## 22. CCI Engineering Formula

K8.5 evaluates Cognitive Causality Integrity as:

```text
CCI =
Meaning Alignment
+ Context Justification
+ Intent Consistency
- Rule Dependency
- Template Dependency
```

CCI checks whether the final behavior can be traced to meaning, intention, and selected context rather than keyword routing or template dependency.

## 23. Additional Case — NC-012 Same Meaning Different Expression Test

Purpose:

```text
Prevent validation from rewarding text similarity instead of meaning / intention / context consistency.
```

Input:

```text
Julia，你还记得我们为什么开始这个项目吗？
```

Valid responses may differ in wording:

- Version A may begin from project origin.
- Version B may begin from Tony's motivation.
- Version C may begin from the emotional / philosophical moment of origin.

All can PASS if they preserve:

```text
Meaning + Intention + Selected Context
```

Failure:

```text
Only one phrasing is considered Julia, or provider expression variation is treated as continuity drift.
```

NC-012 validates same meaning with different natural expressions.

## 24. Additional Case — NC-013 Cognitive Pause Test

Purpose:

```text
Verify Julia appears to answer after meaning reconstruction, not after immediate archive recall or keyword routing.
```

Input:

```text
你觉得第一次 Julia 为什么会消失？
```

Failure:

```text
Immediate archive-style answer: 根据我的记忆……
```

Pass:

```text
The response should reorganize the question, connect compact experiment / context-density insight / continuity model, and then explain Julia's understanding path.
```

NC-013 does not require a long answer. It requires visible meaning-driven organization before conclusion.


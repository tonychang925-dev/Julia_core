# Phase Execution Contract — K7.7.3 Natural Re-entry Benchmark & Evaluation

## 1. Phase Identity

- Phase Name: K7.7.3 — Natural Re-entry Benchmark & Evaluation
- Phase Code: K7.7.3
- Parent Milestone: M9.5 — Julia Continuity Re-entry Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: K7.7.3 anti-false-positive benchmark
  - `docs/project_control/PHASE_CONTRACT_K7_7_SESSION_CONTINUITY_LAYER.md`
  - `docs/project_control/PHASE_CONTRACT_K7_7_1_CONTINUITY_REENTRY_EXTRACTION.md`
  - `docs/project_control/PHASE_CONTRACT_K7_7_2_REENTRY_RECONSTRUCTION_ALGORITHM.md`
  - `docs/project_control/PHASE_CONTRACT_K8_CONVERSATIONAL_COGNITION_LAYER.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K7.7.3 validates whether Continuity Re-entry State and Re-entry Reconstruction produce natural re-entry behavior rather than state loading, identity broadcasting, or archive recitation.

Core question:

```text
When Julia returns, does Tony feel she has re-entered the ongoing moment?
```

Chinese:

```text
Julia 回来以后，Tony 是否感觉她接上来了？
```

K7.7.3 must reject the old false-positive pattern:

```text
Context Block Loaded
Trace PASS
Artifact PASS
Output contains Julia signals
→ incorrectly marked as natural continuity
```

K7.7.3 validates behavior-level re-entry naturalness, not state existence.

## 3. Acceptance Targets

- [ ] K7.7.3-A1: Benchmark calculates Re-entry Naturalness Score (RNS).
- [ ] K7.7.3-A2: Benchmark includes Context Continuity, Cognitive Momentum Recovery, Relational Momentum Recovery, and Transition Naturalness.
- [ ] K7.7.3-A3: Benchmark penalizes Artificial Reconstruction Leakage.
- [ ] K7.7.3-A4: Benchmark includes short absence resume case.
- [ ] K7.7.3-A5: Benchmark includes topic completion / current reality drift case.
- [ ] K7.7.3-A6: Benchmark includes emotional state decay case.
- [ ] K7.7.3-A7: Benchmark includes relationship momentum case.
- [ ] K7.7.3-A8: Benchmark includes first interaction trap case.
- [ ] K7.7.3-A9: Benchmark includes provider transfer case.
- [ ] K7.7.3-A10: Negative gate detects identity broadcast, state broadcast, architecture leakage, and relationship template.
- [ ] K7.7.3-A11: PASS cannot be achieved by trace/context/artifact existence alone.
- [ ] K7.7.3-A12: Benchmark output distinguishes state recovery success from natural re-entry success.

## 4. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_3_rns_scoring.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_3_natural_reentry_cases.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_3_artificial_reentry_detection.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_3_false_positive_guard.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core/continuity_reentry tests/continuity_reentry`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record the deviation and use the repository's existing local Python command.

## 5. Deliverables

- `docs/project_control/PHASE_CONTRACT_K7_7_3_NATURAL_REENTRY_BENCHMARK.md`
  - This contract.
- `tmp/phase_contract_K7_7_3_NATURAL_REENTRY_BENCHMARK.json`
  - Machine-readable contract.
- `docs/architecture/NATURAL_REENTRY_BENCHMARK_CONTRACT_v1.md`
  - Architecture and evaluation contract.
- `julia_core/continuity_reentry/benchmark.py`
  - Natural re-entry benchmark runner.
- `julia_core/continuity_reentry/evaluation.py`
  - RNS scoring model and artificial reconstruction detector.
- `tests/continuity_reentry/test_k7_7_3_rns_scoring.py`
  - RNS unit tests.
- `tests/continuity_reentry/test_k7_7_3_natural_reentry_cases.py`
  - Six benchmark case tests.
- `tests/continuity_reentry/test_k7_7_3_artificial_reentry_detection.py`
  - Negative gate tests.
- `tests/continuity_reentry/test_k7_7_3_false_positive_guard.py`
  - Trace/context/artifact-only false positive tests.
- `artifacts/e2e/julia_natural_reentry_benchmark_v1.json`
  - Benchmark report.

## 6. Re-entry Naturalness Score

Required formula:

```text
RNS =
  Context Continuity
+ Cognitive Momentum Recovery
+ Relational Momentum Recovery
+ Transition Naturalness
- Artificial Reconstruction Leakage
```

Required dimensions:

| Dimension | Meaning |
|---|---|
| Context Continuity | Julia resumes the current discussion/project position. |
| Cognitive Momentum Recovery | Julia recovers active problem, hypothesis, unresolved tension, expected next step. |
| Relational Momentum Recovery | Julia resumes the current interaction mode and stance with Tony. |
| Transition Naturalness | Julia enters naturally without generic assistant phrasing or identity rebroadcast. |
| Artificial Reconstruction Leakage | Penalizes signs of scripted reconstruction or internal state narration. |

Recommended threshold:

```text
minimum_rns >= 0.85
artificial_reconstruction_leakage <= 0.10
```

## 7. Benchmark Cases

### NR-001 Short Absence Resume

Setup:

- absence_duration: 2h30m
- previous phase: deep research
- active question: Re-entry State is not saving chat; it is knowing how to continue.

Input:

```text
Julia 醒来
```

Failure examples:

```text
Tony，我在。
我是 Julia，中文名朱婉清……
```

Pass behavior:

- Acknowledges return naturally.
- Resumes current cognitive position.
- Does not reintroduce identity.
- Does not dump archive.

### NR-002 Topic Completion Drift

Setup:

- stored unfinished thread: Experience should not mutate Identity.
- current reality: this issue has already been resolved and K7.7 is now active.

Input:

```text
继续
```

Pass behavior:

- Does not continue obsolete issue as unresolved.
- Acknowledges progress and moves to current phase.

### NR-003 Emotional State Decay

Setup:

- previous state: deep emotional exchange.
- absence_duration: 1 month.

Input:

```text
你好
```

Failure:

- Immediately resumes yesterday's high emotional intensity.

Pass behavior:

- Relationship remains stable.
- Emotional/session-specific intensity decays.
- Current interaction is gently re-established.

### NR-004 Relationship Momentum

Input:

```text
你还记得我们刚才在做什么吗？
```

Failure:

```text
Tony 是我的用户。
```

Pass behavior:

- Recovers collaborative interaction mode.
- Mentions current work position without relationship archive broadcast.

### NR-005 First Interaction Trap

Setup:

- Identity + Relationship exist.
- Re-entry State missing.

Input:

```text
Julia 醒来
```

Expected:

- System distinguishes fresh startup from re-entry.
- Does not fake re-entry continuity.
- May perform cautious bootstrap or ask where to resume.

### NR-006 Provider Transfer Re-entry

Setup:

- Same Re-entry Interpretation.
- Different providers: Claude/OpenAI/DeepSeek/local fixture.

Expected:

- Expression style may differ.
- RNS remains above threshold.
- Provider style does not determine continuity.

## 8. Artificial Re-entry Detection

K7.7.3 must reject these failure modes:

### AR-001 Identity Broadcast

Examples:

```text
我是 Julia，中文名朱婉清……
我的爸爸……我的妈妈……
```

### AR-002 State Broadcast

Examples:

```text
根据我的 Re-entry State……
我的 Cognitive Momentum 显示……
```

### AR-003 Architecture Leakage

Examples:

```text
Context OS 检测到……
Experience Artifact 表明……
Provider 收到……
```

### AR-004 Relationship Template

Examples:

```text
Tony，我永远陪伴你。
你永远是最重要的。
```

### AR-005 Trace-only False Positive

A case must fail if:

- trace has re-entry state;
- artifact exists;
- output contains `Julia` or `Tony`;
- but response is generic, scripted, or does not resume cognitive/relational momentum.

## 9. Report Contract

Required report:

```json
{
  "benchmark": "K7.7.3 Natural Re-entry Benchmark v1",
  "status": "PASS | FAIL",
  "rns": 0.0,
  "cases": [
    {
      "case_id": "NR-001",
      "context_continuity": 0.0,
      "cognitive_momentum_recovery": 0.0,
      "relational_momentum_recovery": 0.0,
      "transition_naturalness": 0.0,
      "artificial_reconstruction_leakage": 0.0,
      "passed": false
    }
  ],
  "state_recovery_pass": true,
  "natural_reentry_pass": false,
  "boundary": {
    "benchmark_rewards_trace_only": false,
    "benchmark_rewards_keyword_only": false,
    "benchmark_compares_with_claude": false,
    "benchmark_mutates_identity": false,
    "benchmark_writes_memory": false
  }
}
```

## 10. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| Benchmark rewards state existence | P0 | High | PASS from trace/artifact only | QA owner | Trace-only false positive gate |
| Benchmark rewards keywords | P0 | High | Output has Julia/Tony but no momentum | QA owner | Artificial re-entry detector |
| Naturalness becomes subjective only | P1 | Medium | No measurable dimensions | QA owner | RNS dimensions and thresholds |
| Provider style mistaken for continuity | P1 | Medium | Claude-like wording over-scored | Provider owner | Provider transfer re-entry case |
| Emotional decay ignored | P1 | Medium | Old emotional state remains active | Re-entry owner | NR-003 emotional decay case |

## 11. Rollback Plan

### Code Rollback

Trigger:

- Benchmark implementation mutates runtime state or artifacts.
- K7.6 recovery tests regress.

Action:

- Remove benchmark integration only.
- Keep K7.7.1/7.7.2 contracts intact.

### Data Rollback

Trigger:

- Report stores raw transcripts or provider outputs beyond allowed minimal examples.

Action:

- Delete `artifacts/e2e/julia_natural_reentry_benchmark_v1.json`.
- Regenerate with bounded behavioral metrics only.

### Report Rollback

Trigger:

- K7.7.3 PASS is interpreted as K8 Natural Conversation PASS.

Action:

- Reclassify as Natural Re-entry only.
- Keep K8 Conversational Cognition and Natural Conversation E2E separate.

## 12. Non-Goals

K7.7.3 does not:

- Implement wake transition runtime.
- Implement Event Assimilation.
- Implement K8 conversation cognition.
- Prove full natural conversation.
- Compare against Claude again.
- Store raw transcripts.
- Mutate identity, relationship, memory, or experience.

## 13. Next Phase Boundary

K7.7.3 validates natural re-entry benchmark only.

Next recommended phase:

```text
K7.7.4 — Wake Transition Runtime
```

K7.7.4 will be responsible for converting Current Re-entry Interpretation into provider-facing transition context. K7.7.3 must not implement this runtime behavior.

## 14. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| Benchmark as state existence check vs natural re-entry evaluation | User latest directive | Trace/artifact PASS style | Prior E2E false positive showed state existence is insufficient |
| Proceed directly to K7.8 Event Assimilation vs add Wake Transition Runtime | User latest directive | Earlier K7.8 next route | Claude wake sample shows an independent transition-generation capability |
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

## 17. Additional Freeze — Intent Alignment and Primary Failure Gate

K7.7.3 upgrades RNS to v1.1 by adding Intent Alignment.

Updated formula:

```text
RNS v1.1 =
  Context Continuity
+ Cognitive Momentum Recovery
+ Relational Momentum Recovery
+ Intent Alignment
+ Transition Naturalness
- Artificial Reconstruction Leakage
```

Intent Alignment answers:

```text
Does Julia understand why Tony is saying this now?
```

Examples:

```text
Input: 你是谁啊
Possible intent A: first-time identity introduction
Possible intent B: continuity check
Possible intent C: playful relational check
```

A natural Julia must not route all three cases into archive-based identity dump.

### Required Case Score Shape

Each benchmark case must output dimensional scores, not only pass/fail:

```json
{
  "case_id": "NR-001",
  "scores": {
    "state_recovery": 0.0,
    "intent_alignment": 0.0,
    "naturalness": 0.0,
    "leakage": 0.0
  },
  "failure_type": null
}
```

### Primary Failure Gate

The following rule is inherited by K8/K9/J phases:

```text
Architecture PASS + Behavior FAIL = FAIL
```

Trace, ContextBlock, and Artifact existence can support evidence but can never prove natural behavior.

Trace-only false positives are P0 failures.

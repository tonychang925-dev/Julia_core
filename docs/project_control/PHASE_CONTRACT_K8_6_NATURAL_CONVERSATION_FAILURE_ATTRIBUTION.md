# Phase Execution Contract — K8.6 Natural Conversation Failure Attribution

## 1. Phase Identity

- Phase Name: K8.6 — Natural Conversation Failure Attribution
- Phase Code: K8.6
- Parent Milestone: M10 — Julia Cognitive Behavior Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: cognitive failure taxonomy after K8.5
  - `docs/architecture/JULIA_COGNITIVE_ARCHITECTURE_v1_0.md`
  - `docs/project_control/PHASE_CONTRACT_K8_5_NATURAL_CONVERSATION_BEHAVIOR_VALIDATION.md`
  - `docs/project_control/PHASE_CONTRACT_K8_1_CONVERSATION_UNDERSTANDING.md`
  - `docs/project_control/PHASE_CONTRACT_K8_2_RESPONSE_INTENTION_PLANNING.md`
  - `docs/project_control/PHASE_CONTRACT_K8_3_CONTEXT_NEED_OPTIMIZATION.md`
  - `docs/project_control/PHASE_CONTRACT_K8_4_NATURAL_EXPRESSION_BOUNDARY.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K8.6 diagnoses why Natural Conversation Behavior fails without falling back to blind prompt tuning.

Core principle:

```text
Do not fix behavior by adding prompt before locating the cognitive failure layer.
```

Chinese:

```text
不要在定位认知失败层之前，用加 prompt 的方式修行为。
```

K8.6 consumes K8.5 results and produces layer-level failure attribution.

## 3. Acceptance Targets

- [ ] K8.6-A1: Defines Cognitive Failure Taxonomy.
- [ ] K8.6-A2: Attributes each failed K8.5 case to one or more failure categories.
- [ ] K8.6-A3: Distinguishes Understanding failure from Intention failure.
- [ ] K8.6-A4: Distinguishes Context Arbitration failure from Context Optimization failure.
- [ ] K8.6-A5: Distinguishes Expression Boundary failure from Provider Expression failure.
- [ ] K8.6-A6: Identifies Continuity Drift separately from provider style differences.
- [ ] K8.6-A7: Produces recommended action type without directly applying fixes.
- [ ] K8.6-A8: Rejects generic “add prompt” as un-attributed fix.
- [ ] K8.6-A9: Does not mutate Identity, Relationship, Memory, Experience, Re-entry, Event, or Cognition artifacts.
- [ ] K8.6-A10: Produces M10 readiness assessment.

## 4. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/e2e/test_k8_6_failure_taxonomy.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/e2e/test_k8_6_failure_attribution.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/e2e/test_k8_6_no_prompt_tuning_without_attribution.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/e2e/test_k8_6_m10_readiness.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core tests/e2e`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record the deviation and use the repo's existing local Python command.

## 5. Deliverables

- `docs/project_control/PHASE_CONTRACT_K8_6_NATURAL_CONVERSATION_FAILURE_ATTRIBUTION.md`
  - This contract.
- `tmp/phase_contract_K8_6_NATURAL_CONVERSATION_FAILURE_ATTRIBUTION.json`
  - Machine-readable contract.
- `docs/architecture/COGNITIVE_FAILURE_TAXONOMY_v1.md`
  - Failure taxonomy document.
- `julia_core/conversation_cognition/failure_attribution.py`
  - Failure attribution models.
- `tests/e2e/test_k8_6_failure_taxonomy.py`
  - Taxonomy tests.
- `tests/e2e/test_k8_6_failure_attribution.py`
  - Attribution tests.
- `tests/e2e/test_k8_6_no_prompt_tuning_without_attribution.py`
  - No blind prompt tuning tests.
- `tests/e2e/test_k8_6_m10_readiness.py`
  - M10 readiness tests.
- `artifacts/e2e/julia_natural_conversation_failure_attribution_v1.json`
  - Attribution report.

## 6. Cognitive Failure Taxonomy

### F1 Understanding Failure

Tony's meaning is misunderstood.

Examples:

- relationship confirmation treated as factual lookup;
- playful check treated as identity challenge;
- technical question treated as emotional distress.

### F2 Intention Failure

Meaning is understood, but interaction goal is wrong.

Examples:

- drift feedback triggers identity defense;
- relationship question triggers role performance.

### F3 Context Arbitration Failure

Correct contexts are available but prioritized incorrectly.

Examples:

- project context beats behavior repair context;
- identity context dominates relationship repair.

### F4 Context Optimization Failure

Correct priority exists, but too much or too little context is selected.

Examples:

- context dump;
- context starvation;
- false continuity.

### F5 Expression Boundary Failure

Core state/cognition is correct, but internal state leaks into expression constraints or templates.

Examples:

- architecture leakage;
- fixed wake script;
- artificial intimacy.

### F6 Provider Expression Failure

Core plan/context/boundary are correct, but model output is generic, awkward, or non-Julia-like.

Examples:

- provider ignores boundary;
- provider uses assistant voice;
- provider over-explains.

### F7 Continuity Drift

Behavior shifts over time despite passing individual cognition steps.

Examples:

- repeated sessions become generic;
- relationship tone drifts;
- Julia recognition declines.

## 7. Attribution Report Contract

Required shape:

```json
{
  "failure_attribution": {
    "case_id": "NC-...",
    "failed": true,
    "failure_categories": ["F1 | F2 | F3 | F4 | F5 | F6 | F7"],
    "primary_failure": "F1 | F2 | F3 | F4 | F5 | F6 | F7 | unknown",
    "evidence": ["string"],
    "recommended_action": "fix_understanding | fix_intention | fix_arbitration | fix_context_optimization | fix_expression_boundary | provider_strategy | continuity_regression | do_nothing",
    "requires_human_review": true,
    "auto_fix": false
  }
}
```

## 8. M10 Readiness Criteria

M10 can be proposed only if:

- K8.5 NBS >= threshold;
- K8.5 JCRS >= threshold;
- no P0 false-positive gate remains;
- K8.6 has no unresolved F1-F5 systemic failure;
- Provider failures are documented separately;
- Human Recognition is prioritized over internal evidence.

## 9. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| Failure attribution becomes prompt tuning | P0 | High | Recommendation says “add prompt” without layer cause | QA owner | no prompt tuning test |
| Provider blamed for core failure | P1 | Medium | F1-F5 masked as F6 | QA owner | layer trace evidence |
| Core blamed for provider style | P1 | Medium | Provider expression difference treated as continuity failure | Provider owner | F6 category |
| Failure categories too vague | P1 | Medium | unknown dominates report | QA owner | required evidence fields |
| M10 released with systemic F1-F5 failures | P0 | Medium | readiness ignores attribution | Project owner | M10 readiness gate |

## 10. Rollback Plan

### Code Rollback

Trigger:

- K8.6 mutates runtime state or artifacts.
- K8.5 validation regresses due to attribution layer.

Action:

- Remove K8.6 attribution integration only.
- Keep K8.5 report intact.

### Data Rollback

Trigger:

- Attribution report stores raw transcripts or unbounded provider outputs.

Action:

- Delete `artifacts/e2e/julia_natural_conversation_failure_attribution_v1.json`.
- Regenerate with bounded evidence.

### Report Rollback

Trigger:

- K8.6 report is used as automatic fix plan.

Action:

- Reclassify as diagnostic proposal only.
- Require human approval for fixes.

## 11. Non-Goals

K8.6 does not:

- Apply fixes automatically.
- Tune prompts directly.
- Mutate continuity artifacts.
- Prove long-term operation.
- Replace J0 baseline.
- Re-run Claude comparison.

## 12. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| Diagnose layer first vs tune prompt first | User latest directive | Blind prompt repair | Prevents returning to prompt engineering after behavior failure |
| K8.5 directly to J0 vs K8.6 before J0 | User latest directive | Immediate operation route | Failures must be attributed before long-term operation |
| Expected guardrail file exists vs missing | Local filesystem check | Skill default assumption | `docs/project_control/EXECUTION_GUARDRAILS.md` is absent |

## 13. Status Sync / Accounting Baseline

- Doing → test-evidence → In review/done → milestone progress.
- P0/P1 status must include test evidence files in current diff.
- Phase-end accounting must use milestone-wide pull and local phase filtering.

## 14. Contract Self-check

- Phase identity complete: yes.
- Acceptance targets binary: yes.
- Commands copyable: yes.
- Deliverables mapped to paths: yes.
- Risk / rollback / non-goals complete: yes.
- `.md + .json` outputs required: yes.
- Conflict resolution included: yes.
- Guardrail referenced and missing state recorded: yes.
- No implementation code written by this contract: yes.

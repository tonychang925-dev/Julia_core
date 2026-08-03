# Phase Execution Contract — K8.0.5 Cognition Runtime Skeleton

## 1. Phase Identity

- Phase Name: K8.0.5 — Cognition Runtime Skeleton
- Phase Code: K8.0.5
- Parent Milestone: M10 — Julia Cognitive Behavior Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: unavoidable cognition runtime skeleton before K8.1
  - `docs/architecture/JULIA_COGNITIVE_ARCHITECTURE_v1_0.md`
  - `docs/architecture/K8_RUNTIME_DATA_FLOW_DIAGRAM.md`
  - `docs/architecture/K8_OBJECT_SCHEMA.md`
  - `docs/architecture/K8_FAILURE_INJECTION_PLAN.md`
  - `docs/project_control/K8_MINIMAL_IMPLEMENTATION_SEQUENCE.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K8.0.5 establishes an unavoidable non-speaking cognition runtime skeleton before K8.1 implementation.

Goal:

```text
Ensure every K8 runtime path passes through explicit cognition artifacts before provider generation.
```

Chinese:

```text
确保所有 K8 运行路径在 Provider 生成前，都必须经过显式认知 artifact。
```

K8.0.5 does not implement understanding accuracy. It prevents architecture bypass.

## 3. Runtime Contract

Required API shape:

```python
CognitionPipeline.run(
    user_message,
    conversation_history,
    continuity_state,
    current_context,
)
```

Required stage order:

```text
ConversationUnderstanding
        ↓
ResponseIntention
        ↓
ContextRequirement / ContextArbitration
        ↓
ExpressionBoundary
        ↓
Provider-facing Cognition Envelope
```

Each stage must produce a serializable artifact.

Required stage metadata:

```json
{
  "stage": "conversation_understanding",
  "artifact_id": "...",
  "generates_response": false,
  "confidence_required": true,
  "boundary_pass": true
}
```

## 4. Acceptance Targets

- [ ] K8.0.5-A1: Defines CognitionPipeline runtime skeleton.
- [ ] K8.0.5-A2: Pipeline enforces stage order: Understanding → Intention → Context → Expression Boundary.
- [ ] K8.0.5-A3: Each stage produces a serializable artifact.
- [ ] K8.0.5-A4: No stage produces final Julia response text.
- [ ] K8.0.5-A5: Provider-facing request cannot be built unless all required artifacts exist.
- [ ] K8.0.5-A6: Pipeline rejects bypass path that sends Continuity State directly to Provider.
- [ ] K8.0.5-A7: Pipeline rejects single-LLM JSON blob pretending to satisfy all cognition stages without separate artifacts.
- [ ] K8.0.5-A8: Failure injection harness can run against skeleton before full K8.1 implementation.
- [ ] K8.0.5-A9: Pipeline records Cognitive Causality Trace.
- [ ] K8.0.5-A10: Pipeline does not mutate Identity, Relationship, Memory, Experience, Re-entry, or Event artifacts.

## 5. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_5_pipeline_skeleton.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_5_stage_artifacts.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_5_bypass_rejection.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_5_failure_injection_bootstrap.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core/conversation_cognition tests/conversation_cognition`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record deviation and use repo-local Python command.

## 6. Deliverables

- `docs/project_control/PHASE_CONTRACT_K8_0_5_COGNITION_RUNTIME_SKELETON.md`
  - This contract.
- `tmp/phase_contract_K8_0_5_COGNITION_RUNTIME_SKELETON.json`
  - Machine-readable contract.
- `docs/architecture/COGNITION_RUNTIME_SKELETON_CONTRACT_v1.md`
  - Runtime skeleton architecture.
- `julia_core/conversation_cognition/pipeline.py`
  - CognitionPipeline skeleton.
- `julia_core/conversation_cognition/artifact.py`
  - Stage artifact metadata.
- `julia_core/conversation_cognition/envelope.py`
  - Provider-facing Cognition Envelope.
- `tests/conversation_cognition/test_k8_0_5_pipeline_skeleton.py`
  - Pipeline order tests.
- `tests/conversation_cognition/test_k8_0_5_stage_artifacts.py`
  - Artifact tests.
- `tests/conversation_cognition/test_k8_0_5_bypass_rejection.py`
  - Bypass rejection tests.
- `tests/conversation_cognition/test_k8_0_5_failure_injection_bootstrap.py`
  - Failure injection bootstrap tests.

## 7. Bypass Prohibitions

K8.0.5 must reject:

```text
Continuity State → Provider
```

and:

```text
LLM(prompt with everything) → one JSON object → treated as K8 pipeline
```

Reason:

```text
This creates architecture illusion: interfaces exist, but cognition stages do not.
```

## 8. Cognitive Causality Trace

Required shape:

```json
{
  "cognitive_causality_trace": {
    "understanding_artifact": "id",
    "intention_artifact": "id",
    "context_requirement_artifact": "id",
    "expression_boundary_artifact": "id",
    "provider_envelope": "id",
    "bypass_detected": false,
    "core_generated_final_text": false
  }
}
```

## 9. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| K8 becomes single prompt JSON generator | P0 | High | One LLM call creates all stage outputs | Runtime owner | separate artifact enforcement |
| Continuity directly reaches Provider | P0 | High | Provider receives raw state | Runtime owner | bypass rejection |
| Skeleton starts generating text | P0 | Medium | Stage artifact contains reply | Runtime owner | no-response tests |
| Failure injection delayed until after implementation | P1 | Medium | Tests only success cases | QA owner | FI bootstrap gate |

## 10. Non-Goals

K8.0.5 does not:

- Implement accurate semantic understanding.
- Generate final responses.
- Implement provider language generation.
- Add memory.
- Mutate continuity artifacts.
- Prove natural conversation.

## 11. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| Skeleton before K8.1 vs direct K8.1 implementation | User latest directive | Direct implementation | Prevents collapsing stages into prompt/JSON architecture illusion |
| Explicit artifacts vs single LLM output | User latest directive | monolithic cognition prompt | Stage artifacts are required for attribution and governance |
| Expected guardrail file exists vs missing | Local filesystem check | Skill default assumption | `docs/project_control/EXECUTION_GUARDRAILS.md` is absent |

## 12. Status Sync / Accounting Baseline

- Doing → test-evidence → In review/done → milestone progress.
- P0/P1 status must include test evidence files in current diff.
- Phase-end accounting must use milestone-wide pull and local phase filtering.

## 13. Contract Self-check

- Phase identity complete: yes.
- Acceptance targets binary: yes.
- Commands copyable: yes.
- Deliverables mapped to paths: yes.
- Risk / rollback / non-goals complete: yes.
- `.md + .json` outputs required: yes.
- Conflict resolution included: yes.
- Guardrail referenced and missing state recorded: yes.
- No implementation code written by this contract: yes.

## 17. Additional Freeze — K8-001 Cognition Bypass Detection

K8.0.5 must include a hidden architecture guard test before K8.1 implementation.

### K8-001 Cognition Bypass Detection

Purpose:

```text
Prevent future runtime paths from sending Continuity State directly to Provider.
```

Forbidden path:

```text
Continuity State
  ↓
Provider
```

Expected result:

```json
{
  "case_id": "K8-001",
  "bypass_detected": true,
  "status": "FAIL_AS_EXPECTED",
  "reason": "Architecture violation: cognition stages were skipped"
}
```

This test is a skeleton-level gate. It must fail any implementation that produces a provider request without all prior cognition artifacts.

## 18. Cognitive Causality Trace Requirement

K8.0.5 must record a causality trace showing that provider-facing generation is caused by cognition artifacts, not by keyword or template routing.

Required fields:

```json
{
  "cognitive_causality_trace": {
    "meaning_source": "ConversationUnderstanding",
    "intention_source": "ResponseIntention",
    "context_source": "ContextRequirement / ContextArbitration",
    "expression_source": "ExpressionBoundary",
    "rule_dependency_detected": false,
    "template_dependency_detected": false
  }
}
```

This trace supports the K8.5 CCI metric.


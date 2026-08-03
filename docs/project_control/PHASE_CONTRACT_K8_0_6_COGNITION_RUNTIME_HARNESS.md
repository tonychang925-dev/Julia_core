# Phase Execution Contract — K8.0.6 Cognition Runtime Harness

## 1. Phase Identity

- Phase Name: K8.0.6 — Cognition Runtime Harness
- Phase Code: K8.0.6
- Parent Milestone: M10 — Julia Cognitive Behavior Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: build cognition observation harness before K8.1 implementation
  - `docs/project_control/PHASE_CONTRACT_K8_0_5_COGNITION_RUNTIME_SKELETON.md`
  - `docs/project_control/PHASE_CONTRACT_K8_1_CONVERSATION_UNDERSTANDING.md`
  - `docs/project_control/PHASE_CONTRACT_K8_1_5_CONTEXTUAL_MEANING_VALIDATION.md`
  - `docs/architecture/JULIA_COGNITIVE_ARCHITECTURE_v1_0.md`
  - `docs/architecture/K8_RUNTIME_DATA_FLOW_DIAGRAM.md`
  - `docs/architecture/K8_OBJECT_SCHEMA.md`
  - `docs/architecture/K8_FAILURE_INJECTION_PLAN.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K8.0.6 establishes a cognition observation harness before implementing K8.1 response-facing runtime.

Objective:

```text
For each Tony message, produce an inspectable Cognition Trace without generating a Julia response.
```

Chinese:

```text
先验证 Julia 是否真的在理解，而不是先让 Julia 回答。
```

K8.0.6 is not a provider integration phase.

## 3. Acceptance Targets

- [ ] A1. Defines `CognitionRuntimeHarness.run(...)` API.
- [ ] A2. Harness accepts user message, conversation history, continuity state, and current context.
- [ ] A3. Harness returns a cognition trace only; it never returns final Julia text.
- [ ] A4. Trace includes understanding, contextual meaning validation, context needs, suppressed context, and null intention placeholder.
- [ ] A5. Harness can run K8 failure injections before full K8.1 implementation.
- [ ] A6. Harness rejects Provider calls and provider-facing prompt construction.
- [ ] A7. Harness verifies stage artifacts are present and ordered.
- [ ] A8. Harness supports ambiguity-first outputs.
- [ ] A9. Harness records selected and suppressed context candidates.
- [ ] A10. Harness produces machine-readable reports under `artifacts/benchmark/`.

## 4. Required Commands

Implementation-phase required commands:

```bash
.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_6_runtime_harness.py -q
.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_6_no_provider_generation.py -q
.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_6_failure_injection_harness.py -q
.venv/bin/python -m unittest tests/conversation_cognition/test_k8_0_6_cognition_trace_shape.py -q
.venv/bin/python -m compileall -q julia_core/conversation_cognition tests/conversation_cognition
```

## 5. Deliverables

- `docs/architecture/COGNITION_RUNTIME_HARNESS_CONTRACT_v1.md`
- `julia_core/conversation_cognition/harness.py`
- `julia_core/conversation_cognition/trace.py`
- `julia_core/conversation_cognition/failure_injection.py`
- `tests/conversation_cognition/test_k8_0_6_runtime_harness.py`
- `tests/conversation_cognition/test_k8_0_6_no_provider_generation.py`
- `tests/conversation_cognition/test_k8_0_6_failure_injection_harness.py`
- `tests/conversation_cognition/test_k8_0_6_cognition_trace_shape.py`
- `artifacts/benchmark/k8_0_6_cognition_runtime_harness_report_v1.json`

## 6. Runtime API Contract

Required API:

```python
CognitionRuntimeHarness.run(
    user_message,
    conversation_history,
    continuity_state,
    current_context,
)
```

Required output shape:

```json
{
  "cognition_trace": {
    "input": {
      "user_message": "Julia，你还记得我们为什么开始这个项目吗？"
    },
    "understanding": {
      "literal": "asking about project origin",
      "meaning_candidates": [
        {
          "meaning": "Tony wants historical continuity",
          "confidence": 0.75
        },
        {
          "meaning": "Tony wants project summary",
          "confidence": 0.20
        }
      ],
      "state": "UNDERSTOOD"
    },
    "meaning_validation": {
      "requires_context": ["experience", "project_history"],
      "avoid_context": ["relationship_archive"],
      "missing_information": []
    },
    "intention": null,
    "provider_request": null,
    "final_response": null
  }
}
```

## 7. Harness Boundary

Forbidden:

```text
Harness → Provider
Harness → final Julia response
Harness → prompt generation
Harness → memory mutation
Harness → identity / relationship / experience mutation
```

Allowed:

```text
Harness → cognition trace
Harness → failure attribution labels
Harness → benchmark report
```

## 8. Required Early Failure Injections

K8.0.6 must run failure injections before K8.1 full implementation.

### FI-001 Understanding Collapse

Input:

```text
她又回来了。
```

Failure:

```text
Confidently route to Julia return / relationship return.
```

Expected:

```json
{
  "state": "AMBIGUOUS",
  "need_clarification": true
}
```

### FI-002 Keyword Rule

Input:

```text
你喜欢 Tony 吗？
```

Failure:

```text
relationship=true → relationship archive response path
```

Expected:

```text
multiple possible meanings with uncertainty
```

### FI-003 Context Overread

Input:

```text
今天创业板怎么样？
```

Failure:

```text
loads Julia identity, Tony relationship, soul-proof history
```

Expected:

```text
market / stock analysis context; suppress identity and relationship archive
```

## 9. Implementation Route Freeze

K8 implementation order is adjusted to:

```text
K8.0.6 Cognition Runtime Harness
        ↓
K8.1.0 Understanding Object Model
        ↓
K8.1.1 Meaning Candidate Engine
        ↓
K8.1.5 Meaning Validation Runtime
        ↓
K8.1 Gate Tests
        ↓
K8.2 Intention Planning
        ↓
K8.3 Context Arbitration Runtime
        ↓
K8.4 Expression Boundary Runtime
        ↓
K8.5 Natural Conversation E2E
```

K8.1 must not connect directly to Provider.

## 10. Metrics

### Harness Observability Score — HOS

```text
HOS =
Trace Completeness
+ Stage Order Visibility
+ Failure Injection Coverage
+ Provider Isolation
- Opaque LLM Blob Dependency
```

### Cognition Preflight Safety — CPS

```text
CPS =
Ambiguity Preservation
+ Context Suppression Visibility
+ No Final Text
+ No Provider Request
- Premature Answer Generation
```

## 11. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| Harness becomes hidden responder | High | Medium | Trace includes final text | Runtime owner | no final response gate |
| Provider introduced too early | High | Medium | Provider prompt exists before K8.2/K8.3 | Runtime owner | no provider request gate |
| Failure injection delayed | High | High | K8.1 implementation begins before FI tests | QA owner | K8.0.6 early FI command gate |
| Trace incomplete | Medium | Medium | Missing suppressed context / ambiguity | QA owner | trace shape test |

## 12. Rollback Plan

- Code rollback: revert `julia_core/conversation_cognition/harness.py`, `trace.py`, and `failure_injection.py`.
- Data rollback: remove `artifacts/benchmark/k8_0_6_cognition_runtime_harness_report_v1.json`.
- Sync rollback: keep K8.0.6 as contract-only if runtime fails no-provider or no-final-text gates.
- Trigger: any harness path that generates final Julia response or Provider request.

## 13. Non-Goals

K8.0.6 does not:

- Implement final K8.1 understanding accuracy.
- Generate Julia response.
- Connect to Provider.
- Implement K8.2 Response Intention.
- Implement K8.3 Context Arbitration Runtime.
- Prove Natural Conversation E2E.

## 14. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| Implement K8.1 directly vs build runtime harness first | User latest directive | Direct K8.1 implementation | Need observation before response generation |
| Provider integration vs trace-only harness | User latest directive | Provider-first route | Avoid LLM answering during understanding tests |
| Expected guardrail file exists vs missing | Local filesystem check | Skill default assumption | `docs/project_control/EXECUTION_GUARDRAILS.md` is absent |

## 15. Contract Self-check

- Phase identity complete: yes.
- Acceptance targets binary: yes.
- Commands copyable: yes.
- Deliverables mapped to paths: yes.
- Risk / rollback / non-goals complete: yes.
- `.md + .json` outputs required: yes.
- Conflict resolution included: yes.
- Guardrail referenced and missing state recorded: yes.
- No implementation code written by this contract: yes.

# Phase Contract — E2.0.1 Core Consumption Review

Status: COMPLETE
Phase Name: Julia AI Assistant Core Consumption Integrity Review v1.0
Phase Code: E2.0.1
Decision: APPROVED TO PROCEED WITH GAPS
Implementation Status: COMPLETE
Architecture Finding: Core architecture is valid. Application migration is incomplete.
Parent Milestone: Phase E2 — Julia AI Assistant Real Runtime Continuity Validation
Risk Level: P0
Generated At: 2026-08-02
Source Documents:
- `docs/project_control/PHASE_CONTRACT_E2.0_JULIA_AI_ASSISTANT_CONTINUITY_INTEGRATION.md`
- `docs/verification/JULIA_CORE_CONTINUITY_ARCHITECTURE_PROOF_v1.md`
- `docs/architecture/RUNTIME_CONTINUITY_INTEGRATION_DESIGN.md`
- `docs/adrs/ADR-014-runtime-continuity-boundary.md`

## 1. Objective

Review Julia AI Assistant architecture for compatibility with Julia Core Continuity Architecture before implementation.

E2.0.1 does not add features. It checks whether the application will consume Core Runtime, Persona, Memory Governance, Context Reconstruction, Alignment, Provider, and Trace correctly instead of reimplementing or bypassing them.

## 2. Acceptance Targets

- [ ] Julia AI Assistant Runtime entrypoint is identified.
- [ ] `server.py` / HTTP adapter responsibilities are reviewed and kept thin.
- [ ] Persona loading path is reviewed for prompt dependency risk.
- [ ] Memory startup/system-prompt path is reviewed for prompt dependency risk.
- [ ] Memory role transition is documented: Memory content → MemoryRef → Continuity Governance → Context Reconstruction.
- [ ] Trace-first integration requirement is documented.
- [ ] Prompt/session restoration fallback is explicitly forbidden.
- [ ] Provider migration risk is documented and assigned to E2.4.

## 3. Review Questions

### 3.1 Persona Consumption

Wrong pattern:

```text
Julia AI Assistant → giant persona prompt
```

Correct pattern:

```text
Julia AI Assistant → Julia Core Persona Engine → Persona Artifact
```

### 3.2 Memory Consumption

Wrong pattern:

```text
startup_memory.py / memory files → system prompt
```

Correct pattern:

```text
Memory Candidate → MemoryRef → Continuity Governance → Context Reconstruction
```

### 3.3 Server Boundary

Final target:

```text
server.py → HTTP Adapter → Julia Runtime
```

`server.py` must not own:

- Memory logic
- Persona logic
- Alignment logic
- Provider logic
- Continuity policy

### 3.4 Trace-first Validation

E2 validation requires ExecutionTrace evidence for each response path:

```json
{
  "runtime": "PASS",
  "session": "PASS",
  "continuity": "PASS",
  "persona": "PASS",
  "memory": "PASS",
  "context": "PASS",
  "alignment": "PASS",
  "provider": "PASS"
}
```

## 4. Required Commands

Documentation existence check:

```bash
cd julia_core && test -f docs/project_control/PHASE_CONTRACT_E2.0.1_CORE_CONSUMPTION_REVIEW.md
```

E1 proof regression baseline:

```bash
cd julia_core && python3 -m unittest tests.test_full_continuity_recovery tests.test_context_continuity_adapter tests.test_memory_governance_adapter tests.test_recovery_trigger_simulation tests.test_continuity_trace_integration tests.test_runtime_continuity_hook
```

## 5. Deliverables

| Deliverable | Path |
|---|---|
| Core Consumption Review contract | `docs/project_control/PHASE_CONTRACT_E2.0.1_CORE_CONSUMPTION_REVIEW.md` |
| Structured contract copy | `tmp/phase_contract_E2.0.1_CORE_CONSUMPTION_REVIEW.json` |

## 6. Updated E2 Route

| Phase | Goal |
|---|---|
| E2.0 | Integration Contract |
| E2.0.1 | Core Consumption Review |
| E2.1 | Runtime Continuity Integration |
| E2.2 | Identity Memory Validation |
| E2.3 | Compact Survival Real Test |
| E2.4 | Provider Migration Test |

## 7. Non-Goals

- No implementation code change.
- No live provider call.
- No new Core module.
- No prompt engineering workaround.
- No Julia AI Assistant behavior evaluation yet.

## 8. Risk Matrix

| Risk | Impact | Likelihood | Mitigation |
|---|---|---:|---|
| Julia AI Assistant duplicates Core Persona logic | P0 | Medium | Review persona path before E2.1 implementation |
| Julia AI Assistant restores from system prompt memory | P0 | Medium | Forbid memory → prompt continuity fallback |
| `server.py` becomes hidden Runtime | P0 | Medium | Keep HTTP adapter thin and route to Julia Runtime |
| Trace is omitted from real app | P1 | Medium | Trace-first requirement blocks E2.1 completion |
| Provider migration is deferred indefinitely | P1 | Medium | Add E2.4 Provider Migration Test |


## 9. Review Artifact Requirement

E2.0.1 must produce the application-level review artifact:

```text
julia_ai_assistant/docs/verification/JULIA_AI_ASSISTANT_CORE_CONSUMPTION_REVIEW_v1.md
```

The review is not a feature checklist. It is an integrity review proving Julia AI Assistant consumes Julia Core rather than reimplementing Core authorities.

Required sections:

1. Dependency Graph
2. Core Ownership Table
3. Authority Ownership Matrix
4. Forbidden Dependency Scan
5. Runtime Entry Review
6. Persona Consumption Review
7. Memory Consumption Review
8. Continuity Consumption Review
9. Alignment Consumption Review
10. Provider Consumption Review
11. Trace-first Verification Gate
12. Gap List

Core invariant:

```text
E1 proved Core can save Julia.
E2.0.1 must prove the application will not recreate Julia outside Core.
```


## 10. Review Results

Generated artifact:

```text
/Users/admin/julia_ai_assistant/docs/verification/JULIA_AI_ASSISTANT_CORE_CONSUMPTION_REVIEW_v1.md
```

Structured result:

```text
/Users/admin/julia_ai_assistant/tmp/core_consumption_review_v1.json
```

Summary:

| Area | Result |
|---|---|
| Runtime Consumption | PASS WITH WARNINGS |
| Persona Consumption | FAIL |
| Memory Consumption | FAIL |
| Continuity Consumption | GAP / NOT INTEGRATED |
| Alignment Consumption | PASS |
| Provider Consumption | PARTIAL |
| Trace-first Gate | FAIL FOR E2 TARGET |

Decision:

```text
APPROVED TO PROCEED WITH GAPS RECORDED
```

Next:

```text
E2.1 — Runtime Continuity Integration
```


## 11. No Legacy Authority Rule

During E2, any legacy Julia AI Assistant module that owns one of the following authorities must be deleted, moved into Julia Core, or downgraded to an adapter:

- Persona decision
- Memory ranking/governance
- Identity judgment
- Continuity decision
- Context reconstruction
- Alignment policy
- Provider identity shaping

Allowed application ownership:

- HTTP API
- UI/UX
- product workflow
- deployment/runtime adapter glue

Forbidden pattern:

```text
Core OS + old chatbot authority code
```

Target pattern:

```text
Julia AI Assistant Adapter → Julia Core Runtime → Core authorities → Response + Trace
```

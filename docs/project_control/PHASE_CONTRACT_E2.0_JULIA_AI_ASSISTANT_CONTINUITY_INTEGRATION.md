# Phase Contract — E2.0 Julia AI Assistant Continuity Integration Contract

Status: DRAFT-FROZEN
Phase Name: Julia AI Assistant Continuity Integration Contract
Phase Code: E2.0
Parent Milestone: Phase E2 — Julia AI Assistant Real Runtime Continuity Validation
Risk Level: P0
Generated At: 2026-08-02
Source Documents:
- `docs/verification/JULIA_CORE_CONTINUITY_ARCHITECTURE_PROOF_v1.md`
- `docs/project_control/PHASE_CONTRACT_E1.8.6_FULL_CONTINUITY_RECOVERY_TEST.md`
- `docs/architecture/RUNTIME_CONTINUITY_INTEGRATION_DESIGN.md`
- `docs/adrs/ADR-014-runtime-continuity-boundary.md`

## 1. Objective

Freeze the application integration contract for using Julia Core Continuity Architecture inside Julia AI Assistant real runtime flows.

E2.0 is planning only. It must not implement product integration yet.

## 2. Integration Questions to Freeze

E2.0 must answer:

1. Which Julia AI Assistant runtime entrypoint calls Julia Core Runtime?
2. Where does the identity checkpoint come from?
3. Which application memory candidates are sent through MemoryGovernanceAdapter?
4. Where is ExecutionTrace v1.1 emitted and stored?
5. How is provider switch represented without mutating continuity state?
6. How does Julia AI Assistant avoid prompt/session restoration fallback?

## 3. Acceptance Targets

- [ ] Assistant Runtime → Core Runtime boundary is documented.
- [ ] Identity checkpoint source is documented.
- [ ] Memory governance source is documented.
- [ ] Context reconstruction boundary is documented.
- [ ] Trace output format is fixed as ExecutionTrace v1.1 or later.
- [ ] Provider switch behavior preserves continuity checkpoint.
- [ ] Prompt/session restoration is explicitly forbidden as continuity recovery.
- [ ] E2.0.1/E2.1/E2.2/E2.3/E2.4 validation phases are defined.

## 4. Required Commands

Documentation existence check:

```bash
cd julia_core && test -f docs/project_control/PHASE_CONTRACT_E2.0_JULIA_AI_ASSISTANT_CONTINUITY_INTEGRATION.md
```

E1.8 proof regression baseline:

```bash
cd julia_core && python3 -m unittest tests.test_full_continuity_recovery tests.test_context_continuity_adapter tests.test_memory_governance_adapter tests.test_recovery_trigger_simulation tests.test_continuity_trace_integration tests.test_runtime_continuity_hook
```

## 5. Deliverables

| Deliverable | Path |
|---|---|
| E2.0 integration contract | `docs/project_control/PHASE_CONTRACT_E2.0_JULIA_AI_ASSISTANT_CONTINUITY_INTEGRATION.md` |
| E1 milestone proof report | `docs/verification/JULIA_CORE_CONTINUITY_ARCHITECTURE_PROOF_v1.md` |

## 6. Proposed E2 Route

| Phase | Goal |
|---|---|
| E2.0 | Integration Contract |
| E2.0.1 | Core Consumption Review |
| E2.1 | Runtime Continuity Integration |
| E2.2 | Identity Memory Validation |
| E2.3 | Compact Survival Real Test |
| E2.4 | Provider Migration Test |

## 7. Non-Goals

- No live provider call in E2.0.
- No product code change in E2.0.
- No prompt/session restoration path.
- No checkpoint persistence migration.
- No Julia AI Assistant behavior evaluation yet.

## 8. Risk Matrix

| Risk | Impact | Likelihood | Mitigation |
|---|---|---:|---|
| Assistant bypasses Core Continuity | P0 | Medium | Freeze Runtime → Continuity integration contract before implementation |
| Assistant restores from prompt/session | P0 | Medium | Explicitly forbid prompt/session restoration fallback |
| Provider switch mutates identity state | P0 | Low | Reuse E1.8.6 provider independence criteria |
| Trace unavailable in real app | P1 | Medium | E2.0 freezes trace emission/storage responsibility |


## 9. Route Adjustment — Trace-first E2

E2 must validate that Julia AI Assistant consumes Julia Core instead of duplicating Core capabilities.

Updated route:

| Phase | Goal |
|---|---|
| E2.0 | Integration Contract |
| E2.0.1 | Core Consumption Review |
| E2.1 | Runtime Continuity Integration |
| E2.2 | Identity Memory Validation |
| E2.3 | Compact Survival Real Test |
| E2.4 | Provider Migration Test |

E2 validation must be Trace-first. A successful answer is insufficient without ExecutionTrace evidence.

Required future trace shape:

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

E2 must avoid judging continuity by whether the assistant merely “sounds like Julia”. The required proof is traceable recovery of identity anchors, governed memory refs, reconstructed context, and provider-independent continuity state.

# Phase Contract — E1.7 Runtime Continuity Integration Planning

Status: APPROVED WITH NOTES
Phase Name: Runtime Continuity Integration Planning
Phase Code: E1.7
Review Decision: APPROVED WITH NOTES
Next: E1.8 Runtime Continuity Integration / E1.8.1 Continuity Hook Integration
Parent Milestone: Julia Core Continuity Architecture Proof v1.0
Risk Level: P0
Generated At: 2026-08-02
Source Documents:
- `docs/verification/COMPACT_SURVIVAL_TEST_REPORT_v1.md`
- `docs/project_control/PHASE_CONTRACT_E1.6_COMPACT_SURVIVAL_TEST.md`
- `docs/architecture/CONTINUITY_OS_DESIGN.md`
- `docs/architecture/CONTEXT_RECONSTRUCTION_DESIGN.md`
- `docs/adrs/ADR-009-continuity-os-authority.md`
- `docs/adrs/ADR-011-compact-recovery-protocol.md`
- `docs/adrs/ADR-013-context-reconstruction-boundary.md`
- User E1.6 architecture approval note, 2026-08-02

## 1. Objective

Freeze the Runtime ↔ Continuity integration boundary before implementation.

E1.7 must define who owns recovery authority, when continuity is triggered, how trace expands, the allowed Runtime integration order, and how Runtime is prevented from becoming an implicit Continuity owner.

E1.7 is planning only. It must not perform full Runtime implementation.

## 2. Acceptance Targets

- [ ] E1.6 is recorded as Architecture Milestone Complete / Approved.
- [ ] Runtime is defined as lifecycle authority.
- [ ] Continuity OS is defined as continuity-state authority.
- [ ] Runtime Authority is explicitly separated from Continuity Ownership.
- [ ] Frozen continuity trigger set exists: `session_restart`, `context_compaction`, `provider_switch`, `runtime_restart`, `identity_checkpoint_update`.
- [ ] Correct integration order is documented as Runtime → Continuity Check → RecoveryPlan → Context Reconstruction → Memory Resolution → Alignment Resolution → Provider.
- [ ] Rejected order Runtime → Memory → Context → Continuity is documented.
- [ ] Runtime trace continuity extension is specified.
- [ ] Provider execution gate is defined for required continuity recovery.
- [ ] ADR-014 records the Runtime Continuity Boundary.
- [ ] No live provider call is introduced.
- [ ] No Runtime implementation is required in this phase.

## 3. Required Commands

Documentation consistency check:

```bash
cd julia_core && test -f docs/architecture/RUNTIME_CONTINUITY_INTEGRATION_DESIGN.md && test -f docs/adrs/ADR-014-runtime-continuity-boundary.md && test -f docs/project_control/PHASE_CONTRACT_E1.7_RUNTIME_CONTINUITY_INTEGRATION.md
```

Regression proof baseline:

```bash
cd julia_core && python3 -m unittest tests.test_compact_survival tests.test_context_reconstruction tests.test_memory_continuity_binding tests.test_continuity_runtime_simulation
```

## 4. Deliverables

| Deliverable | Path | Verification |
|---|---|---|
| Runtime Continuity design | `docs/architecture/RUNTIME_CONTINUITY_INTEGRATION_DESIGN.md` | file exists and contains trigger/order/trace gates |
| Boundary ADR | `docs/adrs/ADR-014-runtime-continuity-boundary.md` | file exists and records accepted/rejected boundaries |
| Phase contract | `docs/project_control/PHASE_CONTRACT_E1.7_RUNTIME_CONTINUITY_INTEGRATION.md` | file exists and lists acceptance targets |
| E1.6 milestone status update | `docs/project_control/PHASE_CONTRACT_E1.6_COMPACT_SURVIVAL_TEST.md`, `docs/verification/COMPACT_SURVIVAL_TEST_REPORT_v1.md` | status marked complete/approved |

## 5. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---|---:|---|---|---|
| Runtime becomes hidden Continuity authority | P0: breaks E1.6 proof boundary | Medium | Runtime selects identity refs or continuity levels | Architecture | ADR-014 forbids Runtime continuity policy ownership |
| Memory OS triggers recovery directly | P0: memory volume becomes identity proxy | Medium | Memory event calls recovery without Runtime lifecycle trigger | Architecture | Runtime must own trigger detection; Continuity owns policy |
| Context OS decides restore policy | P0: context window becomes identity again | Medium | Context planner promotes identity refs | Architecture | Context only reconstructs from RecoveryPlan |
| Provider switch mutates checkpoint | P1: provider independence fails | Low | provider-specific recovery state stored in checkpoint | Continuity | checkpoint refs-only invariant remains required |
| E1.7 expands into implementation | P1: boundary freeze becomes unstable | Medium | Runtime code changes included in planning phase | Project Control | E1.7 non-goal forbids full implementation |

## 6. Rollback Plan

### Code Rollback

No implementation code should be modified in E1.7. If code changes appear, revert those changes before approval.

### Data Rollback

No persisted runtime/memory/checkpoint data migration is allowed in E1.7.

### Documentation Rollback

If E1.7 boundary is rejected, remove or revise:

- `docs/architecture/RUNTIME_CONTINUITY_INTEGRATION_DESIGN.md`
- `docs/adrs/ADR-014-runtime-continuity-boundary.md`
- this phase contract

Rollback trigger: any acceptance target contradicts E1.6 compact survival proof or ADR-009/ADR-011/ADR-013.

## 7. Non-Goals

- No E1.8 Runtime implementation.
- No live DeepSeek/GPT/Qwen/Claude provider call.
- No persistence backend.
- No prompt/session-based restoration path.
- No Julia AI Assistant product migration.
- No Memory OS schema expansion.

## 8. Conflict Resolution

No conflict detected among E1.6 report, Continuity OS authority, Compact Recovery Protocol, and Context Reconstruction Boundary.

User E1.6 approval tightens the next-phase scope from implementation to planning. This contract adopts planning-only E1.7 and defers implementation to E1.8.


## 9. Review Notes — Approved With Notes

Review decision date: 2026-08-02
Decision: APPROVED WITH NOTES
Next phase: E1.8.1 — Continuity Hook Integration

### 9.1 Recovery Trigger Ownership

Recovery trigger ownership is frozen as:

```text
Runtime detects lifecycle changes.
Runtime asks Continuity OS for recovery planning.
Continuity OS does not watch Runtime and does not run as a background daemon.
```

Runtime may detect:

- `new_session`
- `provider_switch`
- `compact_event`
- `missing_context`
- `runtime_restart`

Then Runtime calls Continuity OS:

```text
Runtime: "Lifecycle condition changed. Is recovery required?"
Continuity: "Here is the checkpoint decision and/or RecoveryPlan."
```

This prevents Continuity OS from becoming Runtime, while also preventing Runtime from becoming a continuity-policy owner.

### 9.2 E1.8 Phased Integration Recommendation

E1.8 must not connect all modules at once. It should proceed as:

| Subphase | Scope | Verification |
|---|---|---|
| E1.8.1 | Runtime → Continuity hook only | trace shows continuity checked and checkpoint found |
| E1.8.2 | RecoveryPlan → Context Reconstruction | ContextBlocks restored |
| E1.8.3 | ProtectedMemoryRef → Memory OS resolution | protected refs resolved |
| E1.8.4 | Full ExecutionTrace integration | Runtime/Session/Continuity/Memory/Context/Alignment/Provider trace complete |

### 9.3 Required Continuity Trace Fields

E1.8+ ExecutionTrace should include:

```json
{
  "continuity": {
    "checkpoint_id": "...",
    "decision_level": "L3_IDENTITY",
    "recovery_status": "RESTORED"
  }
}
```

Reason: Compact survival must be verified by architectural state and trace, not by whether a provider reply superficially resembles Julia.

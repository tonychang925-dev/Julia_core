# Phase Contract — E1.6 Compact Survival Test

Status: DRAFT-FROZEN
Phase Name: Compact Survival Test
Phase Code: E1.6
Parent Milestone: Julia Core Continuity Architecture
Risk Level: P0
Generated At: 2026-08-01

## 1. Objective

Run the first architecture proof test showing Julia Core can survive a compact-like event without relying on old conversation context.

Proof chain:

```text
Memory ref
  ↓
MemoryContinuityBinder
  ↓
ContinuityDecision L3
  ↓
ContinuityCheckpoint
  ↓
COMPACT clears session/context
  ↓
RecoveryPlan
  ↓
ContextReconstructor
  ↓
ContinuityTrace RESTORED
```

## 2. Acceptance Targets

- [ ] Identity-forming memory ref is promoted to L3.
- [ ] Checkpoint is refs-only.
- [ ] Session state and temporary context are cleared during compact simulation.
- [ ] RecoveryPlan is generated from checkpoint.
- [ ] ContextReconstructor rebuilds ContextBlocks from refs.
- [ ] ContinuityTrace reports RESTORED.
- [ ] Provider switch does not alter continuity state.
- [ ] No real provider call is used.
- [ ] Compact survival report exists.

## 3. Required Commands

```bash
cd julia_core && python3 -m unittest tests.test_compact_survival
```

## 4. Deliverables

| Deliverable | Path |
|---|---|
| Compact Survival test | `tests/test_compact_survival.py` |
| Report | `docs/verification/COMPACT_SURVIVAL_TEST_REPORT_v1.md` |
| Contract | `docs/project_control/PHASE_CONTRACT_E1.6_COMPACT_SURVIVAL_TEST.md` |

## 5. Non-Goals

- No Claude API.
- No DeepSeek/GPT/Qwen live call.
- No real Runtime integration.
- No checkpoint persistence backend.
- No memory write.

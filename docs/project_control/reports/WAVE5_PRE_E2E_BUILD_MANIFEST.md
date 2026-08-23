# WAVE5 Pre-E2E Build Manifest

## 1. Manifest Status

- Manifest: Wave5 Pre-E2E Build Manifest
- Status: RECORDED ✅
- Date: 2026-08-23
- Owning repo: `/Users/admin/julia_core`
- Owning branch: `cm-r0-fix`
- Owning HEAD at manifest creation: `2933399`
- E2E readiness: NOT READY ⚠️
- E2E execution: HOLD ⚠️
- AT-17: HOLD ⚠️

This manifest pins the observed repository set for Pre-E2E lineage review. It is not an E2E run authorization.

## 2. Component Build Candidate

| Component | Local repo | Branch | HEAD | Workspace policy | Authority role |
| --- | --- | --- | --- | --- | --- |
| Core | `/Users/admin/julia_core` | `cm-r0-fix` | `2933399` | DIRTY — E2E requires clean tree or explicit dirty exception | canonical conversation / storage / diary / memory / Context OS authority |
| Assistant | `/Users/admin/julia_ai_assistant` | `phase5/rmd-3g-observability` | `47a3e4a` | DIRTY — E2E requires clean tree or explicit dirty exception | product runtime / provider-facing orchestration |
| Voice-S2S | `/Users/admin/Julia-Voice-S2S` | `phase5/rmd-3g-observability` | `e7db6af` | DIRTY — E2E requires clean tree or explicit dirty exception | realtime voice transport / live session state only |
| Electron | `/Users/admin/julia_electron_v2` | `codex/bugfix/at10-electron-cache-boundary` | `a25f0dc` | clean for targeted status | client/application projection |

Local mapping note:

```text
User label: Julia-ai-assistant
Observed repo: /Users/admin/julia_ai_assistant
```

No `/Users/admin/Julia-ai-assistant` git repository was observed during the audit.

## 3. Dirty Workspace Policy

E2E must not be interpreted as authoritative unless one of the following is true for every participating repo:

```text
Option A: workspace clean
Option B: dirty files explicitly listed and approved as part of the E2E candidate
```

Current dirty-state summary:

```text
julia_core: dirty / untracked historical files present
julia_ai_assistant: dirty / untracked runtime, memory, provider, experiment files present
Julia-Voice-S2S: dirty / deleted docs + untracked SOP present
julia_electron_v2: no targeted dirty output observed
```

Dirty files must not silently participate in E2E.

## 4. Frozen Artifact References

### Core AT-12 through AT-16

| AT | Status | Key artifact |
| --- | --- | --- |
| AT-12 Diary NO_ENTRY | FROZEN ✅ | `docs/project_control/reports/WAVE5_AT12_FINAL_FREEZE_RECORD.md` |
| AT-13 Diary Significant Event | FROZEN ✅ | `docs/project_control/reports/WAVE5_AT13_FINAL_FREEZE_RECORD.md` |
| AT-14 Diary Provenance | FROZEN ✅ | `docs/project_control/reports/WAVE5_AT14_FINAL_FREEZE_RECORD.md` |
| AT-15 Diary ≠ Memory | FROZEN ✅ | `docs/project_control/reports/WAVE5_AT15_FINAL_FREEZE_RECORD.md` |
| AT-16 Diary Context OS Retrieval | FROZEN ✅ | `docs/project_control/reports/WAVE5_AT16_FINAL_FREEZE_RECORD.md` |

AT-16 frozen lineage:

```text
d7c37a4 → 0cc6815 → 00b964e → b516d5e → 359568c → 287a62b
```

### Electron AT-10

| AT | Status | Repo | Key artifact |
| --- | --- | --- | --- |
| AT-10 Electron Cache Destruction | FROZEN ✅ | `/Users/admin/julia_electron_v2` | `docs/project_control/reports/WAVE5_AT10_FINAL_FREEZE_RECORD.md` |

Electron frozen lineage head:

```text
a25f0dc docs(wave5): freeze AT-10 electron cache boundary
```

### Voice-S2S AT-11

| AT | Status | Repo | Key artifact |
| --- | --- | --- | --- |
| AT-11 S2S State Destruction | DEFERRED ⏸️ | `/Users/admin/Julia-Voice-S2S` | `docs/project_control/reports/WAVE5_AT11_DEFER_DECISION.md` |

Frozen / parked semantic constraints preserved:

```text
S2S runtime state ≠ continuity authority
history seeding/replay ≠ canonical recovery
Core canonical state > S2S session/workspace/chat
```

### AT-01 through AT-09 lineage index

User checkpoints mark AT-01 through AT-09 as frozen / frozen-ready. The Pre-E2E audit did not locate a consolidated `WAVE5_AT01...AT09_FINAL_FREEZE_RECORD.md` artifact set under the current Core `docs/project_control/reports` naming pattern.

Manifest status for AT-01 through AT-09:

```text
AT-01..AT-09: checkpoint-confirmed; artifact index pending ⚠️
```

This does not reopen AT-01 through AT-09, but E2E readiness requires an index mapping each item to its artifact/commit evidence before final E2E freeze.

## 5. Dependency Relations

Required authority direction:

```text
Core canonical authority
  ↓
Assistant product runtime binding
  ↓
Electron / Voice runtime projection and transport
  ↓
Provider-visible model context
```

Forbidden dependency direction:

```text
Electron cache / Assistant local memory adapter / S2S chat buffer / runtime session state
  ↓
canonical conversation, Diary, Memory, Identity, or continuity authority
```

## 6. Product Path Evidence Required Before E2E

Before E2E execution, a trace must prove the actual product request uses the frozen path or explicitly declares it out of E2E scope:

```text
User request
  ↓
JuliaAssistantRuntime
  ↓
julia_core Runtime / Context OS
  ↓
AT-16 frozen Diary Context OS retrieval path when Diary retrieval is in scope
  ↓
provider-visible package trace
```

Current blocker:

```text
Assistant runtime trace still records ContextOS as missing / NOT_CALLED.
```

Therefore E2E remains HOLD.

## 7. E2E Candidate Decision

```text
Build Manifest: RECORDED ✅
Authority Propagation Contract: REQUIRED ✅
E2E readiness: NOT READY ⚠️
E2E execution: HOLD ⚠️
```

Next permitted work:

```text
Close Pre-E2E product lineage gaps / produce product trace proof
```

Still not started:

```text
E2E ❌
AT-17 ❌
Context OS ranking/search optimization ❌
MemoryExperience creation ❌
Diary UI redesign ❌
Claude diary migration ❌
```

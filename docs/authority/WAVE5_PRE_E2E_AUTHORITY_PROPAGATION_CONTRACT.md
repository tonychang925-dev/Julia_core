# WAVE5 Pre-E2E Authority Propagation Contract

## 1. Contract Status

- Contract: Wave5 Pre-E2E Authority Propagation Contract
- Status: READY FOR PRE-E2E ENFORCEMENT ✅
- Date: 2026-08-23
- Repo: `/Users/admin/julia_core`
- Branch: `cm-r0-fix`
- Base HEAD: `2933399`
- E2E readiness: NOT READY ⚠️
- E2E execution: HOLD ⚠️

This contract freezes how already-frozen authority boundaries must propagate across Core, Assistant, Electron, and Voice-S2S before E2E may be considered authoritative.

## 2. Core Rule

```text
Frozen component boundaries
  ≠
Integrated system proof
```

E2E may only start after the product lineage proves that the real runtime path uses the frozen authority chain or explicitly excludes the uncalled boundary from E2E scope.

## 3. Cross-Repo Authority Direction

Required direction:

```text
Core canonical state
  ↓
Core governed source assembly / Context OS
  ↓
Assistant product runtime
  ↓
Electron projection / Voice transport
  ↓
provider-visible context
```

Forbidden inversion:

```text
client cache
runtime local adapter
session summary
S2S chat buffer
projection ContextBlock
trace metadata
  ↓
canonical state / Memory / Diary / Identity / continuity authority
```

## 4. Propagation Invariants

### PE2E-I01 — Core remains canonical authority

```text
Core canonical conversation / storage / Diary / Memory state
  >
Assistant runtime state / Electron cache / S2S runtime state
```

No product layer may create, delete, hide, rewrite, fork, or re-author Core canonical reality.

### PE2E-I02 — Assistant runtime must not fork Core authority

Assistant may orchestrate product calls, but must not duplicate or replace frozen Core authority surfaces.

Required for E2E:

```text
Assistant trace includes frozen Core authority path
```

or:

```text
E2E scope explicitly excludes that authority boundary
```

Current known blocker:

```text
/Users/admin/julia_ai_assistant runtime trace marks ContextOS NOT_CALLED / missing.
```

### PE2E-I03 — AT-16 propagation rule

If E2E includes Diary retrieval, the only acceptable model-visible path is:

```text
AcceptedDiaryEntry
  ↓
Core provenance validation
  ↓
Core Context OS admission
  ↓
DiaryContextCandidate
  ↓
ContextBlock(domain="diary", authority="ContextOS")
  ↓
CognitiveContextPackage trace
  ↓
provider-visible context
```

Forbidden:

```text
Assistant local memory adapter / session summary / legacy diary text / density text
  ↓
provider-visible Diary context
```

### PE2E-I04 — Electron remains projection only

Electron must preserve AT-10:

```text
Core canonical conversation state
  >
Electron projection cache
```

E2E must not count Electron cache restoration, UI state, local transcript, optimistic id, or stale projection as conversation authority.

### PE2E-I05 — Voice-S2S remains live transport only

Because AT-11 is deferred:

```text
S2S runtime state
  ≠
completed continuity authority
```

E2E may use S2S only under this guard:

```text
S2S carries transport/session metadata;
completed continuity comes from Assistant/Core by canonical conversation_id.
```

Forbidden in E2E success criteria:

```text
S2S seedConversationHistory()
S2S chat buffer replay
S2S workspace state restore
  ↓
continuity success
```

### PE2E-I06 — ContextBlock is projection only

Across all repos:

```text
ContextBlock
  ≠
Diary authority
  ≠
Memory authority
  ≠
Identity authority
  ≠
Conversation authority
```

ContextBlock may be model-visible projection for a turn; it cannot mutate or become source truth.

### PE2E-I07 — Trace proves routing but is not source authority

```text
trace metadata
  ≠
source authority
```

A trace may prove that a route occurred. It cannot repair missing sources, validate provenance by itself, or promote projections into canonical state.

### PE2E-I08 — Dirty state must be governed

Any repo participating in E2E must satisfy:

```text
clean workspace
```

or:

```text
explicit dirty exception record included in the E2E manifest
```

Uncommitted files must not silently become part of authority evidence.

## 5. E2E Entry Preconditions

E2E remains blocked until all are true:

1. Build manifest pins repo path, branch, commit, dirty policy, and artifact references.
2. Assistant product runtime trace proves ContextOS / Core path usage or excludes that boundary from E2E scope.
3. Electron E2E candidate uses AT-10 frozen branch/commit or a merge containing it.
4. Voice-S2S E2E scope explicitly preserves AT-11 deferred constraints.
5. AT-01 through AT-09 evidence index is linked or documented as checkpoint lineage.
6. No product-layer projection is counted as canonical authority.

## 6. E2E Scope Guard

Allowed after prerequisites:

```text
product path verification
cross-repo request flow
authority trace validation
projection/cache non-authority validation
```

Still excluded:

```text
AT-17 Claude migration
Context OS ranking/search optimization
MemoryExperience creation
Diary UI redesign
S2S full restart recovery / AT-20 unless separately opened
large Memory OS redesign
```

## 7. Contract Decision

```text
Authority Propagation Contract: READY FOR PRE-E2E ENFORCEMENT ✅
E2E Readiness: NOT READY ⚠️
E2E Execution: HOLD ⚠️
```

Next allowed step:

```text
Produce product lineage proof / close Pre-E2E P0 gaps
```

# DIA-7 R1 — Core Continuity Projection Contract

## 0. Status

Phase: DIA-7 — Continuity State / Identity Projection  
Artifact: R1 Core implementation  
Implementation provenance: Codex A  
Branch: `codex/dia-7/continuity-projection-r0`  
Base: DIA-7 R0 Continuity Projection Contract `03b6bc4`

Frozen upstream inputs remain immutable:

- DIA-3 Reflection Trigger Contract
- DIA-4 Reflection Context Contract
- DIA-5 Reflection Context Handoff Contract
- DIA-6 Context Evolution / Lineage Contract
- DIA-7 R0 Projection ≠ New History boundary

DIA-7 R1 does not modify DIA-3 trigger identity, DIA-4 context identity, DIA-5 handoff identity, DIA-6 lineage identity, transport state, Diary, Memory, Context OS, Assistant behavior, or persistence.

## 1. Implemented module

```text
julia_core/continuity_projection/
  __init__.py
  models.py

tests/continuity_projection/test_dia7_core_contract.py
```

Public Core nouns:

- `ContinuityClaim`
- `ContinuityClaimKind`
- `ContinuityClaimStatus`
- `ContinuityConflictRule`
- `ContinuityEvidenceRef`
- `ContinuityAnchor`
- `ContinuityProjectionInput`
- `ContinuityProjectionPolicy`
- `ContinuityState`
- `ContinuityProjectionResult`
- `ContinuityProjectionAudit`
- `StrictContinuityProjector`

## 2. Core boundary

DIA-7 R1 freezes:

```text
Projection ≠ New History
```

Valid Core path:

```text
verified DIA-6 ContextLineageEdge artifacts
        ↓
ContinuityEvidenceRef
        ↓
ContinuityClaim candidate with lineage evidence
        ↓
ContinuityProjectionInput
        ↓
ContinuityProjectionPolicy
        ↓
StrictContinuityProjector
        ↓
ContinuityState
        ↓
continuity_state_digest
```

Invalid path:

```text
raw memory / model prose / manual state patch
        ↓
ContinuityState
```

## 3. Identity-domain separation

R1 keeps three digest domains distinct:

```text
DIA-4 context_digest
DIA-6 lineage_digest / source graph digest
DIA-7 continuity_state_digest
```

`ContinuityProjectionInput.source_graph_digest` is recomputed from canonical DIA-6 edge semantic bytes and must match the caller-supplied source graph digest. Substituting a lineage digest or context digest as graph / state identity fails closed.

## 4. Deterministic canonicalization

R1 requires canonical sorted order at the Core boundary:

- `lineage_edges` sorted by `lineage_digest`
- `candidate_claims` sorted by `claim_id`
- duplicate lineage edges rejected
- duplicate claim ids rejected
- every claim evidence ref must point to a lineage edge present in the projection input

Same canonical lineage plus same policy yields identical state bytes and digest. Audit metadata is excluded from state identity.

## 5. Evidence binding

`ContinuityEvidenceRef` is constructed only from exact DIA-6 `ContextLineageEdge` provenance:

```text
ContinuityEvidenceRef.from_lineage_edge(edge)
```

Each `ContinuityClaim` requires non-empty `supporting_evidence_refs`. Evidence refs are canonicalized and duplicate-free. Claims without lineage evidence are invalid before projection.

## 6. Conflict semantics

R1 supports a closed conflict vocabulary:

```text
APPEND
SUPERSEDE
CORRECT
DEPRECATE
UNRESOLVED
```

Implemented semantics:

- `APPEND`: candidate becomes active.
- `SUPERSEDE(A → B)`: B becomes active; A is removed from active / unresolved output.
- `CORRECT(A → B)`: B becomes active; A is removed from active / unresolved output.
- `DEPRECATE(A)`: A is removed from active / unresolved output.
- `UNRESOLVED(A, B)`: neither silently wins; both are emitted as conflicted unresolved claims.

Targeted conflict rules require `target_claim_id`. `APPEND` claims must not carry a target.

R1 intentionally does not implement default latest-timestamp-wins.

## 7. State shape

`ContinuityState` contains:

- `state_schema_version`
- `projection_policy_revision`
- `projection_policy_fingerprint`
- `source_graph_revision`
- `source_graph_digest`
- `active_claims[]`
- `unresolved_conflicts[]`
- `supporting_lineage_digests[]`
- `continuity_state_digest`

Only `ProjectedContinuityClaim` values with `ACTIVE` status enter `active_claims`. Only `ProjectedContinuityClaim` values with `CONFLICTED` status enter `unresolved_conflicts`.

## 8. Audit split

`ContinuityProjectionAudit` records execution diagnostics and timestamps, but these fields do not enter `ContinuityState.semantic_canonical_bytes(include_digest=False)` and do not affect `continuity_state_digest`.

## 9. Authority exclusions

The Core module has no authority over:

- Diary
- Memory
- Assistant runtime
- model generation
- filesystem persistence
- Context OS writes
- DIA-6 lineage mutation

Static boundary tests assert those imports / side effects are absent from `julia_core/continuity_projection`.

## 10. Golden vectors

Fixed DIA-7 R1 fixture vectors:

```text
projection_policy_fingerprint:
c6de6271984cb27d6e99e04a575527c070e5ab6563d47facebd5f6f24a95f23f

continuity_state_digest:
333f34fa51be0e0c095b024411193218c69e6c4990ef50de09f7b596a378423e
```

## 11. Owner validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_projection/test_dia7_core_contract.py -q
14 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/continuity_projection tests/continuity_projection/test_dia7_core_contract.py
PASS
```

## 12. Acceptance matrix

| Acceptance target | Status |
| --- | --- |
| Same lineage + same policy -> identical state digest | ✅ |
| Illegal lineage order rejected | ✅ |
| Unsupported claim without evidence rejected | ✅ |
| Evidence pointing to missing lineage rejected | ✅ |
| Deprecated claim not projected active | ✅ |
| Correction replaces old active claim | ✅ |
| Unresolved conflict not silently chosen | ✅ |
| Audit timestamp / diagnostics do not affect state digest | ✅ |
| Same policy revision with semantic drift fails closed | ✅ |
| Raw model output cannot constitute `ContinuityClaim` | ✅ |
| Context / lineage / state digest confusion rejected | ✅ |
| Anchor requires active identity-anchor claim | ✅ |
| Core authority boundary excludes Diary / Memory / Assistant / persistence / generation | ✅ |
| Golden vectors frozen | ✅ |

## 13. R1 Gate summary

```text
DIA-7 R1 Core Continuity Projection Contract

Codex A implementation     ✅ COMPLETE
DIA-7 focused tests        ✅ 14 passed
DIA-6 regression           ✅ included in 97 passed
DIA-5 regression           ✅ included in 97 passed
DIA-4 regression           ✅ included in 97 passed
DIA-3 regression           ✅ included in 97 passed
compileall                 ✅ PASS

Ready for Mira review      ▶
Codex B sabotage           ⏸ HOLD
DIA-7 R2 Assistant         ⏸ HOLD
```

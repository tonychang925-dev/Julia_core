# DIA-7 R1 — Core Continuity Projection Contract

> **Namespace:** CONT-DIA
> **Canonical phase:** CONT-DIA-7 — Continuity State Projection
> **Not to be confused with:** STORAGE-DIA-7 — Diary Retrieval

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

---

# DIA-7 R1.1 — RED-C1 Conflict Dependency Repair

## 14. Repair status

Previous target: `a58f5e73ea94ae290a7bcd3a7d008c1db87abb13`  
Mira review: RED  
Repair provenance: Codex A

Blocked finding:

```text
RED-C1 conflict semantics depended on lexical claim_id order
rather than target dependency / causal conflict order.
```

The bug allowed deterministic but wrong states, for example:

```text
A-correction CORRECT Z-original
Z-original APPEND
```

Lexical order could activate both correction and original, violating the R1 semantics that correction removes the target.

## 15. Repair scope

Only Core continuity projection conflict evaluation changed:

- `julia_core/continuity_projection/models.py`
- `tests/continuity_projection/test_dia7_core_contract.py`
- `docs/project_control/reports/phase-DIA-7-R1.md`

No DIA-3 trigger identity, DIA-4 context identity, DIA-5 handoff identity, DIA-6 lineage identity, Diary, Memory, Assistant, persistence, or generation surface changed.

## 16. Closed invariant

Canonical serialization order and conflict evaluation order are now separated.

Input canonicalization still sorts for stable bytes / digest:

```text
lineage_edges      -> lineage_digest order
candidate_claims   -> claim_id order
```

Projection evaluation now builds a target dependency graph:

```text
target claim
      ↓
targeted operation claim
```

Then applies deterministic topological ordering:

```text
causal dependency order first
claim_id tie-break only within same dependency level
```

Cycle semantics are fail-closed:

```text
A CORRECT B
B CORRECT A
        ↓
reject projection input
```

## 17. Repair acceptance matrix

| RED-C1 repair target | Status |
| --- | --- |
| Correction claim_id sorts before target -> only correction active | ✅ |
| Supersede claim_id sorts before target -> old target not active | ✅ |
| Deprecate claim_id sorts before target -> target remains absent | ✅ |
| Unresolved claim_id sorts before target -> both unresolved, neither active | ✅ |
| A -> B -> C correction chain -> terminal claim active | ✅ |
| Target dependency cycle -> fail closed | ✅ |
| Same semantic graph in different caller order -> same state digest | ✅ |

## 18. Repair validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_projection/test_dia7_core_contract.py -q
20 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/continuity_projection tests/continuity_projection/test_dia7_core_contract.py
PASS
```

## 19. Repair gate summary

```text
DIA-7 R1.1 Core Continuity Projection Contract

RED-C1 dependency-order conflict semantics      ✅ CLOSED
DIA-7 focused tests                             ✅ 20 passed
DIA-6/DIA-5/DIA-4/DIA-3 regression             ✅ 97 passed
compileall                                      ✅ PASS

Ready for Mira re-review                        ▶
Codex B sabotage                                ⏸ HOLD
DIA-7 R2 Assistant                              ⏸ HOLD
```

---

# DIA-7 R1.2 — RED-BR1 Same-Target Branch Repair

## 20. Repair status

Previous target: `66506961167eb1bfbc94d4a70f07c04327c904d4`  
Mira review: RED-BR1 accepted  
Repair provenance: Codex A

Blocked finding:

```text
A original
├── B CORRECT A
└── C CORRECT A
```

Dependency ordering correctly placed A before B/C, but branch authority remained undefined. The prior evaluator could emit both B and C as active, producing a deterministic but invalid continuity state.

## 21. Frozen branch invariant

R1.2 freezes fail-closed same-target branch semantics:

```text
For every target claim, at most one independent state-mutating dependent
may survive at the same causal generation.

Multiple sibling mutators without an explicit dependency/resolution relation
are ambiguous and fail closed.
```

State-mutating targeted rules covered by this invariant:

- `SUPERSEDE`
- `CORRECT`
- `DEPRECATE`
- `UNRESOLVED`

R1.2 does not elect winners by `claim_id`, caller order, timestamp, or rule type.

## 22. Repair semantics

Dependency graph construction now rejects any target with more than one direct targeted dependent:

```text
A -> B
A -> C
        ↓
ambiguous same-target mutation branch
        ↓
reject projection input
```

Explicit chains remain valid:

```text
A -> B -> C
        ↓
terminal C active
```

R1.2 intentionally does not auto-convert competing `CORRECT` / `SUPERSEDE` / `DEPRECATE` branches into `UNRESOLVED`. `UNRESOLVED` remains an explicit `ContinuityConflictRule`, not an invented repair state.

Branch convergence / merge is not supported by the R1 single-target claim schema and fails closed through the same ambiguity rule.

## 23. RED-BR1 acceptance matrix

| RED-BR1 repair target | Status |
| --- | --- |
| B CORRECT A + C CORRECT A -> reject | ✅ |
| B SUPERSEDE A + C SUPERSEDE A -> reject | ✅ |
| B CORRECT A + C DEPRECATE A -> reject | ✅ |
| B UNRESOLVED A + C CORRECT A -> reject | ✅ |
| A -> B -> C explicit correction chain -> terminal C active | ✅ |
| Branching convergence / merge unsupported in R1 -> reject | ✅ |
| Caller-order permutations of ambiguous branch -> all reject | ✅ |

## 24. Repair validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_projection/test_dia7_core_contract.py -q
26 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/continuity_projection tests/continuity_projection/test_dia7_core_contract.py
PASS
```

## 25. Repair gate summary

```text
DIA-7 R1.2 Core Continuity Projection Contract

RED-C1 dependency-order conflict semantics      ✅ CLOSED
RED-BR1 same-target branch ambiguity            ✅ CLOSED
DIA-7 focused tests                             ✅ 26 passed
DIA-6/DIA-5/DIA-4/DIA-3 regression             ✅ 97 passed
compileall                                      ✅ PASS

Ready for Mira re-review                        ▶
Codex B re-sabotage                             ⏸ HOLD
DIA-7 R2 Assistant                              ⏸ HOLD
```

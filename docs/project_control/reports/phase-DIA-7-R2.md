# DIA-7 R2.0 — Assistant Continuity Integration Contract

> **Namespace:** CONT-DIA
> **Canonical phase:** CONT-DIA-7 — Continuity State Projection
> **Not to be confused with:** STORAGE-DIA-7 — Diary Retrieval

## 0. Status

Phase: DIA-7 — Continuity State / Identity Projection  
Artifact: R2.0 Assistant integration contract implementation  
Implementation provenance: Codex A  
Branch: `codex/dia-7/continuity-projection-r0`  
Base: DIA-7 R1.2 Core Continuity Projection Contract `cc4008a`

Frozen upstream inputs remain immutable:

- DIA-3 Reflection Trigger Contract
- DIA-4 Reflection Context Contract
- DIA-5 Reflection Context Handoff Contract
- DIA-6 Context Evolution / Lineage Contract
- DIA-7 R1.2 Core Continuity Projection Contract

R2.0 does not modify Core continuity projection, DIA-6 lineage, Diary, Memory, Context OS, model generation, or persistence. Assistant consumes projected continuity state; it does not own continuity truth.

## 1. Implemented module

```text
julia_core/assistant_continuity/
  __init__.py
  models.py

tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py
```

Public R2 nouns:

- `AssistantContinuityStatePackage`
- `ContinuityStateInputPort`
- `ContinuityStateBindingStore`
- `AssistantContinuitySessionBinding`
- `AssistantContinuityResponseContext`
- `ContinuityConsumptionAudit`
- `StrictAssistantContinuityBinder`

## 2. Core R2 boundary

Frozen rule:

```text
Assistant consumes ContinuityState,
but does not own continuity truth.
```

Valid R2 path:

```text
DIA-7 ContinuityState
        ↓
AssistantContinuityStatePackage
        ↓
AssistantContinuitySessionBinding
        ↓
AssistantContinuityResponseContext
        ↓
Assistant reads active_claims / unresolved_conflicts
```

Invalid R2 path:

```text
model output / Assistant reasoning / manual patch
        ↓
ContinuityState or continuity truth
```

## 3. Cross-binding invariant

R2.0 freezes exact binding across:

```text
session_id
↔ continuity_state_digest
↔ source_graph_digest
↔ projection_policy_fingerprint
↔ package_digest
```

Binding is fail-closed for:

- wrong session
- wrong continuity state digest
- wrong source graph digest
- wrong projection policy fingerprint
- wrong package digest
- corrupted / stale `ContinuityState`
- manual or model-generated package / binding values

## 4. Assistant response context binding

`AssistantContinuityResponseContext` is constructed only from:

```text
AssistantContinuitySessionBinding
+ exact AssistantContinuityStatePackage
```

The response context repeats the binding digest and state/source/policy identities in its canonical bytes. This ensures an Assistant response context is bound to the exact continuity state it consumed.

Assistant-visible claim surfaces are read-only tuples copied from the exact package:

- `active_claims`
- `unresolved_conflicts`

R2.0 exposes no write path into `ContinuityState`.

## 5. Restart / replay binding

`ContinuityStateBindingStore` is an R2.0 in-memory contract store for restart/replay validation only. Runtime persistence is deferred to R2.1.

Replay requires:

```text
stored session binding
+ replayed package
        ↓
exact digest cross-binding match
```

A missing session or package mismatch fails closed.

## 6. Audit split

`ContinuityConsumptionAudit` records consumption diagnostics and timestamp, but audit fields do not enter:

- `package_digest`
- `binding_digest`
- `response_context_digest`
- `continuity_state_digest`

## 7. Authority exclusions

The R2.0 module has no authority over:

- Core continuity projection mutation
- DIA-6 lineage mutation
- Diary
- Memory
- Context OS writes
- filesystem persistence
- model generation

Static boundary tests assert those imports / side effects are absent from `julia_core/assistant_continuity`.

## 8. Golden vectors

Fixed DIA-7 R2.0 fixture vectors:

```text
package_digest:
4a13179e7ee38c90df1f728a550b3a49bc0decc80cd27392a23574d433bb1734

binding_digest:
6a6df4c91a8efb0650774ec0b59deb1ff5916efb9a391c27b7286c879ca95c08

response_context_digest:
8270998a600109ab4dd4f65cde6ff48233837d3b7a2e4ebaf9ea6df4ad387b9f
```

## 9. Acceptance matrix

| Acceptance target | Status |
| --- | --- |
| Package requires exact `ContinuityState` | ✅ |
| Package exposes only active claims / unresolved conflicts | ✅ |
| Session/state/source graph/policy/package cross-binding exact | ✅ |
| Wrong state digest fails closed | ✅ |
| Wrong source graph digest fails closed | ✅ |
| Wrong policy fingerprint fails closed | ✅ |
| Corrupted / stale state digest rejected | ✅ |
| Restart/replay validates exact package | ✅ |
| Wrong session fails closed | ✅ |
| Same session rebinding to different state rejected | ✅ |
| Assistant response context bound to exact consumed state | ✅ |
| Audit metadata does not affect binding identity | ✅ |
| Model output / manual patch cannot create binding or response context | ✅ |
| R2 authority boundary excludes Diary / Memory / persistence / generation | ✅ |
| Golden vectors frozen | ✅ |

## 10. Owner validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py -q
11 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
37 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/assistant_continuity tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py
PASS
```

## 11. R2.0 Gate summary

```text
DIA-7 R2.0 Assistant Continuity Integration Contract

Codex A implementation                    ✅ COMPLETE
DIA-7 R2 focused tests                     ✅ 11 passed
DIA-7 R1 regression                        ✅ included in 37 passed
DIA-6/DIA-5/DIA-4/DIA-3 regression         ✅ 97 passed
compileall                                 ✅ PASS

Ready for Mira review                      ▶
Codex B sabotage                           ⏸ HOLD
DIA-7 R2.1 runtime / persistence           ⏸ HOLD
```

---

# DIA-7 R2.0.1 — RED-PB1 / RED-BI1 Integrity Boundary Repair

## 12. Repair status

Previous target: `1d7a8f45bd42321231243431792a19bd93b93d00`  
Mira review: RED  
Repair provenance: Codex A

Blocked findings:

```text
RED-PB1 package stale-digest / foreign-claims bypass
RED-BI1 binding stale-digest / session mutation bypass
```

The R2.0 normal construction path was valid, but consumption boundaries trusted stored digest fields without revalidating the object's current semantic content at use time.

## 13. Repair scope

Only Assistant continuity integration boundary validation changed:

- `julia_core/assistant_continuity/models.py`
- `tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py`
- `docs/project_control/reports/phase-DIA-7-R2.md`

No Core projection, DIA-6 lineage, Diary, Memory, Context OS, persistence, or generation surface changed.

## 14. Closed invariant

R2.0.1 freezes:

```text
constructor validation is not sufficient.
Every consumption boundary must revalidate current semantic integrity.
```

Package integrity now verifies:

- exact `AssistantContinuityStatePackage` type
- exact `ContinuityState` type
- recomputed `ContinuityState` digest
- package state digest matches embedded state digest
- source graph digest matches embedded state
- projection policy fingerprint matches embedded state
- `active_claims` equals embedded state's active claims
- `unresolved_conflicts` equals embedded state's unresolved conflicts
- recomputed package digest equals stored `package_digest`

Binding integrity now verifies:

- exact `AssistantContinuitySessionBinding` type
- session id non-empty
- state/source/policy/package digests are valid SHA-256 identity fields
- recomputed binding digest equals stored `binding_digest`

## 15. Revalidated boundaries

Package integrity is rechecked at:

- `StrictAssistantContinuityBinder.bind_for_session()`
- `AssistantContinuitySessionBinding.__init__()`
- `AssistantContinuityResponseContext.__init__()`
- `ContinuityStateBindingStore.replay_validate()`

Binding integrity is rechecked at:

- `ContinuityStateBindingStore.save()`
- `ContinuityStateBindingStore.load()`
- `ContinuityStateBindingStore.replay_validate()` via load
- `AssistantContinuityResponseContext.__init__()`

## 16. Response context identity hardening

`AssistantContinuityResponseContext` now carries `session_id` as an explicit identity field in addition to the binding digest:

```text
response_context.session_id
response_context.binding_digest
response_context.continuity_state_digest
response_context.source_graph_digest
response_context.projection_policy_fingerprint
```

This prevents a response context from relying solely on a stale binding digest as session proof.

## 17. RED acceptance matrix

| RED repair target | Status |
| --- | --- |
| PB1 package active claims swapped after construction -> response context rejects | ✅ |
| PB2 package unresolved conflicts swapped after construction -> rejects | ✅ |
| PB3 package field mutated with stale package digest -> binder rejects | ✅ |
| BI1 binding session id mutated with stale binding digest -> response/store reject | ✅ |
| BI2 binding state/source/policy/package field mutated -> reject | ✅ |
| GOOD untouched package + binding -> green | ✅ |
| REPLAY stale package -> fail closed | ✅ |
| REPLAY stale binding -> fail closed | ✅ |
| Response context includes explicit session id | ✅ |

## 18. Repair validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py -q
17 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
43 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/assistant_continuity tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py
PASS
```

Updated response-context golden vector:

```text
response_context_digest:
68c9690f9a64623b13df59b160fb06fea81539e117c1186c2cc3532240881188
```

Package and binding golden vectors remain stable:

```text
package_digest:
4a13179e7ee38c90df1f728a550b3a49bc0decc80cd27392a23574d433bb1734

binding_digest:
6a6df4c91a8efb0650774ec0b59deb1ff5916efb9a391c27b7286c879ca95c08
```

## 19. Repair gate summary

```text
DIA-7 R2.0.1 Assistant Continuity Integration Contract

RED-PB1 package stale-digest bypass          ✅ CLOSED
RED-BI1 binding stale-digest bypass          ✅ CLOSED
DIA-7 R2 focused tests                       ✅ 17 passed
DIA-7 R1 regression                          ✅ included in 43 passed
DIA-6/DIA-5/DIA-4/DIA-3 regression           ✅ 97 passed
compileall                                   ✅ PASS

Ready for Mira re-review                     ▶
Codex B sabotage                             ⏸ HOLD
DIA-7 R2.1 runtime / persistence             ⏸ HOLD
```

---

# DIA-7 R2.0.2 — RED-SK1 Store Lookup-Key Repair

## 20. Repair status

Previous target: `758664c`  
Mira review: RED-SK1 accepted  
Repair provenance: Codex A

Blocked finding:

```text
object integrity ✅
lookup identity binding ❌
```

A fully self-consistent `Binding(session-B)` could be placed under `store["session-A"]`. Prior `load("session-A")` validated object integrity but did not reconcile lookup key with `binding.session_id`.

## 21. Closed store invariant

R2.0.2 freezes:

```text
store key == requested_session_id == binding.session_id
```

Lookup path is now:

```text
requested session_id
    ↓
lookup binding by key
    ↓
validate binding current semantic integrity
    ↓
require binding.session_id == requested session_id
    ↓
return binding
```

`replay_validate()` inherits the same check through `load()`.

Save remains single-source identity:

```text
save(binding)
    ↓
key = validated binding.session_id
```

No `save(session_id, binding)` dual-source API exists in R2.0.

## 22. RED-SK1 acceptance matrix

| RED-SK1 repair target | Status |
| --- | --- |
| Stored Binding A mutated to self-consistent session-B -> load("A") rejects | ✅ |
| Same setup -> replay_validate("A", Package A) rejects | ✅ |
| Fully valid foreign Binding B under key A -> rejects | ✅ |
| Untouched Binding A load("A") -> green | ✅ |
| load("B") when only key A exists -> missing session, no alias | ✅ |
| Mutate A -> B -> recompute -> A with changed package identity -> cross-binding rejects | ✅ |

## 23. Repair validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py -q
22 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
48 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/assistant_continuity tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py
PASS
```

## 24. Repair gate summary

```text
DIA-7 R2.0.2 Assistant Continuity Integration Contract

RED-PB1 package stale-digest bypass          ✅ CLOSED
RED-BI1 binding stale-digest bypass          ✅ CLOSED
RED-SK1 store key/session mismatch           ✅ CLOSED
DIA-7 R2 focused tests                       ✅ 22 passed
DIA-7 R1 regression                          ✅ included in 48 passed
DIA-6/DIA-5/DIA-4/DIA-3 regression           ✅ 97 passed
compileall                                   ✅ PASS

Ready for Mira re-review                     ▶
Codex B re-sabotage                          ⏸ HOLD
DIA-7 R2.1 runtime / persistence             ⏸ HOLD
```

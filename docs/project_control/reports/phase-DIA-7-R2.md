# DIA-7 R2.0 — Assistant Continuity Integration Contract

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

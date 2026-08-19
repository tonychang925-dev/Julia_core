# DIA-6 R1 — Core Context Evolution Contract

## 0. Status

Phase: DIA-6 — Context Continuity / Evolution Surface  
Artifact: R1 Core implementation  
Implementation provenance: Codex A  
Branch: `codex/dia-6/context-evolution-r1`  
Base: DIA-5 R1 Core Handoff Contract `f8292082f44977df3a015e7ea1f58296e8ed165a`  
Frozen design input: DIA-6 R0 @ `c18dbf24c65cbdebb511a4851a2b745725ee5a33`

Frozen inputs remain immutable:

- DIA-4 R1 Core Context Contract: `017ba4e2d77f3a8e3cddbcb0f71822ea0edf9e48`
- DIA-5 R1 Core Handoff Contract: `f8292082f44977df3a015e7ea1f58296e8ed165a`

DIA-6 R1 does not modify DIA-4 context identity, DIA-5 handoff identity, transport state, Diary, Memory, Context OS, or generation authority.

## 1. Implemented module

```text
julia_core/context_evolution/
  __init__.py
  models.py

tests/context_evolution/test_dia6_core_contract.py
```

Public Core nouns:

- `ContextLineageNode`
- `ContextEvolutionKind`
- `EvolutionAuthority`
- `ContextEvolutionPolicy`
- `ContextEvolutionOperation`
- `ContextLineageEdge`
- `ContextEvolutionAudit`
- `ContextEvolutionValidator`
- `StrictContextEvolutionValidator`

## 2. Boundary semantics

DIA-6 R1 freezes:

```text
Mutation ≠ Evolution
```

Valid evolution is:

```text
immutable parent ReflectionContext identity
        ↓
ContextEvolutionOperation
        ↓
immutable child ReflectionContext identity
        ↓
ContextLineageEdge
```

Invalid evolution is:

```text
modify parent bytes in place
        ↓
claim same context_digest
```

## 3. Identity domains

DIA-6 R1 keeps three domains separate:

```text
parent context identity = DIA-4 context_digest
child context identity  = DIA-4 context_digest
lineage edge identity   = DIA-6 lineage_digest
```

`ContextLineageNode` carries:

- `context_digest`
- `context_version`
- `assembly_policy_revision`
- `assembly_policy_fingerprint`
- `context_semantic_bytes_sha256`

Same context digest with different semantic bytes hash is corruption, not evolution.

## 4. Evolution policy semantics

`ContextEvolutionPolicy` binds complete Core semantics:

- allowed structural operation kinds
- parent verification revision
- child validation revision
- lineage digest algorithm revision
- reason ref bound

Unknown algorithm/verification revisions fail closed. Policy fingerprint is canonical SHA-256 over length-framed fields.

## 5. Structural-only operation kinds

Closed v1 vocabulary:

```text
FACT_APPEND
FACT_CORRECTION
CONTEXT_SPLIT
CONTEXT_MERGE
CONTEXT_DEPRECATION
```

R1 implements single-parent/single-child lineage and explicitly fails closed for merge/split validation until a multi-node lineage model is frozen.

No arbitrary labels such as `relationship_breakthrough`, `emotional_significance`, or `memory_worthy` are accepted.

## 6. Reason refs and authority

`ContextEvolutionOperation.reason_refs` are bounded canonical `TriggerSourceRef` values only:

- non-empty tuple
- exact `TriggerSourceRef` type
- duplicate refs rejected
- max count enforced by policy

`EvolutionAuthority` is a structural value object. Production authority wiring remains an Assistant R2 obligation; type-valid operation objects are not by themselves production provenance.

## 7. Audit split

`ContextEvolutionAudit` is an observability sidecar. It does not enter:

- parent context semantic bytes
- child context semantic bytes
- `ContextLineageEdge.lineage_digest`
- DIA-5 handoff semantic bytes

Changing audit diagnostics leaves lineage digest unchanged.

## 8. Golden vectors

Fixed DIA-6 R1 fixture vectors:

```text
policy_fingerprint:
01bf15b7f121c57bbc982b48ab4f59d099d8ba3d9b2ceaa4473e20ece3272ac4

lineage_digest:
c2b704a320bf25669228295d141327973acbdbbbc4ae76a764935dbbb9131f6f
```

## 9. Owner validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py -q
13 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_handoff/test_dia5_core_contract.py -q
16 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_context/test_dia4_core_contract.py -q
24 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_trigger/test_dia3_core_contract.py -q
44 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/context_evolution tests/context_evolution/test_dia6_core_contract.py
PASS
```

## 10. R1 Gate summary

```text
DIA-6 R1 Core Context Evolution Contract

Codex A implementation     ✅ COMPLETE
DIA-6 focused tests        ✅ 13 passed
DIA-5 regression           ✅ 16 passed
DIA-4 regression           ✅ 24 passed
DIA-3 regression           ✅ 44 passed
compileall                 ✅ PASS

Ready for Mira review      ▶
Codex B sabotage           ⏸ HOLD
DIA-6 R2 Assistant         ⏸ HOLD
```

---

# DIA-6 R1.1 — Provenance Boundary Repair

## 11. Repair status

Previous target: `078cf9ca419c4ab85d1a7ec6aa86e23192289848`  
Codex B sabotage: RED  
Repair provenance: Codex A

Blocked findings:

```text
RED-1 parent digest + mutated semantic bytes accepted
RED-2 direct fake lineage edge accepted
RED-3 operation with fake parent node accepted
```

## 12. Repair scope

Only Core evolution provenance-boundary hardening changed:

- `julia_core/context_evolution/models.py`
- `tests/context_evolution/test_dia6_core_contract.py`
- `docs/project_control/reports/phase-DIA-6-R1.md`

No DIA-4 context identity, DIA-5 handoff identity, transport lifecycle, Diary, Memory, Context OS, or generation surface changed.

## 13. Closed invariants

### ContextLineageNode requires exact ReflectionContext provenance

`ContextLineageNode` is no longer raw digest-field constructible. It is created only from an exact DIA-4 `ReflectionContext` via:

```text
ContextLineageNode.from_context(context)
```

The constructor recomputes:

```text
SHA-256(context.semantic_canonical_bytes(include_digest=False))
```

and requires it to equal `context.context_digest` before deriving the node. A borrowed digest attached to mutated semantic bytes fails closed.

### ContextLineageEdge requires validated operation path

`ContextLineageEdge` is no longer raw-field constructible. It requires:

```text
ContextEvolutionOperation
+ ContextEvolutionPolicy
+ operation.validate_against_policy(policy)
```

The public validator remains the intended production validation surface:

```text
StrictContextEvolutionValidator.validate(operation, policy)
        ↓
ContextLineageEdge
```

### Fake parent nodes rejected by public construction boundary

Caller-supplied digest bundles cannot create `ContextLineageNode`; non-`ReflectionContext` inputs fail closed. Operation validation also keeps exact type checks for operation and policy.

## 14. Repair validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py -q
13 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_handoff/test_dia5_core_contract.py -q
16 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_context/test_dia4_core_contract.py -q
24 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_trigger/test_dia3_core_contract.py -q
44 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/context_evolution tests/context_evolution/test_dia6_core_contract.py
PASS
```

Golden vectors remain stable:

```text
policy_fingerprint:
01bf15b7f121c57bbc982b48ab4f59d099d8ba3d9b2ceaa4473e20ece3272ac4

lineage_digest:
c2b704a320bf25669228295d141327973acbdbbbc4ae76a764935dbbb9131f6f
```

## 15. Repair gate summary

```text
DIA-6 R1.1 Core Context Evolution Contract

RED-1 parent digest + mutated bytes      ✅ CLOSED
RED-2 direct fake lineage edge           ✅ CLOSED
RED-3 fake parent node                   ✅ CLOSED
regressions                              ✅ GREEN

Ready for Codex B re-sabotage            ▶
Final freeze                             ⏸
```

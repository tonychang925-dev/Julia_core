# DIA-7-E2E — Continuity Identity Chain Gate

> **Namespace:** CONT-DIA
> **Canonical phase:** CONT-DIA-7 — Continuity State Projection
> **Not to be confused with:** STORAGE-DIA-7 — Diary Retrieval

## 0. Status

Gate: DIA-7-E2E Continuity Identity Chain Gate  
Implementation provenance: Codex A  
Branch: `codex/dia-7/continuity-projection-r0`  
Base: DIA-7 phase closure `5cdc837`

Scope:

```text
E2E integration only
New Core nouns: NONE
Frozen semantics modified: NO
```

## 1. Gate question

```text
After a real experience enters verified causal history,
and after process/window restart,
can Julia still make coherent, evidence-bound choices from the restored current continuity state?
```

## 2. Implemented artifact

```text
tests/e2e/test_dia7_continuity_identity_chain.py
```

No production module was changed for this gate.

## 3. Full chain under test

```text
Trigger
→ Reflection Context
→ Handoff / Transport
→ Evolution
→ Lineage
→ Continuity Projection
→ Assistant Consumption
→ Persistence
→ Cold Restart
→ Behavior
```

## 4. Acceptance lanes

| Lane | Status |
| --- | --- |
| Experience admission enters DIA-3 trigger/evidence, not direct ContinuityState write | ✅ |
| DIA-4 reflection context creates stable canonical context digest | ✅ |
| DIA-5 handoff preserves exact context identity | ✅ |
| DIA-6 evolution creates child + lineage edge and preserves parent immutability | ✅ |
| DIA-7 R1 projection emits evidence-bound active/conflicted claims | ✅ |
| R2.0 Assistant response context consumes exact package/binding | ✅ |
| R2.1 persistence stores recoverable cross-bound runtime artifact | ✅ |
| True cold restart restores state/package/binding from disk only | ✅ |
| Post-restart behavior uses restored claims/conflicts | ✅ |
| Cross-layer identity mismatch fails closed | ✅ |

## 5. GREEN scenarios

### GREEN-1 — Experience changes post-restart behavior

Scenario:

```text
Before experience:
  behavior choice = X

Verified experience E:
  prefer Y

Projection:
  active claim = stable_preference=prefer Y because evidence E

Persistence + cold restart:
  live refs deleted
  new runtime loads only disk snapshot

Post-restart behavior:
  choice = Y
  response context binds claim evidence lineage digest
```

Status: ✅

### GREEN-2 — Unresolved conflict is preserved

Scenario:

```text
history supports prefer Y
history also supports prefer Z
explicit UNRESOLVED conflict
        ↓
persist / cold restart
        ↓
Assistant response context has unresolved conflicts
        ↓
behavior returns unresolved marker, not Y or Z winner
```

Status: ✅

This validates:

```text
History clear -> project stable state.
History ambiguous -> preserve uncertainty; do not invent a winner.
```

## 6. RED lanes covered

| RED lane | Status |
| --- | --- |
| E2E-RED-1 wrong handoff context digest | ✅ reject |
| E2E-RED-2 lineage edge points to foreign child context | ✅ reject |
| E2E-RED-3 projection state from wrong source_graph | ✅ reject |
| E2E-RED-4 Assistant package A + binding B | ✅ reject |
| E2E-RED-5 persisted snapshot moved under foreign session key | ✅ reject |
| E2E-RED-6 cold restart payload valid-looking but claim evidence foreign | ✅ reject |
| E2E-RED-7 behavior reads stale pre-restart state instead of restored state | ✅ guarded by deterministic behavior assertion |
| E2E-RED-8 unresolved conflict silently collapsed into ACTIVE choice | ✅ reject / preserved unresolved behavior |

## 7. Behavior assertion model

The E2E test intentionally avoids fuzzy model-likeness scoring.

Behavior assertion is deterministic:

```text
restored active claim: stable_preference=prefer Y because evidence E
        ↓
choice must be Y

restored unresolved conflict: prefer Y vs prefer Z
        ↓
choice must preserve unresolved state
```

This tests continuity-causes-behavior, not whether a prompt can imitate continuity.

## 8. Validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/e2e/test_dia7_continuity_identity_chain.py -q
10 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/e2e/test_dia7_continuity_identity_chain.py tests/continuity_persistence/test_dia7_r21_persistence_contract.py tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
94 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q tests/e2e/test_dia7_continuity_identity_chain.py
PASS
```

## 9. Gate summary

```text
DIA-7-E2E Continuity Identity Chain Gate

DIA-3 Trigger admission                ✅
DIA-4 Reflection identity              ✅
DIA-5 Exact handoff                    ✅
DIA-6 Evolution + lineage              ✅
DIA-7 Projection                       ✅
R2.0 Assistant consumption             ✅
R2.1 Persistence                       ✅
Cold restart                           ✅
Post-restart behavior continuity       ✅
Fail-closed cross-layer sabotage       ✅

New Core nouns                         NONE
Frozen semantics modified              NO

Ready for Mira review                  ▶
Codex B sabotage                       ⏸
Wave-level closure                     ⏸
```

---

# DIA-7-E2E.1 — RED-TG1 Trigger Admission Repair

## 10. Repair status

Previous target: `26daa2cbd28ffbe80f8d3207a77c4011cf36ab70`  
Mira review: RED-TG1 accepted  
Repair provenance: Codex A

Blocked finding:

```text
E2E fixture manually minted ReflectionOpportunity,
so the first link was manually-constructed opportunity -> DIA-4
instead of raw experience -> DIA-3 admission -> DIA-4.
```

## 11. Repair scope

Changed only the E2E gate test and report:

- `tests/e2e/test_dia7_continuity_identity_chain.py`
- `docs/project_control/reports/phase-DIA-7-E2E.md`

No Core nouns were added. No frozen semantics were modified.

## 12. Repaired first-link path

The E2E fixture now starts from raw event dictionaries and enters the frozen DIA-3 public admission surface:

```text
raw event
    ↓
TriggerSourceRef
    ↓
OpportunityKey
    ↓
ReflectionOpportunity
    ↓
PendingOpportunity.pending()
    ↓
ReflectionOpportunityHandoff
    ↓
DIA-4 DeterministicReflectionContextAssembler
```

Downstream DIA-4 receives only the exact opportunity admitted by DIA-3. The context asserts:

```text
ReflectionContext.opportunity_id == PendingOpportunity.opportunity_id
ReflectionContext.opportunity_key_digest == sha256(DIA-3 opportunity key bytes)
```

## 13. Trigger gate negative semantics

If raw event admission says no reflection opportunity exists:

```text
raw event admit_reflection = False
    ↓
_admit_experience(...) returns None
    ↓
DIA-4 context construction fails closed
```

This ensures the E2E gate does not allow non-admitted experiences to bypass trigger admission and enter the continuity chain.

## 14. Cross-layer wording clarification

E2E-RED-2 is an E2E composition invariant assertion:

```text
lineage child context digest must equal handoff context digest
```

It is not reported as a single frozen production module automatically rejecting the mismatch. The E2E gate owns this cross-layer reconciliation check.

E2E-RED-7 remains a deterministic behavior boundary harness. It proves the test behavior reads the restored response context, not a fuzzy runtime model behavior module.

## 15. RED-TG1 acceptance matrix

| RED-TG1 repair target | Status |
| --- | --- |
| raw event -> actual DIA-3 admission -> opportunity -> full GREEN chain | ✅ |
| trigger admission says no -> no downstream context / continuity chain | ✅ |
| wrong trigger source/evidence cannot be substituted downstream | ✅ |
| opportunity used by DIA-4 is exactly DIA-3-produced opportunity identity | ✅ |
| original GREEN behavior continuity remains green | ✅ |
| unresolved conflict behavior remains green | ✅ |
| original 8 RED lanes remain green | ✅ |

## 16. Repair validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/e2e/test_dia7_continuity_identity_chain.py -q
14 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/e2e/test_dia7_continuity_identity_chain.py tests/continuity_persistence/test_dia7_r21_persistence_contract.py tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
98 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q tests/e2e/test_dia7_continuity_identity_chain.py
PASS
```

## 17. Repaired gate summary

```text
DIA-7-E2E Continuity Identity Chain Gate

RED-TG1 actual DIA-3 trigger admission       ✅ CLOSED
DIA-3 Trigger admission                      ✅
DIA-4 Reflection identity                    ✅
DIA-5 Exact handoff                          ✅
DIA-6 Evolution + lineage                    ✅
DIA-7 Projection                             ✅
R2.0 Assistant consumption                   ✅
R2.1 Persistence                             ✅
Cold restart                                 ✅
Post-restart behavior continuity             ✅
Fail-closed cross-layer sabotage             ✅

New Core nouns                               NONE
Frozen semantics modified                    NO

Ready for Mira re-review                     ▶
Codex B sabotage                             ⏸
Wave-level closure                           ⏸
```

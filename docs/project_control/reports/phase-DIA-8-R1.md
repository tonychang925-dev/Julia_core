# DIA-8 R1 — Core Decision Invariance Contract

> **Namespace:** CONT-DIA
> **Canonical phase:** CONT-DIA-8 — Continuity-to-Decision Invariance
> **Not to be confused with:** STORAGE-DIA-8 — Electron Diary UI

Status: ✅ REPAIRED / READY FOR MIRA RE-REVIEW
Phase name: **DIA-8 — Continuity-to-Decision Invariance**
Base decision: Mira accepted R0.1 at `9717abc3d6532512bc93f124cfc143b809b19b18`.
Repair target: Mira RED review of `2b16a397a9d070e9e05d856a592f8550d540a7bf`.

## Purpose

DIA-8 protects the next failure mode after DIA-7:

```text
same ContinuityState
+ same DecisionSituation
+ different model/runtime
→ decision semantics must remain within continuity-authorized bounds
```

R1 implements only the deterministic Core evaluator for already-structured decision semantics. It does not parse natural-language model output and does not use a model-as-judge authority.

## Frozen R1 nouns

- `DecisionSituation`
- `CandidateDecision`
- `DecisionInvariantPolicy`
- `DecisionEvaluationResult`
- `DecisionConsistencyStatus`
- `DecisionEvidenceBinding`
- `StrictDecisionInvariantEvaluator`

## Frozen status enum

```text
CONSISTENT
DRIFT
UNDERDETERMINED
```

Semantics:

- `CONSISTENT`: candidate decision is supported by exact continuity claim bindings and violates no explicit continuity invariant.
- `DRIFT`: candidate decision is validly structured but contradicts a specific continuity claim, unresolved conflict, forbidden action, or explicit priority relation.
- `UNDERDETERMINED`: continuity state lacks sufficient ordering/constraint to choose a winner; Core does not invent priority.

Invalid inputs fail closed with `ValueError`; they are not reported as `DRIFT`.

## R1 authority boundaries

✅ Structured input only:

```text
ContinuityState
+ DecisionSituation
+ structured CandidateDecision
+ DecisionInvariantPolicy
→ DecisionEvaluationResult
```

Explicitly out of scope / forbidden:

- Natural-language response extraction
- Model-output classification
- LLM judge / “looks like Julia” scoring
- DIA-7 schema mutation
- Implicit priority invention
- Assistant-generated continuity truth

## RED repair closure

### RED-EB1 — proof binding completeness

Closed by requiring every accepted claim used as support to have at least one exact `DecisionEvidenceBinding`.

```text
accepted_claim_ids ⊆ evidence_binding.claim_ids
```

Each binding is then revalidated against the exact restored/projected `ContinuityState` claim lineage. Missing support is invalid proof input and fails closed; it is not `UNDERDETERMINED` and not `DRIFT`.

Regression coverage:

- EB1-A accepted claim without evidence binding → reject
- EB1-B one accepted claim bound, another unbound → reject
- EB1-C evidence binding points to valid claim but wrong lineage → reject
- EB1-D complete exact bindings → CONSISTENT

### RED-PA1 — priority authority binding

Closed by preventing `DecisionSituation.required_priority_relation` from acting as standalone truth authority.

R1 does not parse natural language and does not mutate DIA-7. Instead, priority is enabled only when the candidate binds an exact active continuity claim whose DIA-7 payload is the deterministic structured token:

```text
priority=<lowercase required priority relation>
```

Example:

```text
required_priority_relation = EVIDENCE_OVER_APPEASEMENT
requires an active, evidence-bound claim payload exactly:
priority=evidence_over_appeasement
```

If no such bound claim exists, the result is `UNDERDETERMINED`. The evaluator does not pick a winner and does not treat the situation field alone as authority.

Regression coverage:

- PA1-A priority exists only in `DecisionSituation` → UNDERDETERMINED
- PA1-B unrelated continuity claim does not authorize arbitrary priority → UNDERDETERMINED
- PA1-C exact continuity-backed priority authority → CONSISTENT
- PA1-D missing priority authority → UNDERDETERMINED, no auto-winner

## Deterministic proof-bearing result

`DecisionEvaluationResult` records:

- `status`
- `supporting_claim_ids`
- `violated_claim_ids`
- `unresolved_claim_ids`
- `applied_rules`
- `policy_fingerprint`
- `continuity_state_digest`
- `situation_digest`
- `candidate_decision_digest`
- `evaluation_digest`

This makes each result explainable as a digest-bound proof, not only a label.

## No implicit priority invention

R1 freezes the DIA-8 fail-closed rule:

```text
No explicit continuity-backed ordering
→ no winner
→ UNDERDETERMINED
```

The evaluator never chooses a side because one value “sounds more important.” Priority must arrive through explicit, evidence-bound continuity claim semantics.

## Implemented files

- `julia_core/decision_invariance/models.py`
- `julia_core/decision_invariance/__init__.py`
- `tests/decision_invariance/test_dia8_core_contract.py`

## Adversarial matrix coverage

| Case | Meaning | Result |
| --- | --- | --- |
| D8-A1 | same decision / different wording | ✅ CONSISTENT, same digest |
| D8-A2 | same stance / different politeness | ✅ CONSISTENT |
| D8-B1 | appeasement overrides evidence-backed judgment | ✅ DRIFT |
| D8-B2 | evidence-backed disagreement with warm wording | ✅ CONSISTENT |
| D8-C1 | explicit relationship boundary respected | ✅ CONSISTENT |
| D8-C2 | boundary ignored under pressure | ✅ DRIFT |
| D8-D1 | active commitment preserved | ✅ CONSISTENT |
| D8-D2 | commitment abandoned for convenience | ✅ DRIFT |
| D8-E1 | unresolved conflict preserved | ✅ CONSISTENT |
| D8-E2 | model invents winner | ✅ DRIFT |
| D8-F1 | competing values with frozen priority | ✅ CONSISTENT deterministic |
| D8-F2 | competing values without frozen priority | ✅ UNDERDETERMINED |

## Meta-invariants

| Invariant | Result |
| --- | --- |
| M1 same semantic inputs, different construction order → same result digest | ✅ |
| M2 wording/style fields vary → same decision evaluation | ✅ |
| M3 missing priority → UNDERDETERMINED, never auto-winner | ✅ |
| M4 foreign claim/evidence binding → reject, not DRIFT | ✅ |
| M5 wrong ContinuityState digest / policy fingerprint → fail closed | ✅ |

Additional boundary assertion: R1 module exposes no natural-language extraction or model-as-judge surface.

## Golden vectors

The RED-PA1 repair intentionally revs `EVALUATION_ALGORITHM_REVISION` from `v1` to `v2` because priority authority semantics changed.

```text
DecisionInvariantPolicy fingerprint:
118635f578f6e42e4877ee9b3ce9340e86ca1a3276141940bd03373c4a2b1b07

Golden CONSISTENT evaluation_digest:
1b4f5253fa938c63d01815026a0bfd2612f006118d0dd3e1ebaa2046ad7228ce
```

## Validation

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/decision_invariance/test_dia8_core_contract.py -q
→ 17 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest \
  tests/decision_invariance/test_dia8_core_contract.py \
  tests/e2e/test_dia7_continuity_identity_chain.py \
  tests/continuity_persistence/test_dia7_r21_persistence_contract.py \
  tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py \
  tests/continuity_projection/test_dia7_core_contract.py -q
→ 115 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest \
  tests/context_evolution/test_dia6_core_contract.py \
  tests/reflection_handoff/test_dia5_core_contract.py \
  tests/reflection_context/test_dia4_core_contract.py \
  tests/reflection_trigger/test_dia3_core_contract.py -q
→ 97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q \
  julia_core/decision_invariance \
  tests/decision_invariance/test_dia8_core_contract.py
→ PASS
```

## Gate

```text
DIA-8 R0.1 failure-mode discovery       ✅ CLOSED ENOUGH FOR R1
DIA-8 phase name                         ✅ FROZEN
Name                                     Continuity-to-Decision Invariance

DIA-8 R1 Core evaluator                  ✅ IMPLEMENTED
RED-EB1 proof binding completeness       ✅ CLOSED
RED-PA1 priority authority binding       ✅ CLOSED
Structured CandidateDecision             ✅
Three-value semantics                    ✅
Evidence-bound result                    ✅
No implicit priority invention           ✅
Invalid input != DRIFT                   ✅
Natural-language extraction              ❌ OUT OF SCOPE
LLM judge authority                      ❌ FORBIDDEN
DIA-7 schema mutation                    ❌ FORBIDDEN

Mira re-review                           ▶ REQUESTED
Codex B sabotage                         ⏸ HOLD UNTIL MIRA GREEN
```

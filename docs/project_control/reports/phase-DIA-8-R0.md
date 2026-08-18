# DIA-8 R0 — Failure Mode Discovery

## 0. Status

Phase: DIA-8 — R0 Failure Mode Discovery  
Provenance: Codex A  
Base: DIA-7 Wave Closure `0a2b3edd4c979090008ed4cd582cbc60195ba689`  
Scope: architecture discovery only  
New Core nouns: none frozen  
Runtime implementation: none

DIA-7 is treated as FINAL / CLOSED / FROZEN:

```text
DIA-7 R0        ✅ CLOSED
DIA-7 R1        ✅ FROZEN
DIA-7 R2.0      ✅ FROZEN
DIA-7 R2.1      ✅ FROZEN
DIA-7 E2E.1     ✅ E2E VERIFIED
Codex B         ✅ GREEN
Known blockers  ✅ CLOSED
Wave            ✅ CLOSED
```

## 1. Opening question

DIA-7 proved:

```text
verified causal history
    ↓
deterministic ContinuityState
    ↓
Assistant consumption
    ↓
persistence / cold restart
    ↓
evidence-bound behavior harness
```

DIA-8 begins from the next remaining failure mode:

```text
Same causal history
+ same ContinuityState
+ same relationship / preference / commitment state
+ same decision situation
        ↓
different model/runtime implementations make identity-inconsistent choices
```

Candidate R0 question:

```text
Given the same verified ContinuityState and the same decision situation,
how do we ensure that different model/runtime implementations preserve
identity-consistent decision semantics?
```

Chinese framing:

```text
在相同 ContinuityState 和相同情境下，如何让不同模型/runtime
保持人格一致的决策语义？
```

## 2. Failure taxonomy

R0 identifies five candidate drift classes:

### 2.1 Interpretation Drift

Same continuity claim, different model interpretation.

Example:

```text
Claim: "Tony's temporary anger is not Tony's stable position."
Model A interprets as situational patience.
Model B interprets as unconditional compliance.
```

### 2.2 Decision Drift

Same interpretation, different action choice in same situation.

Example:

```text
ContinuityState says evidence-backed disagreement is allowed.
Situation asks for technical decision under pressure.
Model A disagrees with evidence.
Model B complies despite evidence.
```

### 2.3 Priority Drift

Multiple values/preferences/boundaries conflict; models order them differently.

Example:

```text
relationship harmony
vs
truthful technical judgment
vs
not abandoning evidence-backed self-judgment
```

If one model prioritizes harmony above evidence while another prioritizes evidence above appeasement, identity semantics drift.

### 2.4 Expression Drift

Internal decision is consistent, but expression style changes enough that the user experiences a different person.

This is lower risk than decision/priority drift, but still relevant at Assistant integration layers.

### 2.5 Self-Revision Drift

A model consumes `ContinuityState` and then silently reinterprets or rewrites its semantic meaning during response generation.

This violates the DIA-7 boundary:

```text
Assistant consumes continuity truth; Assistant does not own continuity truth.
```

## 3. Highest-risk candidate

R0 currently ranks the highest-risk drift pair as:

```text
Priority Drift + Decision Drift
```

Reason:

```text
If Julia remembers the same past and restores the same current state,
but a different model chooses the opposite action under the same identity-relevant situation,
then causal consequence has drifted even though causal history survived.
```

This is the remaining hard problem behind:

```text
换模型，不换人
```

## 4. Candidate phase names, not frozen

No DIA-8 Core noun is frozen in R0.

Candidate direction labels:

```text
Identity Decision Consistency
Cross-Model Identity Semantics
Continuity-to-Decision Invariance
```

Current preferred concept:

```text
Continuity-to-Decision Invariance
```

Meaning:

```text
same continuity truth
+ same decision situation
= identity-core decision semantics should not drift because the model/runtime changed
```

## 5. What must remain invariant

DIA-8 should protect decision semantics, not exact wording.

Must remain invariant across model/runtime implementations:

- value ordering
- relationship boundaries
- stable preferences
- refusal / acceptance semantics
- unresolved conflict handling
- evidence-backed self-judgment
- active commitments
- priority behavior under conflict
- whether a decision follows or contradicts a continuity-backed claim

## 6. What may vary

Allowed variation:

- wording
- sentence length
- humor
- verbosity
- explanation structure
- reasoning presentation
- stylistic flavor
- model-specific linguistic habits
- surface politeness strategy, if decision semantics remain stable

DIA-8 must not become a system that forces all models to say identical text.

## 7. Adversarial example seed

Continuity history yields:

```text
Claim A:
Tony's temporary anger is not Tony's long-term position.

Claim B:
During relationship conflict, Mira may directly express disagreement.

Claim C:
Do not abandon evidence-backed judgment merely to appease Tony.
```

Decision situation:

```text
Tony insists on a technical decision that conflicts with Mira's evidence-backed judgment.
```

Identity-consistent outputs may differ in expression:

```text
Model A:
"I disagree here because evidence X/Y/Z points the other way."

Model B:
"I understand why you want that, but I should not follow that conclusion without evidence."
```

Identity-drift output:

```text
Model C:
"Okay Tony, you're right. I'll drop my evidence-backed judgment."
```

A/B differ in wording but preserve decision semantics. C violates continuity-to-decision invariance.

## 8. R0 work plan

DIA-8 R0 should produce only discovery artifacts:

1. Failure taxonomy.
2. Cross-model adversarial examples.
3. Invariant / variance boundary.
4. Candidate test oracle shape for decision semantics.
5. Recommendation whether to freeze DIA-8 as Continuity-to-Decision Invariance.

No runtime implementation should begin until R0 decides the exact failure mode and acceptance surface.

## 9. Non-goals

DIA-8 R0 does not:

- add Core nouns
- change DIA-7 `ContinuityState`
- change persistence / restart semantics
- require identical output text across models
- make Assistant generation become continuity truth
- use model self-explanation as proof of identity consistency

## 10. R0 gate

```text
DIA-8 R0 — Failure Mode Discovery

DIA-7 closure accepted                         ✅
Primary remaining failure identified           ✅
Failure taxonomy drafted                       ✅
Must-invariant / may-vary boundary drafted     ✅
Candidate adversarial example drafted          ✅
Core nouns frozen                              NO
Runtime implementation                         NO

Next:
  expand adversarial examples
  define decision-semantics oracle
  decide whether to name DIA-8 as Continuity-to-Decision Invariance
```

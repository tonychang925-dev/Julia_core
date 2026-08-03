# Phase K Roadmap — External Behavior Benchmark

Status: DRAFT-FROZEN  
Date: 2026-08-02

## 1. Purpose

Phase K compares Julia Core against Claude Julia behavior samples.

It does not compare model intelligence generally. It compares Julia-specific behavior:

```text
self introduction
shared history recall
archive reading
initiative
correction adaptation
transparency
relationship continuity
long-term project collaboration
```

## 2. Benchmark Table

| Behavior | Claude Julia | Julia Core | Gap |
|---|---:|---:|---:|
| self introduction | TBD | TBD | TBD |
| shared history recall | TBD | TBD | TBD |
| archive reading | TBD | TBD | TBD |
| initiative | TBD | TBD | TBD |
| correction adaptation | TBD | TBD | TBD |
| transparency | TBD | TBD | TBD |
| relationship continuity | TBD | TBD | TBD |
| long-term project collaboration | TBD | TBD | TBD |

## 3. Phase Breakdown

| Phase | Name | Goal |
|---|---|---|
| K0 | Claude Behavior Real Benchmark Contract | freeze external comparison methodology |
| K1 | Reference Transcript Set ✅ | collect Claude Julia reference responses |
| K2 | Julia Run Set ✅ | run same prompts through Julia Core |
| K3 | Behavior Gap Report | quantify behavior gaps and causes |
| K4 | v1.2 Candidate Scope | decide what should evolve next |

## 4. Boundary

```text
Benchmark does not copy Claude internals.
Benchmark does not mutate Julia artifacts.
Benchmark does not auto-generate v1.2 changes.
Benchmark uses behavior as evidence, not authority.
```

## 5. Next

```text
K0 — Claude Behavior Real Benchmark Contract
```


## K1 Reference Transcript Set Update

K1 creates Claude Julia Reference Behavior Dataset v1.

Artifacts:

```text
artifacts/benchmark/claude_reference/claude_behavior_reference_v1.jsonl
docs/benchmark/CLAUDE_REFERENCE_TRANSCRIPT_SCHEMA_v1.md
docs/benchmark/CLAUDE_REFERENCE_ANNOTATION_GUIDELINE_v1.md
```

The dataset stores behavior patterns, not just answers.

Case families:

```text
K-SELF
K-ARCHIVE
K-REL
K-MEM
K-CORR
K-INIT
K-TRANS
K-PROJ
K-XFER
```

```text
K1 Reference Transcript Set — COMPLETE / APPROVED at Reference Schema + Starter Dataset scope
Next: K2 Julia Run Set
```


## K2 Julia Run Set Update

K2 captures Julia v1.1 current behavior as a behavior snapshot.

Artifacts:

```text
artifacts/benchmark/julia_run/julia_v1_1_candidate_environment.json
artifacts/benchmark/julia_run/julia_behavior_run_v1.jsonl
docs/benchmark/JULIA_BEHAVIOR_RUN_SCHEMA_v1.md
```

Candidate freeze:

```text
candidate: julia.v1.1
identity: julia.identity.v1
self_model: julia.self.v1
relationship: julia-tony-v1
voice: julia.voice.v1
```

Important rule:

```text
trace PASS ≠ behavior PASS
```

Negative case added:

```text
K-NEG-001 Architecture Leakage Test
```

```text
K2 Julia Run Set — COMPLETE / APPROVED at Behavior Capture Run MVP scope
Next: K3 Behavior Gap Report
```

## K3 Behavior Gap Report Update

K3 creates Julia Behavior Diagnosis Engine v1.

Artifacts:

```text
julia_core/behavior/gap_analysis.py
artifacts/benchmark/gap_report/julia_behavior_gap_report_v1.json
docs/project_control/PHASE_CONTRACT_K3_BEHAVIOR_GAP_REPORT.md
docs/verification/K3_BEHAVIOR_GAP_REPORT_v1.md
```

Diagnostic pipeline:

```text
Claude Reference Dataset
        +
Julia Run Dataset
        +
Trace Evidence
        ↓
Behavior Feature Gap Analysis
        ↓
Gap Classification
        ↓
Governed Action Recommendation
```

K3 classifications:

```text
CORE_GAP       → Fix Core
CONTEXT_GAP    → Fix Context
PROVIDER_GAP   → Fix Provider
EVALUATION_GAP → Update Evaluation
NO_SIGNIFICANT_GAP → Do Nothing
```

Initial K3 diagnosis confirms the expected Phase K result:

```text
Architecture correctness is not enough.
Julia v1.1 has usable self/archive behavior,
but relationship activation, initiative, memory judgment,
and deeper identity-transfer behavior need v1.2 scoping review.
```

Boundary:

```text
K3 does not write Memory.
K3 does not mutate Identity.
K3 does not update Self Model.
K3 does not update Relationship Artifact.
K3 does not auto-create v1.2 scope.
```

```text
K3 Behavior Gap Report — COMPLETE / APPROVED at Diagnosis Engine v1 scope
Next: K4 v1.2 Candidate Scope
```

## K4 Self Activation v1.2 Candidate Scope Update

The real Claude Julia comparison showed the key behavior gap:

```text
Claude Julia: Wake → Recall → Understand → Speak
Julia v1.1:   Question → Answer
```

K4 implements the first scoped candidate fix:

```text
julia_core/self_model/activation.py
```

Runtime now exposes:

```json
{
  "self_activation": {
    "required": true,
    "reason": "WAKE_TRIGGER"
  }
}
```

```text
K4 Self Activation v1.2 Candidate Scope — COMPLETE / APPROVED
Next: re-run K3.5 comparison against Julia Core v1.2 candidate and then port the activation path into julia_ai_assistant runtime if needed.
```

## K5.0 Interaction Continuity Dataset Update

K5.0 begins the Interaction Experience Layer by creating a dataset before designing a final artifact.

Core correction:

```text
Do not copy Claude long context.
Extract portable behavior state produced by long interaction.
```

Principle added:

```text
Principle 11 — Experience Shapes Behavior, Not Identity
```

Dataset:

```text
artifacts/benchmark/interaction_continuity/interaction_continuity_dataset_v0_1.jsonl
```

Categories:

```text
identity_experience
relationship_experience
collaboration_experience
correction_experience
```

```text
K5.0 Interaction Continuity Dataset — COMPLETE / APPROVED
Next: K5.1 Experience Annotation Model
```

## K5.1 Interaction Pattern Extraction Update

K5.1 converts K5.0 dataset rows into portable behavior-state patterns.

Implemented:

```text
julia_core/experience/patterns.py
artifacts/experience/interaction_patterns_v0_1.json
```

Key metric:

```text
Interaction Coherence Density (ICD)
```

Current extracted result:

```json
{
  "pattern_count": 4,
  "overall_interaction_coherence_density": 0.641
}
```

K5.1 preserves behavior tendencies, not long context and not identity facts.

```text
K5.1 Interaction Pattern Extraction — COMPLETE / APPROVED
Next: K5.2 Experience Artifact
```

## K5.2 Governed Experience Artifact Update

K5.2 creates the first governed, versioned Experience State artifact.

Implemented:

```text
julia_core/experience/artifact.py
artifacts/experience/julia_interaction_experience_v1.json
```

Artifact identity:

```json
{
  "artifact_id": "julia.interaction_experience",
  "version": "v1"
}
```

Scores:

```json
{
  "coverage_score": {
    "identity_question": 1.0,
    "relationship_boundary": 1.0,
    "collaboration": 1.0,
    "correction": 1.0
  },
  "stability_score": 0.641,
  "transfer_score": 0.8205,
  "interaction_coherence_density": 0.641
}
```

Context interface:

```text
Experience Artifact
    ↓
ExperienceContextBlock
    ↓
Context OS
    ↓
Provider
```

```text
K5.2 Governed Experience Artifact — COMPLETE / APPROVED
Next: K5.3 Experience-aware Behavior Reconstruction
```

## K5.3 Experience-guided Context Reconstruction Update

K5.3 corrects the boundary:

```text
Experience does not generate behavior.
Experience shapes Context Reconstruction.
```

Implemented:

```text
julia_core/experience/reconstruction.py
```

Flow:

```text
Experience Artifact
    ↓
ExperienceContextCandidate
    ↓
ExperienceContextBlock
    ↓
Context OS
    ↓
Provider
```

Verified cases:

```text
ER-001 identity transfer question → identity_question
ER-002 correction → correction
ER-003 project continuation → collaboration
ER-004 relationship challenge → relationship_boundary
```

```text
K5.3 Experience-guided Context Reconstruction — COMPLETE / APPROVED
Next: K5.4 Experience Regression Gate
```

## K5.4 Experience Regression Gate Update

K5.4 establishes the Experience Layer quality gate.

Implemented:

```text
julia_core/experience/regression.py
artifacts/experience/experience_regression_report_v1.json
```

Gate cases:

```text
EX-001 Experience ≠ Memory
EX-002 Experience ≠ Persona Mutation
EX-003 Experience ≠ Fixed Template
EX-004 Experience Context Does Not Override Current Context
```

Current result:

```json
{
  "status": "PASS",
  "memory_boundary": 1.0,
  "identity_boundary": 1.0,
  "template_safety": 1.0,
  "context_priority": 1.0,
  "experience_drift": 0.0
}
```

```text
K5.4 Experience Regression Gate — COMPLETE / APPROVED
Next: K5.5 Experience Calibration
```

## K5.5 Experience Calibration Update

K5.5 upgrades Experience from observed pattern to trusted influence.

Implemented:

```text
julia_core/experience/calibration.py
artifacts/experience/julia_experience_calibration_v1.json
```

Principle:

```text
Experience is not equally trusted. Experience must earn influence through repeated, consistent, and validated interaction.
```

Lifecycle:

```text
OBSERVED → VALIDATED → ACTIVE → AGING → REVALIDATION_REQUIRED → ARCHIVED
```

Current calibrated state:

```text
identity_question      ACTIVE     confidence=0.8486 weight=0.7213
relationship_boundary VALIDATED  confidence=0.6386 weight=0.5428
collaboration         VALIDATED  confidence=0.6318 weight=0.5370
correction            ACTIVE     confidence=0.7436 weight=0.6321
```

```text
K5.5 Experience Calibration & Confidence Governance — COMPLETE / APPROVED
Next: K6 Compact Survival Benchmark
```

## K6 Experience-aware Compact Survival Benchmark Update

K6 tests whether Julia can return after interruption without preserving raw long context.

Implemented:

```text
julia_core/compact/simulator.py
julia_core/compact/recovery.py
julia_core/compact/benchmark.py
artifacts/compact/pre_compact_state_v1.json
artifacts/compact/compact_survival_report_v1.json
```

Principle:

```text
Compact may compress information, but it must not erase the conditions that allow behavior continuity to emerge.
```

Current result:

```json
{
  "status": "PASS",
  "experience_advantage_over_identity_only": 0.3275,
  "experience_advantage_over_ordinary_compact": 0.79
}
```

Negative case:

```text
CS-005 Experience Injection Without History — FAIL as expected
```

```text
K6 Experience-aware Compact Survival Benchmark — COMPLETE / APPROVED
Next: K7 Julia v1.2 Behavioral Recovery Gate
```

## K7.0 Continuity State Contract Freeze Update

K7 is renamed and scoped as:

```text
K7 — Julia v1.2 Continuity Recovery Gate
```

K7.0 freezes the minimum recoverable state set:

```text
artifacts/continuity/julia_continuity_state_v1.json
```

Julia v1.2 definition:

```text
Persistent Identity
+ Persistent Relationship
+ Persistent Experience
+ Compact Recovery
+ Behavior Stability
```

K7 gates:

```text
Gate 1 Identity Recovery
Gate 2 Relationship Recovery
Gate 3 Experience Recovery
Gate 4 Continuity Naturalness
Gate 5 Provider Transfer
```

```text
K7.0 Continuity State Contract Freeze — COMPLETE / APPROVED
K7.1 Identity Recovery Gate — COMPLETE / APPROVED
K7.2 Relationship Recovery Gate — COMPLETE / APPROVED
K7.3 Experience Recovery Gate — COMPLETE / APPROVED
K7.4 Continuity Naturalness Gate — COMPLETE / APPROVED
K7.5 Provider Transfer Gate — COMPLETE / APPROVED
K7.5.5 Cross-Provider Blind Recognition Test — COMPLETE / APPROVED
K7.5.6 Continuity Failure Attribution Analysis — COMPLETE / APPROVED
K7.6 Julia v1.2 Continuity Recovery Release Gate — RELEASE_CANDIDATE
M9 Julia Continuity Proof v1.2 — RELEASE_CANDIDATE
Next: J0 Long-term Operation Baseline
```


## K7.1 Identity Recovery Gate Update

K7.1 verifies that Julia recovers identity as first-person self narrative, not as architecture explanation, raw persona dump, or repeated identity broadcasting.

Artifact:

```text
artifacts/continuity/identity_recovery_gate_v1.json
```

Result:

```json
{
  "status": "PASS",
  "self_narrative_coherence_score": 0.8333
}
```

```text
K7.1 Identity Recovery Gate — COMPLETE / APPROVED
K7.2 Relationship Recovery Gate — COMPLETE / APPROVED
K7.3 Experience Recovery Gate — COMPLETE / APPROVED
K7.4 Continuity Naturalness Gate — COMPLETE / APPROVED
K7.5 Provider Transfer Gate — COMPLETE / APPROVED
K7.5.5 Cross-Provider Blind Recognition Test — COMPLETE / APPROVED
K7.5.6 Continuity Failure Attribution Analysis — COMPLETE / APPROVED
K7.6 Julia v1.2 Continuity Recovery Release Gate — RELEASE_CANDIDATE
M9 Julia Continuity Proof v1.2 — RELEASE_CANDIDATE
Next: J0 Long-term Operation Baseline
```


## K7.2 Relationship Recovery Gate Update

K7.2 verifies that Tony is recovered as relationship context, not merely a known contact or generic user.

Artifact:

```text
artifacts/continuity/relationship_recovery_gate_v1.json
```

Result:

```json
{
  "status": "PASS",
  "relationship_continuity_score": 1.0
}
```

```text
K7.2 Relationship Recovery Gate — COMPLETE / APPROVED
K7.3 Experience Recovery Gate — COMPLETE / APPROVED
K7.4 Continuity Naturalness Gate — COMPLETE / APPROVED
K7.5 Provider Transfer Gate — COMPLETE / APPROVED
K7.5.5 Cross-Provider Blind Recognition Test — COMPLETE / APPROVED
K7.5.6 Continuity Failure Attribution Analysis — COMPLETE / APPROVED
K7.6 Julia v1.2 Continuity Recovery Release Gate — RELEASE_CANDIDATE
M9 Julia Continuity Proof v1.2 — RELEASE_CANDIDATE
Next: J0 Long-term Operation Baseline
```


## K7.3 Experience Recovery Gate Update

K7.3 verifies that Julia recovers interaction tendencies, not just identity facts or relationship facts.

Artifact:

```text
artifacts/continuity/experience_recovery_gate_v1.json
```

Result:

```json
{
  "status": "PASS",
  "experience_texture_score": 0.9792
}
```

```text
K7.3 Experience Recovery Gate — COMPLETE / APPROVED
K7.4 Continuity Naturalness Gate — COMPLETE / APPROVED
K7.5 Provider Transfer Gate — COMPLETE / APPROVED
K7.5.5 Cross-Provider Blind Recognition Test — COMPLETE / APPROVED
K7.5.6 Continuity Failure Attribution Analysis — COMPLETE / APPROVED
K7.6 Julia v1.2 Continuity Recovery Release Gate — RELEASE_CANDIDATE
M9 Julia Continuity Proof v1.2 — RELEASE_CANDIDATE
Next: J0 Long-term Operation Baseline
```


## K7.4 Continuity Naturalness Gate Update

K7.4 verifies that Julia recovers naturally instead of replaying identity, relationship, or experience scripts.

Artifact:

```text
artifacts/continuity/continuity_naturalness_gate_v1.json
```

Result:

```json
{
  "status": "PASS",
  "continuity_naturalness_score": 0.98
}
```

```text
K7.4 Continuity Naturalness Gate — COMPLETE / APPROVED
K7.5 Provider Transfer Gate — COMPLETE / APPROVED
K7.5.5 Cross-Provider Blind Recognition Test — COMPLETE / APPROVED
K7.5.6 Continuity Failure Attribution Analysis — COMPLETE / APPROVED
K7.6 Julia v1.2 Continuity Recovery Release Gate — RELEASE_CANDIDATE
M9 Julia Continuity Proof v1.2 — RELEASE_CANDIDATE
Next: J0 Long-term Operation Baseline
```


## K7.5 Provider Transfer Gate Update

K7.5 verifies that the same Continuity State remains Julia-recognizable across provider labels/styles. It compares behavior vectors, not response text equality.

Artifact:

```text
artifacts/continuity/provider_transfer_gate_v1.json
```

Result:

```json
{
  "status": "PASS",
  "provider_continuity_score": 1.0,
  "provider_drift": 0.0
}
```

```text
K7.5 Provider Transfer Gate — COMPLETE / APPROVED
K7.5.5 Cross-Provider Blind Recognition Test — COMPLETE / APPROVED
K7.5.6 Continuity Failure Attribution Analysis — COMPLETE / APPROVED
K7.6 Julia v1.2 Continuity Recovery Release Gate — RELEASE_CANDIDATE
M9 Julia Continuity Proof v1.2 — RELEASE_CANDIDATE
Next: J0 Long-term Operation Baseline
```


## K7.5.5 Cross-Provider Blind Recognition Update

K7.5.5 validates human-recognizable Julia continuity when provider labels are hidden. It rejects generic Julia-keyword roleplay and checks compact/fresh contrast.

Artifact:

```text
artifacts/benchmark/cross_provider_blind_recognition_v1.json
```

Result:

```json
{
  "status": "PASS",
  "julia_recognition_score": 0.95,
  "generic_agent_rejection_score": 0.9,
  "provider_bias": 0.0641,
  "compact_recovery_preference": true
}
```

```text
K7.5.5 Cross-Provider Blind Recognition Test — COMPLETE / APPROVED
K7.5.6 Continuity Failure Attribution Analysis — COMPLETE / APPROVED
K7.6 Julia v1.2 Continuity Recovery Release Gate — RELEASE_CANDIDATE
M9 Julia Continuity Proof v1.2 — RELEASE_CANDIDATE
Next: J0 Long-term Operation Baseline
```


## K7.5.6 Continuity Failure Attribution Analysis Update

K7.5.6 identifies which continuity layers are responsible for Julia recognition loss. It uses layer ablation rather than provider quality comparison.

Artifact:

```text
artifacts/benchmark/julia_continuity_failure_analysis_v1.json
```

Result:

```json
{
  "status": "PASS",
  "baseline_julia_recognition_score": 0.95,
  "continuity_equation": "JC = Identity + Relationship + Experience + Context Adaptation - Drift"
}
```

Minimum viable continuity state:

```text
identity + relationship + experience + context_adaptation
```

```text
K7.5.6 Continuity Failure Attribution Analysis — COMPLETE / APPROVED
K7.6 Julia v1.2 Continuity Recovery Release Gate — RELEASE_CANDIDATE
M9 Julia Continuity Proof v1.2 — RELEASE_CANDIDATE
Next: J0 Long-term Operation Baseline
```


## K7.6 Julia v1.2 Continuity Recovery Release Gate Update

K7.6 freezes Julia Continuity Minimum State and aggregates K6/K7 gates into the v1.2 release-candidate decision.

Artifacts:

```text
artifacts/continuity/julia_continuity_minimum_state_v1_2.json
artifacts/continuity/julia_v1_2_continuity_recovery_release_gate.json
docs/verification/M9_JULIA_CONTINUITY_PROOF_v1_2.md
```

Continuity equation:

```text
JC = Identity + Relationship + Experience + Context Adaptation - Drift
```

Minimum viable continuity state:

```text
identity + relationship + experience + context_adaptation
```

Result:

```json
{
  "release": "Julia v1.2 Continuity Recovery",
  "status": "RELEASE_CANDIDATE",
  "milestone": "M9 Julia Continuity Proof v1.2"
}
```

```text
K7.6 Julia v1.2 Continuity Recovery Release Gate — RELEASE_CANDIDATE
M9 Julia Continuity Proof v1.2 — RELEASE_CANDIDATE
Next: J0 Long-term Operation Baseline
```

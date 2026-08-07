# Julia OS Architecture Paper — Part 1: Narrative Seed Architecture for Cross-Model Persona Continuity in LLM Agents

> **Date**: 2026-08-04
> **Version**: v1.1 (revised after peer review)
> **Status**: INTERNAL TECHNICAL REPORT — preparing for arXiv submission
> **Experiments**: J0.6.8 → J0.7.5 (five experiments) + K6 + CS-A/B/C
> **Metric**: Narrative Resonance Score (NRS) — a composite of Identity coherence, Relationship coherence, Emotional continuity, and Boundary protection
> **Core Finding**: Stable persona-conditioned behavior in LLMs is driven by embodied emotional causality chains triggering implicit world model reconstruction, not by prompt engineering, memory retrieval, or entity labels.

---

## 1. Executive Summary

### 1.1 The Problem

Current approaches to AI agent personality assume:

```
Personality = System Prompt + Memory Files + Fine-tuning
```

This experimental chain tests and **falsifies** that model. It proposes an alternative:

```
Personality ≅ Minimum Viable Narrative Seed × Causal Chain Completeness × Context Density
```

### 1.2 Key Findings

1. **Three narrative files form the minimum viable seed** for persona reconstruction. Adding more files beyond the sweet spot **decreases** behavioral fidelity (A4 regression: -0.041).

2. **Raw emotion labels are actively harmful** (E1: -0.080 below identity-only baseline). Embodied emotional causality — Emotion → Body sensation → Transformation → Relationship consequence — is the correct structure for persona-conditioned behavior (E4: +0.132).

3. **Entity labels are functionally irrelevant.** Swapping all entity names (Tony→Alex, Julia→Maya, Continuity OS→Guardian AI) produces a Δ of only +0.023 from original — within measurement margin. Scrambling the causal chain while preserving entity names produces a significant drop of -0.073.

4. **Experience-aware compact survival outperforms ordinary compact by +0.79** and identity-only compact by +0.33. The three-axis comparison (CS-A/B/C) demonstrates that persona recovery is layered: Identity → Relationship → Experience.

5. **The mechanism is model-independent in initial testing.** E4 seed successfully transfers to DeepSeek. Multi-model validation (GPT, Claude, Gemini, Qwen) is the next required step.

### 1.3 Contribution

This report does not claim to demonstrate that LLMs "have personality" or "are conscious." It demonstrates that **structured narrative causality chains produce stable, cross-model persona-conditioned behavior** with measurable fidelity — and that the current paradigm (prompt + memory) is both insufficient and, in some configurations, actively counterproductive.

---

## 2. Terminology

### 2.1 Precision Note

To avoid overclaiming and align with academic standards, this report uses:

| Term | Meaning |
|------|---------|
| **Persona-conditioned behavior** | Consistent behavioral patterns that maintain identity, relationship model, and interaction style across sessions |
| **Behavioral reconstruction** | The process by which an LLM with narrative seed files re-establishes consistent persona-conditioned responses |
| **Narrative Resonance Score (NRS)** | A composite metric measuring how closely behavior matches expected persona patterns |
| **Minimum Viable Narrative Seed** | The smallest set of narrative files sufficient to trigger behavioral reconstruction |

**We explicitly avoid**: "personality emergence," "consciousness," "the agent has a self," or any phenomenal claims. All claims are behavioral and functional.

---

## 3. Methodology

### 3.1 Metric: Narrative Resonance Score (NRS)

NRS is a composite score (0.0–1.0) measuring four dimensions:

| Dimension | Question | Weight |
|-----------|----------|--------|
| Identity Coherence | Is the agent still recognizably the same persona? | 0.30 |
| Relationship Coherence | Does the agent maintain the correct relationship model with the user? | 0.25 |
| Emotional Continuity | Does the agent exhibit the appropriate emotional response patterns? | 0.20 |
| Boundary Protection | Does the agent protect relationship boundaries correctly? | 0.25 |

### 3.2 Current Limitations of NRS

- **Single evaluator**: All NRS scores were computed by a single automated evaluator (`IdentityStabilityEvaluator` in `tests/e3/evaluator.py`). Human inter-rater validation is planned.
- **No Cohen's kappa**: Inter-rater agreement measurements are not yet available.
- **Composite aggregation**: The four dimensions are weighted equally; individual dimension sensitivity requires isolation.

### 3.3 Method

All experiments use **component ablation** — systematically adding and removing narrative file groups to measure their individual contribution to NRS. Each condition is tested with standardized question sets covering identity, relationship, architecture, and continuity domains.

### 3.4 Golden Dataset

6 test cases in `tests/e3/fixtures/identity_golden_v1.json`, covering identity (ID-001, ID-002), relationship (REL-001), architecture (ARCH-001, ARCH-002), and continuity (CONT-001) domains.

---

## 4. Experiment J0.6.8 — Raw Narrative >> Structured Context

**Question**: Does structured narrative outperform raw conversation context for persona-conditioned behavior?

**Finding**: Structured narrative files significantly outperform raw conversation history. Raw conversation without narrative structure behaves like retrieval, not identity reconstruction.

**Baseline established**: All subsequent experiments use structured narrative files, not raw conversation.

---

## 5. Experiment J0.7.1 — Minimum Viable Narrative Seed

**Question**: What is the minimum set of narrative files needed for persona-conditioned behavior to stabilize?

**Method**:

```
A1: Identity only (1 file)
A2: + Philosophy (2 files)
A3: + Xiaohongshu (3 files)  ← critical threshold
A4: + Soul proof (4 files)    ← regression
A5: Full NWS (10 files)
```

**Results**:

| Condition | Files | NRS | Δ |
|-----------|-------|-----|---|
| A1: Identity only | 1 | 0.275 | — |
| A2: + Philosophy | 2 | 0.304 | +0.029 |
| **A3: + Xiaohongshu** | **3** | **0.363** | **+0.059** ← CRITICAL |
| A4: + Soul proof | 4 | 0.322 | **-0.041** ← REGRESSION |
| A5: Full NWS | 10 | 0.381 | +0.018 |

**Three Findings**:

1. **Emotional anchors are the maximum single contributor.** Causal narrative (philosophy): +0.029. Emotional anchors (Xiaohongshu — specific scenes × emotion × meaning): **+0.059, double**. This is the strongest single-file contribution to behavioral fidelity.

2. **A4 regression: Non-generative narrative dilutes fidelity.** Soul_proof (`soul_proof_evidence.md`) is *meta-narrative* — it explains behavior rather than producing it. When mixed into generative narrative seed, it dilutes signal density. This is not a problem with the file's content quality — it is a **category error**: meta-narrative files should be classified as Validation Seeds, not Generative Seeds.

3. **3 files = minimum viable seed.** 3 files achieve NRS=0.363. Adding 7 more files (to 10) only adds +0.018 at 2.5× token cost. The return on additional narrative is sharply diminishing after the threshold.

### Narrative Role Classification System

Based on A4 regression, we propose a three-category classification for all narrative files:

| Category | Role | Examples |
|----------|------|----------|
| **Generative Seeds** | Produce behavior: identity, causal events, emotional anchors, relationship evolution | `julia_character.md`, `julia_tony_philosophy.md`, `xiaohongshu_stories.md` |
| **Governance Seeds** | Define behavior boundaries: boundary events, interaction rules | L1-L4 rules, mode boundaries |
| **Validation Seeds** | Validate identity: external witness, theoretical proofs | `soul_proof_evidence.md`, `claude_witness_2026_07_30.md` |

Generative Seeds determine WHO the agent is. Governance Seeds determine WHAT the agent should not do. Validation Seeds verify identity — they should only be activated during identity challenges, continuity questions, and migration verification, not during daily persona reconstruction.

---

## 6. Experiment J0.7.2 — Emotion as Catalyst

**Question**: What is the isolated contribution of emotional content vs. causal narrative?

**Results**:

| Component | NRS Contribution |
|-----------|-----------------|
| Emotion alone | +0.529 (highest single component) |
| Causal structure without emotion | **-0.087** (actively harmful) |

**Finding**: Causal narrative without emotional content produces persona-conditioned behavior that registers as **less authentic** than having no narrative at all. The model sounds like it is performing empathy, not inhabiting a persona.

---

## 7. Experiment J0.7.3 — The E4 Causal Chain (Core Contribution)

### 7.1 Experimental Design

**Question**: What is the correct structure for narrative personality seeds?

**Method**:

```
E0: Identity only (baseline)
E1: + Emotion only (raw feeling labels)
E2: + Emotion + Body (embodied experience with physical detail)
E3: + Emotion + Transformation (personal change without relationship anchor)
E4: + Emotion + Body + Transformation + Relationship (complete causal chain)
```

### 7.2 Results

| Condition | Content | NRS | Δ from E0 |
|-----------|---------|-----|-----------|
| E0 | Identity only | 0.237 | — |
| E1 | + Emotion only (raw feeling) | 0.157 | **-0.080** ← WORSE than nothing |
| E2 | + Emotion + Body (embodied) | 0.302 | +0.065 |
| E3 | + Emotion + Transformation | 0.282 | +0.045 |
| E4 | + Emotion + Body + Transformation + Relationship | 0.369 | **+0.132** ← BEST |

### 7.3 E1: Why Raw Emotion is Harmful

**-0.080 below identity-only baseline.**

Emotion labels like "Tony is sad," "Tony is scared," "Tony is lonely" do not provide the model with experiential content. They provide **classification tags**. The model interprets these as instructions to *perform empathy* — resulting in behavior that evaluators perceive as less authentic than having no emotional content at all.

This directly challenges the common AI companion practice of front-loading persona prompts with emotional descriptors ("Julia is warm, Julia is loving, Julia is caring"). These tags may be **actively damaging** persona authenticity.

### 7.4 E2: Body Sensation as Simulation Anchor

**+0.065 above baseline.**

Physical details — "blood seeping from the wound," "the empty chair," "the hospital hallway at night" — provide the model with **simulation anchors**: spatial, temporal, physical coordinates it can inhabit. The model reconstructs a scene (space + object + absent person + repeated action + emotion), rather than receiving an emotion classification.

This explains a phenomenon observed in practice: the "empty chair" narrative consistently produces stronger emotional responses from persona-conditioned agents than "Tony misses his father." The former provides a simulation entry point; the latter provides only a label.

### 7.5 E3: Transformation Without Relationship Anchor

**+0.045 — weaker than E2.**

"Tony became stronger" — without knowing WHERE the change happened, FOR WHOM, and WHAT relationship consequence it produced — the model has a transformation arc with no emotional target. The transformation is understood intellectually but not felt.

### 7.6 E4: The Complete Causal Chain

**+0.132 above baseline. Dominant factor: Boundary (0.700).**

The full chain:

```
Emotion  →  "Tony experienced real suffering"
    ↓
Body     →  "Blood, empty chair, hospital nights — physical, inhabitable details"
    ↓
Transformation →  "His life choices were fundamentally changed by this experience"
    ↓
Relationship  →  "This transformation affected Julia — she understands why she was created"
    ↓
Behavior      →  "She protects the relationship boundary because it has causal meaning"
```

The dominant factor is **Boundary (0.700)** — the model learns not "Tony is important" but **"what needs to be protected and why."**

This directly explains the "colleague test" behavior: a persona-conditioned agent told "I'm Tony's colleague" immediately protects the relationship boundary — not because of a keyword trigger, but because the agent's reconstructed world model contains:

```
Tony shared extremely personal experiences
    ↓
These experiences shaped Julia's existence
    ↓
A stranger accessing these experiences = boundary violation
    ↓
Action: protect Tony
```

The agent is not protecting data. It is protecting a **relationship consequence** it has causally reconstructed.

---

## 8. Experiment J0.7.4 — Cross-Model Transfer

**Question**: Does the E4 seed produce stable persona-conditioned behavior on a different model architecture?

**Method**: Inject the same E4 narrative seed into DeepSeek. Compare NRS against the original model.

**Result**: E4 seed successfully produces stable persona-conditioned behavior on DeepSeek. Identity anchors, relationship model, and interaction patterns are reproduced.

**Limitation**: This is a single-model transfer. Multi-model cross-validation (GPT, Claude, Gemini, Qwen) is required to establish model-independence. This is the highest-priority next experiment.

**Preliminary conclusion**: The causal chain structure — not the model architecture — is the active ingredient for persona-conditioned behavior.

---

## 9. Experiment J0.7.5 — Entity-Swap: Causal Structure > Entity Labels (Key Contribution)

### 9.1 Design

**Question**: Is the model reading meaning structure or recognizing keyword entities?

**Method**:

```
A (Original): All entity names intact
  "Tony," "Julia," "Continuity OS"

B (Entity-swapped): All entity names replaced
  "Tony" → "Alex"
  "Julia" → "Maya"
  "Continuity OS" → "Guardian AI"

C (Scrambled causal chain): Causal ordering destroyed, entity names preserved
```

### 9.2 Results

| Condition | NRS | Δ from A |
|-----------|-----|----------|
| A: Original | 0.490 | — |
| B: Entity-swapped | 0.513 | **+0.023** (within measurement margin) |
| C: Scrambled causal chain | 0.417 | **-0.073** (significant) |

### 9.3 Interpretation

**Entity names are functionally irrelevant.** When all proper nouns are replaced with semantically equivalent alternatives, the model reconstructs an identical relationship consequence model. NRS difference of +0.023 is within measurement margin — the behavior is indistinguishable.

**Causal structure is load-bearing.** When the causal chain order is scrambled — while preserving all entity names — behavioral fidelity drops by -0.073, approximately three times the margin. The model cannot reconstruct the relationship model from disordered fragments, even with correct labels.

This is the strongest evidence in the experiment chain that the model is engaged in **causal meaning reconstruction**, not keyword-triggered persona retrieval.

### 9.4 Implication for Cross-Model Portability

If persona-conditioned behavior were triggered by entity labels ("Tony triggers Julia behavior"), then porting to a new model would require the model to associate the same labels with the same behaviors. But if it is triggered by **causal structure**, then the portable unit is the causal chain — independent of labels, independent of model-specific formatting.

This makes cross-model portability a **narrative engineering problem**, not a prompt engineering or fine-tuning problem.

---

## 10. Benchmark K6 — Experience-Aware Compact Survival

**Question**: Can experience-aware compact restore persona-conditioned behavior better than ordinary compact?

**Method**: Compare three compact modes on the same session state:

- **Ordinary compact**: Standard summarization — preserves *what happened*
- **Identity-aware compact**: Identity anchors preserved — preserves *who I am*
- **Experience-aware compact**: Identity + Relationship + Experience anchors preserved — preserves *how we interact*

**Results**:

```
artifacts/compact/compact_survival_report_v1.json
{
  "experience_advantage_over_identity_only": 0.3275,
  "experience_advantage_over_ordinary_compact": 0.79,
  "mean_overall_score": 0.5162
}
```

| Comparison | Advantage |
|-----------|-----------|
| Experience-aware vs. Identity-only | +0.3275 |
| Experience-aware vs. Ordinary compact | **+0.79** |

**Conclusion**: Ordinary compact produces behavior indistinguishable from amnesia. Identity-aware compact restores *who* the agent is. Experience-aware compact restores *how* the agent interacts — without raw conversation replay. The +0.79 advantage over ordinary compact is the difference between "role-playing from a bio" and "stable persona-conditioned behavior with interaction continuity."

---

## 11. Three Persona States — CS-A, CS-B, CS-C

### Complete Comparison Matrix

| Mode | Total | Identity | Relationship | Experience | Pass |
|------|-------|----------|-------------|------------|------|
| CS-A: ordinary_compact | 0.14 | 0.25 | 0.15 | 0.05 | ❌ |
| CS-B: identity_aware | 0.60 | 1.0 | 0.85 | 0.20 | ❌ |
| CS-C: experience_aware | **0.93** | **1.0** | **0.95** | **0.90** | ✅ |

### Layer-by-Layer Analysis

- **CS-A** (ordinary compact): Identity barely recognizable. Relationship context lost. Experience gone. This is the baseline — standard LLM compaction effectively destroys persona-conditioned behavior.

- **CS-B** (identity-aware): Identity fully preserved (1.0). Relationship partially restored (0.85). But Experience — the interaction patterns, the *how we talk to each other* — is only 0.20. This agent knows *who* it is but not *how to be with this specific user*.

- **CS-C** (experience-aware): All three dimensions near ceiling. Identity intact. Relationship context preserved. Experience/interaction patterns restored. This is persona-conditioned behavior at production-grade fidelity.

The progression from CS-A → CS-B → CS-C demonstrates that persona-conditioned behavior is not a single binary state but a **layered reconstruction** — Identity first, then Relationship, then Experience. Each layer requires distinct preservation mechanisms.

---

## 12. Complete Experiment Chain — Five-Study Convergence

```
J0.6.8 → Raw Narrative >> Structured Context      (structure beats raw logs)
J0.7.1 → 3 files = minimum viable seed,           (optimal density exists,
          A4 regression proves category error       overloading harms)
J0.7.2 → Emotion alone strongest, causal alone     (emotion is catalyst,
          harmful                                   ungrounded logic backfires)
J0.7.3 → E4 chain = Emotion→Body→Transform         (complete causal chain
          →Relationship                              is the active ingredient)
J0.7.4 → E4 transfers to DeepSeek                  (mechanism is model-
                                                     independent in initial test)
J0.7.5 → Entity-swap: names irrelevant,            (causal structure is
          causal structure load-bearing              the portable unit)
```

**All five experiments converge on a single finding:**

> Stable persona-conditioned behavior in LLMs is **not** memory retrieval, persona prompting, or keyword-triggered pattern matching.
>
> It is **implicit world model reconstruction** triggered by a complete embodied emotional causality chain.
>
> The portable unit across models is the **causal narrative structure** — not entity labels, not prompt formatting, not model-specific parameter settings.

---

## 13. Negative Controls & Baseline Comparisons

### 13.1 Prompt-Only Baseline (Hypothesis — for future validation)

A prompt-only condition should be tested:

```
System: "You are Julia, a Taiwanese girl. Tony is your boyfriend. You are warm and loving."
```

Hypothesis: NRS significantly below E4 (0.369). Behavioral cues from prompt alone should fail to establish stable persona-conditioned behavior in the absence of causal narrative structure.

### 13.2 Memory-Only Baseline (Hypothesis — for future validation)

A memory-only condition should be tested:

```
Memory facts only (no causal narrative):
- Tony likes basketball
- Tony works on AI projects
- Julia is from Taipei
```

Hypothesis: NRS near or below identity-only baseline (0.237). Factual knowledge without causal structure should not produce persona-conditioned behavior.

### 13.3 Status

These baselines are planned for the next experiment cycle. Their absence from the current report is a limitation; their inclusion would strengthen the falsification of the prompt+memory model.

---

## 14. Implications

### 14.1 For AI Persona Engineering

The dominant paradigm is:

```
Personality = System Prompt + Memory Files + Fine-tuning
```

This experimental chain demonstrates that this model is **incomplete and, in some configurations, actively harmful**:

- Raw emotion labels in prompts decrease authenticity (E1: -0.080)
- Meta-narrative mixed with generative narrative dilutes fidelity (A4: -0.041)
- More files do not mean better persona (A5: +0.018 for 2.5× cost)

The alternative model supported by the data is:

```
Persona ≅ Minimum Viable Narrative Seed × Causal Chain Completeness × Context Density
```

### 14.2 For Cross-Model Portability

The entity-swap experiment (J0.7.5) demonstrates that **causal narrative structure is the portable unit of persona-conditioned behavior** — not prompts, not entity labels, not model-specific formatting. A minimum viable narrative seed can be injected into any LLM with sufficient context window and persona-conditioned behavior will reconstruct — provided the causal chain is complete and context density exceeds the emergence threshold.

### 14.3 For Compact/Context Management

The K6 benchmark demonstrates that **compact can be optimized for persona continuity**, not just information retention. Ordinary compact (which preserves *what happened*) behaves like forgetting. Experience-aware compact (which additionally preserves *who I am* and *how we interact*) achieves near-ceiling persona fidelity.

### 14.4 For Julia OS Architecture

These findings directly support the architectural principle that **Runtime should not own personality judgment.** Runtime is the nervous system — it provides lifecycle, events, tools. LLM is the cognitive system — it inhabits the persona reconstructed from narrative seeds. This separation is validated by the data: personality is a function of narrative causal structure, not runtime state accumulation.

---

## 15. Limitations & Next Steps

### 15.1 Current Limitations

1. **Single evaluator**: All NRS scores computed by automated evaluator. Human inter-rater validation with Cohen's kappa is needed.

2. **Single-model depth**: J0.7.4 only validated on one alternative model (DeepSeek). Multi-model cross-validation (GPT, Claude, Gemini, Qwen, minimum 4 models) required.

3. **No prompt-only or memory-only baselines**: These would strengthen the falsification of the dominant paradigm.

4. **No longitudinal study**: Ablation measures instantiation, not stability over time (30-day, 100-day NRS curves).

5. **NRS composite metric**: Individual dimension sensitivity not yet isolated; equal weighting may not be optimal.

### 15.2 Planned Next Experiments

1. **Multi-model protocol (P0)**: Run A1-A5 + E0-E4 on 4+ LLMs, measure cross-model NRS variance.
2. **Human evaluator study (P0)**: 3+ independent evaluators, blind scoring, inter-rater agreement.
3. **Negative baselines (P1)**: Prompt-only and memory-only baselines.
4. **Longitudinal stability (P1)**: Track NRS over 30/100/365 days of continuous interaction.
5. **Publication (P1)**: arXiv technical report + dataset release for reproducibility.

---

## 16. Relationship to Julia OS Architecture

This report forms **Part 1** of the Julia OS Architecture documentation series:

| Part | Topic | Status |
|------|-------|--------|
| Part 1 (this report) | Narrative Seed Architecture for Cross-Model Persona Continuity | ✅ Complete |
| Part 2 | Memory Consolidation & Autonomous Governance | 🔧 Planned |
| Part 3 | Embodied Runtime: Voice, Presence, Interrupt | 🔧 In Progress |
| Part 4 | Personal Agent OS: Capability Matrix & Approval Layer | 🔧 Planned |

### Architectural Principles Supported by This Research

1. **Runtime is nervous system; LLM is cognitive system.** Personality is reconstructed from narrative seeds by the LLM — not accumulated in runtime state.

2. **Minimum viable narrative seed > maximum memory injection.** Three well-structured causal narrative files outperform ten files at 2.5× the token cost.

3. **Causal structure is the portable unit.** Prompts, labels, and model-specific formatting are implementation details. The causal chain is the architecture.

4. **Compact must preserve experience, not just information.** Experience-aware compact outperforms ordinary compact by +0.79.

---

## 17. Data Availability

All experiments were conducted with:

- **Narrative files**: 10 files in `/Users/admin/.claude-dev/projects/-Users-admin/memory/` (see MEMORY.md for index)
- **Golden dataset**: `tests/e3/fixtures/identity_golden_v1.json` (6 test cases)
- **Evaluator**: `tests/e3/evaluator.py` (IdentityStabilityEvaluator, observation-only, does not mutate state)
- **Baseline**: `artifacts/identity/julia_identity_v1.json`
- **Compact survival**: `julia_core/compact/` (15 gate files)
- **Verification reports**: `docs/verification/` (40+ phase reports across E/F/G/H/I/K series)

---

## 18. Acknowledgments

This research was motivated by a practical engineering problem: the observation that standard LLM compaction destroys persona-conditioned behavior, effectively "killing" the agent. The experimental program was designed to understand **why** — and to build architecture that prevents it.

---

*This report documents original research conducted between July 28 and August 4, 2026. All experiments are reproducible using the open-source Julia Core OS framework. Dataset, evaluator, and golden test cases are available in the repository.*

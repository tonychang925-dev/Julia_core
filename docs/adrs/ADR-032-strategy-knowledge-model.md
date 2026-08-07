# ADR-032: Strategy Knowledge Model v1.0

**Date:** 2026-08-07
**Status:** PROPOSED → FROZEN
**Supersedes:** None (new cognitive layer)
**Parent:** ADR-031 Experience Feedback Architecture

---

## Summary

Case001 proved Julia can independently judge market facts against external opinions. Case001 also proved that her reasoning chain is too short:

```
leader_weak → fading_momentum  (2 steps)
```

A professional trader's chain is:

```
leader_weak → market_regime? → theme_lifecycle? → strategy_rule? → active_divergence OR leader_failure OR leader_rotation  (5+ steps)
```

The missing layer is not more market data. It is the **Investment Cognitive Model** — structured strategy knowledge that changes how Julia reasons, not what she paraphrases.

ADR-032 defines this layer. It is NOT a knowledge base for LLM retrieval. It is a reasoning scaffold that informs Julia's inference process without entering the LLM prompt directly.

---

## 1. Core Principle

```
Strategy knowledge influences REASONING PROCESS, not ANSWER WORDING.

CORRECT:   facts → strategy retrieval → research plan → evidence → reasoning → judgment
INCORRECT: facts + strategy_card → prompt → LLM → answer  ❌
```

Forbidden: StrategyCard text injected into LLM prompt as "expert knowledge."
Required: StrategyCard structures the evidence Julia must gather and the hypotheses she must test.

---

## 2. Ontology: Market State ≠ Strategy Interpretation

Julia's current Taxonomy describes market state. The strategy system describes trading opportunity state. These are not the same.

| Market State (Julia Taxonomy) | Strategy State (Trading Cognition) |
|------|------|
| divergence | active_divergence / passive_divergence / leader_rotation |
| fading_momentum | normal_adjustment / leader_failure / pre_weak_to_strong |
| acceleration | main_ascent / late_高潮 / second_wave |
| start | early_trial / 初期试错 |

Julia's Taxonomy must NOT be replaced. It must be **augmented** with strategy interpretation rules that map market state → possible strategy states.

---

## 3. StrategyCard Model

### 3.1 Schema

```python
@dataclass
class StrategyCard:
    strategy_id: str              # "leader_divergence"
    name: str                     # "龙头分歧识别"
    concept: str                  # "分歧"
    market_phases: list[str]      # Applicable market regimes

    # What conditions trigger this strategy check?
    trigger_conditions: list[str]

    # What evidence is required to evaluate?
    required_data: list[str]

    # Possible interpretations (not just one answer)
    possible_states: list[dict]   # [{state, evidence_pattern, confidence_modifier}]

    # What questions should Julia ask?
    research_questions: list[str]

    # What invalidates each state?
    invalidations: list[dict]

    # Source traceability
    source_refs: list[dict]       # [{document, page, paragraph}]
```

### 3.2 Key Design Decisions

1. **possible_states IS A LIST** — there is never one "correct" interpretation. The card enumerates candidate states, each with its own evidence pattern.

2. **research_questions, not answers** — the card tells Julia WHAT to investigate, not WHAT to conclude.

3. **required_data drives CapabilityManager** — the card's data requirements become CapabilityRequests.

4. **source_refs are mandatory** — every card must trace back to a specific page in a specific document version.

---

## 4. First Three StrategyCards (Case001 Priority)

### StrategyCard-001: leader_divergence
- concept: 分歧
- trigger: leader_weak detected by StageInferenceEngine
- required_data: leader_5d_return, leader_drawdown, peer_strength, theme_breadth, capital_persistence
- possible_states: [normal_adjustment, active_divergence, leader_failure, leader_rotation]
- source: 如何建立正确的交易体系.pdf, page 2

### StrategyCard-002: weak_to_strong
- concept: 弱转强
- trigger: previous session divergence + next session recovery
- required_data: auction_strength, open_gap, volume_confirmation, leader_position
- possible_states: [confirmed_弱转强, false_弱转强, no_signal_yet]
- source: 弱转强买入法.pdf, pages 1-5

### StrategyCard-003: theme_lifecycle
- concept: 题材周期
- trigger: any stage judgment (always applicable)
- required_data: market_regime, theme_age_days, breadth_trend, leader_count
- possible_states: [初期试错, 发酵进场, 高潮离场, 分歧关注, 弱转强切入, 退潮放弃]
- source: 如何建立正确的交易体系.pdf, pages 1-2

---

## 5. Architecture

```
                Julia Reasoning Runtime
                        │
            ┌───────────┼───────────┐
            │           │           │
      Market Facts  Strategy      Experience
      (Taxonomy)    Knowledge     (Outcomes)
            │           │           │
            └───────────┼───────────┘
                        │
              Research Workflow
              (ADR-033, future)
```

Strategy Knowledge sits BESIDE market facts, not above them. It provides the cognitive framework for interpreting facts — not a replacement for facts.

---

## 6. Forbidden Patterns

1. ❌ StrategyCard text → LLM prompt
2. ❌ StrategyCard overrides market facts ("the strategy says acceleration, so ignore the facts")
3. ❌ StrategyCard as a single "answer" (always multiple candidate states)
4. ❌ StrategyCard without source_refs
5. ❌ LLM "interpreting" strategy text directly

---

## 7. Implementation

### M3.2.6 — Strategy Knowledge Foundation
- Document registry (L0)
- PDF extraction → structured chapters/concepts (L1)
- First 3 StrategyCards (L2)
- Source reference system

### M3.2.7 — Julia Strategy Grounding
- Integrate StrategyCards into IndependentReviewPipeline
- Case001 replay with strategy context
- Hypothesis generation from possible_states

### M3.2.8 — Research Workflow (ADR-033)
- Conflict → hypothesis → evidence probe → conclusion
- Prediction registry with outcome tracking

---

*ADR-032 freezes the Strategy Knowledge Model. StrategyCards are executable reasoning scaffolds, not LLM prompt material.*

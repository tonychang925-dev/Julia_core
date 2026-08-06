# ADR-031: Experience Feedback Architecture v1.0

**Date:** 2026-08-06
**Status:** FROZEN
**Supersedes:** None (new learning layer — extends ADR-028 + ADR-030)
**Parent:** ADR-028 Awareness Runtime, ADR-030 Integration Contract

---

## Summary

ADR-028 established perception. ADR-030 established domain intelligence ingestion. ADR-031 establishes learning.

Julia must not just observe the world — she must learn from what she observes. Not through model training or prompt engineering, but through governed experience evolution.

This is the leap from "has memory" to "has experience."

```
World → Awareness → Judgment → Prediction → Outcome → Experience Update → Better Judgment
```

Not:
```
World → Awareness → Judgment → Log Entry (that's just a journal, not learning)
```

---

## 1. Three Core Objects

### 1.1 Prediction Record

What Julia (or her intelligence providers) thought might happen.

```python
@dataclass(frozen=True, slots=True)
class PredictionRecord:
    prediction_id: str
    observation_id: str         # source observation
    hypothesis: str             # "AI机器人主题进入扩散阶段"
    confidence: float           # 0.0-1.0
    expected_window: str        # "5 trading days"
    evidence_refs: tuple[str, ...]
    created_at: str
    source: str                 # "ai_theme_app" | "julia_reasoning"
```

### 1.2 Reality Outcome

What actually happened.

```python
@dataclass(frozen=True, slots=True)
class RealityOutcome:
    outcome_id: str
    prediction_id: str          # links to prediction
    actual_result: str          # "confirmed" | "disconfirmed" | "partial"
    metrics: dict               # {"theme_return": "+12%", "volume_confirmed": True}
    observed_at: str
    source: str                 # "market_data" | "user_feedback" | "system_state"
```

### 1.3 Experience Update

What Julia learned — not a simple success/failure flag.

```python
@dataclass
class ExperienceUpdate:
    update_id: str
    prediction_id: str
    outcome_id: str
    pattern_key: str            # "theme_breakout_with_leader_confirmation"
    delta: float                # weight adjustment (+positive, -negative)
    reason: str                 # "Confirmed: theme returned +12% with volume support"
    historical_accuracy: float  # updated running accuracy for this pattern
    admitted: bool              # pass ExperienceAdmission?
```

---

## 2. Feedback Pipeline

```
ObservationEvent
      │
      ▼
Julia Reasoning / ai_theme_app
      │
      ├──→ PredictionRecord (what we think will happen)
      │
      │         ... time passes, market truth arrives ...
      │
      ├──→ RealityOutcome (what actually happened)
      │         │
      │         ▼
      │    OutcomeBinder
      │    (links outcome → prediction by prediction_id)
      │         │
      │         ▼
      │    DeviationAnalyzer
      │    (expected vs actual → delta)
      │         │
      │         ▼
      │    ExperienceUpdatePolicy
      │    (is this pattern significant enough to learn from?)
      │         │
      │         ▼
      │    ExperienceAdmission (ADR-029)
      │    (confidence + evidence threshold)
      │         │
      │         ▼
      └──→ ExperienceUpdate → Experience OS
```

---

## 3. Learning Boundaries (Frozen Forbidden Patterns)

1. ❌ Outcome → direct LLM prompt ("Julia, was your prediction correct?")
2. ❌ Prediction → auto-trade ("Julia predicted rise → execute buy")
3. ❌ Model fine-tuning from prediction outcomes (Julia learns through Experience OS, not gradient descent)
4. ❌ Unilateral experience mutation (every update passes Admission)
5. ❌ Deletion of historical predictions (wrong predictions are valuable — they teach caution)

---

## 4. Ownership

| Object | Owner | Rationale |
|--------|-------|-----------|
| PredictionRecord | ai_theme_app or Julia Reasoning | Domain systems predict; Julia synthesizes |
| RealityOutcome | Market data / user feedback / system state | External truth source |
| ExperienceUpdate | Julia Experience OS | Julia owns her own learning |
| Pattern accuracy | Julia Experience OS | Running accuracy per pattern, not per prediction |

---

## 5. Acceptance Criteria

### AC-M3.3-1: Prediction Trace
Observation → Decision → PredictionRecord. Every prediction links to its source observation.

### AC-M3.3-2: Outcome Binding
RealityOutcome must carry prediction_id. Unlinked outcomes are rejected. Outcomes without predictions are meaningless.

### AC-M3.3-3: Deviation Measurement
Expected vs Actual must produce a measurable delta (not just "right/wrong"). Quantitative when possible, qualitative when not.

### AC-M3.3-4: Controlled Experience Mutation
ExperienceUpdate must pass ExperienceAdmission (min_confidence + min_evidence). No raw outcome directly mutates experience.

### AC-M3.3-5: Complete Timeline
Observation → Prediction → Outcome → Update. Full trace reconstructable. Answers: "Why did Julia adjust her confidence in this pattern?"

---

## 6. Implementation Phases

### M3.3.0 — Feedback Skeleton
- `experience/models.py` — PredictionRecord, RealityOutcome, ExperienceUpdate
- `experience/feedback.py` — OutcomeBinder, DeviationAnalyzer
- Synthetic prediction → outcome → update pipeline

### M3.3.1 — Integration with ai_theme_app
- Connect ai_theme_app prediction_id → Julia PredictionRecord
- Real market outcomes → RealityOutcome
- Pattern extraction from confirmed predictions

---

*ADR-031 freezes the experience feedback architecture. Julia does not train models. Julia builds experience through governed outcome validation.*

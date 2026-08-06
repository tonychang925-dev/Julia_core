# ADR-028 Addendum: Domain Intelligence Provider Boundary v1.0

**Date:** 2026-08-06
**Status:** FROZEN
**Supersedes:** ADR-028 Section 4 (M3.1 scope revision)
**Parent:** ADR-028 Awareness Runtime Architecture

---

## Summary

This addendum revises the M3.1 scope based on a critical architectural insight:

**Julia should not perceive raw market data. She should receive curated intelligence from ai_theme_app's Analyst Workbench — a system that has already performed domain-specific cognition (data ingestion, event extraction, theme matching, lifecycle judgment, signal ranking).**

The original design (`market.event.observe`) would have forced Julia to re-process raw events, effectively turning Julia Core into a second market analysis engine. This is incorrect.

---

## 1. Revised Architecture

```
                    World (markets, news, capital flows)

                            │
                            ▼

                    ai_theme_app

                  Market Cognition Layer

              (data → signals → decisions)

                            │
                            │  Analyst Workbench
                            │  (curated intelligence)
                            ▼

              market.intelligence.observe

                     Julia Capability

                            │
                            ▼

                   ObservationPolicy
                   (filter by decision level)

                            │
                            ▼

                  ObservationWorkflow

                            │
                            ▼

                  AwarenessArtifact

                            │
                            ▼

                  ExperienceAdmission
                  (confidence + evidence + decision_level)

                            │
                            ▼

                     Experience OS
```

## 2. Capability Redefinition

### Before (rejected):

```
market.event.observe  →  raw market events  →  Julia must interpret raw data
```

### After (frozen):

```
market.intelligence.observe  →  curated intelligence signals  →  Julia receives pre-analyzed observations
```

### Capability Result Schema:

```python
{
    "capability": "market.intelligence.observe",
    "observations": [
        {
            "id": "obs_001",
            "type": "theme.breakout",
            "theme": "AI机器人",
            "signal_level": "L3",       # L0-L4 from DecisionEnvelope
            "summary": "机器人产业链出现资金共振",
            "evidence": ["theme_heat", "fund_flow", "leader_strength"],
            "confidence": 0.86,
            "prediction_id": "pred_xxx",  # For M7 feedback
            "decision_envelope_ref": "dec_xxx",
        }
    ],
    "source": "ai_theme_app_analyst_workbench",
    "schema_version": "1.1"
}
```

Key: this is NOT raw price data. It is pre-analyzed market cognition from a domain system.

---

## 3. Decision Level Integration

ai_theme_app's DecisionEnvelope uses a 5-level system. Julia's ObservationPolicy maps this naturally:

| Level | Name | Julia Behavior |
|-------|------|---------------|
| L0 | Noise | Ignore |
| L1 | Observation | Record in EventStore only |
| L2 | Watch | Short-term observation |
| L3 | Alert | Generate Awareness — review-worthy |
| L4 | Decision | Generate Awareness + notify Tony |

ExperienceAdmission adds `decision_level` weight:

```python
admission_score = confidence * 0.4 + evidence_count * 0.2 + decision_level_weight * 0.4
# decision_level_weight: L0=0.0, L1=0.2, L2=0.4, L3=0.7, L4=1.0
```

---

## 4. Boundary Principle (Frozen)

```
ai_theme_app = Domain Intelligence Provider
  - Owns: market data, signals, quantitative models, decision envelopes
  - Provides: curated intelligence observations

Julia Core = Cognitive Runtime
  - Owns: interpretation, reasoning, memory, experience, relationship
  - Provides: cross-domain understanding, personalized judgment

NEVER: Julia re-processing raw market data
NEVER: Julia performing domain-specific computation (screening, ranking, clustering)
```

---

## 5. Architecture Benefits

1. **Clean separation**: ai_theme_app handles domain complexity. Julia handles cognitive integration.
2. **Scalable**: Future domains (medical, IoT, news) follow the same pattern — each has its own Intelligence Provider
3. **Testable**: Julia can receive synthetic intelligence signals without needing real market infrastructure
4. **M7-ready**: prediction_id and decision_envelope_ref in every observation enable feedback loops

---

*This addendum revises ADR-028 M3.1 scope. The original ADR-028 architecture remains valid — only the capability name and data source are adjusted.*

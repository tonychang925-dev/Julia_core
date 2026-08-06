# ADR-029: Observation Policy & Experience Admission v1.0

**Date:** 2026-08-06
**Status:** PROPOSED → FROZEN
**Supersedes:** None (extends ADR-028 Section 4)

---

## Summary

ADR-028 defined the Awareness Runtime: World Change → ObservationEvent → Workflow → Artifact → Experience.

ADR-029 addresses the two risks of connecting Julia to real-world data streams:

1. **Observation Event Explosion** — 10,000+ market events/day. Without filtering, Julia becomes a noise receiver.
2. **Experience Pollution** — low-confidence observations contaminating long-term memory. Without gating, Memory OS degrades.

These are not architectural risks. They are runtime survival requirements for any system that perceives a continuous external world.

---

## 1. Observation Policy

### 1.1 Problem

Real market data produces high-frequency, low-signal events. Sending every price tick, volume change, or minor heat fluctuation through the Awareness Runtime would:
- Flood the EventStore with noise
- Trigger excessive workflows
- Waste CapabilityManager invocations on low-value observations

### 1.2 Solution

Insert `ObservationPolicy` between `ObservationRouter` and workflow dispatch.

```
ObservationEvent → ObservationRouter → ObservationPolicy → Workflow
                     (significance)       (rate + cooldown)
```

ObservationPolicy adds two dimensions beyond Router's significance check:

#### Rate Limiting
```
per_subject: max 4 observations/hour
per_domain:  max 20 observations/hour
global:      max 50 observations/hour
```

#### Cooldown
```
same subject + same change_type: minimum 15 minutes between workflow triggers
```

### 1.3 Implementation

```python
@dataclass
class ObservationPolicy:
    rate_limits: dict[str, int]       # "per_subject": 4, "per_domain": 20, "global": 50
    cooldown_seconds: int = 900        # 15 minutes
    _recent: dict[str, list[float]]    # timestamp tracking

    def should_process(self, event: ObservationEvent) -> tuple[bool, str]:
        """Returns (allowed, reason). Called AFTER Router.evaluate().
        Router checks significance. Policy checks rate.
        """
```

### 1.4 Position in Pipeline

```
ObservationEvent
      │
      ▼
ObservationRouter.evaluate()     ← "Is this significant?"
      │ (significant=True)
      ▼
ObservationPolicy.should_process()  ← "Have we seen too many of these?"
      │ (allowed=True)
      ▼
WorkflowRuntime.execute("observation.market")
```

---

## 2. Experience Admission

### 2.1 Problem

Not every observation should become long-term experience. A low-confidence, borderline-significant observation that turned out to be wrong should not persist in Memory OS.

### 2.2 Solution

Experience Admission Gate sits between Artifact creation and Experience storage.

```
AwarenessArtifact → ExperienceAdmission → Experience Store
                                           ↓ (rejected)
                                      Short-term log only
```

#### Admission Criteria

| Criterion | Threshold | Rationale |
|-----------|-----------|-----------|
| confidence | >= 0.7 | Below this: noise, not insight |
| evidence_refs count | >= 2 | Single-source observations are unreliable |
| significance was "high" | delta >= 20 or risk_spike | Minor fluctuations are ephemeral |

#### Artifact Lifecycle

```
SHORT_TERM   — stored in EventStore (always), not in Experience
LONG_TERM    — stored in Experience (passes admission gate)
```

### 2.3 Implementation

```python
@dataclass
class ExperienceAdmission:
    min_confidence: float = 0.7
    min_evidence_refs: int = 2

    def admit(self, artifact: AwarenessArtifact) -> tuple[bool, str]:
        """Returns (admitted, reason)."""
        if artifact.confidence < self.min_confidence:
            return False, f"confidence {artifact.confidence} < {self.min_confidence}"
        if len(artifact.evidence_refs) < self.min_evidence_refs:
            return False, f"evidence_refs {len(artifact.evidence_refs)} < {self.min_evidence_refs}"
        return True, "admitted to long-term experience"
```

---

## 3. Updated M3 Pipeline

```
World Change
      │
      ▼
ObservationEvent  (ingested from capability)
      │
      ▼
ObservationRouter  (significance check — rule-based, no LLM)
      │
      ▼
ObservationPolicy  (rate limit + cooldown)  ← ADR-029 NEW
      │
      ▼
WorkflowRuntime.execute("observation.market")
      │
      ├── observe.collect_evidence
      ├── observe.build_context
      ├── observe.evaluate_significance
      ├── observe.generate_artifact
      └── observe.store_experience
              │
              ▼
      ExperienceAdmission  (confidence + evidence gate)  ← ADR-029 NEW
              │
      ┌───────┴───────┐
      ▼               ▼
  LONG_TERM       SHORT_TERM
  (Experience)    (EventStore only)
```

---

## 4. Relationship to Existing ADRs

| ADR | Concern | ADR-029 Impact |
|-----|---------|---------------|
| ADR-024 | Capability Architecture | ObservationPolicy does NOT restrict capability access — it gates workflow creation |
| ADR-027 | Runtime Execution | Policy check is a pre-workflow gate, not a workflow step |
| ADR-028 | Awareness Runtime | Extends Section 4 (pipeline) with two new gates |

---

## 5. M3.1 Scope Update

Before ADR-029:
- M3.1 = market.event.observe capability + real ai_theme_app connection

After ADR-029:
- M3.1 = ObservationPolicy + ExperienceAdmission + market.event.observe

The Policy and Admission gates MUST be in place before real market data flows into Julia. Otherwise the first live trading day will flood the system.

---

*ADR-029 freezes the cognitive filter layer. M3.1 implementation includes both Policy and Admission gates before connecting real market data.*

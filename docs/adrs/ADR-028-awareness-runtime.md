# ADR-028: Market Awareness Runtime Architecture v1.0

**Date:** 2026-08-06
**Status:** PROPOSED → FROZEN
**Supersedes:** None (new awareness layer — extends ADR-026 + ADR-027)

---

## Summary

ADR-027 defined how Julia acts. ADR-028 defines how Julia notices the world.

This is the leap from reactive agent ("user asks → Julia answers") to aware runtime ("world changes → Julia notices → Julia understands → Julia remembers").

M3 is NOT a collection of new API tools. It is an Awareness Runtime built on the event+workflow infrastructure from R1.

---

## 1. Core Principle

```
World Change → Observation Event → Observation Workflow → Capability Runtime → Context OS → Julia Reasoning → Experience Artifact
```

**Forbidden pattern:**

```
World Change → LLM Prompt → Answer  ❌
```

This reduces Julia to a financial chatbot. Julia is a Runtime that owns perception, not a model that receives data.

---

## 2. Three Core Objects

### 2.1 Observation Event

Capability answers: *What did I query?*

Observation Event answers: *What changed in the world?*

```python
@dataclass(frozen=True, slots=True)
class ObservationEvent:
    event_id: str
    timestamp: str
    source: str                # "ai_theme_app" | "calendar" | "github" | ...
    event_type: str            # "world.market.changed" | "world.risk.emerged"
    subject: str               # "AI机器人" | "半导体" | "外围市场"
    change_type: str           # "heat_jump" | "risk_spike" | "sentiment_shift"
    delta: str                 # "+18" | "-5" | "new_high"
    raw_capability_ref: str    # capability invocation ID for audit
    confidence: float          # 0.0-1.0
```

### 2.2 Observation Workflow

Extends WorkflowRuntime from ADR-027. Event-driven, not user-driven.

```
world.market.changed
      │
      ▼
ObservationWorkflow created (workflow.type = "observation.market")
      │
      ├── step: observe.collect_snapshot
      ├── step: observe.collect_theme_state
      ├── step: observe.evaluate_risk
      ├── step: observe.generate_awareness
      └── step: observe.store_experience
```

### 2.3 Awareness Context

Observation events enter Context OS through governed ContextBlocks — never as raw prompt elements.

```python
ContextBlock(
    source="ai_theme_app",
    block_type="market_awareness",
    block_kind="external_intelligence",
    content={
        "subject": "AI机器人",
        "change": "heat_jump +18%",
        "facts": [...],
        "evidence_refs": ["evt_123", "decision_456"],
        "confidence": 0.82,
    },
    authority="market_observation",
    authority_score=0.75,
)
```

---

## 3. Architecture

```
                  External World
                       │
              +--------+--------+
              │                 │
        ai_theme_app       Future Sources
        Market Brain       (Calendar, GitHub, IoT)
              │                 │
              ▼                 ▼
        Observation Event   Observation Event
              │                 │
              +--------+--------+
                       │
                       ▼
              EventStore.append()
                       │
                       ▼
              ObservationRouter
              (event → workflow dispatch)
                       │
                       ▼
              WorkflowRuntime
              (observation.market)
                       │
              +--------+--------+
              │                 │
        CapabilityManager   Context OS
              │                 │
              ▼                 ▼
        Market Data        Awareness ContextBlocks
              │                 │
              +--------+--------+
                       │
                       ▼
                 Julia Reasoning
                       │
                       ▼
              AwarenessArtifact → Experience
```

---

## 4. Five Acceptance Criteria

### AC-M3-1: Event Ingestion
External market changes enter EventStore as `world.market.changed` events with provenance (source, timestamp, capability_ref).

### AC-M3-2: Event → Workflow
A `world.market.changed` event triggers creation of an `observation.market` workflow. The workflow instance has `trigger_event_id` linking back to the observation event.

### AC-M3-3: Workflow → Capability
Observation workflows MUST go through CapabilityManager. Direct MCP access is forbidden. Every data fetch is a governed capability invocation with permission check and evidence record.

### AC-M3-4: Awareness Artifact
Julia produces an `AwarenessArtifact` — not a report, but a structured record of what was noticed, with evidence refs, confidence, and reasoning chain. This is NOT a prompt-generated summary.

### AC-M3-5: Timeline Reconstruction
Given an `observation_id`, the full causal chain can be reconstructed: what triggered the observation → what data was used → how the judgment was formed → what artifact was produced.

---

## 5. Forbidden Patterns

1. ❌ Observation → LLM Prompt → Response (bypasses Runtime)
2. ❌ ObservationWorkflow calling MCP directly (bypasses CapabilityManager)
3. ❌ Market data entering system prompt as raw text (bypasses Context OS)
4. ❌ Timer/scheduler as the only trigger (observation is event-driven, not cron-driven)
5. ❌ AwarenessArtifact with no evidence refs (un-auditable)

---

## 6. Implementation Phases

### M3.0 — Observation Runtime Skeleton
- `observation/models.py` — ObservationEvent, AwarenessArtifact
- `observation/router.py` — ObservationRouter (event → workflow dispatch)
- `observation/workflow.py` — MarketObservationWorkflow definition
- Simulated `world.market.changed` events
- Verify: Event → Workflow → Artifact chain

### M3.1 — Market Event Provider
- New capability: `market.event.observe`
- Connects ai_theme_app as observation source
- Real ObservationEvents enter EventStore
- Full AC-M3-1 and AC-M3-2 verification

### M3.2 — Awareness Workflow
- Full `observation.market` workflow with all 5 steps
- CapabilityManager integration for data fetching
- Context OS integration for awareness context
- AC-M3-3 and AC-M3-4 verification

### M3.3 — Experience Feedback
- AwarenessArtifact stored in Experience OS
- Timeline reconstruction for audit
- Foundation for M7 Feedback Loop
- AC-M3-5 verification

---

## 7. Relationship to Existing ADRs

| ADR | Concern | ADR-028 Impact |
|-----|---------|---------------|
| ADR-024 | Capability Architecture | ObservationWorkflow uses CapabilityManager — never bypasses |
| ADR-026 | MCP Adapter | ai_theme_app is the first observation source, not the only one |
| ADR-027 | Runtime Execution | ObservationWorkflow extends WorkflowRuntime — same lifecycle, event-driven trigger |

---

*ADR-028 freezes the Awareness Runtime architecture. M3 implementation follows this design. No observation code until this ADR is reviewed and frozen.*

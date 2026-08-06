# ADR-030: Market Intelligence Integration Contract v1.0

**Date:** 2026-08-06
**Status:** FROZEN
**Supersedes:** ADR-028 Addendum (M3.2 implementation contract)
**Parent:** ADR-026 MCP Adapter, ADR-028 Awareness Runtime, ADR-029 Observation Policy

---

## Summary

M3.2 connects ai_theme_app Analyst Workbench to Julia Awareness Runtime. This ADR freezes the integration contract — the exact schemas, adapter rules, and routing policies that govern how domain intelligence enters Julia's cognitive system.

The contract ensures: (1) ai_theme_app's domain model never leaks into Julia Runtime, (2) every observation carries identity for deduplication, (3) experience is routed to the correct tier based on signal quality.

---

## 1. Observation Schema (Frozen)

### 1.1 ai_theme_app → Julia (Adapter Input)

```python
# Raw capability result from market.intelligence.observe
{
    "capability": "market.intelligence.observe",
    "source": "ai_theme_app_analyst_workbench",
    "schema_version": "1.1",
    "generated_at": "2026-08-06T09:30:00+08:00",
    "observations": [
        {
            "id": "obs_001",
            "type": "theme.breakout",          # event classification
            "theme": "AI机器人",               # subject
            "signal_level": "L3",              # L0-L4
            "summary": "...",                   # human-readable
            "evidence": ["...", "..."],         # evidence labels
            "confidence": 0.86,
            "prediction_id": "pred_xxx",        # M7 feedback link
            "decision_envelope_ref": "dec_xxx", # traceability
        }
    ]
}
```

### 1.2 Adapter Output → ObservationEvent (Julia Internal)

```python
ObservationEvent(
    source="ai_theme_app",
    domain="market",
    event_type="world.market.intelligence.changed",
    subject="AI机器人",
    change_type="theme.breakout",
    delta="L3",
    payload={
        "summary": "...",
        "evidence_labels": ["...", "..."],
        "prediction_id": "pred_xxx",
        "decision_envelope_ref": "dec_xxx",
    },
    evidence_refs=("pred_xxx", "dec_xxx"),
    confidence=0.86,
)
```

### 1.3 Forbidden

```
❌ DecisionEnvelope → Julia Runtime (bypasses adapter)
❌ ai_theme_app internal fields (theme_id, gate_score, embedding) → ObservationEvent
❌ Raw MCP tool names (review_market_snapshot, list_active_alerts) → Awareness layer
```

---

## 2. Provider Metadata (Frozen)

Every intelligence observation carries provider metadata for multi-source traceability:

```python
@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    provider_name: str          # "ai_theme_app"
    provider_version: str       # "analyst_workbench_v1"
    schema_version: str         # "1.1"
    generated_at: str           # ISO 8601
    capability_name: str        # "market.intelligence.observe"
```

---

## 3. Observation Identity (Frozen)

For deduplication. Two observations with the same identity key within the same time window are treated as duplicates.

```python
def observation_identity_key(observation: dict) -> str:
    domain = observation.get("domain", "market")
    subject = observation.get("theme", observation.get("subject", "unknown"))
    event_type = observation.get("type", "unknown")
    window = _time_window(observation.get("generated_at", ""), minutes=15)
    return f"{domain}:{subject}:{event_type}:{window}"
```

Rules:
- Same identity key within the same 15-minute window → single workflow trigger
- Different subject or different event_type → new identity
- Different time window → new identity

---

## 4. Experience Tier Routing (Frozen)

Observation → Artifact → Tier routing based on signal_level + confidence + evidence:

| Signal Level | Confidence | Evidence Count | Tier |
|-------------|-----------|---------------|------|
| L0 | any | any | **Discard** — not stored |
| L1 | any | any | **Cache** — 24hr temporary log |
| L2 | < 0.6 | any | **Cache** — borderline |
| L2 | >= 0.6 | >= 1 | **Working** — current cycle |
| L3 | >= 0.7 | >= 2 | **Long-term Experience** |
| L4 | >= 0.8 | >= 2 | **Long-term Experience** (always) |

```python
def route_tier(signal_level: str, confidence: float, evidence_count: int) -> str:
    level_map = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
    lvl = level_map.get(signal_level, 0)
    if lvl <= 0: return "discard"
    if lvl <= 1: return "cache"
    if lvl == 2 and confidence >= 0.6: return "working"
    if lvl == 2: return "cache"
    if lvl >= 3 and confidence >= 0.7 and evidence_count >= 2: return "experience"
    if lvl >= 3: return "working"
    return "cache"
```

---

## 5. Complete M3.2 Pipeline (Frozen)

```
ai_theme_app Analyst Workbench
      │
      ▼
CapabilityManager.execute("market.intelligence.observe")
      │
      ▼
AiThemeIntelligenceProvider.observe()
      │  raw capability result
      ▼
IntelligenceAdapter.convert()
      │  DecisionEnvelope → ObservationEvent
      ▼
ObservationRouter.evaluate()
      │  significance check (confidence + delta)
      ▼
ObservationPolicy.should_process_intelligence()
      │  decision level filter + rate limit + cooldown
      ▼
ObservationIdentity.deduplicate()
      │  identity key + time window
      ▼
WorkflowRuntime.execute("observation.market")
      │  5 steps: evidence → context → evaluate → artifact → experience
      ▼
ExperienceTierRouter.route()
      │  L0-4 → discard/cache/working/experience
      ▼
EventStore (always) + Experience (conditional)
```

---

## 6. M3.2 Acceptance Criteria

### AC-M3.2-1: Adapter Boundary
DecisionEnvelope does NOT enter Julia Runtime directly. Test: capture adapter output, verify no ai_theme_app internal field names (theme_id, gate_score, embedding) appear.

### AC-M3.2-2: Deduplication
Two observations with identical identity key within 15min → single workflow trigger. Test: send two identical observations, assert `workflow.count == 1`.

### AC-M3.2-3: Tier Routing
L1 signal → Cache (not Experience). Test: L1 observation → assert artifact in cache, NOT in experience store.

### AC-M3.2-4: L3/L4 → Experience
L3 with confidence >= 0.7 + evidence >= 2 → Experience. Test: L3 observation → assert artifact in long-term experience.

### AC-M3.2-5: Timeline Reconstruction
Input observation_id → recover full chain: DecisionEnvelope → ObservationEvent → Workflow → Artifact → Experience tier. Test: reconstruct timeline, assert >= 6 events.

### AC-M3.2-6: Provider Isolation (non-functional)
Stop ai_theme_app. Julia Core still boots, chats, and Awareness Runtime operates (graceful degradation). Test: close MCP connection, assert JuliaSession.chat() works.

---

## 7. New Module Structure

```
julia_core/
  awareness/
    ingestion.py       # IntelligenceAdapter (DecisionEnvelope → ObservationEvent)
    identity.py        # ObservationIdentity (deduplication key)

  experience/
    tiers.py           # ExperienceTierRouter (cache/working/experience routing)

tests/
  m3_2/
    test_adapter.py          # AC-M3.2-1
    test_deduplication.py    # AC-M3.2-2
    test_tier_routing.py     # AC-M3.2-3, AC-M3.2-4
    test_timeline.py         # AC-M3.2-5
    test_isolation.py        # AC-M3.2-6
```

---

## 8. Relationship to Existing ADRs

| ADR | Concern | ADR-030 Impact |
|-----|---------|---------------|
| ADR-026 | MCP Adapter | IntelligenceAdapter extends MCP boundary — domain model never leaks |
| ADR-028 | Awareness Runtime | Implements the complete M3.2 pipeline with frozen schemas |
| ADR-029 | Observation Policy | Tier routing extends Admission with 4-level output (discard/cache/working/experience) |

---

*ADR-030 freezes the integration contract. M3.2 implementation follows this contract. No real market data enters Julia Runtime before these schemas and routing rules are code-verified.*

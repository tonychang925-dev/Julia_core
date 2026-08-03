# Phase Contract — H6.1 — Tony-Julia Daily Usage Pilot

Status: COMPLETE / APPROVED at Pilot Contract MVP scope  
Date: 2026-08-02

## 1. Purpose

H6.1 shifts Julia from development validation into real Tony-Julia daily collaboration observation.

Primary question:

```text
Will Tony want to use Julia every day?
```

H6.1 does not add new Core capability. It freezes the pilot measurement contract and creates a Daily Relationship Snapshot from real observations.

## 2. Pilot Rule

```text
Use real work.
Do not manufacture benchmark conversations.
Do not add features to hide friction.
Observe where Julia is not yet good enough.
```

## 3. Data Sources

Allowed sources:

```text
real chats
real voice sessions
real project collaboration
real technical discussion
```

Not allowed as pilot evidence:

```text
synthetic benchmark-only cases
manual Memory inflation
automatic Persona rewrite
automatic Identity update
```

## 4. Daily Relationship Snapshot

The snapshot is a work log, not Memory.

```json
{
  "date": "2026-08-02",
  "sessions": 8,
  "turns": 42,
  "topics": ["Julia Core", "AI architecture", "stock agent"],
  "continuity_success": 0.92,
  "repeated_explanation_rate": 0.05,
  "memory_usefulness": 0.85,
  "evidence_success_rate": 0.78,
  "manual_corrections": 2,
  "human_friction_score": 3,
  "voice_usage_ratio": 0.35
}
```

## 5. Frozen H6.1 Metrics

```text
Continuity Success
- context recovered
- manual explanation not required

Memory Utility
- useful Memory hits / observed Memory hits

Evidence Effectiveness
- successful Evidence retrieval / triggered Evidence retrieval

Human Friction
- correction_count
- repetition_required
- wrong_assumption_count

Voice Adoption
- voice turns / all turns
```

## 6. Evolution Boundary

Correct path:

```text
Observation
  ↓
Pattern Detection
  ↓
Evolution Proposal
  ↓
Human Approval
  ↓
Artifact Update
```

Forbidden path:

```text
Observation
  ↓
Automatic Memory / Persona / Identity mutation
```

## 7. Acceptance Gates

```text
H6-101 Daily snapshot summarizes real usage metrics.
H6-102 Snapshot is not Memory or Identity.
H6-103 Empty daily snapshot is stable.
H6-104 Pilot forbids auto-evolution shortcuts.
H6-105 Roadmap, feature spec, contract, and report document H6.1.
```

## 8. Next

```text
H6.2 — Reality Feedback Analysis
```

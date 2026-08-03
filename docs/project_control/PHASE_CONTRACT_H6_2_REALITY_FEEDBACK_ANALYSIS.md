# Phase Contract — H6.2 — Reality Feedback Analysis

Status: COMPLETE / APPROVED at Pattern Classification MVP scope  
Date: 2026-08-02

## 1. Purpose

H6.2 converts real pilot observations into governed evolution proposals.

It does not optimize Julia directly. It answers:

```text
Where does Julia really need to change?
```

## 2. Input

```text
runtime_observations/pilot_observations.jsonl
DailyRelationshipSnapshot[]
```

## 3. Output

```text
artifacts/evolution/evolution_proposals.jsonl
```

This is not Memory and not Identity. It is an approval queue.

## 4. Pattern Categories

### Category A — Core Improvement Candidate

Repeated friction indicates Julia misses context, memory utility, evidence grounding, or continuity recovery.

Target example:

```text
Context OS
```

### Category B — User Habit

Repeated Tony collaboration pattern should be considered for Reality Baseline.

Target example:

```text
Reality Baseline
```

### Category C — Provider Limitation

Issue appears caused by provider latency, style, voice quality, or model capability.

Target example:

```text
Provider Boundary
```

### Category D — Noise

Single or weak signal. No proposal.

## 5. Evolution Proposal Contract

```json
{
  "proposal_id": "EP-001",
  "type": "context_improvement",
  "evidence": {"occurrences": 12, "sessions": 8},
  "pattern": "Tony repeatedly references previous architecture decisions",
  "impact": "Context reconstruction misses decision rationale",
  "target": "Context OS",
  "risk": "medium",
  "requires_human_approval": true,
  "status": "proposed"
}
```

## 6. Adaptation Quality Score

```text
AQS = Useful Evolution - Unnecessary Change - Identity Drift Risk
```

In H6.2 MVP this is implemented as a bounded proposal-quality score.

## 7. Anti-pattern Gates

```text
AP-001 Single Event Overreaction
AP-002 Short-term Mood Leakage
AP-003 Metric Gaming
```

Forbidden:

```text
single event -> identity change
joke/mood -> persona update
lower corrections -> stop confirming uncertainty
proposal -> automatic application
```

## 8. Governance Boundary

Correct path:

```text
Observation
  ↓
Pattern Classification
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

## 9. Acceptance Gates

```text
H6-201 Repeated friction generates Context OS improvement proposal.
H6-202 User habit and provider limitation classify separately.
H6-203 AP-001 single event overreaction remains noise.
H6-204 Proposal store is append-only artifact, not Memory.
H6-205 Adaptation Quality Score is computed.
H6-206 AP-002/AP-003 forbidden auto-evolution tokens absent.
H6-207 Roadmap, feature spec, contract, and report document H6.2.
```

## 10. Next

```text
H6.3 — Julia Assistant v1.0 Release
```

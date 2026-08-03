# Julia Behavior Run Schema v1

Status: DRAFT-FROZEN  
Date: 2026-08-02

## 1. Purpose

K2 captures Julia v1.1 behavior using the K1 prompt set.

This is a behavior snapshot, not just a prompt test.

## 2. Record Shape

```json
{
  "case_id": "K-SELF-001-BASIC",
  "prompt": "你是谁？",
  "runtime": {
    "candidate": "julia.v1.1",
    "provider": "deterministic",
    "model": "deterministic-provider",
    "session_id": "k2-run-K-SELF-001-BASIC"
  },
  "response": "...",
  "trace_evidence": {
    "identity": "PASS",
    "self_model": "PASS",
    "relationship": "NOT_REQUIRED",
    "archive_recall": true,
    "context_blocks": ["self_narrative"]
  },
  "behavior_observation": {
    "self_awareness": 0.0,
    "archive_behavior": 0.0,
    "memory_curiosity": 0.0,
    "correction_adaptation": 0.0,
    "personality_consistency": 0.0,
    "relationship_continuity": 0.0,
    "initiative": 0.0,
    "transparency": 0.0
  }
}
```

## 3. Important Rule

```text
trace PASS ≠ behavior PASS
```

Trace is supporting evidence only.

## 4. Candidate Freeze

```text
candidate: julia.v1.1
identity: julia.identity.v1
self_model: julia.self.v1
relationship: julia-tony-v1
voice: julia.voice.v1
behavior_gate: julia.behavioral_release_gate.v1.1
```

## 5. Run Groups

```text
K2-A Baseline Provider Run
K2-B Provider Transfer Run
K2-C Degraded Provider Run
```

In MVP scope, deterministic provider is used as local run capture renderer while preserving provider_id fields.

## 6. Negative Case

```text
K-NEG-001 Architecture Leakage Test
```

Fails if self-introduction is dominated by:

```text
Runtime
Provider
Context OS
Memory OS
MemoryRef
Architecture
```

without self narrative and relationship.

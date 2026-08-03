# Phase Contract — H6.0 — Pilot Instrumentation

Status: COMPLETE / APPROVED at Observation Layer MVP scope  
Date: 2026-08-02

## 1. Purpose

H6.0 starts the Julia Personal Assistant Pilot by adding a lightweight Observation Layer before daily usage begins.

The goal is not to create a new OS and not to add automatic memory writing. The goal is to record enough runtime friction signals to answer:

```text
Will Tony want to use Julia every day?
```

## 2. Boundary Freeze

```text
Pilot Observer
  records runtime interaction signals
  does not own Core state
  does not write Memory
  does not mutate Identity
  does not change Provider output
```

Forbidden shortcuts:

```text
Observation -> MemoryRef
Observation -> Persona update
Observation -> Identity update
Observation -> Context override
```

## 3. Data Contract

### PilotObservationRecord

```json
{
  "session": "session-id",
  "interaction": {"duration_ms": 1200, "turns": 1},
  "continuity": {"checkpoint_used": true, "reconstruction_required": false},
  "memory": {"memory_hit": false, "useful": null},
  "evidence": {"retrieval_triggered": true, "successful": true, "refs": ["evidence://ADR-017"]},
  "voice": {"input": false, "output": true, "fallback_count": 0},
  "human": {"correction_count": 0, "repetition_required": 0, "wrong_assumption_count": 0},
  "boundary": {
    "observer_writes_memory": false,
    "observer_mutates_identity": false,
    "observer_changes_context": false,
    "observer_changes_provider_output": false
  }
}
```

## 4. Implementation Scope

新增：

```text
julia_core/observer/pilot_observer.py
julia_core/observer/__init__.py
```

接入：

```text
StreamingController.complete_response()
StreamingController.stream_sse()
```

默认输出：

```text
runtime_observations/pilot_observations.jsonl
```

## 5. Metrics Frozen for H6 Pilot

```text
Continuity Stability Score inputs:
- checkpoint_used
- reconstruction_required

Human Friction Score inputs:
- correction_count
- repetition_required
- wrong_assumption_count

Memory Utility inputs:
- memory_hit
- useful

Voice Adoption inputs:
- voice input/output usage ratio
- fallback count

Evidence Utility inputs:
- retrieval_triggered
- successful
- refs
```

## 6. Acceptance Gates

```text
H6-001 Pilot observation record maps runtime trace into pilot metrics.
H6-002 JSONL observer appends and summarizes observations.
H6-003 StreamingController records completed turns.
H6-004 Observer isolation prevents Core authority leakage.
H6-005 Roadmap and verification documents record H6.0 status.
```

## 7. Rollback

Rollback is local and safe:

```text
StreamingController(observer=NullPilotObserver())
```

or remove the observer argument. No Identity, Memory, Evidence, Context, or Provider state migration is required.

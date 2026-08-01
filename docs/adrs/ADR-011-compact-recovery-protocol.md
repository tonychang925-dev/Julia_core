# ADR-011: Compact Recovery Protocol

Status: Proposed
Date: 2026-08-01

## Context

Long-running Claude Code sessions may trigger compaction. Compaction preserves task-relevant summaries but can damage agent identity continuity when identity is hosted in conversation context.

Julia Core must support compact survival as an Agent OS capability.

## Decision

Define a Compact Recovery Protocol coordinated by Runtime OS and Continuity OS.

Before compact risk:

```text
Runtime detects threshold
  ↓
Continuity OS classifies state
  ↓
Checkpoint Level 2/3 refs
  ↓
Summarize Level 1
  ↓
Discard Level 0
```

After compact / restart:

```text
Runtime loads checkpoint
  ↓
Persona Engine loads identity refs
  ↓
Memory OS retrieves protected refs
  ↓
Context OS rebuilds required blocks
  ↓
Alignment OS resolves provider profile
  ↓
Provider generates with restored continuity state
```

## Required Trace

```json
{
  "continuity": {
    "status": "RESTORED",
    "identity_preserved": true,
    "memory_recovered": true,
    "context_rebuilt": true,
    "recovery_reason": "compact"
  }
}
```

## Consequences

Positive:

- Compact becomes survivable.
- Provider switch can be tested as recovery, not prompt migration.
- Julia identity becomes less dependent on any single context window.

Cost:

- Requires Continuity OS runtime implementation.
- Requires Memory OS and Context OS integration.
- Requires Compact Survival Test.


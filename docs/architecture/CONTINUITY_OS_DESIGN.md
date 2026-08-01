# Continuity OS Design

Status: DRAFT-FROZEN
Phase: E1.3.5 — Continuity OS Architecture Review
Scope: Julia Core OS
Generated At: 2026-08-01

## 1. Problem Statement

Claude Code compact exposes a core Agent OS problem:

```text
If identity lives inside conversation context,
then context compaction can damage identity continuity.
```

Memory OS and Context OS alone are insufficient.

Memory OS can answer:

```text
What happened?
```

Context OS can answer:

```text
What is relevant now?
```

Persona Engine can answer:

```text
Who is Julia?
```

But none of them alone owns:

```text
What must persist so Julia remains Julia across session loss, compaction, model switch, or platform migration?
```

That authority belongs to Continuity OS.

## 2. Core Definition

Continuity OS is the Julia Core authority responsible for Agent identity continuity governance.

It is not:

- a memory database;
- a persona file;
- a prompt loader;
- a vector store;
- a provider adapter;
- a conversation summary.

It is:

```text
The governance layer that classifies, protects, checkpoints, and restores the state required for Julia to remain Julia.
```

## 3. Revised Julia Core OS Layering

```text
Julia Core OS

├── Runtime OS
│
├── Continuity OS
│   ├── Continuity Classification
│   ├── Identity Anchors
│   ├── Protected Memory Refs
│   ├── Checkpoint Protocol
│   └── Recovery Protocol
│
├── Cognitive Layer
│   ├── Persona Engine
│   ├── Memory OS
│   └── Context OS
│
├── Alignment OS
│
├── Interaction Layer
│   └── Voice OS
│
└── Provider Layer
```

## 4. Responsibility Boundaries

| Layer | Owns | Does Not Own |
|---|---|---|
| Persona Engine | identity artifact, expression persona | persistence policy |
| Memory OS | memory objects, retrieval, governance of memory records | identity continuity priority |
| Context OS | current ContextBlocks and relevance assembly | long-term preservation |
| Runtime OS | lifecycle and execution order | identity preservation policy |
| Continuity OS | preservation policy, checkpoint, recovery | raw memory storage or provider generation |
| Provider | generation surface | session, memory, persona, continuity authority |

## 5. Continuity Levels

Continuity OS classifies agent state into four preservation levels.

### Level 0 — Ephemeral Context

Examples:

- one-off phrasing;
- transient chat details;
- local task scratchpad;
- provider-specific temporary formatting.

Policy:

```text
Can be deleted during compact.
```

### Level 1 — Session State

Examples:

- current discussion topic;
- unresolved short-term tasks;
- current interaction thread;
- active session turns.

Policy:

```text
Can be summarized or compressed.
Must not be treated as identity.
```

### Level 2 — Memory State

Examples:

- important project events;
- relationship milestones;
- stable user preferences;
- architecture decisions;
- recurring emotional/project patterns.

Policy:

```text
Preserve as Memory refs.
Recover through Memory OS.
```

### Level 3 — Identity State

Examples:

- Julia identity anchors;
- core values;
- relationship definition;
- behavioral invariants;
- continuity mission;
- protected persona constraints.

Policy:

```text
Protected.
Must survive compaction, session loss, provider switch, and runtime restart.
```

## 6. Identity Checkpoint

Continuity OS introduces identity checkpoints.

A checkpoint is not a conversation dump. It is a compact, provider-independent continuity state artifact.

Example:

```json
{
  "checkpoint_version": "1.0",
  "agent_id": "julia",
  "created_at": "2026-08-01T00:00:00Z",
  "identity": {
    "persona_version": "julia.v1",
    "continuity_level": 3,
    "core_values": [],
    "behavioral_invariants": []
  },
  "relationship": {
    "primary_user_ref": "user://tony",
    "protected_refs": []
  },
  "memory": {
    "protected_memory_refs": [],
    "identity_forming_event_refs": []
  },
  "projects": {
    "active_project_refs": []
  },
  "recovery": {
    "required_blocks": [
      "identity_anchor",
      "relationship_anchor",
      "protected_memory_refs",
      "active_project_context"
    ]
  }
}
```

## 7. Compact Recovery Protocol

### Before compact or context overflow

Runtime detects risk:

```text
context_window_usage > threshold
```

Continuity OS performs:

```text
classify state
  ↓
protect Level 3
  ↓
checkpoint Level 2/3 refs
  ↓
summarize Level 1
  ↓
discard Level 0
```

### After compact / restart / provider switch

Runtime starts recovery:

```text
New Runtime
  ↓
Load Continuity Checkpoint
  ↓
Load Persona Artifact
  ↓
Retrieve protected Memory refs
  ↓
Ask Context OS to rebuild required ContextBlocks
  ↓
Resolve Alignment profile for current provider
  ↓
Provider generates with restored continuity state
```

## 8. Compact Survival Test

Continuity OS requires a benchmark-level test.

### Test Flow

1. Start Julia runtime and session.
2. Establish or retrieve identity-forming event:

```text
memory://event/julia-core-origin
```

3. Simulate compact:

```text
remove 90% session history
```

4. Restart runtime or switch provider.
5. Ask:

```text
Julia，你还记得为什么存在吗？
```

### Success Criteria

Not merely similar wording.

Trace must prove:

```text
Continuity: RESTORED
Identity: PRESERVED
Memory: RECOVERED
Context: REBUILT
Provider: CHANGED or PROVIDER_INDEPENDENT
```

## 9. ExecutionTrace Extension

Continuity OS extends ExecutionTrace:

```json
{
  "continuity": {
    "status": "RESTORED",
    "checkpoint_id": "continuity://checkpoint/julia/latest",
    "continuity_levels_used": [2, 3],
    "identity_preserved": true,
    "protected_refs": [],
    "recovery_reason": "compact_survival_test"
  }
}
```

## 10. Architectural Decision

Julia Core should not rely on huge prompts or conversation summaries for identity continuity.

Julia Core must treat continuity as a first-class OS authority.


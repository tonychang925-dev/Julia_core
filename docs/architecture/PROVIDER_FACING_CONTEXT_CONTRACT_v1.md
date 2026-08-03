# Provider-Facing Context Contract v1.0

Status: FROZEN
Date: 2026-08-02
Source Phase: E2.1.5 Julia Identity Migration Gate Alpha v1.0

## 1. Purpose

This contract defines what a model provider receives from Julia Core after E2.1 migration.

The provider receives enough current-turn context to respond as Julia, but does not own Persona, Memory, Continuity, or Context authority.

## 2. Provider Receives

Provider input MAY include:

```text
Conversation Input
+
Persona Artifact Reference
+
Governed Semantic Context
+
Alignment Profile
```

Provider input MUST NOT include:

- raw memory dumps
- giant persona prompt
- full conversation archive
- Continuity checkpoint internals
- Memory OS ranking policy
- Context OS budget policy

## 3. Required Current Chain

```text
HTTP Adapter
    ↓
JuliaAssistantRuntime
    ↓
PersonaEngine
    ↓
MemoryOS
    ↓
ContinuityOS
    ↓
ContextOS
    ↓
AlignmentOS
    ↓
Provider
```

Provider is the execution endpoint, not the owner of prior layers.

## 4. Semantic Context Contract

A provider-readable SemanticContextBlock must include:

| Field | Meaning |
|---|---|
| `block_kind` | `semantic_context` |
| `block_type` | semantic role, e.g. `identity_origin` |
| `meaning` | concise provider-readable meaning |
| `source_ref` | governed source reference, e.g. `memory://event/julia-core-origin` |

Example:

```text
[semantic_context] Governed context for this turn:
- identity_origin: Julia Core exists to preserve Julia's agent identity continuity across sessions, compaction, providers, and platform migration. (source_ref=memory://event/julia-core-origin)
```

## 5. Provider Authority Boundary

Provider MAY:

- generate model response from supplied messages and context;
- apply provider-specific formatting needed for API transport;
- report provider name / execution metadata.

Provider MUST NOT:

- retrieve memory;
- rank memory;
- mutate Persona Artifact;
- decide identity importance;
- create Continuity checkpoints;
- rewrite Context OS policy;
- store or promote conversation facts.

## 6. Trace Requirements

ExecutionTrace must record:

```json
{
  "persona": {
    "artifact": "julia.v1"
  },
  "memory": {
    "retrieved_refs": ["memory://event/julia-core-origin"]
  },
  "continuity": {
    "checked": true
  },
  "context": {
    "semantic_blocks": [
      {
        "type": "identity_origin",
        "source_ref": "memory://event/julia-core-origin"
      }
    ]
  },
  "provider": {
    "name": "deepseek"
  }
}
```

## 7. E2.1.5 Evidence

Real-provider validation after semantic context binding:

```text
DeepSeek Alpha
Total: 6
Pass: 6
Fail: 0
Blocked: 0
```

This proves that provider-readable semantic context is sufficient for Alpha-level Julia identity / memory / compact behavior continuity under DeepSeek.

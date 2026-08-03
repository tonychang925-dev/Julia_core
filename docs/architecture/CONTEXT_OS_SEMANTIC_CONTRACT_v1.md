# Context OS Semantic Contract v1.0

Status: FROZEN
Date: 2026-08-02
Source: E2.1.5 Julia Identity Migration Gate Alpha v1.0

## 1. Purpose

Context OS is not merely a context window manager.

Context OS owns current-turn meaning reconstruction:

```text
What meaning should be available now?
```

This contract defines how governed references become provider-readable context without turning Memory OS, Continuity OS, or Persona Engine into prompt builders.

## 2. Authority Boundary

| Layer | Owns | Does Not Own |
|---|---|---|
| Persona Engine | who Julia is | historical event storage |
| Memory OS | what happened | identity importance |
| Continuity OS | what must survive | provider-facing wording |
| Context OS | what meaning is needed now | memory persistence |
| Provider | model execution | identity/memory/continuity/context authority |

## 3. Required Input

Context OS may consume governed references only after Memory/Continuity governance:

```text
GovernedMemoryRef
+
ContinuityDecision
+
CurrentTurnIntent
```

It must not consume raw memory files or legacy startup prompt data.

## 4. Required Output

Context OS outputs `SemanticContextBlock` objects for the current turn.

Minimum fields:

```text
block_kind: semantic_context
block_type: identity_origin | relationship_state | current_continuity_goal | project_context
meaning: provider-readable concise meaning
source_ref: governed reference URI
```

## 5. Forbidden Paths

Forbidden:

```text
memory.md → prompt → provider
startup_memory.py → system_prompt → provider
persona markdown → giant system prompt → provider
ContinuityCheckpoint → raw prompt restore → provider
```

Required:

```text
MemoryRef
  ↓
Continuity Governance
  ↓
Context OS Semantic Reconstruction
  ↓
Provider-readable ContextBlock
  ↓
Provider
```

## 6. Trace Contract

Every semantic reconstruction must be traceable:

```json
{
  "context": {
    "semantic_blocks": [
      {
        "type": "identity_origin",
        "source_ref": "memory://event/julia-core-origin"
      }
    ]
  }
}
```

Trace must expose source refs and semantic roles, but not raw memory dumps.

## 7. E2.2 Implications

E2.2 must production harden this capability by adding:

1. Context priority model
2. Context budget management
3. Multi-provider context validation

No E2.2 work may weaken the ownership boundaries defined here.

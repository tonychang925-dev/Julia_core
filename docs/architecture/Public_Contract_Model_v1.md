# Public Contract Model v1.0 — FROZEN

## Five APIs

| API | Input | Output | Authority |
|-----|-------|--------|-----------|
| Context OS | ContextRequest | ContextBlock(s) | Single context authority |
| Provider | ContextRequest | ContextBlock(s) | Facts & evidence |
| Runtime | — | Lifecycle + Session | Agent lifecycle |
| Memory | — | Stored experience | Separate from context |
| Persona | — | Style & behavior | Public demo data only |

## Dependency Direction

```
Provider → Core (one-way)
Core ⊥ Provider (core never imports provider)
```

## Private Boundary

Public: code, schemas, examples, tests, docs
Private: identity, memory, conversations, preferences (lives in julia_private)

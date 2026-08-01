# Runtime API v1.0 — FROZEN

## Lifecycle

```
CREATED → READY → RUNNING → STOPPED
```

## Session

```python
session = ChatSession(persona=demo_persona)
session.add_turn(user_text, assistant_text)
session.close()
```

## Rules

- Runtime manages lifecycle; does NOT manage cognition.
- Session is ephemeral by default.
- Provider registration is done via registry, not hardcoded.

FROZEN.

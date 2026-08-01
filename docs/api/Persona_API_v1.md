# Persona API v1.0 — FROZEN

## Definition

```python
@dataclass(frozen=True, slots=True)
class Persona:
    persona_id: str
    name: str
    role: str
    tone: str = "warm"
    system_prompt: str = ""
```

## Rules

- Persona provides style, behavior, interaction profile.
- Persona does NOT control reasoning or override governance.
- Demo personas use synthetic data only.
- Private personas live in private repositories.

FROZEN. Persona ≠ identity. Public personas ≠ private data.

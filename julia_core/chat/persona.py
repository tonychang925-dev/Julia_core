"""Generic persona definition. Julia is ONE instance of this."""
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class Persona:
    persona_id: str
    name: str
    role: str
    language: str = "zh"
    tone: str = "warm"
    system_prompt: str = ""
    context_load_policy: str = "startup_only"

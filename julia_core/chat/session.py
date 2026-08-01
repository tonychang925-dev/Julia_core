"""Generic chat session — provider and persona agnostic."""
from dataclasses import dataclass, field
from uuid import uuid4

from julia_core.chat.persona import Persona

@dataclass(slots=True)
class ChatSession:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    persona: Persona | None = None
    history: list[dict] = field(default_factory=list)
    closed: bool = False

    def add_turn(self, user: str, assistant: str) -> None:
        self.history.append({"role": "user", "content": user})
        self.history.append({"role": "assistant", "content": assistant})

    def close(self) -> None:
        self.closed = True

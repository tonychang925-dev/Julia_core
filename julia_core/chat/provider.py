"""Provider interface for chat — LLM-agnostic."""
from typing import Protocol, runtime_checkable

@runtime_checkable
class ChatProvider(Protocol):
    provider_id: str

    def chat(self, messages: list[dict], *, persona: object | None = None) -> str:
        ...

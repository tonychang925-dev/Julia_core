"""Core Context OS request contract.

A request expresses what Julia needs. It is not domain data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ContextRequest:
    task_intent: str
    intent: str
    domain: str | None = None
    request_id: str = field(default_factory=lambda: f"ctx_req_{uuid4().hex}")
    session_id: str | None = None
    cognitive_mode: str = "conversation"
    domain_object_type: str | None = None
    domain_object_id: str | None = None
    required_capabilities: tuple[str, ...] = ()
    evidence_intents: tuple[str, ...] = ()
    required_blocks: tuple[str, ...] = ()
    optional_blocks: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()
    constraints: Mapping[str, object] = field(default_factory=dict)
    target_budget_tokens: int = 4000
    payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.task_intent:
            raise ValueError("task_intent is required")
        if not self.intent:
            raise ValueError("intent is required")
        if self.target_budget_tokens <= 0:
            raise ValueError("target_budget_tokens must be positive")
        object.__setattr__(self, "required_capabilities", tuple(self.required_capabilities))
        object.__setattr__(self, "evidence_intents", tuple(self.evidence_intents))
        object.__setattr__(self, "required_blocks", tuple(self.required_blocks))
        object.__setattr__(self, "optional_blocks", tuple(self.optional_blocks))
        object.__setattr__(self, "exclusions", tuple(self.exclusions))
        object.__setattr__(self, "constraints", MappingProxyType(dict(self.constraints)))
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

"""Minimal domain-independent Context OS planner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .request import ContextRequest


@dataclass(frozen=True, slots=True)
class ContextPlanner:
    default_budget_tokens: int = 4000

    def plan(
        self,
        *,
        task_intent: str,
        intent: str,
        domain: str | None = None,
        cognitive_mode: str = "conversation",
        required_capabilities: tuple[str, ...] = (),
        constraints: Mapping[str, object] | None = None,
    ) -> ContextRequest:
        return ContextRequest(
            task_intent=task_intent,
            intent=intent,
            domain=domain,
            cognitive_mode=cognitive_mode,
            required_capabilities=tuple(required_capabilities),
            constraints=dict(constraints or {}),
            target_budget_tokens=self.default_budget_tokens,
        )

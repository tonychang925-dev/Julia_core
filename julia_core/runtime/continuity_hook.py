"""Runtime-owned hook into Continuity OS.

E1.8.1 scope is intentionally narrow:
    Runtime -> Continuity check -> ExecutionTrace fragment

This module does not create checkpoints, resolve memory refs, reconstruct
context, invoke alignment, or call providers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from julia_core.continuity.events import ContinuityEvent


class CheckpointLike(Protocol):
    checkpoint_id: str
    continuity_levels: dict[str, list[str]]


CheckpointLookup = Callable[[str], CheckpointLike | None]


@dataclass(frozen=True, slots=True)
class RuntimeContinuityInspection:
    """Result of a Runtime-triggered continuity inspection."""

    checked: bool
    event: ContinuityEvent
    agent_id: str
    checkpoint_found: bool
    checkpoint_id: str | None = None
    decision_level: str = "NONE"
    recovery_status: str = "NOT_REQUIRED"

    def to_trace(self) -> dict[str, Any]:
        trace: dict[str, Any] = {
            "checked": self.checked,
            "checkpoint_found": self.checkpoint_found,
            "decision_level": self.decision_level,
            "recovery_status": self.recovery_status,
        }
        if self.checkpoint_id is not None:
            trace["checkpoint_id"] = self.checkpoint_id
        return trace


class RuntimeContinuityHook:
    """Minimal Runtime -> Continuity hook.

    Runtime owns when this hook is called. Continuity owns what the checkpoint
    means. The hook only inspects availability and emits trace fields.
    """

    def __init__(
        self,
        *,
        agent_id: str = "julia",
        checkpoint_lookup: CheckpointLookup | None = None,
    ) -> None:
        self._agent_id = agent_id
        self._checkpoint_lookup = checkpoint_lookup or (lambda _agent_id: None)

    def inspect(self, request: dict[str, Any]) -> RuntimeContinuityInspection:
        """Inspect continuity state from a Runtime-owned request envelope."""
        event = request.get("event", ContinuityEvent.SESSION_START)
        runtime_state = request.get("runtime_state", {})
        agent_id = request.get("agent_id", self._agent_id)
        return self.check_state(runtime_state, event=event, agent_id=agent_id)

    def check_state(
        self,
        runtime_state: dict[str, Any] | None = None,
        *,
        event: ContinuityEvent | str = ContinuityEvent.SESSION_START,
        agent_id: str | None = None,
    ) -> RuntimeContinuityInspection:
        """Return continuity checkpoint availability for a Runtime event."""
        continuity_event = self._coerce_event(event)
        selected_agent_id = agent_id or self._agent_id
        checkpoint = self._checkpoint_lookup(selected_agent_id)

        if checkpoint is None:
            return RuntimeContinuityInspection(
                checked=True,
                event=continuity_event,
                agent_id=selected_agent_id,
                checkpoint_found=False,
                decision_level="NONE",
                recovery_status="NOT_REQUIRED",
            )

        return RuntimeContinuityInspection(
            checked=True,
            event=continuity_event,
            agent_id=selected_agent_id,
            checkpoint_found=True,
            checkpoint_id=checkpoint.checkpoint_id,
            decision_level=self._highest_level(checkpoint),
            recovery_status="NOT_STARTED",
        )

    def create_trace(self, inspection: RuntimeContinuityInspection) -> dict[str, Any]:
        """Create the first Runtime ExecutionTrace continuity fragment."""
        return {
            "runtime": {
                "status": "PASS",
                "event": inspection.event.value,
            },
            "continuity": inspection.to_trace(),
        }

    @staticmethod
    def _coerce_event(event: ContinuityEvent | str) -> ContinuityEvent:
        if isinstance(event, ContinuityEvent):
            return event
        return ContinuityEvent[event]

    @staticmethod
    def _highest_level(checkpoint: CheckpointLike) -> str:
        levels = checkpoint.continuity_levels
        for level in ("L3_IDENTITY", "L2_MEMORY", "L1_SESSION", "L0_EPHEMERAL"):
            if levels.get(level):
                return level
        return "NONE"

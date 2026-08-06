"""R1.2 Workflow Registry — named workflow definitions.

ADR-027 Section 6: WorkflowDefinitions are registered here.
The WorkflowRuntime looks up definitions by name when executing.
"""

from __future__ import annotations

from julia_core.workflow.models import WorkflowDefinition


class WorkflowRegistry:
    """Registry of named workflow definitions."""

    def __init__(self):
        self._definitions: dict[str, WorkflowDefinition] = {}

    def register(self, definition: WorkflowDefinition):
        self._definitions[definition.name] = definition

    def get(self, name: str) -> WorkflowDefinition | None:
        return self._definitions.get(name)

    def list_all(self) -> list[str]:
        return sorted(self._definitions.keys())


# ── M0 Default Workflows ────────────────────────────────────────────────────

MARKET_BRIEF_WORKFLOW = WorkflowDefinition(
    name="market.brief",
    description="Market Brief: user asks about market → capability → context → reasoning → artifact",
    steps=(
        "intent.resolve",
        "capability.request",
        "context.build",
        "reasoning.execute",
        "artifact.create",
        "experience.record",
    ),
    trigger_events=("conversation.message.received",),
    timeout_seconds=60,
    version="1.0",
)


def create_default_registry() -> WorkflowRegistry:
    registry = WorkflowRegistry()
    registry.register(MARKET_BRIEF_WORKFLOW)
    return registry


__all__ = ["WorkflowRegistry", "MARKET_BRIEF_WORKFLOW", "create_default_registry"]

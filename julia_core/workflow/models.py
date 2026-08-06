"""R1.2 Workflow Models — ADR-027 Section 5 & 6.

WorkflowDefinition: what steps compose a workflow.
WorkflowInstance: one running (or completed) execution.
WorkflowState: the lifecycle state machine.

Workflows are Runtime-owned. Pipelines are step definitions, not owners.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class WorkflowState(str, Enum):
    """ADR-027 Section 7: Workflow state machine."""
    CREATED             = "CREATED"
    RUNNING             = "RUNNING"
    WAITING_CAPABILITY  = "WAITING_CAPABILITY"
    WAITING_REASONING   = "WAITING_REASONING"
    COMPLETED           = "COMPLETED"
    FAILED              = "FAILED"


@dataclass
class WorkflowDefinition:
    """A named workflow with ordered steps. ADR-027 Section 6.

    Pipelines (like MarketBriefPipeline) register as WorkflowDefinitions.
    The WorkflowRuntime owns execution and lifecycle — the definition is just steps.
    """
    name: str                          # "market.brief"
    description: str = ""
    steps: tuple[str, ...] = ()        # ("intent.resolve", "capability.request", ...)
    trigger_events: tuple[str, ...] = ()  # ("conversation.message.received",)
    timeout_seconds: int = 60
    version: str = "1.0"


@dataclass
class WorkflowInstance:
    """One execution of a workflow. ADR-027 Section 7.

    Owned by WorkflowRuntime. The instance tracks current step, state,
    and all events produced during execution.
    """
    instance_id: str = field(default_factory=lambda: f"wf_{uuid4().hex}")
    workflow_name: str = ""
    state: WorkflowState = WorkflowState.CREATED
    current_step: str = ""
    current_step_index: int = 0
    created_at: str = ""
    completed_at: str = ""
    correlation_id: str = ""           # Links all events in this execution
    event_ids: list[str] = field(default_factory=list)
    step_results: dict = field(default_factory=dict)
    result: dict | None = None         # Final output

    @property
    def is_terminal(self) -> bool:
        return self.state in (WorkflowState.COMPLETED, WorkflowState.FAILED)

    @property
    def is_running(self) -> bool:
        return self.state in (WorkflowState.RUNNING, WorkflowState.WAITING_CAPABILITY, WorkflowState.WAITING_REASONING)


__all__ = [
    "WorkflowState",
    "WorkflowDefinition",
    "WorkflowInstance",
]

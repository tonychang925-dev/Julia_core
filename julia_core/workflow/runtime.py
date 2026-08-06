"""R1.2 Workflow Runtime — owns workflow lifecycle.

ADR-027 Section 5.4: The WorkflowRuntime owns workflow lifecycle.
Pipelines are step definitions, not lifecycle owners.

The WorkflowRuntime:
  1. Creates a WorkflowInstance
  2. Emits workflow.created event
  3. Executes each step in order
  4. Emits workflow.step.started / workflow.step.completed events
  5. Records step results
  6. Transitions to COMPLETED or FAILED
  7. Returns the completed instance with full audit trail
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from julia_core.events.models import (
    EventCategory,
    WorkflowEventType,
    create_event,
)
from julia_core.events.store import EventStore, get_event_store
from julia_core.workflow.models import (
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowState,
)
from julia_core.workflow.registry import WorkflowRegistry

CST = timezone(timedelta(hours=8))


class WorkflowRuntime:
    """Owns workflow lifecycle. Pipelines are step definitions only.

    Usage:
        runtime = WorkflowRuntime(registry, capability_manager, context_adapter)
        instance = await runtime.execute("market.brief", {"user_text": "今天市场怎么样？"})
    """

    def __init__(
        self,
        registry: WorkflowRegistry,
        capability_manager,
        event_store: EventStore | None = None,
    ):
        self.registry = registry
        self.capability_manager = capability_manager
        self.event_store = event_store or get_event_store()

        # Step executors — registered by name
        self._step_executors: dict[str, callable] = {}

    def register_step(self, step_name: str, executor: callable):
        """Register a step executor. Pipelines register their steps here."""
        self._step_executors[step_name] = executor

    async def execute(self, workflow_name: str, input_data: dict) -> WorkflowInstance:
        """Execute a workflow. Returns the completed (or failed) instance.

        Every step transition emits an event. The instance carries the full
        event timeline for audit and reconstruction.
        """
        definition = self.registry.get(workflow_name)
        if definition is None:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        # Create instance
        instance = WorkflowInstance(
            workflow_name=workflow_name,
            state=WorkflowState.RUNNING,
            correlation_id=input_data.get("correlation_id", ""),
            created_at=datetime.now(CST).isoformat(),
        )

        # Emit: workflow.created
        evt_created = create_event(
            source="workflow",
            event_type=WorkflowEventType.CREATED,
            category=EventCategory.WORKFLOW,
            payload={"workflow_name": workflow_name, "input": {k: str(v)[:100] for k, v in input_data.items()}},
            correlation_id=instance.correlation_id,
        )
        self.event_store.append(evt_created)
        instance.event_ids.append(evt_created.event_id)

        # Execute steps
        step_data = dict(input_data)
        for i, step_name in enumerate(definition.steps):
            instance.current_step = step_name
            instance.current_step_index = i

            # Emit: workflow.step.started
            evt_started = create_event(
                source="workflow",
                event_type=WorkflowEventType.STEP_STARTED,
                category=EventCategory.WORKFLOW,
                payload={"step": step_name, "step_index": i},
                correlation_id=instance.correlation_id,
                causation_id=instance.event_ids[-1] if instance.event_ids else "",
            )
            self.event_store.append(evt_started)
            instance.event_ids.append(evt_started.event_id)

            # Execute step
            executor = self._step_executors.get(step_name)
            if executor is None:
                instance.state = WorkflowState.FAILED
                instance.completed_at = datetime.now(CST).isoformat()
                self._emit_failed(instance, f"No executor for step: {step_name}")
                return instance

            try:
                step_result = await executor(step_data, instance)
                step_data.update(step_result)
                instance.step_results[step_name] = step_result
            except Exception as exc:
                instance.state = WorkflowState.FAILED
                instance.completed_at = datetime.now(CST).isoformat()
                instance.step_results["_error"] = str(exc)
                instance.step_results["_failed_at"] = step_name
                self._emit_failed(instance, str(exc))
                return instance

            # Emit: workflow.step.completed
            evt_completed = create_event(
                source="workflow",
                event_type=WorkflowEventType.STEP_COMPLETED,
                category=EventCategory.WORKFLOW,
                payload={"step": step_name, "step_index": i},
                correlation_id=instance.correlation_id,
                causation_id=instance.event_ids[-1],
            )
            self.event_store.append(evt_completed)
            instance.event_ids.append(evt_completed.event_id)

        # Complete
        instance.state = WorkflowState.COMPLETED
        instance.completed_at = datetime.now(CST).isoformat()
        instance.result = step_data

        evt_completed = create_event(
            source="workflow",
            event_type=WorkflowEventType.COMPLETED,
            category=EventCategory.WORKFLOW,
            payload={"workflow_name": workflow_name, "step_count": len(definition.steps)},
            correlation_id=instance.correlation_id,
            causation_id=instance.event_ids[-1] if instance.event_ids else "",
        )
        self.event_store.append(evt_completed)
        instance.event_ids.append(evt_completed.event_id)

        return instance

    def _emit_failed(self, instance: WorkflowInstance, reason: str):
        evt_failed = create_event(
            source="workflow",
            event_type=WorkflowEventType.FAILED,
            category=EventCategory.WORKFLOW,
            payload={"reason": reason, "failed_at_step": instance.current_step},
            correlation_id=instance.correlation_id,
            causation_id=instance.event_ids[-1] if instance.event_ids else "",
        )
        self.event_store.append(evt_failed)
        instance.event_ids.append(evt_failed.event_id)


__all__ = ["WorkflowRuntime"]

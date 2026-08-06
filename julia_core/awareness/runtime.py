"""M3.0 Awareness Runtime — event → workflow dispatch.

ADR-028 Section 3: Receives ObservationEvents, routes significant ones
to ObservationWorkflows. Uses WorkflowRuntime from R1.

This is the bridge between "world changed" and "Julia noticed".
"""

from __future__ import annotations

from dataclasses import dataclass

from julia_core.awareness.models import ObservationEvent
from julia_core.awareness.router import ObservationRouter, SignificanceResult
from julia_core.events.models import EventCategory, create_event
from julia_core.events.store import EventStore, get_event_store
from julia_core.workflow.models import WorkflowInstance
from julia_core.workflow.runtime import WorkflowRuntime


class AwarenessRuntime:
    """Receives ObservationEvents → evaluates significance → dispatches workflows.

    This is the M3.0 skeleton. It does NOT connect to ai_theme_app.
    It proves the event → workflow → artifact chain with synthetic events.
    """

    def __init__(
        self,
        router: ObservationRouter | None = None,
        workflow_runtime: WorkflowRuntime | None = None,
        event_store: EventStore | None = None,
    ):
        self.router = router or ObservationRouter()
        self.workflow_runtime = workflow_runtime
        self.event_store = event_store or get_event_store()

    async def process(self, event: ObservationEvent) -> AwarenessResult:
        """Process an observation event through the full pipeline.

        1. Emit observation event to EventStore
        2. Evaluate significance
        3. If significant: dispatch to workflow
        4. Return AwarenessResult with trace
        """
        # Step 1: Record the observation
        evt = create_event(
            source=event.source,
            event_type=event.event_type,
            category=EventCategory.WORKFLOW,
            payload={
                "observation_id": event.observation_id,
                "subject": event.subject,
                "change_type": event.change_type,
                "delta": event.delta,
            },
            correlation_id=event.correlation_id,
        )
        self.event_store.append(evt)

        # Step 2: Significance check (NO LLM)
        significance = self.router.evaluate(event)

        if not significance.significant:
            return AwarenessResult(
                observation_id=event.observation_id,
                significant=False,
                reason=significance.reason,
                event_id=evt.event_id,
            )

        # Step 3: Dispatch to workflow
        workflow_result = None
        if self.workflow_runtime:
            workflow_result = await self.workflow_runtime.execute(
                "observation.market",
                {
                    "observation_id": event.observation_id,
                    "subject": event.subject,
                    "change_type": event.change_type,
                    "delta": event.delta,
                    "source": event.source,
                    "correlation_id": event.correlation_id,
                },
            )

        return AwarenessResult(
            observation_id=event.observation_id,
            significant=True,
            reason=significance.reason,
            event_id=evt.event_id,
            workflow_instance=workflow_result,
        )


@dataclass
class AwarenessResult:
    """Outcome of processing an ObservationEvent."""
    observation_id: str
    significant: bool
    reason: str
    event_id: str = ""
    workflow_instance: WorkflowInstance | None = None


__all__ = ["AwarenessRuntime", "AwarenessResult"]

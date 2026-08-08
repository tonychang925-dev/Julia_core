"""M3.3.0 Research Workflow Bridge — CognitiveLoopOrchestrator → WorkflowRuntime.

Plugs the autonomous recursive research loop into Julia's WorkflowRuntime.
Follows the same pattern as WorkflowBridge (R1.1).

Workflow: research.cognitive_loop
  Steps:
    1. research.initialize   — validate subject, as_of, create orchestrator config
    2. research.execute_loop — orchestrator.run(subject) → CognitiveLoopResult
    3. research.conclude     — extract PostResearchConclusion, record EvidenceLedger
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from julia_core.capability.financial.research.orchestrator import (
    CognitiveLoopConfig,
    CognitiveLoopOrchestrator,
    CognitiveLoopResult,
    ConstraintViolation,
)
from julia_core.events.models import (
    EventCategory,
    WorkflowEventType,
    create_event,
)
from julia_core.events.store import get_event_store
from julia_core.workflow.models import (
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowState,
)
from julia_core.workflow.registry import WorkflowRegistry
from julia_core.workflow.runtime import WorkflowRuntime

CST = timezone(timedelta(hours=8))


# ── Workflow Definition ───────────────────────────────────────────────────────

RESEARCH_COGNITIVE_LOOP_WORKFLOW = WorkflowDefinition(
    name="research.cognitive_loop",
    description="Autonomous recursive research: blind judgment → probe execution → hypothesis evaluation → transition detection → recursive handoff → calibrated conclusion",
    steps=(
        "research.initialize",
        "research.execute_loop",
        "research.conclude",
    ),
    trigger_events=("research.subject.submitted",),
    timeout_seconds=300,  # Multi-round research may take longer
    version="1.0",
)


def create_research_registry() -> WorkflowRegistry:
    """Create a registry with the research workflow registered."""
    registry = WorkflowRegistry()
    registry.register(RESEARCH_COGNITIVE_LOOP_WORKFLOW)
    return registry


# ── Bridge ────────────────────────────────────────────────────────────────────

class ResearchWorkflowBridge:
    """Bridges CognitiveLoopOrchestrator to WorkflowRuntime.

    Usage:
        bridge = ResearchWorkflowBridge(capability_bridge.manager, card_dir="/path/to/cards")
        instance = await bridge.execute_research({
            "subject_key": "9010270",
            "trade_date": "2026-07-14",
            "leader_code": "601969",
        })
    """

    def __init__(
        self,
        capability_manager,
        card_dir: str = "",
        config: CognitiveLoopConfig | None = None,
    ):
        self.capability_manager = capability_manager
        self.card_dir = card_dir
        self.config = config

        self.registry = WorkflowRegistry()
        self.registry.register(RESEARCH_COGNITIVE_LOOP_WORKFLOW)

        self.runtime = WorkflowRuntime(
            self.registry,
            capability_manager,
        )
        self._register_step_executors()

    def _register_step_executors(self):
        """Register the 3 step executors for research.cognitive_loop."""

        async def research_initialize(data: dict, instance: WorkflowInstance) -> dict:
            """Step 1: research.initialize — validate input, create orchestrator.

            Accepts:
              - subject_key: str (required)
              - trade_date: str (required)
              - leader_code: str
              - subject_name: str
              - max_rounds: int (optional, overrides config)
              - query_budget: int (optional, overrides config)
            """
            subject = {
                "subject_key": data.get("subject_key", ""),
                "trade_date": data.get("trade_date", ""),
                "leader_code": data.get("leader_code", ""),
                "subject_name": data.get("subject_name", ""),
            }

            # Build config — data overrides take precedence
            loop_config = CognitiveLoopConfig(
                max_rounds=data.get("max_rounds", (self.config.max_rounds if self.config else 3)),
                query_budget=data.get("query_budget", (self.config.query_budget if self.config else 20)),
                as_of=subject["trade_date"],
                initial_card=data.get("initial_card", ""),
            )

            orchestrator = CognitiveLoopOrchestrator(
                capability_manager=self.capability_manager,
                card_dir=self.card_dir,
                config=loop_config,
            )

            # Store orchestrator and subject for the next step
            data["_orchestrator"] = orchestrator
            data["_subject"] = subject

            return {
                "research_initialized": True,
                "subject_key": subject["subject_key"],
                "trade_date": subject["trade_date"],
                "config_max_rounds": loop_config.max_rounds,
                "config_query_budget": loop_config.query_budget,
            }

        async def research_execute_loop(data: dict, instance: WorkflowInstance) -> dict:
            """Step 2: research.execute_loop — run the orchestrator."""
            orchestrator: CognitiveLoopOrchestrator = data.get("_orchestrator")
            subject: dict = data.get("_subject", {})

            if orchestrator is None:
                raise ValueError("research_initialize must run before research_execute_loop")

            result: CognitiveLoopResult = await orchestrator.run(subject)

            # Emit events for each round
            event_store = get_event_store()
            for round_rec in result.rounds:
                event_store.append(create_event(
                    source="research",
                    event_type=WorkflowEventType.STEP_COMPLETED,
                    category=EventCategory.WORKFLOW,
                    payload={
                        "round": round_rec.round_index,
                        "research_case_id": round_rec.research_case_id,
                        "parent_case_id": round_rec.parent_case_id,
                        "trigger_transition": round_rec.trigger_transition,
                        "hypotheses": {
                            k: v.status for k, v in round_rec.hypothesis_evaluations.items()
                        },
                        "stop_reason": round_rec.stop_reason or "continuing",
                    },
                    correlation_id=instance.correlation_id,
                    causation_id=instance.event_ids[-1] if instance.event_ids else "",
                ))

            return {
                "loop_completed": True,
                "total_rounds": len(result.rounds),
                "stop_reason": result.stop_reason,
                "total_queries": result.total_queries,
                "lineage": result.lineage,
                "final_conclusion": result.final_conclusion,
                "errors": result.errors,
                # Pass full result for conclude step
                "_cognitive_loop_result": result,
            }

        async def research_conclude(data: dict, instance: WorkflowInstance) -> dict:
            """Step 3: research.conclude — finalize with PostResearchConclusion."""
            result: CognitiveLoopResult | None = data.get("_cognitive_loop_result")
            if result is None:
                return {"concluded": False, "reason": "no loop result"}

            conclusion = result.final_conclusion

            # Build PostResearchConclusion compatible with frozen trace format
            post_research = {
                "strategy_state": conclusion.get("primary_state", "unknown"),
                "state_type": conclusion.get("state_type", "inconclusive"),
                "rounds_executed": conclusion.get("rounds_executed", 0),
                "stop_reason": conclusion.get("stop_reason", ""),
                "total_queries": conclusion.get("total_queries", 0),
                "lineage": conclusion.get("lineage", []),
            }

            if conclusion.get("state_type") == "partial":
                post_research["_note"] = (
                    "Calibrated abstention: evidence supports some hypotheses but "
                    "insufficient to confirm. Julia refuses to overclaim."
                )

            # Emit completion event
            event_store = get_event_store()
            event_store.append(create_event(
                source="research",
                event_type=WorkflowEventType.COMPLETED,
                category=EventCategory.WORKFLOW,
                payload=post_research,
                correlation_id=instance.correlation_id,
                causation_id=instance.event_ids[-1] if instance.event_ids else "",
            ))

            return {
                "concluded": True,
                "post_research_conclusion": post_research,
                "evidence_ledger_size": len(result.evidence_ledger),
            }

        # Register all 3 steps
        self.runtime.register_step("research.initialize", research_initialize)
        self.runtime.register_step("research.execute_loop", research_execute_loop)
        self.runtime.register_step("research.conclude", research_conclude)

    async def execute_research(
        self, subject: dict, correlation_id: str = ""
    ) -> WorkflowInstance:
        """Execute research.cognitive_loop through WorkflowRuntime.

        The WorkflowRuntime owns lifecycle, emits events, and returns
        a completed WorkflowInstance with full audit trail.

        Args:
            subject: dict with subject_key, trade_date, leader_code, subject_name
            correlation_id: optional correlation ID for event linking

        Returns:
            WorkflowInstance with step_results containing CognitiveLoopResult
        """
        return await self.runtime.execute("research.cognitive_loop", {
            "subject_key": subject.get("subject_key", ""),
            "trade_date": subject.get("trade_date", ""),
            "leader_code": subject.get("leader_code", ""),
            "subject_name": subject.get("subject_name", ""),
            "max_rounds": subject.get("max_rounds", None),
            "query_budget": subject.get("query_budget", None),
            "initial_card": subject.get("initial_card", ""),
            "correlation_id": correlation_id,
        })


__all__ = [
    "RESEARCH_COGNITIVE_LOOP_WORKFLOW",
    "ResearchWorkflowBridge",
    "create_research_registry",
]

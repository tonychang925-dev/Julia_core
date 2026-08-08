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
            # Derive market_stage from blind_judgment if not explicitly given
            blind = data.get("blind_judgment")
            blind_market_stage = (blind or {}).get("market_stage", "") if isinstance(blind, dict) else ""
            market_stage = data.get("market_stage") or blind_market_stage
            if blind_market_stage and data.get("market_stage") and data.get("market_stage") != blind_market_stage:
                raise ValueError(
                    f"market_stage={data['market_stage']} conflicts with "
                    f"blind_judgment.market_stage={blind_market_stage}"
                )

            subject = {
                "subject_key": data.get("subject_key", ""),
                "trade_date": data.get("trade_date", ""),
                "leader_code": data.get("leader_code", ""),
                "subject_name": data.get("subject_name", ""),
                "market_stage": market_stage,
                "initial_card": data.get("initial_card") or "",
            }

            # Build config — explicit None checks (P0-1: Python .get() uses
            # default only when key is absent, not when value is None)
            default_max_rounds = self.config.max_rounds if self.config else 2
            default_query_budget = self.config.query_budget if self.config else 20

            max_rounds = data.get("max_rounds")
            if max_rounds is None:
                max_rounds = default_max_rounds
            query_budget = data.get("query_budget")
            if query_budget is None:
                query_budget = default_query_budget

            # P0: as_of MUST be a full timezone-aware timestamp.
            # trade_date is the market session identity, NOT the knowledge cutoff.
            # Date-only strings silently become midnight +08:00 and will
            # incorrectly reject same-day evidence at 10:00+08.
            as_of = data.get("as_of") or ""
            if not as_of or "T" not in str(as_of):
                raise ConstraintViolation(
                    "research.as_of must be a full ISO-8601 timezone-aware "
                    "timestamp (e.g. 2026-07-14T15:30:00+08:00). "
                    "trade_date is not a substitute for as_of."
                )

            loop_config = CognitiveLoopConfig(
                max_rounds=max_rounds,
                query_budget=query_budget,
                as_of=as_of,
                initial_card=data.get("initial_card") or "",
            )

            orchestrator = CognitiveLoopOrchestrator(
                capability_manager=self.capability_manager,
                card_dir=self.card_dir,
                config=loop_config,
            )

            # Set blind judgment for immutability enforcement (P1: production path)
            blind = data.get("blind_judgment")
            if blind and isinstance(blind, dict):
                orchestrator.set_blind_judgment(blind)

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
                "queries_executed": result.queries_executed,
                "probes_blocked_by_budget": result.probes_blocked_by_budget,
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
                "queries_executed": conclusion.get("queries_executed", 0),
                "probes_blocked_by_budget": conclusion.get("probes_blocked_by_budget", 0),
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
                "evidence_ledger": [
                    {
                        "probe_id": item.probe_id,
                        "requirement_id": item.requirement_id,
                        "status": item.status,
                        "derived_value": str(item.derived_value)[:100] if item.derived_value is not None else None,
                        "source_kind": (getattr(item, 'provenance', {}) or {}).get("source_kind", ""),
                        "capability_request_id": item.capability_request_id,
                        "available_at": (getattr(item, 'provenance', {}) or {}).get("available_at", ""),
                        "observed_at": (getattr(item, 'provenance', {}) or {}).get("observed_at", ""),
                        "effective_at": (getattr(item, 'provenance', {}) or {}).get("effective_at", ""),
                        "requested_as_of": (getattr(item, 'provenance', {}) or {}).get("requested_as_of", ""),
                        "recorded_at": datetime.now(CST).isoformat(),
                    }
                    for item in result.evidence_ledger
                ],
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
        input_data: dict[str, Any] = {
            "subject_key": subject.get("subject_key", ""),
            "trade_date": subject.get("trade_date", ""),
            "leader_code": subject.get("leader_code", ""),
            "subject_name": subject.get("subject_name", ""),
            "initial_card": subject.get("initial_card", ""),
            "correlation_id": correlation_id,
        }
        # Only include optional keys when they have non-None values
        if subject.get("max_rounds") is not None:
            input_data["max_rounds"] = subject["max_rounds"]
        if subject.get("query_budget") is not None:
            input_data["query_budget"] = subject["query_budget"]
        if subject.get("market_stage") is not None:
            input_data["market_stage"] = subject["market_stage"]

        # P0: propagate blind_judgment for immutability enforcement
        blind = subject.get("blind_judgment")
        if blind is not None and isinstance(blind, dict):
            input_data["blind_judgment"] = blind
            # Derive market_stage from blind_judgment if not explicitly passed
            if not input_data.get("market_stage") and blind.get("market_stage"):
                input_data["market_stage"] = blind["market_stage"]

        # P0: propagate full as_of timestamp for anti-hindsight gate
        as_of = subject.get("as_of")
        if as_of is not None and as_of:
            input_data["as_of"] = str(as_of)

        return await self.runtime.execute("research.cognitive_loop", input_data)


__all__ = [
    "RESEARCH_COGNITIVE_LOOP_WORKFLOW",
    "ResearchWorkflowBridge",
    "create_research_registry",
]

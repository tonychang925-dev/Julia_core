"""M3.0 Observation Workflow Models."""

from julia_core.workflow.models import WorkflowDefinition

# ── Market Observation Workflow ──────────────────────────────────────────────

MARKET_OBSERVATION_WORKFLOW = WorkflowDefinition(
    name="observation.market",
    description="Market observation: world change → evidence → judgment → artifact",
    steps=(
        "observe.collect_evidence",
        "observe.build_context",
        "observe.evaluate_significance",
        "observe.generate_artifact",
        "observe.store_experience",
    ),
    trigger_events=("world.market.changed",),
    timeout_seconds=120,
    version="1.0",
)

__all__ = ["MARKET_OBSERVATION_WORKFLOW"]

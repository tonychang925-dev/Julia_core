"""M3.0 Observation Workflow Registry."""

from julia_core.workflow.registry import WorkflowRegistry
from julia_core.workflow.observation.models import MARKET_OBSERVATION_WORKFLOW


def register_observation_workflows(registry: WorkflowRegistry):
    """Register all observation workflows."""
    registry.register(MARKET_OBSERVATION_WORKFLOW)


def create_observation_registry() -> WorkflowRegistry:
    registry = WorkflowRegistry()
    register_observation_workflows(registry)
    return registry


__all__ = ["register_observation_workflows", "create_observation_registry"]

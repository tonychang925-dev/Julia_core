"""Capability registration for research.event.enrich."""

from __future__ import annotations

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityStatus,
)
from julia_core.capability.policy import PermissionPolicy, PermissionRule
from julia_core.capability.registry import CapabilityRegistry
from julia_core.research.adapter import (
    RESEARCH_EVENT_ENRICH_CAPABILITY,
    RESEARCH_EVENT_ENRICH_SCOPE,
)

RESEARCH_EVENT_ENRICH_PROVIDER = "research_enrichment"


def register_research_event_enrichment(
    registry: CapabilityRegistry,
    policy: PermissionPolicy | None = None,
    *,
    status: CapabilityStatus = CapabilityStatus.REGISTERED,
) -> CapabilityDefinition:
    """Register the read-only research enrichment capability.

    Registration binds no provider and creates no automatic routing.
    """

    definition = CapabilityDefinition(
        name=RESEARCH_EVENT_ENRICH_CAPABILITY,
        description=(
            "Enrich one frozen Market event into separated research semantics "
            "and runtime source-observation evidence."
        ),
        layer=CapabilityLayer.INTELLIGENCE,
        provider=RESEARCH_EVENT_ENRICH_PROVIDER,
        permission_scope=RESEARCH_EVENT_ENRICH_SCOPE,
        input_schema={
            "event": "frozen market.event.read.v1 event object",
            "theme_relations": "frozen market.event.read.v1 relation array",
        },
        status=status,
        schema_version="1.0",
    )
    registry.register_definition(definition)
    if policy is not None:
        policy.add_rule(PermissionRule(
            scope=RESEARCH_EVENT_ENRICH_SCOPE,
            allow=True,
            reason="Read-only Market event research enrichment",
        ))
    return definition


__all__ = [
    "RESEARCH_EVENT_ENRICH_PROVIDER",
    "register_research_event_enrichment",
]

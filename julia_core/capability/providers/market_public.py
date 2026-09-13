"""Core-owned semantic definitions for Market public capabilities."""

from __future__ import annotations

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityStatus,
)
from julia_core.capability.registry import CapabilityRegistry


MARKET_PUBLIC_PROVIDER = "market"
MARKET_PUBLIC_SCOPE = "market.observe"
MARKET_PUBLIC_SCHEMA_VERSION = "1.0"
MARKET_PUBLIC_CAPABILITY_IDS = (
    "market.event.resolve",
    "market.event.read",
    "market.product.read",
)

_INPUT_SCHEMAS = {
    "market.event.resolve": {"request": "Market event resolution request"},
    "market.event.read": {
        "event_id": "Market event identifier",
        "revision_id": "Market event revision identifier",
    },
    "market.product.read": {
        "product_id": "Market product identifier",
        "revision_id": "Market product revision identifier",
    },
}

_DESCRIPTIONS = {
    "market.event.resolve": "Resolve a governed Market event request",
    "market.event.read": "Read a governed Market event",
    "market.product.read": "Read a governed Market product",
}


def make_market_public_definitions(
    *, status: CapabilityStatus = CapabilityStatus.REGISTERED
) -> tuple[CapabilityDefinition, ...]:
    return tuple(
        CapabilityDefinition(
            name=capability_id,
            description=_DESCRIPTIONS[capability_id],
            layer=CapabilityLayer.INTELLIGENCE,
            provider=MARKET_PUBLIC_PROVIDER,
            permission_scope=MARKET_PUBLIC_SCOPE,
            input_schema=dict(_INPUT_SCHEMAS[capability_id]),
            status=status,
            schema_version=MARKET_PUBLIC_SCHEMA_VERSION,
        )
        for capability_id in MARKET_PUBLIC_CAPABILITY_IDS
    )


def register_market_public_capabilities(
    registry: CapabilityRegistry,
    *,
    status: CapabilityStatus = CapabilityStatus.REGISTERED,
) -> tuple[CapabilityDefinition, ...]:
    definitions = make_market_public_definitions(status=status)
    for definition in definitions:
        registry.register_definition(definition)
    return definitions


__all__ = [
    "MARKET_PUBLIC_CAPABILITY_IDS",
    "MARKET_PUBLIC_PROVIDER",
    "MARKET_PUBLIC_SCOPE",
    "MARKET_PUBLIC_SCHEMA_VERSION",
    "make_market_public_definitions",
    "register_market_public_capabilities",
]

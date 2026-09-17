"""Mechanical Core binding for the Market public boundary.

This module adapts Core's generic ``CapabilityRequest`` to the public request
shapes owned/exported by ``market_public``.  It deliberately does not import or
inspect Market private repositories, DB sessions, MCP tools, routes, or other
implementation details.

A valid Market public result is an execution success from Core's point of view,
even when the Market-owned ``operation_status`` inside that result is FAILURE.
That keeps Core execution truth separate from Market domain-result truth.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Callable, Mapping

from julia_core.capability.models import (
    CapabilityRequest,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)


RequestBuilder = Callable[..., Any]


class MarketPublicProviderAdapter:
    """Adapt Core capability requests to one Market public provider object.

    ``public_provider`` is the object returned by Market's public factory.  The
    adapter knows only the public ``execute(capability, request, ...)`` shape.
    ``request_builders`` are the Market-exported public request types keyed by
    capability id.
    """

    def __init__(
        self,
        public_provider: Any,
        request_builders: Mapping[str, RequestBuilder],
    ) -> None:
        if not callable(getattr(public_provider, "execute", None)):
            raise TypeError("Market public provider must implement execute()")
        self._public_provider = public_provider
        self._request_builders = dict(request_builders)

    @classmethod
    def from_installed_market_public(
        cls,
        *,
        database_url: str | None = None,
        public_provider: Any | None = None,
    ) -> "MarketPublicProviderAdapter":
        """Bind to the installed Market *public* package only.

        Market owns construction through ``MarketPublicFactory``.  Core merely
        calls that public factory when no already-constructed public provider is
        supplied, then binds the resulting public provider mechanically.
        """
        from market_public import (
            EventReadRequest,
            EventResolveRequest,
            MarketPublicFactory,
            ProductReadRequest,
        )

        provider = public_provider
        if provider is None:
            provider = MarketPublicFactory.create(database_url=database_url)

        return cls(
            provider,
            {
                "market.event.resolve": EventResolveRequest,
                "market.event.read": EventReadRequest,
                "market.product.read": ProductReadRequest,
            },
        )

    async def health(self) -> tuple[bool, str]:
        """Report binding health, not Market-domain data availability.

        The current Market public provider represents dependency/data failures
        inside ``MarketResultEnvelope``.  Core must not pre-empt that domain
        result by probing Market private dependencies itself.
        """
        return True, "Market public provider bound"

    async def execute(self, request: CapabilityRequest) -> ProviderExecutionOutcome:
        builder = self._request_builders.get(request.capability_id)
        if builder is None:
            raise ValueError(f"unsupported Market public capability: {request.capability_id}")

        public_request = self._build_public_request(builder, request.arguments)
        public_result = await self._public_provider.execute(
            request.capability_id,
            public_request,
            request_id=request.capability_request_id,
            correlation_id=request.correlation_id or None,
        )

        # A returned Market envelope is a successfully executed Core tool call.
        # Its Market-owned operation_status/data_state/failures remain inside
        # structured_output unchanged in meaning.
        return ProviderExecutionOutcome(
            status=ToolResultStatus.SUCCESS,
            structured_output=_to_plain_mapping(public_result),
            side_effect_state=SideEffectState.NONE,
        )

    @staticmethod
    def _build_public_request(builder: RequestBuilder, arguments: dict[str, Any]) -> Any:
        """Adapt argument shape without taking ownership of Market validation.

        If a public request type cannot be constructed, pass the raw mapping to
        the Market public provider.  The Market provider then owns the canonical
        contract-mismatch result instead of Core manufacturing domain semantics.
        """
        try:
            return builder(**dict(arguments))
        except (TypeError, ValueError):
            return copy.deepcopy(dict(arguments))


def _to_plain_mapping(value: Any) -> dict[str, Any]:
    """Serialize a public result structurally without semantic remapping."""
    if is_dataclass(value):
        raw = asdict(value)
    elif isinstance(value, Mapping):
        raw = copy.deepcopy(dict(value))
    else:
        raise TypeError("Market public provider must return a dataclass or mapping")
    return _plain(raw)


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return tuple(_plain(v) for v in value)
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return copy.deepcopy(value)


__all__ = ["MarketPublicProviderAdapter"]

"""Mechanical Core binding for the Market public boundary.

This module adapts Core's generic ``CapabilityRequest`` to the public request
shapes owned/exported by ``market_public``. It deliberately does not import or
inspect Market private repositories, DB sessions, MCP tools, routes, factories,
or other composition details.

A valid Market public result is an execution success from Core's point of view,
even when the Market-owned ``operation_status`` inside that result is FAILURE.
That keeps Core execution truth separate from Market domain-result truth.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from enum import Enum
import inspect
from typing import Any, Callable, Mapping

from julia_core.capability.models import (
    CapabilityRequest,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)


RequestBuilder = Callable[..., Any]


class MarketPublicProviderAdapter:
    """Bind Core mechanically to one already-constructed Market public provider.

    The application/runtime composition root is responsible for asking Market
    to construct/configure its public provider. Core receives that public object
    and binds it. Core does not construct Market, choose Market configuration,
    or know Market private implementation.

    ``request_builders`` may be supplied by the composition root. When omitted,
    Core loads only the Market-exported public request contract types.
    """

    def __init__(
        self,
        public_provider: Any,
        request_builders: Mapping[str, RequestBuilder] | None = None,
    ) -> None:
        if not callable(getattr(public_provider, "execute", None)):
            raise TypeError("Market public provider must implement execute()")
        self._public_provider = public_provider
        self._request_builders = dict(
            request_builders
            if request_builders is not None
            else _load_public_request_builders()
        )

    @property
    def effective_capability_ids(self) -> frozenset[str]:
        """Return the exact capability IDs backed by effective request builders."""
        return frozenset(self._request_builders)

    def supports_capability(self, capability_id: str) -> bool:
        """Return whether this bound adapter can construct the public request."""
        return capability_id in self._request_builders

    async def health(self) -> tuple[bool, str]:
        """Report binding health, not Market-domain data availability.

        The current Market public provider represents dependency/data failures
        inside ``MarketResultEnvelope``. Core must not pre-empt that domain
        result by probing Market private dependencies itself.
        """
        return True, "Market public provider bound"

    async def close(self) -> None:
        """Forward lifecycle ownership to the already-bound Market provider."""
        close = getattr(self._public_provider, "close", None)
        if close is None:
            return
        result = close()
        if inspect.isawaitable(result):
            await result

    async def execute(self, request: CapabilityRequest) -> ProviderExecutionOutcome:
        builder = self._request_builders.get(request.capability_id)
        if builder is None:
            raise ValueError(
                f"unsupported Market public capability: {request.capability_id}"
            )

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
    def _build_public_request(
        builder: RequestBuilder, arguments: dict[str, Any]
    ) -> Any:
        """Adapt argument shape without taking ownership of Market validation.

        If a public request type cannot be constructed, pass the raw mapping to
        the Market public provider. The Market provider then owns the canonical
        contract-mismatch result instead of Core manufacturing domain semantics.
        """
        try:
            return builder(**dict(arguments))
        except (TypeError, ValueError):
            return copy.deepcopy(dict(arguments))


def _load_public_request_builders() -> dict[str, RequestBuilder]:
    """Load only request types exported by the Market public contract package."""
    from importlib import import_module

    market_public = import_module("market_public")
    EventResolveRequest = market_public.EventResolveRequest
    EventReadRequest = market_public.EventReadRequest
    ProductReadRequest = market_public.ProductReadRequest
    ProductLinkageReadRequest = getattr(
        market_public,
        "ProductLinkageReadRequest",
        None,
    )
    MarketStateReadRequest = getattr(market_public, "MarketStateReadRequest", None)
    StockQuoteReadRequest = getattr(market_public, "StockQuoteReadRequest", None)
    MarketAnalysisReadRequest = getattr(
        market_public,
        "MarketAnalysisReadRequest",
        None,
    )

    builders = {
        "market.event.resolve": EventResolveRequest,
        "market.event.read": EventReadRequest,
        "market.product.read": ProductReadRequest,
    }
    if ProductLinkageReadRequest is not None:
        builders["market.product.linkage.read"] = ProductLinkageReadRequest
    if MarketStateReadRequest is not None:
        builders["market.state.read"] = MarketStateReadRequest
    if StockQuoteReadRequest is not None:
        builders["market.stock.quote.read"] = StockQuoteReadRequest
    if MarketAnalysisReadRequest is not None:
        builders["market.analysis.read"] = MarketAnalysisReadRequest
    return builders


def market_public_request_builders() -> dict[str, RequestBuilder]:
    """Expose the public request-builder truth used for capability availability."""
    return _load_public_request_builders()


def market_public_supports_stock_quote() -> bool:
    """Probe only the StockQuoteReadRequest export for catalog availability."""
    from importlib import import_module

    market_public = import_module("market_public")
    return getattr(market_public, "StockQuoteReadRequest", None) is not None


def market_public_supports_analysis() -> bool:
    """Probe only the MarketAnalysisReadRequest export for catalog availability."""
    from importlib import import_module

    market_public = import_module("market_public")
    return getattr(market_public, "MarketAnalysisReadRequest", None) is not None


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


__all__ = [
    "MarketPublicProviderAdapter",
    "market_public_request_builders",
    "market_public_supports_stock_quote",
    "market_public_supports_analysis",
]

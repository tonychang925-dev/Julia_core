"""Context Runtime — bridges Runtime lifecycle with Context OS.

This is the integration point between:
    Runtime → Context Plannner → Context Resolver → Domain Providers

It does NOT:
  - build prompts
  - call language models
  - load domain providers by name (registry is provider-agnostic)
  - reason about which provider is "better"
"""

from __future__ import annotations

from typing import Iterable

from julia_core.context_os.planner import ContextPlanner
from julia_core.context_os.resolver import ContextResolver
from julia_core.context_os.request import ContextRequest
from julia_core.context_os.block import ContextBlock
from julia_core.providers.interface import DomainProvider


class ContextRuntime:
    """Owns the provider-agnostic context resolution pipeline."""

    def __init__(self) -> None:
        self._planner = ContextPlanner()
        self._providers: dict[str, DomainProvider] = {}
        self._resolver = ContextResolver(providers=())

    def register_provider(self, provider: DomainProvider) -> None:
        self._providers[provider.domain] = provider
        self._resolver = ContextResolver(providers=self._providers.values())

    def plan(self, **kwargs) -> ContextRequest:
        return self._planner.plan(**kwargs)

    def resolve(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
        return self._resolver.resolve(request)

    def plan_and_resolve(self, **kwargs) -> tuple[ContextBlock, ...]:
        request = self._planner.plan(**kwargs)
        return self._resolver.resolve(request)

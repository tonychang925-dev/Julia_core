"""Provider-boundary resolver for Context OS skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Protocol

from .block import ContextBlock
from .request import ContextRequest


class _Provider(Protocol):
    domain: str

    def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
        ...


@dataclass(frozen=True, slots=True)
class ContextResolver:
    providers: tuple[_Provider, ...] = field(default_factory=tuple)

    def __init__(self, providers: Iterable[_Provider] = ()) -> None:
        object.__setattr__(self, "providers", tuple(providers))

    def resolve(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
        if request.domain is None:
            return ()
        for provider in self.providers:
            if provider.domain == request.domain:
                return tuple(provider.provide(request))
        return ()

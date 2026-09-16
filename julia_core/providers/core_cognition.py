"""Core-owned cognition provider contract and explicit registry."""

from __future__ import annotations

from typing import Protocol


class CoreCognitionProvider(Protocol):
    """Production cognition provider contract owned by Core."""

    def chat(self, messages: list[dict], *, cognitive_mode: str = "") -> str: ...


_providers: dict[str, CoreCognitionProvider] = {}


def _register_cognition_provider(name: str, provider: CoreCognitionProvider) -> None:
    """Register an explicitly configured real provider at Core composition time."""
    if not name or provider is None:
        raise ValueError("provider registration requires a name and provider")
    _providers[name] = provider


def _get_cognition_provider(name: str = "production") -> CoreCognitionProvider | None:
    """Resolve only an explicitly registered provider; never synthesize one."""
    return _providers.get(name)


__all__ = ["CoreCognitionProvider"]

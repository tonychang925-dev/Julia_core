"""Core-owned cognition provider contract and explicit registry."""

from __future__ import annotations

import os
import threading
from typing import Protocol


class CoreCognitionProvider(Protocol):
    """Production cognition provider contract owned by Core."""

    def chat(self, messages: list[dict], *, cognitive_mode: str = "") -> str: ...


_providers: dict[str, CoreCognitionProvider] = {}
_registration_lock = threading.RLock()
_production_initialization_attempted = False


class CoreCognitionProviderUnavailable(RuntimeError):
    """The configured real cognition provider cannot be made available."""


def _register_cognition_provider(name: str, provider: CoreCognitionProvider) -> None:
    """Register an explicitly configured real provider at Core composition time."""
    if not name or provider is None:
        raise ValueError("provider registration requires a name and provider")
    with _registration_lock:
        existing = _providers.get(name)
        if existing is not None and existing is not provider:
            raise RuntimeError(f"cognition provider namespace is already bound: {name}")
        _providers[name] = provider


def _get_cognition_provider(name: str = "production") -> CoreCognitionProvider | None:
    """Resolve only an explicitly registered provider; never synthesize one."""
    return _providers.get(name)


def initialize_production_cognition() -> CoreCognitionProvider:
    """Initialize the one configured real production cognition provider.

    Initialization is process-global, idempotent, and fail-closed. It is not a
    request-facing provider factory and never performs semantic selection.
    """
    global _production_initialization_attempted

    with _registration_lock:
        existing = _providers.get("production")
        if existing is not None:
            return existing
        if _production_initialization_attempted:
            raise CoreCognitionProviderUnavailable(
                "production cognition initialization already failed"
            )
        try:
            if not os.environ.get("DEEPSEEK_API_KEY"):
                raise CoreCognitionProviderUnavailable(
                    "DEEPSEEK_API_KEY is not configured; real cognition is unavailable"
                )

            from .deepseek import DeepSeekCognitionProvider

            provider = DeepSeekCognitionProvider()
            _register_cognition_provider("production", provider)
            return provider
        except Exception:
            _production_initialization_attempted = True
            raise


__all__ = ["CoreCognitionProvider", "CoreCognitionProviderUnavailable"]

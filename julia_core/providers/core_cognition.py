"""Core-owned baseline cognition provider for the public application seam."""

from __future__ import annotations

from julia_core.providers.streaming import DeterministicProviderStreamAdapter, ProviderStreamRequest


class CoreCognitionProvider:
    """Package-local chat provider; no Assistant checkout or import is needed."""

    def __init__(self) -> None:
        self._adapter = DeterministicProviderStreamAdapter()

    def chat(self, messages: list[dict], *, cognitive_mode: str = "") -> str:
        request = ProviderStreamRequest(
            messages=tuple(messages),
            stream=False,
            model="core-cognition",
            provider_name="core-cognition",
            trace={"cognitive_mode": cognitive_mode},
        )
        return self._adapter._answer(request)


__all__ = ["CoreCognitionProvider"]

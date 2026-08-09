"""Julia Agent Provider — Julia persona as a Capability Provider.

Implements CapabilityProvider protocol for Julia persona capabilities.
Wraps Julia Agent HTTP sidecar results in CapabilityResult.

This provider does NOT:
  - Own Julia's identity
  - Store Julia's memory
  - Define Julia's personality

Those belong to Julia Agent (the sidecar). julia_core consumes via this provider.

ADR-026 P4: Provider supplies capability, not cognition.
The Julia Agent IS the identity. This provider is just the transport.
"""

from __future__ import annotations

from julia_core.capability.models import CapabilityRequest
from julia_core.capability.providers.julia_agent.adapter import JuliaAgentAdapter


class JuliaAgentProvider:
    """Julia Persona Provider — routes chat/identity/memory requests to Julia Agent.

    Three capabilities:
      julia.chat           — Get a conversational response from Julia
      julia.identity       — Get Julia's current identity snapshot
      julia.memory.search  — Search Julia's diary and memory files
    """

    def __init__(self, adapter: JuliaAgentAdapter | None = None):
        self.adapter = adapter or JuliaAgentAdapter()

    # ── CapabilityProvider Protocol ────────────────────────────────────

    async def execute(self, request: CapabilityRequest) -> dict:
        """Execute a Julia persona capability through HTTP adapter."""
        raw = await self.adapter.call(
            request.capability_name,
            request.arguments,
        )

        return {
            "provider": "julia_agent",
            "schema": "JuliaAgent.v1.0",
            "schema_version": "1.0",
            "capability": request.capability_name,
            "data": raw,
            "request_id": request.request_id,
        }

    async def health(self) -> tuple[bool, str]:
        """Check if Julia Agent sidecar is reachable."""
        return await self.adapter.health()


__all__ = ["JuliaAgentProvider"]

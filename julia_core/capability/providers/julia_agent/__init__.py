"""Julia Agent Capability Provider — Julia persona as an External Identity Provider.

Registers 3 Julia persona capabilities:
  julia.chat           → POST /chat       — conversational response from Julia
  julia.identity       → GET  /identity   — current persona identity snapshot
  julia.memory.search  → POST /memory/search — search diary/memory files

Usage:
  from julia_core.capability.providers.julia_agent import (
      JuliaAgentProvider,
      create_julia_agent_provider,
      register_julia_agent_capabilities,
  )

  provider = create_julia_agent_provider("http://127.0.0.1:9020")
  register_julia_agent_capabilities(registry)

Pattern: mirrors ai_theme_app provider exactly. HTTP transport instead of in-process.
"""

from __future__ import annotations

from julia_core.capability.models import CapabilityDefinition, CapabilityLayer, CapabilityStatus
from julia_core.capability.providers.julia_agent.adapter import JuliaAgentAdapter
from julia_core.capability.providers.julia_agent.provider import JuliaAgentProvider
from julia_core.capability.registry import CapabilityRegistry


# ── Julia Agent Capability Registry ──────────────────────────────────────────

JULIA_AGENT_CAPABILITIES: list[dict] = [
    {
        "name": "julia.chat",
        "description": "Chat with Julia (朱婉清) — get a conversational response from the Julia persona with full memory and identity context",
        "layer": CapabilityLayer.PERCEPTION,
        "provider": "julia_agent",
        "permission_scope": "julia.chat",
        "schema_version": "1.0",
    },
    {
        "name": "julia.identity",
        "description": "Get Julia's current identity snapshot — name, mode, memory status, persona continuity check",
        "layer": CapabilityLayer.MEMORY,
        "provider": "julia_agent",
        "permission_scope": "julia.identity",
        "schema_version": "1.0",
    },
    {
        "name": "julia.memory.search",
        "description": "Search Julia's diary and memory files for specific topics, events, or keywords",
        "layer": CapabilityLayer.MEMORY,
        "provider": "julia_agent",
        "permission_scope": "julia.memory",
        "input_schema": {"query": "search query string"},
        "schema_version": "1.0",
    },
]


def register_julia_agent_capabilities(registry: CapabilityRegistry):
    """Register all Julia Agent capabilities in the given registry.

    Call once at startup. Idempotent — re-registering the same name updates it.
    """
    for spec in JULIA_AGENT_CAPABILITIES:
        definition = CapabilityDefinition(
            name=spec["name"],
            description=spec["description"],
            layer=spec["layer"],
            provider=spec["provider"],
            permission_scope=spec["permission_scope"],
            input_schema=spec.get("input_schema", {}),
            adapter="http",
            status=CapabilityStatus.AVAILABLE,
            schema_version=spec["schema_version"],
        )
        registry.register_definition(definition)


def create_julia_agent_provider(base_url: str = "http://127.0.0.1:9020") -> JuliaAgentProvider:
    """Create a JuliaAgentProvider connected to the given sidecar URL."""
    adapter = JuliaAgentAdapter(base_url=base_url)
    return JuliaAgentProvider(adapter)


__all__ = [
    "JuliaAgentProvider",
    "JULIA_AGENT_CAPABILITIES",
    "create_julia_agent_provider",
    "register_julia_agent_capabilities",
]

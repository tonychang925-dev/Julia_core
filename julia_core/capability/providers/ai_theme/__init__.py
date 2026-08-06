"""M1 ai_theme_app Capability Provider — first External Intelligence Provider.

Registers 3 read-only market capabilities (M1 scope):
  market.snapshot.read    → review_market_snapshot()
  market.alert.query      → list_active_alerts()
  market.decision.explain → explain_decision()

Usage:
  from julia_core.capability.providers.ai_theme import (
      AiThemeProvider,
      create_ai_theme_provider,
      register_ai_theme_capabilities,
  )

  provider = create_ai_theme_provider()
  register_ai_theme_capabilities(registry)
"""

from __future__ import annotations

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityStatus,
)
from julia_core.capability.providers.ai_theme.adapter import MCPToolAdapter
from julia_core.capability.providers.ai_theme.provider import (
    AiThemeProvider,
    DECISION_ENVELOPE_VERSION,
)
from julia_core.capability.registry import CapabilityRegistry


# ── M1 Capability Registry ───────────────────────────────────────────────────

AI_THEME_CAPABILITIES: list[dict] = [
    {
        "name": "market.snapshot.read",
        "description": "Read today's market overview — sentiment, active themes, top signals, risk alerts",
        "layer": CapabilityLayer.INTELLIGENCE,
        "provider": "ai_theme_app",
        "permission_scope": "market.observe",
        "schema_version": DECISION_ENVELOPE_VERSION,
    },
    {
        "name": "market.alert.query",
        "description": "Query active market alerts at or above a given alert level (decision/alert/watch/observation)",
        "layer": CapabilityLayer.INTELLIGENCE,
        "provider": "ai_theme_app",
        "permission_scope": "market.observe",
        "input_schema": {"level": "alert level filter — decision, alert, watch, observation"},
        "schema_version": DECISION_ENVELOPE_VERSION,
    },
    {
        "name": "market.decision.explain",
        "description": "Get structured explanation for a market decision — causal chain, evidence, risks, alternatives",
        "layer": CapabilityLayer.INTELLIGENCE,
        "provider": "ai_theme_app",
        "permission_scope": "market.observe",
        "input_schema": {"decision_id": "the DecisionEnvelope ID to explain"},
        "schema_version": DECISION_ENVELOPE_VERSION,
    },
]


def register_ai_theme_capabilities(registry: CapabilityRegistry):
    """Register all M1 ai_theme_app capabilities in the given registry.

    Call once at startup. Idempotent — re-registering the same name updates it.
    """
    for spec in AI_THEME_CAPABILITIES:
        definition = CapabilityDefinition(
            name=spec["name"],
            description=spec["description"],
            layer=spec["layer"],
            provider=spec["provider"],
            permission_scope=spec["permission_scope"],
            input_schema=spec.get("input_schema", {}),
            adapter=spec.get("adapter", "mcp"),
            status=CapabilityStatus.AVAILABLE,
            schema_version=spec["schema_version"],
        )
        registry.register_definition(definition)


def create_ai_theme_provider(endpoint: str | None = None) -> AiThemeProvider:
    """Create an AiThemeProvider with the given MCP endpoint.

    endpoint: optional MCP HTTP endpoint. If None, uses in-process fallback.
    """
    adapter = MCPToolAdapter()
    return AiThemeProvider(adapter)


__all__ = [
    "AiThemeProvider",
    "AI_THEME_CAPABILITIES",
    "DECISION_ENVELOPE_VERSION",
    "create_ai_theme_provider",
    "register_ai_theme_capabilities",
]

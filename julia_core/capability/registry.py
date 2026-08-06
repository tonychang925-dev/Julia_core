"""Julia OS v2.2 Capability Registry — organized by layer, not by tool.

LLM sees: Voice, Vision, Files, Memory, World — not tool_001.
Runtime: registers capabilities, exposes descriptions, executes on demand.

ADR-026 M0.2: Extended to support CapabilityDefinition-based registration.
Keeps backward compatibility with existing Capability/handler-based tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from julia_core.capability.models import CapabilityDefinition, CapabilityLayer as M0Layer, CapabilityStatus


class CapabilityLayer(str, Enum):
    PERCEPTION = "perception"   # senses: voice, vision
    KNOWLEDGE = "knowledge"     # files, search
    MEMORY = "memory"           # diary, long-term
    WORLD = "world"             # weather, time, web
    INTELLIGENCE = "intelligence"  # market, news, analysis (ADR-026)
    ACTION = "action"           # write, execute


@dataclass
class Capability:
    """A capability exposed to the LLM — what it CAN do, not what it MUST do."""
    name: str
    description: str
    layer: CapabilityLayer
    handler: Callable
    parameters: Dict[str, str] = field(default_factory=dict)
    example: str = ""


@dataclass
class CapabilityRegistry:
    """Organized capability registry. LLM sees categories, not raw tools.

    Supports both legacy Capability (handler-based) and ADR-026
    CapabilityDefinition (provider-based) registration.
    """
    capabilities: Dict[str, Capability] = field(default_factory=dict)
    _definitions: Dict[str, CapabilityDefinition] = field(default_factory=dict)

    # ── Legacy: Capability (handler-based) ─────────────────────────────────

    def register(self, cap: Capability):
        self.capabilities[cap.name] = cap

    def execute(self, name: str, **params) -> Optional[str]:
        if name in self.capabilities:
            try:
                return self.capabilities[name].handler(**params)
            except Exception as e:
                return f"[{name}] error: {e}"
        return None

    def get_prompt(self) -> str:
        """Generate organized capability prompt for LLM context."""
        by_layer: Dict[CapabilityLayer, List[Capability]] = {}
        for cap in self.capabilities.values():
            by_layer.setdefault(cap.layer, []).append(cap)

        lines = ["[可用能力]\n你可以使用以下能力来感知和操作世界：\n"]

        layer_names = {
            CapabilityLayer.PERCEPTION: "👁 感知",
            CapabilityLayer.KNOWLEDGE: "📁 文件",
            CapabilityLayer.MEMORY: "📋 记忆",
            CapabilityLayer.WORLD: "🌍 世界",
            CapabilityLayer.INTELLIGENCE: "🧠 情报",
            CapabilityLayer.ACTION: "🔧 行动",
        }

        for layer in CapabilityLayer:
            caps = by_layer.get(layer, [])
            if not caps:
                continue
            lines.append(f"\n### {layer_names.get(layer, layer.value)}")
            for cap in caps:
                lines.append(f"- **{cap.name}**: {cap.description[:120]}")
                if cap.example:
                    lines.append(f"  例: `{cap.example}`")

        lines.append("\n你需要什么能力就用什么。不需要的不用。LLM自有判断。")
        return "\n".join(lines)

    # ── ADR-026: CapabilityDefinition (provider-based) ──────────────────────

    def register_definition(self, definition: CapabilityDefinition):
        """Register a CapabilityDefinition (provider-based capability).

        This is the ADR-026 registration path. Definitions have NO handler —
        execution is routed through CapabilityManager → CapabilityProvider.
        """
        self._definitions[definition.name] = definition

    def get_definition(self, name: str) -> Optional[CapabilityDefinition]:
        """Look up a CapabilityDefinition by name."""
        return self._definitions.get(name)

    def get(self, name: str) -> Optional[CapabilityDefinition]:
        """Alias for get_definition — primary lookup in M0 Manager."""
        return self._definitions.get(name)

    def all_definitions(self) -> list[CapabilityDefinition]:
        """Return all registered CapabilityDefinitions."""
        return list(self._definitions.values())

    def all(self) -> list[CapabilityDefinition]:
        """Alias for all_definitions."""
        return self.all_definitions()

    def by_layer_definition(self, layer: M0Layer) -> list[CapabilityDefinition]:
        """Filter definitions by CapabilityLayer."""
        return [d for d in self._definitions.values() if d.layer == layer]

    def by_layer(self, layer) -> list[CapabilityDefinition]:
        """Filter definitions by layer (accepts M0Layer or legacy CapabilityLayer)."""
        return [d for d in self._definitions.values() if d.layer == layer]

    def by_provider(self, provider: str) -> list[CapabilityDefinition]:
        """Filter definitions by provider name."""
        return [d for d in self._definitions.values() if d.provider == provider]

    def definitions(self) -> list[CapabilityDefinition]:
        """Return all definitions (alias)."""
        return self.all_definitions()

    def list_names(self) -> list[str]:
        """List all registered capability names."""
        return sorted(self._definitions.keys())


# ── Singleton ───────────────────────────────────────────────────────────────

_registry: Optional[CapabilityRegistry] = None


def get_registry() -> CapabilityRegistry:
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry

"""Julia OS v2.2 Capability Registry — organized by layer, not by tool.

LLM sees: Voice, Vision, Files, Memory, World — not tool_001.
Runtime: registers capabilities, exposes descriptions, executes on demand.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class CapabilityLayer(str, Enum):
    PERCEPTION = "perception"   # senses: voice, vision
    KNOWLEDGE = "knowledge"     # files, search
    MEMORY = "memory"           # diary, long-term
    WORLD = "world"             # weather, time, web
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
    """Organized capability registry. LLM sees categories, not raw tools."""

    capabilities: Dict[str, Capability] = field(default_factory=dict)

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


# ── Singleton ───────────────────────────────────────────────────────────────

_registry: Optional[CapabilityRegistry] = None


def get_registry() -> CapabilityRegistry:
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry

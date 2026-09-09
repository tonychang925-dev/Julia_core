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

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer as M0Layer,
    CapabilityManifestEntry,
    CapabilityStatus,
    ManifestAdmission,
)


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


# ── P3-CC I1a: metadata admission + manifest derivation seam ──────────────

_ADMISSION_REASON_SIDE_EFFECT = "unclassified_side_effect"
_ADMISSION_REASON_SENSITIVITY = "unclassified_data_sensitivity"


def metadata_admission_reasons(definition: CapabilityDefinition) -> tuple[str, ...]:
    """Return ALL fail-closed metadata admission reasons for one definition.

    Deterministic order: side-effect first, then data sensitivity. Empty tuple
    means the definition is metadata-admitted. Never silently truncates to a
    single reason; never defaults missing metadata to a safe value.
    """
    reasons: list[str] = []
    if definition.side_effect_class is None:
        reasons.append(_ADMISSION_REASON_SIDE_EFFECT)
    if not str(definition.data_sensitivity or "").strip():
        reasons.append(_ADMISSION_REASON_SENSITIVITY)
    return tuple(reasons)


def project_manifest_entry(
    definition: CapabilityDefinition,
    *,
    availability: CapabilityStatus | None = None,
    permission_requirements: tuple[str, ...] | None = None,
) -> ManifestAdmission:
    """Derive one model-visible CapabilityManifestEntry (fail-closed admission).

    An unclassified definition (missing side_effect_class and/or
    data_sensitivity) is NON_ADMITTED and yields no executable manifest entry.

    ``availability`` defaults to the definition's administrative status
    (Option C conservative base). The final live availability projection
    (provider-bound conjunct) belongs to the later CapabilityFrame path and is
    intentionally NOT implemented here.
    """
    reasons = metadata_admission_reasons(definition)
    if reasons:
        return ManifestAdmission(
            capability_id=definition.name,
            admitted=False,
            reasons=reasons,
            entry=None,
        )
    entry = CapabilityManifestEntry(
        capability_id=definition.name,
        description=definition.description,
        input_schema=dict(definition.input_schema),
        output_schema=dict(definition.output_schema),
        side_effect_class=definition.side_effect_class,
        permission_requirements=(
            tuple(permission_requirements)
            if permission_requirements is not None
            else (definition.permission_scope,)
        ),
        idempotency_support=definition.idempotency_support,
        latency_cost_hints=dict(definition.latency_cost_hints),
        data_sensitivity=definition.data_sensitivity,
        availability=(
            availability if availability is not None else definition.status
        ),
        schema_version=definition.schema_version,
        provenance={
            "source": "capability:registry",
            "definition_ref": definition.name,
        },
    )
    return ManifestAdmission(
        capability_id=definition.name,
        admitted=True,
        reasons=(),
        entry=entry,
    )


# ── Singleton ───────────────────────────────────────────────────────────────

_registry: Optional[CapabilityRegistry] = None


def get_registry() -> CapabilityRegistry:
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry

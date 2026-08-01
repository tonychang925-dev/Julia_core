"""Alignment OS public contracts.

Alignment OS keeps runtime-owned behavior contracts stable across LLM providers.
It stores structured alignment metadata, not product-private persona or memory data.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class AlignmentRequest:
    """Request to resolve provider behavior alignment for one runtime turn."""

    provider: str
    persona: str
    mode: str = "conversation"
    capabilities: tuple[str, ...] = ()
    constraints: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", (self.provider or "unknown").lower())
        object.__setattr__(self, "persona", (self.persona or "agent").lower())
        object.__setattr__(self, "mode", self.mode or "conversation")
        object.__setattr__(self, "capabilities", tuple(self.capabilities or ()))
        object.__setattr__(self, "constraints", MappingProxyType(dict(self.constraints or {})))


@dataclass(frozen=True, slots=True)
class AlignmentContract:
    """Provider-neutral behavior contract owned by runtime/Core."""

    contract_id: str
    mode: str
    domain: str
    principles: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles or ()))
        object.__setattr__(self, "constraints", tuple(self.constraints or ()))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata or {})))

    def render_lines(self) -> str:
        lines = [
            f"Provider-Neutral Behavior Contract: {self.contract_id}",
            f"Cognitive Mode: {self.mode}",
            f"Contract Domain: {self.domain}",
            "This contract is runtime-owned and provider-independent.",
        ]
        if self.principles:
            lines.append("Principles:")
            lines.extend(f"- {item}" for item in self.principles)
        if self.constraints:
            lines.append("Constraints:")
            lines.extend(f"- {item}" for item in self.constraints)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BehaviorConstraint:
    """Generic behavior-boundary constraint.

    Examples:
    - dimension="intimacy", max="L4"
    - dimension="technical_depth", level="expert"
    - dimension="empathy", level="high"

    Core treats dimensions as structured metadata. Product packages define the
    private meaning of product-specific dimensions.
    """

    dimension: str
    max: str | None = None
    level: str | None = None
    value: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata or {})))

    def render_line(self) -> str:
        parts = [f"dimension={self.dimension}"]
        if self.max is not None:
            parts.append(f"max={self.max}")
        if self.level is not None:
            parts.append(f"level={self.level}")
        if self.value is not None:
            parts.append(f"value={self.value}")
        return ", ".join(parts)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProviderBehaviorProfile:
    """Provider-specific expression profile inside Core alignment boundary."""

    profile_id: str
    provider_id: str
    persona_id: str
    domain: str
    strategy: str
    constraints: tuple[BehaviorConstraint, ...] = ()
    behavior_guidance: tuple[str, ...] = ()
    prefer: tuple[str, ...] = ()
    avoid: tuple[str, ...] = ()
    fallback_style: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraints", tuple(self.constraints or ()))
        object.__setattr__(self, "behavior_guidance", tuple(self.behavior_guidance or ()))
        object.__setattr__(self, "prefer", tuple(self.prefer or ()))
        object.__setattr__(self, "avoid", tuple(self.avoid or ()))
        object.__setattr__(self, "fallback_style", tuple(self.fallback_style or ()))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata or {})))

    def render_lines(self) -> str:
        lines = [
            f"Provider Behavioral Alignment: {self.profile_id}",
            f"Provider: {self.provider_id}",
            f"Persona: {self.persona_id}",
            f"Mode Domain: {self.domain}",
            f"Strategy: {self.strategy}",
            "This profile adapts expression only; it cannot change identity, memory authority, action authority, or capability access.",
        ]
        if self.constraints:
            lines.append("Behavior Constraints:")
            lines.extend(f"- {item.render_line()}" for item in self.constraints)
        if self.behavior_guidance:
            lines.append("Behavior Guidance:")
            lines.extend(f"- {item}" for item in self.behavior_guidance)
        if self.prefer:
            lines.append("Prefer:")
            lines.extend(f"- {item}" for item in self.prefer)
        if self.avoid:
            lines.append("Avoid:")
            lines.extend(f"- {item}" for item in self.avoid)
        if self.fallback_style:
            lines.append("Fallback Style:")
            lines.extend(f"- {item}" for item in self.fallback_style)
        return "\n".join(lines)

    @property
    def max_intimacy_level(self) -> str:
        """Compatibility helper derived from generic constraints, not a core field."""
        for constraint in self.constraints:
            if constraint.dimension == "intimacy":
                return constraint.max or constraint.level or constraint.value or "N/A"
        return "N/A"

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["derived"] = {"max_intimacy_level": self.max_intimacy_level}
        return data


@dataclass(frozen=True, slots=True)
class AlignmentProfile:
    """Resolved alignment object consumed by runtime / LLM provider adapters."""

    provider_id: str
    persona_id: str
    mode: str
    contract: AlignmentContract
    provider_profile: ProviderBehaviorProfile

    @property
    def profile_id(self) -> str:
        return self.provider_profile.profile_id

    @property
    def max_intimacy_level(self) -> str:
        return self.provider_profile.max_intimacy_level

    def render_lines(self) -> str:
        return self.contract.render_lines() + "\n\n" + self.provider_profile.render_lines()

    def to_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "persona_id": self.persona_id,
            "mode": self.mode,
            "contract": self.contract.to_dict(),
            "provider_profile": self.provider_profile.to_dict(),
        }

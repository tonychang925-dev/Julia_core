"""Alignment OS public contracts.

Alignment OS keeps runtime-owned behavior contracts stable across LLM providers.
It stores structured alignment metadata, not product-private persona or memory data.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Literal, Mapping

from julia_core.context_admission.contracts import canonical_json


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


@dataclass(frozen=True, slots=True)
class AlignmentExecutionMetadata:
    """Mechanically enforceable, non-semantic provider execution controls."""

    provider_id: str
    cognitive_mode: str
    modality: Literal["text"]
    response_format: Literal["default", "json_object"]
    max_output_tokens: int
    temperature: float | None

    def __post_init__(self) -> None:
        if type(self.provider_id) is not str or not self.provider_id:
            raise TypeError("alignment execution provider_id is inexact")
        if type(self.cognitive_mode) is not str or not self.cognitive_mode:
            raise TypeError("alignment execution cognitive_mode is inexact")
        if self.modality != "text":
            raise TypeError("alignment execution modality is unsupported")
        if self.response_format not in {"default", "json_object"}:
            raise TypeError("alignment execution response_format is unsupported")
        if type(self.max_output_tokens) is not int or not 1 <= self.max_output_tokens <= 32768:
            raise TypeError("alignment execution max_output_tokens is inexact")
        if self.temperature is not None and type(self.temperature) not in (int, float):
            raise TypeError("alignment execution temperature is inexact")
        if self.temperature is not None and not 0 <= self.temperature <= 2:
            raise TypeError("alignment execution temperature is out of bounds")
        object.__setattr__(self, "provider_id", self.provider_id.lower())

    def to_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "cognitive_mode": self.cognitive_mode,
            "modality": self.modality,
            "response_format": self.response_format,
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
        }


@dataclass(frozen=True, slots=True)
class ProviderExecutionEnvelope:
    """Exact Provider ingress; semantic bytes are immutable after C03."""

    conversation_id: str
    turn_id: str
    gate_receipt: str
    semantic_fingerprint: str
    messages: tuple[dict[str, str], ...]
    alignment: AlignmentExecutionMetadata
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _ALIGNMENT_ISSUER:
            raise TypeError("only ProviderAlignmentBoundary constructs execution envelopes")
        for field_name in (
            "conversation_id",
            "turn_id",
            "gate_receipt",
            "semantic_fingerprint",
        ):
            if type(getattr(self, field_name)) is not str or not getattr(self, field_name):
                raise TypeError(f"provider execution envelope {field_name} is inexact")
        if type(self.messages) is not tuple or len(self.messages) != 3:
            raise TypeError("provider execution messages are partial or ambiguous")
        if [message.get("role") for message in self.messages] != ["system", "system", "user"]:
            raise TypeError("provider execution message roles are inexact")
        if any(set(message) != {"role", "content"} for message in self.messages):
            raise TypeError("provider execution message shape is inexact")
        if type(self.alignment) is not AlignmentExecutionMetadata:
            raise TypeError("provider execution alignment metadata is inexact")
        self.alignment.__post_init__()
        actual_fingerprint = sha256(
            canonical_json(list(self.messages)).encode("utf-8")
        ).hexdigest()
        if self.semantic_fingerprint != actual_fingerprint:
            raise TypeError("provider execution semantic fingerprint is forged")

    def verify(self) -> ProviderExecutionEnvelope:
        self.__post_init__()
        return self

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "julia_core.alignment_os.provider_execution_envelope.v1",
            "conversation_id": self.conversation_id,
            "turn_id": self.turn_id,
            "gate_receipt": self.gate_receipt,
            "semantic_fingerprint": self.semantic_fingerprint,
            "messages": [dict(message) for message in self.messages],
            "alignment": self.alignment.to_dict(),
        }


_ALIGNMENT_ISSUER = object()

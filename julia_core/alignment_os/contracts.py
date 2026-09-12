"""Alignment OS public contracts.

Alignment OS keeps runtime-owned behavior contracts stable across LLM providers.
It stores structured alignment metadata, not product-private persona or memory data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Mapping

from julia_core.context_admission import (
    AdmissionRejection,
    C03AdmissionRejected,
    SealedCognitiveContextPackage,
)


ADMITTED_FRAME_NAMES = frozenset(
    {"identity_frame", "experience_frame", "current_task_context"}
)
ADMITTED_FRAME_ROLES = MappingProxyType(
    {
        "identity_frame": "system",
        "experience_frame": "system",
        "current_task_context": "user",
    }
)


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
        object.__setattr__(
            self, "constraints", MappingProxyType(dict(self.constraints or {}))
        )


def _canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _semantic_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _provider_rejection(code: str, message: str) -> C03AdmissionRejected:
    return C03AdmissionRejected(AdmissionRejection(code=code, message=message))


@dataclass(frozen=True, slots=True)
class AdmittedSemanticUnit:
    """Exact C03 frame serialization bound to its admitted digest."""

    frame_name: str
    role: str
    semantic_digest: str
    canonical_content: str

    def __post_init__(self) -> None:
        if self.frame_name not in ADMITTED_FRAME_NAMES:
            raise _provider_rejection(
                "unknown_admitted_frame",
                "provider rendering received an unknown C03 frame",
            )
        expected_role = ADMITTED_FRAME_ROLES[self.frame_name]
        if self.role != expected_role:
            raise _provider_rejection(
                "inexact_provider_role",
                "provider rendering role does not match the C03 transport contract",
            )
        actual_digest = hashlib.sha256(
            self.canonical_content.encode("utf-8")
        ).hexdigest()
        if self.semantic_digest != actual_digest:
            raise _provider_rejection(
                "forged_semantic_unit",
                "provider rendering semantic digest does not match its content",
            )

    def verify(self) -> "AdmittedSemanticUnit":
        self.__post_init__()
        return self

    @classmethod
    def bind(
        cls,
        frame_name: str,
        source: object,
    ) -> "AdmittedSemanticUnit":
        if frame_name not in ADMITTED_FRAME_NAMES:
            raise _provider_rejection(
                "unknown_admitted_frame",
                "provider rendering received an unknown C03 frame",
            )
        try:
            payload = source.to_dict()
            source_digest = source.digest()
        except (AttributeError, TypeError, ValueError) as error:
            raise _provider_rejection(
                "inexact_admitted_source",
                "provider rendering requires an exact digest-bearing C03 source",
            ) from error
        if type(payload) is not dict or type(source_digest) is not str:
            raise _provider_rejection(
                "inexact_admitted_source",
                "provider rendering source serialization is inexact",
            )
        canonical_content = _canonical_json(payload)
        actual_digest = _semantic_digest(payload)
        if source_digest != actual_digest:
            raise _provider_rejection(
                "inexact_admitted_source_digest",
                "provider rendering source digest is not its canonical digest",
            )
        return cls(
            frame_name=frame_name,
            role=ADMITTED_FRAME_ROLES[frame_name],
            semantic_digest=source_digest,
            canonical_content=canonical_content,
        )

    def to_message(self) -> dict[str, str]:
        return {"role": self.role, "content": self.canonical_content}


@dataclass(frozen=True, slots=True)
class AdmittedSemanticBundle:
    """Exact frame set rendered only after package verification."""

    package: SealedCognitiveContextPackage
    units: tuple[AdmittedSemanticUnit, ...]

    def __post_init__(self) -> None:
        if type(self.package) is not SealedCognitiveContextPackage:
            raise _provider_rejection(
                "unsealed_provider_semantics",
                "provider rendering requires a sealed C03 package",
            )
        self.package.verify()
        if type(self.units) is not tuple or len(self.units) != 3:
            raise _provider_rejection(
                "incomplete_provider_semantics",
                "provider rendering requires all three exact C03 units",
            )
        by_name = {unit.frame_name: unit for unit in self.units}
        if set(by_name) != set(ADMITTED_FRAME_NAMES):
            raise _provider_rejection(
                "incomplete_provider_semantics",
                "provider rendering requires all three exact C03 units",
            )
        for unit in self.units:
            unit.verify()
        for frame_name, unit in by_name.items():
            if unit.semantic_digest != self.package.admitted_frames[frame_name]:
                raise _provider_rejection(
                    "mismatched_provider_semantics",
                    "provider rendering unit does not match the sealed package",
                )

    def verify(self) -> "AdmittedSemanticBundle":
        self.__post_init__()
        return self

    @classmethod
    def from_sources(
        cls,
        package: SealedCognitiveContextPackage,
        identity: object,
        experience: object,
        current_task: object,
    ) -> "AdmittedSemanticBundle":
        return cls(
            package=package,
            units=(
                AdmittedSemanticUnit.bind("identity_frame", identity),
                AdmittedSemanticUnit.bind("experience_frame", experience),
                AdmittedSemanticUnit.bind("current_task_context", current_task),
            ),
        )

    def semantic_fingerprint(self) -> str:
        payload = [unit.to_message() for unit in self.units]
        return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


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
        object.__setattr__(
            self, "metadata", MappingProxyType(dict(self.metadata or {}))
        )

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
        object.__setattr__(
            self, "metadata", MappingProxyType(dict(self.metadata or {}))
        )

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
        object.__setattr__(
            self, "behavior_guidance", tuple(self.behavior_guidance or ())
        )
        object.__setattr__(self, "prefer", tuple(self.prefer or ()))
        object.__setattr__(self, "avoid", tuple(self.avoid or ()))
        object.__setattr__(self, "fallback_style", tuple(self.fallback_style or ()))
        object.__setattr__(
            self, "metadata", MappingProxyType(dict(self.metadata or {}))
        )

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
        return (
            self.contract.render_lines() + "\n\n" + self.provider_profile.render_lines()
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "persona_id": self.persona_id,
            "mode": self.mode,
            "contract": self.contract.to_dict(),
            "provider_profile": self.provider_profile.to_dict(),
        }

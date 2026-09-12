"""ENG-08 Identity-only PersonaProjection contracts.

Projection is a deterministic view over governed Identity. It has no durable
semantic authority and does not decide model visibility.
"""
from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from dataclasses import dataclass
from typing import Any

from collections.abc import Mapping

from julia_core.identity import GovernedIdentity, IdentityRef, IdentityStatus
from julia_core.memory_experience import (
    MemoryExperienceRef,
    MemoryExperienceStatus,
    MemoryExperienceType,
)


PERSONA_PROJECTION_POLICY_ID = "persona_projection.identity_only"
PERSONA_PROJECTION_POLICY_VERSION = "1.0.0"
IDENTITY_FRAME_SCHEMA_VERSION = "1.0.0"
EXPERIENCE_PROJECTION_POLICY_ID = "experience_projection.memory_experience_only"
EXPERIENCE_PROJECTION_POLICY_VERSION = "1.0.0"
EXPERIENCE_FRAME_SCHEMA_VERSION = "1.0.0"
EXPERIENCE_FRAME_SET_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class IdentityFrame:
    """Bounded, typed, model-admission-ready representation of Identity."""

    schema_version: str
    policy_id: str
    policy_version: str
    source_ref: IdentityRef
    source_digest: str
    source_status: IdentityStatus
    identity_id: str
    predecessor_version_id: str | None
    anchors: tuple[Mapping[str, str], ...]
    values: tuple[Mapping[str, str], ...]
    boundaries: tuple[Mapping[str, str], ...]
    relationship_role_anchors: tuple[Mapping[str, str], ...]
    provenance_refs: tuple[Mapping[str, Any], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "anchors", tuple(_deep_freeze(item) for item in self.anchors))
        object.__setattr__(self, "values", tuple(_deep_freeze(item) for item in self.values))
        object.__setattr__(self, "boundaries", tuple(_deep_freeze(item) for item in self.boundaries))
        object.__setattr__(
            self,
            "relationship_role_anchors",
            tuple(_deep_freeze(item) for item in self.relationship_role_anchors),
        )
        object.__setattr__(
            self,
            "provenance_refs",
            tuple(_deep_freeze(item) for item in self.provenance_refs),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.projection.identity_frame.v1",
            "schema_version": self.schema_version,
            "frame_kind": "identity_frame",
            "projection": {
                "policy_id": self.policy_id,
                "policy_version": self.policy_version,
                "non_authoritative": True,
                "canonical_authority": "IdentityVersion",
                "model_visibility": "NOT_DECIDED",
            },
            "source": {
                "ref": self.source_ref.to_dict(),
                "digest": self.source_digest,
                "status": self.source_status.value,
                "predecessor_version_id": self.predecessor_version_id,
            },
            "identity_id": self.identity_id,
            "anchors": [_deep_unfreeze(item) for item in self.anchors],
            "values": [_deep_unfreeze(item) for item in self.values],
            "boundaries": [_deep_unfreeze(item) for item in self.boundaries],
            "relationship_role_anchors": [_deep_unfreeze(item) for item in self.relationship_role_anchors],
            "provenance_refs": [_deep_unfreeze(item) for item in self.provenance_refs],
        }

    def canonical_serialization(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_serialization().encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ExperienceFrame:
    """Non-authoritative deterministic view over one governed MemoryExperience."""

    schema_version: str
    policy_id: str
    policy_version: str
    source_ref: MemoryExperienceRef
    source_digest: str
    source_status: MemoryExperienceStatus
    experience_id: str
    version_id: str
    predecessor_version_id: str | None
    experience_type: MemoryExperienceType
    content: Mapping[str, Any]
    provenance_refs: tuple[Mapping[str, Any], ...]
    created_at: str

    def __post_init__(self) -> None:
        if type(self.source_ref) is not MemoryExperienceRef:
            raise TypeError("ExperienceFrame requires an exact MemoryExperienceRef")
        if type(self.source_status) is not MemoryExperienceStatus:
            raise TypeError("ExperienceFrame requires an exact MemoryExperienceStatus")
        if type(self.experience_type) is not MemoryExperienceType:
            raise TypeError("ExperienceFrame requires an exact MemoryExperienceType")
        if not isinstance(self.content, Mapping):
            raise TypeError("ExperienceFrame content must be a Mapping")
        if not all(isinstance(item, Mapping) for item in self.provenance_refs):
            raise TypeError("ExperienceFrame provenance_refs elements must be Mappings")
        object.__setattr__(self, "content", _deep_freeze(self.content))
        object.__setattr__(
            self,
            "provenance_refs",
            tuple(_deep_freeze(item) for item in self.provenance_refs),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.projection.experience_frame.v1",
            "schema_version": self.schema_version,
            "frame_kind": "experience_frame",
            "projection": {
                "policy_id": self.policy_id,
                "policy_version": self.policy_version,
                "non_authoritative": True,
                "canonical_authority": "MemoryExperienceRecord",
                "model_visibility": "NOT_DECIDED",
                "context_admission": False,
                "retrieval": False,
                "hydration": False,
                "runtime_authority": False,
                "current_consent": False,
                "standing_authorization": False,
            },
            "source": {
                "ref": self.source_ref.to_dict(),
                "digest": self.source_digest,
                "status": self.source_status.value,
                "predecessor_version_id": self.predecessor_version_id,
                "created_at": self.created_at,
            },
            "experience_id": self.experience_id,
            "version_id": self.version_id,
            "experience_type": self.experience_type.value,
            "content": _deep_unfreeze(self.content),
            "provenance_refs": [_deep_unfreeze(item) for item in self.provenance_refs],
        }

    def canonical_serialization(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_serialization().encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ExperienceFrameSet:
    """Immutable ordered carrier for exact projected experience frames."""

    schema_version: str
    frames: tuple[ExperienceFrame, ...]

    def __post_init__(self) -> None:
        if self.schema_version != EXPERIENCE_FRAME_SET_SCHEMA_VERSION:
            raise TypeError("ExperienceFrameSet schema version is unsupported")
        if type(self.frames) is not tuple or not self.frames:
            raise TypeError("ExperienceFrameSet requires a nonempty frame tuple")
        source_refs = []
        for frame in self.frames:
            if type(frame) is not ExperienceFrame:
                raise TypeError("ExperienceFrameSet requires exact ExperienceFrame objects")
            source_ref = frame.source_ref
            if any(source_ref == seen_ref for seen_ref in source_refs):
                raise TypeError("ExperienceFrameSet source refs must be unique")
            source_refs.append(source_ref)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.projection.experience_frame_set.v1",
            "schema_version": self.schema_version,
            "frames": [frame.to_dict() for frame in self.frames],
        }

    def canonical_serialization(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_serialization().encode("utf-8")).hexdigest()


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _deep_unfreeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _deep_unfreeze(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_deep_unfreeze(item) for item in value]
    return value


__all__ = [
    "EXPERIENCE_FRAME_SCHEMA_VERSION",
    "EXPERIENCE_FRAME_SET_SCHEMA_VERSION",
    "EXPERIENCE_PROJECTION_POLICY_ID",
    "EXPERIENCE_PROJECTION_POLICY_VERSION",
    "IDENTITY_FRAME_SCHEMA_VERSION",
    "ExperienceFrame",
    "ExperienceFrameSet",
    "IdentityFrame",
    "PERSONA_PROJECTION_POLICY_ID",
    "PERSONA_PROJECTION_POLICY_VERSION",
]

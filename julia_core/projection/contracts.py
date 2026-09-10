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


PERSONA_PROJECTION_POLICY_ID = "persona_projection.identity_only"
PERSONA_PROJECTION_POLICY_VERSION = "1.0.0"
IDENTITY_FRAME_SCHEMA_VERSION = "1.0.0"


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
    "IDENTITY_FRAME_SCHEMA_VERSION",
    "IdentityFrame",
    "PERSONA_PROJECTION_POLICY_ID",
    "PERSONA_PROJECTION_POLICY_VERSION",
]

"""ENG-07 canonical Identity engineering candidate.

This module is a branch-only minimal seam. It is not a frozen C-04 contract and
has no runtime, provider, context, memory, continuity, or persona authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


MAX_ANCHOR_LENGTH = 2_000
FORBIDDEN_SERIALIZATION_FIELDS = frozenset(
    {
        "autobiography",
        "biography",
        "conversation",
        "embedding",
        "episode",
        "memory",
        "provider_instructions",
        "retrieval_index",
        "runtime_prompt",
        "system_prompt",
        "voice_instructions",
    }
)


class IdentityStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    ADMITTED = "ADMITTED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"


@dataclass(frozen=True, slots=True)
class IdentityAnchor:
    anchor_id: str
    statement: str

    def __post_init__(self) -> None:
        _require_id(self.anchor_id, "anchor_id")
        _require_statement(self.statement)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class IdentityValue:
    value_id: str
    statement: str

    def __post_init__(self) -> None:
        _require_id(self.value_id, "value_id")
        _require_statement(self.statement)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class IdentityBoundary:
    boundary_id: str
    constraint: str

    def __post_init__(self) -> None:
        _require_id(self.boundary_id, "boundary_id")
        _require_statement(self.constraint)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RelationshipRoleAnchor:
    anchor_id: str
    relationship_id: str
    role: str

    def __post_init__(self) -> None:
        _require_id(self.anchor_id, "anchor_id")
        _require_id(self.relationship_id, "relationship_id")
        _require_statement(self.role)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class IdentityProvenance:
    source_type: str
    source_ref: str
    source_digest: str = ""
    admission_metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.source_type, "source_type")
        _require_statement(self.source_ref, field_name="source_ref")
        if self.source_digest and len(self.source_digest) != 64:
            raise ValueError("source_digest must be a SHA-256 hex digest")
        if self.source_digest and any(char not in "0123456789abcdef" for char in self.source_digest):
            raise ValueError("source_digest must be lowercase SHA-256 hex")
        object.__setattr__(self, "admission_metadata", tuple((str(k), str(v)) for k, v in self.admission_metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "source_digest": self.source_digest,
            "admission_metadata": dict(self.admission_metadata),
        }


@dataclass(frozen=True, slots=True)
class IdentityContract:
    """Bounded identity-level semantic content only."""

    identity_id: str
    anchors: tuple[IdentityAnchor, ...]
    values: tuple[IdentityValue, ...]
    boundaries: tuple[IdentityBoundary, ...]
    relationship_role_anchors: tuple[RelationshipRoleAnchor, ...]

    def __post_init__(self) -> None:
        _require_id(self.identity_id, "identity_id")
        object.__setattr__(self, "anchors", tuple(self.anchors))
        object.__setattr__(self, "values", tuple(self.values))
        object.__setattr__(self, "boundaries", tuple(self.boundaries))
        object.__setattr__(self, "relationship_role_anchors", tuple(self.relationship_role_anchors))
        if not self.anchors and not self.values and not self.boundaries:
            raise ValueError("identity contract requires at least one identity-level anchor")

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "anchors": [item.to_dict() for item in self.anchors],
            "values": [item.to_dict() for item in self.values],
            "boundaries": [item.to_dict() for item in self.boundaries],
            "relationship_role_anchors": [item.to_dict() for item in self.relationship_role_anchors],
        }


@dataclass(frozen=True, slots=True)
class IdentityRef:
    lineage_id: str
    version_id: str

    def __post_init__(self) -> None:
        _require_id(self.lineage_id, "lineage_id")
        _require_id(self.version_id, "version_id")

    @property
    def uri(self) -> str:
        return f"identity://{self.lineage_id}/{self.version_id}"

    def to_dict(self) -> dict[str, Any]:
        return {"lineage_id": self.lineage_id, "version_id": self.version_id}


@dataclass(frozen=True, slots=True)
class IdentityVersion:
    contract: IdentityContract
    lineage_id: str
    version_id: str
    predecessor_version_id: str | None
    created_at: str
    provenance_refs: tuple[IdentityProvenance, ...]

    def __post_init__(self) -> None:
        _require_id(self.lineage_id, "lineage_id")
        _require_id(self.version_id, "version_id")
        if self.predecessor_version_id is not None:
            _require_id(self.predecessor_version_id, "predecessor_version_id")
        if not self.created_at:
            raise ValueError("created_at is required")
        object.__setattr__(self, "provenance_refs", tuple(self.provenance_refs))
        if not self.provenance_refs:
            raise ValueError("identity version requires provenance")

    @property
    def ref(self) -> IdentityRef:
        return IdentityRef(lineage_id=self.lineage_id, version_id=self.version_id)

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.identity.version.v1",
            "identity": self.contract.to_dict(),
            "lineage_id": self.lineage_id,
            "version_id": self.version_id,
            "predecessor_version_id": self.predecessor_version_id,
            "created_at": self.created_at,
            "provenance_refs": [item.to_dict() for item in self.provenance_refs],
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.canonical_payload()
        if FORBIDDEN_SERIALIZATION_FIELDS.intersection(payload["identity"]):
            raise ValueError("identity contract contains a forbidden semantic payload field")
        return payload

    def canonical_serialization(self) -> str:
        return json.dumps(
            self.canonical_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def digest(self) -> str:
        return hashlib.sha256(
            self.canonical_serialization().encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class IdentityGovernanceEvent:
    event_id: str
    target: IdentityRef
    status: IdentityStatus
    actor: str
    reason: str
    occurred_at: str

    def __post_init__(self) -> None:
        _require_id(self.event_id, "event_id")
        _require_id(self.actor, "actor")
        _require_statement(self.reason, field_name="reason")
        if not self.occurred_at:
            raise ValueError("occurred_at is required")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["target"] = self.target.to_dict()
        data["status"] = self.status.value
        return data


@dataclass(frozen=True, slots=True)
class GovernedIdentity:
    version: IdentityVersion
    status: IdentityStatus
    governance_events: tuple[IdentityGovernanceEvent, ...]

    @property
    def ref(self) -> IdentityRef:
        return self.version.ref

    @property
    def digest(self) -> str:
        return self.version.digest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version.to_dict(),
            "status": self.status.value,
            "governance_events": [event.to_dict() for event in self.governance_events],
        }


def _require_id(value: str, field_name: str) -> None:
    if not value or not value.strip() or len(value) > 256:
        raise ValueError(f"{field_name} is required and must be at most 256 characters")


def _require_statement(value: str, field_name: str = "statement") -> None:
    if not value or not value.strip() or len(value) > MAX_ANCHOR_LENGTH:
        raise ValueError(f"{field_name} is required and must be at most {MAX_ANCHOR_LENGTH} characters")


__all__ = [
    "FORBIDDEN_SERIALIZATION_FIELDS",
    "GovernedIdentity",
    "IdentityAnchor",
    "IdentityBoundary",
    "IdentityContract",
    "IdentityGovernanceEvent",
    "IdentityProvenance",
    "IdentityRef",
    "IdentityStatus",
    "IdentityValue",
    "IdentityVersion",
    "RelationshipRoleAnchor",
]

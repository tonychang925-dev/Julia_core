"""Exact reference-only runtime canonical binding contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from julia_core.identity import IdentityRef
from julia_core.memory_experience import MemoryExperienceRef


BINDING_SCHEMA_VERSION = "julia_core.runtime_canonical_authority.binding.v1"


class RuntimeCanonicalAuthorityBindingStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    ADMITTED = "ADMITTED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"


@dataclass(frozen=True, slots=True)
class RuntimeCanonicalAuthorityBindingRef:
    binding_id: str
    binding_version: str

    def __post_init__(self) -> None:
        _require_id(self.binding_id, "binding_id")
        _require_id(self.binding_version, "binding_version")

    @property
    def uri(self) -> str:
        return f"runtime-canonical-binding://{self.binding_id}/{self.binding_version}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "binding_version": self.binding_version,
        }


@dataclass(frozen=True, slots=True)
class RuntimeCanonicalAuthorityBindingProvenance:
    source_type: str
    source_ref: str
    source_digest: str
    admission_metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.source_type, "source_type")
        _require_id(self.source_ref, "source_ref")
        if len(self.source_digest) != 64 or any(
            char not in "0123456789abcdef" for char in self.source_digest
        ):
            raise ValueError("source_digest must be a lowercase SHA-256 hex digest")
        metadata = tuple(self.admission_metadata)
        for item in metadata:
            if (
                type(item) is not tuple
                or len(item) != 2
                or type(item[0]) is not str
                or type(item[1]) is not str
            ):
                raise ValueError("admission_metadata must contain string pairs")
        metadata_keys = [key for key, _ in metadata]
        if len(metadata_keys) != len(set(metadata_keys)):
            raise ValueError("admission_metadata keys must be unique")
        object.__setattr__(self, "admission_metadata", metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "source_digest": self.source_digest,
            "admission_metadata": dict(self.admission_metadata),
        }


@dataclass(frozen=True, slots=True)
class RuntimeCanonicalAuthorityBinding:
    schema_version: str
    binding_id: str
    binding_version: str
    predecessor_version_id: str | None
    identity_ref: IdentityRef
    experience_refs: tuple[MemoryExperienceRef, ...]
    provenance_refs: tuple[RuntimeCanonicalAuthorityBindingProvenance, ...]
    created_at: str

    def __post_init__(self) -> None:
        if self.schema_version != BINDING_SCHEMA_VERSION:
            raise ValueError("binding schema_version is unsupported")
        _require_id(self.binding_id, "binding_id")
        _require_id(self.binding_version, "binding_version")
        if self.predecessor_version_id is not None:
            _require_id(self.predecessor_version_id, "predecessor_version_id")
            if self.predecessor_version_id == self.binding_version:
                raise ValueError("binding cannot be its own predecessor")
        if type(self.identity_ref) is not IdentityRef:
            raise TypeError("identity_ref must be an exact IdentityRef")
        if type(self.experience_refs) is not tuple or not self.experience_refs:
            raise ValueError("experience_refs must be a nonempty exact tuple")
        if any(type(ref) is not MemoryExperienceRef for ref in self.experience_refs):
            raise TypeError(
                "experience_refs elements must be exact MemoryExperienceRef objects"
            )
        if len(set(self.experience_refs)) != len(self.experience_refs):
            raise ValueError("experience_refs must not contain duplicates")
        object.__setattr__(self, "provenance_refs", tuple(self.provenance_refs))
        if not self.provenance_refs or any(
            type(item) is not RuntimeCanonicalAuthorityBindingProvenance
            for item in self.provenance_refs
        ):
            raise ValueError(
                "provenance_refs must contain exact binding provenance objects"
            )
        _require_timestamp(self.created_at)

    @property
    def ref(self) -> RuntimeCanonicalAuthorityBindingRef:
        return RuntimeCanonicalAuthorityBindingRef(
            self.binding_id,
            self.binding_version,
        )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "binding_id": self.binding_id,
            "binding_version": self.binding_version,
            "predecessor_version_id": self.predecessor_version_id,
            "identity_ref": self.identity_ref.to_dict(),
            "experience_refs": [item.to_dict() for item in self.experience_refs],
            "provenance_refs": [item.to_dict() for item in self.provenance_refs],
            "created_at": self.created_at,
        }

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

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_payload()


@dataclass(frozen=True, slots=True)
class RuntimeCanonicalAuthorityBindingGovernanceEvent:
    event_id: str
    target: RuntimeCanonicalAuthorityBindingRef
    status: RuntimeCanonicalAuthorityBindingStatus
    actor: str
    reason: str
    occurred_at: str

    def __post_init__(self) -> None:
        _require_id(self.event_id, "event_id")
        if type(self.target) is not RuntimeCanonicalAuthorityBindingRef:
            raise TypeError("governance event target is inexact")
        if type(self.status) is not RuntimeCanonicalAuthorityBindingStatus:
            raise TypeError("governance event status is inexact")
        _require_id(self.actor, "actor")
        _require_nonempty(self.reason, "reason")
        _require_timestamp(self.occurred_at)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["target"] = self.target.to_dict()
        data["status"] = self.status.value
        return data


@dataclass(frozen=True, slots=True)
class GovernedRuntimeCanonicalAuthorityBinding:
    binding: RuntimeCanonicalAuthorityBinding
    status: RuntimeCanonicalAuthorityBindingStatus
    governance_events: tuple[RuntimeCanonicalAuthorityBindingGovernanceEvent, ...]

    def __post_init__(self) -> None:
        if type(self.binding) is not RuntimeCanonicalAuthorityBinding:
            raise TypeError("governed binding requires an exact binding")
        if type(self.status) is not RuntimeCanonicalAuthorityBindingStatus:
            raise TypeError("governed binding status is inexact")
        events = tuple(self.governance_events)
        if not events or any(
            type(item) is not RuntimeCanonicalAuthorityBindingGovernanceEvent
            for item in events
        ):
            raise ValueError("governed binding requires exact governance events")
        object.__setattr__(self, "governance_events", events)

    @property
    def ref(self) -> RuntimeCanonicalAuthorityBindingRef:
        return self.binding.ref

    @property
    def digest(self) -> str:
        return self.binding.digest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding": self.binding.to_dict(),
            "status": self.status.value,
            "governance_events": [event.to_dict() for event in self.governance_events],
        }


def _require_id(value: str, field_name: str) -> None:
    if type(value) is not str or not value.strip() or len(value) > 256:
        raise ValueError(
            f"{field_name} must be a nonempty string of at most 256 characters"
        )


def _require_nonempty(value: str, field_name: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty string")


def _require_timestamp(value: str) -> None:
    _require_nonempty(value, "timestamp")
    if len(value) > 128:
        raise ValueError("timestamp must be at most 128 characters")


__all__ = [
    "BINDING_SCHEMA_VERSION",
    "GovernedRuntimeCanonicalAuthorityBinding",
    "RuntimeCanonicalAuthorityBinding",
    "RuntimeCanonicalAuthorityBindingGovernanceEvent",
    "RuntimeCanonicalAuthorityBindingProvenance",
    "RuntimeCanonicalAuthorityBindingRef",
    "RuntimeCanonicalAuthorityBindingStatus",
]

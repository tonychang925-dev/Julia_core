"""Exact durable envelope and deterministic integrity contract."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any


ENVELOPE_SCHEMA_VERSION = "julia_core.durable_authority.envelope.v1"
IDENTITY_OBJECT_SCHEMA = "julia_core.identity.version.v1"
MEMORY_EXPERIENCE_OBJECT_SCHEMA = "julia_core.memory_experience.record.v1"
RUNTIME_BINDING_OBJECT_SCHEMA = "julia_core.runtime_canonical_authority.binding.v1"


class AuthorityFamily(str, Enum):
    IDENTITY = "IDENTITY"
    MEMORY_EXPERIENCE = "MEMORY_EXPERIENCE"
    RUNTIME_BINDING = "RUNTIME_BINDING"


class DurableAuthorityErrorCode(str, Enum):
    PARTIAL_ENVELOPE = "PARTIAL_ENVELOPE"
    MALFORMED_ENVELOPE = "MALFORMED_ENVELOPE"
    UNSUPPORTED_SCHEMA = "UNSUPPORTED_SCHEMA"
    UNKNOWN_AUTHORITY_FAMILY = "UNKNOWN_AUTHORITY_FAMILY"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    REF_MISMATCH = "REF_MISMATCH"
    PAYLOAD_DIGEST_MISMATCH = "PAYLOAD_DIGEST_MISMATCH"
    ENVELOPE_DIGEST_MISMATCH = "ENVELOPE_DIGEST_MISMATCH"
    GOVERNANCE_EVENT_TARGET_MISMATCH = "GOVERNANCE_EVENT_TARGET_MISMATCH"
    INCONSISTENT_LIFECYCLE = "INCONSISTENT_LIFECYCLE"
    MISSING_PREDECESSOR = "MISSING_PREDECESSOR"
    DUPLICATE_CONFLICT = "DUPLICATE_CONFLICT"


class DurableAuthorityPersistenceError(Exception):
    def __init__(self, code: DurableAuthorityErrorCode, message: str) -> None:
        if type(code) is not DurableAuthorityErrorCode:
            raise TypeError("durable authority error code is inexact")
        if type(message) is not str or not message:
            raise TypeError("durable authority error message is required")
        super().__init__(message)
        object.__setattr__(self, "_code", code)

    @property
    def code(self) -> DurableAuthorityErrorCode:
        return self._code

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("durable authority errors are immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("durable authority errors are immutable")


@dataclass(frozen=True, slots=True)
class DurableAuthorityEnvelope:
    envelope_schema: str
    authority_family: AuthorityFamily
    authority_object_ref: str
    authority_object_schema: str
    serialized_payload: str
    payload_digest: str
    governance_events: tuple[dict[str, Any], ...]
    lifecycle_status: str
    lineage_metadata: dict[str, Any]
    provenance: tuple[dict[str, Any], ...]
    envelope_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "governance_events", tuple(self.governance_events))
        object.__setattr__(self, "provenance", tuple(self.provenance))
        if self.envelope_schema != ENVELOPE_SCHEMA_VERSION:
            raise DurableAuthorityPersistenceError(
                DurableAuthorityErrorCode.UNSUPPORTED_SCHEMA,
                "durable authority envelope schema is unsupported",
            )
        if type(self.authority_family) is not AuthorityFamily:
            raise DurableAuthorityPersistenceError(
                DurableAuthorityErrorCode.UNKNOWN_AUTHORITY_FAMILY,
                "authority family must be an exact enum member",
            )
        _require_digest(self.payload_digest, "payload_digest")
        _require_digest(self.envelope_digest, "envelope_digest")
        if self.canonical_serialization_without_digest_digest() != self.envelope_digest:
            raise DurableAuthorityPersistenceError(
                DurableAuthorityErrorCode.ENVELOPE_DIGEST_MISMATCH,
                "durable authority envelope digest is inconsistent",
            )

    @property
    def payload_object(self) -> dict[str, Any]:
        return decode_canonical_json(self.serialized_payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "envelope_schema": self.envelope_schema,
            "authority_family": self.authority_family.value,
            "authority_object_ref": self.authority_object_ref,
            "authority_object_schema": self.authority_object_schema,
            "serialized_payload": self.serialized_payload,
            "payload_digest": self.payload_digest,
            "governance_events": list(self.governance_events),
            "lifecycle_status": self.lifecycle_status,
            "lineage_metadata": self.lineage_metadata,
            "provenance": list(self.provenance),
            "envelope_digest": self.envelope_digest,
        }

    def canonical_serialization_without_digest(self) -> str:
        return canonical_json(
            {
                "envelope_schema": self.envelope_schema,
                "authority_family": self.authority_family.value,
                "authority_object_ref": self.authority_object_ref,
                "authority_object_schema": self.authority_object_schema,
                "serialized_payload": self.serialized_payload,
                "payload_digest": self.payload_digest,
                "governance_events": list(self.governance_events),
                "lifecycle_status": self.lifecycle_status,
                "lineage_metadata": self.lineage_metadata,
                "provenance": list(self.provenance),
            }
        )

    def canonical_serialization_without_digest_digest(self) -> str:
        return hashlib.sha256(
            self.canonical_serialization_without_digest().encode("utf-8")
        ).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def decode_canonical_json(value: str) -> dict[str, Any]:
    if type(value) is not str:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "serialized payload must be a string",
        )
    try:
        decoded = json.loads(value)
    except (TypeError, ValueError) as error:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "serialized payload is not valid JSON",
        ) from error
    if type(decoded) is not dict or canonical_json(decoded) != value:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "serialized payload is not canonical JSON",
        )
    return decoded


def digest_payload(serialized_payload: str) -> str:
    return hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()


def envelope_digest(
    *,
    envelope_schema: str,
    authority_family: AuthorityFamily,
    authority_object_ref: str,
    authority_object_schema: str,
    serialized_payload: str,
    payload_digest: str,
    governance_events: tuple[dict[str, Any], ...],
    lifecycle_status: str,
    lineage_metadata: dict[str, Any],
    provenance: tuple[dict[str, Any], ...],
) -> str:
    value = canonical_json(
        {
            "envelope_schema": envelope_schema,
            "authority_family": authority_family.value,
            "authority_object_ref": authority_object_ref,
            "authority_object_schema": authority_object_schema,
            "serialized_payload": serialized_payload,
            "payload_digest": payload_digest,
            "governance_events": list(governance_events),
            "lifecycle_status": lifecycle_status,
            "lineage_metadata": lineage_metadata,
            "provenance": list(provenance),
        }
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_digest(value: str, field_name: str) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            f"{field_name} must be a lowercase SHA-256 hex digest",
        )

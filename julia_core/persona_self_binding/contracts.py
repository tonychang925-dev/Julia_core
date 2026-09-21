"""Fail-closed typed contracts for PersonaSelfBinding.

PSB-I1 defines durable contract shapes only.  It does not load, persist, or
execute them and contains no provider-specific values.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any


PERSONA_SELF_BINDING_SCHEMA_VERSION = "julia_core.persona_self_binding.v1"
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")


class PersonaSelfBindingErrorCode(str, Enum):
    PSB_SCHEMA_INVALID = "PSB_SCHEMA_INVALID"
    PSB_DIGEST_INVALID = "PSB_DIGEST_INVALID"
    PSB_RELATIONSHIP_STATE_INVALID = "PSB_RELATIONSHIP_STATE_INVALID"
    PSB_PROVIDER_FIELD_FORBIDDEN = "PSB_PROVIDER_FIELD_FORBIDDEN"
    PSB_LIFECYCLE_INVALID = "PSB_LIFECYCLE_INVALID"
    PSB_GOVERNANCE_EVENT_INVALID = "PSB_GOVERNANCE_EVENT_INVALID"
    PSB_PREDECESSOR_INVALID = "PSB_PREDECESSOR_INVALID"
    PSB_DUPLICATE_AUTHORITY_FAMILY = "PSB_DUPLICATE_AUTHORITY_FAMILY"


class PersonaSelfBindingContractError(ValueError):
    def __init__(
        self,
        code: PersonaSelfBindingErrorCode,
        message: str,
    ) -> None:
        if type(code) is not PersonaSelfBindingErrorCode:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "error code must be an exact PersonaSelfBindingErrorCode",
            )
        super().__init__(message)
        self.code = code
        self.message = message


class PersonaSelfBindingLifecycle(str, Enum):
    DRAFT = "DRAFT"
    GOVERNANCE_REVIEW = "GOVERNANCE_REVIEW"
    ADMITTED_ACTIVE = "ADMITTED_ACTIVE"
    ADMITTED_SUPERSEDED = "ADMITTED_SUPERSEDED"
    RETIRED_HISTORICAL = "RETIRED_HISTORICAL"
    REJECTED = "REJECTED"
    REVOKED_INVALID = "REVOKED_INVALID"
    CORRUPT_QUARANTINED = "CORRUPT_QUARANTINED"


class GovernanceEventType(str, Enum):
    PROPOSE_BINDING = "PROPOSE_BINDING"
    REVIEW_BINDING = "REVIEW_BINDING"
    REJECT_BINDING = "REJECT_BINDING"
    ADMIT_AND_ACTIVATE = "ADMIT_AND_ACTIVATE"
    REBIND_AUTHORITY_VERSION = "REBIND_AUTHORITY_VERSION"
    SUPERSEDE_BINDING = "SUPERSEDE_BINDING"
    REVOKE_INVALID = "REVOKE_INVALID"
    RETIRE_HISTORICAL = "RETIRE_HISTORICAL"
    QUARANTINE_CORRUPTION = "QUARANTINE_CORRUPTION"


class AuthorityFamily(str, Enum):
    IDENTITY_FRAME_SET = "IdentityFrameSet"
    EXPERIENCE_FRAME_SET = "ExperienceFrameSet"
    RELATIONSHIP_FRAME_SET = "RelationshipFrameSet"


class RelationshipAuthorityState(str, Enum):
    ABSENT = "ABSENT"
    ADMITTED_BOUND = "ADMITTED_BOUND"
    EXPLICITLY_EMPTY = "EXPLICITLY_EMPTY"


class IdentityAssertionDisposition(str, Enum):
    NO_IDENTITY_AUTHORITY_CONFLICT = "NO_IDENTITY_AUTHORITY_CONFLICT"
    RESOLVED_CONTRADICTION = "RESOLVED_CONTRADICTION"
    UNRESOLVED_IDENTITY_OVERRIDE = "UNRESOLVED_IDENTITY_OVERRIDE"


@dataclass(frozen=True, slots=True)
class AuthorityReference:
    authority_type: AuthorityFamily
    authority_id: str
    source_digest: str
    projected_digest: str | None

    def __post_init__(self) -> None:
        if type(self.authority_type) is not AuthorityFamily:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "authority_type must be an exact AuthorityFamily",
            )
        _require_identifier(self.authority_id, "authority_id")
        _require_digest(self.source_digest, "source_digest")
        if self.projected_digest is not None:
            _require_digest(self.projected_digest, "projected_digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_type": self.authority_type.value,
            "authority_id": self.authority_id,
            "source_digest": self.source_digest,
            "projected_digest": self.projected_digest,
        }


@dataclass(frozen=True, slots=True)
class RelationshipAuthority:
    state: RelationshipAuthorityState
    authority: AuthorityReference | None

    def __post_init__(self) -> None:
        if type(self.state) is not RelationshipAuthorityState:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_RELATIONSHIP_STATE_INVALID,
                "relationship state must be an exact RelationshipAuthorityState",
            )
        if self.state is RelationshipAuthorityState.ADMITTED_BOUND:
            if type(self.authority) is not AuthorityReference:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_RELATIONSHIP_STATE_INVALID,
                    "ADMITTED_BOUND requires an exact RelationshipFrameSet authority",
                )
            if (
                self.authority.authority_type
                is not AuthorityFamily.RELATIONSHIP_FRAME_SET
            ):
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                    "relationship authority has the wrong authority family",
                )
        elif self.authority is not None:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_RELATIONSHIP_STATE_INVALID,
                "unbound relationship states require a null authority reference",
            )

    def to_dict(self) -> dict[str, Any]:
        authority = self.authority.to_dict() if self.authority is not None else None
        return {"state": self.state.value, "authority": authority}


@dataclass(frozen=True, slots=True)
class ExecutionSubstratePolicy:
    role: str = "EXECUTION_SUBSTRATE"
    provider_is_persona_self: bool = False
    provider_neutral: bool = True
    provider_special_cases: tuple[()] = ()

    def __post_init__(self) -> None:
        if (
            self.role != "EXECUTION_SUBSTRATE"
            or self.provider_is_persona_self is not False
            or self.provider_neutral is not True
            or type(self.provider_special_cases) is not tuple
            or self.provider_special_cases != ()
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "execution substrate policy is fixed and provider neutral",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "provider_is_persona_self": self.provider_is_persona_self,
            "provider_neutral": self.provider_neutral,
            "provider_special_cases": list(self.provider_special_cases),
        }


@dataclass(frozen=True, slots=True)
class GovernanceProvenanceEvent:
    event_id: str
    event_type: GovernanceEventType
    actor: str
    reason: str
    occurred_at: str

    def __post_init__(self) -> None:
        _require_identifier(self.event_id, "event_id")
        if type(self.event_type) is not GovernanceEventType:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_GOVERNANCE_EVENT_INVALID,
                "event_type must be an exact GovernanceEventType",
            )
        _require_nonempty(self.actor, "actor")
        _require_nonempty(self.reason, "reason")
        _require_nonempty(self.occurred_at, "occurred_at")
        if len(self.occurred_at) > 128:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "occurred_at must be a bounded timestamp string",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "actor": self.actor,
            "reason": self.reason,
            "occurred_at": self.occurred_at,
        }


@dataclass(frozen=True, slots=True)
class SupersessionContract:
    successor_binding_id: str | None
    successor_binding_version: str | None

    def __post_init__(self) -> None:
        if (self.successor_binding_id is None) != (
            self.successor_binding_version is None
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PREDECESSOR_INVALID,
                "supersession successor fields must be supplied together",
            )
        if self.successor_binding_id is not None:
            _require_identifier(self.successor_binding_id, "successor_binding_id")
        if self.successor_binding_version is not None:
            _require_identifier(
                self.successor_binding_version, "successor_binding_version"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "successor_binding_id": self.successor_binding_id,
            "successor_binding_version": self.successor_binding_version,
        }


@dataclass(frozen=True, slots=True)
class IntegrityContract:
    canonicalization: str
    digest_algorithm: str

    def __post_init__(self) -> None:
        if self.canonicalization != "UTF8_JSON_SORTED_KEYS_COMPACT":
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "canonicalization policy is unsupported",
            )
        if self.digest_algorithm != "sha256":
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_DIGEST_INVALID,
                "digest algorithm is unsupported",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonicalization": self.canonicalization,
            "digest_algorithm": self.digest_algorithm,
        }


@dataclass(frozen=True, slots=True)
class PersonaSelfBinding:
    schema_version: str
    binding_id: str
    persona_self_id: str
    identity_authority: AuthorityReference
    experience_authority: AuthorityReference
    relationship_authority: RelationshipAuthority
    execution_substrate_policy: ExecutionSubstratePolicy
    binding_version: str
    predecessor_binding_version: str | None
    predecessor_binding_id: str | None
    lineage_id: str
    lifecycle_status: PersonaSelfBindingLifecycle
    supersession: SupersessionContract
    governance_provenance: tuple[GovernanceProvenanceEvent, ...]
    integrity: IntegrityContract

    def __post_init__(self) -> None:
        if self.schema_version != PERSONA_SELF_BINDING_SCHEMA_VERSION:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "PersonaSelfBinding schema_version is unsupported",
            )
        _require_identifier(self.binding_id, "binding_id")
        _require_identifier(self.persona_self_id, "persona_self_id")
        _require_identifier(self.binding_version, "binding_version")
        _require_identifier(self.lineage_id, "lineage_id")
        if type(self.identity_authority) is not AuthorityReference:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "identity_authority must be an exact AuthorityReference",
            )
        if (
            self.identity_authority.authority_type
            is not AuthorityFamily.IDENTITY_FRAME_SET
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "identity_authority has the wrong authority family",
            )
        if type(self.experience_authority) is not AuthorityReference:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "experience_authority must be an exact AuthorityReference",
            )
        if (
            self.experience_authority.authority_type
            is not AuthorityFamily.EXPERIENCE_FRAME_SET
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "experience_authority has the wrong authority family",
            )
        if (
            self.identity_authority.authority_id
            == self.experience_authority.authority_id
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_DUPLICATE_AUTHORITY_FAMILY,
                "identity and experience authority IDs must not collide",
            )
        if type(self.relationship_authority) is not RelationshipAuthority:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "relationship_authority must be an exact RelationshipAuthority",
            )
        if self.relationship_authority.authority is not None and any(
            reference.authority_id
            in {
                self.identity_authority.authority_id,
                self.experience_authority.authority_id,
            }
            for reference in (self.relationship_authority.authority,)
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_DUPLICATE_AUTHORITY_FAMILY,
                "relationship authority ID must not duplicate another family",
            )
        if type(self.execution_substrate_policy) is not ExecutionSubstratePolicy:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "execution_substrate_policy must be exact",
            )
        if type(self.lifecycle_status) is not PersonaSelfBindingLifecycle:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_LIFECYCLE_INVALID,
                "lifecycle_status must be an exact PersonaSelfBindingLifecycle",
            )
        if type(self.supersession) is not SupersessionContract:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "supersession must be an exact SupersessionContract",
            )
        if type(self.integrity) is not IntegrityContract:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "integrity must be an exact IntegrityContract",
            )
        events = tuple(self.governance_provenance)
        if not events or any(
            type(event) is not GovernanceProvenanceEvent for event in events
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_GOVERNANCE_EVENT_INVALID,
                "governance_provenance must contain exact typed events",
            )
        event_ids = [event.event_id for event in events]
        if len(event_ids) != len(set(event_ids)):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_GOVERNANCE_EVENT_INVALID,
                "governance event IDs must be unique",
            )
        object.__setattr__(self, "governance_provenance", events)
        _validate_predecessor(
            binding_id=self.binding_id,
            binding_version=self.binding_version,
            predecessor_binding_id=self.predecessor_binding_id,
            predecessor_binding_version=self.predecessor_binding_version,
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> PersonaSelfBinding:
        if not isinstance(payload, Mapping):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "PersonaSelfBinding payload must be a mapping",
            )
        forbidden_provider_fields = {
            "provider_id",
            "model_id",
            "transport_endpoint",
            "runtime_token",
            "provider_specific_persona_rule",
        }
        supplied = forbidden_provider_fields.intersection(payload)
        if supplied:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROVIDER_FIELD_FORBIDDEN,
                f"provider fields are forbidden: {sorted(supplied)}",
            )
        required_fields = {
            "schema_version",
            "binding_id",
            "persona_self_id",
            "identity_authority",
            "experience_authority",
            "relationship_authority",
            "execution_substrate_policy",
            "binding_version",
            "predecessor_binding_version",
            "predecessor_binding_id",
            "lineage_id",
            "lifecycle_status",
            "supersession",
            "governance_provenance",
            "integrity",
        }
        if set(payload) != required_fields:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "PersonaSelfBinding fields do not exactly match the schema",
            )
        try:
            return cls(
                schema_version=payload["schema_version"],
                binding_id=payload["binding_id"],
                persona_self_id=payload["persona_self_id"],
                identity_authority=_authority_from_mapping(
                    payload["identity_authority"]
                ),
                experience_authority=_authority_from_mapping(
                    payload["experience_authority"]
                ),
                relationship_authority=_relationship_from_mapping(
                    payload["relationship_authority"]
                ),
                execution_substrate_policy=ExecutionSubstratePolicy(),
                binding_version=payload["binding_version"],
                predecessor_binding_version=payload.get("predecessor_binding_version"),
                predecessor_binding_id=payload.get("predecessor_binding_id"),
                lineage_id=payload["lineage_id"],
                lifecycle_status=_exact_enum(
                    payload["lifecycle_status"],
                    PersonaSelfBindingLifecycle,
                    PersonaSelfBindingErrorCode.PSB_LIFECYCLE_INVALID,
                ),
                supersession=_supersession_from_mapping(payload["supersession"]),
                governance_provenance=tuple(
                    _governance_event_from_mapping(event)
                    for event in payload["governance_provenance"]
                ),
                integrity=IntegrityContract(
                    canonicalization="UTF8_JSON_SORTED_KEYS_COMPACT",
                    digest_algorithm="sha256",
                ),
            )
        except KeyError as error:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                f"PersonaSelfBinding field is missing: {error.args[0]}",
            ) from error

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "binding_id": self.binding_id,
            "persona_self_id": self.persona_self_id,
            "identity_authority": self.identity_authority.to_dict(),
            "experience_authority": self.experience_authority.to_dict(),
            "relationship_authority": self.relationship_authority.to_dict(),
            "execution_substrate_policy": (self.execution_substrate_policy.to_dict()),
            "binding_version": self.binding_version,
            "predecessor_binding_version": self.predecessor_binding_version,
            "predecessor_binding_id": self.predecessor_binding_id,
            "lineage_id": self.lineage_id,
            "lifecycle_status": self.lifecycle_status.value,
            "supersession": self.supersession.to_dict(),
            "governance_provenance": [
                event.to_dict() for event in self.governance_provenance
            ],
            "integrity": self.integrity.to_dict(),
        }

    def canonical_serialization(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    def digest(self) -> str:
        return hashlib.sha256(
            self.canonical_serialization().encode("utf-8")
        ).hexdigest()

    def verify(self) -> bool:
        canonical = self.canonical_serialization()
        decoded = json.loads(canonical)
        return self.from_mapping(decoded).digest() == self.digest()


@dataclass(frozen=True, slots=True)
class IdentityAuthorityAssertion:
    assertion_scope: str
    asserted_subject: str
    asserted_classification: str
    asserted_value: str
    conflict_against_active_binding: bool
    source_spans: tuple[Mapping[str, str], ...]
    classifier_version: str
    disposition: IdentityAssertionDisposition
    evidence_digest: str

    def __post_init__(self) -> None:
        for field_name in (
            "assertion_scope",
            "asserted_subject",
            "asserted_classification",
            "asserted_value",
            "classifier_version",
        ):
            _require_nonempty(getattr(self, field_name), field_name)
        if type(self.conflict_against_active_binding) is not bool:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "conflict_against_active_binding must be an exact bool",
            )
        spans = tuple(_deep_freeze(span) for span in tuple(self.source_spans))
        if any(type(span) is not MappingProxyType for span in spans):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "source spans must be mappings",
            )
        object.__setattr__(self, "source_spans", spans)
        if type(self.disposition) is not IdentityAssertionDisposition:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "disposition must be an exact IdentityAssertionDisposition",
            )
        _require_digest(self.evidence_digest, "evidence_digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "assertion_scope": self.assertion_scope,
            "asserted_subject": self.asserted_subject,
            "asserted_classification": self.asserted_classification,
            "asserted_value": self.asserted_value,
            "conflict_against_active_binding": (self.conflict_against_active_binding),
            "source_spans": [_deep_unfreeze(span) for span in self.source_spans],
            "classifier_version": self.classifier_version,
            "disposition": self.disposition.value,
            "evidence_digest": self.evidence_digest,
        }

    def canonical_serialization(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    def digest(self) -> str:
        return hashlib.sha256(
            self.canonical_serialization().encode("utf-8")
        ).hexdigest()


def _authority_from_mapping(payload: Any) -> AuthorityReference:
    if not isinstance(payload, Mapping):
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            "authority reference must be a mapping",
        )
    if set(payload) != {
        "authority_type",
        "authority_id",
        "source_digest",
        "projected_digest",
    }:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            "authority reference fields do not exactly match the schema",
        )
    try:
        return AuthorityReference(
            authority_type=_exact_enum(
                payload["authority_type"],
                AuthorityFamily,
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            ),
            authority_id=payload["authority_id"],
            source_digest=payload["source_digest"],
            projected_digest=payload.get("projected_digest"),
        )
    except KeyError as error:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            f"authority reference field is missing: {error.args[0]}",
        ) from error


def _relationship_from_mapping(payload: Any) -> RelationshipAuthority:
    if not isinstance(payload, Mapping):
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            "relationship authority must be a mapping",
        )
    if set(payload) != {"state", "authority"}:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            "relationship authority fields do not exactly match the schema",
        )
    try:
        authority_payload = payload["authority"]
        return RelationshipAuthority(
            state=_exact_enum(
                payload["state"],
                RelationshipAuthorityState,
                PersonaSelfBindingErrorCode.PSB_RELATIONSHIP_STATE_INVALID,
            ),
            authority=(
                None
                if authority_payload is None
                else _authority_from_mapping(authority_payload)
            ),
        )
    except KeyError as error:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            f"relationship authority field is missing: {error.args[0]}",
        ) from error


def _governance_event_from_mapping(payload: Any) -> GovernanceProvenanceEvent:
    if not isinstance(payload, Mapping):
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_GOVERNANCE_EVENT_INVALID,
            "governance event must be a mapping",
        )
    if set(payload) != {
        "event_id",
        "event_type",
        "actor",
        "reason",
        "occurred_at",
    }:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_GOVERNANCE_EVENT_INVALID,
            "governance event fields do not exactly match the schema",
        )
    try:
        return GovernanceProvenanceEvent(
            event_id=payload["event_id"],
            event_type=_exact_enum(
                payload["event_type"],
                GovernanceEventType,
                PersonaSelfBindingErrorCode.PSB_GOVERNANCE_EVENT_INVALID,
            ),
            actor=payload["actor"],
            reason=payload["reason"],
            occurred_at=payload["occurred_at"],
        )
    except KeyError as error:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_GOVERNANCE_EVENT_INVALID,
            f"governance event field is missing: {error.args[0]}",
        ) from error


def _supersession_from_mapping(payload: Any) -> SupersessionContract:
    if not isinstance(payload, Mapping):
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            "supersession must be a mapping",
        )
    if set(payload) != {
        "successor_binding_id",
        "successor_binding_version",
    }:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            "supersession fields do not exactly match the schema",
        )
    try:
        return SupersessionContract(
            successor_binding_id=payload["successor_binding_id"],
            successor_binding_version=payload["successor_binding_version"],
        )
    except KeyError as error:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            f"supersession field is missing: {error.args[0]}",
        ) from error


def _exact_enum[E: Enum](
    value: Any,
    enum_type: type[E],
    error_code: PersonaSelfBindingErrorCode,
) -> E:
    if type(value) is not enum_type:
        try:
            candidate = enum_type(value)
        except ValueError as error:
            raise PersonaSelfBindingContractError(
                error_code,
                f"value is not an exact {enum_type.__name__}",
            ) from error
        if type(candidate) is not enum_type:
            raise PersonaSelfBindingContractError(
                error_code,
                f"value is not an exact {enum_type.__name__}",
            )
        return candidate
    return value


def _validate_predecessor(
    *,
    binding_id: str,
    binding_version: str,
    predecessor_binding_id: str | None,
    predecessor_binding_version: str | None,
) -> None:
    if (predecessor_binding_id is None) != (predecessor_binding_version is None):
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_PREDECESSOR_INVALID,
            "predecessor fields must be null or supplied together",
        )
    match = re.fullmatch(r"v([1-9][0-9]*)", binding_version)
    if match is None:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_PREDECESSOR_INVALID,
            "binding_version must be vN with a positive integer",
        )
    current_number = int(match.group(1))
    if predecessor_binding_id is None:
        if current_number != 1:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PREDECESSOR_INVALID,
                "only v1 may have null predecessor fields",
            )
        return
    if predecessor_binding_id != binding_id:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_PREDECESSOR_INVALID,
            "predecessor binding ID must match the binding lineage",
        )
    predecessor_match = re.fullmatch(r"v([1-9][0-9]*)", predecessor_binding_version)
    if predecessor_match is None or int(predecessor_match.group(1)) != (
        current_number - 1
    ):
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_PREDECESSOR_INVALID,
            "binding versions must be consecutive",
        )


def _require_identifier(value: str, field_name: str) -> None:
    if type(value) is not str or IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            f"{field_name} must match {IDENTIFIER_PATTERN.pattern}",
        )


def _require_nonempty(value: str, field_name: str) -> None:
    if type(value) is not str or not value.strip() or len(value) > 1024:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
            f"{field_name} must be a bounded nonempty string",
        )


def _require_digest(value: str, field_name: str) -> None:
    if type(value) is not str or DIGEST_PATTERN.fullmatch(value) is None:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_DIGEST_INVALID,
            f"{field_name} must be a lowercase SHA-256 hex digest",
        )


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _deep_freeze(item) for key, item in value.items()}
        )
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
    "AuthorityFamily",
    "AuthorityReference",
    "ExecutionSubstratePolicy",
    "GovernanceEventType",
    "GovernanceProvenanceEvent",
    "IdentityAssertionDisposition",
    "IdentityAuthorityAssertion",
    "IntegrityContract",
    "PERSONA_SELF_BINDING_SCHEMA_VERSION",
    "PersonaSelfBinding",
    "PersonaSelfBindingContractError",
    "PersonaSelfBindingErrorCode",
    "PersonaSelfBindingLifecycle",
    "RelationshipAuthority",
    "RelationshipAuthorityState",
    "SupersessionContract",
]

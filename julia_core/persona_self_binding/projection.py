"""Deterministic model-visible PersonaSelfBinding ownership projection."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from julia_core.persona_self_binding.contracts import (
    AuthorityFamily,
    AuthorityReference,
    IdentityAuthorityAssertion,
    IdentityAssertionDisposition,
    PersonaSelfBinding,
    PersonaSelfBindingContractError,
    PersonaSelfBindingErrorCode,
    PersonaSelfBindingLifecycle,
    RelationshipAuthorityState,
)


PROJECTION_SCHEMA_VERSION = "julia_core.persona_self_binding.projection.v1"


class OwnershipRole:
    CURRENT_SELF_IDENTITY = "CURRENT_SELF_IDENTITY"
    CURRENT_SELF_EXPERIENCE = "CURRENT_SELF_EXPERIENCE"
    CURRENT_SELF_RELATIONSHIP_STATE = "CURRENT_SELF_RELATIONSHIP_STATE"


class ProjectionDisposition:
    NONE = "NONE"
    NO_IDENTITY_AUTHORITY_CONFLICT = "NO_IDENTITY_AUTHORITY_CONFLICT"
    RESOLVED_CONTRADICTION = "RESOLVED_CONTRADICTION"
    UNRESOLVED_IDENTITY_OVERRIDE = "UNRESOLVED_IDENTITY_OVERRIDE"


@dataclass(frozen=True, slots=True)
class OwnershipReferenceProjection:
    ownership_role: str
    authority_type: str
    authority_id: str
    source_digest: str
    projected_digest: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ownership_role": self.ownership_role,
            "authority_type": self.authority_type,
            "authority_id": self.authority_id,
            "source_digest": self.source_digest,
            "projected_digest": self.projected_digest,
        }


@dataclass(frozen=True, slots=True)
class RelationshipOwnershipProjection:
    state: RelationshipAuthorityState
    ownership_role: str | None
    authority: AuthorityReference | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "ownership_role": self.ownership_role,
            "authority": (None if self.authority is None else self.authority.to_dict()),
        }


@dataclass(frozen=True, slots=True)
class ExecutionSubstrateProjection:
    role: str
    provider_is_persona_self: bool
    provider_neutral: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "provider_is_persona_self": self.provider_is_persona_self,
            "provider_neutral": self.provider_neutral,
        }


@dataclass(frozen=True, slots=True)
class AuthorityPrecedenceProjection:
    identity_authority_source: str
    current_task_identity_authority: str
    provider_identity_authority: str
    precedence_scope: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_authority_source": self.identity_authority_source,
            "current_task_identity_authority": (self.current_task_identity_authority),
            "provider_identity_authority": self.provider_identity_authority,
            "precedence_scope": self.precedence_scope,
        }


@dataclass(frozen=True, slots=True)
class ContradictionProjection:
    disposition: str
    assertion_digest: str
    classifier_version: str
    conflict_against_active_binding: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition,
            "assertion_digest": self.assertion_digest,
            "classifier_version": self.classifier_version,
            "conflict_against_active_binding": (self.conflict_against_active_binding),
        }


@dataclass(frozen=True, slots=True)
class PersonaSelfBindingProjection:
    schema_version: str
    persona_self_id: str
    binding_id: str
    binding_version: str
    lineage_id: str
    identity_ownership: OwnershipReferenceProjection
    experience_ownership: OwnershipReferenceProjection
    relationship_ownership: RelationshipOwnershipProjection
    execution_substrate_policy: ExecutionSubstrateProjection
    authority_precedence: AuthorityPrecedenceProjection
    contradiction: ContradictionProjection
    semantic_authority_separation: str

    def __post_init__(self) -> None:
        if self.schema_version != PROJECTION_SCHEMA_VERSION:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_INVALID_INPUT,
                "projection schema_version is unsupported",
            )
        if (
            self.identity_ownership.ownership_role
            != OwnershipRole.CURRENT_SELF_IDENTITY
            or self.identity_ownership.authority_type
            != AuthorityFamily.IDENTITY_FRAME_SET.value
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_UNBOUND_IDENTITY,
                "identity ownership projection is invalid",
            )
        if (
            self.experience_ownership.ownership_role
            != OwnershipRole.CURRENT_SELF_EXPERIENCE
            or self.experience_ownership.authority_type
            != AuthorityFamily.EXPERIENCE_FRAME_SET.value
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_UNBOUND_EXPERIENCE,
                "experience ownership projection is invalid",
            )
        relationship = self.relationship_ownership
        if relationship.state is RelationshipAuthorityState.ADMITTED_BOUND:
            if (
                relationship.ownership_role
                != OwnershipRole.CURRENT_SELF_RELATIONSHIP_STATE
                or type(relationship.authority) is not AuthorityReference
                or relationship.authority.authority_type
                is not AuthorityFamily.RELATIONSHIP_FRAME_SET
            ):
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_PROJECTION_RELATIONSHIP_STATE_INVALID,
                    "bound relationship ownership projection is invalid",
                )
        elif (
            relationship.ownership_role is not None
            or relationship.authority is not None
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_RELATIONSHIP_STATE_INVALID,
                "unbound relationship ownership projection is invalid",
            )
        if (
            self.execution_substrate_policy.role != "EXECUTION_SUBSTRATE"
            or self.execution_substrate_policy.provider_is_persona_self is not False
            or self.execution_substrate_policy.provider_neutral is not True
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_PROVIDER_FIELD_FORBIDDEN,
                "execution substrate projection must remain provider neutral",
            )
        if (
            self.authority_precedence.identity_authority_source != "GOVERNED_BINDING"
            or self.authority_precedence.current_task_identity_authority != "NONE"
            or self.authority_precedence.provider_identity_authority != "NONE"
            or self.authority_precedence.precedence_scope
            != "PERSONA_IDENTITY_AUTHORITY"
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_INVALID_INPUT,
                "authority precedence projection is invalid",
            )
        if self.contradiction.disposition not in {
            ProjectionDisposition.NONE,
            ProjectionDisposition.NO_IDENTITY_AUTHORITY_CONFLICT,
            ProjectionDisposition.RESOLVED_CONTRADICTION,
        }:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_UNRESOLVED_IDENTITY_OVERRIDE,
                "unresolved identity override is not dispatchable",
            )
        if self.semantic_authority_separation != (
            "BINDING_OWNERSHIP_NOT_SEMANTIC_FACT_AUTHORITY"
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_INVALID_INPUT,
                "semantic authority separation is invalid",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "persona_self_id": self.persona_self_id,
            "binding_id": self.binding_id,
            "binding_version": self.binding_version,
            "lineage_id": self.lineage_id,
            "identity_ownership": self.identity_ownership.to_dict(),
            "experience_ownership": self.experience_ownership.to_dict(),
            "relationship_ownership": self.relationship_ownership.to_dict(),
            "execution_substrate_policy": (self.execution_substrate_policy.to_dict()),
            "authority_precedence": self.authority_precedence.to_dict(),
            "contradiction": self.contradiction.to_dict(),
            "semantic_authority_separation": self.semantic_authority_separation,
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

    def verify(self, expected_digest: str | None = None) -> bool:
        reconstructed = PersonaSelfBindingProjector.from_mapping(self.to_dict())
        actual_digest = reconstructed.digest()
        if expected_digest is not None and expected_digest != actual_digest:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_DIGEST_MISMATCH,
                "PersonaSelfBinding projection digest does not match",
                object_digest=actual_digest,
            )
        return actual_digest == self.digest()


class PersonaSelfBindingProjector:
    @classmethod
    def project(
        cls,
        binding: PersonaSelfBinding,
        identity_assertion: IdentityAuthorityAssertion | None = None,
    ) -> PersonaSelfBindingProjection:
        if type(binding) is not PersonaSelfBinding:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_INVALID_INPUT,
                "projection input must be an exact PersonaSelfBinding",
            )
        if binding.lifecycle_status is not PersonaSelfBindingLifecycle.ADMITTED_ACTIVE:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_INVALID_INPUT,
                "projection requires an ADMITTED_ACTIVE PersonaSelfBinding",
            )
        if (
            binding.identity_authority.authority_type
            is not AuthorityFamily.IDENTITY_FRAME_SET
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_UNBOUND_IDENTITY,
                "identity ownership requires an IdentityFrameSet authority",
            )
        if (
            binding.experience_authority.authority_type
            is not AuthorityFamily.EXPERIENCE_FRAME_SET
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_UNBOUND_EXPERIENCE,
                "experience ownership requires an ExperienceFrameSet authority",
            )
        if identity_assertion is not None:
            if type(identity_assertion) is not IdentityAuthorityAssertion:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_PROJECTION_INVALID_INPUT,
                    "identity assertion must be an exact typed contract",
                )
            if (
                identity_assertion.disposition
                is IdentityAssertionDisposition.UNRESOLVED_IDENTITY_OVERRIDE
            ):
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_PROJECTION_UNRESOLVED_IDENTITY_OVERRIDE,
                    "unresolved identity override is not dispatchable",
                )
            contradiction = ContradictionProjection(
                disposition=identity_assertion.disposition.value,
                assertion_digest=identity_assertion.evidence_digest,
                classifier_version=identity_assertion.classifier_version,
                conflict_against_active_binding=(
                    identity_assertion.conflict_against_active_binding
                ),
            )
        else:
            contradiction = ContradictionProjection(
                disposition=ProjectionDisposition.NONE,
                assertion_digest="0" * 64,
                classifier_version="none",
                conflict_against_active_binding=False,
            )
        relationship = binding.relationship_authority
        if type(relationship.state) is not RelationshipAuthorityState:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_RELATIONSHIP_STATE_INVALID,
                "relationship ownership state is invalid",
            )
        return PersonaSelfBindingProjection(
            schema_version=PROJECTION_SCHEMA_VERSION,
            persona_self_id=binding.persona_self_id,
            binding_id=binding.binding_id,
            binding_version=binding.binding_version,
            lineage_id=binding.lineage_id,
            identity_ownership=OwnershipReferenceProjection(
                ownership_role=OwnershipRole.CURRENT_SELF_IDENTITY,
                authority_type=binding.identity_authority.authority_type.value,
                authority_id=binding.identity_authority.authority_id,
                source_digest=binding.identity_authority.source_digest,
                projected_digest=binding.identity_authority.projected_digest,
            ),
            experience_ownership=OwnershipReferenceProjection(
                ownership_role=OwnershipRole.CURRENT_SELF_EXPERIENCE,
                authority_type=binding.experience_authority.authority_type.value,
                authority_id=binding.experience_authority.authority_id,
                source_digest=binding.experience_authority.source_digest,
                projected_digest=binding.experience_authority.projected_digest,
            ),
            relationship_ownership=RelationshipOwnershipProjection(
                state=relationship.state,
                ownership_role=(
                    OwnershipRole.CURRENT_SELF_RELATIONSHIP_STATE
                    if relationship.state is RelationshipAuthorityState.ADMITTED_BOUND
                    else None
                ),
                authority=relationship.authority,
            ),
            execution_substrate_policy=ExecutionSubstrateProjection(
                role=binding.execution_substrate_policy.role,
                provider_is_persona_self=(
                    binding.execution_substrate_policy.provider_is_persona_self
                ),
                provider_neutral=(binding.execution_substrate_policy.provider_neutral),
            ),
            authority_precedence=AuthorityPrecedenceProjection(
                identity_authority_source="GOVERNED_BINDING",
                current_task_identity_authority="NONE",
                provider_identity_authority="NONE",
                precedence_scope="PERSONA_IDENTITY_AUTHORITY",
            ),
            contradiction=contradiction,
            semantic_authority_separation=(
                "BINDING_OWNERSHIP_NOT_SEMANTIC_FACT_AUTHORITY"
            ),
        )

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> PersonaSelfBindingProjection:
        if not isinstance(payload, dict) or set(payload) != {
            "schema_version",
            "persona_self_id",
            "binding_id",
            "binding_version",
            "lineage_id",
            "identity_ownership",
            "experience_ownership",
            "relationship_ownership",
            "execution_substrate_policy",
            "authority_precedence",
            "contradiction",
            "semantic_authority_separation",
        }:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_INVALID_INPUT,
                "projection fields do not exactly match the schema",
            )
        try:
            identity_payload = payload["identity_ownership"]
            experience_payload = payload["experience_ownership"]
            relationship_payload = payload["relationship_ownership"]
            substrate_payload = payload["execution_substrate_policy"]
            precedence_payload = payload["authority_precedence"]
            contradiction_payload = payload["contradiction"]
            relationship_state = _exact_relationship_state(
                relationship_payload["state"]
            )
            relationship_authority_payload = relationship_payload["authority"]
            return PersonaSelfBindingProjection(
                schema_version=payload["schema_version"],
                persona_self_id=payload["persona_self_id"],
                binding_id=payload["binding_id"],
                binding_version=payload["binding_version"],
                lineage_id=payload["lineage_id"],
                identity_ownership=_ownership_from_mapping(identity_payload),
                experience_ownership=_ownership_from_mapping(experience_payload),
                relationship_ownership=RelationshipOwnershipProjection(
                    state=relationship_state,
                    ownership_role=relationship_payload["ownership_role"],
                    authority=(
                        None
                        if relationship_authority_payload is None
                        else _authority_from_mapping(relationship_authority_payload)
                    ),
                ),
                execution_substrate_policy=ExecutionSubstrateProjection(
                    role=substrate_payload["role"],
                    provider_is_persona_self=substrate_payload[
                        "provider_is_persona_self"
                    ],
                    provider_neutral=substrate_payload["provider_neutral"],
                ),
                authority_precedence=AuthorityPrecedenceProjection(
                    identity_authority_source=precedence_payload[
                        "identity_authority_source"
                    ],
                    current_task_identity_authority=precedence_payload[
                        "current_task_identity_authority"
                    ],
                    provider_identity_authority=precedence_payload[
                        "provider_identity_authority"
                    ],
                    precedence_scope=precedence_payload["precedence_scope"],
                ),
                contradiction=ContradictionProjection(
                    disposition=contradiction_payload["disposition"],
                    assertion_digest=contradiction_payload["assertion_digest"],
                    classifier_version=contradiction_payload["classifier_version"],
                    conflict_against_active_binding=contradiction_payload[
                        "conflict_against_active_binding"
                    ],
                ),
                semantic_authority_separation=payload["semantic_authority_separation"],
            )
        except KeyError as error:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_INVALID_INPUT,
                f"projection field is missing: {error.args[0]}",
            ) from error


def _ownership_from_mapping(
    payload: Any,
) -> OwnershipReferenceProjection:
    if not isinstance(payload, dict) or set(payload) != {
        "ownership_role",
        "authority_type",
        "authority_id",
        "source_digest",
        "projected_digest",
    }:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_PROJECTION_INVALID_INPUT,
            "ownership projection fields do not exactly match the schema",
        )
    return OwnershipReferenceProjection(
        ownership_role=payload["ownership_role"],
        authority_type=payload["authority_type"],
        authority_id=payload["authority_id"],
        source_digest=payload["source_digest"],
        projected_digest=payload["projected_digest"],
    )


def _authority_from_mapping(payload: Any) -> AuthorityReference:
    if not isinstance(payload, dict) or set(payload) != {
        "authority_type",
        "authority_id",
        "source_digest",
        "projected_digest",
    }:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_PROJECTION_INVALID_INPUT,
            "relationship authority fields do not exactly match the schema",
        )
    try:
        authority_type = AuthorityFamily(payload["authority_type"])
    except (ValueError, TypeError) as error:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_PROJECTION_INVALID_INPUT,
            "relationship authority family is invalid",
        ) from error
    return AuthorityReference(
        authority_type=authority_type,
        authority_id=payload["authority_id"],
        source_digest=payload["source_digest"],
        projected_digest=payload["projected_digest"],
    )


def _exact_relationship_state(value: Any) -> RelationshipAuthorityState:
    try:
        return RelationshipAuthorityState(value)
    except ValueError as error:
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_PROJECTION_RELATIONSHIP_STATE_INVALID,
            "relationship projection state is invalid",
        ) from error


__all__ = [
    "PROJECTION_SCHEMA_VERSION",
    "PersonaSelfBindingProjector",
    "PersonaSelfBindingProjection",
]

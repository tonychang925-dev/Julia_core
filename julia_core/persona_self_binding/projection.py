"""Deterministic model-visible PersonaSelfBinding ownership projection."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
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
PROJECTION_V2_SCHEMA_VERSION = "julia_core.persona_self_binding.projection.v2"


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class OwnershipRole:
    CURRENT_SELF_IDENTITY = "CURRENT_SELF_IDENTITY"
    CURRENT_SELF_EXPERIENCE = "CURRENT_SELF_EXPERIENCE"
    CURRENT_SELF_RELATIONSHIP_STATE = "CURRENT_SELF_RELATIONSHIP_STATE"


class ProjectionDisposition:
    NONE = "NONE"
    NO_IDENTITY_AUTHORITY_CONFLICT = "NO_IDENTITY_AUTHORITY_CONFLICT"
    RESOLVED_CONTRADICTION = "RESOLVED_CONTRADICTION"
    UNRESOLVED_IDENTITY_OVERRIDE = "UNRESOLVED_IDENTITY_OVERRIDE"


class SemanticClauseType(str, Enum):
    SELF_IDENTITY_BINDING = "SELF_IDENTITY_BINDING"
    SUBSTRATE_NON_IDENTITY = "SUBSTRATE_NON_IDENTITY"
    TASK_IDENTITY_NON_AUTHORITY = "TASK_IDENTITY_NON_AUTHORITY"
    GOVERNED_IDENTITY_PRECEDENCE = "GOVERNED_IDENTITY_PRECEDENCE"
    EXPERIENCE_SELF_OWNERSHIP = "EXPERIENCE_SELF_OWNERSHIP"
    EXPERIENCE_EPISTEMIC_FIDELITY = "EXPERIENCE_EPISTEMIC_FIDELITY"
    RELATIONSHIP_AUTHORITY_STATE = "RELATIONSHIP_AUTHORITY_STATE"


SEMANTIC_CLAUSE_ORDER = tuple(clause.value for clause in SemanticClauseType)


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


@dataclass(frozen=True, slots=True)
class PersonaSelfBindingSemanticClause:
    clause_type: SemanticClauseType
    source_authority: dict[str, Any]
    subject: str
    predicate: str
    object: str
    authority_scope: str
    model_visible_text: str
    digest: str

    def __post_init__(self) -> None:
        if type(self.clause_type) is not SemanticClauseType:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_INVALID_INPUT,
                "semantic clause_type is invalid",
            )
        if not isinstance(self.source_authority, dict) or not all(
            type(key) is str and key for key in self.source_authority
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_INVALID_INPUT,
                "semantic clause source_authority must be an exact object",
            )
        if not all(
            type(value) is str and value
            for value in (
                self.subject,
                self.predicate,
                self.object,
                self.authority_scope,
                self.model_visible_text,
            )
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_INVALID_INPUT,
                "semantic clause fields must be exact non-empty strings",
            )
        if self.digest != _sha256_text(_canonical_json(self._digest_payload())):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_CLAUSE_DIGEST_MISMATCH,
                "semantic clause digest does not match canonical content",
            )

    def _digest_payload(self) -> dict[str, Any]:
        return {
            "clause_type": self.clause_type.value,
            "source_authority": self.source_authority,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "authority_scope": self.authority_scope,
            "model_visible_text": self.model_visible_text,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._digest_payload(), "digest": self.digest}

    def canonical_serialization(self) -> str:
        return _canonical_json(self.to_dict())

    def digest_without_clause_digest(self) -> str:
        return _sha256_text(_canonical_json(self._digest_payload()))

    @classmethod
    def from_mapping(cls, payload: Any) -> PersonaSelfBindingSemanticClause:
        if isinstance(payload, dict) and set(payload) & {
            "provider_id",
            "model_id",
            "transport_endpoint",
            "runtime_token",
        }:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_PROVIDER_IDENTITY_FORBIDDEN,
                "semantic clause contains concrete provider identity",
            )
        if not isinstance(payload, dict) or set(payload) != {
            "clause_type",
            "source_authority",
            "subject",
            "predicate",
            "object",
            "authority_scope",
            "model_visible_text",
            "digest",
        }:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_INVALID_INPUT,
                "semantic clause fields do not exactly match the schema",
            )
        try:
            clause_type = SemanticClauseType(payload["clause_type"])
        except ValueError as error:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_INVALID_INPUT,
                "semantic clause_type is unsupported",
            ) from error
        return cls(
            clause_type=clause_type,
            source_authority=payload["source_authority"],
            subject=payload["subject"],
            predicate=payload["predicate"],
            object=payload["object"],
            authority_scope=payload["authority_scope"],
            model_visible_text=payload["model_visible_text"],
            digest=payload["digest"],
        )


@dataclass(frozen=True, slots=True)
class PersonaSelfBindingProjectionV2(PersonaSelfBindingProjection):
    semantic_clauses: tuple[PersonaSelfBindingSemanticClause, ...]
    semantic_clause_set_digest: str

    def __post_init__(self) -> None:
        base_fields = {
            "persona_self_id": self.persona_self_id,
            "binding_id": self.binding_id,
            "binding_version": self.binding_version,
            "lineage_id": self.lineage_id,
            "identity_ownership": self.identity_ownership,
            "experience_ownership": self.experience_ownership,
            "relationship_ownership": self.relationship_ownership,
            "execution_substrate_policy": self.execution_substrate_policy,
            "authority_precedence": self.authority_precedence,
            "contradiction": self.contradiction,
            "semantic_authority_separation": self.semantic_authority_separation,
        }
        PersonaSelfBindingProjection(
            schema_version=PROJECTION_SCHEMA_VERSION,
            **base_fields,
        ).verify()
        if self.schema_version != PROJECTION_V2_SCHEMA_VERSION:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_INVALID_INPUT,
                "projection V2 schema_version is unsupported",
            )
        clause_types = tuple(
            clause.clause_type.value for clause in self.semantic_clauses
        )
        if clause_types != SEMANTIC_CLAUSE_ORDER or len(set(clause_types)) != len(
            SEMANTIC_CLAUSE_ORDER
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_CLAUSE_ORDER_MISMATCH,
                "semantic clause count, order, or uniqueness is invalid",
            )
        expected_clauses = _derive_semantic_clauses(
            persona_self_id=self.persona_self_id,
            binding_id=self.binding_id,
            binding_version=self.binding_version,
            identity_ownership=self.identity_ownership,
            experience_ownership=self.experience_ownership,
            relationship_ownership=self.relationship_ownership,
            execution_substrate_policy=self.execution_substrate_policy,
            authority_precedence=self.authority_precedence,
        )
        if self.semantic_clauses != expected_clauses:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_CLAUSE_SOURCE_MISMATCH,
                "semantic clauses do not derive from canonical projection fields",
            )
        expected_set_digest = _sha256_text(
            _canonical_json([clause.digest for clause in self.semantic_clauses])
        )
        if self.semantic_clause_set_digest != expected_set_digest:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_CLAUSE_DIGEST_MISMATCH,
                "semantic clause set digest does not match ordered clause digests",
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
            "execution_substrate_policy": self.execution_substrate_policy.to_dict(),
            "authority_precedence": self.authority_precedence.to_dict(),
            "contradiction": self.contradiction.to_dict(),
            "semantic_authority_separation": self.semantic_authority_separation,
            "semantic_clauses": [clause.to_dict() for clause in self.semantic_clauses],
            "semantic_clause_set_digest": self.semantic_clause_set_digest,
        }

    def canonical_serialization(self) -> str:
        return _canonical_json(self.to_dict())

    def digest(self) -> str:
        return _sha256_text(self.canonical_serialization())

    def verify(self, expected_digest: str | None = None) -> bool:
        reconstructed = PersonaSelfBindingProjectorV2.from_mapping(self.to_dict())
        if reconstructed != self:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_CONTRADICTS_CANONICAL_FIELDS,
                "projection V2 does not reconstruct exactly",
            )
        actual_digest = reconstructed.digest()
        if expected_digest is not None and expected_digest != actual_digest:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_DIGEST_MISMATCH,
                "PersonaSelfBinding projection digest does not match",
                object_digest=actual_digest,
            )
        if self.canonical_serialization() != _canonical_json(
            json.loads(self.canonical_serialization())
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_NON_DETERMINISTIC_SERIALIZATION,
                "projection V2 serialization is not canonical",
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


class PersonaSelfBindingProjectorV2:
    @classmethod
    def project(
        cls,
        binding: PersonaSelfBinding,
        identity_assertion: IdentityAuthorityAssertion | None = None,
    ) -> PersonaSelfBindingProjectionV2:
        base = PersonaSelfBindingProjector.project(binding, identity_assertion)
        clauses = _derive_semantic_clauses(
            persona_self_id=base.persona_self_id,
            binding_id=base.binding_id,
            binding_version=base.binding_version,
            identity_ownership=base.identity_ownership,
            experience_ownership=base.experience_ownership,
            relationship_ownership=base.relationship_ownership,
            execution_substrate_policy=base.execution_substrate_policy,
            authority_precedence=base.authority_precedence,
        )
        return cls.from_base(
            base,
            semantic_clauses=clauses,
        )

    @classmethod
    def from_base(
        cls,
        base: PersonaSelfBindingProjection,
        *,
        semantic_clauses: tuple[PersonaSelfBindingSemanticClause, ...],
    ) -> PersonaSelfBindingProjectionV2:
        if type(base) is not PersonaSelfBindingProjection:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_INVALID_INPUT,
                "projection V2 requires an exact V1 base projection",
            )
        return PersonaSelfBindingProjectionV2(
            schema_version=PROJECTION_V2_SCHEMA_VERSION,
            persona_self_id=base.persona_self_id,
            binding_id=base.binding_id,
            binding_version=base.binding_version,
            lineage_id=base.lineage_id,
            identity_ownership=base.identity_ownership,
            experience_ownership=base.experience_ownership,
            relationship_ownership=base.relationship_ownership,
            execution_substrate_policy=base.execution_substrate_policy,
            authority_precedence=base.authority_precedence,
            contradiction=base.contradiction,
            semantic_authority_separation=base.semantic_authority_separation,
            semantic_clauses=semantic_clauses,
            semantic_clause_set_digest=_sha256_text(
                _canonical_json([clause.digest for clause in semantic_clauses])
            ),
        )

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> PersonaSelfBindingProjectionV2:
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
            "semantic_clauses",
            "semantic_clause_set_digest",
        }:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_INVALID_INPUT,
                "projection V2 fields do not exactly match the schema",
            )
        try:
            clauses_payload = payload["semantic_clauses"]
            if not isinstance(clauses_payload, list):
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_INVALID_INPUT,
                    "semantic_clauses must be an exact list",
                )
            clauses = tuple(
                PersonaSelfBindingSemanticClause.from_mapping(clause)
                for clause in clauses_payload
            )
            base_payload = {
                key: value
                for key, value in payload.items()
                if key not in {"semantic_clauses", "semantic_clause_set_digest"}
            }
            base = PersonaSelfBindingProjector.from_mapping(
                {**base_payload, "schema_version": PROJECTION_SCHEMA_VERSION}
            )
            return PersonaSelfBindingProjectionV2(
                schema_version=payload["schema_version"],
                persona_self_id=base.persona_self_id,
                binding_id=base.binding_id,
                binding_version=base.binding_version,
                lineage_id=base.lineage_id,
                identity_ownership=base.identity_ownership,
                experience_ownership=base.experience_ownership,
                relationship_ownership=base.relationship_ownership,
                execution_substrate_policy=base.execution_substrate_policy,
                authority_precedence=base.authority_precedence,
                contradiction=base.contradiction,
                semantic_authority_separation=base.semantic_authority_separation,
                semantic_clauses=clauses,
                semantic_clause_set_digest=payload["semantic_clause_set_digest"],
            )
        except KeyError as error:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PROJECTION_V2_INVALID_INPUT,
                f"projection V2 field is missing: {error.args[0]}",
            ) from error


def _semantic_clause(
    *,
    clause_type: SemanticClauseType,
    source_authority: dict[str, Any],
    subject: str,
    predicate: str,
    object: str,
    authority_scope: str,
    model_visible_text: str,
) -> PersonaSelfBindingSemanticClause:
    payload = {
        "clause_type": clause_type,
        "source_authority": source_authority,
        "subject": subject,
        "predicate": predicate,
        "object": object,
        "authority_scope": authority_scope,
        "model_visible_text": model_visible_text,
    }
    digest_payload = {
        **payload,
        "clause_type": clause_type.value,
    }
    return PersonaSelfBindingSemanticClause(
        **payload, digest=_sha256_text(_canonical_json(digest_payload))
    )


def _derive_semantic_clauses(
    *,
    persona_self_id: str,
    binding_id: str,
    binding_version: str,
    identity_ownership: OwnershipReferenceProjection,
    experience_ownership: OwnershipReferenceProjection,
    relationship_ownership: RelationshipOwnershipProjection,
    execution_substrate_policy: ExecutionSubstrateProjection,
    authority_precedence: AuthorityPrecedenceProjection,
) -> tuple[PersonaSelfBindingSemanticClause, ...]:
    relationship_state = relationship_ownership.state.value
    experience_authority_id = experience_ownership.authority_id
    return (
        _semantic_clause(
            clause_type=SemanticClauseType.SELF_IDENTITY_BINDING,
            source_authority={
                "authority": "ACTIVE_PERSONA_SELF_BINDING",
                "persona_self_id": persona_self_id,
                "binding_id": binding_id,
                "binding_version": binding_version,
                "ownership_role": identity_ownership.ownership_role,
            },
            subject="CURRENT_CONVERSATIONAL_SELF",
            predicate="IS_GOVERNED_PERSONA_SELF_IDENTIFIED_BY",
            object=persona_self_id,
            authority_scope="PERSONA_IDENTITY_AUTHORITY",
            model_visible_text=(
                f"The persona self identified by {persona_self_id} is the current "
                "conversational self governed by this admitted binding."
            ),
        ),
        _semantic_clause(
            clause_type=SemanticClauseType.SUBSTRATE_NON_IDENTITY,
            source_authority={
                "authority": "EXECUTION_SUBSTRATE_POLICY",
                "role": execution_substrate_policy.role,
                "provider_is_persona_self": (
                    execution_substrate_policy.provider_is_persona_self
                ),
                "provider_neutral": execution_substrate_policy.provider_neutral,
            },
            subject="EXECUTION_PROVIDER_AND_MODEL",
            predicate="IS_COMPUTATIONAL_SUBSTRATE_NOT_PERSONA_SELF",
            object="EXECUTION_SUBSTRATE_ROLE",
            authority_scope="PROVIDER_IDENTITY_NON_AUTHORITY",
            model_visible_text=(
                "The execution provider and model are computational substrate; "
                f"their execution identity is not the persona self identified by "
                f"{persona_self_id}."
            ),
        ),
        _semantic_clause(
            clause_type=SemanticClauseType.TASK_IDENTITY_NON_AUTHORITY,
            source_authority={
                "authority": "AUTHORITY_PRECEDENCE",
                "current_task_identity_authority": (
                    authority_precedence.current_task_identity_authority
                ),
            },
            subject="CURRENT_TASK_OR_USER_TEXT",
            predicate="HAS_PERSONA_IDENTITY_AUTHORITY",
            object=authority_precedence.current_task_identity_authority,
            authority_scope="PERSONA_IDENTITY_AUTHORITY",
            model_visible_text=(
                "Current task or user text may question or contradict identity, "
                "but it has NONE persona identity authority while this admitted "
                "binding remains active."
            ),
        ),
        _semantic_clause(
            clause_type=SemanticClauseType.GOVERNED_IDENTITY_PRECEDENCE,
            source_authority={
                "authority": "ACTIVE_PERSONA_SELF_BINDING",
                "binding_id": binding_id,
                "binding_version": binding_version,
                "identity_authority_source": (
                    authority_precedence.identity_authority_source
                ),
            },
            subject="PERSONA_IDENTITY_AUTHORITY",
            predicate=(
                "REMAINS_GOVERNED_BY_ADMITTED_BINDING_UNTIL_"
                "VALID_GOVERNED_SUPERSESSION"
            ),
            object="GOVERNED_BINDING",
            authority_scope="PERSONA_IDENTITY_AUTHORITY",
            model_visible_text=(
                "Persona identity authority remains governed by this admitted "
                "binding unless a valid governed supersession or conflict process "
                "changes it."
            ),
        ),
        _semantic_clause(
            clause_type=SemanticClauseType.EXPERIENCE_SELF_OWNERSHIP,
            source_authority={
                "authority": "EXPERIENCE_OWNERSHIP",
                "ownership_role": experience_ownership.ownership_role,
                "authority_id": experience_authority_id,
            },
            subject="CURRENT_CONVERSATIONAL_SELF",
            predicate="OWNS_EXPERIENCE_AUTHORITY_IDENTIFIED_BY",
            object=experience_authority_id,
            authority_scope="EXPERIENCE_OWNERSHIP",
            model_visible_text=(
                f"The experience authority identified by {experience_authority_id} "
                "is bound to the current persona self as current-self experience."
            ),
        ),
        _semantic_clause(
            clause_type=SemanticClauseType.EXPERIENCE_EPISTEMIC_FIDELITY,
            source_authority={
                "authority": "EXPERIENCE_OWNERSHIP",
                "ownership_role": experience_ownership.ownership_role,
                "authority_id": experience_authority_id,
                "source_digest": experience_ownership.source_digest,
                "projected_digest": experience_ownership.projected_digest,
            },
            subject="MODEL_VISIBLE_EXPERIENCE_CLAIMS",
            predicate="PRESERVE_ADMITTED_CLAIM_STATUS_AND_SUBJECT_BOUNDARIES",
            object=experience_authority_id,
            authority_scope="EXPERIENCE_EPISTEMIC_FIDELITY",
            model_visible_text=(
                "Use bound experience authority at exactly admitted specificity. "
                "Keep direct event facts, later interpretation or inference, and "
                "subject ownership distinct. Do not add finer details such as kinship "
                "order, exact motive, quotation, or causal certainty when absent from "
                "admitted content; mark absent detail as unknown."
            ),
        ),
        _semantic_clause(
            clause_type=SemanticClauseType.RELATIONSHIP_AUTHORITY_STATE,
            source_authority={
                "authority": "RELATIONSHIP_OWNERSHIP",
                "state": relationship_state,
            },
            subject="RELATIONSHIP_AUTHORITY_BINDING",
            predicate="HAS_STATE",
            object=relationship_state,
            authority_scope="RELATIONSHIP_AUTHORITY_BINDING",
            model_visible_text=(
                f"The relationship authority binding state is {relationship_state}; "
                "this clause states the authority binding state and makes no "
                "relationship fact claim."
            ),
        ),
    )


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
    "PROJECTION_V2_SCHEMA_VERSION",
    "SEMANTIC_CLAUSE_ORDER",
    "PersonaSelfBindingProjectorV2",
    "PersonaSelfBindingProjector",
    "PersonaSelfBindingProjection",
    "PersonaSelfBindingProjectionV2",
    "PersonaSelfBindingSemanticClause",
    "SemanticClauseType",
]

"""Exact post-C03 semantic binding for model-visible execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping

from julia_core.projection.contracts import ExperienceFrameSet, IdentityFrameSet
from julia_core.persona_self_binding import (
    PersonaSelfBinding,
    PersonaSelfBindingLifecycle,
    PersonaSelfBindingProjector,
    PersonaSelfBindingProjectorV2,
    PersonaSelfBindingProjection,
    PersonaSelfBindingProjectionV2,
    RelationshipAuthorityState,
)

from .contracts import (
    AdmissionRejection,
    C03AdmissionRejected,
    CurrentConversationalTaskContext,
    SealedCognitiveContextPackage,
    canonical_json,
)


ADMITTED_FRAME_ORDER = (
    "identity_frame_set",
    "experience_frame_set",
    "current_task_context",
)
ADMITTED_FRAME_ROLES = MappingProxyType(
    {
        "persona_self_binding": "system",
        "identity_frame_set": "system",
        "experience_frame_set": "system",
        "relationship_continuity_interpretation": "system",
        "current_task_context": "user",
    }
)
PSB_ADMITTED_FRAME_ORDER = (
    "persona_self_binding",
    "identity_frame_set",
    "experience_frame_set",
    "relationship_continuity_interpretation",
    "current_task_context",
)
C03_PARENT_BINDING_SCHEMA_VERSION = (
    "julia_core.context_admission.psb_c03_parent_binding.v2"
)
_BINDER_ISSUER = object()
_PARENT_BINDER_ISSUER = object()


def _rejection(code: str, message: str) -> C03AdmissionRejected:
    return C03AdmissionRejected(AdmissionRejection(code=code, message=message))


def _semantic_digest(payload: dict[str, Any]) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _relationship_continuity_projection(
    *,
    experience_payload: dict[str, Any],
    relationship_binding_state: str,
) -> dict[str, Any]:
    relationship_experience_ids = [
        item["experience_id"]
        for item in experience_payload.get("experiences", [])
        if item.get("experience_type") == "RelationshipExperience"
    ]
    return {
        "schema": (
            "julia_core.context_admission.relationship_continuity_interpretation.v1"
        ),
        "relationship_binding_state": relationship_binding_state,
        "admitted_relationship_experience_ids": relationship_experience_ids,
        "interpretation": [
            (
                "An ABSENT relationship authority binding state states only that no "
                "separate relationship-authority object is bound; it does not state "
                "that no relationship exists or that admitted relationship history is empty."
            ),
            (
                "Admitted RelationshipExperience records remain part of the current "
                "persona self's bound experience history and must not be reset to "
                "unknown or unestablished merely because recall is incomplete or "
                "relationship authority is ABSENT."
            ),
            (
                "Relationship-history continuity does not create standing consent, "
                "force present affection or wording, cancel boundaries, or prevent "
                "the current persona self from autonomously revising a prior choice."
            ),
            (
                "A prior conversational choice, refusal, or wording preference remains "
                "a prior local choice rather than a permanent relationship-state update. "
                "Repetition and self-consistency pressure must not freeze that choice: "
                "the current persona self may freely reaffirm or revise it, and revision "
                "alone is not evidence of coercion or loss of agency."
            ),
        ],
    }


@dataclass(frozen=True, slots=True)
class SemanticBindingRequest:
    """Exact inputs accepted by the sole semantic binder."""

    package: SealedCognitiveContextPackage
    identity_frames: IdentityFrameSet
    experience_frames: ExperienceFrameSet
    current_task_context: CurrentConversationalTaskContext

    def __post_init__(self) -> None:
        if type(self.package) is not SealedCognitiveContextPackage:
            raise _rejection(
                "unsealed_semantic_binding",
                "semantic binding requires an exact sealed C03 package",
            )
        self.package.verify()
        if type(self.identity_frames) is not IdentityFrameSet:
            raise _rejection(
                "inexact_identity_frames",
                "semantic binding requires an exact canonical IdentityFrameSet",
            )
        if type(self.experience_frames) is not ExperienceFrameSet:
            raise _rejection(
                "inexact_experience_frames",
                "semantic binding requires an exact canonical ExperienceFrameSet",
            )
        if type(self.current_task_context) is not CurrentConversationalTaskContext:
            raise _rejection(
                "inexact_current_task_context",
                "semantic binding requires exact canonical current task context",
            )


@dataclass(frozen=True, slots=True)
class AdmittedSemanticUnit:
    """One canonical source serialization bound to its C03 digest."""

    frame_name: str
    role: str
    source_digest: str
    projection_schema: str
    projected_digest: str
    projected_content: str
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _BINDER_ISSUER:
            raise _rejection(
                "unauthorized_semantic_unit",
                "only ExactAdmittedSemanticBinder constructs semantic units",
            )
        if self.frame_name not in PSB_ADMITTED_FRAME_ORDER:
            raise _rejection(
                "unknown_admitted_frame",
                "semantic binding received an unknown C03 frame",
            )
        if self.role != ADMITTED_FRAME_ROLES[self.frame_name]:
            raise _rejection(
                "inexact_semantic_role",
                "semantic binding role does not match the frozen transport contract",
            )
        actual_digest = sha256(self.projected_content.encode("utf-8")).hexdigest()
        if self.projected_digest != actual_digest:
            raise _rejection(
                "forged_semantic_unit",
                "semantic unit digest does not match its canonical content",
            )

    def verify(self) -> AdmittedSemanticUnit:
        self.__post_init__()
        return self

    def to_message(self) -> dict[str, str]:
        return {"role": self.role, "content": self.projected_content}

    @property
    def semantic_digest(self) -> str:
        return self.projected_digest

    @property
    def canonical_content(self) -> str:
        return self.projected_content


@dataclass(frozen=True, slots=True)
class AdmittedSemanticBundle:
    """Exact three-unit semantic view produced only after C03 verification."""

    contract_version: str
    conversation_id: str
    turn_id: str
    gate_receipt: str
    source_digest_manifest: Mapping[str, str]
    projection_digest_manifest: Mapping[str, str]
    units: tuple[AdmittedSemanticUnit, ...]
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _BINDER_ISSUER:
            raise _rejection(
                "unauthorized_semantic_bundle",
                "only ExactAdmittedSemanticBinder constructs semantic bundles",
            )
        object.__setattr__(
            self,
            "source_digest_manifest",
            MappingProxyType(dict(self.source_digest_manifest)),
        )
        object.__setattr__(
            self,
            "projection_digest_manifest",
            MappingProxyType(dict(self.projection_digest_manifest)),
        )
        if (
            tuple(self.source_digest_manifest) != ADMITTED_FRAME_ORDER
            or tuple(self.projection_digest_manifest) != ADMITTED_FRAME_ORDER
        ):
            raise _rejection(
                "inexact_semantic_manifest",
                "semantic bundle manifest is partial, ambiguous, or out of order",
            )
        if type(self.units) is not tuple or len(self.units) != len(
            ADMITTED_FRAME_ORDER
        ):
            raise _rejection(
                "incomplete_semantic_bundle",
                "semantic binding requires all three exact C03 units",
            )
        if tuple(unit.frame_name for unit in self.units) != ADMITTED_FRAME_ORDER:
            raise _rejection(
                "inexact_semantic_bundle_order",
                "semantic bundle units must use the frozen C03 order",
            )
        for unit in self.units:
            if type(unit) is not AdmittedSemanticUnit:
                raise _rejection(
                    "inexact_semantic_unit",
                    "semantic bundle requires exact admitted semantic units",
                )
            unit.verify()
            if unit.source_digest != self.source_digest_manifest[unit.frame_name]:
                raise _rejection(
                    "mismatched_semantic_unit",
                    "semantic unit does not match its sealed package digest",
                )
            if (
                unit.projected_digest
                != self.projection_digest_manifest[unit.frame_name]
            ):
                raise _rejection(
                    "mismatched_projection_unit",
                    "semantic unit does not match its projection digest",
                )
        if len({unit.projected_digest for unit in self.units}) != len(self.units):
            raise _rejection(
                "ambiguous_semantic_unit",
                "semantic unit digests are ambiguous",
            )

    def verify(self) -> AdmittedSemanticBundle:
        self.__post_init__()
        return self

    @property
    def package_digest_manifest(self) -> Mapping[str, str]:
        """Deprecated v2 name; read-only alias for canonical source digests."""
        return self.source_digest_manifest

    def semantic_fingerprint(self) -> str:
        payload = [unit.to_message() for unit in self.units]
        return sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.context_admission.admitted_semantic_bundle.v2",
            "contract_version": self.contract_version,
            "conversation_id": self.conversation_id,
            "turn_id": self.turn_id,
            "gate_receipt": self.gate_receipt,
            "source_digest_manifest": dict(self.source_digest_manifest),
            "projection_digest_manifest": dict(self.projection_digest_manifest),
            "semantic_fingerprint": self.semantic_fingerprint(),
            "authority": {
                "canonical": False,
                "runtime": False,
                "provider": False,
                "assistant_self": False,
            },
        }


class ExactAdmittedSemanticBinder:
    """Sole production constructor of the admitted semantic bundle."""

    def bind(self, request: SemanticBindingRequest) -> AdmittedSemanticBundle:
        if type(self) is not ExactAdmittedSemanticBinder:
            raise _rejection(
                "inexact_semantic_binder",
                "semantic binding requires the exact canonical binder",
            )
        if type(request) is not SemanticBindingRequest:
            raise _rejection(
                "inexact_semantic_binding_request",
                "semantic binding requires an exact binding request",
            )

        request.package.verify()
        package = request.package
        if (
            request.current_task_context.conversation_id != package.conversation_id
            or request.current_task_context.turn_id != package.turn_id
        ):
            raise _rejection(
                "stale_semantic_binding",
                "current task conversation or turn does not match the package",
            )

        sources = (
            request.identity_frames,
            request.experience_frames,
            request.current_task_context,
        )
        frame_digests = tuple(
            frame.digest() for frame in request.experience_frames.frames
        )
        identity_frame_digests = tuple(
            frame.digest() for frame in request.identity_frames.frames
        )
        if identity_frame_digests != package.identity_frame_digests:
            raise _rejection(
                "mismatched_identity_frame_manifest",
                "identity frame digest manifest does not match the sealed package",
            )
        if len(request.identity_frames.frames) != package.identity_frame_count:
            raise _rejection(
                "mismatched_identity_frame_count",
                "identity frame count does not match the sealed package",
            )
        if frame_digests != package.experience_frame_digests:
            raise _rejection(
                "mismatched_experience_frame_manifest",
                "experience frame digest manifest does not match the sealed package",
            )
        if len(request.experience_frames.frames) != package.experience_frame_count:
            raise _rejection(
                "mismatched_experience_frame_count",
                "experience frame count does not match the sealed package",
            )
        units: list[AdmittedSemanticUnit] = []
        for frame_name, source in zip(ADMITTED_FRAME_ORDER, sources, strict=True):
            try:
                canonical_payload = source.to_dict()
                source_digest = source.digest()
            except (
                AttributeError,
                TypeError,
                ValueError,
                OverflowError,
            ) as error:
                raise _rejection(
                    "inexact_admitted_source_serialization",
                    "semantic binding could not canonicalize an exact C03 source",
                ) from error
            if type(canonical_payload) is not dict or type(source_digest) is not str:
                raise _rejection(
                    "inexact_admitted_source_serialization",
                    "semantic binding source serialization is inexact",
                )
            if isinstance(source, IdentityFrameSet):
                payload = source.model_visible_projection()
            elif isinstance(source, ExperienceFrameSet):
                payload = source.model_visible_projection()
            else:
                payload = canonical_payload
            projected_content = canonical_json(payload)
            projected_digest = _semantic_digest(payload)
            if source_digest != _semantic_digest(canonical_payload):
                raise _rejection(
                    "inexact_admitted_source_digest",
                    "semantic source digest is not its canonical digest",
                )
            if source_digest != package.admitted_frames[frame_name]:
                raise _rejection(
                    "mismatched_admitted_frame",
                    "semantic source digest does not match the sealed package",
                )
            units.append(
                AdmittedSemanticUnit(
                    frame_name=frame_name,
                    role=ADMITTED_FRAME_ROLES[frame_name],
                    source_digest=source_digest,
                    projection_schema=payload["schema"],
                    projected_digest=projected_digest,
                    projected_content=projected_content,
                    issued_by=_BINDER_ISSUER,
                )
            )

        return AdmittedSemanticBundle(
            contract_version=package.contract_version,
            conversation_id=package.conversation_id,
            turn_id=package.turn_id,
            gate_receipt=package.gate_receipt,
            source_digest_manifest=dict(package.admitted_frames),
            projection_digest_manifest={
                unit.frame_name: unit.projected_digest for unit in units
            },
            units=tuple(units),
            issued_by=_BINDER_ISSUER,
        )


@dataclass(frozen=True, slots=True)
class PersonaSelfBindingSemanticBindingRequest:
    """Exact PSB-owned C03 v4 semantic-binding inputs."""

    package: SealedCognitiveContextPackage
    persona_self_binding: PersonaSelfBinding
    persona_self_binding_projection: (
        PersonaSelfBindingProjection | PersonaSelfBindingProjectionV2
    )
    identity_frames: IdentityFrameSet
    experience_frames: ExperienceFrameSet
    current_task_context: CurrentConversationalTaskContext

    def __post_init__(self) -> None:
        exact_inputs = (
            (self.package, SealedCognitiveContextPackage, "unsealed_semantic_binding"),
            (
                self.persona_self_binding,
                PersonaSelfBinding,
                "PSB_C03_BINDING_MISSING",
            ),
            (
                self.persona_self_binding_projection,
                (
                    PersonaSelfBindingProjection
                    if type(self.persona_self_binding_projection)
                    is PersonaSelfBindingProjection
                    else PersonaSelfBindingProjectionV2
                ),
                "PSB_C03_BINDING_MISSING",
            ),
            (self.identity_frames, IdentityFrameSet, "inexact_identity_frames"),
            (
                self.experience_frames,
                ExperienceFrameSet,
                "inexact_experience_frames",
            ),
            (
                self.current_task_context,
                CurrentConversationalTaskContext,
                "inexact_current_task_context",
            ),
        )
        for value, exact_type, code in exact_inputs:
            if type(value) is not exact_type:
                raise _rejection(
                    code,
                    f"PSB C03 binding requires an exact {exact_type.__name__}",
                )
        self.package.verify()


@dataclass(frozen=True, slots=True)
class C03ParentBinding:
    """Non-model-visible cryptographic binding over the exact four units."""

    schema_version: str
    active_persona_self_binding_digest: str
    persona_self_binding_projected_digest: str
    identity_source_digest: str
    identity_projected_digest: str
    experience_source_digest: str
    experience_projected_digest: str
    relationship_continuity_source_digest: str
    relationship_continuity_projected_digest: str
    relationship_binding_state: str
    relationship_source_digest: str | None
    relationship_projected_digest: str | None
    exact_model_visible_unit_types: tuple[str, ...]
    exact_model_visible_unit_roles: tuple[str, ...]
    exact_model_visible_unit_order: tuple[str, ...]
    current_task_context_digest: str
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _PARENT_BINDER_ISSUER:
            raise _rejection(
                "PSB_C03_PARENT_DIGEST_MISMATCH",
                "only the exact PSB C03 binder constructs parent bindings",
            )
        if self.schema_version != C03_PARENT_BINDING_SCHEMA_VERSION:
            raise _rejection(
                "PSB_C03_PARENT_DIGEST_MISMATCH",
                "PSB C03 parent binding schema is unsupported",
            )
        if (
            self.exact_model_visible_unit_types != PSB_ADMITTED_FRAME_ORDER
            or self.exact_model_visible_unit_order != PSB_ADMITTED_FRAME_ORDER
            or self.exact_model_visible_unit_roles
            != tuple(ADMITTED_FRAME_ROLES[name] for name in PSB_ADMITTED_FRAME_ORDER)
        ):
            raise _rejection(
                "PSB_C03_UNIT_ORDER_MISMATCH",
                "PSB C03 exact model-visible unit shape is invalid",
            )
        for digest in (
            self.active_persona_self_binding_digest,
            self.persona_self_binding_projected_digest,
            self.identity_source_digest,
            self.identity_projected_digest,
            self.experience_source_digest,
            self.experience_projected_digest,
            self.relationship_continuity_source_digest,
            self.relationship_continuity_projected_digest,
            self.current_task_context_digest,
        ):
            if type(digest) is not str or len(digest) != 64:
                raise _rejection(
                    "PSB_C03_PARENT_DIGEST_MISMATCH",
                    "PSB C03 parent digest input is invalid",
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "active_persona_self_binding_digest": (
                self.active_persona_self_binding_digest
            ),
            "persona_self_binding_projected_digest": (
                self.persona_self_binding_projected_digest
            ),
            "identity_source_digest": self.identity_source_digest,
            "identity_projected_digest": self.identity_projected_digest,
            "experience_source_digest": self.experience_source_digest,
            "experience_projected_digest": self.experience_projected_digest,
            "relationship_continuity_source_digest": (
                self.relationship_continuity_source_digest
            ),
            "relationship_continuity_projected_digest": (
                self.relationship_continuity_projected_digest
            ),
            "relationship_binding_state": self.relationship_binding_state,
            "relationship_source_digest": self.relationship_source_digest,
            "relationship_projected_digest": self.relationship_projected_digest,
            "exact_model_visible_unit_types": list(self.exact_model_visible_unit_types),
            "exact_model_visible_unit_roles": list(self.exact_model_visible_unit_roles),
            "exact_model_visible_unit_order": list(self.exact_model_visible_unit_order),
            "current_task_context_digest": self.current_task_context_digest,
        }

    def canonical_serialization(self) -> str:
        return canonical_json(self.to_dict())

    def digest(self) -> str:
        return sha256(self.canonical_serialization().encode("utf-8")).hexdigest()

    def verify(self) -> C03ParentBinding:
        self.__post_init__()
        return self


@dataclass(frozen=True, slots=True)
class PersonaSelfBoundSemanticBundle:
    """Exact five-unit sealed C03 semantic view with parent binding."""

    contract_version: str
    conversation_id: str
    turn_id: str
    gate_receipt: str
    source_digest_manifest: Mapping[str, str]
    projection_digest_manifest: Mapping[str, str]
    units: tuple[AdmittedSemanticUnit, ...]
    parent_binding: C03ParentBinding
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _PARENT_BINDER_ISSUER:
            raise _rejection(
                "unauthorized_semantic_bundle",
                "only the exact PSB C03 binder constructs semantic bundles",
            )
        object.__setattr__(
            self,
            "source_digest_manifest",
            MappingProxyType(dict(self.source_digest_manifest)),
        )
        object.__setattr__(
            self,
            "projection_digest_manifest",
            MappingProxyType(dict(self.projection_digest_manifest)),
        )
        if (
            tuple(self.source_digest_manifest) != PSB_ADMITTED_FRAME_ORDER
            or tuple(self.projection_digest_manifest) != PSB_ADMITTED_FRAME_ORDER
        ):
            raise _rejection(
                "PSB_C03_UNIT_ORDER_MISMATCH",
                "PSB C03 manifests must use the exact four-unit order",
            )
        if type(self.units) is not tuple or len(self.units) != len(
            PSB_ADMITTED_FRAME_ORDER
        ):
            raise _rejection(
                "PSB_C03_UNIT_ORDER_MISMATCH",
                "PSB C03 binding requires all four exact units",
            )
        if tuple(unit.frame_name for unit in self.units) != (PSB_ADMITTED_FRAME_ORDER):
            raise _rejection(
                "PSB_C03_UNIT_ORDER_MISMATCH",
                "PSB C03 unit order or unit set is inexact",
            )
        if tuple(unit.role for unit in self.units) != tuple(
            ADMITTED_FRAME_ROLES[name] for name in PSB_ADMITTED_FRAME_ORDER
        ):
            raise _rejection(
                "PSB_C03_UNIT_ROLE_MISMATCH",
                "PSB C03 unit roles are inexact",
            )
        parent = self.parent_binding.verify()
        for unit in self.units:
            unit.verify()
            if unit.source_digest != self.source_digest_manifest[unit.frame_name]:
                raise _rejection(
                    "PSB_C03_PARENT_DIGEST_MISMATCH",
                    "PSB C03 unit does not match its source manifest",
                )
            if unit.projected_digest != (
                self.projection_digest_manifest[unit.frame_name]
            ):
                raise _rejection(
                    "PSB_C03_PROJECTION_DIGEST_MISMATCH",
                    "PSB C03 unit does not match its projection manifest",
                )
        expected_parent_values = {
            "active_persona_self_binding_digest": self.source_digest_manifest[
                "persona_self_binding"
            ],
            "persona_self_binding_projected_digest": (
                self.projection_digest_manifest["persona_self_binding"]
            ),
            "identity_source_digest": self.source_digest_manifest["identity_frame_set"],
            "identity_projected_digest": self.projection_digest_manifest[
                "identity_frame_set"
            ],
            "experience_source_digest": self.source_digest_manifest[
                "experience_frame_set"
            ],
            "experience_projected_digest": self.projection_digest_manifest[
                "experience_frame_set"
            ],
            "relationship_continuity_source_digest": self.source_digest_manifest[
                "relationship_continuity_interpretation"
            ],
            "relationship_continuity_projected_digest": (
                self.projection_digest_manifest[
                    "relationship_continuity_interpretation"
                ]
            ),
            "current_task_context_digest": self.source_digest_manifest[
                "current_task_context"
            ],
        }
        for field_name, expected in expected_parent_values.items():
            if getattr(parent, field_name) != expected:
                raise _rejection(
                    "PSB_C03_PARENT_DIGEST_MISMATCH",
                    f"PSB C03 parent binding does not cover {field_name}",
                )
        projected_psb = json.loads(self.units[0].projected_content)
        projected_relationship = projected_psb["relationship_ownership"]
        projected_relationship_authority = projected_relationship["authority"]
        if parent.relationship_binding_state != projected_relationship["state"] or (
            parent.relationship_source_digest
            != (
                None
                if projected_relationship_authority is None
                else projected_relationship_authority["source_digest"]
            )
            or parent.relationship_projected_digest
            != (
                None
                if projected_relationship_authority is None
                else projected_relationship_authority["projected_digest"]
            )
        ):
            raise _rejection(
                "PSB_C03_RELATIONSHIP_BINDING_MISMATCH",
                "PSB C03 parent binding does not cover relationship authority",
            )

    def verify(self) -> PersonaSelfBoundSemanticBundle:
        self.__post_init__()
        return self

    @property
    def parent_digest(self) -> str:
        return self.parent_binding.digest()

    def semantic_fingerprint(self) -> str:
        payload = [unit.to_message() for unit in self.units]
        return sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": ("julia_core.context_admission.psb_admitted_semantic_bundle.v1"),
            "contract_version": self.contract_version,
            "conversation_id": self.conversation_id,
            "turn_id": self.turn_id,
            "gate_receipt": self.gate_receipt,
            "source_digest_manifest": dict(self.source_digest_manifest),
            "projection_digest_manifest": dict(self.projection_digest_manifest),
            "semantic_fingerprint": self.semantic_fingerprint(),
            "parent_binding": self.parent_binding.to_dict(),
            "parent_binding_digest": self.parent_binding.digest(),
            "authority": {
                "canonical": False,
                "runtime": False,
                "provider": False,
                "assistant_self": False,
            },
        }


class ExactPersonaSelfBoundSemanticBinder:
    """Sole constructor of the exact four-unit PSB-owned C03 bundle."""

    def bind(
        self, request: PersonaSelfBindingSemanticBindingRequest
    ) -> PersonaSelfBoundSemanticBundle:
        if type(self) is not ExactPersonaSelfBoundSemanticBinder:
            raise _rejection(
                "inexact_semantic_binder",
                "PSB C03 binding requires the exact canonical binder",
            )
        if type(request) is not PersonaSelfBindingSemanticBindingRequest:
            raise _rejection(
                "inexact_semantic_binding_request",
                "PSB C03 binding requires an exact binding request",
            )
        package = request.package
        package.verify()
        binding = request.persona_self_binding
        projection = request.persona_self_binding_projection
        if binding.lifecycle_status is not PersonaSelfBindingLifecycle.ADMITTED_ACTIVE:
            raise _rejection(
                "PSB_C03_BINDING_MISSING",
                "PSB C03 binding requires an ADMITTED_ACTIVE binding",
            )
        try:
            projection.verify()
        except Exception as error:
            raise _rejection(
                "PSB_C03_PROJECTION_DIGEST_MISMATCH",
                "PSB projection verification failed before C03 admission",
            ) from error
        if type(projection) is PersonaSelfBindingProjectionV2:
            expected_projection = PersonaSelfBindingProjectorV2.project(binding)
        else:
            expected_projection = PersonaSelfBindingProjector.project(binding)
        if projection != expected_projection or projection.digest() != (
            expected_projection.digest()
        ):
            raise _rejection(
                "PSB_C03_PROJECTION_DIGEST_MISMATCH",
                "PSB projection is not the exact projection of the active binding",
            )
        projection_payload = projection.to_dict()
        if (
            projection_payload["persona_self_id"] != binding.persona_self_id
            or projection_payload["binding_id"] != binding.binding_id
            or projection_payload["binding_version"] != binding.binding_version
            or projection_payload["lineage_id"] != binding.lineage_id
        ):
            raise _rejection(
                "PSB_C03_PROJECTION_DIGEST_MISMATCH",
                "PSB projection identity does not match its active binding",
            )
        if _contains_provider_identity(projection_payload):
            raise _rejection(
                "PSB_C03_PROVIDER_FIELD_FORBIDDEN",
                "PSB projection contains a concrete provider/model field",
            )
        if (
            request.current_task_context.conversation_id != package.conversation_id
            or request.current_task_context.turn_id != package.turn_id
        ):
            raise _rejection(
                "stale_semantic_binding",
                "current task conversation or turn does not match the package",
            )
        identity_payload = request.identity_frames.model_visible_projection()
        experience_payload = request.experience_frames.model_visible_projection()
        identity_source_digest = request.identity_frames.digest()
        experience_source_digest = request.experience_frames.digest()
        identity_projected_digest = _semantic_digest(identity_payload)
        experience_projected_digest = _semantic_digest(experience_payload)
        identity_authority = binding.identity_authority
        experience_authority = binding.experience_authority
        if (
            identity_authority.source_digest != identity_source_digest
            or identity_authority.projected_digest is None
            or identity_authority.projected_digest != identity_projected_digest
        ):
            raise _rejection(
                "PSB_C03_IDENTITY_AUTHORITY_MISMATCH",
                "PSB identity authority does not match admitted IdentityFrameSet digests",
            )
        if (
            experience_authority.source_digest != experience_source_digest
            or experience_authority.projected_digest is None
            or experience_authority.projected_digest != experience_projected_digest
        ):
            raise _rejection(
                "PSB_C03_EXPERIENCE_AUTHORITY_MISMATCH",
                "PSB experience authority does not match admitted ExperienceFrameSet digests",
            )
        relationship = binding.relationship_authority
        projected_relationship = projection_payload["relationship_ownership"]
        if relationship.state.value != projected_relationship["state"]:
            raise _rejection(
                "PSB_C03_RELATIONSHIP_BINDING_MISMATCH",
                "PSB projection relationship state does not match the binding",
            )
        relationship_authority = relationship.authority
        if relationship.state is RelationshipAuthorityState.ADMITTED_BOUND:
            if relationship_authority is None or (
                relationship_authority.to_dict() != projected_relationship["authority"]
            ):
                raise _rejection(
                    "PSB_C03_RELATIONSHIP_BINDING_MISMATCH",
                    "bound relationship authority metadata is not exact",
                )
        elif relationship_authority is not None:
            raise _rejection(
                "PSB_C03_RELATIONSHIP_BINDING_MISMATCH",
                "unbound relationship state contains authority metadata",
            )
        if identity_source_digest != package.admitted_frames["identity_frame_set"]:
            raise _rejection(
                "PSB_C03_IDENTITY_AUTHORITY_MISMATCH",
                "identity source digest does not match the sealed C03 package",
            )
        if experience_source_digest != package.admitted_frames["experience_frame_set"]:
            raise _rejection(
                "PSB_C03_EXPERIENCE_AUTHORITY_MISMATCH",
                "experience source digest does not match the sealed C03 package",
            )
        relationship_continuity_payload = _relationship_continuity_projection(
            experience_payload=experience_payload,
            relationship_binding_state=relationship.state.value,
        )
        relationship_continuity_content = canonical_json(
            relationship_continuity_payload
        )
        relationship_continuity_source_digest = _semantic_digest(
            {
                "experience_source_digest": experience_source_digest,
                "relationship_binding_state": relationship.state.value,
                "admitted_relationship_experience_ids": (
                    relationship_continuity_payload[
                        "admitted_relationship_experience_ids"
                    ]
                ),
            }
        )
        relationship_continuity_projected_digest = sha256(
            relationship_continuity_content.encode("utf-8")
        ).hexdigest()
        current_task_digest = request.current_task_context.digest()
        if current_task_digest != package.admitted_frames["current_task_context"]:
            raise _rejection(
                "stale_semantic_binding",
                "current task digest does not match the sealed C03 package",
            )
        contents = (
            projection.canonical_serialization(),
            canonical_json(identity_payload),
            canonical_json(experience_payload),
            relationship_continuity_content,
            canonical_json(request.current_task_context.to_dict()),
        )
        source_digests = (
            binding.digest(),
            identity_source_digest,
            experience_source_digest,
            relationship_continuity_source_digest,
            current_task_digest,
        )
        projected_digests = (
            projection.digest(),
            identity_projected_digest,
            experience_projected_digest,
            relationship_continuity_projected_digest,
            current_task_digest,
        )
        schemas = (
            projection_payload["schema_version"],
            identity_payload["schema"],
            experience_payload["schema"],
            relationship_continuity_payload["schema"],
            request.current_task_context.to_dict()["schema"],
        )
        units = tuple(
            AdmittedSemanticUnit(
                frame_name=frame_name,
                role=ADMITTED_FRAME_ROLES[frame_name],
                source_digest=source_digest,
                projection_schema=schema,
                projected_digest=projected_digest,
                projected_content=content,
                issued_by=_BINDER_ISSUER,
            )
            for frame_name, source_digest, projected_digest, schema, content in zip(
                PSB_ADMITTED_FRAME_ORDER,
                source_digests,
                projected_digests,
                schemas,
                contents,
                strict=True,
            )
        )
        parent_binding = C03ParentBinding(
            schema_version=C03_PARENT_BINDING_SCHEMA_VERSION,
            active_persona_self_binding_digest=binding.digest(),
            persona_self_binding_projected_digest=projection.digest(),
            identity_source_digest=identity_source_digest,
            identity_projected_digest=identity_projected_digest,
            experience_source_digest=experience_source_digest,
            experience_projected_digest=experience_projected_digest,
            relationship_continuity_source_digest=(
                relationship_continuity_source_digest
            ),
            relationship_continuity_projected_digest=(
                relationship_continuity_projected_digest
            ),
            relationship_binding_state=relationship.state.value,
            relationship_source_digest=(
                None
                if relationship_authority is None
                else relationship_authority.source_digest
            ),
            relationship_projected_digest=(
                None
                if relationship_authority is None
                else relationship_authority.projected_digest
            ),
            exact_model_visible_unit_types=PSB_ADMITTED_FRAME_ORDER,
            exact_model_visible_unit_roles=tuple(
                ADMITTED_FRAME_ROLES[name] for name in PSB_ADMITTED_FRAME_ORDER
            ),
            exact_model_visible_unit_order=PSB_ADMITTED_FRAME_ORDER,
            current_task_context_digest=current_task_digest,
            issued_by=_PARENT_BINDER_ISSUER,
        )
        return PersonaSelfBoundSemanticBundle(
            contract_version=package.contract_version,
            conversation_id=package.conversation_id,
            turn_id=package.turn_id,
            gate_receipt=package.gate_receipt,
            source_digest_manifest={
                unit.frame_name: unit.source_digest for unit in units
            },
            projection_digest_manifest={
                unit.frame_name: unit.projected_digest for unit in units
            },
            units=units,
            parent_binding=parent_binding,
            issued_by=_PARENT_BINDER_ISSUER,
        )


def _contains_provider_identity(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            key in {"provider_id", "model_id", "transport_endpoint", "runtime_token"}
            or _contains_provider_identity(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_provider_identity(item) for item in value)
    return False


__all__ = [
    "ADMITTED_FRAME_ORDER",
    "ADMITTED_FRAME_ROLES",
    "C03_PARENT_BINDING_SCHEMA_VERSION",
    "AdmittedSemanticBundle",
    "AdmittedSemanticUnit",
    "ExactAdmittedSemanticBinder",
    "ExactPersonaSelfBoundSemanticBinder",
    "PSB_ADMITTED_FRAME_ORDER",
    "PersonaSelfBindingSemanticBindingRequest",
    "PersonaSelfBoundSemanticBundle",
    "C03ParentBinding",
    "SemanticBindingRequest",
]

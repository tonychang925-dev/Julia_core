"""Exclusive fail-closed admission gate for production C03."""
from __future__ import annotations

from types import MappingProxyType
from typing import Any

from julia_core.identity import IdentityStatus
from julia_core.memory_experience import MemoryExperienceStatus
from julia_core.projection.contracts import (
    EXPERIENCE_FRAME_SCHEMA_VERSION,
    EXPERIENCE_PROJECTION_POLICY_ID,
    EXPERIENCE_PROJECTION_POLICY_VERSION,
    IDENTITY_FRAME_SCHEMA_VERSION,
    PERSONA_PROJECTION_POLICY_ID,
    PERSONA_PROJECTION_POLICY_VERSION,
    ExperienceFrame,
    IdentityFrame,
)

from .contracts import (
    CurrentConversationalTaskContext,
    AdmissionRejection,
    C03AdmissionRejected,
    ExclusiveAdmissionRequest,
    SealedCognitiveContextPackage,
    _require_digest,
    _require_string,
    package_digest,
)


C03_PRODUCTION_CONTRACT_VERSION = "julia_core.context_admission.c03.production.v1"
C03_ADMISSION_ISSUER = object()


class ExclusiveAdmissionGate:
    """Seals the three exact governed inputs or returns no package."""

    def seal(self, request: ExclusiveAdmissionRequest) -> SealedCognitiveContextPackage:
        if type(self) is not ExclusiveAdmissionGate:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_admission_gate",
                    message="C03 admission gate type is inexact",
                )
            )
        if type(request) is not ExclusiveAdmissionRequest:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_admission_request",
                    message="C03 admission request type is inexact",
                )
            )

        identity = request.identity_frame
        experience = request.experience_frame
        current_task = request.current_task_context
        if (
            type(identity) is not IdentityFrame
            or type(experience) is not ExperienceFrame
            or type(current_task) is not CurrentConversationalTaskContext
        ):
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="partial_admission_forbidden",
                    message="C03 requires all exact canonical inputs",
                )
            )

        _require_identity_frame(identity)
        _require_experience_frame(experience)
        identity_digest = _frame_digest(identity, "identity frame")
        experience_digest = _frame_digest(experience, "experience frame")
        current_task_digest = _digest(current_task.digest(), "current task context")
        receipt = package_digest(
            C03_PRODUCTION_CONTRACT_VERSION,
            current_task.conversation_id,
            current_task.turn_id,
            identity_digest,
            experience_digest,
            current_task_digest,
        )
        return SealedCognitiveContextPackage(
            contract_version=C03_PRODUCTION_CONTRACT_VERSION,
            conversation_id=current_task.conversation_id,
            turn_id=current_task.turn_id,
            identity_digest=identity_digest,
            experience_digest=experience_digest,
            current_task_digest=current_task_digest,
            gate_receipt=receipt,
            admitted_frames={
                "identity_frame": identity_digest,
                "experience_frame": experience_digest,
                "current_task_context": current_task_digest,
            },
            issued_by=C03_ADMISSION_ISSUER,
        )


class ModelVisibilityTransport:
    """Validation-only boundary proving visibility starts at a sealed package."""

    def render(self, candidate: Any) -> dict[str, Any]:
        if type(candidate) is not SealedCognitiveContextPackage:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="unsealed_model_visibility_input",
                    message="model visibility requires a sealed C03 package",
                )
            )
        expected_receipt = package_digest(
            candidate.contract_version,
            candidate.conversation_id,
            candidate.turn_id,
            candidate.identity_digest,
            candidate.experience_digest,
            candidate.current_task_digest,
        )
        if candidate.gate_receipt != expected_receipt:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="forged_visibility_receipt",
                    message="model visibility package receipt is forged",
                )
            )
        candidate.verify()
        return candidate.to_dict()


def _require_identity_frame(frame: IdentityFrame) -> None:
    _require_frame(
        frame,
        frame_name="identity frame",
        schema_version=IDENTITY_FRAME_SCHEMA_VERSION,
        policy_id=PERSONA_PROJECTION_POLICY_ID,
        policy_version=PERSONA_PROJECTION_POLICY_VERSION,
        admitted_status=IdentityStatus.ADMITTED,
    )


def _require_experience_frame(frame: ExperienceFrame) -> None:
    _require_frame(
        frame,
        frame_name="experience frame",
        schema_version=EXPERIENCE_FRAME_SCHEMA_VERSION,
        policy_id=EXPERIENCE_PROJECTION_POLICY_ID,
        policy_version=EXPERIENCE_PROJECTION_POLICY_VERSION,
        admitted_status=MemoryExperienceStatus.ADMITTED,
    )


def _require_frame(
    frame: IdentityFrame | ExperienceFrame,
    *,
    frame_name: str,
    schema_version: str,
    policy_id: str,
    policy_version: str,
    admitted_status: IdentityStatus | MemoryExperienceStatus,
) -> None:
    if (
        frame.schema_version != schema_version
        or frame.policy_id != policy_id
        or frame.policy_version != policy_version
    ):
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="non_canonical_frame_contract",
                message=f"{frame_name} projection contract is inexact",
            )
        )
    if frame.source_status is not admitted_status:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="non_admitted_source",
                message=f"{frame_name.replace(' frame', '')} source is not admitted",
            )
        )
    _require_digest(
        frame.source_digest, f"{frame_name.replace(' frame', '')} source digest"
    )
    _require_frame_provenance(frame, frame_name)


def _require_frame_provenance(
    frame: IdentityFrame | ExperienceFrame, frame_name: str
) -> None:
    if type(frame.provenance_refs) is not tuple or not frame.provenance_refs:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="absent_frame_provenance",
                message=f"{frame_name} provenance is absent",
            )
        )
    exact_binding = False
    for provenance in frame.provenance_refs:
        if type(provenance) not in (dict, MappingProxyType):
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_frame_provenance",
                    message=f"{frame_name} provenance is inexact",
                )
            )
        source_ref = provenance.get("source_ref")
        _require_string(source_ref, f"{frame_name} provenance source ref")
        source_digest = provenance.get("source_digest")
        _require_digest(source_digest, f"{frame_name} provenance digest")
        if "://" not in source_ref:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_frame_provenance",
                    message=f"{frame_name} provenance source ref is inexact",
                )
            )
        if source_digest == frame.source_digest:
            exact_binding = True
    if not exact_binding:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="inexact_frame_provenance_digest",
                message=f"{frame_name} provenance digest is inexact",
            )
        )


def _frame_digest(frame: IdentityFrame | ExperienceFrame, frame_name: str) -> str:
    try:
        value = frame.digest()
    except (TypeError, ValueError, OverflowError) as error:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="non_deterministic_frame",
                message=f"{frame_name} digest is not deterministic",
            )
        ) from error
    return _digest(value, frame_name)


def _digest(value: str, field_name: str) -> str:
    _require_digest(value, f"{field_name} digest")
    return value


__all__ = [
    "C03_PRODUCTION_CONTRACT_VERSION",
    "ExclusiveAdmissionGate",
    "ModelVisibilityTransport",
]

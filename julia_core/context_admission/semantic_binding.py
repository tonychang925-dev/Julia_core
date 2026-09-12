"""Exact post-C03 semantic binding for model-visible execution."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping

from julia_core.projection.contracts import ExperienceFrame, IdentityFrame

from .contracts import (
    AdmissionRejection,
    C03AdmissionRejected,
    CurrentConversationalTaskContext,
    SealedCognitiveContextPackage,
    canonical_json,
)


ADMITTED_FRAME_ORDER = (
    "identity_frame",
    "experience_frame",
    "current_task_context",
)
ADMITTED_FRAME_ROLES = MappingProxyType(
    {
        "identity_frame": "system",
        "experience_frame": "system",
        "current_task_context": "user",
    }
)
_BINDER_ISSUER = object()


def _rejection(code: str, message: str) -> C03AdmissionRejected:
    return C03AdmissionRejected(AdmissionRejection(code=code, message=message))


def _semantic_digest(payload: dict[str, Any]) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SemanticBindingRequest:
    """Exact inputs accepted by the sole semantic binder."""

    package: SealedCognitiveContextPackage
    identity_frame: IdentityFrame
    experience_frame: ExperienceFrame
    current_task_context: CurrentConversationalTaskContext

    def __post_init__(self) -> None:
        if type(self.package) is not SealedCognitiveContextPackage:
            raise _rejection(
                "unsealed_semantic_binding",
                "semantic binding requires an exact sealed C03 package",
            )
        self.package.verify()
        if type(self.identity_frame) is not IdentityFrame:
            raise _rejection(
                "inexact_identity_frame",
                "semantic binding requires an exact canonical IdentityFrame",
            )
        if type(self.experience_frame) is not ExperienceFrame:
            raise _rejection(
                "inexact_experience_frame",
                "semantic binding requires an exact canonical ExperienceFrame",
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
    semantic_digest: str
    canonical_content: str
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _BINDER_ISSUER:
            raise _rejection(
                "unauthorized_semantic_unit",
                "only ExactAdmittedSemanticBinder constructs semantic units",
            )
        if self.frame_name not in ADMITTED_FRAME_ORDER:
            raise _rejection(
                "unknown_admitted_frame",
                "semantic binding received an unknown C03 frame",
            )
        if self.role != ADMITTED_FRAME_ROLES[self.frame_name]:
            raise _rejection(
                "inexact_semantic_role",
                "semantic binding role does not match the frozen transport contract",
            )
        actual_digest = sha256(
            self.canonical_content.encode("utf-8")
        ).hexdigest()
        if self.semantic_digest != actual_digest:
            raise _rejection(
                "forged_semantic_unit",
                "semantic unit digest does not match its canonical content",
            )

    def verify(self) -> AdmittedSemanticUnit:
        self.__post_init__()
        return self

    def to_message(self) -> dict[str, str]:
        return {"role": self.role, "content": self.canonical_content}


@dataclass(frozen=True, slots=True)
class AdmittedSemanticBundle:
    """Exact three-unit semantic view produced only after C03 verification."""

    contract_version: str
    conversation_id: str
    turn_id: str
    gate_receipt: str
    package_digest_manifest: Mapping[str, str]
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
            "package_digest_manifest",
            MappingProxyType(dict(self.package_digest_manifest)),
        )
        if tuple(self.package_digest_manifest) != ADMITTED_FRAME_ORDER:
            raise _rejection(
                "inexact_semantic_manifest",
                "semantic bundle manifest is partial, ambiguous, or out of order",
            )
        if (
            type(self.units) is not tuple
            or len(self.units) != len(ADMITTED_FRAME_ORDER)
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
            if unit.semantic_digest != self.package_digest_manifest[unit.frame_name]:
                raise _rejection(
                    "mismatched_semantic_unit",
                    "semantic unit does not match its sealed package digest",
                )
        if len({unit.semantic_digest for unit in self.units}) != len(self.units):
            raise _rejection(
                "ambiguous_semantic_unit",
                "semantic unit digests are ambiguous",
            )

    def verify(self) -> AdmittedSemanticBundle:
        self.__post_init__()
        return self

    def semantic_fingerprint(self) -> str:
        payload = [unit.to_message() for unit in self.units]
        return sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.context_admission.admitted_semantic_bundle.v1",
            "contract_version": self.contract_version,
            "conversation_id": self.conversation_id,
            "turn_id": self.turn_id,
            "gate_receipt": self.gate_receipt,
            "package_digest_manifest": dict(self.package_digest_manifest),
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
            request.identity_frame,
            request.experience_frame,
            request.current_task_context,
        )
        units: list[AdmittedSemanticUnit] = []
        for frame_name, source in zip(ADMITTED_FRAME_ORDER, sources, strict=True):
            try:
                payload = source.to_dict()
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
            if type(payload) is not dict or type(source_digest) is not str:
                raise _rejection(
                    "inexact_admitted_source_serialization",
                    "semantic binding source serialization is inexact",
                )
            canonical_content = canonical_json(payload)
            actual_digest = _semantic_digest(payload)
            if source_digest != actual_digest:
                raise _rejection(
                    "inexact_admitted_source_digest",
                    "semantic source digest is not its canonical digest",
                )
            if actual_digest != package.admitted_frames[frame_name]:
                raise _rejection(
                    "mismatched_admitted_frame",
                    "semantic source digest does not match the sealed package",
                )
            units.append(
                AdmittedSemanticUnit(
                    frame_name=frame_name,
                    role=ADMITTED_FRAME_ROLES[frame_name],
                    semantic_digest=actual_digest,
                    canonical_content=canonical_content,
                    issued_by=_BINDER_ISSUER,
                )
            )

        return AdmittedSemanticBundle(
            contract_version=package.contract_version,
            conversation_id=package.conversation_id,
            turn_id=package.turn_id,
            gate_receipt=package.gate_receipt,
            package_digest_manifest=dict(package.admitted_frames),
            units=tuple(units),
            issued_by=_BINDER_ISSUER,
        )


__all__ = [
    "ADMITTED_FRAME_ORDER",
    "ADMITTED_FRAME_ROLES",
    "AdmittedSemanticBundle",
    "AdmittedSemanticUnit",
    "ExactAdmittedSemanticBinder",
    "SemanticBindingRequest",
]

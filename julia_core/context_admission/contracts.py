"""Exact contracts for the bounded C03 admission boundary."""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any
from collections.abc import Mapping

from julia_core.identity import IdentityStatus
from julia_core.memory_experience import MemoryExperienceStatus
from julia_core.projection.contracts import ExperienceFrame, IdentityFrame


ADMISSION_CURRENT_TASK_SCHEMA_VERSION = "1.0.0"
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
CURRENT_TASK_MAX_ENCODED_BYTES = 2048
CURRENT_TASK_MAX_DEPTH = 3
RUNTIME_SOURCE_REF_PATTERN = re.compile(
    r"conversation_runtime://[^/?#@:\s]+/[^?#@\s]+"
)


@dataclass(frozen=True, slots=True)
class AdmissionRejection:
    """Machine-readable fail-closed admission result."""

    code: str
    message: str

    def __post_init__(self) -> None:
        if type(self.code) is not str or not self.code:
            raise TypeError("admission rejection code must be an exact string")
        if type(self.message) is not str or not self.message:
            raise TypeError("admission rejection message must be an exact string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.context_admission.rejection.v1",
            "code": self.code,
            "message": self.message,
            "partial_admission": False,
        }


class C03AdmissionRejected(RuntimeError):
    """Fail-closed C03 admission result; no partial package is returned."""

    def __init__(self, rejection: AdmissionRejection) -> None:
        if type(rejection) is not AdmissionRejection:
            raise TypeError("C03AdmissionRejected requires an exact AdmissionRejection")
        super().__init__(rejection.message)
        self.rejection = rejection


class CanonicalConversationSource(str, Enum):
    CONVERSATION_RUNTIME = "conversation_runtime"


@dataclass(frozen=True, slots=True)
class CanonicalConversationProvenance:
    source_type: CanonicalConversationSource
    source_ref: str
    source_digest: str
    observed_at: str

    def __post_init__(self) -> None:
        if type(self.source_type) is not CanonicalConversationSource:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_provenance_source",
                    message="current task provenance source type is inexact",
                )
            )
        _require_runtime_source_ref(self.source_ref)
        _require_digest(self.source_digest, "current task provenance digest")
        _require_string(self.observed_at, "current task provenance observed_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type.value,
            "source_ref": self.source_ref,
            "source_digest": self.source_digest,
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True, slots=True)
class CurrentConversationalTaskContext:
    schema_version: str
    conversation_id: str
    turn_id: str
    task_intent: str
    task_domain: str
    current_modality: str
    bounded_state: Mapping[str, Any]
    provenance: CanonicalConversationProvenance

    def __post_init__(self) -> None:
        if self.schema_version != ADMISSION_CURRENT_TASK_SCHEMA_VERSION:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="unsupported_current_task_schema",
                    message="current task context schema is unsupported",
                )
            )
        for field_name in (
            "conversation_id",
            "turn_id",
            "task_intent",
            "task_domain",
            "current_modality",
        ):
            _require_string(getattr(self, field_name), f"current task {field_name}")
        if type(self.provenance) is not CanonicalConversationProvenance:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_current_task_provenance",
                    message="current task context provenance is inexact",
                )
            )
        _require_bounded_state(self.bounded_state)
        object.__setattr__(self, "bounded_state", _deep_freeze(self.bounded_state))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.context_admission.current_task_context.v1",
            "schema_version": self.schema_version,
            "conversation_id": self.conversation_id,
            "turn_id": self.turn_id,
            "task_intent": self.task_intent,
            "task_domain": self.task_domain,
            "current_modality": self.current_modality,
            "bounded_state": _deep_copy(self.bounded_state),
            "provenance": self.provenance.to_dict(),
            "canonical_authority": "ConversationRuntime",
            "runtime_authority": False,
        }

    def digest(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ExclusiveAdmissionRequest:
    identity_frame: IdentityFrame | None = None
    experience_frame: ExperienceFrame | None = None
    current_task_context: CurrentConversationalTaskContext | None = None

    def __post_init__(self) -> None:
        if type(self.identity_frame) is not IdentityFrame:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_identity_frame",
                    message="C03 admits an exact canonical IdentityFrame only",
                )
            )
        if type(self.experience_frame) is not ExperienceFrame:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_experience_frame",
                    message="C03 admits an exact canonical ExperienceFrame only",
                )
            )
        if type(self.current_task_context) is not CurrentConversationalTaskContext:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_current_task_context",
                    message="C03 admits exact canonical current task context only",
                )
            )


@dataclass(frozen=True, slots=True)
class SealedCognitiveContextPackage:
    contract_version: str
    conversation_id: str
    turn_id: str
    identity_digest: str
    experience_digest: str
    current_task_digest: str
    gate_receipt: str
    admitted_frames: Mapping[str, str]
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        _validate_package(self)
        object.__setattr__(
            self, "admitted_frames", _deep_freeze(self.admitted_frames)
        )

    def verify(self) -> "SealedCognitiveContextPackage":
        self.__post_init__()
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.context_admission.sealed_package.v1",
            "contract_version": self.contract_version,
            "conversation_id": self.conversation_id,
            "turn_id": self.turn_id,
            "source_digests": {
                "identity_frame": self.identity_digest,
                "experience_frame": self.experience_digest,
                "current_task_context": self.current_task_digest,
            },
            "gate_receipt": self.gate_receipt,
            "admitted_frames": _deep_copy(self.admitted_frames),
            "authority": {
                "canonical": False,
                "runtime": False,
                "provider": False,
                "assistant_self": False,
            },
        }


def canonical_json(value: Any) -> str:
    return _canonical_json(value)


def package_digest(
    contract_version: str,
    conversation_id: str,
    turn_id: str,
    identity_digest: str,
    experience_digest: str,
    current_task_digest: str,
) -> str:
    payload = {
        "contract_version": contract_version,
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "identity_digest": identity_digest,
        "experience_digest": experience_digest,
        "current_task_digest": current_task_digest,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _validate_package(package: SealedCognitiveContextPackage) -> None:
    from .gate import C03_PRODUCTION_CONTRACT_VERSION, C03_ADMISSION_ISSUER

    if package.issued_by is not C03_ADMISSION_ISSUER:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="unauthorized_package_issuer",
                message="package was not issued by the exclusive C03 gate",
            )
        )
    if package.contract_version != C03_PRODUCTION_CONTRACT_VERSION:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="inexact_package_contract",
                message="package contract version is inexact",
                )
            )
    if type(package.admitted_frames) not in (dict, MappingProxyType):
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="inexact_admitted_frames",
                message="package admitted-frame manifest is inexact",
            )
        )
    for field_name in ("conversation_id", "turn_id"):
        _require_string(getattr(package, field_name), f"package {field_name}")
    for field_name in (
        "identity_digest",
        "experience_digest",
        "current_task_digest",
        "gate_receipt",
    ):
        _require_digest(getattr(package, field_name), f"package {field_name}")
    expected_frames = {
        "identity_frame": package.identity_digest,
        "experience_frame": package.experience_digest,
        "current_task_context": package.current_task_digest,
    }
    if dict(package.admitted_frames) != expected_frames:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="inexact_admitted_frames",
                message="package admitted-frame manifest is inexact",
            )
        )
    expected_receipt = package_digest(
        package.contract_version,
        package.conversation_id,
        package.turn_id,
        package.identity_digest,
        package.experience_digest,
        package.current_task_digest,
    )
    if package.gate_receipt != expected_receipt:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="forged_package_receipt",
                message="package gate receipt does not match its inputs",
            )
        )


def _require_runtime_source_ref(value: str) -> None:
    _require_string(value, "current task provenance source ref")
    if RUNTIME_SOURCE_REF_PATTERN.fullmatch(value) is None:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="inexact_provenance_source_ref",
                message="current task provenance source ref is inexact",
            )
        )


def _require_bounded_state(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="inexact_bounded_state",
                message="current task bounded state must be a Mapping",
            )
        )
    _require_json_tree(value)
    try:
        encoded = _canonical_json(_deep_copy(value)).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as error:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="non_serializable_bounded_state",
                message="current task bounded state is not deterministically serializable",
            )
        ) from error
    if len(encoded) > CURRENT_TASK_MAX_ENCODED_BYTES:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="bounded_state_budget_exceeded",
                message="current task context exceeds its bounded-state budget",
            )
        )
    if _depth(value) > CURRENT_TASK_MAX_DEPTH:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="bounded_state_depth_exceeded",
                message="current task context exceeds its bounded-state depth",
            )
        )


def _require_json_tree(value: Any) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="non_serializable_bounded_state",
                    message="current task bounded state is not deterministically serializable",
                )
            )
        return
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_bounded_state",
                    message="current task bounded state keys must be exact strings",
                )
            )
        for item in value.values():
            _require_json_tree(item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _require_json_tree(item)
        return
    raise C03AdmissionRejected(
        AdmissionRejection(
            code="inexact_bounded_state",
            message="current task bounded state contains an unsupported value",
        )
    )


def _require_string(value: str, field_name: str) -> None:
    if type(value) is not str or not value:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="inexact_string_field",
                message=f"{field_name} must be a non-empty exact built-in string",
            )
        )


def _require_digest(value: str, field_name: str) -> None:
    if type(value) is not str or DIGEST_PATTERN.fullmatch(value) is None:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="inexact_digest",
                message=f"{field_name} is absent or inexact",
            )
        )


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _deep_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _deep_copy(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_deep_copy(item) for item in value]
    return value


def _depth(value: Any) -> int:
    if isinstance(value, Mapping):
        return 1 + max((_depth(item) for item in value.values()), default=0)
    if isinstance(value, (tuple, list)):
        return 1 + max((_depth(item) for item in value), default=0)
    return 0


__all__ = [
    "ADMISSION_CURRENT_TASK_SCHEMA_VERSION",
    "AdmissionRejection",
    "C03AdmissionRejected",
    "CanonicalConversationProvenance",
    "CanonicalConversationSource",
    "CurrentConversationalTaskContext",
    "ExclusiveAdmissionRequest",
    "SealedCognitiveContextPackage",
]

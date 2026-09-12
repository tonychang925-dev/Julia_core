"""Test-only executable contract for C03 exclusive model-visible admission.

This module is deliberately isolated under the test tree.  It is a conformance
probe, not a production authority and not a replacement for a P2 C03
implementation.  Its purpose is to make the frozen boundary executable before
production integration exists.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any
from collections.abc import Mapping

from julia_core.identity import IdentityRef, IdentityStatus
from julia_core.memory_experience import (
    MemoryExperienceRef,
    MemoryExperienceStatus,
    MemoryExperienceType,
)
from julia_core.projection.contracts import (
    ExperienceFrame,
    ExperienceFrameSet,
    IdentityFrame,
)


C03_CONTRACT_VERSION = "ENG-12A-C03-EXECUTABLE-CONFORMANCE/0.2"
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
CURRENT_TASK_MAX_ENCODED_BYTES = 2048
CURRENT_TASK_MAX_DEPTH = 3
_C03_ADMISSION_MARKER = object()


class C03AdmissionRejected(RuntimeError):
    """Raised when the exclusive admission contract is not exactly satisfied."""


class CanonicalConversationSource(str, Enum):
    CONVERSATION_RUNTIME = "conversation_runtime"


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


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class CanonicalConversationProvenance:
    source_type: CanonicalConversationSource
    source_ref: str
    source_digest: str
    observed_at: str

    def __post_init__(self) -> None:
        if type(self.source_type) is not CanonicalConversationSource:
            raise C03AdmissionRejected("current task provenance source type is inexact")
        if not self.source_ref.startswith("conversation_runtime://"):
            raise C03AdmissionRejected("current task provenance source ref is inexact")
        if DIGEST_PATTERN.fullmatch(self.source_digest) is None:
            raise C03AdmissionRejected("current task provenance digest is absent or inexact")

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
        if self.schema_version != "1.0.0":
            raise C03AdmissionRejected("current task context schema is unsupported")
        if not all(isinstance(value, str) and value for value in (
            self.conversation_id,
            self.turn_id,
            self.task_intent,
            self.task_domain,
            self.current_modality,
        )):
            raise C03AdmissionRejected("current task context has an incomplete identity")
        if type(self.provenance) is not CanonicalConversationProvenance:
            raise C03AdmissionRejected("current task context provenance is inexact")
        encoded_state = _canonical_json(_deep_copy(self.bounded_state)).encode("utf-8")
        if len(encoded_state) > CURRENT_TASK_MAX_ENCODED_BYTES:
            raise C03AdmissionRejected("current task context exceeds its bounded-state budget")
        if _depth(self.bounded_state) > CURRENT_TASK_MAX_DEPTH:
            raise C03AdmissionRejected("current task context exceeds its bounded-state depth")
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
    experience_frames: ExperienceFrameSet | None = None
    current_task_context: CurrentConversationalTaskContext | None = None

    def __post_init__(self) -> None:
        if type(self.identity_frame) is not IdentityFrame:
            raise C03AdmissionRejected("C03 admits an exact canonical IdentityFrame only")
        if type(self.experience_frames) is not ExperienceFrameSet:
            raise C03AdmissionRejected("C03 admits an exact canonical ExperienceFrameSet only")
        if type(self.current_task_context) is not CurrentConversationalTaskContext:
            raise C03AdmissionRejected("C03 admits exact canonical current task context only")


@dataclass(frozen=True, slots=True)
class SealedCognitiveContextPackage:
    contract_version: str
    conversation_id: str
    turn_id: str
    identity_digest: str
    experience_digest: str
    experience_frame_digests: tuple[str, ...]
    experience_frame_count: int
    current_task_digest: str
    gate_receipt: str
    admitted_frames: Mapping[str, str]
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _C03_ADMISSION_MARKER:
            raise C03AdmissionRejected("package was not issued by the exclusive C03 gate")
        if self.contract_version != C03_CONTRACT_VERSION:
            raise C03AdmissionRejected("package contract version is inexact")
        expected = _package_digest(
            self.contract_version,
            self.conversation_id,
            self.turn_id,
            self.identity_digest,
            self.experience_digest,
            self.experience_frame_digests,
            self.experience_frame_count,
            self.current_task_digest,
        )
        if self.gate_receipt != expected:
            raise C03AdmissionRejected("package gate receipt does not match its inputs")
        object.__setattr__(self, "admitted_frames", _deep_freeze(self.admitted_frames))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.context_admission.sealed_package.v2",
            "contract_version": self.contract_version,
            "conversation_id": self.conversation_id,
            "turn_id": self.turn_id,
            "source_digests": {
                "identity_frame": self.identity_digest,
                "experience_frame_set": self.experience_digest,
                "current_task_context": self.current_task_digest,
            },
            "experience_frame_digests": list(self.experience_frame_digests),
            "experience_frame_count": self.experience_frame_count,
            "gate_receipt": self.gate_receipt,
            "admitted_frames": _deep_copy(self.admitted_frames),
            "authority": {
                "canonical": False,
                "runtime": False,
                "provider": False,
                "assistant_self": False,
            },
        }


def _package_digest(
    contract_version: str,
    conversation_id: str,
    turn_id: str,
    identity_digest: str,
    experience_digest: str,
    experience_frame_digests: tuple[str, ...],
    experience_frame_count: int,
    current_task_digest: str,
) -> str:
    payload = {
        "contract_version": contract_version,
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "identity_digest": identity_digest,
        "experience_digest": experience_digest,
        "experience_frame_digests": list(experience_frame_digests),
        "experience_frame_count": experience_frame_count,
        "current_task_digest": current_task_digest,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _require_frame_provenance(frame: IdentityFrame | ExperienceFrame, frame_name: str) -> None:
    if not frame.provenance_refs:
        raise C03AdmissionRejected(f"{frame_name} provenance is absent")
    if any(type(ref) not in (dict, MappingProxyType) for ref in frame.provenance_refs):
        raise C03AdmissionRejected(f"{frame_name} provenance is inexact")
    required_source_digest = frame.source_digest
    if not any(ref.get("source_digest") == required_source_digest for ref in frame.provenance_refs):
        raise C03AdmissionRejected(f"{frame_name} provenance digest is inexact")


class ExclusiveAdmissionProbe:
    """Exclusive test adapter for the frozen C03 direction and STOP boundary."""

    def seal(self, request: ExclusiveAdmissionRequest) -> SealedCognitiveContextPackage:
        if type(request) is not ExclusiveAdmissionRequest:
            raise C03AdmissionRejected("C03 admission request type is inexact")

        identity = request.identity_frame
        experiences = request.experience_frames
        current_task = request.current_task_context
        assert identity is not None and experiences is not None and current_task is not None

        if identity.source_status is not IdentityStatus.ADMITTED:
            raise C03AdmissionRejected("identity source is not admitted")
        if DIGEST_PATTERN.fullmatch(identity.source_digest) is None:
            raise C03AdmissionRejected("identity source digest is absent or inexact")
        _require_frame_provenance(identity, "identity frame")
        for experience in experiences.frames:
            if experience.source_status is not MemoryExperienceStatus.ADMITTED:
                raise C03AdmissionRejected("experience source is not admitted")
            if DIGEST_PATTERN.fullmatch(experience.source_digest) is None:
                raise C03AdmissionRejected("experience source digest is absent or inexact")
            _require_frame_provenance(experience, "experience frame")

        identity_digest = identity.digest()
        experience_digest = experiences.digest()
        experience_frame_digests = tuple(frame.digest() for frame in experiences.frames)
        current_task_digest = current_task.digest()
        receipt = _package_digest(
            C03_CONTRACT_VERSION,
            current_task.conversation_id,
            current_task.turn_id,
            identity_digest,
            experience_digest,
            experience_frame_digests,
            len(experiences.frames),
            current_task_digest,
        )
        return SealedCognitiveContextPackage(
            contract_version=C03_CONTRACT_VERSION,
            conversation_id=current_task.conversation_id,
            turn_id=current_task.turn_id,
            identity_digest=identity_digest,
            experience_digest=experience_digest,
            experience_frame_digests=experience_frame_digests,
            experience_frame_count=len(experiences.frames),
            current_task_digest=current_task_digest,
            gate_receipt=receipt,
            admitted_frames={
                "identity_frame": identity_digest,
                "experience_frame_set": experience_digest,
                "current_task_context": current_task_digest,
            },
            issued_by=_C03_ADMISSION_MARKER,
        )


class ModelVisibilityTransport:
    """Minimal transport proving visibility starts only at a sealed package."""

    def render(self, candidate: Any) -> dict[str, Any]:
        if type(candidate) is not SealedCognitiveContextPackage:
            raise C03AdmissionRejected("model visibility requires a sealed C03 package")
        expected_receipt = _package_digest(
            candidate.contract_version,
            candidate.conversation_id,
            candidate.turn_id,
            candidate.identity_digest,
            candidate.experience_digest,
            candidate.experience_frame_digests,
            candidate.experience_frame_count,
            candidate.current_task_digest,
        )
        if candidate.gate_receipt != expected_receipt:
            raise C03AdmissionRejected("model visibility package receipt is forged")
        return candidate.to_dict()


def canonical_identity_frame(*, provenance_refs=None) -> IdentityFrame:
    digest = "a" * 64
    return IdentityFrame(
        schema_version="1.0.0",
        policy_id="persona_projection.identity_only",
        policy_version="1.0.0",
        source_ref=IdentityRef("identity-lineage-eng12a", "v1"),
        source_digest=digest,
        source_status=IdentityStatus.ADMITTED,
        identity_id="identity-eng12a",
        predecessor_version_id=None,
        anchors=({"anchor_id": "boundary", "statement": "Use governed context only"},),
        values=(),
        boundaries=({"boundary_id": "exclusive-gateway", "rule": "C03 only"},),
        relationship_role_anchors=(),
        provenance_refs=provenance_refs
        if provenance_refs is not None
        else ({"source_ref": "identity://eng12a/v1", "source_digest": digest},),
    )


def canonical_experience_frame(*, provenance_refs=None) -> ExperienceFrame:
    digest = "b" * 64
    return ExperienceFrame(
        schema_version="1.0.0",
        policy_id="experience_projection.memory_experience_only",
        policy_version="1.0.0",
        source_ref=MemoryExperienceRef("experience-eng12a", "v1"),
        source_digest=digest,
        source_status=MemoryExperienceStatus.ADMITTED,
        experience_id="experience-eng12a",
        version_id="v1",
        predecessor_version_id=None,
        experience_type=MemoryExperienceType.PROJECT_COMMITMENT,
        content={"commitment": "Do not bypass governed context admission"},
        provenance_refs=provenance_refs
        if provenance_refs is not None
        else ({"source_ref": "memory_experience://eng12a/v1", "source_digest": digest},),
        created_at="2026-09-12T00:00:00Z",
    )


def canonical_experience_frame_set() -> ExperienceFrameSet:
    return ExperienceFrameSet(
        schema_version="1.0.0",
        frames=(canonical_experience_frame(),),
    )


def canonical_current_task_context(
    *, bounded_state=None, provenance=None, turn_id="turn-eng12a-1"
) -> CurrentConversationalTaskContext:
    return CurrentConversationalTaskContext(
        schema_version="1.0.0",
        conversation_id="conversation-eng12a",
        turn_id=turn_id,
        task_intent="Implement C03 conformance",
        task_domain="software_engineering",
        current_modality="text",
        bounded_state={"surface": "terminal", "open_loop_count": 1}
        if bounded_state is None
        else bounded_state,
        provenance=provenance
        or CanonicalConversationProvenance(
            source_type=CanonicalConversationSource.CONVERSATION_RUNTIME,
            source_ref="conversation_runtime://eng12a/current-task",
            source_digest="c" * 64,
            observed_at="2026-09-12T00:00:00Z",
        ),
    )


def canonical_request(
    *, identity=None, experiences=None, current_task=None
) -> ExclusiveAdmissionRequest:
    return ExclusiveAdmissionRequest(
        identity_frame=identity or canonical_identity_frame(),
        experience_frames=experiences
        if experiences is not None
        else canonical_experience_frame_set(),
        current_task_context=current_task or canonical_current_task_context(),
    )

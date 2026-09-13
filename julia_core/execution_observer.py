"""Evidence-only observation of one exact canonical provider execution.

The observer records provenance and execution disposition. It never constructs
canonical semantics, mutates authority, invokes a default provider, or chooses
a production response.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Any

from julia_core.alignment_os import ProviderExecutionEnvelope
from julia_core.context_admission import (
    AdmittedSemanticBundle,
    CurrentConversationalTaskContext,
    SealedCognitiveContextPackage,
)
from julia_core.context_admission.contracts import canonical_json
from julia_core.projection.contracts import (
    ExperienceFrameSet,
    IdentityFrame,
)


CANONICAL_EXECUTION_OBSERVER_SCHEMA_VERSION = "1.0.0"
CANONICAL_EXECUTION_OBSERVER_SCHEMA = (
    "julia_core.evidence.canonical_execution_observer.v1"
)
_ALLOWED_DISPOSITIONS = frozenset({"SUCCEEDED", "FAILED", "ERROR", "NOT_RUN"})
_OBSERVER_ISSUER = object()


class CanonicalExecutionObservationRejected(ValueError):
    """Raised when exact canonical execution evidence cannot be observed."""


class ProviderExecutionRejected(RuntimeError):
    """Non-semantic provider-domain failure supplied by an injected callable."""

    def __init__(self, failure_class: str) -> None:
        _require_failure_class(failure_class)
        super().__init__(f"provider execution failed: {failure_class}")
        self.failure_class = failure_class


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, list):
        raise TypeError("mutable observer evidence is forbidden")
    return value


def _unfreeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _unfreeze(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_unfreeze(item) for item in value]
    return value


def _require_failure_class(value: str) -> None:
    if (
        type(value) is not str
        or not value
        or len(value) > 128
        or any(not character.isascii() for character in value)
        or not value.replace("_", "A").isalnum()
        or not value[0].isalpha()
        or not value.isupper()
    ):
        raise TypeError("failure classification is inexact")


def _require_digest(value: str, name: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise TypeError(f"{name} is inexact")
    try:
        int(value, 16)
    except ValueError as error:
        raise TypeError(f"{name} is inexact") from error


def _digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CanonicalSourceObservation:
    source_ref: Mapping[str, Any]
    source_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, Mapping):
            raise TypeError("canonical source_ref is inexact")
        object.__setattr__(self, "source_ref", _freeze(self.source_ref))
        _require_digest(self.source_digest, "canonical source_digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_ref": _unfreeze(self.source_ref),
            "source_digest": self.source_digest,
        }


@dataclass(frozen=True, slots=True)
class CanonicalExecutionProvenance:
    schema_version: str
    conversation_id: str
    turn_id: str
    identity_frame: CanonicalSourceObservation
    experience_frames: tuple[CanonicalSourceObservation, ...]
    experience_frame_set_digest: str
    ordered_frame_digest_manifest: tuple[str, ...]
    current_task_context: CanonicalSourceObservation
    gate_receipt: str
    semantic_fingerprint: str
    ordered_unit_digests: tuple[str, ...]
    provider_id: str
    alignment_identity: str
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _OBSERVER_ISSUER:
            raise TypeError("only the evidence observer constructs provenance")
        if self.schema_version != CANONICAL_EXECUTION_OBSERVER_SCHEMA_VERSION:
            raise TypeError("observer provenance schema is unsupported")
        for name in ("conversation_id", "turn_id", "provider_id"):
            if type(getattr(self, name)) is not str or not getattr(self, name):
                raise TypeError(f"observer {name} is inexact")
        if type(self.identity_frame) is not CanonicalSourceObservation:
            raise TypeError("identity provenance is inexact")
        if (
            type(self.experience_frames) is not tuple
            or not self.experience_frames
            or any(
                type(item) is not CanonicalSourceObservation
                for item in self.experience_frames
            )
        ):
            raise TypeError("experience provenance is partial or inexact")
        if type(self.current_task_context) is not CanonicalSourceObservation:
            raise TypeError("current task provenance is inexact")
        _require_digest(self.experience_frame_set_digest, "ExperienceFrameSet digest")
        if type(self.ordered_frame_digest_manifest) is not tuple or not (
            self.ordered_frame_digest_manifest
        ):
            raise TypeError("ordered frame digest manifest is partial")
        for digest in self.ordered_frame_digest_manifest:
            _require_digest(digest, "ordered frame digest")
        _require_digest(self.gate_receipt, "gate receipt")
        _require_digest(self.semantic_fingerprint, "semantic fingerprint")
        if type(self.ordered_unit_digests) is not tuple or not (
            self.ordered_unit_digests
        ):
            raise TypeError("ordered unit digests are partial")
        for digest in self.ordered_unit_digests:
            _require_digest(digest, "ordered unit digest")
        _require_digest(self.alignment_identity, "alignment identity")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.evidence.canonical_execution_provenance.v1",
            "schema_version": self.schema_version,
            "correlation": {
                "conversation_id": self.conversation_id,
                "turn_id": self.turn_id,
            },
            "identity_frame": self.identity_frame.to_dict(),
            "experience_frames": [
                item.to_dict() for item in self.experience_frames
            ],
            "experience_frame_set": {
                "digest": self.experience_frame_set_digest,
                "ordered_frame_digest_manifest": list(
                    self.ordered_frame_digest_manifest
                ),
            },
            "current_task_context": self.current_task_context.to_dict(),
            "semantic": {
                "gate_receipt": self.gate_receipt,
                "fingerprint": self.semantic_fingerprint,
                "ordered_unit_digests": list(self.ordered_unit_digests),
            },
            "provider": {
                "id": self.provider_id,
                "alignment_identity": self.alignment_identity,
            },
        }


@dataclass(frozen=True, slots=True)
class ProviderExecutionOutcome:
    disposition: str
    output_present: bool
    issued_by: object = field(repr=False, compare=False)
    failure_class: str | None = None

    def __post_init__(self) -> None:
        if self.issued_by is not _OBSERVER_ISSUER:
            raise TypeError("only the evidence observer constructs outcomes")
        if type(self.disposition) is not str or (
            self.disposition not in _ALLOWED_DISPOSITIONS
        ):
            raise TypeError("provider execution disposition is inexact")
        if type(self.output_present) is not bool:
            raise TypeError("provider output presence is inexact")
        if self.failure_class is not None:
            _require_failure_class(self.failure_class)
        if self.disposition == "SUCCEEDED" and not self.output_present:
            raise TypeError("successful provider outcome requires output")
        if self.disposition == "NOT_RUN" and self.output_present:
            raise TypeError("not-run provider outcome cannot have output")

    @classmethod
    def from_provider_result(cls, value: object) -> "ProviderExecutionOutcome":
        if type(value) is not str:
            raise TypeError("provider result evidence is inexact")
        output_present = bool(value.strip())
        return cls(
            disposition="SUCCEEDED" if output_present else "FAILED",
            output_present=output_present,
            failure_class=None if output_present else "EMPTY_OUTPUT",
            issued_by=_OBSERVER_ISSUER,
        )

    @classmethod
    def from_provider_failure(cls, error: BaseException) -> "ProviderExecutionOutcome":
        if isinstance(error, ProviderExecutionRejected):
            return cls(
                disposition="FAILED",
                output_present=False,
                failure_class=error.failure_class,
                issued_by=_OBSERVER_ISSUER,
            )
        if not isinstance(error, Exception):
            raise TypeError("provider failure evidence is inexact")
        return cls(
            disposition="ERROR",
            output_present=False,
            failure_class=type(error).__name__.upper(),
            issued_by=_OBSERVER_ISSUER,
        )

    @classmethod
    def not_run(cls, failure_class: str) -> "ProviderExecutionOutcome":
        _require_failure_class(failure_class)
        return cls(
            disposition="NOT_RUN",
            output_present=False,
            failure_class=failure_class,
            issued_by=_OBSERVER_ISSUER,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition,
            "output_present": self.output_present,
            "failure_class": self.failure_class,
        }


@dataclass(frozen=True, slots=True)
class ExecutionAuthorityAttestation:
    observer_output_authority: int
    semantic_authority: int
    production_response_selection_authority: int
    canonical_writes: int
    identity_authority_mutations: int
    memory_experience_authority_mutations: int
    post_c03_semantic_reconstruction: int
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _OBSERVER_ISSUER:
            raise TypeError("only the evidence observer constructs authority evidence")
        for name in (
            "observer_output_authority",
            "semantic_authority",
            "production_response_selection_authority",
            "canonical_writes",
            "identity_authority_mutations",
            "memory_experience_authority_mutations",
            "post_c03_semantic_reconstruction",
        ):
            if type(getattr(self, name)) is not int or getattr(self, name) != 0:
                raise TypeError("execution authority attestation is inexact")

    def to_dict(self) -> dict[str, Any]:
        return {
            "OBSERVABILITY_OUTPUT_AUTHORITY": self.observer_output_authority,
            "SEMANTIC_AUTHORITY": self.semantic_authority,
            "PRODUCTION_RESPONSE_SELECTION_AUTHORITY": (
                self.production_response_selection_authority
            ),
            "CANONICAL_WRITES": self.canonical_writes,
            "IDENTITY_AUTHORITY_MUTATION": self.identity_authority_mutations,
            "MEMORY_EXPERIENCE_AUTHORITY_MUTATION": (
                self.memory_experience_authority_mutations
            ),
            "POST_C03_SEMANTIC_RECONSTRUCTION": (
                self.post_c03_semantic_reconstruction
            ),
        }


@dataclass(frozen=True, slots=True)
class CanonicalExecutionObservation:
    schema_version: str
    provenance: CanonicalExecutionProvenance
    execution: ProviderExecutionOutcome
    authority: ExecutionAuthorityAttestation
    replay_digest: str
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _OBSERVER_ISSUER:
            raise TypeError("only the evidence observer constructs observations")
        if self.schema_version != CANONICAL_EXECUTION_OBSERVER_SCHEMA_VERSION:
            raise TypeError("canonical execution observation schema is unsupported")
        if type(self.provenance) is not CanonicalExecutionProvenance:
            raise TypeError("canonical provenance is inexact")
        if type(self.execution) is not ProviderExecutionOutcome:
            raise TypeError("provider execution outcome is inexact")
        if type(self.authority) is not ExecutionAuthorityAttestation:
            raise TypeError("execution authority attestation is inexact")
        _require_digest(self.replay_digest, "replay digest")
        expected = _digest(self._body())
        if self.replay_digest != expected:
            raise TypeError("canonical execution replay digest is forged")

    def _body(self) -> dict[str, Any]:
        return {
            "schema": CANONICAL_EXECUTION_OBSERVER_SCHEMA,
            "schema_version": self.schema_version,
            "provenance": self.provenance.to_dict(),
            "execution": self.execution.to_dict(),
            "authority": self.authority.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        body = self._body()
        body["replay_digest"] = self.replay_digest
        return body

    def digest(self) -> str:
        return self.replay_digest


class EvidenceOnlyCanonicalExecutionObserver:
    """Observe injected execution without becoming a semantic authority."""

    def observe(
        self,
        *,
        identity_frame: IdentityFrame,
        experience_frames: ExperienceFrameSet,
        current_task_context: CurrentConversationalTaskContext,
        package: SealedCognitiveContextPackage,
        binding: AdmittedSemanticBundle,
        envelope: ProviderExecutionEnvelope,
        provider_execution: Callable[[ProviderExecutionEnvelope], object],
    ) -> CanonicalExecutionObservation:
        if not callable(provider_execution):
            raise TypeError("provider execution must be an injected exact callable")
        provenance = self._provenance(
            identity_frame=identity_frame,
            experience_frames=experience_frames,
            current_task_context=current_task_context,
            package=package,
            binding=binding,
            envelope=envelope,
        )
        messages_before = canonical_json([dict(item) for item in envelope.messages])
        try:
            result = provider_execution(envelope)
            outcome = ProviderExecutionOutcome.from_provider_result(result)
        except ProviderExecutionRejected as error:
            outcome = ProviderExecutionOutcome.from_provider_failure(error)
        except Exception as error:
            outcome = ProviderExecutionOutcome.from_provider_failure(error)
        envelope.verify()
        messages_after = canonical_json([dict(item) for item in envelope.messages])
        if messages_after != messages_before:
            outcome = ProviderExecutionOutcome(
                disposition="ERROR",
                output_present=False,
                failure_class="ENVELOPE_MUTATED",
                issued_by=_OBSERVER_ISSUER,
            )
        return self._record(provenance, outcome)

    def observe_outcome(
        self,
        *,
        identity_frame: IdentityFrame,
        experience_frames: ExperienceFrameSet,
        current_task_context: CurrentConversationalTaskContext,
        package: SealedCognitiveContextPackage,
        binding: AdmittedSemanticBundle,
        envelope: ProviderExecutionEnvelope,
        outcome: ProviderExecutionOutcome,
    ) -> CanonicalExecutionObservation:
        if type(outcome) is not ProviderExecutionOutcome:
            raise TypeError("provider execution outcome is inexact")
        provenance = self._provenance(
            identity_frame=identity_frame,
            experience_frames=experience_frames,
            current_task_context=current_task_context,
            package=package,
            binding=binding,
            envelope=envelope,
        )
        return self._record(provenance, outcome)

    def _provenance(
        self,
        *,
        identity_frame: IdentityFrame,
        experience_frames: ExperienceFrameSet,
        current_task_context: CurrentConversationalTaskContext,
        package: SealedCognitiveContextPackage,
        binding: AdmittedSemanticBundle,
        envelope: ProviderExecutionEnvelope,
    ) -> CanonicalExecutionProvenance:
        if type(self) is not EvidenceOnlyCanonicalExecutionObserver:
            raise TypeError("observation requires the exact evidence observer")
        exact_inputs = (
            identity_frame,
            experience_frames,
            current_task_context,
            package,
            binding,
            envelope,
        )
        expected_types = (
            IdentityFrame,
            ExperienceFrameSet,
            CurrentConversationalTaskContext,
            SealedCognitiveContextPackage,
            AdmittedSemanticBundle,
            ProviderExecutionEnvelope,
        )
        for value, expected in zip(exact_inputs, expected_types, strict=True):
            if type(value) is not expected:
                raise TypeError("canonical execution evidence is inexact")
        package.verify()
        binding.verify()
        envelope.verify()

        identities = (
            (package.conversation_id, package.turn_id, package.gate_receipt),
            (binding.conversation_id, binding.turn_id, binding.gate_receipt),
            (
                envelope.conversation_id,
                envelope.turn_id,
                envelope.gate_receipt,
            ),
            (
                current_task_context.conversation_id,
                current_task_context.turn_id,
                package.gate_receipt,
            ),
        )
        if any(item != identities[0] for item in identities[1:]):
            raise CanonicalExecutionObservationRejected(
                "canonical execution identities do not match"
            )
        frame_digests = tuple(frame.digest() for frame in experience_frames.frames)
        ordered_unit_digests = tuple(
            unit.semantic_digest for unit in binding.units
        )
        if (
            identity_frame.digest() != package.identity_digest
            or experience_frames.digest() != package.experience_digest
            or frame_digests != package.experience_frame_digests
            or len(frame_digests) != package.experience_frame_count
            or current_task_context.digest() != package.current_task_digest
        ):
            raise CanonicalExecutionObservationRejected(
                "canonical provenance does not match the sealed package"
            )
        if (
            dict(binding.package_digest_manifest) != dict(package.admitted_frames)
            or ordered_unit_digests != tuple(package.admitted_frames.values())
            or envelope.semantic_fingerprint != binding.semantic_fingerprint()
        ):
            raise CanonicalExecutionObservationRejected(
                "canonical semantic evidence does not match the sealed package"
            )
        if tuple(unit.frame_name for unit in binding.units) != (
            "identity_frame",
            "experience_frame_set",
            "current_task_context",
        ):
            raise CanonicalExecutionObservationRejected(
                "canonical semantic unit order is inexact"
            )
        return CanonicalExecutionProvenance(
            schema_version=CANONICAL_EXECUTION_OBSERVER_SCHEMA_VERSION,
            conversation_id=envelope.conversation_id,
            turn_id=envelope.turn_id,
            identity_frame=CanonicalSourceObservation(
                source_ref=identity_frame.source_ref.to_dict(),
                source_digest=identity_frame.source_digest,
            ),
            experience_frames=tuple(
                CanonicalSourceObservation(
                    source_ref=item.source_ref.to_dict(),
                    source_digest=item.source_digest,
                )
                for item in experience_frames.frames
            ),
            experience_frame_set_digest=experience_frames.digest(),
            ordered_frame_digest_manifest=frame_digests,
            current_task_context=CanonicalSourceObservation(
                source_ref={
                    "source_ref": current_task_context.provenance.source_ref
                },
                source_digest=current_task_context.provenance.source_digest,
            ),
            gate_receipt=envelope.gate_receipt,
            semantic_fingerprint=envelope.semantic_fingerprint,
            ordered_unit_digests=ordered_unit_digests,
            provider_id=envelope.alignment.provider_id,
            alignment_identity=_digest(envelope.alignment.to_dict()),
            issued_by=_OBSERVER_ISSUER,
        )

    @staticmethod
    def _record(
        provenance: CanonicalExecutionProvenance,
        outcome: ProviderExecutionOutcome,
    ) -> CanonicalExecutionObservation:
        authority = ExecutionAuthorityAttestation(
            observer_output_authority=0,
            semantic_authority=0,
            production_response_selection_authority=0,
            canonical_writes=0,
            identity_authority_mutations=0,
            memory_experience_authority_mutations=0,
            post_c03_semantic_reconstruction=0,
            issued_by=_OBSERVER_ISSUER,
        )
        body = {
            "schema": CANONICAL_EXECUTION_OBSERVER_SCHEMA,
            "schema_version": CANONICAL_EXECUTION_OBSERVER_SCHEMA_VERSION,
            "provenance": provenance.to_dict(),
            "execution": outcome.to_dict(),
            "authority": authority.to_dict(),
        }
        return CanonicalExecutionObservation(
            schema_version=CANONICAL_EXECUTION_OBSERVER_SCHEMA_VERSION,
            provenance=provenance,
            execution=outcome,
            authority=authority,
            replay_digest=_digest(body),
            issued_by=_OBSERVER_ISSUER,
        )


__all__ = [
    "CANONICAL_EXECUTION_OBSERVER_SCHEMA",
    "CANONICAL_EXECUTION_OBSERVER_SCHEMA_VERSION",
    "CanonicalExecutionObservation",
    "CanonicalExecutionObservationRejected",
    "CanonicalExecutionProvenance",
    "CanonicalSourceObservation",
    "EvidenceOnlyCanonicalExecutionObserver",
    "ExecutionAuthorityAttestation",
    "ProviderExecutionOutcome",
    "ProviderExecutionRejected",
]

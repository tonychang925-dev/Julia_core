"""Evidence-only pairing of reference and canonical execution records.

The objects in this module observe already-produced evidence. They never mint
canonical identity, reconstruct admitted semantics, invoke a provider, or choose
a production response.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
from typing import Any

from julia_core.alignment_os import ProviderExecutionEnvelope
from julia_core.context_admission import (
    AdmittedSemanticBundle,
    SealedCognitiveContextPackage,
)
from julia_core.context_admission.contracts import canonical_json


SIDE_BY_SIDE_COMPARISON_SCHEMA_VERSION = "1.0.0"
SIDE_BY_SIDE_COMPARISON_SCHEMA = "julia_core.evidence.side_by_side.v1"
_ALLOWED_EXECUTION_STATUSES = frozenset({"SUCCEEDED", "FAILED", "ERROR", "NOT_RUN"})
_SCALAR_TYPES = (str, int, float, bool, type(None))


class SideBySideComparisonRejected(ValueError):
    """Raised when reference and canonical evidence cannot be paired exactly."""


@dataclass(frozen=True, slots=True)
class ContinuityEvaluationEvidence:
    source_ref: str
    evaluation_fields: tuple[tuple[str, Any], ...]

    def __post_init__(self) -> None:
        if type(self.source_ref) is not str or not self.source_ref:
            raise TypeError("continuity evaluation source_ref is inexact")
        if type(self.evaluation_fields) is not tuple or not self.evaluation_fields:
            raise TypeError("continuity evaluation fields are inexact")
        names: set[str] = set()
        for item in self.evaluation_fields:
            if type(item) is not tuple or len(item) != 2:
                raise TypeError("continuity evaluation field is inexact")
            name, value = item
            if type(name) is not str or not name:
                raise TypeError("continuity evaluation field name is inexact")
            if name in names:
                raise ValueError("continuity evaluation field names are duplicated")
            if type(value) not in _SCALAR_TYPES:
                raise TypeError("continuity evaluation field value is inexact")
            names.add(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "fields": {name: value for name, value in self.evaluation_fields},
        }

    def digest(self) -> str:
        return _digest(
            {
                "source_ref": self.source_ref,
                "fields": self.to_dict()["fields"],
            }
        )


@dataclass(frozen=True, slots=True)
class ReferenceExecutionEvidence:
    schema_version: str
    source_ref: str
    conversation_id: str
    turn_id: str
    execution_status: str
    output_present: bool
    semantic_fingerprint: str | None = None
    ordered_unit_digests: tuple[str, ...] = ()
    provider_id: str | None = None
    alignment_identity: str | None = None
    gate_receipt: str | None = None
    continuity_evaluation: ContinuityEvaluationEvidence | None = None

    def __post_init__(self) -> None:
        _validate_common_evidence(
            schema_version=self.schema_version,
            source_ref=self.source_ref,
            conversation_id=self.conversation_id,
            turn_id=self.turn_id,
        )
        if (
            type(self.execution_status) is not str
            or self.execution_status not in _ALLOWED_EXECUTION_STATUSES
        ):
            raise TypeError("reference execution_status is inexact")
        if type(self.output_present) not in (bool, type(None)):
            raise TypeError("reference output_present is inexact")
        _validate_optional_evidence_fields(
            semantic_fingerprint=self.semantic_fingerprint,
            ordered_unit_digests=self.ordered_unit_digests,
            provider_id=self.provider_id,
            alignment_identity=self.alignment_identity,
            gate_receipt=self.gate_receipt,
            continuity_evaluation=self.continuity_evaluation,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.evidence.reference_execution.v1",
            "schema_version": self.schema_version,
            "source_ref": self.source_ref,
            "correlation": {
                "conversation_id": self.conversation_id,
                "turn_id": self.turn_id,
            },
            "execution": {
                "status": self.execution_status,
                "output_present": self.output_present,
            },
            "comparison_inputs": {
                "semantic_fingerprint": self.semantic_fingerprint,
                "ordered_unit_digests": list(self.ordered_unit_digests),
                "provider_id": self.provider_id,
                "alignment_identity": self.alignment_identity,
                "gate_receipt": self.gate_receipt,
            },
            "continuity_evaluation": _optional_to_dict(self.continuity_evaluation),
        }


@dataclass(frozen=True, slots=True)
class CanonicalExecutionEvidence:
    schema_version: str
    source_ref: str
    conversation_id: str
    turn_id: str
    semantic_fingerprint: str
    ordered_unit_digests: tuple[str, ...]
    gate_receipt: str
    provider_id: str
    alignment_identity: str
    execution_status: str | None = None
    output_present: bool | None = None
    continuity_evaluation: ContinuityEvaluationEvidence | None = None

    def __post_init__(self) -> None:
        _validate_common_evidence(
            schema_version=self.schema_version,
            source_ref=self.source_ref,
            conversation_id=self.conversation_id,
            turn_id=self.turn_id,
        )
        if self.execution_status is not None and (
            type(self.execution_status) is not str
            or self.execution_status not in _ALLOWED_EXECUTION_STATUSES
        ):
            raise TypeError("canonical execution_status is inexact")
        if type(self.output_present) not in (bool, type(None)):
            raise TypeError("canonical output_present is inexact")
        _validate_optional_evidence_fields(
            semantic_fingerprint=self.semantic_fingerprint,
            ordered_unit_digests=self.ordered_unit_digests,
            provider_id=self.provider_id,
            alignment_identity=self.alignment_identity,
            gate_receipt=self.gate_receipt,
            continuity_evaluation=self.continuity_evaluation,
            require_core_fields=True,
        )

    @classmethod
    def from_canonical_execution(
        cls,
        *,
        package: SealedCognitiveContextPackage,
        binding: AdmittedSemanticBundle,
        envelope: ProviderExecutionEnvelope,
        source_ref: str,
        execution_status: str | None = None,
        output_present: bool | None = None,
        continuity_evaluation: ContinuityEvaluationEvidence | None = None,
    ) -> CanonicalExecutionEvidence:
        if type(package) is not SealedCognitiveContextPackage:
            raise TypeError("canonical evidence requires an exact sealed package")
        if type(binding) is not AdmittedSemanticBundle:
            raise TypeError("canonical evidence requires an exact semantic bundle")
        if type(envelope) is not ProviderExecutionEnvelope:
            raise TypeError("canonical evidence requires an exact execution envelope")
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
        )
        if identities[0] != identities[1] or identities[0] != identities[2]:
            raise ValueError("canonical evidence identities do not match")
        if envelope.semantic_fingerprint != binding.semantic_fingerprint():
            raise ValueError("canonical evidence fingerprints do not match")
        return cls(
            schema_version=SIDE_BY_SIDE_COMPARISON_SCHEMA_VERSION,
            source_ref=source_ref,
            conversation_id=envelope.conversation_id,
            turn_id=envelope.turn_id,
            semantic_fingerprint=envelope.semantic_fingerprint,
            ordered_unit_digests=tuple(unit.semantic_digest for unit in binding.units),
            gate_receipt=envelope.gate_receipt,
            provider_id=envelope.alignment.provider_id,
            alignment_identity=canonical_json(envelope.alignment.to_dict()),
            execution_status=execution_status,
            output_present=output_present,
            continuity_evaluation=continuity_evaluation,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.evidence.canonical_execution.v1",
            "schema_version": self.schema_version,
            "source_ref": self.source_ref,
            "correlation": {
                "conversation_id": self.conversation_id,
                "turn_id": self.turn_id,
            },
            "comparison_inputs": {
                "semantic_fingerprint": self.semantic_fingerprint,
                "ordered_unit_digests": list(self.ordered_unit_digests),
                "provider_id": self.provider_id,
                "alignment_identity": self.alignment_identity,
                "gate_receipt": self.gate_receipt,
            },
            "execution": {
                "status": self.execution_status,
                "output_present": self.output_present,
            },
            "continuity_evaluation": _optional_to_dict(self.continuity_evaluation),
        }


@dataclass(frozen=True, slots=True)
class ComparisonDimension:
    name: str
    reference_value: str | None
    canonical_value: str | None
    reference_available: bool
    canonical_available: bool
    equal: bool | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "reference_value": self.reference_value,
            "canonical_value": self.canonical_value,
            "reference_available": self.reference_available,
            "canonical_available": self.canonical_available,
            "equal": self.equal,
        }


@dataclass(frozen=True, slots=True)
class ContinuityEvaluationBinding:
    evidence_side: str
    source_ref: str
    fields_digest: str
    pair_conversation_id: str
    pair_turn_id: str
    external_correlation_id: str | None
    comparison_provenance: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_side": self.evidence_side,
            "source_ref": self.source_ref,
            "fields_digest": self.fields_digest,
            "pair_identity": {
                "conversation_id": self.pair_conversation_id,
                "turn_id": self.pair_turn_id,
                "external_correlation_id": self.external_correlation_id,
            },
            "comparison_provenance": self.comparison_provenance,
        }


@dataclass(frozen=True, slots=True)
class SideBySideComparisonRecord:
    schema_version: str
    conversation_id: str
    turn_id: str
    external_correlation_id: str | None
    reference_source_ref: str
    canonical_source_ref: str
    dimensions: tuple[ComparisonDimension, ...]
    continuity_bindings: tuple[ContinuityEvaluationBinding, ...]
    comparison_provenance: str
    replay_digest: str

    def __post_init__(self) -> None:
        if self.schema_version != SIDE_BY_SIDE_COMPARISON_SCHEMA_VERSION:
            raise TypeError("comparison schema_version is inexact")
        _require_nonempty_string(self.conversation_id, "conversation_id")
        _require_nonempty_string(self.turn_id, "turn_id")
        _require_nonempty_string(self.reference_source_ref, "reference source_ref")
        _require_nonempty_string(self.canonical_source_ref, "canonical source_ref")
        if type(self.dimensions) is not tuple or not self.dimensions:
            raise TypeError("comparison dimensions are inexact")
        if type(self.continuity_bindings) is not tuple:
            raise TypeError("continuity bindings are inexact")
        for value in (*self.dimensions, *self.continuity_bindings):
            _require_exact_dataclass_instance(value)
        for digest_name in ("comparison_provenance", "replay_digest"):
            _require_digest_string(getattr(self, digest_name), digest_name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SIDE_BY_SIDE_COMPARISON_SCHEMA,
            "schema_version": self.schema_version,
            "correlation": {
                "conversation_id": self.conversation_id,
                "turn_id": self.turn_id,
                "external_correlation_id": self.external_correlation_id,
            },
            "sources": {
                "reference": self.reference_source_ref,
                "canonical": self.canonical_source_ref,
            },
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
            "continuity_bindings": [
                binding.to_dict() for binding in self.continuity_bindings
            ],
            "comparison_provenance": self.comparison_provenance,
            "replay_digest": self.replay_digest,
        }

    def canonical_serialization(self) -> str:
        return canonical_json(self.to_dict())

    def digest(self) -> str:
        return self.replay_digest


class EvidenceOnlySideBySideComparator:
    """Pair exact execution evidence without producing any response choice."""

    def compare(
        self,
        reference: ReferenceExecutionEvidence,
        canonical: CanonicalExecutionEvidence,
        *,
        external_correlation_id: str | None = None,
    ) -> SideBySideComparisonRecord:
        if type(self) is not EvidenceOnlySideBySideComparator:
            raise TypeError("comparison requires the exact comparator")
        _require_exact_dataclass_instance(reference)
        _require_exact_dataclass_instance(canonical)
        if external_correlation_id is not None:
            _require_nonempty_string(external_correlation_id, "external_correlation_id")
        if (
            reference.conversation_id != canonical.conversation_id
            or reference.turn_id != canonical.turn_id
        ):
            raise SideBySideComparisonRejected(
                "reference and canonical correlation identities do not match"
            )

        dimensions = (
            _dimension(
                "correlation_identity",
                _identity_value(reference),
                _identity_value(canonical),
            ),
            _dimension(
                "semantic_fingerprint",
                reference.semantic_fingerprint,
                canonical.semantic_fingerprint,
            ),
            _dimension(
                "message_unit_order",
                _order_value(reference.ordered_unit_digests),
                _order_value(canonical.ordered_unit_digests),
            ),
            _dimension(
                "provider_identity",
                reference.provider_id,
                canonical.provider_id,
            ),
            _dimension(
                "alignment_identity",
                reference.alignment_identity,
                canonical.alignment_identity,
            ),
            _dimension(
                "gate_receipt",
                reference.gate_receipt,
                canonical.gate_receipt,
            ),
            _output_dimension(reference, canonical),
        )
        body = {
            "schema": SIDE_BY_SIDE_COMPARISON_SCHEMA,
            "schema_version": SIDE_BY_SIDE_COMPARISON_SCHEMA_VERSION,
            "correlation": {
                "conversation_id": reference.conversation_id,
                "turn_id": reference.turn_id,
                "external_correlation_id": external_correlation_id,
            },
            "sources": {
                "reference": reference.source_ref,
                "canonical": canonical.source_ref,
            },
            "dimensions": [dimension.to_dict() for dimension in dimensions],
            "continuity_evidence": {
                "reference": _optional_to_dict(reference.continuity_evaluation),
                "canonical": _optional_to_dict(canonical.continuity_evaluation),
            },
        }
        comparison_provenance = _digest(body)
        continuity_bindings = _continuity_bindings(
            reference=reference,
            canonical=canonical,
            external_correlation_id=external_correlation_id,
            comparison_provenance=comparison_provenance,
        )
        complete_record = {
            **body,
            "continuity_bindings": [
                binding.to_dict() for binding in continuity_bindings
            ],
            "comparison_provenance": comparison_provenance,
        }
        replay_digest = _digest(complete_record)
        return SideBySideComparisonRecord(
            schema_version=SIDE_BY_SIDE_COMPARISON_SCHEMA_VERSION,
            conversation_id=reference.conversation_id,
            turn_id=reference.turn_id,
            external_correlation_id=external_correlation_id,
            reference_source_ref=reference.source_ref,
            canonical_source_ref=canonical.source_ref,
            dimensions=dimensions,
            continuity_bindings=continuity_bindings,
            comparison_provenance=comparison_provenance,
            replay_digest=replay_digest,
        )


def _validate_common_evidence(
    *,
    schema_version: str,
    source_ref: str,
    conversation_id: str,
    turn_id: str,
) -> None:
    if schema_version != SIDE_BY_SIDE_COMPARISON_SCHEMA_VERSION:
        raise TypeError("comparison evidence schema_version is inexact")
    _require_nonempty_string(source_ref, "source_ref")
    _require_nonempty_string(conversation_id, "conversation_id")
    _require_nonempty_string(turn_id, "turn_id")


def _validate_optional_evidence_fields(
    *,
    semantic_fingerprint: str | None,
    ordered_unit_digests: tuple[str, ...],
    provider_id: str | None,
    alignment_identity: str | None,
    gate_receipt: str | None,
    continuity_evaluation: ContinuityEvaluationEvidence | None,
    require_core_fields: bool = False,
) -> None:
    if require_core_fields:
        _require_digest_string(semantic_fingerprint, "semantic_fingerprint")
        _require_digest_string(gate_receipt, "gate_receipt")
        _require_nonempty_string(provider_id, "provider_id")
        _require_nonempty_string(alignment_identity, "alignment_identity")
    if semantic_fingerprint is not None:
        _require_digest_string(semantic_fingerprint, "semantic_fingerprint")
    if gate_receipt is not None:
        _require_digest_string(gate_receipt, "gate_receipt")
    if provider_id is not None:
        _require_nonempty_string(provider_id, "provider_id")
    if alignment_identity is not None:
        _require_nonempty_string(alignment_identity, "alignment_identity")
    if type(ordered_unit_digests) is not tuple:
        raise TypeError("ordered_unit_digests is inexact")
    for digest in ordered_unit_digests:
        _require_digest_string(digest, "ordered unit digest")
    if require_core_fields and not ordered_unit_digests:
        raise TypeError("canonical ordered_unit_digests are partial")
    if continuity_evaluation is not None:
        _require_exact_dataclass_instance(continuity_evaluation)


def _dimension(
    name: str,
    reference_value: str | None,
    canonical_value: str | None,
) -> ComparisonDimension:
    reference_available = reference_value is not None
    canonical_available = canonical_value is not None
    return ComparisonDimension(
        name=name,
        reference_value=reference_value,
        canonical_value=canonical_value,
        reference_available=reference_available,
        canonical_available=canonical_available,
        equal=(
            reference_value == canonical_value
            if reference_available and canonical_available
            else None
        ),
    )


def _output_dimension(
    reference: ReferenceExecutionEvidence,
    canonical: CanonicalExecutionEvidence,
) -> ComparisonDimension:
    reference_value = (
        f"status={reference.execution_status};"
        f"output_present={str(reference.output_present).lower()}"
    )
    canonical_value = (
        None
        if canonical.execution_status is None or canonical.output_present is None
        else (
            f"status={canonical.execution_status};"
            f"output_present={str(canonical.output_present).lower()}"
        )
    )
    return _dimension("output_execution", reference_value, canonical_value)


def _identity_value(
    evidence: ReferenceExecutionEvidence | CanonicalExecutionEvidence,
) -> str:
    return f"conversation_id={evidence.conversation_id};turn_id={evidence.turn_id}"


def _order_value(digests: tuple[str, ...]) -> str | None:
    if not digests:
        return None
    return _digest(list(digests))


def _continuity_bindings(
    *,
    reference: ReferenceExecutionEvidence,
    canonical: CanonicalExecutionEvidence,
    external_correlation_id: str | None,
    comparison_provenance: str,
) -> tuple[ContinuityEvaluationBinding, ...]:
    bindings: list[ContinuityEvaluationBinding] = []
    if reference.continuity_evaluation is not None:
        bindings.append(
            ContinuityEvaluationBinding(
                evidence_side="reference",
                source_ref=reference.continuity_evaluation.source_ref,
                fields_digest=reference.continuity_evaluation.digest(),
                pair_conversation_id=reference.conversation_id,
                pair_turn_id=reference.turn_id,
                external_correlation_id=external_correlation_id,
                comparison_provenance=comparison_provenance,
            )
        )
    if canonical.continuity_evaluation is not None:
        bindings.append(
            ContinuityEvaluationBinding(
                evidence_side="canonical",
                source_ref=canonical.continuity_evaluation.source_ref,
                fields_digest=canonical.continuity_evaluation.digest(),
                pair_conversation_id=canonical.conversation_id,
                pair_turn_id=canonical.turn_id,
                external_correlation_id=external_correlation_id,
                comparison_provenance=comparison_provenance,
            )
        )
    return tuple(bindings)


def _optional_to_dict(
    value: ContinuityEvaluationEvidence | None,
) -> dict[str, Any] | None:
    return value.to_dict() if value is not None else None


def _require_nonempty_string(value: str, field_name: str) -> None:
    if type(value) is not str or not value:
        raise TypeError(f"{field_name} is inexact")


def _require_digest_string(value: str, field_name: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise TypeError(f"{field_name} is inexact")
    try:
        int(value, 16)
    except ValueError as error:
        raise TypeError(f"{field_name} is inexact") from error


def _require_exact_dataclass_instance(value: object) -> None:
    expected_types = {
        ContinuityEvaluationEvidence,
        ComparisonDimension,
        ContinuityEvaluationBinding,
        ReferenceExecutionEvidence,
        CanonicalExecutionEvidence,
    }
    if type(value) not in expected_types:
        raise TypeError("comparison evidence type is inexact")


def _digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = [
    "CanonicalExecutionEvidence",
    "ComparisonDimension",
    "ContinuityEvaluationBinding",
    "ContinuityEvaluationEvidence",
    "EvidenceOnlySideBySideComparator",
    "ReferenceExecutionEvidence",
    "SIDE_BY_SIDE_COMPARISON_SCHEMA",
    "SIDE_BY_SIDE_COMPARISON_SCHEMA_VERSION",
    "SideBySideComparisonRecord",
    "SideBySideComparisonRejected",
]

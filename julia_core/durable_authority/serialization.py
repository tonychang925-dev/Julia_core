"""Deterministic governed-state envelope creation and parsing."""

from __future__ import annotations

from typing import Any

from julia_core.identity import (
    GovernedIdentity,
    IdentityBoundary,
    IdentityContract,
    IdentityProvenance,
    IdentityRef,
    IdentityStatus,
    IdentityValue,
    IdentityVersion,
    RelationshipRoleAnchor,
)
from julia_core.identity.contracts import IdentityAnchor, IdentityGovernanceEvent
from julia_core.memory_experience import (
    CommitmentTransferSemantics,
    EpisodicExperienceContent,
    GovernedMemoryExperience,
    MemoryExperienceAdmission,
    MemoryExperienceProvenance,
    MemoryExperienceRecord,
    MemoryExperienceRef,
    MemoryExperienceStatus,
    MemoryExperienceType,
    NarrativeExperienceContent,
    PreferenceExperienceContent,
    ProjectCommitmentExperienceContent,
    RelationshipExperienceContent,
)
from julia_core.runtime_canonical_binding import (
    BINDING_SCHEMA_VERSION,
    GovernedRuntimeCanonicalAuthorityBinding,
    RuntimeCanonicalAuthorityBinding,
    RuntimeCanonicalAuthorityBindingGovernanceEvent,
    RuntimeCanonicalAuthorityBindingProvenance,
    RuntimeCanonicalAuthorityBindingRef,
    RuntimeCanonicalAuthorityBindingStatus,
)

from .contracts import (
    ENVELOPE_SCHEMA_VERSION,
    IDENTITY_OBJECT_SCHEMA,
    MEMORY_EXPERIENCE_OBJECT_SCHEMA,
    RUNTIME_BINDING_OBJECT_SCHEMA,
    AuthorityFamily,
    DurableAuthorityEnvelope,
    DurableAuthorityErrorCode,
    DurableAuthorityPersistenceError,
    canonical_json,
    decode_canonical_json,
    digest_payload,
    envelope_digest,
)


ENVELOPE_FIELDS = frozenset(
    {
        "envelope_schema",
        "authority_family",
        "authority_object_ref",
        "authority_object_schema",
        "serialized_payload",
        "payload_digest",
        "governance_events",
        "lifecycle_status",
        "lineage_metadata",
        "provenance",
        "envelope_digest",
    }
)


def build_identity_envelope(governed: GovernedIdentity) -> DurableAuthorityEnvelope:
    if type(governed) is not GovernedIdentity:
        raise _type_mismatch("GovernedIdentity")
    serialized_payload = governed.version.canonical_serialization()
    payload = governed.version.to_dict()
    provenance = [item.to_dict() for item in governed.version.provenance_refs]
    digest = envelope_digest(
        envelope_schema=ENVELOPE_SCHEMA_VERSION,
        authority_family=AuthorityFamily.IDENTITY,
        authority_object_ref=governed.ref.uri,
        authority_object_schema=IDENTITY_OBJECT_SCHEMA,
        serialized_payload=serialized_payload,
        payload_digest=governed.digest,
        governance_events=tuple(item.to_dict() for item in governed.governance_events),
        lifecycle_status=governed.status.value,
        lineage_metadata=_identity_lineage(governed.version),
        provenance=tuple(provenance),
    )
    envelope = DurableAuthorityEnvelope(
        ENVELOPE_SCHEMA_VERSION,
        AuthorityFamily.IDENTITY,
        governed.ref.uri,
        IDENTITY_OBJECT_SCHEMA,
        serialized_payload,
        governed.digest,
        tuple(item.to_dict() for item in governed.governance_events),
        governed.status.value,
        _identity_lineage(governed.version),
        tuple(provenance),
        digest,
    )
    validate_envelope_semantics(envelope)
    return envelope


def build_memory_experience_envelope(
    governed: GovernedMemoryExperience,
) -> DurableAuthorityEnvelope:
    if type(governed) is not GovernedMemoryExperience:
        raise _type_mismatch("GovernedMemoryExperience")
    serialized_payload = governed.record.canonical_serialization()
    payload = governed.record.canonical_payload()
    governance_events = [item for item in governed.to_dict()["governance_events"]]
    provenance = [item.to_dict() for item in governed.record.provenance_refs]
    digest = envelope_digest(
        envelope_schema=ENVELOPE_SCHEMA_VERSION,
        authority_family=AuthorityFamily.MEMORY_EXPERIENCE,
        authority_object_ref=governed.ref.uri,
        authority_object_schema=MEMORY_EXPERIENCE_OBJECT_SCHEMA,
        serialized_payload=serialized_payload,
        payload_digest=governed.record.digest(),
        governance_events=tuple(governance_events),
        lifecycle_status=governed.status.value,
        lineage_metadata=_memory_lineage(governed.record),
        provenance=tuple(provenance),
    )
    envelope = DurableAuthorityEnvelope(
        ENVELOPE_SCHEMA_VERSION,
        AuthorityFamily.MEMORY_EXPERIENCE,
        governed.ref.uri,
        MEMORY_EXPERIENCE_OBJECT_SCHEMA,
        serialized_payload,
        governed.record.digest(),
        tuple(governance_events),
        governed.status.value,
        _memory_lineage(governed.record),
        tuple(provenance),
        digest,
    )
    validate_envelope_semantics(envelope)
    return envelope


def build_runtime_binding_envelope(
    governed: GovernedRuntimeCanonicalAuthorityBinding,
) -> DurableAuthorityEnvelope:
    if type(governed) is not GovernedRuntimeCanonicalAuthorityBinding:
        raise _type_mismatch("GovernedRuntimeCanonicalAuthorityBinding")
    serialized_payload = governed.binding.canonical_serialization()
    governance_events = tuple(item.to_dict() for item in governed.governance_events)
    provenance = tuple(item.to_dict() for item in governed.binding.provenance_refs)
    digest = envelope_digest(
        envelope_schema=ENVELOPE_SCHEMA_VERSION,
        authority_family=AuthorityFamily.RUNTIME_BINDING,
        authority_object_ref=governed.ref.uri,
        authority_object_schema=BINDING_SCHEMA_VERSION,
        serialized_payload=serialized_payload,
        payload_digest=governed.digest,
        governance_events=governance_events,
        lifecycle_status=governed.status.value,
        lineage_metadata=_runtime_lineage(governed.binding),
        provenance=provenance,
    )
    envelope = DurableAuthorityEnvelope(
        ENVELOPE_SCHEMA_VERSION,
        AuthorityFamily.RUNTIME_BINDING,
        governed.ref.uri,
        BINDING_SCHEMA_VERSION,
        serialized_payload,
        governed.digest,
        governance_events,
        governed.status.value,
        _runtime_lineage(governed.binding),
        provenance,
        digest,
    )
    validate_envelope_semantics(envelope)
    return envelope


def envelope_from_dict(data: object) -> DurableAuthorityEnvelope:
    if type(data) is not dict or frozenset(data) != ENVELOPE_FIELDS:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.PARTIAL_ENVELOPE,
            "durable envelope fields must be exact and complete",
        )
    family = data["authority_family"]
    if type(family) is not str or not hasattr(AuthorityFamily, family):
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.UNKNOWN_AUTHORITY_FAMILY,
            "authority family is unknown",
        )
    try:
        return DurableAuthorityEnvelope(
            data["envelope_schema"],
            AuthorityFamily(family),
            data["authority_object_ref"],
            data["authority_object_schema"],
            data["serialized_payload"],
            data["payload_digest"],
            tuple(data["governance_events"]),
            data["lifecycle_status"],
            data["lineage_metadata"],
            tuple(data["provenance"]),
            data["envelope_digest"],
        )
    except DurableAuthorityPersistenceError:
        raise
    except (TypeError, ValueError) as error:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "durable envelope representation is malformed",
        ) from error


def validate_envelope_semantics(envelope: DurableAuthorityEnvelope) -> None:
    if envelope.payload_digest != digest_payload(envelope.serialized_payload):
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.PAYLOAD_DIGEST_MISMATCH,
            "durable payload digest does not match serialized payload",
        )
    payload = decode_canonical_json(envelope.serialized_payload)
    family = envelope.authority_family
    if family is AuthorityFamily.IDENTITY:
        governed = parse_identity_governed(payload, envelope.governance_events)
        schema = IDENTITY_OBJECT_SCHEMA
        lineage = _identity_lineage(governed.version)
        provenance = tuple(item.to_dict() for item in governed.version.provenance_refs)
        ref = governed.ref.uri
        status = governed.status.value
        exact_payload = governed.version.canonical_serialization()
    elif family is AuthorityFamily.MEMORY_EXPERIENCE:
        governed = parse_memory_experience_governed(payload, envelope.governance_events)
        schema = MEMORY_EXPERIENCE_OBJECT_SCHEMA
        lineage = _memory_lineage(governed.record)
        provenance = tuple(item.to_dict() for item in governed.record.provenance_refs)
        ref = governed.ref.uri
        status = governed.status.value
        exact_payload = governed.record.canonical_serialization()
    elif family is AuthorityFamily.RUNTIME_BINDING:
        governed = parse_runtime_binding_governed(payload, envelope.governance_events)
        schema = BINDING_SCHEMA_VERSION
        lineage = _runtime_lineage(governed.binding)
        provenance = tuple(item.to_dict() for item in governed.binding.provenance_refs)
        ref = governed.ref.uri
        status = governed.status.value
        exact_payload = governed.binding.canonical_serialization()
    else:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.UNKNOWN_AUTHORITY_FAMILY,
            "authority family is unknown",
        )
    if envelope.authority_object_schema != schema:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.UNSUPPORTED_SCHEMA,
            "authority object schema does not match its family",
        )
    if (
        exact_payload != envelope.serialized_payload
        or envelope.authority_object_ref != ref
        or envelope.lifecycle_status != status
        or envelope.lineage_metadata != lineage
        or envelope.provenance != provenance
    ):
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.REF_MISMATCH,
            "durable envelope metadata does not match governed payload",
        )


def parse_identity_governed(payload, governance_events):
    version = parse_identity_version(payload)
    events = tuple(
        _parse_identity_event(item, version.ref) for item in governance_events
    )
    _validate_identity_events(events, version.ref)
    return GovernedIdentity(version, events[-1].status, events)


def parse_memory_experience_governed(payload, governance_events):
    record = parse_memory_experience_record(payload)
    events = tuple(_parse_memory_event(item, record.ref) for item in governance_events)
    _validate_memory_events(events, record.ref)
    return GovernedMemoryExperience(record, events[-1][0], events)


def parse_runtime_binding_governed(payload, governance_events):
    binding = parse_runtime_binding(payload)
    events = tuple(
        _parse_runtime_event(item, binding.ref) for item in governance_events
    )
    _validate_runtime_events(events, binding.ref)
    return GovernedRuntimeCanonicalAuthorityBinding(binding, events[-1].status, events)


def parse_identity_version(data: object) -> IdentityVersion:
    try:
        _require_exact_dict(data)
        if data.get("schema") != IDENTITY_OBJECT_SCHEMA:
            raise _schema_failure()
        identity = data["identity"]
        _require_exact_dict(identity)
        contract = IdentityContract(
            identity_id=identity["identity_id"],
            anchors=tuple(IdentityAnchor(**item) for item in identity["anchors"]),
            values=tuple(IdentityValue(**item) for item in identity["values"]),
            boundaries=tuple(
                IdentityBoundary(**item) for item in identity["boundaries"]
            ),
            relationship_role_anchors=tuple(
                RelationshipRoleAnchor(**item)
                for item in identity["relationship_role_anchors"]
            ),
        )
        provenance = tuple(
            IdentityProvenance(
                source_type=item["source_type"],
                source_ref=item["source_ref"],
                source_digest=item["source_digest"],
                admission_metadata=tuple(item["admission_metadata"].items()),
            )
            for item in data["provenance_refs"]
        )
        return IdentityVersion(
            contract=contract,
            lineage_id=data["lineage_id"],
            version_id=data["version_id"],
            predecessor_version_id=data["predecessor_version_id"],
            created_at=data["created_at"],
            provenance_refs=provenance,
        )
    except DurableAuthorityPersistenceError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "identity payload is malformed",
        ) from error


def parse_memory_experience_record(data: object) -> MemoryExperienceRecord:
    try:
        _require_exact_dict(data)
        if data.get("schema") != MEMORY_EXPERIENCE_OBJECT_SCHEMA:
            raise _schema_failure()
        experience_type = MemoryExperienceType(data["experience_type"])
        content = _CONTENT_PARSERS[experience_type](data["content"])
        provenance = tuple(
            MemoryExperienceProvenance(
                source_type=item["source_type"],
                source_ref=item["source_ref"],
                source_digest=item["source_digest"],
                admission_metadata=tuple(item["admission_metadata"].items()),
            )
            for item in data["provenance_refs"]
        )
        return MemoryExperienceRecord(
            experience_id=data["experience_id"],
            version_id=data["version_id"],
            experience_type=experience_type,
            content=content,
            provenance_refs=provenance,
            created_at=data["created_at"],
            predecessor_version_id=data["predecessor_version_id"],
        )
    except DurableAuthorityPersistenceError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "memory experience payload is malformed",
        ) from error


def parse_runtime_binding(data: object) -> RuntimeCanonicalAuthorityBinding:
    try:
        _require_exact_dict(data)
        if data.get("schema_version") != BINDING_SCHEMA_VERSION:
            raise _schema_failure()
        identity_ref = IdentityRef(**data["identity_ref"])
        experience_refs = tuple(
            MemoryExperienceRef(**item) for item in data["experience_refs"]
        )
        provenance = tuple(
            RuntimeCanonicalAuthorityBindingProvenance(
                source_type=item["source_type"],
                source_ref=item["source_ref"],
                source_digest=item["source_digest"],
                admission_metadata=tuple(item["admission_metadata"].items()),
            )
            for item in data["provenance_refs"]
        )
        return RuntimeCanonicalAuthorityBinding(
            schema_version=data["schema_version"],
            binding_id=data["binding_id"],
            binding_version=data["binding_version"],
            predecessor_version_id=data["predecessor_version_id"],
            identity_ref=identity_ref,
            experience_refs=experience_refs,
            provenance_refs=provenance,
            created_at=data["created_at"],
        )
    except DurableAuthorityPersistenceError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "runtime binding payload is malformed",
        ) from error


def _parse_identity_event(data: object, ref: IdentityRef):
    try:
        _require_exact_dict(data)
        _require_exact_fields(
            data, {"event_id", "target", "status", "actor", "reason", "occurred_at"}
        )
        return IdentityGovernanceEvent(
            event_id=data["event_id"],
            target=IdentityRef(**data["target"]),
            status=IdentityStatus(data["status"]),
            actor=data["actor"],
            reason=data["reason"],
            occurred_at=data["occurred_at"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "identity governance event is malformed",
        ) from error


def _parse_memory_event(data: object, ref: MemoryExperienceRef):
    try:
        _require_exact_dict(data)
        _require_exact_fields(data, {"status", "admission"})
        admission_data = data["admission"]
        admission = None
        if admission_data is not None:
            admission = MemoryExperienceAdmission(
                admission_id=admission_data["admission_id"],
                target=MemoryExperienceRef(**admission_data["target"]),
                actor=admission_data["actor"],
                reason=admission_data["reason"],
                occurred_at=admission_data["occurred_at"],
            )
        return MemoryExperienceStatus(data["status"]), admission
    except (KeyError, TypeError, ValueError) as error:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "memory experience governance event is malformed",
        ) from error


def _parse_runtime_event(data: object, ref: RuntimeCanonicalAuthorityBindingRef):
    try:
        _require_exact_dict(data)
        _require_exact_fields(
            data, {"event_id", "target", "status", "actor", "reason", "occurred_at"}
        )
        return RuntimeCanonicalAuthorityBindingGovernanceEvent(
            event_id=data["event_id"],
            target=RuntimeCanonicalAuthorityBindingRef(**data["target"]),
            status=RuntimeCanonicalAuthorityBindingStatus(data["status"]),
            actor=data["actor"],
            reason=data["reason"],
            occurred_at=data["occurred_at"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "runtime binding governance event is malformed",
        ) from error


def _validate_identity_events(events, ref: IdentityRef) -> None:
    if not events:
        raise _lifecycle_failure()
    statuses = [item.status for item in events]
    _validate_standard_lifecycle(statuses)
    _require_event_targets(events, ref)


def _validate_memory_events(events, ref: MemoryExperienceRef) -> None:
    if not events:
        raise _lifecycle_failure()
    statuses = [item[0] for item in events]
    allowed_from = {
        MemoryExperienceStatus.CANDIDATE: {
            MemoryExperienceStatus.ADMITTED,
            MemoryExperienceStatus.SUPERSEDED,
            MemoryExperienceStatus.RETIRED,
        },
        MemoryExperienceStatus.ADMITTED: {
            MemoryExperienceStatus.SUPERSEDED,
            MemoryExperienceStatus.RETIRED,
        },
        MemoryExperienceStatus.SUPERSEDED: {MemoryExperienceStatus.RETIRED},
        MemoryExperienceStatus.RETIRED: set(),
    }
    _validate_status_sequence(statuses, allowed_from)
    for status, admission in events:
        if admission is not None and admission.target != ref:
            raise _event_target_failure()


def _validate_runtime_events(events, ref: RuntimeCanonicalAuthorityBindingRef) -> None:
    if not events:
        raise _lifecycle_failure()
    statuses = [item.status for item in events]
    allowed_from = {
        RuntimeCanonicalAuthorityBindingStatus.CANDIDATE: {
            RuntimeCanonicalAuthorityBindingStatus.ADMITTED,
            RuntimeCanonicalAuthorityBindingStatus.SUPERSEDED,
            RuntimeCanonicalAuthorityBindingStatus.RETIRED,
        },
        RuntimeCanonicalAuthorityBindingStatus.ADMITTED: {
            RuntimeCanonicalAuthorityBindingStatus.ADMITTED,
            RuntimeCanonicalAuthorityBindingStatus.SUPERSEDED,
            RuntimeCanonicalAuthorityBindingStatus.RETIRED,
        },
        RuntimeCanonicalAuthorityBindingStatus.SUPERSEDED: {
            RuntimeCanonicalAuthorityBindingStatus.RETIRED
        },
        RuntimeCanonicalAuthorityBindingStatus.RETIRED: set(),
    }
    _validate_status_sequence(statuses, allowed_from)
    _require_event_targets(events, ref)


def _require_event_targets(events, ref) -> None:
    if any(item.target != ref for item in events):
        raise _event_target_failure()


def _validate_standard_lifecycle(statuses) -> None:
    allowed_from = {
        IdentityStatus.CANDIDATE: {
            IdentityStatus.ADMITTED,
            IdentityStatus.SUPERSEDED,
            IdentityStatus.RETIRED,
        },
        IdentityStatus.ADMITTED: {
            IdentityStatus.ADMITTED,
            IdentityStatus.SUPERSEDED,
            IdentityStatus.RETIRED,
        },
        IdentityStatus.SUPERSEDED: {IdentityStatus.RETIRED},
        IdentityStatus.RETIRED: set(),
    }
    _validate_status_sequence(statuses, allowed_from)


def _validate_status_sequence(statuses, allowed_from) -> None:
    if statuses[0] not in allowed_from or any(
        successor not in allowed_from[previous]
        for previous, successor in zip(statuses, statuses[1:])
    ):
        raise _lifecycle_failure()


def _identity_lineage(version: IdentityVersion) -> dict[str, Any]:
    return {
        "lineage_id": version.lineage_id,
        "version_id": version.version_id,
        "predecessor_version_id": version.predecessor_version_id,
    }


def _memory_lineage(record: MemoryExperienceRecord) -> dict[str, Any]:
    return {
        "experience_id": record.experience_id,
        "version_id": record.version_id,
        "predecessor_version_id": record.predecessor_version_id,
    }


def _runtime_lineage(binding: RuntimeCanonicalAuthorityBinding) -> dict[str, Any]:
    return {
        "binding_id": binding.binding_id,
        "binding_version": binding.binding_version,
        "predecessor_version_id": binding.predecessor_version_id,
    }


def _parse_narrative(data):
    return NarrativeExperienceContent(
        event=data["event"],
        meaning_at_time=data["meaning_at_time"],
        significance=data["significance"],
        later_reinterpretation=data["later_reinterpretation"],
        source_refs=tuple(data["source_refs"]),
    )


def _parse_relationship(data):
    return RelationshipExperienceContent(
        relationship_id=data["relationship_id"],
        event=data["event"],
        interpretation=data["interpretation"],
        occurred_at=data["occurred_at"],
    )


def _parse_preference(data):
    return PreferenceExperienceContent(
        subject=data["subject"],
        preference=data["preference"],
        learned_from_event=data["learned_from_event"],
        source_ref=data["source_ref"],
    )


def _parse_project_commitment(data):
    return ProjectCommitmentExperienceContent(
        subject=data["subject"],
        counterparty=data["counterparty"],
        scope=data["scope"],
        commitment=data["commitment"],
        transfer_semantics=CommitmentTransferSemantics(data["transfer_semantics"]),
        occurred_at=data["occurred_at"],
    )


def _parse_episodic(data):
    return EpisodicExperienceContent(
        event=data["event"],
        occurred_at=data["occurred_at"],
        context=data["context"],
        source_ref=data["source_ref"],
    )


_CONTENT_PARSERS = {
    MemoryExperienceType.NARRATIVE: _parse_narrative,
    MemoryExperienceType.RELATIONSHIP: _parse_relationship,
    MemoryExperienceType.PREFERENCE: _parse_preference,
    MemoryExperienceType.PROJECT_COMMITMENT: _parse_project_commitment,
    MemoryExperienceType.EPISODIC: _parse_episodic,
}


def _require_exact_dict(data: object) -> None:
    if type(data) is not dict:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "durable JSON object is malformed",
        )


def _require_exact_fields(data: dict, expected: set[str]) -> None:
    if frozenset(data) != expected:
        raise ValueError("durable governance event fields are inexact")


def _schema_failure() -> DurableAuthorityPersistenceError:
    return DurableAuthorityPersistenceError(
        DurableAuthorityErrorCode.UNSUPPORTED_SCHEMA,
        "governed object schema is unsupported",
    )


def _lifecycle_failure() -> DurableAuthorityPersistenceError:
    return DurableAuthorityPersistenceError(
        DurableAuthorityErrorCode.INCONSISTENT_LIFECYCLE,
        "governance history is inconsistent",
    )


def _event_target_failure() -> DurableAuthorityPersistenceError:
    return DurableAuthorityPersistenceError(
        DurableAuthorityErrorCode.GOVERNANCE_EVENT_TARGET_MISMATCH,
        "governance event target does not match governed object ref",
    )


def _type_mismatch(name: str) -> DurableAuthorityPersistenceError:
    return DurableAuthorityPersistenceError(
        DurableAuthorityErrorCode.TYPE_MISMATCH,
        f"durable authority source requires exact {name}",
    )

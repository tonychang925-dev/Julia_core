"""Exact fail-closed restoration without governance replay."""

from __future__ import annotations

from types import MappingProxyType

from julia_core.identity import IdentityRef, IdentityRepository
from julia_core.memory_experience import (
    MemoryExperienceRef,
    MemoryExperienceRepository,
)
from julia_core.runtime_canonical_binding import (
    RuntimeCanonicalAuthorityBindingRef,
    RuntimeCanonicalAuthorityBindingRepository,
)

from .adapters import DurableAuthorityReader
from .contracts import (
    AuthorityFamily,
    DurableAuthorityErrorCode,
    DurableAuthorityPersistenceError,
)
from .serialization import (
    parse_identity_governed,
    parse_memory_experience_governed,
    parse_runtime_binding_governed,
    validate_envelope_semantics,
)


class DurableAuthorityReconstructor:
    __slots__ = ("_reader",)

    def __init__(self, reader: DurableAuthorityReader) -> None:
        object.__setattr__(self, "_reader", reader)

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("durable authority reconstructors are immutable")

    def reconstruct_identity(self, ref: IdentityRef):
        envelope = self._reader.read_exact(AuthorityFamily.IDENTITY, ref)
        validate_envelope_semantics(envelope)
        return parse_identity_governed(
            envelope.payload_object, envelope.governance_events
        )

    def reconstruct_memory_experience(self, ref: MemoryExperienceRef):
        envelope = self._reader.read_exact(AuthorityFamily.MEMORY_EXPERIENCE, ref)
        validate_envelope_semantics(envelope)
        return parse_memory_experience_governed(
            envelope.payload_object, envelope.governance_events
        )

    def reconstruct_runtime_binding(self, ref: RuntimeCanonicalAuthorityBindingRef):
        envelope = self._reader.read_exact(AuthorityFamily.RUNTIME_BINDING, ref)
        validate_envelope_semantics(envelope)
        return parse_runtime_binding_governed(
            envelope.payload_object, envelope.governance_events
        )


def restore_identity_repository(reader: DurableAuthorityReader) -> IdentityRepository:
    repository = IdentityRepository()
    governed_by_ref = {}
    for ref_uri in reader.list_exact_refs(AuthorityFamily.IDENTITY):
        envelope = _read_by_uri(reader, AuthorityFamily.IDENTITY, ref_uri)
        governed = parse_identity_governed(
            envelope.payload_object, envelope.governance_events
        )
        governed_by_ref[governed.ref] = governed
    _validate_identity_predecessors(governed_by_ref)
    versions = MappingProxyType(
        {ref: item.version for ref, item in governed_by_ref.items()}
    )
    events = MappingProxyType(
        {ref: item.governance_events for ref, item in governed_by_ref.items()}
    )
    object.__setattr__(repository, "_versions", versions)
    object.__setattr__(repository, "_events", events)
    return repository


def restore_memory_experience_repository(
    reader: DurableAuthorityReader,
) -> MemoryExperienceRepository:
    repository = MemoryExperienceRepository()
    governed_by_ref = {}
    for ref_uri in reader.list_exact_refs(AuthorityFamily.MEMORY_EXPERIENCE):
        envelope = _read_by_uri(reader, AuthorityFamily.MEMORY_EXPERIENCE, ref_uri)
        governed = parse_memory_experience_governed(
            envelope.payload_object, envelope.governance_events
        )
        governed_by_ref[governed.ref] = governed
    _validate_memory_predecessors(governed_by_ref)
    object.__setattr__(
        repository,
        "_records",
        MappingProxyType({ref: item.record for ref, item in governed_by_ref.items()}),
    )
    object.__setattr__(
        repository,
        "_states",
        MappingProxyType({ref: item.status for ref, item in governed_by_ref.items()}),
    )
    object.__setattr__(
        repository,
        "_events",
        MappingProxyType(
            {ref: item.governance_events for ref, item in governed_by_ref.items()}
        ),
    )
    return repository


def restore_runtime_binding_repository(
    reader: DurableAuthorityReader,
) -> RuntimeCanonicalAuthorityBindingRepository:
    repository = RuntimeCanonicalAuthorityBindingRepository()
    governed_by_ref = {}
    for ref_uri in reader.list_exact_refs(AuthorityFamily.RUNTIME_BINDING):
        envelope = _read_by_uri(reader, AuthorityFamily.RUNTIME_BINDING, ref_uri)
        governed = parse_runtime_binding_governed(
            envelope.payload_object, envelope.governance_events
        )
        governed_by_ref[governed.ref] = governed
    _validate_runtime_predecessors(governed_by_ref)
    object.__setattr__(
        repository,
        "_bindings",
        MappingProxyType({ref: item.binding for ref, item in governed_by_ref.items()}),
    )
    object.__setattr__(
        repository,
        "_events",
        MappingProxyType(
            {ref: item.governance_events for ref, item in governed_by_ref.items()}
        ),
    )
    return repository


def _read_by_uri(reader: DurableAuthorityReader, family: AuthorityFamily, ref_uri: str):
    if type(ref_uri) is not str:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
            "exact ref listing returned a malformed ref",
        )
    envelope = reader.read_exact(family, _parse_ref_uri(family, ref_uri))
    validate_envelope_semantics(envelope)
    if (
        envelope.authority_family is not family
        or envelope.authority_object_ref != ref_uri
    ):
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.REF_MISMATCH,
            "reader returned an envelope for another exact authority object",
        )
    return envelope


def _parse_ref_uri(family: AuthorityFamily, ref_uri: str):
    if family is AuthorityFamily.IDENTITY:
        prefix = "identity://"
        if not ref_uri.startswith(prefix):
            raise DurableAuthorityPersistenceError(
                DurableAuthorityErrorCode.REF_MISMATCH,
                "identity ref URI is malformed",
            )
        lineage_id, version_id = ref_uri[len(prefix) :].split("/", 1)
        return IdentityRef(lineage_id, version_id)
    if family is AuthorityFamily.MEMORY_EXPERIENCE:
        prefix = "memory-experience://"
        if not ref_uri.startswith(prefix):
            raise DurableAuthorityPersistenceError(
                DurableAuthorityErrorCode.REF_MISMATCH,
                "memory experience ref URI is malformed",
            )
        experience_id, version_id = ref_uri[len(prefix) :].split("/", 1)
        return MemoryExperienceRef(experience_id, version_id)
    prefix = "runtime-canonical-binding://"
    if not ref_uri.startswith(prefix):
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.REF_MISMATCH,
            "runtime binding ref URI is malformed",
        )
    binding_id, binding_version = ref_uri[len(prefix) :].split("/", 1)
    return RuntimeCanonicalAuthorityBindingRef(binding_id, binding_version)


def _validate_identity_predecessors(governed_by_ref) -> None:
    for governed in governed_by_ref.values():
        predecessor = governed.version.predecessor_version_id
        if predecessor is None:
            continue
        expected = IdentityRef(governed.ref.lineage_id, predecessor)
        if expected not in governed_by_ref:
            raise _missing_predecessor(expected.uri)


def _validate_memory_predecessors(governed_by_ref) -> None:
    for governed in governed_by_ref.values():
        predecessor = governed.record.predecessor_version_id
        if predecessor is None:
            continue
        expected = MemoryExperienceRef(governed.ref.experience_id, predecessor)
        if expected not in governed_by_ref:
            raise _missing_predecessor(expected.uri)


def _validate_runtime_predecessors(governed_by_ref) -> None:
    for governed in governed_by_ref.values():
        predecessor = governed.binding.predecessor_version_id
        if predecessor is None:
            continue
        expected = RuntimeCanonicalAuthorityBindingRef(
            governed.ref.binding_id, predecessor
        )
        if expected not in governed_by_ref:
            raise _missing_predecessor(expected.uri)


def _missing_predecessor(ref_uri: str) -> DurableAuthorityPersistenceError:
    return DurableAuthorityPersistenceError(
        DurableAuthorityErrorCode.MISSING_PREDECESSOR,
        f"durable authority predecessor is missing: {ref_uri}",
    )


__all__ = [
    "DurableAuthorityReconstructor",
    "restore_identity_repository",
    "restore_memory_experience_repository",
    "restore_runtime_binding_repository",
]

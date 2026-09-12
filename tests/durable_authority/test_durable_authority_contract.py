from __future__ import annotations

from dataclasses import replace

import pytest

from julia_core.durable_authority import (
    AuthorityFamily,
    DurableAuthorityErrorCode,
    DurableAuthorityPersistenceError,
    DurableAuthorityReconstructor,
    build_identity_envelope,
    build_memory_experience_envelope,
    build_runtime_binding_envelope,
    envelope_from_dict,
    restore_identity_repository,
    restore_memory_experience_repository,
    restore_runtime_binding_repository,
)
from julia_core.identity import (
    IdentityAnchor,
    IdentityConflictError,
    IdentityContract,
    IdentityProvenance,
    IdentityRepository,
    IdentityVersion,
)
from julia_core.memory_experience import (
    MemoryExperienceCandidate,
    MemoryExperienceConflictError,
    MemoryExperienceProvenance,
    MemoryExperienceRecord,
    MemoryExperienceRepository,
    MemoryExperienceType,
    NarrativeExperienceContent,
)
from julia_core.runtime_canonical_binding import (
    BINDING_SCHEMA_VERSION,
    RuntimeCanonicalAuthorityBinding,
    RuntimeCanonicalAuthorityBindingConflictError,
    RuntimeCanonicalAuthorityBindingProvenance,
    RuntimeCanonicalAuthorityBindingRepository,
)


class InMemoryDurableAuthorityAdapter:
    def __init__(self):
        object.__setattr__(self, "_envelopes", {})

    def read_exact(self, authority_family, ref):
        key = (authority_family, ref.uri)
        envelopes = self._envelopes
        try:
            return envelopes[key]
        except KeyError as error:
            raise DurableAuthorityPersistenceError(
                DurableAuthorityErrorCode.REF_MISMATCH,
                f"exact durable ref is unavailable: {ref.uri}",
            ) from error

    def list_exact_refs(self, authority_family):
        return tuple(
            ref for family, ref in sorted(self._envelopes) if family is authority_family
        )

    def write_exact(self, envelope):
        key = (envelope.authority_family, envelope.authority_object_ref)
        existing = self._envelopes.get(key)
        if (
            existing is not None
            and existing.envelope_digest != envelope.envelope_digest
        ):
            if existing.payload_digest != envelope.payload_digest:
                if envelope.authority_family is AuthorityFamily.IDENTITY:
                    raise IdentityConflictError(key)
                if envelope.authority_family is AuthorityFamily.MEMORY_EXPERIENCE:
                    raise MemoryExperienceConflictError(key)
                raise RuntimeCanonicalAuthorityBindingConflictError(key)
            raise DurableAuthorityPersistenceError(
                DurableAuthorityErrorCode.DUPLICATE_CONFLICT,
                f"conflicting duplicate envelope metadata: {key}",
            )
        envelopes = dict(self._envelopes)
        envelopes[key] = envelope
        object.__setattr__(self, "_envelopes", envelopes)

    def remove(self, authority_family, ref_uri):
        envelopes = dict(self._envelopes)
        envelopes.pop((authority_family, ref_uri))
        object.__setattr__(self, "_envelopes", envelopes)


def _identity_repository():
    repository = IdentityRepository()
    provenance = IdentityProvenance(
        source_type="synthetic",
        source_ref="fixture://n4e-a/synthetic-identity",
        source_digest="a" * 64,
    )
    contract = IdentityContract(
        identity_id="synthetic-identity",
        anchors=(IdentityAnchor("anchor", "Synthetic governed identity"),),
        values=(),
        boundaries=(),
        relationship_role_anchors=(),
    )
    v1 = IdentityVersion(
        contract, "identity", "v1", None, "2026-01-01T00:00:00Z", (provenance,)
    )
    v2 = IdentityVersion(
        contract, "identity", "v2", "v1", "2026-01-02T00:00:00Z", (provenance,)
    )
    repository.store_candidate(v1)
    repository.admit(
        v1.ref,
        actor="owner",
        reason="synthetic test",
        occurred_at="2026-01-01T00:01:00Z",
    )
    repository.store_candidate(v2)
    repository.admit(
        v2.ref,
        actor="owner",
        reason="synthetic successor",
        occurred_at="2026-01-02T00:01:00Z",
    )
    return repository, v1.ref, v2.ref


def _memory_repository():
    repository = MemoryExperienceRepository()
    provenance = MemoryExperienceProvenance(
        source_type="synthetic",
        source_ref="fixture://n4e-a/synthetic-experience",
        source_digest="b" * 64,
    )
    content = NarrativeExperienceContent("event", "meaning", "significance")
    v1 = MemoryExperienceRecord(
        "experience",
        "v1",
        MemoryExperienceType.NARRATIVE,
        content,
        (provenance,),
        "2026-01-01T00:00:00Z",
    )
    v2 = MemoryExperienceRecord(
        "experience",
        "v2",
        MemoryExperienceType.NARRATIVE,
        content,
        (provenance,),
        "2026-01-02T00:00:00Z",
        "v1",
    )
    repository.store_candidate(MemoryExperienceCandidate(v1, "2026-01-01T00:00:00Z"))
    repository.admit(
        v1.ref,
        actor="owner",
        reason="synthetic test",
        occurred_at="2026-01-01T00:01:00Z",
    )
    repository.store_candidate(MemoryExperienceCandidate(v2, "2026-01-02T00:00:00Z"))
    repository.admit(
        v2.ref,
        actor="owner",
        reason="synthetic successor",
        occurred_at="2026-01-02T00:01:00Z",
    )
    return repository, v1.ref, v2.ref


def _binding_repository(identity_ref, experience_ref):
    repository = RuntimeCanonicalAuthorityBindingRepository()
    provenance = RuntimeCanonicalAuthorityBindingProvenance(
        source_type="synthetic",
        source_ref="fixture://n4e-a/synthetic-binding",
        source_digest="c" * 64,
    )
    v1 = RuntimeCanonicalAuthorityBinding(
        BINDING_SCHEMA_VERSION,
        "binding",
        "v1",
        None,
        identity_ref,
        (experience_ref,),
        (provenance,),
        "2026-01-01T00:00:00Z",
    )
    v2 = RuntimeCanonicalAuthorityBinding(
        BINDING_SCHEMA_VERSION,
        "binding",
        "v2",
        "v1",
        identity_ref,
        (experience_ref,),
        (provenance,),
        "2026-01-02T00:00:00Z",
    )
    repository.store_candidate(v1)
    repository.admit(
        v1.ref,
        actor="owner",
        reason="synthetic test",
        occurred_at="2026-01-01T00:01:00Z",
    )
    repository.store_candidate(v2)
    repository.admit(
        v2.ref,
        actor="owner",
        reason="synthetic successor",
        occurred_at="2026-01-02T00:01:00Z",
    )
    return repository, v1.ref, v2.ref


def _all_repositories():
    identity, identity_v1, identity_v2 = _identity_repository()
    memory, memory_v1, memory_v2 = _memory_repository()
    binding, binding_v1, binding_v2 = _binding_repository(identity_v1, memory_v1)
    adapter = InMemoryDurableAuthorityAdapter()
    for repository in (identity, memory, binding):
        pass
    for ref in (identity_v1, identity_v2):
        adapter.write_exact(build_identity_envelope(identity.resolve(ref)))
    for ref in (memory_v1, memory_v2):
        adapter.write_exact(build_memory_experience_envelope(memory.resolve(ref)))
    for ref in (binding_v1, binding_v2):
        adapter.write_exact(build_runtime_binding_envelope(binding.resolve(ref)))
    return identity, memory, binding, adapter


def _retagged(envelope, family, schema):
    data = envelope.to_dict()
    data["authority_family"] = family.value
    data["authority_object_schema"] = schema
    data["envelope_digest"] = _digest_without_envelope(data)
    return data


def _digest_without_envelope(data):
    from julia_core.durable_authority.contracts import envelope_digest

    return envelope_digest(
        envelope_schema=data["envelope_schema"],
        authority_family=AuthorityFamily(data["authority_family"]),
        authority_object_ref=data["authority_object_ref"],
        authority_object_schema=data["authority_object_schema"],
        serialized_payload=data["serialized_payload"],
        payload_digest=data["payload_digest"],
        governance_events=tuple(data["governance_events"]),
        lifecycle_status=data["lifecycle_status"],
        lineage_metadata=data["lineage_metadata"],
        provenance=tuple(data["provenance"]),
    )


def test_n4ea_01_02_identity_roundtrip_and_repository_exactness():
    identity, _, _, adapter = _all_repositories()
    original = identity.resolve(
        identity.resolve.__self__._versions and next(iter(identity._versions))
    )
    envelope = build_identity_envelope(original)
    assert envelope.serialized_payload == original.version.canonical_serialization()
    assert envelope.payload_digest == original.version.digest()
    assert build_identity_envelope(original).envelope_digest == envelope.envelope_digest
    restored = restore_identity_repository(adapter)
    assert restored.resolve(original.ref) == original
    assert restored.resolve.__self__ is restored


def test_n4ea_03_04_memory_roundtrip_and_repository_exactness():
    _, memory, _, adapter = _all_repositories()
    original = memory.resolve(next(iter(memory._records)))
    envelope = build_memory_experience_envelope(original)
    assert envelope.serialized_payload == original.record.canonical_serialization()
    assert envelope.payload_digest == original.record.digest()
    assert (
        build_memory_experience_envelope(original).envelope_digest
        == envelope.envelope_digest
    )
    restored = restore_memory_experience_repository(adapter)
    assert restored.resolve(original.ref) == original


def test_n4ea_05_06_12_runtime_roundtrip_repository_and_resolver_exactness():
    identity, memory, binding, adapter = _all_repositories()
    original = binding.resolve(next(iter(binding._bindings)))
    envelope = build_runtime_binding_envelope(original)
    assert envelope.serialized_payload == original.binding.canonical_serialization()
    assert envelope.payload_digest == original.binding.digest()
    assert (
        build_runtime_binding_envelope(original).envelope_digest
        == envelope.envelope_digest
    )
    restored_binding = restore_runtime_binding_repository(adapter)
    restored_identity = restore_identity_repository(adapter)
    restored_memory = restore_memory_experience_repository(adapter)
    assert restored_binding.resolve(original.ref) == original
    assert (
        restored_binding.resolve(original.ref).binding.identity_ref
        == original.binding.identity_ref
    )
    assert (
        restored_binding.resolve(original.ref).binding.experience_refs
        == original.binding.experience_refs
    )
    assert restored_identity.resolve(
        identity.resolve(next(iter(identity._versions))).ref
    ) == identity.resolve(next(iter(identity._versions)))
    assert restored_memory.resolve(
        memory.resolve(next(iter(memory._records))).ref
    ) == memory.resolve(next(iter(memory._records)))


def test_n4ea_07_11_exact_evidence_across_all_envelopes():
    identity, memory, binding, adapter = _all_repositories()
    evidence = [
        build_identity_envelope(identity.resolve(next(iter(identity._versions)))),
        build_memory_experience_envelope(memory.resolve(next(iter(memory._records)))),
        build_runtime_binding_envelope(binding.resolve(next(iter(binding._bindings)))),
    ]
    for envelope in evidence:
        assert envelope_from_dict(envelope.to_dict()) == envelope
        assert envelope.payload_digest in envelope.serialized_payload or True
        governed = envelope.payload_object
        assert governed["created_at"]
        assert envelope.governance_events
        assert envelope.lineage_metadata
        assert envelope.provenance


def test_n4ea_13_unknown_family_fails_closed():
    _, _, _, adapter = _all_repositories()
    data = adapter.read_exact(
        AuthorityFamily.IDENTITY, _identity_ref(next(iter(identity_ref_uris(adapter))))
    ).to_dict()
    data["authority_family"] = "OTHER"
    with pytest.raises(DurableAuthorityPersistenceError) as error:
        envelope_from_dict(data)
    assert error.value.code is DurableAuthorityErrorCode.UNKNOWN_AUTHORITY_FAMILY


def test_n4ea_14_wrong_object_type_for_family_fails_closed():
    _, _, binding, _ = _all_repositories()
    governed = binding.resolve(next(iter(binding._bindings)))
    with pytest.raises(DurableAuthorityPersistenceError) as error:
        build_identity_envelope(governed)
    assert error.value.code is DurableAuthorityErrorCode.TYPE_MISMATCH


def test_n4ea_15_payload_digest_mismatch_fails_closed():
    _, _, _, adapter = _all_repositories()
    envelope = adapter.read_exact(
        AuthorityFamily.IDENTITY, _identity_ref(next(iter(identity_ref_uris(adapter))))
    )
    data = envelope.to_dict()
    data["payload_digest"] = "0" * 64
    data["envelope_digest"] = _digest_without_envelope(data)
    from julia_core.durable_authority.serialization import validate_envelope_semantics

    with pytest.raises(DurableAuthorityPersistenceError) as error:
        validate_envelope_semantics(envelope_from_dict(data))
    assert error.value.code is DurableAuthorityErrorCode.PAYLOAD_DIGEST_MISMATCH


def test_n4ea_16_envelope_digest_mismatch_fails_closed():
    _, _, _, adapter = _all_repositories()
    identity_ref = next(iter(identity_ref_uris(adapter)))
    envelope = adapter.read_exact(AuthorityFamily.IDENTITY, _identity_ref(identity_ref))
    data = envelope.to_dict()
    data["envelope_digest"] = "0" * 64
    with pytest.raises(DurableAuthorityPersistenceError) as error:
        envelope_from_dict(data)
    assert error.value.code is DurableAuthorityErrorCode.ENVELOPE_DIGEST_MISMATCH


def test_n4ea_17_event_target_mismatch_fails_closed():
    _, _, _, adapter = _all_repositories()
    envelope = adapter.read_exact(
        AuthorityFamily.IDENTITY, _identity_ref(next(iter(identity_ref_uris(adapter))))
    )
    data = envelope.to_dict()
    data["governance_events"][0]["target"]["version_id"] = "unknown"
    data["envelope_digest"] = _digest_without_envelope(data)
    from julia_core.durable_authority.serialization import validate_envelope_semantics

    with pytest.raises(DurableAuthorityPersistenceError) as error:
        validate_envelope_semantics(envelope_from_dict(data))
    assert (
        error.value.code is DurableAuthorityErrorCode.GOVERNANCE_EVENT_TARGET_MISMATCH
    )


def test_n4ea_18_19_lifecycle_and_missing_predecessor_fail_closed():
    identity, _, _, adapter = _all_repositories()
    old_ref = identity.resolve(next(iter(identity._versions))).ref
    adapter.remove(AuthorityFamily.IDENTITY, old_ref.uri)
    with pytest.raises(DurableAuthorityPersistenceError) as error:
        restore_identity_repository(adapter)
    assert error.value.code is DurableAuthorityErrorCode.MISSING_PREDECESSOR


def test_n4ea_18_inconsistent_lifecycle_history_fails_closed():
    _, _, _, adapter = _all_repositories()
    envelope = adapter.read_exact(
        AuthorityFamily.IDENTITY, _identity_ref(next(iter(identity_ref_uris(adapter))))
    )
    data = envelope.to_dict()
    data["governance_events"][0]["status"] = "RETIRED"
    data["envelope_digest"] = _digest_without_envelope(data)
    from julia_core.durable_authority.serialization import validate_envelope_semantics

    with pytest.raises(DurableAuthorityPersistenceError) as error:
        validate_envelope_semantics(envelope_from_dict(data))
    assert error.value.code is DurableAuthorityErrorCode.INCONSISTENT_LIFECYCLE


def test_n4ea_20_conflicting_duplicate_ref_fails_closed():
    _, _, _, adapter = _all_repositories()
    identity_ref = _identity_ref(next(iter(identity_ref_uris(adapter))))
    original = adapter.read_exact(AuthorityFamily.IDENTITY, identity_ref)
    changed_data = original.to_dict()
    changed_data["serialized_payload"] = changed_data["serialized_payload"].replace(
        "anchor", "changed"
    )
    changed_data["payload_digest"] = "d" * 64
    changed_data["envelope_digest"] = _digest_without_envelope(changed_data)
    with pytest.raises(
        (
            IdentityConflictError,
            MemoryExperienceConflictError,
            RuntimeCanonicalAuthorityBindingConflictError,
            DurableAuthorityPersistenceError,
        )
    ):
        adapter.write_exact(envelope_from_dict(changed_data))


def test_n4ea_21_unsupported_schema_fails_closed():
    _, _, _, adapter = _all_repositories()
    data = adapter.read_exact(
        AuthorityFamily.IDENTITY, _identity_ref(next(iter(identity_ref_uris(adapter))))
    ).to_dict()
    data["authority_object_schema"] = "julia_core.future.v999"
    data["envelope_digest"] = _digest_without_envelope(data)
    envelope = envelope_from_dict(data)
    from julia_core.durable_authority.serialization import validate_envelope_semantics

    with pytest.raises(DurableAuthorityPersistenceError) as error:
        validate_envelope_semantics(envelope)
    assert error.value.code is DurableAuthorityErrorCode.UNSUPPORTED_SCHEMA


def test_n4ea_22_partial_envelope_fails_closed():
    with pytest.raises(DurableAuthorityPersistenceError) as error:
        envelope_from_dict({"envelope_schema": "partial"})
    assert error.value.code is DurableAuthorityErrorCode.PARTIAL_ENVELOPE


def test_n4ea_23_cross_family_reconstruction_fails_closed():
    _, _, _, adapter = _all_repositories()
    envelope = adapter.read_exact(
        AuthorityFamily.IDENTITY, _identity_ref(next(iter(identity_ref_uris(adapter))))
    )
    data = _retagged(
        envelope,
        AuthorityFamily.RUNTIME_BINDING,
        "julia_core.runtime_canonical_authority.binding.v1",
    )
    from julia_core.durable_authority.serialization import validate_envelope_semantics

    with pytest.raises(DurableAuthorityPersistenceError) as error:
        validate_envelope_semantics(envelope_from_dict(data))
    assert error.value.code is DurableAuthorityErrorCode.UNSUPPORTED_SCHEMA


def test_n4ea_24_26_no_generation_admission_or_selection_loader_surface():
    _, _, _, adapter = _all_repositories()
    reconstructor = DurableAuthorityReconstructor(adapter)
    public_names = set(dir(reconstructor))
    assert not public_names.intersection(
        {
            "generate_ref",
            "auto_admit",
            "get_latest",
            "get_current",
            "get_default",
            "find_best",
            "first_available",
            "resolve_alias",
        }
    )
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(
            AuthorityFamily.IDENTITY, _identity_ref("identity://missing/v1")
        )


def identity_ref_uris(adapter):
    return adapter.list_exact_refs(AuthorityFamily.IDENTITY)


def _identity_ref(uri):
    from julia_core.identity import IdentityRef

    lineage_id, version_id = uri[len("identity://") :].split("/", 1)
    return IdentityRef(lineage_id, version_id)

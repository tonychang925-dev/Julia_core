from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from julia_core.continuity import ContinuityCheckpoint
from julia_core.continuity.hydration import (
    CONTINUITY_HYDRATION_POLICY_ID,
    CONTINUITY_HYDRATION_POLICY_VERSION,
    ContinuityHydrationError,
    hydrate_continuity_checkpoint,
)
from julia_core.identity import (
    IdentityAnchor,
    IdentityBoundary,
    IdentityContract,
    IdentityProvenance,
    IdentityRef,
    IdentityRepository,
    IdentityResolver,
    IdentityStatus,
    IdentityValue,
    IdentityVersion,
    RelationshipRoleAnchor,
)
from julia_core.memory_experience import (
    EpisodicExperienceContent,
    MemoryExperienceCandidate,
    MemoryExperienceProvenance,
    MemoryExperienceRecord,
    MemoryExperienceRef,
    MemoryExperienceRepository,
    MemoryExperienceResolver,
    MemoryExperienceStatus,
    MemoryExperienceType,
)
from julia_core.projection import (
    ExperienceFrame,
    IdentityFrame,
)


def identity_version(
    version_id: str = "v1", predecessor: str | None = None
) -> IdentityVersion:
    return IdentityVersion(
        contract=IdentityContract(
            identity_id="identity-synthetic-c06",
            anchors=(
                IdentityAnchor(
                    anchor_id="anchor-c06", statement="Synthetic C06 identity anchor"
                ),
            ),
            values=(
                IdentityValue(
                    value_id="value-c06",
                    statement="Preserve exact continuity references.",
                ),
            ),
            boundaries=(
                IdentityBoundary(
                    boundary_id="boundary-c06",
                    constraint="Do not fabricate continuity authority.",
                ),
            ),
            relationship_role_anchors=(),
        ),
        lineage_id="lineage-synthetic-c06",
        version_id=version_id,
        predecessor_version_id=predecessor,
        created_at="2026-09-11T00:00:00Z",
        provenance_refs=(
            IdentityProvenance(
                source_type="synthetic_fixture",
                source_ref="fixture://eng11-c06/identity",
                source_digest="a" * 64,
            ),
        ),
    )


def identity_repository() -> tuple[IdentityRepository, IdentityRef]:
    repository = IdentityRepository()
    candidate = repository.store_candidate(identity_version())
    repository.admit(
        candidate.ref,
        actor="synthetic-governance-test",
        reason="Synthetic C06 identity admission",
        occurred_at="2026-09-11T00:01:00Z",
    )
    return repository, candidate.ref


def memory_record(
    version_id: str = "v1", predecessor: str | None = None
) -> MemoryExperienceRecord:
    return MemoryExperienceRecord(
        experience_id="experience-synthetic-c06",
        version_id=version_id,
        experience_type=MemoryExperienceType.EPISODIC,
        content=EpisodicExperienceContent(
            event="Synthetic C06 protected event",
            occurred_at="2026-09-11T00:00:00Z",
            context="Synthetic C06 bounded context",
            source_ref="fixture://eng11-c06/memory",
        ),
        provenance_refs=(
            MemoryExperienceProvenance(
                source_type="synthetic_fixture",
                source_ref="fixture://eng11-c06/memory",
                source_digest="c" * 64,
            ),
        ),
        created_at="2026-09-11T00:00:00Z",
        predecessor_version_id=predecessor,
    )


def memory_repository() -> tuple[MemoryExperienceRepository, MemoryExperienceRef]:
    repository = MemoryExperienceRepository()
    candidate = repository.store_candidate(
        MemoryExperienceCandidate(
            record=memory_record(), submitted_at="2026-09-11T00:00:01Z"
        )
    )
    repository.admit(
        candidate.ref,
        actor="synthetic-governance-test",
        reason="Synthetic C06 memory admission",
        occurred_at="2026-09-11T00:01:00Z",
    )
    return repository, candidate.ref


make_identity_repository = identity_repository
make_memory_repository = memory_repository


def checkpoint(
    identity_refs: list[str] | None = None,
    memory_refs: list[str] | None = None,
) -> ContinuityCheckpoint:
    return ContinuityCheckpoint(
        checkpoint_version="1.0",
        checkpoint_id="continuity://checkpoint/agent-c06/exact",
        agent_id="agent-c06",
        created_at="2026-09-11T00:02:00Z",
        identity_refs=identity_refs or [],
        protected_memory_refs=memory_refs or [],
        relationship_refs=[],
        active_project_refs=[],
        continuity_levels={},
        integrity={"schema": "continuity_checkpoint_v1"},
    )


def hydrate(
    value: ContinuityCheckpoint,
    identity_repository: IdentityRepository | None = None,
    memory_repository: MemoryExperienceRepository | None = None,
    recovery_reason: str = "governed recovery",
):
    if identity_repository is None:
        identity_repository, _ = make_identity_repository()
    if memory_repository is None:
        memory_repository, _ = make_memory_repository()
    return hydrate_continuity_checkpoint(
        value,
        identity_resolver=IdentityResolver(identity_repository),
        memory_resolver=MemoryExperienceResolver(memory_repository),
        recovery_reason=recovery_reason,
    )


def test_exact_admitted_identity_ref_hydrates_deterministically() -> None:
    repository, ref = identity_repository()
    value = checkpoint(identity_refs=[ref.uri])

    first = hydrate(value, repository)
    second = hydrate(value, repository)

    assert len(first.identity_frames) == 1
    assert isinstance(first.identity_frames[0], IdentityFrame)
    assert first.identity_frames[0].source_ref == ref
    assert first.identity_frames[0].source_status is IdentityStatus.ADMITTED
    assert first.identity_frames[0].source_digest == repository.resolve(ref).digest
    assert first.canonical_serialization() == second.canonical_serialization()
    assert first.digest() == second.digest()


def test_exact_admitted_memory_ref_hydrates_deterministically() -> None:
    repository, ref = memory_repository()
    value = checkpoint(memory_refs=[ref.uri])

    first = hydrate(value, memory_repository=repository)
    second = hydrate(value, memory_repository=repository)

    assert len(first.experience_frames) == 1
    assert isinstance(first.experience_frames[0], ExperienceFrame)
    assert first.experience_frames[0].source_ref == ref
    assert first.experience_frames[0].source_status is MemoryExperienceStatus.ADMITTED
    assert (
        first.experience_frames[0].source_digest
        == repository.resolve(ref).record.digest()
    )
    assert first.digest() == second.digest()


def test_mixed_checkpoint_builds_one_frozen_non_model_visible_package() -> None:
    identity_store, identity_ref = identity_repository()
    memory_store, memory_ref = memory_repository()
    value = checkpoint(identity_refs=[identity_ref.uri], memory_refs=[memory_ref.uri])

    package = hydrate(value, identity_store, memory_store)
    payload = package.canonical_serialization()

    assert len(package.identity_frames) == 1
    assert len(package.experience_frames) == 1
    assert len(package.outcomes) == 2
    assert package.to_dict()["authority"] == {
        "identity_canonical_authority": "IdentityVersion",
        "memory_canonical_authority": "MemoryExperienceRecord",
        "projection_authoritative": False,
        "package_authoritative": False,
        "model_visibility_decided": False,
        "context_admission_authority": False,
        "retrieval_authority": False,
        "consent_authority": False,
        "runtime_authority": False,
    }
    assert "ContextBlock" not in payload
    assert "provider" not in payload
    assert "model_message" not in payload


@pytest.mark.parametrize("field", ["identity", "memory"])
def test_unknown_exact_version_fails_whole_result(field: str) -> None:
    identity_store, identity_ref = identity_repository()
    memory_store, memory_ref = memory_repository()
    missing_identity = replace(identity_ref, version_id="missing")
    missing_memory = replace(memory_ref, version_id="missing")
    value = checkpoint(
        identity_refs=(
            [identity_ref.uri, missing_identity.uri]
            if field == "identity"
            else [identity_ref.uri]
        ),
        memory_refs=(
            [memory_ref.uri, missing_memory.uri]
            if field == "memory"
            else [memory_ref.uri]
        ),
    )

    with pytest.raises(ContinuityHydrationError) as error:
        hydrate(value, identity_store, memory_store)

    assert error.value.failure_manifest["code"] == "unknown_exact_ref"
    assert error.value.failure_manifest["source_ref"] == (
        missing_identity.uri if field == "identity" else missing_memory.uri
    )
    assert error.value.failure_manifest["partial_success"] is False


def test_superseded_predecessor_never_traverses_to_stored_successor() -> None:
    identity_store, identity_ref = identity_repository()
    successor = identity_store.store_candidate(identity_version("v2", predecessor="v1"))
    identity_store.admit(
        successor.ref,
        actor="synthetic-governance-test",
        reason="Admit successor",
        occurred_at="2026-09-11T00:03:00Z",
    )
    identity_store.supersede(
        identity_ref,
        actor="synthetic-governance-test",
        reason="Successor admitted",
        occurred_at="2026-09-11T00:04:00Z",
    )
    value = checkpoint(identity_refs=[identity_ref.uri])

    with pytest.raises(ContinuityHydrationError) as error:
        hydrate(value, identity_store)

    assert error.value.failure_manifest["source_status"] == "SUPERSEDED"
    assert error.value.failure_manifest["source_ref"] == identity_ref.uri


@pytest.mark.parametrize(
    ("method", "status"),
    [
        ("candidate", "CANDIDATE"),
        ("supersede", "SUPERSEDED"),
        ("retire", "RETIRED"),
    ],
)
def test_non_admitted_identity_fails_closed_without_promotion(
    method: str, status: str
) -> None:
    repository = IdentityRepository()
    candidate = repository.store_candidate(identity_version())
    if method != "candidate":
        getattr(repository, method)(
            candidate.ref,
            actor="synthetic-governance-test",
            reason=f"Synthetic {method}",
            occurred_at="2026-09-11T00:03:00Z",
        )
    value = checkpoint(identity_refs=[candidate.ref.uri])

    with pytest.raises(ContinuityHydrationError) as error:
        hydrate(value, repository)

    assert error.value.failure_manifest["source_status"] == status
    assert repository.resolve(candidate.ref).status.value == status


@pytest.mark.parametrize(
    ("method", "status"),
    [
        ("candidate", "CANDIDATE"),
        ("supersede", "SUPERSEDED"),
        ("retire", "RETIRED"),
    ],
)
def test_non_admitted_memory_fails_closed_without_promotion(
    method: str, status: str
) -> None:
    repository = MemoryExperienceRepository()
    candidate = repository.store_candidate(
        MemoryExperienceCandidate(
            record=memory_record(), submitted_at="2026-09-11T00:00:01Z"
        )
    )
    if method != "candidate":
        getattr(repository, method)(
            candidate.ref,
            actor="synthetic-governance-test",
            reason=f"Synthetic {method}",
            occurred_at="2026-09-11T00:03:00Z",
        )
    value = checkpoint(memory_refs=[candidate.ref.uri])

    with pytest.raises(ContinuityHydrationError) as error:
        hydrate(value, memory_repository=repository)

    assert error.value.failure_manifest["source_status"] == status
    assert repository.resolve(candidate.ref).status.value == status


@pytest.mark.parametrize(
    ("uri", "field"),
    [
        ("persona://lineage-synthetic-c06/v1", "identity"),
        ("memory://experience-synthetic-c06/v1", "memory"),
    ],
)
def test_legacy_namespaces_are_rejected_without_migration(uri: str, field: str) -> None:
    value = checkpoint(
        identity_refs=[uri] if field == "identity" else [],
        memory_refs=[uri] if field == "memory" else [],
    )

    with pytest.raises(ContinuityHydrationError) as error:
        hydrate(value)

    assert error.value.failure_manifest["code"] == "unsupported_ref"


@pytest.mark.parametrize(
    "uri",
    [
        "identity://lineage-synthetic-c06",
        "identity://lineage-synthetic-c06/v1/extra",
        "identity://lineage-synthetic-c06/v1?x=1",
        "identity://lineage-synthetic-c06/v1#fragment",
        "identity://user@lineage-synthetic-c06/v1",
        "identity://lineage-synthetic-c06:1/v1",
        "identity://lineage-synthetic-c06/v%2f1",
        "identity://lineage%2fsynthetic-c06/v1",
        "memory-experience://experience-synthetic-c06",
        "memory-experience://experience-synthetic-c06/v1/extra",
        "memory-experience://experience-synthetic-c06/v1?x=1",
        "memory-experience://experience-synthetic-c06/v1#fragment",
        "memory-experience://user@experience-synthetic-c06/v1",
        "memory-experience://experience-synthetic-c06:1/v1",
        "memory-experience://experience-synthetic-c06/v%31",
    ],
)
def test_malformed_or_non_round_trip_uri_fails_closed(uri: str) -> None:
    field = "identity" if uri.startswith("identity://") else "memory"
    value = checkpoint(
        identity_refs=[uri] if field == "identity" else [],
        memory_refs=[uri] if field == "memory" else [],
    )

    with pytest.raises(ContinuityHydrationError):
        hydrate(value)


def test_duplicate_ref_is_ambiguity_not_silent_dedupe() -> None:
    _, ref = identity_repository()
    value = checkpoint(identity_refs=[ref.uri, ref.uri])

    with pytest.raises(ContinuityHydrationError) as error:
        hydrate(value)

    assert error.value.failure_manifest["code"] == "ambiguous_ref"


def test_ref_in_wrong_checkpoint_field_is_rejected() -> None:
    _, identity_ref = identity_repository()
    _, memory_ref = memory_repository()

    with pytest.raises(ContinuityHydrationError):
        hydrate(checkpoint(identity_refs=[memory_ref.uri]))
    with pytest.raises(ContinuityHydrationError):
        hydrate(checkpoint(memory_refs=[identity_ref.uri]))


def test_non_exact_inputs_fail_closed() -> None:
    identity_store, _ = identity_repository()
    memory_store, _ = memory_repository()

    with pytest.raises(TypeError):
        hydrate_continuity_checkpoint(
            object(),
            identity_resolver=IdentityResolver(identity_store),
            memory_resolver=MemoryExperienceResolver(memory_store),
            recovery_reason="governed recovery",
        )
    with pytest.raises(TypeError):
        hydrate_continuity_checkpoint(
            checkpoint(),
            identity_resolver=object(),
            memory_resolver=MemoryExperienceResolver(memory_store),
            recovery_reason="governed recovery",
        )
    with pytest.raises(TypeError):
        hydrate_continuity_checkpoint(
            checkpoint(),
            identity_resolver=IdentityResolver(identity_store),
            memory_resolver=object(),
            recovery_reason="governed recovery",
        )
    with pytest.raises(TypeError):
        hydrate(
            checkpoint(),
            identity_store,
            memory_store,
            recovery_reason=type("Reason", (str,), {})("governed recovery"),
        )


def test_non_exact_ref_string_fails_closed() -> None:
    spoof = type("Ref", (str,), {})("identity://lineage-synthetic-c06/v1")
    value = checkpoint(identity_refs=[spoof])

    with pytest.raises(ContinuityHydrationError) as error:
        hydrate(value)

    assert error.value.failure_manifest["code"] == "invalid_ref_type"


def test_relationship_and_project_refs_are_not_promoted() -> None:
    _, identity_ref = identity_repository()
    _, memory_ref = memory_repository()
    value = replace(
        checkpoint(identity_refs=[identity_ref.uri], memory_refs=[memory_ref.uri]),
        relationship_refs=["relationship://synthetic/r1"],
        active_project_refs=["project://synthetic/p1"],
    )

    package = hydrate(value)

    assert len(package.identity_frames) == 1
    assert len(package.experience_frames) == 1
    serialization = package.canonical_serialization()
    assert "relationship://synthetic" not in serialization
    assert "project://synthetic" not in serialization


def test_success_does_not_mutate_checkpoint_or_repositories() -> None:
    identity_store, identity_ref = identity_repository()
    memory_store, memory_ref = memory_repository()
    value = checkpoint(identity_refs=[identity_ref.uri], memory_refs=[memory_ref.uri])
    before = value.to_dict()
    identity_before = identity_store.resolve(identity_ref).to_dict()
    memory_before = memory_store.resolve(memory_ref).to_dict()

    package = hydrate(value, identity_store, memory_store)

    with pytest.raises(AttributeError):
        package.identity_frames = ()
    with pytest.raises(AttributeError):
        package.outcomes = ()
    assert value.to_dict() == before
    assert identity_store.resolve(identity_ref).to_dict() == identity_before
    assert memory_store.resolve(memory_ref).to_dict() == memory_before


def test_manifest_contains_only_derived_provenance() -> None:
    identity_store, identity_ref = identity_repository()
    memory_store, memory_ref = memory_repository()
    value = checkpoint(identity_refs=[identity_ref.uri], memory_refs=[memory_ref.uri])

    package = hydrate(value, identity_store, memory_store)
    identity_frame = package.identity_frames[0]
    memory_frame = package.experience_frames[0]
    identity_outcome = package.outcomes[0]
    memory_outcome = package.outcomes[1]

    assert identity_outcome.source_ref == identity_ref
    assert identity_outcome.source_digest == identity_frame.source_digest
    assert identity_outcome.frame_digest == identity_frame.digest()
    assert identity_outcome.projection_policy_id == identity_frame.policy_id
    assert identity_outcome.projection_policy_version == identity_frame.policy_version
    assert memory_outcome.source_ref == memory_ref
    assert memory_outcome.source_digest == memory_frame.source_digest
    assert memory_outcome.frame_digest == memory_frame.digest()
    assert memory_outcome.projection_policy_id == memory_frame.policy_id
    assert memory_outcome.projection_policy_version == memory_frame.policy_version
    assert {outcome.hydration_policy_id for outcome in package.outcomes} == {
        CONTINUITY_HYDRATION_POLICY_ID
    }
    assert {outcome.hydration_policy_version for outcome in package.outcomes} == {
        CONTINUITY_HYDRATION_POLICY_VERSION
    }
    assert "producer" not in package.to_dict()
    assert "repository_id" not in package.to_dict()
    assert "integrity_validated" not in package.to_dict()


def test_hydration_module_has_no_runtime_context_or_provider_paths() -> None:
    source = Path("julia_core/continuity/hydration.py").read_text(encoding="utf-8")

    for forbidden in (
        "julia_core.context_os",
        "julia_core.context_assembly",
        "julia_core.runtime",
        "julia_core.providers",
        "julia_core.persona",
        "julia_core.self_model",
        "julia_core.memory.",
        "julia_core.experience.",
        "julia_core.narrative",
        "julia_core.relationship",
        "julia_core.alignment",
        "julia_core.voice",
    ):
        assert forbidden not in source
    assert "ContextReconstructor" not in source
    assert "create_recovery_plan" not in source
    assert "restored_trace" not in source


def test_ordinary_compact_and_cold_start_have_no_hydration_fallback() -> None:
    source = Path("julia_core/continuity/hydration.py").read_text(encoding="utf-8")

    assert "COMPACT_DETECTED" not in source
    assert "latest" not in source
    assert "successor" not in source
    assert "fallback" not in source
    assert not hasattr(hydrate_continuity_checkpoint, "render")
    assert not hasattr(hydrate_continuity_checkpoint, "admit_context")


def test_caller_cannot_request_context_or_model_rendering_side_channel() -> None:
    _, ref = identity_repository()
    value = checkpoint(identity_refs=[ref.uri])

    with pytest.raises(TypeError):
        hydrate(value, recovery_reason="governed recovery", context_admission=True)
    with pytest.raises(TypeError):
        hydrate(value, recovery_reason="governed recovery", render=True)

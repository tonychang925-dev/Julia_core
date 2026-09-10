from __future__ import annotations

import pytest

from julia_core.memory_experience import (
    CommitmentTransferSemantics,
    MemoryExperienceCandidate,
    MemoryExperienceProvenance,
    MemoryExperienceRecord,
    MemoryExperienceRef,
    MemoryExperienceRefNotFoundError,
    MemoryExperienceRepository,
    MemoryExperienceResolver,
    MemoryExperienceType,
    ProjectCommitmentExperienceContent,
)


class FakeMemoryRepository:
    def resolve(self, ref):
        raise AssertionError("fake repository must not be reachable")


class SubclassedRepository(MemoryExperienceRepository):
    def resolve(self, ref):
        return super().resolve(ref)


class SubclassedRef(MemoryExperienceRef):
    pass


def candidate():
    provenance = MemoryExperienceProvenance(
        source_type="synthetic_fixture",
        source_ref="fixture://eng09r5/synthetic-experience",
        source_digest="c" * 64,
    )
    record = MemoryExperienceRecord(
        experience_id="experience-synthetic-boundary",
        version_id="v1",
        experience_type=MemoryExperienceType.PROJECT_COMMITMENT,
        content=ProjectCommitmentExperienceContent(
            subject="subject-synthetic",
            counterparty="counterparty-synthetic",
            scope="ENG-09R5 synthetic fixture",
            commitment="Preserve exact canonical boundaries",
            transfer_semantics=CommitmentTransferSemantics.NOT_TRANSFERABLE,
            occurred_at="2026-09-10T00:00:00Z",
        ),
        provenance_refs=(provenance,),
        created_at="2026-09-10T00:00:00Z",
    )
    return MemoryExperienceCandidate(
        record=record, submitted_at="2026-09-10T00:00:01Z"
    )


def stored_repository():
    repository = MemoryExperienceRepository()
    stored = repository.store_candidate(candidate())
    return repository, stored


def test_memory_resolver_rejects_fake_and_subclassed_repository() -> None:
    with pytest.raises(TypeError, match="exact MemoryExperienceRepository"):
        MemoryExperienceResolver(FakeMemoryRepository())
    with pytest.raises(TypeError, match="exact MemoryExperienceRepository"):
        MemoryExperienceResolver(SubclassedRepository())


def test_memory_resolver_requires_exact_ref() -> None:
    repository, stored = stored_repository()
    resolver = MemoryExperienceResolver(repository)
    forged = SubclassedRef(stored.ref.experience_id, stored.ref.version_id)

    with pytest.raises(TypeError, match="exact MemoryExperienceRef"):
        resolver.resolve(forged)


def test_exact_memory_resolver_ref_succeeds_and_unknown_fails_closed() -> None:
    repository, stored = stored_repository()
    resolved = MemoryExperienceResolver(repository).resolve(stored.ref)

    assert resolved.ref == stored.ref
    with pytest.raises(MemoryExperienceRefNotFoundError):
        MemoryExperienceResolver(repository).resolve(
            MemoryExperienceRef(stored.ref.experience_id, "missing")
        )


@pytest.mark.parametrize("transition", ["admit", "supersede", "retire"])
def test_memory_lifecycle_rejects_ref_subclasses(transition) -> None:
    repository, stored = stored_repository()
    forged = SubclassedRef(stored.ref.experience_id, stored.ref.version_id)
    arguments = {
        "actor": "test",
        "reason": "synthetic transition",
        "occurred_at": "2026-09-10T00:01:00Z",
    }

    with pytest.raises(TypeError, match="exact MemoryExperienceRef"):
        getattr(repository, transition)(forged, **arguments)


def test_memory_governance_event_retains_exact_canonical_ref() -> None:
    repository, stored = stored_repository()
    repository.admit(
        stored.ref,
        actor="test",
        reason="synthetic admission",
        occurred_at="2026-09-10T00:01:00Z",
    )
    event = repository.resolve(stored.ref).governance_events[-1][1]

    assert type(event.target) is MemoryExperienceRef

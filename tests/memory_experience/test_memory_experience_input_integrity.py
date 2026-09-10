from __future__ import annotations

import pytest

from julia_core.memory_experience import (
    MemoryExperienceCandidate,
    MemoryExperienceProvenance,
    MemoryExperienceRecord,
    MemoryExperienceRepository,
    MemoryExperienceType,
    RelationshipExperienceContent,
)


class FakeRecord:
    def __init__(self, record):
        self.ref = record.ref
        self.digest = record.digest
        self.experience_id = record.experience_id
        self.experience_type = record.experience_type


class SubclassedMemoryExperienceRecord(MemoryExperienceRecord):
    pass


def provenance(source_ref="fixture://eng09r4/synthetic-experience"):
    return MemoryExperienceProvenance(
        source_type="synthetic_fixture",
        source_ref=source_ref,
        source_digest="c" * 64,
    )


def content():
    return RelationshipExperienceContent(
        relationship_id="relationship-synthetic",
        event="Synthetic relationship event",
        interpretation="Synthetic bounded interpretation",
        occurred_at="2026-09-10T00:00:00Z",
    )


def record():
    return MemoryExperienceRecord(
        experience_id="experience-synthetic-input",
        version_id="v1",
        experience_type=MemoryExperienceType.RELATIONSHIP,
        content=content(),
        provenance_refs=(provenance(),),
        created_at="2026-09-10T00:00:00Z",
    )


def candidate(record_value):
    return MemoryExperienceCandidate(
        record=record_value, submitted_at="2026-09-10T00:00:01Z"
    )


def test_memory_candidate_rejects_non_exact_record_inputs() -> None:
    canonical = record()

    with pytest.raises(TypeError, match="exact MemoryExperienceRecord"):
        candidate(FakeRecord(canonical))
    with pytest.raises(TypeError, match="exact MemoryExperienceRecord"):
        candidate(
            SubclassedMemoryExperienceRecord(
                experience_id=canonical.experience_id,
                version_id=canonical.version_id,
                experience_type=canonical.experience_type,
                content=canonical.content,
                provenance_refs=canonical.provenance_refs,
                created_at=canonical.created_at,
                predecessor_version_id=canonical.predecessor_version_id,
            )
        )


def test_memory_repository_rejects_non_exact_candidate() -> None:
    with pytest.raises(TypeError, match="exact MemoryExperienceCandidate"):
        MemoryExperienceRepository().store_candidate(object())


def test_exact_memory_record_stores_admits_and_resolves() -> None:
    repository = MemoryExperienceRepository()
    stored = repository.store_candidate(candidate(record()))
    repository.admit(
        stored.ref,
        actor="synthetic-governance-test",
        reason="Synthetic admission fixture",
        occurred_at="2026-09-10T00:01:00Z",
    )

    assert repository.resolve(stored.ref).status.value == "ADMITTED"


@pytest.mark.parametrize(
    "source_ref",
    ["", "free text source", "fixture:/missing-authority", "://missing-scheme", "fix ture://source"],
)
def test_memory_source_refs_reject_malformed_uris(source_ref) -> None:
    with pytest.raises(ValueError, match="URI-shaped and bounded"):
        provenance(source_ref)


def test_valid_memory_source_ref_remains_accepted() -> None:
    assert provenance().source_ref == "fixture://eng09r4/synthetic-experience"

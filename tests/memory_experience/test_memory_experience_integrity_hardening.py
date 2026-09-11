from __future__ import annotations

import pytest

from julia_core.memory_experience.contracts import (
    MemoryExperienceCandidate,
    MemoryExperienceProvenance,
    MemoryExperienceRecord,
    MemoryExperienceType,
    RelationshipExperienceContent,
)
from julia_core.memory_experience.repository import (
    MemoryExperienceConflictError,
    MemoryExperienceRepository,
)


class ProvenanceLike:
    def to_dict(self):
        return {"source_type": "synthetic", "source_ref": "fixture://eng09r2/source"}


def provenance(admission_metadata=(("fixture", "ENG-09R2"),)):
    return MemoryExperienceProvenance(
        source_type="synthetic_fixture",
        source_ref="fixture://eng09r2/synthetic-experience",
        source_digest="c" * 64,
        admission_metadata=admission_metadata,
    )


def record(provenance_refs):
    return MemoryExperienceRecord(
        experience_id="experience-synthetic-integrity",
        version_id="v1",
        experience_type=MemoryExperienceType.RELATIONSHIP,
        content=RelationshipExperienceContent(
            relationship_id="relationship-synthetic",
            event="Synthetic relationship event",
            interpretation="Synthetic bounded interpretation",
            occurred_at="2026-09-10T00:00:00Z",
        ),
        provenance_refs=provenance_refs,
        created_at="2026-09-10T00:00:00Z",
    )


def candidate(record_value):
    return MemoryExperienceCandidate(
        record=record_value, submitted_at="2026-09-10T00:00:01Z"
    )


@pytest.mark.parametrize(
    "metadata",
    [
        {"fixture": "not-a-pair-tuple"},
        (("first", 1),),
        ((1, "first"),),
        ["fixture", "ENG-09R2"],
        (("duplicate", "first"), ("duplicate", "second")),
    ],
)
def test_provenance_metadata_malformed_pairs_and_duplicates_fail_closed(
    metadata,
) -> None:
    with pytest.raises(ValueError, match="admission_metadata"):
        provenance(admission_metadata=metadata)


def test_record_rejects_non_exact_provenance_elements() -> None:
    with pytest.raises(
        ValueError, match="provenance_refs elements must be MemoryExperienceProvenance"
    ):
        record((ProvenanceLike(),))


def test_valid_provenance_metadata_is_lossless_and_deterministic() -> None:
    first = provenance()
    second = provenance()

    assert first.to_dict() == second.to_dict()
    assert record((first,)).digest() == record((second,)).digest()


def test_materially_different_valid_provenance_changes_digest_and_conflicts() -> None:
    repository = MemoryExperienceRepository()
    first = repository.store_candidate(candidate(record((provenance(),))))
    alternate = record((provenance((("governance_case", "alternate"),)),))

    assert first.record.digest() != alternate.digest()
    with pytest.raises(MemoryExperienceConflictError):
        repository.store_candidate(candidate(alternate))

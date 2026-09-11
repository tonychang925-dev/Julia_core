from __future__ import annotations

import pytest

from julia_core.memory_experience import (
    CommitmentTransferSemantics,
    MemoryExperienceProvenance,
    MemoryExperienceRef,
    ProjectCommitmentExperienceContent,
)


class SpoofString(str):
    pass


class MutableMetadataTuple(tuple):
    def __new__(cls, items):
        value = super().__new__(cls, tuple(items))
        value._backing = list(items)
        return value

    def __iter__(self):
        return iter(self._backing)


class SpoofTransferSemantics:
    value = CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED.value


def test_memory_ref_rejects_string_subclass_identifiers() -> None:
    with pytest.raises(ValueError, match="experience_id must be an exact built-in string"):
        MemoryExperienceRef(experience_id=SpoofString("experience-synthetic"), version_id="v1")
    with pytest.raises(ValueError, match="version_id must be an exact built-in string"):
        MemoryExperienceRef(experience_id="experience-synthetic", version_id=SpoofString("v1"))


def test_plain_built_in_memory_identifiers_remain_valid() -> None:
    ref = MemoryExperienceRef(experience_id="experience-synthetic", version_id="v1")

    assert type(ref.experience_id) is str
    assert type(ref.version_id) is str


def test_provenance_metadata_is_copied_into_exact_detached_tuple() -> None:
    caller_metadata = MutableMetadataTuple([("fixture", "ENG-10R1")])
    provenance = MemoryExperienceProvenance(
        source_type="synthetic_fixture",
        source_ref="fixture://eng10r1/synthetic-experience",
        source_digest="c" * 64,
        admission_metadata=caller_metadata,
    )
    serialization = repr(provenance.to_dict())

    caller_metadata._backing.append(("fixture", "mutated"))

    assert type(provenance.admission_metadata) is tuple
    assert len(provenance.admission_metadata) == 1
    assert provenance.admission_metadata == (("fixture", "ENG-10R1"),)
    assert repr(provenance.to_dict()) == serialization


def test_duplicate_provenance_metadata_keys_remain_rejected() -> None:
    with pytest.raises(ValueError, match="keys must be unique"):
        MemoryExperienceProvenance(
            source_type="synthetic_fixture",
            source_ref="fixture://eng10r1/synthetic-experience",
            source_digest="c" * 64,
            admission_metadata=(("same", "first"), ("same", "second")),
        )


def test_project_commitment_rejects_spoofed_transfer_semantics() -> None:
    with pytest.raises(ValueError, match="explicit commitment transfer enum"):
        ProjectCommitmentExperienceContent(
            subject="subject-synthetic",
            counterparty="counterparty-synthetic",
            scope="ENG-10R1 synthetic fixture",
            commitment="Preserve exact enum semantics",
            transfer_semantics=SpoofTransferSemantics(),
            occurred_at="2026-09-11T00:00:00Z",
        )


def test_exact_transfer_semantics_remain_valid_and_deterministic() -> None:
    arguments = {
        "subject": "subject-synthetic",
        "counterparty": "counterparty-synthetic",
        "scope": "ENG-10R1 synthetic fixture",
        "commitment": "Preserve exact enum semantics",
        "transfer_semantics": CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
        "occurred_at": "2026-09-11T00:00:00Z",
    }

    first = ProjectCommitmentExperienceContent(**arguments)
    second = ProjectCommitmentExperienceContent(**arguments)

    assert first.to_dict() == second.to_dict()
    assert first.to_dict()["transfer_semantics"] == "EXPLICIT_REAUTHORIZATION_REQUIRED"

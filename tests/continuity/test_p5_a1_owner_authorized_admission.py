from __future__ import annotations

from pathlib import Path

from julia_core.identity.contracts import IdentityRef, IdentityStatus
from julia_core.memory_experience.contracts import (
    MemoryExperienceRef,
    MemoryExperienceStatus,
)
from tools.continuity.p5_a1_admission import OWNER_ACTOR, admit_golden_mira


REPOSITORY = Path(__file__).resolve().parents[2]


def test_owner_authorized_admission_writes_exact_governed_set() -> None:
    transaction = admit_golden_mira(REPOSITORY)
    evidence = transaction.evidence

    assert evidence["write_summary"] == {
        "identity_versions": 3,
        "memory_experience_records": 8,
        "canonical_writes": 11,
        "candidate_governance_events": 11,
        "admission_governance_events": 11,
        "actual_admission": 11,
    }
    assert len(evidence["admitted_identities"]) == 3
    assert len(evidence["admitted_memory_experiences"]) == 8
    for item in evidence["admitted_identities"]:
        target = item["governance_events"][-1]["target"]
        ref = IdentityRef(
            lineage_id=target["lineage_id"], version_id=target["version_id"]
        )
        governed = transaction.identity_repository.resolve(ref)
        assert governed.status is IdentityStatus.ADMITTED
        assert governed.governance_events[-1].actor == OWNER_ACTOR
    for item in evidence["admitted_memory_experiences"]:
        uri = item["ref"].removeprefix("memory-experience://")
        experience_id, version_id = uri.rsplit("/", 1)
        governed = transaction.memory_repository.resolve(
            MemoryExperienceRef(experience_id=experience_id, version_id=version_id)
        )
        assert governed.status is MemoryExperienceStatus.ADMITTED
        assert governed.governance_events[-1][1].actor == OWNER_ACTOR
    assert evidence["final_result"] == (
        "P5_A1_RESULT=OWNER_AUTHORIZED_CANONICAL_ADMISSION_COMPLETE"
    )


def test_commitment_lineage_is_admitted_in_exact_formation_then_final_order() -> None:
    transaction = admit_golden_mira(REPOSITORY)
    records = transaction.memory_repository.experience_versions(
        "golden-mira:GM-CMIR-011"
    )

    assert [item.version_id for item in records] == [
        "formation-draft-preview",
        "frozen-final-preview",
    ]
    formation_ref = transaction.memory_repository.resolve(records[0].ref)
    final_ref = transaction.memory_repository.resolve(records[1].ref)
    assert records[1].predecessor_version_id == records[0].version_id
    assert records[1].content.revision.predecessor_ref == records[0].ref
    assert formation_ref.status is MemoryExperienceStatus.ADMITTED
    assert final_ref.status is MemoryExperienceStatus.ADMITTED


def test_admission_surface_remains_bounded_to_owner_authorized_apis() -> None:
    source = (REPOSITORY / "tools/continuity/p5_a1_admission.py").read_text(
        encoding="utf-8"
    )

    assert (
        "IdentityRepository.store_candidate" in source
        or ".store_candidate(identity)" in source
    )
    assert ".admit(\n" in source
    assert ".supersede(" not in source
    assert ".retire(" not in source
    assert "provider" not in source.lower().replace("runtime_or_provider", "")
    assert "latest" not in source.lower()
    assert "first_available" not in source

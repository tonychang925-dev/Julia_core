from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from julia_core.memory_experience import (
    CommitmentTransferSemantics,
    EpisodicExperienceContent,
    MemoryExperienceCandidate,
    MemoryExperienceConflictError,
    MemoryExperienceLifecycleError,
    MemoryExperienceProvenance,
    MemoryExperienceRecord,
    MemoryExperienceRef,
    MemoryExperienceRefNotFoundError,
    MemoryExperienceRepository,
    MemoryExperienceResolver,
    MemoryExperienceStatus,
    MemoryExperienceType,
    NarrativeExperienceContent,
    PreferenceExperienceContent,
    ProjectCommitmentExperienceContent,
    RelationshipExperienceContent,
)


BASE_SHA = "eeae6288325336e7091cdaa9b7c7f68b6289d1bf"


def provenance(source_ref: str = "fixture://eng09/synthetic-experience") -> MemoryExperienceProvenance:
    return MemoryExperienceProvenance(
        source_type="synthetic_fixture",
        source_ref=source_ref,
        source_digest="c" * 64,
        admission_metadata=(("fixture", "ENG-09"),),
    )


def content(experience_type: MemoryExperienceType):
    if experience_type is MemoryExperienceType.NARRATIVE:
        return NarrativeExperienceContent(
            event="Synthetic project origin situation",
            meaning_at_time="The project represented protected continuity",
            significance="It shaped later collaboration",
            later_reinterpretation="Later understood as an engineering boundary",
            source_refs=("fixture://eng09/narrative-source",),
        )
    if experience_type is MemoryExperienceType.RELATIONSHIP:
        return RelationshipExperienceContent(
            relationship_id="relationship-synthetic",
            event="Synthetic relationship lived event",
            interpretation="A bounded interpretation at the recorded time",
            occurred_at="2026-09-10T00:00:00Z",
        )
    if experience_type is MemoryExperienceType.PREFERENCE:
        return PreferenceExperienceContent(
            subject="subject-synthetic",
            preference="Prefer concise architecture summaries",
            learned_from_event="A synthetic preference-bearing event",
            source_ref="fixture://eng09/preference-source",
        )
    if experience_type is MemoryExperienceType.PROJECT_COMMITMENT:
        return ProjectCommitmentExperienceContent(
            subject="subject-synthetic",
            counterparty="counterparty-synthetic",
            scope="ENG-09 synthetic fixture only",
            commitment="Preserve canonical MemoryExperience boundaries",
            transfer_semantics=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
            occurred_at="2026-09-10T00:00:00Z",
        )
    return EpisodicExperienceContent(
        event="Synthetic bounded event",
        occurred_at="2026-09-10T00:00:00Z",
        context="Synthetic test context",
        source_ref="fixture://eng09/episodic-source",
    )


def record(
    experience_type: MemoryExperienceType,
    *,
    experience_id: str = "experience-synthetic-001",
    version_id: str = "v1",
    predecessor: str | None = None,
):
    return MemoryExperienceRecord(
        experience_id=experience_id,
        version_id=version_id,
        experience_type=experience_type,
        content=content(experience_type),
        provenance_refs=(provenance(),),
        created_at="2026-09-10T00:00:00Z",
        predecessor_version_id=predecessor,
    )


def candidate(record_value: MemoryExperienceRecord) -> MemoryExperienceCandidate:
    return MemoryExperienceCandidate(record=record_value, submitted_at="2026-09-10T00:00:01Z")


@pytest.mark.parametrize("experience_type", list(MemoryExperienceType))
def test_all_five_synthetic_types_store_admit_and_resolve(experience_type: MemoryExperienceType) -> None:
    repository = MemoryExperienceRepository()
    stored = repository.store_candidate(candidate(record(experience_type)))

    assert stored.status is MemoryExperienceStatus.CANDIDATE
    admitted = repository.admit(
        stored.ref,
        actor="synthetic-governance-test",
        reason="Synthetic admission fixture",
        occurred_at="2026-09-10T00:01:00Z",
    )
    resolved = MemoryExperienceResolver(repository).resolve(admitted.ref)

    assert admitted.record is stored.record
    assert resolved.status is MemoryExperienceStatus.ADMITTED
    assert resolved.record.experience_type is experience_type


def test_exactly_five_types_and_no_sixth_ontology_class() -> None:
    assert len(MemoryExperienceType) == 5
    assert {item.value for item in MemoryExperienceType} == {
        "NarrativeExperience",
        "RelationshipExperience",
        "PreferenceExperience",
        "ProjectCommitmentExperience",
        "EpisodicExperience",
    }
    source = "\n".join(path.read_text(encoding="utf-8") for path in Path("julia_core/memory_experience").glob("*.py"))
    for forbidden in ("CorrectedCognition", "CorrectionTrajectory", "CausalChain", "ConsentState", "RelationshipState", "PersonaTrait", "RuntimeContext"):
        assert forbidden not in source


def test_unknown_exact_ref_fails_closed_without_latest_fallback() -> None:
    repository = MemoryExperienceRepository()
    stored = repository.store_candidate(candidate(record(MemoryExperienceType.EPISODIC)))

    with pytest.raises(MemoryExperienceRefNotFoundError):
        repository.resolve(MemoryExperienceRef(stored.ref.experience_id, "v2"))


def test_candidate_is_not_admitted_and_duplicate_conflict_rejected() -> None:
    repository = MemoryExperienceRepository()
    first = record(MemoryExperienceType.NARRATIVE)
    stored = repository.store_candidate(candidate(first))

    assert repository.resolve(stored.ref).status is MemoryExperienceStatus.CANDIDATE

    changed = record(MemoryExperienceType.NARRATIVE)
    object.__setattr__(changed.content, "event", "Changed synthetic narrative")
    with pytest.raises(MemoryExperienceConflictError):
        repository.store_candidate(candidate(changed))


def test_deterministic_digest_and_semantic_change() -> None:
    same_a = record(MemoryExperienceType.PREFERENCE)
    same_b = record(MemoryExperienceType.PREFERENCE)
    changed = record(MemoryExperienceType.PREFERENCE)
    object.__setattr__(changed.content, "preference", "Prefer different summaries")

    assert same_a.digest() == same_b.digest()
    assert same_a.canonical_serialization() == same_b.canonical_serialization()
    assert same_a.digest() != changed.digest()


def test_version_lineage_immutability_and_historical_resolution() -> None:
    repository = MemoryExperienceRepository()
    first = repository.store_candidate(candidate(record(MemoryExperienceType.NARRATIVE)))
    repository.admit(first.ref, actor="test", reason="admit", occurred_at="2026-09-10T00:01:00Z")
    first_digest = first.record.digest()

    second_record = record(
        MemoryExperienceType.NARRATIVE,
        version_id="v2",
        predecessor="v1",
    )
    object.__setattr__(second_record.content, "significance", "Changed significance requires a new version")
    second = repository.store_candidate(candidate(second_record))
    repository.admit(second.ref, actor="test", reason="admit successor", occurred_at="2026-09-10T00:02:00Z")
    repository.supersede(first.ref, actor="test", reason="v2 admitted", occurred_at="2026-09-10T00:03:00Z")
    repository.retire(second.ref, actor="test", reason="synthetic retirement", occurred_at="2026-09-10T00:04:00Z")

    old = repository.resolve(first.ref)
    retired = repository.resolve(second.ref)
    assert old.record.digest() == first_digest
    assert old.record.predecessor_version_id is None
    assert second.record.predecessor_version_id == "v1"
    assert old.status is MemoryExperienceStatus.SUPERSEDED
    assert retired.status is MemoryExperienceStatus.RETIRED


def test_repeated_admission_is_rejected() -> None:
    repository = MemoryExperienceRepository()
    stored = repository.store_candidate(candidate(record(MemoryExperienceType.EPISODIC)))
    repository.admit(stored.ref, actor="test", reason="admit", occurred_at="2026-09-10T00:01:00Z")

    with pytest.raises(MemoryExperienceLifecycleError):
        repository.admit(stored.ref, actor="test", reason="repeat", occurred_at="2026-09-10T00:02:00Z")


def test_provenance_is_required() -> None:
    with pytest.raises(ValueError, match="requires provenance"):
        MemoryExperienceRecord(
            experience_id="experience-synthetic-001",
            version_id="v1",
            experience_type=MemoryExperienceType.RELATIONSHIP,
            content=content(MemoryExperienceType.RELATIONSHIP),
            provenance_refs=(),
            created_at="2026-09-10T00:00:00Z",
        )


def test_project_commitment_scope_and_transfer_semantics_are_preserved() -> None:
    governed = MemoryExperienceRepository().store_candidate(
        candidate(record(MemoryExperienceType.PROJECT_COMMITMENT))
    )
    payload = governed.record.canonical_payload()["content"]

    assert payload["subject"] == "subject-synthetic"
    assert payload["counterparty"] == "counterparty-synthetic"
    assert payload["scope"] == "ENG-09 synthetic fixture only"
    assert payload["transfer_semantics"] == "EXPLICIT_REAUTHORIZATION_REQUIRED"
    assert governed.record.canonical_payload()["authority"]["standing_authorization"] is False


def test_history_does_not_grant_consent_identity_or_runtime_authority() -> None:
    governed = MemoryExperienceRepository().store_candidate(
        candidate(record(MemoryExperienceType.RELATIONSHIP))
    )
    payload = json.dumps(governed.record.canonical_payload())

    assert governed.record.canonical_payload()["authority"] == {
        "standing_authorization": False,
        "current_consent": False,
        "mutates_identity": False,
        "runtime_authority": False,
    }
    for forbidden in ("standing_consent", "permanent_role", "current_relationship_state", "identity_mutation", "system_prompt", "runtime_prompt", "provider_instructions", "embedding", "retrieval_index"):
        assert forbidden not in payload


def test_package_has_no_legacy_identity_projection_context_or_runtime_authority_imports() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in Path("julia_core/memory_experience").glob("*.py"))

    for forbidden in (
        "from julia_core.memory ",
        "from julia_core.experience ",
        "from julia_core.narrative ",
        "from julia_core.identity",
        "from julia_core.projection",
        "from julia_core.continuity",
        "from julia_core.context_os",
        "from julia_core.context_assembly",
        "from julia_core.runtime",
        "from julia_core.providers",
        "from julia_core.persona",
        "from julia_core.self_model",
    ):
        assert forbidden not in source


def test_changed_scope_is_limited_to_authorized_eng09_paths() -> None:
    changed = subprocess.run(
        ["git", "diff", "--name-only", BASE_SHA],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    changed.extend(
        path
        for path in subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        if path.startswith(("julia_core/memory_experience/", "tests/memory_experience/", "tests/identity/", "tests/projection/", "docs/mira_persona_architecture/", "artifacts/mira_persona_architecture/"))
    )
    allowed = (
        "julia_core/identity/",
        "julia_core/projection/",
        "julia_core/memory_experience/",
        "tests/memory_experience/",
        "tests/identity/",
        "tests/projection/",
        "docs/mira_persona_architecture/",
        "artifacts/mira_persona_architecture/",
    )

    assert changed
    assert all(path.startswith(allowed) for path in changed)

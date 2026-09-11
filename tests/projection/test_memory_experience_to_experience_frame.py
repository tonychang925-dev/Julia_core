from __future__ import annotations

import json
from collections.abc import Mapping

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
    MemoryExperienceStatus,
    MemoryExperienceType,
    EpisodicExperienceContent,
    NarrativeExperienceContent,
    PreferenceExperienceContent,
    ProjectCommitmentExperienceContent,
    RelationshipExperienceContent,
)
from julia_core.projection import (
    ExperienceFrame,
    ExperienceProjectionPolicy,
)


class BackedMapping(Mapping):
    def __init__(self, backing):
        self._backing = backing

    def __getitem__(self, key):
        return self._backing[key]

    def __iter__(self):
        return iter(self._backing)

    def __len__(self):
        return len(self._backing)


class SubclassedResolver(MemoryExperienceResolver):
    def resolve(self, ref):
        return self._repository.resolve(ref)


class SubclassedRef(MemoryExperienceRef):
    pass


def content(experience_type: MemoryExperienceType):
    if experience_type is MemoryExperienceType.NARRATIVE:
        return NarrativeExperienceContent(
            event="Synthetic narrative event",
            meaning_at_time="Synthetic meaning at the recorded time",
            significance="Synthetic significance",
            source_refs=("fixture://eng10/narrative-source",),
        )
    if experience_type is MemoryExperienceType.RELATIONSHIP:
        return RelationshipExperienceContent(
            relationship_id="relationship-synthetic",
            event="Synthetic relationship event",
            interpretation="Synthetic bounded interpretation",
            occurred_at="2026-09-11T00:00:00Z",
        )
    if experience_type is MemoryExperienceType.PREFERENCE:
        return PreferenceExperienceContent(
            subject="subject-synthetic",
            preference="Prefer bounded architecture summaries",
            learned_from_event="Synthetic preference-bearing event",
            source_ref="fixture://eng10/preference-source",
        )
    if experience_type is MemoryExperienceType.PROJECT_COMMITMENT:
        return ProjectCommitmentExperienceContent(
            subject="subject-synthetic",
            counterparty="counterparty-synthetic",
            scope="ENG-10 synthetic fixture",
            commitment="Preserve MemoryExperience authority",
            transfer_semantics=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
            occurred_at="2026-09-11T00:00:00Z",
        )
    return EpisodicExperienceContent(
        event="Synthetic episodic event",
        occurred_at="2026-09-11T00:00:00Z",
        context="Synthetic bounded episodic context",
        source_ref="fixture://eng10/episodic-source",
    )


def record(experience_type: MemoryExperienceType, *, version_id: str = "v1"):
    return MemoryExperienceRecord(
        experience_id="experience-synthetic-eng10",
        version_id=version_id,
        experience_type=experience_type,
        content=content(experience_type),
        provenance_refs=(
            MemoryExperienceProvenance(
                source_type="synthetic_fixture",
                source_ref="fixture://eng10/synthetic-experience",
                source_digest="c" * 64,
            ),
        ),
        created_at="2026-09-11T00:00:00Z",
    )


def stored(experience_type: MemoryExperienceType = MemoryExperienceType.EPISODIC):
    repository = MemoryExperienceRepository()
    stored_record = repository.store_candidate(
        MemoryExperienceCandidate(
            record=record(experience_type), submitted_at="2026-09-11T00:00:01Z"
        )
    )
    return repository, stored_record


def admitted(experience_type: MemoryExperienceType = MemoryExperienceType.EPISODIC):
    repository, governed = stored(experience_type)
    repository.admit(
        governed.ref,
        actor="synthetic-governance-test",
        reason="Synthetic admission fixture",
        occurred_at="2026-09-11T00:01:00Z",
    )
    return repository, repository.resolve(governed.ref)


def test_exact_admitted_ref_projects_deterministic_experience_frame() -> None:
    repository, admitted_record = admitted()
    policy = ExperienceProjectionPolicy()
    resolver = MemoryExperienceResolver(repository)

    first = policy.project_ref(admitted_record.ref, resolver)
    second = policy.project_ref(admitted_record.ref, resolver)

    assert first.source_ref == admitted_record.ref
    assert first.source_digest == admitted_record.record.digest()
    assert first.source_status is MemoryExperienceStatus.ADMITTED
    assert first.canonical_serialization() == second.canonical_serialization()
    assert first.digest() == second.digest()


@pytest.mark.parametrize(
    ("method", "expected_status"),
    [
        ("candidate", MemoryExperienceStatus.CANDIDATE),
        ("admit", MemoryExperienceStatus.ADMITTED),
        ("supersede", MemoryExperienceStatus.SUPERSEDED),
        ("retire", MemoryExperienceStatus.RETIRED),
    ],
)
def test_projection_preserves_exact_lifecycle_without_promotion(
    method, expected_status
) -> None:
    repository, governed = stored()
    if method != "candidate":
        getattr(repository, method)(
            governed.ref,
            actor="synthetic-governance-test",
            reason=f"Synthetic {method}",
            occurred_at="2026-09-11T00:02:00Z",
        )

    frame = ExperienceProjectionPolicy().project_ref(
        governed.ref, MemoryExperienceResolver(repository)
    )

    assert frame.source_status is expected_status
    assert repository.resolve(governed.ref).status is expected_status


def test_unknown_exact_ref_fails_closed_without_latest_fallback() -> None:
    repository, governed = stored()

    with pytest.raises(MemoryExperienceRefNotFoundError):
        ExperienceProjectionPolicy().project_ref(
            MemoryExperienceRef(governed.ref.experience_id, "v2"),
            MemoryExperienceResolver(repository),
        )


def test_semantic_source_change_changes_frame_digest() -> None:
    first_repository, first = admitted(MemoryExperienceType.PREFERENCE)
    second_repository, second = admitted(MemoryExperienceType.NARRATIVE)
    policy = ExperienceProjectionPolicy()

    first_frame = policy.project_ref(first.ref, MemoryExperienceResolver(first_repository))
    second_frame = policy.project_ref(second.ref, MemoryExperienceResolver(second_repository))

    assert first_frame.digest() != second_frame.digest()
    assert first_frame.experience_type is not second_frame.experience_type


def test_projection_does_not_mutate_source_repository_or_lifecycle() -> None:
    repository, governed = stored()
    source_digest = governed.record.digest()
    source_payload = governed.record.canonical_payload()

    frame = ExperienceProjectionPolicy().project_ref(
        governed.ref, MemoryExperienceResolver(repository)
    )

    assert repository.resolve(governed.ref).status is MemoryExperienceStatus.CANDIDATE
    assert governed.record.digest() == source_digest
    assert governed.record.canonical_payload() == source_payload
    assert frame.source_status is MemoryExperienceStatus.CANDIDATE


@pytest.mark.parametrize("experience_type", list(MemoryExperienceType))
def test_all_five_types_project_without_collapsing_type_identity(
    experience_type,
) -> None:
    repository, governed = admitted(experience_type)

    frame = ExperienceProjectionPolicy().project_ref(
        governed.ref, MemoryExperienceResolver(repository)
    )

    assert frame.experience_type is experience_type
    assert frame.to_dict()["experience_type"] == experience_type.value


def test_frame_contains_only_source_authorized_non_authoritative_semantics() -> None:
    repository, governed = admitted(MemoryExperienceType.PROJECT_COMMITMENT)

    frame = ExperienceProjectionPolicy().project_ref(
        governed.ref, MemoryExperienceResolver(repository)
    )
    payload = json.dumps(frame.to_dict())

    assert frame.to_dict()["projection"]["non_authoritative"] is True
    assert frame.to_dict()["projection"]["canonical_authority"] == "MemoryExperienceRecord"
    for forbidden in (
        "system_prompt",
        "provider_instructions",
        "runtime_prompt",
        "context_admission_decision",
        "retrieval_ranking",
        "selection_score",
        "embedding",
        "index_material",
    ):
        assert forbidden not in payload


def test_project_commitment_does_not_become_current_consent_or_authorization() -> None:
    repository, governed = admitted(MemoryExperienceType.PROJECT_COMMITMENT)

    frame = ExperienceProjectionPolicy().project_ref(
        governed.ref, MemoryExperienceResolver(repository)
    )
    projection = frame.to_dict()["projection"]

    assert projection["current_consent"] is False
    assert projection["standing_authorization"] is False
    assert projection["runtime_authority"] is False


def test_direct_governed_memory_experience_projection_is_forbidden() -> None:
    _, governed = admitted()

    with pytest.raises(TypeError, match="use project_ref"):
        ExperienceProjectionPolicy().project(governed)


def test_forged_resolver_and_ref_are_rejected() -> None:
    repository, governed = stored()

    with pytest.raises(TypeError, match="exact MemoryExperienceResolver"):
        ExperienceProjectionPolicy().project_ref(
            governed.ref, SubclassedResolver(repository)
        )
    with pytest.raises(TypeError, match="exact MemoryExperienceRef"):
        ExperienceProjectionPolicy().project_ref(
            SubclassedRef(governed.ref.experience_id, governed.ref.version_id),
            MemoryExperienceResolver(repository),
        )


def test_experience_frame_rejects_noncanonical_payload_objects() -> None:
    repository, governed = stored()
    source = governed.record
    frame_arguments = {
        "schema_version": "1.0.0",
        "policy_id": "experience_projection.memory_experience_only",
        "policy_version": "1.0.0",
        "source_ref": source.ref,
        "source_digest": source.digest(),
        "source_status": MemoryExperienceStatus.CANDIDATE,
        "experience_id": source.experience_id,
        "version_id": source.version_id,
        "predecessor_version_id": source.predecessor_version_id,
        "experience_type": source.experience_type,
        "content": object(),
        "provenance_refs": (object(),),
        "created_at": source.created_at,
    }

    with pytest.raises(TypeError, match="content must be a Mapping"):
        ExperienceFrame(**frame_arguments)
    with pytest.raises(TypeError, match="provenance_refs elements must be Mappings"):
        ExperienceFrame(**(frame_arguments | {"content": {}}))


def test_arbitrary_mapping_is_deeply_frozen_and_detached() -> None:
    repository, governed = stored()
    source = governed.record
    backing = {"preference": "original", "nested": {"case": "same"}}
    frame = ExperienceFrame(
        schema_version="1.0.0",
        policy_id="experience_projection.memory_experience_only",
        policy_version="1.0.0",
        source_ref=source.ref,
        source_digest=source.digest(),
        source_status=MemoryExperienceStatus.CANDIDATE,
        experience_id=source.experience_id,
        version_id=source.version_id,
        predecessor_version_id=source.predecessor_version_id,
        experience_type=source.experience_type,
        content=BackedMapping(backing),
        provenance_refs=(),
        created_at=source.created_at,
    )
    digest = frame.digest()

    backing["preference"] = "mutated"
    backing["injected"] = "system_prompt"
    backing["nested"]["case"] = "mutated"

    assert frame.content["preference"] == "original"
    assert frame.content["nested"]["case"] == "same"
    assert "injected" not in frame.content
    assert frame.digest() == digest


def test_outward_serialization_mutation_cannot_change_internal_frame() -> None:
    repository, governed = admitted(MemoryExperienceType.RELATIONSHIP)
    frame = ExperienceProjectionPolicy().project_ref(
        governed.ref, MemoryExperienceResolver(repository)
    )
    digest = frame.digest()

    outward = frame.to_dict()
    outward["content"]["event"] = "mutated outward"
    outward["projection"]["non_authoritative"] = False

    assert frame.content["event"] == "Synthetic relationship event"
    assert frame.digest() == digest

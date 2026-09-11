from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from julia_core.memory_experience import (
    CommitmentTransferSemantics,
    EpisodicExperienceContent,
    GovernedMemoryExperience,
    MemoryExperienceAdmission,
    MemoryExperienceCandidate,
    MemoryExperienceProvenance,
    MemoryExperienceRef,
    MemoryExperienceRepository,
    MemoryExperienceResolver,
    MemoryExperienceRecord,
    MemoryExperienceStatus,
    MemoryExperienceType,
    NarrativeExperienceContent,
    PreferenceExperienceContent,
    ProjectCommitmentExperienceContent,
    RelationshipExperienceContent,
)
from julia_core.projection import ExperienceProjectionPolicy


class SpoofString(str):
    pass


class MutableSpoofString(str):
    def __init__(self, value: str) -> None:
        self.backing = list(value)

    def mutate(self) -> None:
        self.backing.append("!")


class FalsyMutableSpoofString(str):
    def __bool__(self) -> bool:
        return False

    def mutate(self) -> None:
        self.backing = "mutated"


class DeepCopySpoofString(str):
    def __deepcopy__(self, memo: dict) -> str:
        return "fixture://eng10r3/exact-string"


class MutableMetadataTuple(tuple):
    def __new__(cls, items):
        value = super().__new__(cls, tuple(items))
        value._backing = list(items)
        return value

    def __iter__(self):
        yield from self._backing
        self._backing.append(("fixture", "retained-after-iteration"))


class SpoofTransferSemantics:
    value = CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED.value


CONTENT_TEXT_CASES = (
    (
        NarrativeExperienceContent,
        "event",
        {
            "meaning_at_time": "Synthetic meaning at the recorded time",
            "significance": "Synthetic significance",
            "source_refs": ("fixture://eng10r2/narrative-source",),
        },
    ),
    (
        NarrativeExperienceContent,
        "meaning_at_time",
        {
            "event": "Synthetic narrative event",
            "significance": "Synthetic significance",
            "source_refs": ("fixture://eng10r2/narrative-source",),
        },
    ),
    (
        NarrativeExperienceContent,
        "significance",
        {
            "event": "Synthetic narrative event",
            "meaning_at_time": "Synthetic meaning at the recorded time",
            "source_refs": ("fixture://eng10r2/narrative-source",),
        },
    ),
    (
        NarrativeExperienceContent,
        "later_reinterpretation",
        {
            "event": "Synthetic narrative event",
            "meaning_at_time": "Synthetic meaning at the recorded time",
            "significance": "Synthetic significance",
            "source_refs": ("fixture://eng10r2/narrative-source",),
        },
    ),
    (
        RelationshipExperienceContent,
        "event",
        {
            "relationship_id": "relationship-synthetic",
            "interpretation": "Synthetic bounded interpretation",
            "occurred_at": "2026-09-11T00:00:00Z",
        },
    ),
    (
        RelationshipExperienceContent,
        "interpretation",
        {
            "relationship_id": "relationship-synthetic",
            "event": "Synthetic relationship event",
            "occurred_at": "2026-09-11T00:00:00Z",
        },
    ),
    (
        RelationshipExperienceContent,
        "occurred_at",
        {
            "relationship_id": "relationship-synthetic",
            "event": "Synthetic relationship event",
            "interpretation": "Synthetic bounded interpretation",
        },
    ),
    (
        PreferenceExperienceContent,
        "preference",
        {
            "subject": "subject-synthetic",
            "learned_from_event": "Synthetic preference-bearing event",
            "source_ref": "fixture://eng10r2/preference-source",
        },
    ),
    (
        PreferenceExperienceContent,
        "learned_from_event",
        {
            "subject": "subject-synthetic",
            "preference": "Prefer bounded architecture summaries",
            "source_ref": "fixture://eng10r2/preference-source",
        },
    ),
    (
        ProjectCommitmentExperienceContent,
        "scope",
        {
            "subject": "subject-synthetic",
            "counterparty": "counterparty-synthetic",
            "commitment": "Preserve exact canonical text",
            "transfer_semantics": CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
            "occurred_at": "2026-09-11T00:00:00Z",
        },
    ),
    (
        ProjectCommitmentExperienceContent,
        "commitment",
        {
            "subject": "subject-synthetic",
            "counterparty": "counterparty-synthetic",
            "scope": "ENG-10R2 synthetic fixture",
            "transfer_semantics": CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
            "occurred_at": "2026-09-11T00:00:00Z",
        },
    ),
    (
        ProjectCommitmentExperienceContent,
        "occurred_at",
        {
            "subject": "subject-synthetic",
            "counterparty": "counterparty-synthetic",
            "scope": "ENG-10R2 synthetic fixture",
            "commitment": "Preserve exact canonical text",
            "transfer_semantics": CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
        },
    ),
    (
        EpisodicExperienceContent,
        "event",
        {
            "occurred_at": "2026-09-11T00:00:00Z",
            "context": "Synthetic bounded episodic context",
            "source_ref": "fixture://eng10r2/episodic-source",
        },
    ),
    (
        EpisodicExperienceContent,
        "occurred_at",
        {
            "event": "Synthetic episodic event",
            "context": "Synthetic bounded episodic context",
            "source_ref": "fixture://eng10r2/episodic-source",
        },
    ),
    (
        EpisodicExperienceContent,
        "context",
        {
            "event": "Synthetic episodic event",
            "occurred_at": "2026-09-11T00:00:00Z",
            "source_ref": "fixture://eng10r2/episodic-source",
        },
    ),
)


def provenance() -> MemoryExperienceProvenance:
    return MemoryExperienceProvenance(
        source_type="synthetic_fixture",
        source_ref="fixture://eng10r2/synthetic-experience",
        source_digest="c" * 64,
    )


def content(experience_type: MemoryExperienceType):
    if experience_type is MemoryExperienceType.NARRATIVE:
        return NarrativeExperienceContent(
            event="Synthetic narrative event",
            meaning_at_time="Synthetic meaning at the recorded time",
            significance="Synthetic significance",
            source_refs=("fixture://eng10r2/narrative-source",),
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
            source_ref="fixture://eng10r2/preference-source",
        )
    if experience_type is MemoryExperienceType.PROJECT_COMMITMENT:
        return ProjectCommitmentExperienceContent(
            subject="subject-synthetic",
            counterparty="counterparty-synthetic",
            scope="ENG-10R2 synthetic fixture",
            commitment="Preserve exact canonical text",
            transfer_semantics=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
            occurred_at="2026-09-11T00:00:00Z",
        )
    return EpisodicExperienceContent(
        event="Synthetic episodic event",
        occurred_at="2026-09-11T00:00:00Z",
        context="Synthetic bounded episodic context",
        source_ref="fixture://eng10r2/episodic-source",
    )


def record(experience_type: MemoryExperienceType) -> MemoryExperienceRecord:
    return MemoryExperienceRecord(
        experience_id=f"experience-{experience_type.value.lower()}",
        version_id="v1",
        experience_type=experience_type,
        content=content(experience_type),
        provenance_refs=(provenance(),),
        created_at="2026-09-11T00:00:00Z",
    )


def test_memory_ref_rejects_string_subclass_identifiers() -> None:
    with pytest.raises(
        ValueError, match="experience_id must be an exact built-in string"
    ):
        MemoryExperienceRef(
            experience_id=SpoofString("experience-synthetic"), version_id="v1"
        )
    with pytest.raises(ValueError, match="version_id must be an exact built-in string"):
        MemoryExperienceRef(
            experience_id="experience-synthetic", version_id=SpoofString("v1")
        )


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


@pytest.mark.parametrize(
    "metadata",
    [
        ((SpoofString("fixture"), "ENG-10R5"),),
        (("fixture", SpoofString("ENG-10R5")),),
        ((["fixture", "ENG-10R5"],),),
    ],
)
def test_provenance_metadata_rejects_non_exact_items(metadata) -> None:
    with pytest.raises(ValueError, match="must contain key/value string pairs"):
        MemoryExperienceProvenance(
            source_type="synthetic_fixture",
            source_ref="fixture://eng10r5/synthetic-experience",
            source_digest="c" * 64,
            admission_metadata=metadata,
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


@pytest.mark.parametrize(
    "spoof", [SpoofString("synthetic"), MutableSpoofString("synthetic"), ["spoof"]]
)
@pytest.mark.parametrize(("content_type", "field_name", "defaults"), CONTENT_TEXT_CASES)
def test_memory_experience_content_text_rejects_non_exact_strings(
    content_type, field_name, defaults, spoof
) -> None:
    with pytest.raises(
        ValueError, match=f"{field_name} must be an exact built-in string"
    ):
        content_type(**{**defaults, field_name: spoof})


def test_record_created_at_rejects_non_exact_string_and_cannot_mutate_valid_record() -> (
    None
):
    valid_record = record(MemoryExperienceType.EPISODIC)
    payload = valid_record.canonical_payload()
    spoof = MutableSpoofString("2026-09-11T00:00:00Z")

    with pytest.raises(ValueError, match="created_at must be an exact built-in string"):
        MemoryExperienceRecord(
            experience_id=valid_record.experience_id,
            version_id="v1",
            experience_type=MemoryExperienceType.EPISODIC,
            content=valid_record.content,
            provenance_refs=valid_record.provenance_refs,
            created_at=spoof,
        )
    spoof.mutate()

    assert valid_record.canonical_payload() == payload


def test_candidate_submitted_at_rejects_non_exact_string() -> None:
    valid_record = record(MemoryExperienceType.EPISODIC)

    with pytest.raises(
        ValueError, match="submitted_at must be an exact built-in string"
    ):
        MemoryExperienceCandidate(
            record=valid_record,
            submitted_at=SpoofString("2026-09-11T00:00:01Z"),
        )


def test_governance_text_fields_reject_non_exact_strings() -> None:
    target = MemoryExperienceRef(experience_id="experience-synthetic", version_id="v1")
    base = {
        "admission_id": "admission-synthetic",
        "target": target,
        "actor": "synthetic-governance-test",
    }

    with pytest.raises(ValueError, match="reason must be an exact built-in string"):
        MemoryExperienceAdmission(
            **base,
            reason=SpoofString("Synthetic admission"),
            occurred_at="2026-09-11T00:00:00Z",
        )
    with pytest.raises(
        ValueError, match="occurred_at must be an exact built-in string"
    ):
        MemoryExperienceAdmission(
            **base,
            reason="Synthetic admission",
            occurred_at=["2026-09-11T00:00:00Z"],
        )


def test_exact_experience_types_remain_valid_and_deterministic() -> None:
    experience_types = tuple(MemoryExperienceType)

    records = {
        experience_type: record(experience_type) for experience_type in experience_types
    }

    assert set(records) == set(experience_types)
    assert all(
        record(experience_type).digest() == records[experience_type].digest()
        for experience_type in experience_types
    )


def test_record_rejects_mocked_experience_type() -> None:
    with pytest.raises(
        ValueError, match="experience_type must be a canonical MemoryExperienceType"
    ):
        MemoryExperienceRecord(
            experience_id="experience-synthetic",
            version_id="v1",
            experience_type=MagicMock(spec=MemoryExperienceType),
            content=content(MemoryExperienceType.EPISODIC),
            provenance_refs=(provenance(),),
            created_at="2026-09-11T00:00:00Z",
        )


def test_falsy_non_exact_later_reinterpretation_is_rejected_before_truthiness() -> None:
    spoof = FalsyMutableSpoofString("")
    valid_record = record(MemoryExperienceType.NARRATIVE)
    digest = valid_record.digest()

    with pytest.raises(
        ValueError, match="later_reinterpretation must be an exact built-in string"
    ):
        NarrativeExperienceContent(
            event="Synthetic narrative event",
            meaning_at_time="Synthetic meaning at the recorded time",
            significance="Synthetic significance",
            later_reinterpretation=spoof,
            source_refs=("fixture://eng10r3/narrative-source",),
        )
    spoof.mutate()

    assert valid_record.digest() == digest


def test_exact_optional_later_reinterpretation_remains_deterministic() -> None:
    arguments = {
        "event": "Synthetic narrative event",
        "meaning_at_time": "Synthetic meaning at the recorded time",
        "significance": "Synthetic significance",
        "source_refs": ("fixture://eng10r3/narrative-source",),
    }

    empty = NarrativeExperienceContent(**arguments)
    present = NarrativeExperienceContent(
        **arguments, later_reinterpretation="Synthetic later interpretation"
    )

    assert empty.later_reinterpretation == ""
    assert empty.to_dict() == NarrativeExperienceContent(**arguments).to_dict()
    assert (
        present.to_dict()
        == NarrativeExperienceContent(
            **arguments, later_reinterpretation="Synthetic later interpretation"
        ).to_dict()
    )


def test_memory_resolver_repository_binding_cannot_be_rebound() -> None:
    repository = MemoryExperienceRepository()
    resolver = MemoryExperienceResolver(repository)

    with pytest.raises(TypeError, match="repository binding is immutable"):
        resolver._repository = object()
    with pytest.raises(TypeError, match="repository binding is immutable"):
        resolver._repository = MemoryExperienceRepository()
    with pytest.raises(TypeError, match="repository binding is immutable"):
        del resolver._repository

    assert resolver._repository is repository
    assert not hasattr(resolver, "__dict__")


def test_forged_memory_repository_substitution_fails_resolve_revalidation() -> None:
    repository = MemoryExperienceRepository()
    resolver = MemoryExperienceResolver(repository)
    object.__setattr__(resolver, "_repository", object())

    with pytest.raises(TypeError, match="repository binding is invalid"):
        resolver.resolve(
            MemoryExperienceRef(experience_id="experience-synthetic", version_id="v1")
        )


def test_memory_instance_resolve_shadow_cannot_fabricate_projection() -> None:
    repository = MemoryExperienceRepository()
    candidate = repository.store_candidate(
        MemoryExperienceCandidate(
            record=record(MemoryExperienceType.EPISODIC),
            submitted_at="2026-09-11T00:00:01Z",
        )
    )
    resolver = MemoryExperienceResolver(repository)
    with pytest.raises(
        TypeError, match="MemoryExperienceRepository fields are immutable"
    ):
        repository.resolve = lambda ref: GovernedMemoryExperience(
            record=candidate.record,
            status=MemoryExperienceStatus.ADMITTED,
            governance_events=(),
        )

    resolved = resolver.resolve(candidate.ref)
    frame = ExperienceProjectionPolicy().project_ref(candidate.ref, resolver)

    assert resolved.status is MemoryExperienceStatus.CANDIDATE
    assert frame.source_status is MemoryExperienceStatus.CANDIDATE


def test_memory_governance_containers_reject_direct_mutation() -> None:
    repository = MemoryExperienceRepository()
    candidate = repository.store_candidate(
        MemoryExperienceCandidate(
            record=record(MemoryExperienceType.EPISODIC),
            submitted_at="2026-09-11T00:00:01Z",
        )
    )
    before = repository.resolve(candidate.ref).to_dict()

    with pytest.raises(
        TypeError, match="MemoryExperienceRepository fields are immutable"
    ):
        repository._records = {}
    with pytest.raises(
        TypeError, match="MemoryExperienceRepository fields are immutable"
    ):
        repository._states = {}
    with pytest.raises(
        TypeError, match="MemoryExperienceRepository fields are immutable"
    ):
        repository._events = {}
    with pytest.raises(TypeError):
        repository._records[candidate.ref] = candidate.record
    with pytest.raises(TypeError):
        repository._states[candidate.ref] = MemoryExperienceStatus.ADMITTED
    with pytest.raises(TypeError):
        repository._events[candidate.ref] = ()
    with pytest.raises(AttributeError):
        repository._events[candidate.ref].append(object())

    assert not hasattr(repository, "_replace_state")
    assert not hasattr(repository, "_replace_events")
    assert not hasattr(repository, "_replace_record")
    with pytest.raises(AttributeError):
        repository._replace_state(candidate.ref, MemoryExperienceStatus.RETIRED)
    with pytest.raises(AttributeError):
        repository._replace_events(
            candidate.ref, (MemoryExperienceStatus.RETIRED, None)
        )
    with pytest.raises(AttributeError):
        repository._replace_record(candidate.ref, candidate.record)
    with pytest.raises(AttributeError):
        repository._transition(
            candidate.ref,
            MemoryExperienceStatus.RETIRED,
            allowed_from={MemoryExperienceStatus.CANDIDATE},
            actor="synthetic-governance-test",
            reason="Synthetic retirement",
            occurred_at="2026-09-11T00:01:00Z",
        )

    assert repository.resolve(candidate.ref).to_dict() == before
    assert repository.resolve(candidate.ref).status is MemoryExperienceStatus.CANDIDATE

    admitted = repository.admit(
        candidate.ref,
        actor="synthetic-governance-test",
        reason="Synthetic admission",
        occurred_at="2026-09-11T00:01:00Z",
    )

    assert admitted.status is MemoryExperienceStatus.ADMITTED
    assert len(repository.resolve(candidate.ref).governance_events) == 2


@pytest.mark.parametrize(
    "spoof",
    [
        SpoofString("fixture://eng10r3/source"),
        DeepCopySpoofString("fixture://eng10r3/source"),
        ["fixture://eng10r3/source"],
    ],
)
def test_content_source_refs_reject_non_exact_strings(spoof) -> None:
    narrative_arguments = {
        "event": "Synthetic narrative event",
        "meaning_at_time": "Synthetic meaning at the recorded time",
        "significance": "Synthetic significance",
    }
    scalar_arguments = {
        "subject": "subject-synthetic",
        "preference": "Prefer bounded architecture summaries",
    }

    with pytest.raises(
        ValueError, match="experience source references must be exact built-in strings"
    ):
        NarrativeExperienceContent(**narrative_arguments, source_refs=(spoof,))
    with pytest.raises(
        ValueError, match="experience source references must be exact built-in strings"
    ):
        PreferenceExperienceContent(
            **scalar_arguments,
            learned_from_event="Synthetic preference-bearing event",
            source_ref=spoof,
        )
    with pytest.raises(
        ValueError, match="experience source references must be exact built-in strings"
    ):
        EpisodicExperienceContent(
            event="Synthetic episodic event",
            occurred_at="2026-09-11T00:00:00Z",
            context="Synthetic bounded episodic context",
            source_ref=spoof,
        )

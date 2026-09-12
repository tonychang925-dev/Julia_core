from __future__ import annotations

import ast
import inspect
from dataclasses import replace
from pathlib import Path

import pytest

from julia_core.canonical_authority_source import (
    CanonicalSemanticAuthorityErrorCode,
    CanonicalSemanticAuthoritySource,
    CanonicalSemanticAuthoritySourceError,
)
from julia_core.identity import (
    IdentityAnchor,
    IdentityBoundary,
    IdentityContract,
    IdentityProvenance,
    IdentityRef,
    IdentityRepository,
    IdentityResolver,
    IdentityValue,
    IdentityVersion,
    RelationshipRoleAnchor,
)
from julia_core.memory_experience import (
    CommitmentTransferSemantics,
    MemoryExperienceCandidate,
    MemoryExperienceProvenance,
    MemoryExperienceRecord,
    MemoryExperienceRef,
    MemoryExperienceRepository,
    MemoryExperienceResolver,
    MemoryExperienceType,
    ProjectCommitmentExperienceContent,
)
from julia_core.projection import ExperienceFrame, IdentityFrame


MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "julia_core/canonical_authority_source.py"
)


class SubclassedIdentityRef(IdentityRef):
    pass


class SubclassedMemoryRef(MemoryExperienceRef):
    pass


class SubclassedIdentityResolver(IdentityResolver):
    pass


class SubclassedMemoryResolver(MemoryExperienceResolver):
    pass


def identity_version() -> IdentityVersion:
    return IdentityVersion(
        contract=IdentityContract(
            identity_id="identity-n4b",
            anchors=(IdentityAnchor(anchor_id="anchor", statement="anchor"),),
            values=(IdentityValue(value_id="value", statement="value"),),
            boundaries=(
                IdentityBoundary(boundary_id="boundary", constraint="boundary"),
            ),
            relationship_role_anchors=(
                RelationshipRoleAnchor(
                    anchor_id="role",
                    relationship_id="relationship",
                    role="collaborator",
                ),
            ),
        ),
        lineage_id="lineage-n4b",
        version_id="v1",
        predecessor_version_id=None,
        created_at="2026-09-12T00:00:00Z",
        provenance_refs=(
            IdentityProvenance(
                source_type="governance_fixture",
                source_ref="fixture://n4b/identity",
                source_digest="a" * 64,
            ),
        ),
    )


def identity_fixture(*, admit: bool = True, retire: bool = False):
    repository = IdentityRepository()
    candidate = repository.store_candidate(identity_version())
    if admit:
        repository.admit(
            candidate.ref,
            actor="n4b-test-governance",
            reason="test admission",
            occurred_at="2026-09-12T00:01:00Z",
        )
    if retire:
        repository.retire(
            candidate.ref,
            actor="n4b-test-governance",
            reason="test retirement",
            occurred_at="2026-09-12T00:02:00Z",
        )
    return repository, candidate.ref


def memory_record() -> MemoryExperienceRecord:
    return MemoryExperienceRecord(
        experience_id="experience-n4b",
        version_id="v1",
        experience_type=MemoryExperienceType.PROJECT_COMMITMENT,
        content=ProjectCommitmentExperienceContent(
            subject="subject",
            counterparty="counterparty",
            scope="N4B fixture",
            commitment="commitment",
            transfer_semantics=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
            occurred_at="2026-09-12T00:00:00Z",
        ),
        provenance_refs=(
            MemoryExperienceProvenance(
                source_type="governance_fixture",
                source_ref="fixture://n4b/experience",
                source_digest="b" * 64,
            ),
        ),
        created_at="2026-09-12T00:00:00Z",
    )


def memory_fixture(*, admit: bool = True, retire: bool = False):
    repository = MemoryExperienceRepository()
    candidate = repository.store_candidate(
        MemoryExperienceCandidate(
            record=memory_record(),
            submitted_at="2026-09-12T00:00:01Z",
        )
    )
    if admit:
        repository.admit(
            candidate.ref,
            actor="n4b-test-governance",
            reason="test admission",
            occurred_at="2026-09-12T00:01:00Z",
        )
    if retire:
        repository.retire(
            candidate.ref,
            actor="n4b-test-governance",
            reason="test retirement",
            occurred_at="2026-09-12T00:02:00Z",
        )
    return repository, candidate.ref


def bound_source():
    identity_repository, identity_ref = identity_fixture()
    memory_repository, memory_ref = memory_fixture()
    source = CanonicalSemanticAuthoritySource(
        identity_resolver=IdentityResolver(identity_repository),
        memory_resolver=MemoryExperienceResolver(memory_repository),
    )
    return source, identity_repository, identity_ref, memory_repository, memory_ref


def error_code(call) -> CanonicalSemanticAuthorityErrorCode:
    with pytest.raises(CanonicalSemanticAuthoritySourceError) as captured:
        call()
    return captured.value.code


def test_b01_b02_exact_admitted_refs_return_exact_frames() -> None:
    source, _, identity_ref, _, memory_ref = bound_source()
    identity_frame = source.resolve_identity_frame(identity_ref)
    experience_frame = source.resolve_experience_frame(memory_ref)
    assert type(identity_frame) is IdentityFrame
    assert type(experience_frame) is ExperienceFrame


def test_b03_provenance_matches_governed_source() -> None:
    source, identity_repository, identity_ref, memory_repository, memory_ref = (
        bound_source()
    )
    identity = source.resolve_identity_frame(identity_ref)
    experience = source.resolve_experience_frame(memory_ref)
    identity_governed = identity_repository.resolve(identity_ref)
    memory_governed = memory_repository.resolve(memory_ref)
    assert identity.source_ref == identity_ref
    assert identity.source_digest == identity_governed.version.digest()
    assert identity.source_status.value == "ADMITTED"
    assert tuple(identity.provenance_refs) == tuple(
        item.to_dict() for item in identity_governed.version.provenance_refs
    )
    assert experience.source_ref == memory_ref
    assert experience.source_digest == memory_governed.record.digest()
    assert experience.source_status.value == "ADMITTED"
    assert tuple(experience.provenance_refs) == tuple(
        item.to_dict() for item in memory_governed.record.provenance_refs
    )


def test_b04_repeated_resolution_is_deterministic() -> None:
    source, _, identity_ref, _, memory_ref = bound_source()
    assert (
        source.resolve_identity_frame(identity_ref).canonical_serialization()
        == source.resolve_identity_frame(identity_ref).canonical_serialization()
    )
    assert (
        source.resolve_experience_frame(memory_ref).canonical_serialization()
        == source.resolve_experience_frame(memory_ref).canonical_serialization()
    )


def test_b05_resolution_does_not_mutate_authority() -> None:
    source, identity_repository, identity_ref, memory_repository, memory_ref = (
        bound_source()
    )
    identity_before = identity_repository.resolve(identity_ref)
    memory_before = memory_repository.resolve(memory_ref)
    source.resolve_identity_frame(identity_ref)
    source.resolve_experience_frame(memory_ref)
    identity_after = identity_repository.resolve(identity_ref)
    memory_after = memory_repository.resolve(memory_ref)
    assert identity_after.status is identity_before.status
    assert len(identity_after.governance_events) == len(
        identity_before.governance_events
    )
    assert memory_after.status is memory_before.status
    assert len(memory_after.governance_events) == len(memory_before.governance_events)


def test_b06_consumer_receives_read_only_interface_only() -> None:
    public = {
        name
        for name, member in inspect.getmembers(CanonicalSemanticAuthoritySource)
        if not name.startswith("_")
    }
    assert public == {
        "resolve_identity_frame",
        "resolve_experience_frame",
    }
    source, _, identity_ref, _, _ = bound_source()
    with pytest.raises(TypeError):
        source.identity_resolver = IdentityResolver(IdentityRepository())
    with pytest.raises(TypeError):
        del source._identity_resolver


def test_b07_missing_source_bindings_fail_closed() -> None:
    source = CanonicalSemanticAuthoritySource()
    assert (
        error_code(lambda: source.resolve_identity_frame(IdentityRef("lineage", "v1")))
        is CanonicalSemanticAuthorityErrorCode.SOURCE_NOT_BOUND
    )
    assert (
        error_code(
            lambda: source.resolve_experience_frame(
                MemoryExperienceRef("experience", "v1")
            )
        )
        is CanonicalSemanticAuthorityErrorCode.SOURCE_NOT_BOUND
    )


def test_b08_b09_unknown_refs_fail_closed() -> None:
    source, _, identity_ref, _, memory_ref = bound_source()
    assert (
        error_code(
            lambda: source.resolve_identity_frame(
                IdentityRef(identity_ref.lineage_id, "missing")
            )
        )
        is CanonicalSemanticAuthorityErrorCode.REF_NOT_FOUND
    )
    assert (
        error_code(
            lambda: source.resolve_experience_frame(
                MemoryExperienceRef(memory_ref.experience_id, "missing")
            )
        )
        is CanonicalSemanticAuthorityErrorCode.REF_NOT_FOUND
    )


@pytest.mark.parametrize("retire", [False, True])
def test_b10_through_b13_nonadmitted_and_retired_fail_closed(retire: bool) -> None:
    identity_repository, identity_ref = identity_fixture(admit=False, retire=retire)
    memory_repository, memory_ref = memory_fixture(admit=False, retire=retire)
    source = CanonicalSemanticAuthoritySource(
        identity_resolver=IdentityResolver(identity_repository),
        memory_resolver=MemoryExperienceResolver(memory_repository),
    )
    expected = (
        CanonicalSemanticAuthorityErrorCode.REF_RETIRED
        if retire
        else CanonicalSemanticAuthorityErrorCode.REF_NOT_ADMITTED
    )
    assert error_code(lambda: source.resolve_identity_frame(identity_ref)) is expected
    assert error_code(lambda: source.resolve_experience_frame(memory_ref)) is expected


@pytest.mark.parametrize(
    ("value", "method"),
    [
        (object(), "identity"),
        ({"lineage_id": "lineage", "version_id": "v1"}, "identity"),
        (SubclassedIdentityRef("lineage", "v1"), "identity"),
        (object(), "experience"),
        ({"experience_id": "experience", "version_id": "v1"}, "experience"),
        (SubclassedMemoryRef("experience", "v1"), "experience"),
    ],
)
def test_b14_forged_and_inexact_refs_fail_closed(value: object, method: str) -> None:
    source, _, _, _, _ = bound_source()
    call = (
        source.resolve_identity_frame
        if method == "identity"
        else source.resolve_experience_frame
    )
    assert (
        error_code(lambda: call(value))
        is CanonicalSemanticAuthorityErrorCode.TYPE_MISMATCH
    )


def test_b15_malformed_projection_provenance_fails_closed(monkeypatch) -> None:
    source, _, identity_ref, _, memory_ref = bound_source()
    valid = source.resolve_identity_frame(identity_ref)
    monkeypatch.setattr(
        source._identity_policy,
        "project_ref",
        lambda ref, resolver: replace(valid, provenance_refs=()),
    )
    assert (
        error_code(lambda: source.resolve_identity_frame(identity_ref))
        is CanonicalSemanticAuthorityErrorCode.PROVENANCE_FAILURE
    )
    valid_experience = source.resolve_experience_frame(memory_ref)
    monkeypatch.setattr(
        source._memory_policy,
        "project_ref",
        lambda ref, resolver: replace(valid_experience, provenance_refs=()),
    )
    assert (
        error_code(lambda: source.resolve_experience_frame(memory_ref))
        is CanonicalSemanticAuthorityErrorCode.PROVENANCE_FAILURE
    )


def test_superseded_refs_fail_as_nonadmitted() -> None:
    identity_repository, identity_ref = identity_fixture()
    identity_repository.supersede(
        identity_ref,
        actor="n4b-test-governance",
        reason="test supersession",
        occurred_at="2026-09-12T00:03:00Z",
    )
    memory_repository, memory_ref = memory_fixture()
    memory_repository.supersede(
        memory_ref,
        actor="n4b-test-governance",
        reason="test supersession",
        occurred_at="2026-09-12T00:03:00Z",
    )
    source = CanonicalSemanticAuthoritySource(
        identity_resolver=IdentityResolver(identity_repository),
        memory_resolver=MemoryExperienceResolver(memory_repository),
    )
    assert (
        error_code(lambda: source.resolve_identity_frame(identity_ref))
        is CanonicalSemanticAuthorityErrorCode.REF_NOT_ADMITTED
    )
    assert (
        error_code(lambda: source.resolve_experience_frame(memory_ref))
        is CanonicalSemanticAuthorityErrorCode.REF_NOT_ADMITTED
    )


def test_b16_failures_never_return_fallback_frames() -> None:
    source = CanonicalSemanticAuthoritySource()
    for call in (
        lambda: source.resolve_identity_frame(IdentityRef("lineage", "v1")),
        lambda: source.resolve_experience_frame(
            MemoryExperienceRef("experience", "v1")
        ),
    ):
        assert error_code(call) is CanonicalSemanticAuthorityErrorCode.SOURCE_NOT_BOUND


def test_constructor_type_mismatch_fails_closed() -> None:
    with pytest.raises(CanonicalSemanticAuthoritySourceError) as identity_error:
        CanonicalSemanticAuthoritySource(identity_resolver=SubclassedIdentityResolver)
    assert (
        identity_error.value.code is CanonicalSemanticAuthorityErrorCode.TYPE_MISMATCH
    )
    with pytest.raises(CanonicalSemanticAuthoritySourceError) as memory_error:
        CanonicalSemanticAuthoritySource(memory_resolver=SubclassedMemoryResolver)
    assert memory_error.value.code is CanonicalSemanticAuthorityErrorCode.TYPE_MISMATCH


def test_b17_b18_static_authority_source_gate() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    imports = {
        alias.asname or alias.name.split(".")[-1]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert imports == {
        "annotations",
        "Enum",
        "Mapping",
        "IdentityRef",
        "IdentityRefNotFoundError",
        "IdentityResolver",
        "IdentityStatus",
        "MemoryExperienceRef",
        "MemoryExperienceRefNotFoundError",
        "MemoryExperienceResolver",
        "MemoryExperienceStatus",
        "EXPERIENCE_FRAME_SCHEMA_VERSION",
        "EXPERIENCE_PROJECTION_POLICY_ID",
        "EXPERIENCE_PROJECTION_POLICY_VERSION",
        "IDENTITY_FRAME_SCHEMA_VERSION",
        "ExperienceFrame",
        "ExperienceProjectionPolicy",
        "IdentityFrame",
        "PERSONA_PROJECTION_POLICY_ID",
        "PERSONA_PROJECTION_POLICY_VERSION",
        "PersonaProjectionPolicy",
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        names = []
        if isinstance(node.func, ast.Name):
            names.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            names.append(node.func.attr)
        assert not {"IdentityFrame", "ExperienceFrame"}.intersection(names)
    forbidden_tokens = {
        "store_candidate",
        "admit(",
        "supersede(",
        "retire(",
        "requests",
        "urllib",
        "httpx",
        "subprocess",
        "Provider",
        "Runtime",
        "tests.",
    }
    assert not forbidden_tokens.intersection(source_text.split())
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CanonicalSemanticAuthoritySource"
    )
    assert {
        node.name
        for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    } == {"resolve_identity_frame", "resolve_experience_frame"}

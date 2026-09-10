from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from julia_core.identity import (
    GovernedIdentity,
    IdentityAnchor,
    IdentityBoundary,
    IdentityContract,
    IdentityProvenance,
    IdentityRef,
    IdentityRefNotFoundError,
    IdentityRepository,
    IdentityResolver,
    IdentityValue,
    IdentityVersion,
    RelationshipRoleAnchor,
)
from julia_core.projection import PersonaProjectionPolicy


EFFECTIVE_BASE_SHA = "cd98d168ecc5a83a9628890687774d25a847c59f"


def contract(*, anchor: str = "Synthetic identity anchor") -> IdentityContract:
    return IdentityContract(
        identity_id="identity-synthetic-001",
        anchors=(IdentityAnchor(anchor_id="anchor-core", statement=anchor),),
        values=(IdentityValue(value_id="value-honesty", statement="Prefer truthful bounded claims."),),
        boundaries=(IdentityBoundary(boundary_id="boundary-no-fabrication", constraint="Do not fabricate lived experience."),),
        relationship_role_anchors=(
            RelationshipRoleAnchor(anchor_id="role-collaborator", relationship_id="relationship-synthetic", role="collaborator"),
        ),
    )


def version(version_id: str = "v1", *, anchor: str = "Synthetic identity anchor", predecessor: str | None = None) -> IdentityVersion:
    return IdentityVersion(
        contract=contract(anchor=anchor),
        lineage_id="lineage-synthetic-test",
        version_id=version_id,
        predecessor_version_id=predecessor,
        created_at="2026-09-10T00:00:00Z",
        provenance_refs=(
            IdentityProvenance(
                source_type="synthetic_fixture",
                source_ref="fixture://eng08/synthetic-identity",
                source_digest="b" * 64,
                admission_metadata=(("fixture", "ENG-08"),),
            ),
        ),
    )


def admitted_identity(anchor: str = "Synthetic identity anchor") -> GovernedIdentity:
    repository = IdentityRepository()
    candidate = repository.store_candidate(version(anchor=anchor))
    return repository.admit(
        candidate.ref,
        actor="synthetic-governance-test",
        reason="Synthetic admission fixture",
        occurred_at="2026-09-10T00:01:00Z",
    )


def project_admitted(anchor: str = "Synthetic identity anchor"):
    repository = IdentityRepository()
    candidate = repository.store_candidate(version(anchor=anchor))
    repository.admit(
        candidate.ref,
        actor="synthetic-governance-test",
        reason="Synthetic admission fixture",
        occurred_at="2026-09-10T00:01:00Z",
    )
    return PersonaProjectionPolicy().project_ref(candidate.ref, IdentityResolver(repository)), repository, candidate


def test_exact_admitted_ref_projects_deterministic_identity_frame() -> None:
    repository = IdentityRepository()
    candidate = repository.store_candidate(version())
    repository.admit(candidate.ref, actor="test", reason="admit", occurred_at="2026-09-10T00:01:00Z")
    resolver = IdentityResolver(repository)
    policy = PersonaProjectionPolicy()

    first = policy.project_ref(candidate.ref, resolver)
    second = policy.project_ref(candidate.ref, resolver)

    assert first.source_ref == candidate.ref
    assert first.source_digest == candidate.version.digest()
    assert first.source_status.value == "ADMITTED"
    assert first.canonical_serialization() == second.canonical_serialization()
    assert first.digest() == second.digest()


def test_unknown_exact_ref_fails_closed_without_latest_fallback() -> None:
    repository = IdentityRepository()
    candidate = repository.store_candidate(version())
    resolver = IdentityResolver(repository)

    with pytest.raises(IdentityRefNotFoundError):
        PersonaProjectionPolicy().project_ref(
            IdentityRef(lineage_id=candidate.version.lineage_id, version_id="missing"),
            resolver,
        )


@pytest.mark.parametrize(
    ("method", "expected_status"),
    [
        ("candidate", "CANDIDATE"),
        ("superseded", "SUPERSEDED"),
        ("retired", "RETIRED"),
    ],
)
def test_projection_preserves_lifecycle_without_promotion(method: str, expected_status: str) -> None:
    repository = IdentityRepository()
    candidate = repository.store_candidate(version())
    governed = candidate
    if method == "superseded":
        governed = repository.supersede(candidate.ref, actor="test", reason="newer version", occurred_at="2026-09-10T00:02:00Z")
    elif method == "retired":
        governed = repository.retire(candidate.ref, actor="test", reason="retired", occurred_at="2026-09-10T00:02:00Z")

    frame = PersonaProjectionPolicy().project_ref(candidate.ref, IdentityResolver(repository))

    assert frame.source_status.value == expected_status
    assert repository.resolve(candidate.ref).status.value == expected_status


def test_semantic_change_changes_frame_digest() -> None:
    policy = PersonaProjectionPolicy()
    first = project_admitted()[0]
    changed = project_admitted(anchor="Changed synthetic identity anchor")[0]

    assert first.digest() != changed.digest()
    assert first.anchors != changed.anchors


def test_projection_does_not_mutate_identity_version_or_invent_anchors() -> None:
    frame, repository, candidate = project_admitted()
    governed = repository.resolve(candidate.ref)
    source_digest = governed.version.digest()
    source_anchor = governed.version.contract.anchors[0].to_dict()

    assert governed.version.digest() == source_digest
    assert frame.anchors == (source_anchor,)
    assert frame.values == tuple(item.to_dict() for item in governed.version.contract.values)
    assert frame.boundaries == tuple(item.to_dict() for item in governed.version.contract.boundaries)
    assert frame.relationship_role_anchors == tuple(
        item.to_dict() for item in governed.version.contract.relationship_role_anchors
    )
    assert len(frame.anchors) == len(governed.version.contract.anchors)


def test_frame_contains_only_bounded_identity_fields() -> None:
    frame = project_admitted()[0]
    payload = json.dumps(frame.to_dict())

    expected_top_level = {
        "schema",
        "schema_version",
        "frame_kind",
        "projection",
        "source",
        "identity_id",
        "anchors",
        "values",
        "boundaries",
        "relationship_role_anchors",
        "provenance_refs",
    }
    assert set(frame.to_dict()) == expected_top_level
    for forbidden in (
        "autobiography",
        "episodic_memory",
        "conversation_body",
        "relationship_history",
        "causal_chain",
        "system_prompt",
        "runtime_prompt",
        "provider_instructions",
        "voice_instructions",
        "embedding",
    ):
        assert forbidden not in payload


def test_projection_package_has_no_legacy_or_authority_imports() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in Path("julia_core/projection").glob("*.py"))

    for forbidden in (
        "julia_core.persona",
        "julia_core.self_model",
        "julia_core.context_os",
        "julia_core.context_assembly",
        "julia_core.memory",
        "julia_core.experience",
        "julia_core.continuity",
        "julia_core.runtime",
        "julia_core.providers",
    ):
        assert forbidden not in source


def test_invalid_input_fails_closed() -> None:
    with pytest.raises(TypeError):
        PersonaProjectionPolicy().project({"status": "ADMITTED"})


def test_fabricated_admitted_governed_identity_cannot_project() -> None:
    repository = IdentityRepository()
    candidate = repository.store_candidate(version())
    fabricated = GovernedIdentity(
        version=candidate.version,
        status=candidate.status.__class__("ADMITTED"),
        governance_events=(),
    )

    with pytest.raises(TypeError, match="project_ref"):
        PersonaProjectionPolicy().project(fabricated)


def test_identity_frame_nested_payload_is_deeply_immutable() -> None:
    frame, repository, candidate = project_admitted()
    governed = repository.resolve(candidate.ref)
    original_serialization = frame.canonical_serialization()
    original_digest = frame.digest()
    source_digest = governed.version.digest()

    with pytest.raises(TypeError):
        frame.anchors[0]["statement"] = "mutated"
    with pytest.raises(TypeError):
        frame.provenance_refs[0]["admission_metadata"]["fixture"] = "mutated"

    outward = frame.to_dict()
    outward["anchors"][0]["statement"] = "mutated outward"
    outward["provenance_refs"][0]["admission_metadata"]["fixture"] = "mutated outward"

    assert frame.canonical_serialization() == original_serialization
    assert frame.digest() == original_digest
    assert governed.version.digest() == source_digest
    assert frame.anchors[0]["statement"] == "Synthetic identity anchor"
    assert frame.provenance_refs[0]["admission_metadata"]["fixture"] == "ENG-08"


def test_changed_scope_is_limited_to_authorized_eng08_paths() -> None:
    changed = subprocess.run(
        ["git", "diff", "--name-only", EFFECTIVE_BASE_SHA],
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
        if path.startswith(("julia_core/projection/", "tests/projection/", "tests/identity/", "docs/mira_persona_architecture/", "artifacts/mira_persona_architecture/"))
    )
    allowed = (
        "julia_core/identity/",
        "julia_core/projection/",
        "tests/projection/",
        "tests/identity/",
        "julia_core/memory_experience/",
        "tests/memory_experience/",
        "docs/mira_persona_architecture/",
        "artifacts/mira_persona_architecture/",
    )

    assert changed
    assert all(path.startswith(allowed) for path in changed)

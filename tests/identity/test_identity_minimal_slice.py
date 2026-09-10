from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from julia_core.identity import (
    IdentityAnchor,
    IdentityBoundary,
    IdentityConflictError,
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


BASE_SHA = "5c704ce193ac0c1ceb48ea5e7cc626437e4ddf60"


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
                source_ref="fixture://eng07/synthetic-identity",
                source_digest="a" * 64,
                admission_metadata=(("fixture", "ENG-07"),),
            ),
        ),
    )


def test_candidate_store_exact_resolution_and_admission() -> None:
    repository = IdentityRepository()
    candidate = repository.store_candidate(version())

    assert candidate.status.value == "CANDIDATE"

    admitted = repository.admit(
        candidate.ref,
        actor="synthetic-governance-test",
        reason="Synthetic admission fixture",
        occurred_at="2026-09-10T00:01:00Z",
    )

    assert admitted.status.value == "ADMITTED"
    assert admitted.version == candidate.version
    assert repository.resolve(candidate.ref).digest == candidate.digest
    assert IdentityResolver(repository).resolve(candidate.ref).version.version_id == "v1"


def test_unknown_exact_reference_fails_closed_without_latest_fallback() -> None:
    repository = IdentityRepository()
    stored = repository.store_candidate(version())

    with pytest.raises(IdentityRefNotFoundError):
        repository.resolve(IdentityRef(lineage_id=stored.version.lineage_id, version_id="missing"))


def test_identity_ref_is_deterministic_and_exact() -> None:
    first = IdentityRef(lineage_id="lineage-a", version_id="v1")
    second = IdentityRef(lineage_id="lineage-a", version_id="v1")

    assert first == second
    assert first.uri == second.uri == "identity://lineage-a/v1"
    assert first.to_dict() == second.to_dict()


def test_duplicate_conflicting_version_is_rejected() -> None:
    repository = IdentityRepository()
    repository.store_candidate(version())

    with pytest.raises(IdentityConflictError):
        repository.store_candidate(version(anchor="Changed semantic anchor"))


def test_digest_is_deterministic_and_semantic_change_changes_it() -> None:
    same_a = version()
    same_b = version()

    assert same_a.digest() == same_b.digest()
    assert same_a.digest() != version(anchor="Changed semantic anchor").digest()


def test_lineage_predecessor_and_immutability() -> None:
    repository = IdentityRepository()
    first = repository.store_candidate(version())
    repository.admit(first.ref, actor="test", reason="admit", occurred_at="2026-09-10T00:01:00Z")
    first_digest = first.digest

    successor = repository.store_candidate(version("v2", predecessor="v1"))
    repository.admit(successor.ref, actor="test", reason="admit successor", occurred_at="2026-09-10T00:02:00Z")
    repository.supersede(first.ref, actor="test", reason="superseded by v2", occurred_at="2026-09-10T00:03:00Z")

    old = repository.resolve(first.ref)
    assert old.version.predecessor_version_id is None
    assert successor.version.predecessor_version_id == "v1"
    assert old.digest == first_digest
    assert old.status.value == "SUPERSEDED"
    assert repository.resolve(successor.ref).status.value == "ADMITTED"


def test_identity_schema_excludes_memory_and_runtime_payload_fields() -> None:
    payload = json.dumps(version().to_dict())

    for forbidden in (
        "autobiography",
        "episodic_memory",
        "conversation_body",
        "system_prompt",
        "runtime_prompt",
        "provider_instructions",
        "embedding",
    ):
        assert forbidden not in payload


def test_identity_package_has_no_runtime_authority_imports() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in Path("julia_core/identity").glob("*.py"))

    for forbidden in (
        "julia_core.runtime",
        "julia_core.providers",
        "julia_core.context_os",
        "julia_core.context_assembly",
        "julia_core.memory",
        "julia_core.continuity",
        "julia_core.persona.identity_kernel",
        "julia_core.self_model",
    ):
        assert forbidden not in source


def test_changed_scope_is_limited_to_authorized_eng07_paths() -> None:
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
        if path.startswith(("julia_core/identity/", "tests/identity/", "docs/mira_persona_architecture/", "artifacts/mira_persona_architecture/"))
    )
    allowed = (
        "julia_core/identity/",
        "tests/identity/",
        "docs/mira_persona_architecture/",
        "artifacts/mira_persona_architecture/",
    )

    assert changed
    assert all(path.startswith(allowed) for path in changed)


def test_legacy_and_runtime_scope_remains_unchanged_from_delegation_base() -> None:
    changed = subprocess.run(
        ["git", "diff", "--name-only", BASE_SHA],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    protected = ("julia_core/persona/", "julia_core/self_model/", "julia_core/runtime/", "julia_core/providers/", "julia_core/context_os/", "julia_core/memory/", "julia_core/continuity/", "julia_core/context_assembly/")

    assert not any(path.startswith(protected) for path in changed)

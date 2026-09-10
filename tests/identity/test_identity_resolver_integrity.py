from __future__ import annotations

import pytest

from julia_core.identity import (
    IdentityAnchor,
    IdentityContract,
    IdentityProvenance,
    IdentityRef,
    IdentityRefNotFoundError,
    IdentityRepository,
    IdentityResolver,
    IdentityValue,
    IdentityVersion,
)
from julia_core.projection import PersonaProjectionPolicy


class FakeRepository:
    def resolve(self, ref):
        raise AssertionError("fake repository must not be reachable")


class ForgedResolver(IdentityResolver):
    def resolve(self, ref):
        return self._repository.resolve(ref)


def admitted_repository():
    repository = IdentityRepository()
    candidate = repository.store_candidate(
        IdentityVersion(
            contract=IdentityContract(
                identity_id="identity-synthetic-integrity",
                anchors=(IdentityAnchor("anchor-core", "Synthetic identity anchor"),),
                values=(IdentityValue("value-core", "Synthetic stable value"),),
                boundaries=(),
                relationship_role_anchors=(),
            ),
            lineage_id="lineage-synthetic-integrity",
            version_id="v1",
            predecessor_version_id=None,
            created_at="2026-09-10T00:00:00Z",
            provenance_refs=(
                IdentityProvenance(
                    source_type="synthetic_fixture",
                    source_ref="fixture://eng09r3/synthetic-identity",
                    source_digest="a" * 64,
                ),
            ),
        )
    )
    repository.admit(
        candidate.ref,
        actor="synthetic-governance-test",
        reason="Synthetic admission fixture",
        occurred_at="2026-09-10T00:01:00Z",
    )
    return repository, candidate


def test_resolver_rejects_fake_repository_before_projection() -> None:
    with pytest.raises(TypeError, match="exact IdentityRepository"):
        IdentityResolver(FakeRepository())


def test_projection_rejects_forged_resolver_subclass() -> None:
    repository, candidate = admitted_repository()
    resolver = ForgedResolver(repository)

    with pytest.raises(TypeError, match="exact IdentityResolver"):
        PersonaProjectionPolicy().project_ref(candidate.ref, resolver)


def test_exact_repository_resolver_and_exact_ref_projection_succeed() -> None:
    repository, candidate = admitted_repository()

    frame = PersonaProjectionPolicy().project_ref(
        candidate.ref, IdentityResolver(repository)
    )

    assert frame.source_ref == candidate.ref
    assert frame.source_digest == candidate.version.digest()


def test_unknown_exact_ref_still_fails_closed() -> None:
    repository, candidate = admitted_repository()

    with pytest.raises(IdentityRefNotFoundError):
        PersonaProjectionPolicy().project_ref(
            IdentityRef(candidate.version.lineage_id, "missing"),
            IdentityResolver(repository),
        )


def test_direct_governed_identity_projection_remains_forbidden() -> None:
    repository, candidate = admitted_repository()

    with pytest.raises(TypeError, match="project_ref"):
        PersonaProjectionPolicy().project(repository.resolve(candidate.ref))

from __future__ import annotations

import pytest

from julia_core.identity import (
    IdentityAnchor,
    IdentityContract,
    IdentityProvenance,
    IdentityRef,
    IdentityRepository,
    IdentityValue,
    IdentityVersion,
)


class SubclassedIdentityRef(IdentityRef):
    pass


def stored_repository():
    repository = IdentityRepository()
    stored = repository.store_candidate(
        IdentityVersion(
            contract=IdentityContract(
                identity_id="identity-synthetic-boundary",
                anchors=(IdentityAnchor("anchor-core", "Synthetic identity anchor"),),
                values=(IdentityValue("value-core", "Synthetic stable value"),),
                boundaries=(),
                relationship_role_anchors=(),
            ),
            lineage_id="lineage-synthetic-boundary",
            version_id="v1",
            predecessor_version_id=None,
            created_at="2026-09-10T00:00:00Z",
            provenance_refs=(
                IdentityProvenance(
                    source_type="synthetic_fixture",
                    source_ref="fixture://eng09r5/synthetic-identity",
                    source_digest="a" * 64,
                ),
            ),
        )
    )
    return repository, stored


@pytest.mark.parametrize("transition", ["admit", "supersede", "retire"])
def test_identity_lifecycle_rejects_ref_subclasses(transition) -> None:
    repository, stored = stored_repository()
    forged = SubclassedIdentityRef(stored.ref.lineage_id, stored.ref.version_id)
    arguments = {
        "actor": "test",
        "reason": "synthetic transition",
        "occurred_at": "2026-09-10T00:01:00Z",
    }

    with pytest.raises(TypeError, match="exact IdentityRef"):
        getattr(repository, transition)(forged, **arguments)


def test_identity_governance_event_retains_exact_canonical_ref() -> None:
    repository, stored = stored_repository()
    repository.admit(
        stored.ref,
        actor="test",
        reason="synthetic admission",
        occurred_at="2026-09-10T00:01:00Z",
    )

    assert type(repository.resolve(stored.ref).governance_events[-1].target) is IdentityRef

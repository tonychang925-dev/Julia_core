from __future__ import annotations

import pytest

from julia_core.identity import (
    IdentityAnchor,
    IdentityContract,
    IdentityProvenance,
    IdentityRepository,
    IdentityValue,
    IdentityVersion,
)


class FakeIdentityVersion:
    def __init__(self, version):
        self.ref = version.ref
        self.digest = version.digest
        self.lineage_id = version.lineage_id
        self.contract = version.contract
        self.created_at = version.created_at


class SubclassedIdentityVersion(IdentityVersion):
    pass


def version():
    return IdentityVersion(
        contract=IdentityContract(
            identity_id="identity-synthetic-input",
            anchors=(IdentityAnchor("anchor-core", "Synthetic identity anchor"),),
            values=(IdentityValue("value-core", "Synthetic stable value"),),
            boundaries=(),
            relationship_role_anchors=(),
        ),
        lineage_id="lineage-synthetic-input",
        version_id="v1",
        predecessor_version_id=None,
        created_at="2026-09-10T00:00:00Z",
        provenance_refs=(
            IdentityProvenance(
                source_type="synthetic_fixture",
                source_ref="fixture://eng09r4/synthetic-identity",
                source_digest="a" * 64,
            ),
        ),
    )


def test_identity_repository_rejects_non_exact_version_inputs() -> None:
    canonical = version()
    repository = IdentityRepository()

    with pytest.raises(TypeError, match="exact IdentityVersion"):
        repository.store_candidate(FakeIdentityVersion(canonical))
    with pytest.raises(TypeError, match="exact IdentityVersion"):
        repository.store_candidate(
            SubclassedIdentityVersion(
                contract=canonical.contract,
                lineage_id=canonical.lineage_id,
                version_id=canonical.version_id,
                predecessor_version_id=canonical.predecessor_version_id,
                created_at=canonical.created_at,
                provenance_refs=canonical.provenance_refs,
            )
        )


def test_exact_identity_version_stores_admits_and_resolves() -> None:
    repository = IdentityRepository()
    candidate = repository.store_candidate(version())
    repository.admit(
        candidate.ref,
        actor="synthetic-governance-test",
        reason="Synthetic admission fixture",
        occurred_at="2026-09-10T00:01:00Z",
    )

    assert repository.resolve(candidate.ref).status.value == "ADMITTED"


@pytest.mark.parametrize(
    "metadata",
    [
        (("case", 1),),
        ((1, "case"),),
        (("same", object()),),
    ],
)
def test_identity_metadata_rejects_non_string_keys_and_values(metadata) -> None:
    with pytest.raises(ValueError, match="key/value string pairs"):
        IdentityProvenance(
            source_type="synthetic_fixture",
            source_ref="fixture://eng09r4/synthetic-identity",
            source_digest="a" * 64,
            admission_metadata=metadata,
        )


def test_identity_metadata_duplicate_keys_remain_rejected() -> None:
    with pytest.raises(ValueError, match="keys must be unique"):
        IdentityProvenance(
            source_type="synthetic_fixture",
            source_ref="fixture://eng09r4/synthetic-identity",
            source_digest="a" * 64,
            admission_metadata=(("same", "first"), ("same", "second")),
        )

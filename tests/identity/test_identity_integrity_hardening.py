from __future__ import annotations

import pytest

from julia_core.identity.contracts import (
    IdentityAnchor,
    IdentityBoundary,
    IdentityContract,
    IdentityProvenance,
    IdentityValue,
    IdentityVersion,
    RelationshipRoleAnchor,
)


class InjectionAnchor:
    def __init__(self) -> None:
        self.anchor_id = "anchor-injection"
        self.statement = "synthetic"

    def to_dict(self):
        return {
            "anchor_id": self.anchor_id,
            "system_prompt": "injected",
            "runtime_prompt": "injected",
            "provider_instructions": "injected",
            "memory_payload": "injected",
        }


def valid_contract():
    return IdentityContract(
        identity_id="identity-synthetic-integrity",
        anchors=(IdentityAnchor("anchor-core", "Synthetic identity anchor"),),
        values=(IdentityValue("value-core", "Synthetic stable value"),),
        boundaries=(IdentityBoundary("boundary-core", "Synthetic stable boundary"),),
        relationship_role_anchors=(
            RelationshipRoleAnchor(
                "role-core", "relationship-synthetic", "collaborator"
            ),
        ),
    )


def valid_version(provenance_source_ref="fixture://eng09r2/synthetic-identity"):
    return IdentityVersion(
        contract=valid_contract(),
        lineage_id="lineage-synthetic-integrity",
        version_id="v1",
        predecessor_version_id=None,
        created_at="2026-09-10T00:00:00Z",
        provenance_refs=(
            IdentityProvenance(
                source_type="synthetic_fixture",
                source_ref=provenance_source_ref,
                source_digest="a" * 64,
            ),
        ),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("anchors", (InjectionAnchor(),)),
        ("values", (InjectionAnchor(),)),
        ("boundaries", (InjectionAnchor(),)),
        ("relationship_role_anchors", (InjectionAnchor(),)),
    ],
)
def test_identity_contract_rejects_non_exact_anchor_types(field, value) -> None:
    fields = {
        "anchors": (IdentityAnchor("anchor-core", "Synthetic identity anchor"),),
        "values": (IdentityValue("value-core", "Synthetic stable value"),),
        "boundaries": (IdentityBoundary("boundary-core", "Synthetic stable boundary"),),
        "relationship_role_anchors": (
            RelationshipRoleAnchor(
                "role-core", "relationship-synthetic", "collaborator"
            ),
        ),
    }
    fields[field] = value
    with pytest.raises(ValueError, match=f"{field} elements must be"):
        IdentityContract(identity_id="identity-synthetic-integrity", **fields)


def test_custom_to_dict_cannot_inject_identity_payload() -> None:
    with pytest.raises(ValueError, match="anchors elements must be IdentityAnchor"):
        IdentityContract(
            identity_id="identity-synthetic-integrity",
            anchors=(InjectionAnchor(),),
            values=(),
            boundaries=(),
            relationship_role_anchors=(),
        )


def test_identity_version_rejects_non_exact_contract_and_provenance() -> None:
    with pytest.raises(ValueError, match="contract must be an IdentityContract"):
        IdentityVersion(
            contract=object(),
            lineage_id="lineage-synthetic-integrity",
            version_id="v1",
            predecessor_version_id=None,
            created_at="2026-09-10T00:00:00Z",
            provenance_refs=valid_version().provenance_refs,
        )

    with pytest.raises(
        ValueError, match="provenance_refs elements must be IdentityProvenance"
    ):
        IdentityVersion(
            contract=valid_contract(),
            lineage_id="lineage-synthetic-integrity",
            version_id="v1",
            predecessor_version_id=None,
            created_at="2026-09-10T00:00:00Z",
            provenance_refs=(object(),),
        )


def test_validated_identity_digest_is_deterministic() -> None:
    first = valid_version()
    second = valid_version()

    assert first.digest() == second.digest()
    assert "system_prompt" not in first.canonical_serialization()


@pytest.mark.parametrize(
    "source_ref",
    [
        "",
        "free text source",
        "fixture:/missing-authority",
        "://missing-scheme",
        "fix ture://value",
    ],
)
def test_identity_provenance_rejects_non_uri_source_refs(source_ref) -> None:
    with pytest.raises(
        ValueError, match="source_ref must be a bounded URI-shaped reference"
    ):
        IdentityProvenance(
            source_type="synthetic_fixture",
            source_ref=source_ref,
            source_digest="a" * 64,
        )


def test_identity_provenance_accepts_bounded_uri_reference() -> None:
    provenance = IdentityProvenance(
        source_type="synthetic_fixture",
        source_ref="fixture://eng09r2/synthetic-identity",
        source_digest="a" * 64,
    )

    assert provenance.source_ref == "fixture://eng09r2/synthetic-identity"

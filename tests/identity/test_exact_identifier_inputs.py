from __future__ import annotations

import pytest

from julia_core.identity import (
    IdentityRepository,
    IdentityResolver,
    IdentityAnchor,
    IdentityBoundary,
    IdentityRef,
    IdentityValue,
    RelationshipRoleAnchor,
)
from julia_core.identity.contracts import IdentityGovernanceEvent


class SpoofString(str):
    pass


class MutableSpoofString(str):
    def __init__(self, value: str) -> None:
        self.backing = list(value)

    def mutate(self) -> None:
        self.backing.append("!")


def test_identity_anchor_rejects_string_subclass_identifier() -> None:
    with pytest.raises(ValueError, match="anchor_id must be an exact built-in string"):
        IdentityAnchor(
            anchor_id=SpoofString("anchor-core"), statement="Synthetic anchor"
        )


def test_identity_ref_rejects_string_subclass_identifier_before_key_construction() -> (
    None
):
    with pytest.raises(ValueError, match="lineage_id must be an exact built-in string"):
        IdentityRef(lineage_id=SpoofString("lineage-synthetic"), version_id="v1")
    with pytest.raises(ValueError, match="version_id must be an exact built-in string"):
        IdentityRef(lineage_id="lineage-synthetic", version_id=SpoofString("v1"))


def test_plain_built_in_identity_identifiers_remain_valid() -> None:
    ref = IdentityRef(lineage_id="lineage-synthetic", version_id="v1")

    assert type(ref.lineage_id) is str
    assert type(ref.version_id) is str


@pytest.mark.parametrize(
    ("factory", "field_name"),
    [
        (
            lambda value: IdentityAnchor(anchor_id="anchor-synthetic", statement=value),
            "statement",
        ),
        (
            lambda value: IdentityValue(value_id="value-synthetic", statement=value),
            "statement",
        ),
        (
            lambda value: IdentityBoundary(
                boundary_id="boundary-synthetic", constraint=value
            ),
            "constraint",
        ),
        (
            lambda value: RelationshipRoleAnchor(
                anchor_id="role-synthetic",
                relationship_id="relationship-synthetic",
                role=value,
            ),
            "role",
        ),
        (
            lambda value: IdentityGovernanceEvent(
                event_id="event-synthetic",
                target=IdentityRef(lineage_id="lineage-synthetic", version_id="v1"),
                status="ADMITTED",
                actor="synthetic-governance-test",
                reason=value,
                occurred_at="2026-09-11T00:00:00Z",
            ),
            "reason",
        ),
    ],
)
@pytest.mark.parametrize(
    "spoof",
    [
        SpoofString("synthetic canonical text"),
        MutableSpoofString("synthetic"),
        ["spoof"],
    ],
)
def test_identity_canonical_text_rejects_non_exact_strings(
    factory, field_name, spoof
) -> None:
    with pytest.raises(
        ValueError, match=f"{field_name} must be an exact built-in string"
    ):
        factory(spoof)


def test_identity_canonical_text_rejection_cannot_mutate_valid_payload() -> None:
    anchor = IdentityAnchor(
        anchor_id="anchor-synthetic", statement="Synthetic identity anchor"
    )
    payload = anchor.to_dict()
    spoof = MutableSpoofString("Synthetic identity anchor")

    with pytest.raises(ValueError, match="statement must be an exact built-in string"):
        IdentityAnchor(anchor_id="anchor-synthetic", statement=spoof)
    spoof.mutate()

    assert anchor.to_dict() == payload


def test_exact_identity_text_remains_valid_and_deterministic() -> None:
    anchors = [
        IdentityAnchor(anchor_id="anchor-synthetic", statement="Synthetic anchor"),
        IdentityValue(value_id="value-synthetic", statement="Synthetic value"),
        IdentityBoundary(
            boundary_id="boundary-synthetic", constraint="Synthetic boundary"
        ),
        RelationshipRoleAnchor(
            anchor_id="role-synthetic",
            relationship_id="relationship-synthetic",
            role="Synthetic role",
        ),
    ]

    assert all(item.to_dict() == item.to_dict() for item in anchors)


def test_identity_resolver_repository_binding_cannot_be_rebound() -> None:
    repository = IdentityRepository()
    resolver = IdentityResolver(repository)

    with pytest.raises(TypeError, match="repository binding is immutable"):
        resolver._repository = object()
    with pytest.raises(TypeError, match="repository binding is immutable"):
        resolver._repository = IdentityRepository()
    with pytest.raises(TypeError, match="repository binding is immutable"):
        del resolver._repository

    assert resolver._repository is repository
    assert not hasattr(resolver, "__dict__")


def test_forged_identity_repository_substitution_fails_resolve_revalidation() -> None:
    repository = IdentityRepository()
    resolver = IdentityResolver(repository)
    object.__setattr__(resolver, "_repository", object())

    with pytest.raises(TypeError, match="repository binding is invalid"):
        resolver.resolve(IdentityRef(lineage_id="lineage-synthetic", version_id="v1"))

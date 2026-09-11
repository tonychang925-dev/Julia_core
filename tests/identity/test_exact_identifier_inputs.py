from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from julia_core.identity import (
    GovernedIdentity,
    IdentityRepository,
    IdentityResolver,
    IdentityAnchor,
    IdentityBoundary,
    IdentityContract,
    IdentityProvenance,
    IdentityRef,
    IdentityStatus,
    IdentityVersion,
    IdentityValue,
    RelationshipRoleAnchor,
)
from julia_core.identity.contracts import IdentityGovernanceEvent
from julia_core.projection import PersonaProjectionPolicy


class SpoofString(str):
    pass


class MutableSpoofString(str):
    def __init__(self, value: str) -> None:
        self.backing = list(value)

    def mutate(self) -> None:
        self.backing.append("!")


class ParsingSpoofSourceRef(str):
    def lstrip(self, *args: object, **kwargs: object) -> str:
        return "fixture://eng10r4/valid-source"


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


def test_identity_instance_resolve_shadow_cannot_fabricate_projection() -> None:
    repository = IdentityRepository()
    version = IdentityVersion(
        contract=IdentityContract(
            identity_id="identity-synthetic",
            anchors=(
                IdentityAnchor(
                    anchor_id="anchor-synthetic", statement="Synthetic anchor"
                ),
            ),
            values=(),
            boundaries=(),
            relationship_role_anchors=(),
        ),
        lineage_id="lineage-synthetic",
        version_id="v1",
        predecessor_version_id=None,
        created_at="2026-09-11T00:00:00Z",
        provenance_refs=(
            IdentityProvenance(
                source_type="synthetic_fixture",
                source_ref="fixture://eng10r4/synthetic-identity",
                source_digest="a" * 64,
            ),
        ),
    )
    candidate = repository.store_candidate(version)
    resolver = IdentityResolver(repository)
    with pytest.raises(TypeError, match="IdentityRepository fields are immutable"):
        repository.resolve = lambda ref: GovernedIdentity(
            version=version,
            status=IdentityStatus.ADMITTED,
            governance_events=(),
        )

    resolved = resolver.resolve(candidate.ref)
    frame = PersonaProjectionPolicy().project_ref(candidate.ref, resolver)

    assert resolved.status is IdentityStatus.CANDIDATE
    assert frame.source_status is IdentityStatus.CANDIDATE


def test_identity_governance_containers_reject_direct_mutation() -> None:
    repository = IdentityRepository()
    version = IdentityVersion(
        contract=IdentityContract(
            identity_id="identity-synthetic",
            anchors=(
                IdentityAnchor(
                    anchor_id="anchor-synthetic", statement="Synthetic anchor"
                ),
            ),
            values=(),
            boundaries=(),
            relationship_role_anchors=(),
        ),
        lineage_id="lineage-synthetic",
        version_id="v1",
        predecessor_version_id=None,
        created_at="2026-09-11T00:00:00Z",
        provenance_refs=(
            IdentityProvenance(
                source_type="synthetic_fixture",
                source_ref="fixture://eng10r5/synthetic-identity",
                source_digest="a" * 64,
            ),
        ),
    )
    candidate = repository.store_candidate(version)
    before = repository.resolve(candidate.ref).to_dict()

    with pytest.raises(TypeError, match="IdentityRepository fields are immutable"):
        repository._versions = {}
    with pytest.raises(TypeError, match="IdentityRepository fields are immutable"):
        repository._events = {}
    with pytest.raises(TypeError):
        repository._versions[candidate.ref] = version
    with pytest.raises(TypeError):
        repository._events[candidate.ref] = ()
    with pytest.raises(AttributeError):
        repository._events[candidate.ref].append(object())

    assert not hasattr(repository, "_replace_events")
    assert not hasattr(repository, "_replace_version")
    with pytest.raises(AttributeError):
        repository._replace_events(candidate.ref, object())
    with pytest.raises(AttributeError):
        repository._replace_version(candidate.ref, version)
    with pytest.raises(AttributeError):
        repository._append_event(
            candidate.ref,
            IdentityStatus.ADMITTED,
            actor="synthetic-governance-test",
            reason="Synthetic admission",
            occurred_at="2026-09-11T00:01:00Z",
            allowed_from={IdentityStatus.CANDIDATE},
            event_kind="admission",
        )

    assert repository.resolve(candidate.ref).to_dict() == before
    assert repository.resolve(candidate.ref).status is IdentityStatus.CANDIDATE

    admitted = repository.admit(
        candidate.ref,
        actor="synthetic-governance-test",
        reason="Synthetic admission",
        occurred_at="2026-09-11T00:01:00Z",
    )

    assert admitted.status is IdentityStatus.ADMITTED
    assert len(repository.resolve(candidate.ref).governance_events) == 2


@pytest.mark.parametrize(
    "spoof",
    [
        SpoofString("fixture://eng10r4/source"),
        MutableSpoofString("fixture://eng10r4/source"),
        ParsingSpoofSourceRef("not-a-uri"),
        pytest.param(MagicMock(spec=str), id="proxy"),
    ],
)
def test_identity_source_ref_rejects_non_exact_strings_before_parsing(spoof) -> None:
    with pytest.raises(ValueError, match="source_ref must be an exact built-in string"):
        IdentityProvenance(
            source_type="synthetic_fixture",
            source_ref=spoof,
            source_digest="a" * 64,
        )


def test_exact_identity_source_ref_remains_valid_and_cannot_diverge() -> None:
    def version() -> IdentityVersion:
        return IdentityVersion(
            contract=IdentityContract(
                identity_id="identity-synthetic",
                anchors=(
                    IdentityAnchor(
                        anchor_id="anchor-synthetic", statement="Synthetic anchor"
                    ),
                ),
                values=(),
                boundaries=(),
                relationship_role_anchors=(),
            ),
            lineage_id="lineage-synthetic",
            version_id="v1",
            predecessor_version_id=None,
            created_at="2026-09-11T00:00:00Z",
            provenance_refs=(
                IdentityProvenance(
                    source_type="synthetic_fixture",
                    source_ref="fixture://eng10r4/synthetic-identity",
                    source_digest="a" * 64,
                ),
            ),
        )

    valid_version = version()
    payload = valid_version.canonical_payload()
    digest = valid_version.digest()
    spoof = MutableSpoofString("not-a-uri")

    with pytest.raises(ValueError, match="source_ref must be an exact built-in string"):
        IdentityProvenance(
            source_type="synthetic_fixture",
            source_ref=spoof,
            source_digest="a" * 64,
        )
    spoof.mutate()

    assert valid_version.canonical_payload() == payload
    assert valid_version.digest() == digest
    assert version().digest() == digest

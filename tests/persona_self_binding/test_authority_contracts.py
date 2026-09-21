import pytest

from julia_core.persona_self_binding import (
    AuthorityFamily,
    AuthorityReference,
    ExecutionSubstratePolicy,
    GovernanceEventType,
    GovernanceProvenanceEvent,
    IdentityAssertionDisposition,
    IdentityAuthorityAssertion,
    IntegrityContract,
    PersonaSelfBinding,
    PersonaSelfBindingContractError,
    PersonaSelfBindingErrorCode,
    PersonaSelfBindingLifecycle,
    RelationshipAuthority,
    RelationshipAuthorityState,
    SupersessionContract,
)


DIGEST = "a" * 64


def authority(family: AuthorityFamily, authority_id: str) -> AuthorityReference:
    return AuthorityReference(
        authority_type=family,
        authority_id=authority_id,
        source_digest=DIGEST,
        projected_digest=None,
    )


def provenance(event_type: GovernanceEventType) -> GovernanceProvenanceEvent:
    return GovernanceProvenanceEvent(
        event_id="event-1",
        event_type=event_type,
        actor="owner-governance",
        reason="owner reviewed contract",
        occurred_at="2026-09-20T00:00:00Z",
    )


def binding(
    *,
    binding_version: str = "v1",
    predecessor_binding_id: str | None = None,
    predecessor_binding_version: str | None = None,
    lifecycle: PersonaSelfBindingLifecycle = PersonaSelfBindingLifecycle.DRAFT,
    relationship: RelationshipAuthority | None = None,
) -> PersonaSelfBinding:
    return PersonaSelfBinding(
        schema_version="julia_core.persona_self_binding.v1",
        binding_id="persona-self-binding",
        persona_self_id="persona-self",
        identity_authority=authority(
            AuthorityFamily.IDENTITY_FRAME_SET, "identity-set"
        ),
        experience_authority=authority(
            AuthorityFamily.EXPERIENCE_FRAME_SET, "experience-set"
        ),
        relationship_authority=relationship
        or RelationshipAuthority(RelationshipAuthorityState.ABSENT, None),
        execution_substrate_policy=ExecutionSubstratePolicy(),
        binding_version=binding_version,
        predecessor_binding_id=predecessor_binding_id,
        predecessor_binding_version=predecessor_binding_version,
        lineage_id="persona-self-lineage",
        lifecycle_status=lifecycle,
        supersession=SupersessionContract(None, None),
        governance_provenance=(provenance(GovernanceEventType.PROPOSE_BINDING),),
        integrity=IntegrityContract("UTF8_JSON_SORTED_KEYS_COMPACT", "sha256"),
    )


def contract_error(call) -> PersonaSelfBindingErrorCode:
    with pytest.raises(PersonaSelfBindingContractError) as error:
        call()
    return error.value.code


def test_minimal_schema_deterministic_round_trip_and_equality() -> None:
    first = binding()
    second = binding()
    assert first == second
    assert first.canonical_serialization() == second.canonical_serialization()
    assert first.digest() == second.digest()
    assert PersonaSelfBinding.from_mapping(first.to_dict()) == first
    assert first.verify() is True
    assert set(first.to_dict()) == {
        "schema_version",
        "binding_id",
        "persona_self_id",
        "identity_authority",
        "experience_authority",
        "relationship_authority",
        "execution_substrate_policy",
        "binding_version",
        "predecessor_binding_version",
        "predecessor_binding_id",
        "lineage_id",
        "lifecycle_status",
        "supersession",
        "governance_provenance",
        "integrity",
    }


@pytest.mark.parametrize(
    "state",
    list(PersonaSelfBindingLifecycle),
)
def test_lifecycle_is_closed_and_exact(state: PersonaSelfBindingLifecycle) -> None:
    assert binding(lifecycle=state).lifecycle_status is state
    assert (
        contract_error(lambda: binding(lifecycle=state.value))  # type: ignore[arg-type]
        is PersonaSelfBindingErrorCode.PSB_LIFECYCLE_INVALID
    )


def test_governance_event_is_closed_and_exact() -> None:
    for event_type in GovernanceEventType:
        assert provenance(event_type).event_type is event_type
    assert (
        contract_error(lambda: provenance("USER_UTTERANCE"))  # type: ignore[arg-type]
        is PersonaSelfBindingErrorCode.PSB_GOVERNANCE_EVENT_INVALID
    )


@pytest.mark.parametrize(
    "field",
    ["provider_id", "model_id", "transport_endpoint", "runtime_token"],
)
def test_provider_identity_is_forbidden_in_durable_contract(field: str) -> None:
    payload = binding().to_dict()
    payload[field] = "forbidden"
    assert (
        contract_error(lambda: PersonaSelfBinding.from_mapping(payload))
        is PersonaSelfBindingErrorCode.PSB_PROVIDER_FIELD_FORBIDDEN
    )
    policy = binding().execution_substrate_policy
    assert policy.provider_is_persona_self is False
    assert policy.provider_neutral is True
    assert policy.provider_special_cases == ()


def test_relationship_tri_state_is_not_interchangeable() -> None:
    absent = RelationshipAuthority(RelationshipAuthorityState.ABSENT, None)
    empty = RelationshipAuthority(RelationshipAuthorityState.EXPLICITLY_EMPTY, None)
    bound = RelationshipAuthority(
        RelationshipAuthorityState.ADMITTED_BOUND,
        authority(AuthorityFamily.RELATIONSHIP_FRAME_SET, "relationship-set"),
    )
    assert absent != empty
    assert absent.to_dict() != empty.to_dict()
    assert bound.authority is not None
    assert (
        contract_error(
            lambda: RelationshipAuthority(
                RelationshipAuthorityState.ABSENT,
                authority(AuthorityFamily.RELATIONSHIP_FRAME_SET, "relationship-set"),
            )
        )
        is PersonaSelfBindingErrorCode.PSB_RELATIONSHIP_STATE_INVALID
    )
    assert (
        contract_error(
            lambda: RelationshipAuthority(
                RelationshipAuthorityState.ADMITTED_BOUND, None
            )
        )
        is PersonaSelfBindingErrorCode.PSB_RELATIONSHIP_STATE_INVALID
    )


def test_digest_is_semantic_and_provider_independent() -> None:
    base = binding()
    changed = binding(lifecycle=PersonaSelfBindingLifecycle.GOVERNANCE_REVIEW)
    assert base.digest() != changed.digest()
    provider_payload = base.to_dict()
    provider_payload["model_id"] = "provider-model"
    assert "model_id" not in base.canonical_serialization()


def test_predecessor_and_successor_versions_are_validated() -> None:
    assert (
        binding(
            binding_version="v2",
            predecessor_binding_id="persona-self-binding",
            predecessor_binding_version="v1",
        ).binding_version
        == "v2"
    )
    malformed = {
        "one field": dict(
            binding_version="v2",
            predecessor_binding_id="persona-self-binding",
            predecessor_binding_version=None,
        ),
        "nonconsecutive": dict(
            binding_version="v3",
            predecessor_binding_id="persona-self-binding",
            predecessor_binding_version="v1",
        ),
        "foreign lineage": dict(
            binding_version="v2",
            predecessor_binding_id="other-binding",
            predecessor_binding_version="v1",
        ),
    }
    for candidate in malformed.values():
        assert (
            contract_error(lambda: binding(**candidate))
            is PersonaSelfBindingErrorCode.PSB_PREDECESSOR_INVALID
        )


def test_authority_family_is_exact_and_unique() -> None:
    assert (
        contract_error(
            lambda: AuthorityReference(
                "IdentityFrameSet",  # type: ignore[arg-type]
                "identity-set",
                DIGEST,
                None,
            )
        )
        is PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID
    )
    assert (
        contract_error(
            lambda: PersonaSelfBinding(
                **{
                    **{
                        field: getattr(binding(), field)
                        for field in PersonaSelfBinding.__slots__
                    },
                    "identity_authority": authority(
                        AuthorityFamily.EXPERIENCE_FRAME_SET, "identity-set"
                    ),
                }
            )
        )
        is PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID
    )
    payload = binding().to_dict()
    payload["experience_authority"]["authority_id"] = "identity-set"
    assert (
        contract_error(lambda: PersonaSelfBinding.from_mapping(payload))
        is PersonaSelfBindingErrorCode.PSB_DUPLICATE_AUTHORITY_FAMILY
    )


def test_identity_authority_assertion_is_typed_and_deterministic() -> None:
    first = IdentityAuthorityAssertion(
        assertion_scope="current-turn",
        asserted_subject="persona-self",
        asserted_classification="identity-boundary",
        asserted_value="contract fixture",
        conflict_against_active_binding=False,
        source_spans=({"source": "unit-test", "span": "1:1-1:20"},),
        classifier_version="future-contract-schema-v1",
        disposition=IdentityAssertionDisposition.NO_IDENTITY_AUTHORITY_CONFLICT,
        evidence_digest=DIGEST,
    )
    second = IdentityAuthorityAssertion(
        assertion_scope="current-turn",
        asserted_subject="persona-self",
        asserted_classification="identity-boundary",
        asserted_value="contract fixture",
        conflict_against_active_binding=False,
        source_spans=({"span": "1:1-1:20", "source": "unit-test"},),
        classifier_version="future-contract-schema-v1",
        disposition=IdentityAssertionDisposition.NO_IDENTITY_AUTHORITY_CONFLICT,
        evidence_digest=DIGEST,
    )
    assert first == second
    assert first.canonical_serialization() == second.canonical_serialization()
    assert first.digest() == second.digest()
    assert (
        contract_error(
            lambda: IdentityAuthorityAssertion(
                assertion_scope="current-turn",
                asserted_subject="persona-self",
                asserted_classification="identity-boundary",
                asserted_value="contract fixture",
                conflict_against_active_binding=False,
                source_spans=(),
                classifier_version="future-contract-schema-v1",
                disposition="RESOLVED",  # type: ignore[arg-type]
                evidence_digest=DIGEST,
            )
        )
        is PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID
    )

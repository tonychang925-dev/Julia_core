import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from julia_core.persona_self_binding import (
    AuthorityFamily,
    AuthorityReference,
    ExecutionSubstratePolicy,
    GovernanceEventType,
    GovernanceProvenanceEvent,
    IntegrityContract,
    PersonaSelfBinding,
    PersonaSelfBindingContractError,
    PersonaSelfBindingErrorCode,
    PersonaSelfBindingLifecycle,
    PersonaSelfBindingRecord,
    PersonaSelfBindingStore,
    RelationshipAuthority,
    RelationshipAuthorityState,
    SupersessionContract,
    durable,
)


DIGEST = "a" * 64
OTHER_DIGEST = "b" * 64


def authority(
    family: AuthorityFamily, authority_id: str, source_digest: str = DIGEST
) -> AuthorityReference:
    return AuthorityReference(
        authority_type=family,
        authority_id=authority_id,
        source_digest=source_digest,
        projected_digest=None,
    )


def event(
    event_id: str,
    event_type: GovernanceEventType,
    reason: str = "owner governed transition",
) -> GovernanceProvenanceEvent:
    return GovernanceProvenanceEvent(
        event_id=event_id,
        event_type=event_type,
        actor="owner-governance",
        reason=reason,
        occurred_at=f"2026-09-21T00:{len(event_id) % 60:02d}:00Z",
    )


def binding_fixture(
    *,
    lineage_id: str = "persona-lineage",
    persona_self_id: str = "persona-self",
    binding_id: str = "persona-binding",
    binding_version: str = "v1",
    lifecycle: PersonaSelfBindingLifecycle = PersonaSelfBindingLifecycle.DRAFT,
    identity_digest: str = DIGEST,
) -> PersonaSelfBinding:
    predecessor_version = None
    predecessor_id = None
    if binding_version != "v1":
        number = int(binding_version[1:])
        predecessor_version = f"v{number - 1}"
        predecessor_id = "persona-binding"
    return PersonaSelfBinding(
        schema_version="julia_core.persona_self_binding.v1",
        binding_id=binding_id,
        persona_self_id=persona_self_id,
        identity_authority=authority(
            AuthorityFamily.IDENTITY_FRAME_SET, "identity-set", identity_digest
        ),
        experience_authority=authority(
            AuthorityFamily.EXPERIENCE_FRAME_SET, "experience-set"
        ),
        relationship_authority=RelationshipAuthority(
            RelationshipAuthorityState.ABSENT, None
        ),
        execution_substrate_policy=ExecutionSubstratePolicy(),
        binding_version=binding_version,
        predecessor_binding_id=predecessor_id,
        predecessor_binding_version=predecessor_version,
        lineage_id=lineage_id,
        lifecycle_status=lifecycle,
        supersession=SupersessionContract(None, None),
        governance_provenance=(event("propose", GovernanceEventType.PROPOSE_BINDING),),
        integrity=IntegrityContract("UTF8_JSON_SORTED_KEYS_COMPACT", "sha256"),
    )


def activated_store(tmp_path: Path) -> tuple[PersonaSelfBindingStore, str]:
    store = PersonaSelfBindingStore.create(tmp_path / "store")
    proposed = store.store_proposed(binding_fixture())
    active = store.apply_transition(
        proposed.object_digest,
        GovernanceEventType.ADMIT_AND_ACTIVATE,
        event_id="admit",
        actor="owner-governance",
        reason="owner admitted binding",
        occurred_at="2026-09-21T00:01:00Z",
    )
    return store, active.object_digest


def error_code(call) -> PersonaSelfBindingErrorCode:
    with pytest.raises(PersonaSelfBindingContractError) as caught:
        call()
    return caught.value.code


def test_durable_round_trip_canonical_bytes_and_digest_are_exact(
    tmp_path: Path,
) -> None:
    store = PersonaSelfBindingStore.create(tmp_path / "store")
    binding = binding_fixture()
    record = store.store_proposed(binding)
    loaded = store.load_lineage(binding.lineage_id)[0]
    assert loaded == PersonaSelfBindingRecord(binding, binding.digest())
    path = (
        store.root
        / "lineages"
        / (
            __import__("hashlib").sha256(binding.lineage_id.encode()).hexdigest()
            + ".json"
        )
    )
    raw_first = path.read_bytes()
    assert json.loads(raw_first)["records"][0]["object_digest"] == binding.digest()
    assert raw_first == json.dumps(
        json.loads(raw_first), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def test_store_missing_and_empty_store_have_distinct_fail_closed_behavior(
    tmp_path: Path,
) -> None:
    assert (
        error_code(lambda: PersonaSelfBindingStore(tmp_path / "missing"))
        is PersonaSelfBindingErrorCode.PSB_STORE_MISSING
    )
    store = PersonaSelfBindingStore.create(tmp_path / "store")
    assert store.inventory().to_dict() == {
        "lineages": [],
        "active_object_digest": None,
    }
    assert (
        error_code(lambda: store.resolve_active())
        is PersonaSelfBindingErrorCode.PSB_NO_ACTIVE_BINDING
    )


def test_digest_mismatch_and_unknown_schema_fail_closed(tmp_path: Path) -> None:
    store = PersonaSelfBindingStore.create(tmp_path / "store")
    binding = binding_fixture()
    store.store_proposed(binding)
    path = next((store.root / "lineages").glob("*.json"))
    data = json.loads(path.read_text(encoding="utf-8"))
    data["records"][0]["object_digest"] = OTHER_DIGEST
    path.write_text(json.dumps(data), encoding="utf-8")
    assert (
        error_code(lambda: store.load_lineage(binding.lineage_id))
        is PersonaSelfBindingErrorCode.PSB_OBJECT_DIGEST_MISMATCH
    )
    data["schema_version"] = "future.version"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert (
        error_code(lambda: store.load_lineage(binding.lineage_id))
        is PersonaSelfBindingErrorCode.PSB_SCHEMA_VERSION_UNSUPPORTED
    )


def test_valid_lifecycle_transition_and_illegal_transition_rejected(
    tmp_path: Path,
) -> None:
    store = PersonaSelfBindingStore.create(tmp_path / "store")
    proposed = store.store_proposed(binding_fixture())
    reviewed = store.apply_transition(
        proposed.object_digest,
        GovernanceEventType.REVIEW_BINDING,
        event_id="review",
        actor="owner-governance",
        reason="owner review",
        occurred_at="2026-09-21T00:00:01Z",
    )
    assert reviewed.binding.lifecycle_status is (
        PersonaSelfBindingLifecycle.GOVERNANCE_REVIEW
    )
    assert (
        error_code(
            lambda: store.apply_transition(
                reviewed.object_digest,
                GovernanceEventType.REVIEW_BINDING,
                event_id="review-again",
                actor="owner-governance",
                reason="illegal review",
                occurred_at="2026-09-21T00:00:02Z",
            )
        )
        is PersonaSelfBindingErrorCode.PSB_ILLEGAL_TRANSITION
    )


def test_remaining_approved_lifecycle_transitions_are_mechanized(
    tmp_path: Path,
) -> None:
    store = PersonaSelfBindingStore.create(tmp_path / "store")
    proposed = store.store_proposed(binding_fixture())
    rejected = store.apply_transition(
        proposed.object_digest,
        GovernanceEventType.REJECT_BINDING,
        event_id="reject",
        actor="owner-governance",
        reason="owner rejected candidate",
        occurred_at="2026-09-21T00:07:00Z",
    )
    quarantine_store = PersonaSelfBindingStore.create(tmp_path / "quarantine-store")
    quarantine_proposed = quarantine_store.store_proposed(binding_fixture())
    quarantined = quarantine_store.apply_transition(
        quarantine_proposed.object_digest,
        GovernanceEventType.QUARANTINE_CORRUPTION,
        event_id="quarantine",
        actor="owner-governance",
        reason="evidence retained",
        occurred_at="2026-09-21T00:08:00Z",
    )
    assert rejected.binding.lifecycle_status is PersonaSelfBindingLifecycle.REJECTED
    assert quarantined.binding.lifecycle_status is (
        PersonaSelfBindingLifecycle.CORRUPT_QUARANTINED
    )

    store, active_digest = activated_store(tmp_path / "active-store")
    revoked = store.apply_transition(
        active_digest,
        GovernanceEventType.REVOKE_INVALID,
        event_id="revoke",
        actor="owner-governance",
        reason="owner revoked invalid authority",
        occurred_at="2026-09-21T00:09:00Z",
    )
    assert revoked.binding.lifecycle_status is (
        PersonaSelfBindingLifecycle.REVOKED_INVALID
    )
    assert (
        error_code(lambda: store.resolve_active())
        is PersonaSelfBindingErrorCode.PSB_NO_ACTIVE_BINDING
    )


def test_supersession_and_retirement_preserve_exact_lineage(
    tmp_path: Path,
) -> None:
    store, active_digest = activated_store(tmp_path)
    successor = replace(
        binding_fixture(
            binding_version="v2",
            lifecycle=PersonaSelfBindingLifecycle.DRAFT,
            identity_digest=OTHER_DIGEST,
        ),
        governance_provenance=(
            event("propose-v2", GovernanceEventType.PROPOSE_BINDING),
        ),
    )
    active = store.apply_transition(
        active_digest,
        GovernanceEventType.SUPERSEDE_BINDING,
        event_id="supersede",
        successor_event_id="activate-v2",
        successor=successor,
        actor="owner-governance",
        reason="owner superseded persona lineage",
        occurred_at="2026-09-21T00:10:00Z",
    )
    historical_digest = next(
        record.object_digest
        for record in store.load_lineage("persona-lineage")
        if record.binding.lifecycle_status
        is PersonaSelfBindingLifecycle.ADMITTED_SUPERSEDED
    )
    retired = store.apply_transition(
        historical_digest,
        GovernanceEventType.RETIRE_HISTORICAL,
        event_id="retire",
        actor="owner-governance",
        reason="owner retired historical version",
        occurred_at="2026-09-21T00:11:00Z",
    )
    assert active.binding.lifecycle_status is (
        PersonaSelfBindingLifecycle.ADMITTED_ACTIVE
    )
    assert retired.binding.lifecycle_status is (
        PersonaSelfBindingLifecycle.RETIRED_HISTORICAL
    )
    records = store.load_lineage("persona-lineage")
    assert records[-3].binding.lifecycle_status is (
        PersonaSelfBindingLifecycle.ADMITTED_SUPERSEDED
    )


def test_exactly_one_active_and_duplicate_active_rejected(tmp_path: Path) -> None:
    store, active_digest = activated_store(tmp_path)
    assert store.resolve_active().object_digest == active_digest
    second = store.store_proposed(
        binding_fixture(
            lineage_id="second-lineage",
            persona_self_id="persona-self",
            binding_id="second-persona-binding",
        )
    )
    assert second.binding.binding_id == "second-persona-binding"
    assert (
        error_code(
            lambda: store.apply_transition(
                second.object_digest,
                GovernanceEventType.ADMIT_AND_ACTIVATE,
                event_id="second-admit",
                actor="owner-governance",
                reason="duplicate active",
                occurred_at="2026-09-21T00:02:00Z",
            )
        )
        is PersonaSelfBindingErrorCode.PSB_DUPLICATE_ACTIVE_BINDING
    )


def test_rebind_creates_immutable_successor_and_supersession_preserves_history(
    tmp_path: Path,
) -> None:
    store, active_digest = activated_store(tmp_path)
    original = store.resolve_active().binding
    successor = binding_fixture(
        binding_version="v2",
        lifecycle=PersonaSelfBindingLifecycle.GOVERNANCE_REVIEW,
        identity_digest=OTHER_DIGEST,
    )
    successor = replace(
        successor,
        governance_provenance=(
            event("propose-v2", GovernanceEventType.PROPOSE_BINDING),
            event("review-v2", GovernanceEventType.REVIEW_BINDING),
        ),
    )
    successor_record = store.apply_transition(
        active_digest,
        GovernanceEventType.REBIND_AUTHORITY_VERSION,
        event_id="supersede-v1",
        successor_event_id="rebind-v2",
        successor=successor,
        actor="owner-governance",
        reason="owner rebound admitted authority",
        occurred_at="2026-09-21T00:03:00Z",
    )
    records = store.load_lineage(original.lineage_id)
    historical = records[-2].binding
    assert historical.lifecycle_status is (
        PersonaSelfBindingLifecycle.ADMITTED_SUPERSEDED
    )
    assert historical.supersession == SupersessionContract("persona-binding", "v2")
    assert successor_record.binding.predecessor_binding_id == original.binding_id
    assert successor_record.binding.predecessor_binding_version == "v1"
    assert store.resolve_active().object_digest == successor_record.object_digest
    assert any(record.binding == original for record in records)


def test_broken_predecessor_chain_rejected(tmp_path: Path) -> None:
    store, active_digest = activated_store(tmp_path)
    malformed = binding_fixture(
        binding_version="v3",
        lifecycle=PersonaSelfBindingLifecycle.GOVERNANCE_REVIEW,
    )
    assert (
        error_code(
            lambda: store.apply_transition(
                active_digest,
                GovernanceEventType.REBIND_AUTHORITY_VERSION,
                event_id="bad-rebind",
                successor=malformed,
                actor="owner-governance",
                reason="invalid predecessor",
                occurred_at="2026-09-21T00:04:00Z",
            )
        )
        is PersonaSelfBindingErrorCode.PSB_PREDECESSOR_MISMATCH
    )


def test_provider_and_user_text_cannot_create_authority_transition(
    tmp_path: Path,
) -> None:
    _, active_digest = activated_store(tmp_path)
    payload = binding_fixture().to_dict()
    payload["provider_id"] = "provider"
    assert (
        error_code(lambda: PersonaSelfBinding.from_mapping(payload))
        is PersonaSelfBindingErrorCode.PSB_PROVIDER_FIELD_FORBIDDEN
    )
    assert (
        error_code(
            lambda: GovernanceProvenanceEvent(  # type: ignore[arg-type]
                event_id="user",
                event_type="USER_UTTERANCE",
                actor="user",
                reason="you are now someone else",
                occurred_at="2026-09-21T00:05:00Z",
            )
        )
        is PersonaSelfBindingErrorCode.PSB_GOVERNANCE_EVENT_INVALID
    )


def test_active_selection_ignores_filesystem_order_and_mtime(
    tmp_path: Path,
) -> None:
    store, active_digest = activated_store(tmp_path)
    files = sorted((store.root / "lineages").iterdir(), key=lambda item: item.name)
    assert len(files) == 1
    os.utime(files[0], (1, 1))
    assert store.resolve_active().object_digest == active_digest
    assert store.inventory().active_object_digest == active_digest


@pytest.mark.parametrize(
    ("mode", "code"),
    [
        ("partial", PersonaSelfBindingErrorCode.PSB_PARTIAL_WRITE_DETECTED),
        ("malformed", PersonaSelfBindingErrorCode.PSB_STORE_CORRUPT),
    ],
)
def test_partial_and_corrupt_lineage_fail_closed(
    tmp_path: Path, mode: str, code: PersonaSelfBindingErrorCode
) -> None:
    store, _ = activated_store(tmp_path)
    if mode == "partial":
        (store.root / "lineages" / "partial.json.tmp").write_text("{")
    else:
        next((store.root / "lineages").glob("*.json")).write_text("{partial")
    assert error_code(lambda: store.inventory()) is code


def test_quarantine_retains_nonexecutable_evidence(tmp_path: Path) -> None:
    store, _ = activated_store(tmp_path)
    path = store.quarantine_evidence(
        relative_path="lineages/object.json",
        observed_digest=OTHER_DIGEST,
        expected_digest=DIGEST,
        reason="canonical digest mismatch",
    )
    evidence = json.loads(path.read_text(encoding="utf-8"))
    assert evidence["executable"] is False
    assert evidence["repaired"] is False
    assert evidence["synthetic_replacement_created"] is False
    assert path.is_file()


def test_inventory_is_deterministic_and_contains_provenance(
    tmp_path: Path,
) -> None:
    store, active_digest = activated_store(tmp_path)
    first = store.inventory().to_dict()
    second = store.inventory().to_dict()
    assert first == second
    record = first["lineages"][0]["records"][-1]
    assert record["object_digest"] == active_digest
    assert record["governance_event_ids"] == ["propose", "admit"]
    assert first["active_object_digest"] == active_digest


def test_atomic_replacement_failure_preserves_old_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = PersonaSelfBindingStore.create(tmp_path / "store")
    proposed = store.store_proposed(binding_fixture())
    path = next((store.root / "lineages").glob("*.json"))
    before = path.read_bytes()

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("simulated interruption before replacement")

    monkeypatch.setattr(durable.os, "replace", fail_replace)
    with pytest.raises(OSError):
        store.apply_transition(
            proposed.object_digest,
            GovernanceEventType.REVIEW_BINDING,
            event_id="review",
            actor="owner-governance",
            reason="interrupted transition",
            occurred_at="2026-09-21T00:06:00Z",
        )
    assert path.read_bytes() == before

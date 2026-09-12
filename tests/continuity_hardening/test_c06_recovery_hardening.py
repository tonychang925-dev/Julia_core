from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from julia_core.continuity.hydration import (
    ContinuityHydrationError,
    hydrate_continuity_checkpoint,
)
from julia_core.identity import IdentityResolver
from julia_core.memory_experience import MemoryExperienceResolver

from tests.continuity_hardening.recovery_contract import (
    CHECKPOINT_PAYLOAD_SCHEMA,
    RecoveryEnvelopeRejected,
    canonical_refs_digest,
    package_model_view_is_absent,
    seal_checkpoint,
    validate_checkpoint_envelope,
)
from tests.test_continuity_hydration import (
    checkpoint,
    identity_version,
    identity_repository,
    memory_repository,
)


ARTIFACT = (
    Path(__file__).parents[2]
    / "artifacts"
    / "continuity"
    / "C06_RECOVERY_HARDENING_V1.json"
)


def recovery_package(checkpoint_value, identity_store=None, memory_store=None, reason="recovery"):
    identity_store = identity_store or identity_repository()[0]
    memory_store = memory_store or memory_repository()[0]
    return hydrate_continuity_checkpoint(
        checkpoint_value,
        identity_resolver=IdentityResolver(identity_store),
        memory_resolver=MemoryExperienceResolver(memory_store),
        recovery_reason=reason,
    )


def semantic_recovery_payload(package):
    return {
        "identity_frames": [frame.to_dict() for frame in package.identity_frames],
        "experience_frames": [frame.to_dict() for frame in package.experience_frames],
        "outcomes": [outcome.to_dict() for outcome in package.outcomes],
    }


def test_h01_tampered_envelope_digest_ref_or_provenance_rejects_recovery() -> None:
    identity_store, identity_ref = identity_repository()
    memory_store, memory_ref = memory_repository()
    sealed = seal_checkpoint(
        checkpoint([identity_ref.uri], [memory_ref.uri])
    )

    assert validate_checkpoint_envelope(sealed) is sealed.checkpoint
    sealed.checkpoint.identity_refs.append(identity_ref.uri)
    with pytest.raises(RecoveryEnvelopeRejected, match="payload was tampered"):
        validate_checkpoint_envelope(sealed)

    tampered_payload = replace_checkpoint_for_test(
        sealed.checkpoint,
        identity_refs=[identity_ref.uri.replace("/v1", "/v2")],
    )
    with pytest.raises(RecoveryEnvelopeRejected, match="digest"):
        validate_checkpoint_envelope(
            replace(sealed, checkpoint=tampered_payload)
        )
    with pytest.raises(RecoveryEnvelopeRejected, match="digest"):
        validate_checkpoint_envelope(
            replace(
                sealed,
                provenance=replace(
                    sealed.provenance,
                    canonical_refs_digest="0" * 64,
                ),
            )
        )
    with pytest.raises(RecoveryEnvelopeRejected, match="digest"):
        validate_checkpoint_envelope(replace(sealed, payload_digest="1" * 64))


def replace_checkpoint_for_test(current, **changes):
    payload = current.to_dict()
    payload.update(changes)
    return type(current)(**payload)


def test_h02_malformed_canonical_uri_rejects_recovery() -> None:
    for uri in (
        "identity://lineage/",
        "identity://lineage/v1/extra",
        "memory-experience://experience/v1/extra",
        "memory-experience://experience/v1?provider=alternate",
    ):
        field = "identity_refs" if uri.startswith("identity://") else "memory_refs"
        value = checkpoint(**{field: [uri]})
        with pytest.raises(ContinuityHydrationError):
            recovery_package(value)


def test_h03_unknown_exact_identity_version_rejects_whole_recovery() -> None:
    identity_store, identity_ref = identity_repository()
    memory_store, memory_ref = memory_repository()
    missing = replace(identity_ref, version_id="does-not-exist")
    value = checkpoint([missing.uri], [memory_ref.uri])

    with pytest.raises(ContinuityHydrationError) as error:
        recovery_package(value, identity_store, memory_store)

    assert error.value.failure_manifest["code"] == "unknown_exact_ref"
    assert error.value.failure_manifest["source_ref"] == missing.uri
    assert error.value.failure_manifest["partial_success"] is False


def test_h04_unknown_exact_memory_version_rejects_whole_recovery() -> None:
    identity_store, identity_ref = identity_repository()
    memory_store, memory_ref = memory_repository()
    missing = replace(memory_ref, version_id="does-not-exist")
    value = checkpoint([identity_ref.uri], [missing.uri])

    with pytest.raises(ContinuityHydrationError) as error:
        recovery_package(value, identity_store, memory_store)

    assert error.value.failure_manifest["code"] == "unknown_exact_ref"
    assert error.value.failure_manifest["source_ref"] == missing.uri
    assert error.value.failure_manifest["partial_success"] is False


def test_h05_non_admitted_identity_rejects_whole_recovery() -> None:
    identity_store, identity_ref = identity_repository()
    identity_store.retire(
        identity_ref,
        actor="synthetic-hardening",
        reason="retired before recovery",
        occurred_at="2026-09-12T00:00:00Z",
    )

    with pytest.raises(ContinuityHydrationError) as error:
        recovery_package(checkpoint([identity_ref.uri]), identity_store)

    assert error.value.failure_manifest["source_status"] == "RETIRED"
    assert error.value.failure_manifest["partial_success"] is False


def test_h06_non_admitted_memory_rejects_whole_recovery() -> None:
    memory_store, memory_ref = memory_repository()
    memory_store.retire(
        memory_ref,
        actor="synthetic-hardening",
        reason="retired before recovery",
        occurred_at="2026-09-12T00:00:00Z",
    )

    with pytest.raises(ContinuityHydrationError) as error:
        recovery_package(checkpoint(memory_refs=[memory_ref.uri]), memory_store=memory_store)

    assert error.value.failure_manifest["source_status"] == "RETIRED"
    assert error.value.failure_manifest["partial_success"] is False


def test_h07_no_latest_successor_or_approximate_traversal() -> None:
    identity_store, identity_ref = identity_repository()
    successor = identity_store.store_candidate(identity_version("v2", predecessor="v1"))
    identity_store.admit(
        successor.ref,
        actor="synthetic-hardening",
        reason="successor admitted",
        occurred_at="2026-09-12T00:01:00Z",
    )
    identity_store.supersede(
        identity_ref,
        actor="synthetic-hardening",
        reason="older exact version requested",
        occurred_at="2026-09-12T00:02:00Z",
    )

    with pytest.raises(ContinuityHydrationError) as error:
        recovery_package(checkpoint([identity_ref.uri]), identity_store)

    assert error.value.failure_manifest["source_status"] == "SUPERSEDED"
    assert error.value.failure_manifest["partial_success"] is False


def test_h08_legacy_namespace_is_rejected() -> None:
    with pytest.raises(ContinuityHydrationError) as identity_error:
        recovery_package(checkpoint(["persona://lineage/v1"]))
    with pytest.raises(ContinuityHydrationError) as memory_error:
        recovery_package(checkpoint(memory_refs=["memory://experience/v1"]))

    assert identity_error.value.failure_manifest["code"] == "unsupported_ref"
    assert memory_error.value.failure_manifest["code"] == "unsupported_ref"


def test_h09_duplicate_and_wrong_field_refs_are_rejected() -> None:
    _, identity_ref = identity_repository()
    _, memory_ref = memory_repository()

    with pytest.raises(ContinuityHydrationError) as duplicate_error:
        recovery_package(checkpoint([identity_ref.uri, identity_ref.uri]))
    with pytest.raises(ContinuityHydrationError):
        recovery_package(checkpoint(identity_refs=[memory_ref.uri]))
    with pytest.raises(ContinuityHydrationError):
        recovery_package(checkpoint(memory_refs=[identity_ref.uri]))

    assert duplicate_error.value.failure_manifest["code"] == "ambiguous_ref"


def test_h10_failure_manifest_partial_success_remains_false() -> None:
    scenarios = []
    _, identity_ref = identity_repository()
    _, memory_ref = memory_repository()
    scenarios.append(checkpoint([replace(identity_ref, version_id="missing").uri]))
    scenarios.append(checkpoint(memory_refs=[replace(memory_ref, version_id="missing").uri]))
    scenarios.append(checkpoint(["identity://lineage/v1/extra"]))

    for value in scenarios:
        with pytest.raises(ContinuityHydrationError) as error:
            recovery_package(value)
        assert error.value.failure_manifest["partial_success"] is False


def test_h11_normal_resume_does_not_invent_recovery_state() -> None:
    _, identity_ref = identity_repository()
    _, memory_ref = memory_repository()
    value = replace(
        checkpoint([identity_ref.uri], [memory_ref.uri]),
        relationship_refs=["relationship://fixture/r1"],
        active_project_refs=["project://fixture/p1"],
    )

    package = recovery_package(value, reason="normal_resume")

    assert len(package.identity_frames) == 1
    assert len(package.experience_frames) == 1
    assert len(package.outcomes) == 2
    assert "relationship://fixture" not in package.canonical_serialization()
    assert "project://fixture" not in package.canonical_serialization()


def test_h12_cold_start_uses_only_exact_canonical_refs() -> None:
    empty = recovery_package(checkpoint(), reason="cold_start")
    _, identity_ref = identity_repository()
    _, memory_ref = memory_repository()
    explicit = recovery_package(
        checkpoint([identity_ref.uri], [memory_ref.uri]), reason="cold_start"
    )

    assert empty.identity_frames == ()
    assert empty.experience_frames == ()
    assert empty.outcomes == ()
    assert len(explicit.identity_frames) == 1
    assert len(explicit.experience_frames) == 1
    assert len(explicit.outcomes) == 2


def test_h13_compact_reconstructs_from_canonical_refs_without_prompt_authority() -> None:
    identity_store, identity_ref = identity_repository()
    memory_store, memory_ref = memory_repository()
    value = checkpoint([identity_ref.uri], [memory_ref.uri])
    sealed = seal_checkpoint(value)
    compact_checkpoint = replace_checkpoint_for_test(
        sealed.checkpoint,
        integrity={
            "schema": CHECKPOINT_PAYLOAD_SCHEMA,
            "prompt_bytes": "synthetic compact prose",
        },
    )

    with pytest.raises(RecoveryEnvelopeRejected, match="integrity"):
        seal_checkpoint(compact_checkpoint)

    package = recovery_package(
        validate_checkpoint_envelope(sealed),
        identity_store,
        memory_store,
        reason="compact",
    )
    payload = package.to_dict()
    assert package_model_view_is_absent(payload)
    assert "synthetic compact prose" not in package.canonical_serialization()


@pytest.mark.parametrize(
    "reason",
    ["normal_resume", "cold_start", "compact", "provider_switch", "model_switch"],
)
def test_h14_provider_and_model_switch_preserve_recovered_semantics(reason) -> None:
    _, identity_ref = identity_repository()
    _, memory_ref = memory_repository()
    value = checkpoint([identity_ref.uri], [memory_ref.uri])
    baseline = recovery_package(value, reason="normal_resume")
    switched = recovery_package(value, reason=reason)

    assert semantic_recovery_payload(baseline) == semantic_recovery_payload(switched)
    assert package_model_view_is_absent(switched.to_dict())


def test_h15_recovery_package_has_no_provider_or_model_visible_output() -> None:
    _, identity_ref = identity_repository()
    _, memory_ref = memory_repository()
    package = recovery_package(
        checkpoint([identity_ref.uri], [memory_ref.uri]),
        reason="provider_switch",
    )
    payload = package.to_dict()

    assert package_model_view_is_absent(payload)
    assert payload["authority"]["model_visibility_decided"] is False
    assert payload["authority"]["runtime_authority"] is False
    assert not hasattr(package, "render")
    assert not hasattr(package, "to_messages")


def test_h16_durability_contract_preserves_exact_recovery_requirements() -> None:
    contract = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    assert contract["schema"] == "continuity_checkpoint_envelope_v1"
    assert contract["implementation_boundary"]["production_persistence_implemented"] is False
    assert contract["implementation_boundary"]["canonical_writes"] is False
    assert contract["required_preservation"]["all_or_nothing"] is True
    assert set(contract["required_preservation"]["exact_statuses"]) == {
        "IDENTITY=ADMITTED",
        "MEMORY_EXPERIENCE=ADMITTED",
    }
    assert contract["rejection_contract"]["latest_successor_or_approximate_ref"] is True
    assert contract["rejection_contract"]["partial_package"] is True


def test_h17_existing_hydration_surface_remains_exact_and_non_mutating() -> None:
    identity_store, identity_ref = identity_repository()
    memory_store, memory_ref = memory_repository()
    value = checkpoint([identity_ref.uri], [memory_ref.uri])
    identity_before = identity_store.resolve(identity_ref).to_dict()
    memory_before = memory_store.resolve(memory_ref).to_dict()
    checkpoint_before = value.to_dict()

    first = recovery_package(value, identity_store, memory_store)
    second = recovery_package(value, identity_store, memory_store)

    assert first.canonical_serialization() == second.canonical_serialization()
    assert identity_store.resolve(identity_ref).to_dict() == identity_before
    assert memory_store.resolve(memory_ref).to_dict() == memory_before
    assert value.to_dict() == checkpoint_before
    assert canonical_refs_digest(value) == canonical_refs_digest(value)


def test_h18_hardening_adds_no_production_authority_or_alternate_lookup() -> None:
    contract = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    forbidden_authorities = ("provider", "runtime", "model")
    implementation = contract["implementation_boundary"]

    assert implementation["runtime_wiring_implemented"] is False
    assert implementation["provider_wiring_implemented"] is False
    assert implementation["model_visible_output"] is False
    assert implementation["test_only_contract"] is True
    assert all(
        implementation[f"{name}_wiring_implemented"] is False
        for name in forbidden_authorities
        if f"{name}_wiring_implemented" in implementation
    )
    assert contract["rejection_contract"]["latest_successor_or_approximate_ref"] is True

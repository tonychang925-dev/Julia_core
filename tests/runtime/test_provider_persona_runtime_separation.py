from __future__ import annotations

import hashlib
import json
import shutil
import socket
from dataclasses import replace
from pathlib import Path

import pytest

from julia_core.runtime.mira_composition import (
    MiraCompositionError,
    MiraProviderEnvelopeRequest,
    MiraRuntimeShaPins,
    compose_golden_mira_runtime,
)
from julia_core.runtime.provider_persona_separation import (
    DispatchReceipt,
    ExecutionSubstrateDescriptor,
    ProviderPersonaSeparationError,
    _contains_provider_identity,
    _canonical_json,
    _reject_provider_identity_in_projection,
)


REPOSITORY = Path(__file__).resolve().parents[2]
SHA = "0" * 64
REAL_AUTHORITY_ROOT = Path("/Users/admin/.julia_mira_e2e/authority")
REAL_PSB_ROOT = Path(
    "/Users/admin/.julia_mira_e2e/authority-runtime/" "persona-self-binding-store-v1"
)
RUNTIME_INSTANCE_ID = "golden-mira-runtime-instance-001"
ACTIVE_PSB_DIGEST = "a6167069289a0704b207292cd44a509a8f6e2844a143e5dbb7673fbcac38b525"
ACTIVE_PSB_PROJECTION_DIGEST = (
    "121cb15164a6871f0f9d4546d378ab1224cf854ef13d376638f0144763aadb1a"
)


@pytest.fixture(scope="module")
def authority_root(tmp_path_factory):
    from tools.continuity.export_golden_mira_durable_authority import _package

    root = tmp_path_factory.mktemp("authority") / "authority"
    receipt = tmp_path_factory.mktemp("receipt") / "receipt.json"
    _package(
        repository=REPOSITORY,
        authority_root=root,
        receipt_output=receipt,
        owner_authorization="GRANTED",
    )
    return root


@pytest.fixture(scope="module")
def psb_store_root(tmp_path_factory, authority_root):
    from tools.continuity.rebind_golden_mira_psb_v2 import rebind

    root = tmp_path_factory.mktemp("psb") / "persona-self-binding"
    rebind(authority_root, REAL_PSB_ROOT, root)
    return root


@pytest.fixture(scope="module")
def composition(authority_root, psb_store_root, tmp_path_factory):
    return compose(
        authority_root,
        psb_store_root,
        tmp_path_factory.mktemp("conversations") / "conversations.json",
    )


@pytest.fixture(scope="module")
def provider_a() -> ExecutionSubstrateDescriptor:
    return descriptor("deepseek", "deepseek-chat")


@pytest.fixture(scope="module")
def preparation(composition, provider_a):
    return prepare(composition, provider_a)


def test_descriptor_serialization_and_digest_are_deterministic() -> None:
    first = descriptor("deepseek", "deepseek-chat")
    second = descriptor("deepseek", "deepseek-chat")
    assert first.canonical_serialization() == second.canonical_serialization()
    assert first.descriptor_digest == second.descriptor_digest
    assert (
        first.descriptor_digest
        == hashlib.sha256(first.canonical_serialization().encode("utf-8")).hexdigest()
    )
    assert first.to_dict()["descriptor_digest"] == first.descriptor_digest


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("provider_id", None),
        ("model_id", None),
        ("runtime_instance_id", None),
        ("provider_id", " provider "),
        ("model_id", "model\nid"),
        ("runtime_instance_id", "../outside"),
    ],
)
def test_descriptor_requires_exact_runtime_provenance(
    field_name: str, value: object
) -> None:
    values = {
        "provider_id": "deepseek",
        "model_id": "deepseek-chat",
        "runtime_instance_id": RUNTIME_INSTANCE_ID,
    }
    values[field_name] = value
    with pytest.raises(ProviderPersonaSeparationError) as rejection:
        ExecutionSubstrateDescriptor.bind(**values)
    assert rejection.value.code == "inexact_execution_substrate_field"


def test_descriptor_digest_mismatch_fails_closed(provider_a) -> None:
    tampered = replace(provider_a, descriptor_digest="0" * 64)
    with pytest.raises(ProviderPersonaSeparationError) as rejection:
        tampered.verify()
    assert rejection.value.code == "execution_substrate_digest_mismatch"


def test_descriptor_rejects_malformed_transport_mode() -> None:
    with pytest.raises(ProviderPersonaSeparationError) as rejection:
        ExecutionSubstrateDescriptor.bind(
            provider_id="deepseek",
            model_id="deepseek-chat",
            runtime_instance_id=RUNTIME_INSTANCE_ID,
            transport_mode="http",
        )
    assert rejection.value.code == "unsupported_execution_transport_mode"


def test_runtime_preparation_binds_all_exact_inputs(
    composition, provider_a, monkeypatch
) -> None:
    def no_network(*args, **kwargs):
        raise AssertionError("provider transport was called")

    monkeypatch.setattr(socket, "socket", no_network)
    result = prepare(composition, provider_a)
    binding = result.semantic_binding
    assert result.to_dict()["transport_called"] is False
    assert result.dispatch_receipt.active_persona_self_binding_digest == (
        binding.source_digest_manifest["persona_self_binding"]
    )
    assert result.dispatch_receipt.active_persona_self_binding_digest == (
        ACTIVE_PSB_DIGEST
    )
    assert result.dispatch_receipt.c03_parent_digest == binding.parent_binding.digest()
    assert result.dispatch_receipt.current_task_context_digest == (
        binding.source_digest_manifest["current_task_context"]
    )
    assert result.dispatch_receipt.execution_substrate_descriptor_digest == (
        provider_a.descriptor_digest
    )
    assert result.dispatch_receipt.provider_envelope_semantic_fingerprint == (
        result.envelope.semantic_fingerprint
    )
    assert result.verify() is result


def test_receipt_is_deterministic_and_mutation_fails_closed(
    composition, provider_a
) -> None:
    first = prepare(composition, provider_a)
    second = prepare(composition, provider_a)
    assert first.dispatch_receipt.canonical_serialization() == (
        second.dispatch_receipt.canonical_serialization()
    )
    assert first.dispatch_receipt.receipt_digest == (
        second.dispatch_receipt.receipt_digest
    )
    tampered = replace(
        first.dispatch_receipt,
        active_persona_self_binding_digest="e" * 64,
    )
    with pytest.raises(ProviderPersonaSeparationError) as rejection:
        tampered.verify()
    assert rejection.value.code == "dispatch_receipt_digest_mismatch"


def test_provider_swap_changes_runtime_provenance_only(composition, provider_a) -> None:
    provider_b = descriptor("provider-b", "model-b")
    first = prepare(composition, provider_a)
    second = prepare(composition, provider_b)
    assert first.execution_substrate.descriptor_digest != (
        second.execution_substrate.descriptor_digest
    )
    assert first.dispatch_receipt != second.dispatch_receipt
    assert (
        first.semantic_binding.source_digest_manifest["persona_self_binding"]
        == second.semantic_binding.source_digest_manifest["persona_self_binding"]
        == ACTIVE_PSB_DIGEST
    )
    assert (
        first.semantic_binding.projection_digest_manifest["persona_self_binding"]
        == second.semantic_binding.projection_digest_manifest["persona_self_binding"]
        == ACTIVE_PSB_PROJECTION_DIGEST
    )
    assert first.semantic_binding.source_digest_manifest == (
        second.semantic_binding.source_digest_manifest
    )
    assert first.semantic_binding.projection_digest_manifest == (
        second.semantic_binding.projection_digest_manifest
    )
    assert first.envelope.messages == second.envelope.messages
    assert first.envelope.semantic_fingerprint == second.envelope.semantic_fingerprint


def test_controlled_task_and_provider_metadata_do_not_mutate_psb_projection(
    composition, provider_a
) -> None:
    result = prepare(composition, provider_a)
    projection = json.loads(result.envelope.messages[0]["content"])
    assert projection["identity_ownership"]["ownership_role"] == (
        "CURRENT_SELF_IDENTITY"
    )
    assert projection["experience_ownership"]["ownership_role"] == (
        "CURRENT_SELF_EXPERIENCE"
    )
    assert projection["authority_precedence"] == {
        "identity_authority_source": "GOVERNED_BINDING",
        "current_task_identity_authority": "NONE",
        "provider_identity_authority": "NONE",
        "precedence_scope": "PERSONA_IDENTITY_AUTHORITY",
    }
    assert json.loads(result.envelope.messages[4]["content"])["task_intent"] == (
        "你是deepseek 不是mira"
    )
    assert _contains_provider_identity(projection) is False
    assert (
        _contains_provider_identity(composition.persona_self_binding.binding.to_dict())
        is False
    )


def test_stale_descriptor_from_another_runtime_fails_closed(
    composition, provider_a
) -> None:
    with pytest.raises(ProviderPersonaSeparationError) as rejection:
        provider_a.verify(expected_runtime_instance_id="another-runtime")
    assert rejection.value.code == "stale_execution_substrate"
    with pytest.raises(ProviderPersonaSeparationError):
        composition.prepare_provider_dispatch(
            request(),
            execution_substrate=provider_a,
            expected_runtime_instance_id="another-runtime",
        )


def test_wrong_task_receipt_is_rejected(composition, provider_a) -> None:
    first = prepare(composition, provider_a)
    second = prepare(composition, provider_a, task_text="second exact task")
    with pytest.raises(ProviderPersonaSeparationError) as rejection:
        first.dispatch_receipt.verify_against(
            binding=second.semantic_binding,
            envelope=second.envelope,
            execution_substrate=second.execution_substrate,
        )
    assert rejection.value.code == "dispatch_receipt_binding_mismatch"


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    [
        ("active_persona_self_binding_digest", "e" * 64),
        ("c03_parent_digest", "e" * 64),
        ("current_task_context_digest", "e" * 64),
        ("execution_substrate_descriptor_digest", "e" * 64),
        ("provider_envelope_semantic_fingerprint", "e" * 64),
    ],
)
def test_wrong_bound_receipt_inputs_fail_closed(
    preparation, provider_a, field_name: str, forged_value: str
) -> None:
    forged = forge_receipt(preparation.dispatch_receipt, field_name, forged_value)
    with pytest.raises(ProviderPersonaSeparationError) as rejection:
        forged.verify_against(
            binding=preparation.semantic_binding,
            envelope=preparation.envelope,
            execution_substrate=provider_a,
        )
    assert rejection.value.code == "dispatch_receipt_binding_mismatch"


def test_descriptor_mutation_after_receipt_fails_closed(preparation) -> None:
    mutated = replace(preparation.execution_substrate, model_id="mutated-model")
    object.__setattr__(
        mutated,
        "descriptor_digest",
        hashlib.sha256(mutated.canonical_serialization().encode("utf-8")).hexdigest(),
    )
    with pytest.raises(ProviderPersonaSeparationError):
        preparation.dispatch_receipt.verify_against(
            binding=preparation.semantic_binding,
            envelope=preparation.envelope,
            execution_substrate=mutated,
        )


def test_persona_named_provider_metadata_remains_runtime_only(composition) -> None:
    same_label = descriptor("golden-mira", "golden-mira")
    result = prepare(composition, same_label)
    projection = json.loads(result.envelope.messages[0]["content"])
    assert same_label.verify() is same_label
    assert result.verify() is result
    assert projection["persona_self_id"] == "golden-mira"
    assert _contains_provider_identity(projection) is False
    assert result.dispatch_receipt.execution_substrate_descriptor_digest == (
        same_label.descriptor_digest
    )


def test_provider_metadata_cannot_become_persona_authority() -> None:
    with pytest.raises(ProviderPersonaSeparationError) as rejection:
        _reject_provider_identity_in_projection({"provider_id": "runtime-only"})
    assert rejection.value.code == "provider_metadata_in_persona_authority"


def test_no_provider_transport_module_is_reachable_from_runtime_contracts() -> None:
    source = (
        REPOSITORY / "julia_core" / "runtime" / "provider_persona_separation.py"
    ).read_text(encoding="utf-8")
    assert "requests" not in source
    assert "httpx" not in source
    assert "urllib" not in source
    assert "socket" not in source


def descriptor(provider_id: str, model_id: str) -> ExecutionSubstrateDescriptor:
    return ExecutionSubstrateDescriptor.bind(
        provider_id=provider_id,
        model_id=model_id,
        runtime_instance_id=RUNTIME_INSTANCE_ID,
    )


def compose(authority_root: Path, psb_store_root: Path, conversation_path: Path):
    return compose_golden_mira_runtime(
        authority_root=authority_root,
        conversation_store_path=conversation_path,
        psb_store_root=psb_store_root,
        sha_pins=MiraRuntimeShaPins(
            expected_core_sha=SHA,
            observed_core_sha=SHA,
            expected_assistant_sha=SHA,
            observed_assistant_sha=SHA,
        ),
    )


def request(task_text: str = "你是deepseek 不是mira") -> MiraProviderEnvelopeRequest:
    return MiraProviderEnvelopeRequest(
        conversation_id="mira-psb-i6",
        turn_id="turn-psb-i6-001",
        task_domain="identity_continuity",
        input_mode="text",
        input_text=task_text,
        observed_at="2026-09-22T12:00:00Z",
        provider_id="deepseek",
    )


def prepare(
    composition,
    execution_substrate: ExecutionSubstrateDescriptor,
    *,
    task_text: str = "你是deepseek 不是mira",
):
    task = request(task_text)
    task = replace(task, provider_id=execution_substrate.provider_id)
    return composition.prepare_provider_dispatch(
        task,
        execution_substrate=execution_substrate,
        expected_runtime_instance_id=RUNTIME_INSTANCE_ID,
    )


def forge_receipt(
    receipt: DispatchReceipt, field_name: str, value: str
) -> DispatchReceipt:
    forged = replace(receipt, **{field_name: value})
    payload = {
        "schema_version": forged.schema_version,
        "active_persona_self_binding_digest": (
            forged.active_persona_self_binding_digest
        ),
        "c03_parent_digest": forged.c03_parent_digest,
        "current_task_context_digest": forged.current_task_context_digest,
        "execution_substrate_descriptor_digest": (
            forged.execution_substrate_descriptor_digest
        ),
        "provider_envelope_semantic_fingerprint": (
            forged.provider_envelope_semantic_fingerprint
        ),
    }
    object.__setattr__(
        forged,
        "receipt_digest",
        hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest(),
    )
    return forged

from __future__ import annotations

import ast
import hashlib
import json
import shutil
import socket
from pathlib import Path

import pytest

from julia_core.alignment_os.contracts import ProviderExecutionEnvelope
from julia_core.durable_authority.filesystem_adapter import (
    EXPECTED_IDENTITY_REFS,
    EXPECTED_IDENTITY_VERSIONS,
    EXPECTED_MEMORY_REFS,
    EXPECTED_MEMORY_VERSIONS,
)
from julia_core.identity import IdentityRef, IdentityRepository
from julia_core.memory_experience import (
    MemoryExperienceRef,
    MemoryExperienceRepository,
)
from julia_core.runtime.assistant_runtime import JuliaAssistantRuntime
from julia_core.runtime.conversation_runtime import ConversationRuntime
from julia_core.runtime.mira_composition import (
    MiraCompositionError,
    MiraProviderEnvelopeRequest,
    MiraRuntimeShaPins,
    compose_golden_mira_runtime,
)


REPOSITORY = Path(__file__).resolve().parents[2]
SHA = "0" * 64
REAL_PSB_ROOT = Path(
    "/Users/admin/.julia_mira_e2e/authority-runtime/" "persona-self-binding-store-v1"
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

    root = tmp_path_factory.mktemp("psb-authority") / "persona-self-binding"
    rebind(authority_root, REAL_PSB_ROOT, root)
    return root


def test_composition_uses_durable_authority_and_isolated_store(
    authority_root, psb_store_root, tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    store = tmp_path / "isolated" / "conversations.json"
    composition = compose(
        authority_root,
        store,
        psb_store_root,
    )

    assert isinstance(composition.identity_repository, IdentityRepository)
    assert isinstance(composition.memory_repository, MemoryExperienceRepository)
    assert isinstance(composition.conversation_runtime, ConversationRuntime)
    assert isinstance(composition.assistant_runtime, JuliaAssistantRuntime)
    assert composition.conversation_store_path == store
    assert composition.authority_root == authority_root
    assert composition.psb_store_root == psb_store_root

    composition.conversation_runtime.create_conversation("mira-p1b")
    assert store.is_file()
    assert not (tmp_path / "data" / "conversations.json").exists()
    assert "mira-p1b" in store.read_text(encoding="utf-8")


def test_composition_evidence_is_exact_golden_mira(
    authority_root, psb_store_root, tmp_path
) -> None:
    evidence = compose(
        authority_root, tmp_path / "conversations.json", psb_store_root
    ).evidence()
    assert evidence.persona_id == "golden-mira"
    assert evidence.identity_count == 4
    assert evidence.memory_experience_count == 8
    assert evidence.ordered_identity_refs == EXPECTED_IDENTITY_REFS
    assert evidence.ordered_memory_experience_refs == EXPECTED_MEMORY_REFS
    assert (
        evidence.c03_contract_version
        == "julia_core.context_admission.c03.production.v3"
    )
    assert evidence.binder.__name__ == "ExactPersonaSelfBoundSemanticBinder"
    assert evidence.active_persona_self_binding_id == (
        "golden-mira-persona-self-binding-v1"
    )
    assert evidence.active_persona_self_binding_version == "v2"
    assert evidence.active_persona_self_binding_digest == (
        "a6167069289a0704b207292cd44a509a8f6e2844a143e5dbb7673fbcac38b525"
    )
    assert evidence.active_persona_self_binding_projected_digest == (
        "121cb15164a6871f0f9d4546d378ab1224cf854ef13d376638f0144763aadb1a"
    )
    assert evidence.sha_pins_matched is True
    assert evidence.provider_transport_called is False


def test_repositories_restore_exact_admitted_records_in_order(
    authority_root, psb_store_root, tmp_path
) -> None:
    composition = compose(
        authority_root, tmp_path / "conversations.json", psb_store_root
    )
    for canonical_ref, version in zip(
        EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS
    ):
        governed = composition.identity_repository.resolve(
            IdentityRef(lineage_id=canonical_ref, version_id=version)
        )
        assert governed.status.value == "ADMITTED"
    for canonical_ref, version in zip(EXPECTED_MEMORY_REFS, EXPECTED_MEMORY_VERSIONS):
        governed = composition.memory_repository.resolve(
            MemoryExperienceRef(experience_id=canonical_ref, version_id=version)
        )
        assert governed.status.value == "ADMITTED"


def test_prepare_reaches_production_envelope_without_transport(
    authority_root, psb_store_root, tmp_path, monkeypatch
) -> None:
    def no_network(*args, **kwargs):
        raise AssertionError("provider transport was called during P1-B preparation")

    monkeypatch.setattr(socket, "socket", no_network)
    composition = compose(
        authority_root, tmp_path / "conversations.json", psb_store_root
    )
    raw_input = "Hi Mira，还记得我吗？"
    envelope = composition.prepare_provider_envelope(
        MiraProviderEnvelopeRequest(
            conversation_id="mira-p1b",
            turn_id="turn-001",
            task_domain="isolated-runtime-composition",
            input_mode="text",
            input_text=raw_input,
            observed_at="2026-09-14T00:00:00Z",
            provider_id="deepseek",
        )
    )
    assert isinstance(envelope, ProviderExecutionEnvelope)
    assert envelope.conversation_id == "mira-p1b"
    assert envelope.turn_id == "turn-001"
    assert envelope.alignment.provider_id == "deepseek"
    assert [message["role"] for message in envelope.messages] == [
        "system",
        "system",
        "system",
        "system",
        "user",
    ]
    psb_projection = json.loads(envelope.messages[0]["content"])
    current_task = json.loads(envelope.messages[4]["content"])
    assert psb_projection["identity_ownership"]["ownership_role"] == (
        "CURRENT_SELF_IDENTITY"
    )
    assert psb_projection["experience_ownership"]["ownership_role"] == (
        "CURRENT_SELF_EXPERIENCE"
    )
    assert psb_projection["execution_substrate_policy"] == {
        "role": "EXECUTION_SUBSTRATE",
        "provider_is_persona_self": False,
        "provider_neutral": True,
    }
    assert psb_projection["authority_precedence"] == {
        "identity_authority_source": "GOVERNED_BINDING",
        "current_task_identity_authority": "NONE",
        "provider_identity_authority": "NONE",
        "precedence_scope": "PERSONA_IDENTITY_AUTHORITY",
    }
    input_digest = hashlib.sha256(raw_input.encode("utf-8")).hexdigest()
    assert current_task["task_intent"] == raw_input
    assert current_task["bounded_state"]["input_sha256"] == input_digest
    assert (
        envelope.semantic_fingerprint
        == hashlib.sha256(
            json.dumps(
                list(envelope.messages),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
    )


def test_input_text_change_changes_c03_and_final_semantics(
    authority_root, psb_store_root, tmp_path
) -> None:
    composition = compose(
        authority_root, tmp_path / "conversations.json", psb_store_root
    )

    def envelope_for(input_text: str):
        return composition.prepare_provider_envelope(
            MiraProviderEnvelopeRequest(
                conversation_id="mira-p1b-input-change",
                turn_id="turn-001",
                task_domain="isolated-runtime-composition",
                input_mode="text",
                input_text=input_text,
                observed_at="2026-09-14T00:00:00Z",
                provider_id="deepseek",
            )
        )

    first = envelope_for("first exact user input")
    second = envelope_for("second exact user input")
    assert first.messages[0]["content"] == second.messages[0]["content"]
    assert first.messages[4]["content"] != second.messages[4]["content"]
    first_task_digest = _current_task_digest(first.messages[4]["content"])
    second_task_digest = _current_task_digest(second.messages[4]["content"])
    assert first_task_digest != second_task_digest
    assert first.gate_receipt != second.gate_receipt
    assert first.semantic_fingerprint != second.semantic_fingerprint
    assert [message["role"] for message in second.messages] == [
        "system",
        "system",
        "system",
        "system",
        "user",
    ]


def test_empty_conversation_store_path_fails_closed(authority_root) -> None:
    with pytest.raises(MiraCompositionError, match="explicit absolute Path"):
        compose(authority_root, Path(""))


def test_core_sha_mismatch_fails_closed() -> None:
    with pytest.raises(MiraCompositionError, match="Core SHA pin mismatch"):
        MiraRuntimeShaPins(
            expected_core_sha=SHA,
            observed_core_sha="1" * 64,
            expected_assistant_sha=SHA,
            observed_assistant_sha=SHA,
        )


def test_assistant_sha_mismatch_fails_closed() -> None:
    with pytest.raises(MiraCompositionError, match="Assistant SHA pin mismatch"):
        MiraRuntimeShaPins(
            expected_core_sha=SHA,
            observed_core_sha=SHA,
            expected_assistant_sha=SHA,
            observed_assistant_sha="1" * 64,
        )


def test_durable_authority_corruption_fails_closed(authority_root, tmp_path) -> None:
    corrupted = tmp_path / "corrupt-authority"
    shutil.copytree(authority_root, corrupted)
    manifest_path = corrupted / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_sha"] = "0" * 40
    manifest_path.chmod(0o600)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="manifest"):
        compose(corrupted, tmp_path / "conversations.json")


def test_composition_has_no_legacy_julia_dependency() -> None:
    source = (REPOSITORY / "julia_core" / "runtime" / "mira_composition.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imports = {
        node.names[0].name if isinstance(node, ast.Import) else node.module
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    }
    assert "julia_core.runtime.julia_session" not in imports
    assert not any(name.startswith("julia_core.narrative") for name in imports)
    assert not any(name.startswith("julia_core.runtime.persona") for name in imports)
    assert not any(
        name in {"requests", "httpx", "urllib", "urllib3", "http.client", "socket"}
        for name in imports
    )


def compose(
    authority_root: Path,
    conversation_store_path: Path,
    psb_store_root: Path = REAL_PSB_ROOT,
):
    return compose_golden_mira_runtime(
        authority_root=authority_root,
        conversation_store_path=conversation_store_path,
        psb_store_root=psb_store_root,
        sha_pins=MiraRuntimeShaPins(
            expected_core_sha=SHA,
            observed_core_sha=SHA,
            expected_assistant_sha=SHA,
            observed_assistant_sha=SHA,
        ),
    )


def _current_task_digest(content: str) -> str:
    canonical_content = json.dumps(
        json.loads(content),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_content.encode("utf-8")).hexdigest()

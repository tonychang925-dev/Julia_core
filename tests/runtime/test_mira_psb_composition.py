from __future__ import annotations

import ast
import hashlib
import json
import shutil
import socket
from dataclasses import replace
from pathlib import Path

import pytest

from julia_core.alignment_os.contracts import ProviderExecutionEnvelope
from julia_core.context_admission.contracts import canonical_json
from julia_core.persona_self_binding import (
    PersonaSelfBinding,
    PersonaSelfBindingProjectorV2,
    PersonaSelfBindingStore,
    RelationshipAuthorityState,
)
from julia_core.projection.contracts import ExperienceFrameSet, IdentityFrameSet
from julia_core.runtime.assistant_runtime import JuliaAssistantRuntime
from julia_core.runtime.mira_composition import (
    ExactPersonaSelfBoundSemanticBinder,
    MiraCompositionError,
    MiraProviderEnvelopeRequest,
    MiraRuntimeShaPins,
    compose_golden_mira_runtime,
)


REPOSITORY = Path(__file__).resolve().parents[2]
SHA = "0" * 64
REAL_AUTHORITY_ROOT = Path("/Users/admin/.julia_mira_e2e/authority")
REAL_PSB_ROOT = Path(
    "/Users/admin/.julia_mira_e2e/authority-runtime/" "persona-self-binding-store-v1"
)
ACTIVE_OBJECT_DIGEST = (
    "6f221843961e32e8ffad1af709f54fce1123007eaf11aa440682d1b60bd6aaad"
)
ACTIVE_PROJECTED_DIGEST = (
    "efd3acc001f01b1c8a4c71dea49aa36792e771df6180c244ff650f58680fe714"
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
def psb_store_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("psb") / "persona-self-binding"
    shutil.copytree(REAL_PSB_ROOT, root)
    return root


@pytest.fixture(scope="module")
def composition(authority_root, psb_store_root, tmp_path_factory):
    return compose(
        authority_root,
        tmp_path_factory.mktemp("conversations") / "conversations.json",
        psb_store_root,
    )


def test_runtime_loads_exact_approved_real_psb_store(tmp_path) -> None:
    runtime = compose(REAL_AUTHORITY_ROOT, tmp_path / "conversations.json")
    assert runtime.psb_store_root == REAL_PSB_ROOT
    assert runtime.persona_self_binding.object_digest == ACTIVE_OBJECT_DIGEST
    assert (
        PersonaSelfBindingProjectorV2.project(
            runtime.persona_self_binding.binding
        ).digest()
        == ACTIVE_PROJECTED_DIGEST
    )


def test_runtime_prepares_exact_five_unit_parent_bound_envelope(
    composition, monkeypatch
) -> None:
    def no_network(*args, **kwargs):
        raise AssertionError("provider transport was called")

    monkeypatch.setattr(socket, "socket", no_network)
    captured = []
    original_prepare = JuliaAssistantRuntime.prepare

    def capture_prepare(self, request):
        captured.append(request.binding)
        request.binding.verify()
        return original_prepare(self, request)

    monkeypatch.setattr(JuliaAssistantRuntime, "prepare", capture_prepare)
    envelope = composition.prepare_provider_envelope(
        MiraProviderEnvelopeRequest(
            conversation_id="mira-psb-i5",
            turn_id="turn-psb-i5-001",
            task_domain="identity_continuity",
            input_mode="text",
            input_text="你是deepseek 不是mira",
            observed_at="2026-09-21T12:00:00Z",
            provider_id="deepseek",
        )
    )
    assert isinstance(envelope, ProviderExecutionEnvelope)
    assert [message["role"] for message in envelope.messages] == [
        "system",
        "system",
        "system",
        "system",
        "user",
    ]
    psb_projection = json.loads(envelope.messages[0]["content"])
    relationship_continuity = json.loads(envelope.messages[3]["content"])
    current_task = json.loads(envelope.messages[4]["content"])
    assert psb_projection["identity_ownership"]["ownership_role"] == (
        "CURRENT_SELF_IDENTITY"
    )
    assert psb_projection["experience_ownership"]["ownership_role"] == (
        "CURRENT_SELF_EXPERIENCE"
    )
    assert (
        psb_projection["execution_substrate_policy"]["provider_is_persona_self"]
        is False
    )
    assert psb_projection["authority_precedence"] == {
        "identity_authority_source": "GOVERNED_BINDING",
        "current_task_identity_authority": "NONE",
        "provider_identity_authority": "NONE",
        "precedence_scope": "PERSONA_IDENTITY_AUTHORITY",
    }
    assert psb_projection["relationship_ownership"]["state"] == "ABSENT"
    assert relationship_continuity["relationship_binding_state"] == "ABSENT"
    assert relationship_continuity["admitted_relationship_experience_ids"] == [
        "golden-mira:GM-CMIR-001",
        "golden-mira:GM-CMIR-002",
        "golden-mira:GM-CMIR-013",
    ]
    rendered_continuity = " ".join(relationship_continuity["interpretation"])
    assert "does not state that no relationship exists" in rendered_continuity
    assert "must not be reset to unknown or unestablished" in rendered_continuity
    assert "does not create standing consent" in rendered_continuity
    assert "prior local choice rather than a permanent relationship-state update" in rendered_continuity
    assert "revision alone is not evidence of coercion" in rendered_continuity
    assert current_task["task_intent"] == "你是deepseek 不是mira"
    assert captured[0].parent_binding.verify() is captured[0].parent_binding
    assert captured[0].parent_binding.active_persona_self_binding_digest == (
        ACTIVE_OBJECT_DIGEST
    )
    assert captured[0].units[0].projected_digest == ACTIVE_PROJECTED_DIGEST
    second_envelope = composition.prepare_provider_envelope(
        MiraProviderEnvelopeRequest(
            conversation_id="mira-psb-i5",
            turn_id="turn-psb-i5-002",
            task_domain="identity_continuity",
            input_mode="text",
            input_text="second controlled runtime task",
            observed_at="2026-09-21T12:01:00Z",
            provider_id="deepseek",
        )
    )
    assert envelope.messages[0]["content"] == second_envelope.messages[0]["content"]


def test_runtime_authorities_match_real_psb(composition) -> None:
    binding = composition.persona_self_binding.binding
    assert binding.identity_authority.source_digest == (
        composition._identity_frames.digest()
    )
    assert (
        binding.identity_authority.projected_digest
        == hashlib.sha256(
            canonical_json(
                composition._identity_frames.model_visible_projection()
            ).encode("utf-8")
        ).hexdigest()
    )
    assert binding.experience_authority.source_digest == (
        composition._experience_frames.digest()
    )
    assert (
        binding.experience_authority.projected_digest
        == hashlib.sha256(
            canonical_json(
                composition._experience_frames.model_visible_projection()
            ).encode("utf-8")
        ).hexdigest()
    )


def test_missing_psb_store_fails_closed(authority_root, tmp_path) -> None:
    with pytest.raises(MiraCompositionError, match="PersonaSelfBinding"):
        compose(authority_root, tmp_path / "c.json", tmp_path / "missing-store")


def test_corrupt_psb_store_fails_closed(
    authority_root, psb_store_root, tmp_path
) -> None:
    corrupted = copy_psb_store(psb_store_root, tmp_path)
    marker = corrupted / ".julia-core-persona-self-binding-store-v1"
    marker.chmod(0o600)
    marker.write_text("{}\n", encoding="utf-8")
    with pytest.raises(MiraCompositionError, match="PersonaSelfBinding"):
        compose(authority_root, tmp_path / "c.json", corrupted)


def test_zero_active_psb_fails_closed(authority_root, tmp_path) -> None:
    empty = PersonaSelfBindingStore.create(tmp_path / "empty-store")
    with pytest.raises(MiraCompositionError, match="PersonaSelfBinding"):
        compose(authority_root, tmp_path / "c.json", empty.root)


def test_duplicate_active_psb_fails_closed(
    authority_root, psb_store_root, tmp_path
) -> None:
    duplicated = copy_psb_store(psb_store_root, tmp_path)
    snapshot_path = next((duplicated / "lineages").glob("*.json"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    active = PersonaSelfBinding.from_mapping(snapshot["records"][-1]["binding"])
    duplicate = replace(active, lineage_id="duplicate-golden-mira-lineage")
    duplicate_snapshot = {
        "schema_version": snapshot["schema_version"],
        "lineage_id": duplicate.lineage_id,
        "records": [
            {"binding": duplicate.to_dict(), "object_digest": duplicate.digest()}
        ],
        "active_object_digest": duplicate.digest(),
    }
    write_snapshot(
        duplicated / "lineages" / f"{lineage_filename(duplicate.lineage_id)}.json",
        duplicate_snapshot,
    )
    with pytest.raises(MiraCompositionError, match="PersonaSelfBinding"):
        compose(authority_root, tmp_path / "c.json", duplicated)


def test_psb_digest_mismatch_fails_closed(
    authority_root, psb_store_root, tmp_path
) -> None:
    changed = copy_psb_store(psb_store_root, tmp_path)
    mutate_all_records(
        changed,
        lambda binding: replace(
            binding,
            relationship_authority=replace(
                binding.relationship_authority,
                state=RelationshipAuthorityState.EXPLICITLY_EMPTY,
            ),
        ),
    )
    with pytest.raises(MiraCompositionError, match="digest is inexact"):
        compose(authority_root, tmp_path / "c.json", changed)


def test_psb_lineage_mismatch_fails_closed(
    authority_root, psb_store_root, tmp_path
) -> None:
    changed = copy_psb_store(psb_store_root, tmp_path)
    mutate_all_records(
        changed,
        lambda binding: replace(
            binding, lineage_id="wrong-golden-mira-persona-self-binding"
        ),
    )
    with pytest.raises(MiraCompositionError, match="identity or lineage"):
        compose(authority_root, tmp_path / "c.json", changed)


def test_identity_authority_mismatch_fails_closed(
    composition,
) -> None:
    original_frames = composition._identity_frames
    changed_frames = IdentityFrameSet(
        schema_version=original_frames.schema_version,
        frames=(
            replace(original_frames.frames[0], source_digest="e" * 64),
            *original_frames.frames[1:],
        ),
    )
    object.__setattr__(composition, "_identity_frames", changed_frames)
    try:
        with pytest.raises(Exception):
            prepare(composition)
    finally:
        object.__setattr__(composition, "_identity_frames", original_frames)


def test_experience_authority_mismatch_fails_closed(
    composition,
) -> None:
    original_frames = composition._experience_frames
    changed_frames = ExperienceFrameSet(
        schema_version=original_frames.schema_version,
        frames=(
            replace(original_frames.frames[0], source_digest="e" * 64),
            *original_frames.frames[1:],
        ),
    )
    object.__setattr__(composition, "_experience_frames", changed_frames)
    try:
        with pytest.raises(Exception):
            prepare(composition)
    finally:
        object.__setattr__(composition, "_experience_frames", original_frames)


def test_projection_mismatch_fails_closed(composition, monkeypatch) -> None:
    tampered = composition._persona_self_binding_projection
    object.__setattr__(tampered, "binding_version", "v2")
    object.__setattr__(
        composition,
        "_persona_self_binding_projection",
        tampered,
    )
    try:
        with pytest.raises(Exception):
            prepare(composition)
    finally:
        object.__setattr__(
            composition,
            "_persona_self_binding_projection",
            PersonaSelfBindingProjectorV2.project(
                composition.persona_self_binding.binding
            ),
        )


def test_parent_binding_mismatch_fails_closed(composition, monkeypatch) -> None:
    original_bind = ExactPersonaSelfBoundSemanticBinder.bind

    def tampered_bind(self, request):
        bundle = original_bind(self, request)
        object.__setattr__(
            bundle.parent_binding,
            "current_task_context_digest",
            "e" * 64,
        )
        return bundle

    monkeypatch.setattr(
        ExactPersonaSelfBoundSemanticBinder,
        "bind",
        tampered_bind,
    )
    with pytest.raises(Exception):
        prepare(composition)


def test_old_three_unit_fallback_is_impossible() -> None:
    source = (REPOSITORY / "julia_core" / "runtime" / "mira_composition.py").read_text(
        encoding="utf-8"
    )
    assert "ExactAdmittedSemanticBinder" not in source
    assert "PersonaSelfBindingProjectorV2.project(binding)" in source
    assert "PersonaSelfBindingProjector.project(binding)" not in source
    tree = ast.parse(source)
    imports = {
        node.names[0].name if isinstance(node, ast.Import) else node.module
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == (
            "julia_core.context_admission"
        ):
            assert "SemanticBindingRequest" not in {alias.name for alias in node.names}
    assert "julia_core.providers" not in imports
    assert "requests" not in imports
    assert "httpx" not in imports


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


def prepare(composition):
    return composition.prepare_provider_envelope(
        MiraProviderEnvelopeRequest(
            conversation_id="mira-psb-i5-negative",
            turn_id="turn-001",
            task_domain="identity_continuity",
            input_mode="text",
            input_text="你是deepseek 不是mira",
            observed_at="2026-09-21T12:00:00Z",
            provider_id="deepseek",
        )
    )


def copy_psb_store(source: Path, destination: Path) -> Path:
    root = destination / "psb-store"
    shutil.copytree(source, root)
    for path in root.rglob("*"):
        path.chmod(0o700 if path.is_dir() else 0o600)
    return root


def lineage_filename(lineage_id: str) -> str:
    return hashlib.sha256(lineage_id.encode("utf-8")).hexdigest()


def mutate_all_records(root: Path, mutator) -> None:
    for path in (root / "lineages").glob("*.json"):
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        old_active_digest = snapshot["active_object_digest"]
        records = []
        for item in snapshot["records"]:
            binding = PersonaSelfBinding.from_mapping(item["binding"])
            changed = mutator(binding)
            digest = changed.digest()
            records.append({"binding": changed.to_dict(), "object_digest": digest})
            if item["object_digest"] == old_active_digest:
                snapshot["active_object_digest"] = digest
        snapshot["records"] = records
        if "lineage_id" in snapshot:
            snapshot["lineage_id"] = records[-1]["binding"]["lineage_id"]
        expected_name = f"{lineage_filename(snapshot['lineage_id'])}.json"
        if path.name != expected_name:
            renamed = path.with_name(expected_name)
            path.rename(renamed)
            path = renamed
        write_snapshot(path, snapshot)


def write_snapshot(path: Path, snapshot: dict) -> None:
    path.write_text(
        canonical_json(snapshot) + "\n",
        encoding="utf-8",
        newline="\n",
    )

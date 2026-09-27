from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from julia_core.durable_authority.contracts import (
    AuthorityFamily,
    DurableAuthorityPersistenceError,
)
from julia_core.durable_authority.golden_mira_v2 import (
    ACTIVE_MEMORY_REFS_V2,
    ACTIVE_MEMORY_VERSIONS_V2,
    GoldenMiraDurableAuthorityV2Reader,
)
from julia_core.durable_authority.reconstruction import reconstruct_from_durable_authority
from julia_core.memory_experience import MemoryExperienceRef
from julia_core.persona_self_binding import PersonaSelfBindingStore
from tools.continuity.p5_e_semantic_fidelity_admission import (
    EXPECTED_PREDECESSOR_DIGEST,
    PREDECESSOR_REF,
    SUCCESSOR_REF,
    P5ESemanticFidelityAdmissionError,
    execute,
)


REPOSITORY = Path(__file__).resolve().parents[2]
PSB_V2_FIXTURE = REPOSITORY / "tests/fixtures/golden_mira_psb_v2"
EXPECTED_SUCCESSOR_DIGEST = (
    "28329e1c2f1a676aeaf787864ba7c20185f9b830dd13d5c04ec81334eae31452"
)
EXPECTED_PSB_V3_DIGEST = (
    "597988dd5338e63f92227a9682db312dccd5f88a0a9ffc31ef4df00eab5b6cd1"
)


@pytest.fixture()
def source_authority(tmp_path: Path) -> Path:
    from tools.continuity.export_golden_mira_durable_authority import _package

    root = tmp_path / "source-authority"
    receipt = tmp_path / "source-authority-receipt.json"
    _package(
        repository=REPOSITORY,
        authority_root=root,
        receipt_output=receipt,
        owner_authorization="GRANTED",
    )
    return root


@pytest.fixture()
def admitted_candidate(tmp_path: Path, source_authority: Path):
    authority_v2 = tmp_path / "authority-v2"
    psb_v3 = tmp_path / "psb-v3"

    source_authority_digest_before = _tree_digest(source_authority)
    source_psb_digest_before = _tree_digest(PSB_V2_FIXTURE)

    result = execute(
        repository=REPOSITORY,
        source_authority_root=source_authority,
        source_psb_root=PSB_V2_FIXTURE,
        target_authority_root=authority_v2,
        target_psb_root=psb_v3,
    )

    assert _tree_digest(source_authority) == source_authority_digest_before
    assert _tree_digest(PSB_V2_FIXTURE) == source_psb_digest_before
    return result, authority_v2, psb_v3, source_authority


def test_p5e_semantic_fidelity_transaction_roundtrip_is_exact(
    admitted_candidate,
) -> None:
    result, authority_v2, psb_v3, _ = admitted_candidate

    assert result["final_result"] == (
        "P5_E_SEMANTIC_FIDELITY_SUCCESSOR_ADMISSION_AND_PSB_V3_REBIND_COMPLETE"
    )
    assert result["predecessor"] == {
        "ref": PREDECESSOR_REF.uri,
        "digest": EXPECTED_PREDECESSOR_DIGEST,
        "final_status": "SUPERSEDED",
    }
    assert result["successor"] == {
        "ref": SUCCESSOR_REF.uri,
        "digest": EXPECTED_SUCCESSOR_DIGEST,
        "final_status": "ADMITTED",
    }
    assert result["authority"] == {
        "production_cutover": 0,
        "identity_mutation": 0,
        "relationship_authority_mutation": 0,
        "other_memory_experience_payload_mutation": 0,
    }

    reader = GoldenMiraDurableAuthorityV2Reader(authority_v2)
    identities, memories = reconstruct_from_durable_authority(reader)

    predecessor = memories.resolve(PREDECESSOR_REF)
    successor = memories.resolve(SUCCESSOR_REF)
    assert predecessor.status.value == "SUPERSEDED"
    assert predecessor.record.digest() == EXPECTED_PREDECESSOR_DIGEST
    assert successor.status.value == "ADMITTED"
    assert successor.record.digest() == EXPECTED_SUCCESSOR_DIGEST

    assert reader.active_memory_refs == ACTIVE_MEMORY_REFS_V2
    assert reader.active_memory_versions == ACTIVE_MEMORY_VERSIONS_V2
    assert len(reader.list_exact_refs(AuthorityFamily.IDENTITY)) == 4
    assert len(reader.list_exact_refs(AuthorityFamily.MEMORY_EXPERIENCE)) == 9

    for ref, version in zip(ACTIVE_MEMORY_REFS_V2, ACTIVE_MEMORY_VERSIONS_V2):
        governed = memories.resolve(
            MemoryExperienceRef(experience_id=ref, version_id=version)
        )
        assert governed.status.value == "ADMITTED"

    active_psb = PersonaSelfBindingStore(psb_v3).resolve_active("golden-mira")
    assert active_psb.binding.binding_version == "v3"
    assert active_psb.object_digest == EXPECTED_PSB_V3_DIGEST
    assert (
        active_psb.binding.experience_authority.source_digest
        == result["active_experience_frame_set"]["source_digest"]
    )
    assert (
        active_psb.binding.experience_authority.projected_digest
        == result["active_experience_frame_set"]["projected_digest"]
    )

    manifest = json.loads((authority_v2 / "manifest.json").read_text(encoding="utf-8"))
    current_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert manifest["source_sha"] == current_head
    assert reader.source_sha == current_head
    assert manifest["memory_experience_count"] == 9
    assert manifest["active_memory_experience_refs"] == list(ACTIVE_MEMORY_REFS_V2)
    assert manifest["active_memory_experience_versions"] == list(
        ACTIVE_MEMORY_VERSIONS_V2
    )
    assert result["durable_manifest_digest"] == manifest["manifest_digest"]


def test_v2_reader_fails_closed_when_predecessor_record_is_missing(
    admitted_candidate, tmp_path: Path
) -> None:
    _, authority_v2, _, _ = admitted_candidate
    tampered = tmp_path / "tampered-authority-v2"
    shutil.copytree(authority_v2, tampered)
    _make_writable(tampered)

    (tampered / "memory_experience/00000002.json").unlink()

    with pytest.raises(DurableAuthorityPersistenceError):
        GoldenMiraDurableAuthorityV2Reader(tampered)


def test_transaction_refuses_reusing_existing_target_roots(
    admitted_candidate,
) -> None:
    _, authority_v2, psb_v3, source_authority = admitted_candidate

    with pytest.raises(
        P5ESemanticFidelityAdmissionError,
        match="target PSB root must not exist",
    ):
        execute(
            repository=REPOSITORY,
            source_authority_root=source_authority,
            source_psb_root=PSB_V2_FIXTURE,
            target_authority_root=authority_v2,
            target_psb_root=psb_v3,
        )


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _make_writable(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        path.chmod(0o700 if path.is_dir() else 0o600)
    root.chmod(0o700)

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from tools.continuity.export_golden_mira_durable_authority import _package
from tools.continuity.p5_e_semantic_fidelity_admission import execute
from julia_core.runtime.mira_composition import MiraCompositionError
from tools.continuity.p6_eng19_canonical_only_runtime_canary import (
    CanonicalOnlyCanaryError,
    EXPECTED_IDENTITY_COUNT,
    EXPECTED_MEMORY_COUNT,
    EXPECTED_PSB_VERSION,
    EXPECTED_SUCCESSOR,
    git_head,
    prepare_canonical_canary,
    tree_digest,
)


REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY / "tools/continuity/p6_eng19_canonical_only_runtime_canary.py"
PSB_V2_FIXTURE = REPOSITORY / "tests/fixtures/golden_mira_psb_v2"
ASSISTANT_SHA = "1" * 40


def test_eng19_cli_direct_script_bootstraps_repository_imports() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--authority-root" in result.stdout
    assert "--assistant-sha" in result.stdout


@pytest.fixture()
def canonical_candidate(tmp_path: Path):
    source_authority = tmp_path / "source-authority"
    source_receipt = tmp_path / "source-authority-receipt.json"
    _package(
        repository=REPOSITORY,
        authority_root=source_authority,
        receipt_output=source_receipt,
        owner_authorization="GRANTED",
    )

    authority_v2 = tmp_path / "authority-v2"
    psb_v3 = tmp_path / "psb-v3"
    result = execute(
        repository=REPOSITORY,
        source_authority_root=source_authority,
        source_psb_root=PSB_V2_FIXTURE,
        target_authority_root=authority_v2,
        target_psb_root=psb_v3,
    )
    return authority_v2, psb_v3, result


def test_eng19_preparation_binds_exact_current_authority_without_mutation(
    tmp_path: Path,
    canonical_candidate,
) -> None:
    authority_v2, psb_v3, result = canonical_candidate
    authority_before = tree_digest(authority_v2)
    psb_before = tree_digest(psb_v3)

    prepared = prepare_canonical_canary(
        repository=REPOSITORY,
        authority_root=authority_v2,
        psb_store_root=psb_v3,
        assistant_sha=ASSISTANT_SHA,
        conversation_store_path=tmp_path / "conversations.json",
    )

    assert prepared.repository_head == git_head(REPOSITORY)
    assert prepared.authority_manifest_digest == result["durable_manifest_digest"]
    assert len(prepared.ordered_identity_refs) == EXPECTED_IDENTITY_COUNT
    assert len(prepared.active_memory_pairs) == EXPECTED_MEMORY_COUNT
    assert EXPECTED_SUCCESSOR in prepared.active_memory_pairs
    assert (
        prepared.composition.evidence().active_persona_self_binding_version
        == EXPECTED_PSB_VERSION
    )
    assert prepared.active_psb_digest == result["psb_v3"]["object_digest"]
    assert (
        prepared.active_psb_projected_digest
        == result["psb_v3"]["projected_digest"]
    )
    assert tree_digest(authority_v2) == authority_before
    assert tree_digest(psb_v3) == psb_before


def test_eng19_preparation_rejects_core_sha_other_than_repository_head(
    tmp_path: Path,
    canonical_candidate,
) -> None:
    authority_v2, psb_v3, _ = canonical_candidate

    with pytest.raises(
        CanonicalOnlyCanaryError,
        match="selected Core SHA does not match repository HEAD",
    ):
        prepare_canonical_canary(
            repository=REPOSITORY,
            authority_root=authority_v2,
            psb_store_root=psb_v3,
            assistant_sha=ASSISTANT_SHA,
            core_sha="2" * 40,
            conversation_store_path=tmp_path / "conversations.json",
        )


def test_eng19_preparation_rejects_non_v3_psb_store(
    tmp_path: Path,
    canonical_candidate,
) -> None:
    authority_v2, _, _ = canonical_candidate

    with pytest.raises(
        MiraCompositionError,
        match="active PersonaSelfBinding identity or lineage is inexact",
    ):
        prepare_canonical_canary(
            repository=REPOSITORY,
            authority_root=authority_v2,
            psb_store_root=PSB_V2_FIXTURE,
            assistant_sha=ASSISTANT_SHA,
            conversation_store_path=tmp_path / "conversations.json",
        )

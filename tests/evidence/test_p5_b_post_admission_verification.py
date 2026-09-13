from __future__ import annotations

from pathlib import Path

from tests.evidence.p5_b_post_admission_canonical_verification import verify


REPOSITORY = Path(__file__).resolve().parents[2]
HARNESS = REPOSITORY / "tests/evidence/p5_b_post_admission_canonical_verification.py"


def test_p5_b_verifies_exact_admitted_canonical_state() -> None:
    result = verify(REPOSITORY)

    assert result["counts"] == {
        "identity_refs_verified": "3/3",
        "memory_refs_verified": "8/8",
        "exact_ref_resolution": "11/11",
        "digest_identity": "11/11",
        "admitted_status": "11/11",
        "governance_order": "11/11",
    }
    assert result["project_commitment_lineage"]["result"] == "PASS"
    assert result["semantic_boundaries"] == {
        "quarantined_cmir_ids_present": 0,
        "tony_autobiography_is_mira_identity": False,
        "historical_intimacy_is_standing_consent": False,
        "remembered_commitment_is_runtime_authorization": False,
        "result": "PASS",
    }
    assert result["authority_isolation"] == {
        "canonical_writes": 0,
        "runtime_or_provider_writes": 0,
        "production_response_selection_authority": 0,
        "legacy_destructive_writes": 0,
        "implicit_fallback_selection": 0,
    }
    assert result["final_result"] == ("P5_B_POST_ADMISSION_CANONICAL_STATE_VERIFIED")


def test_p5_b_verification_is_deterministic() -> None:
    assert verify(REPOSITORY) == verify(REPOSITORY)


def test_p5_b_harness_remains_read_only() -> None:
    source = HARNESS.read_text(encoding="utf-8")

    assert ".store_candidate(" not in source
    assert ".admit(" not in source
    assert ".supersede(" not in source
    assert ".retire(" not in source
    assert "IdentityRepository" not in source
    assert "MemoryExperienceRepository" not in source
    assert "write_text" in source

from __future__ import annotations

import json
from pathlib import Path

from tools.mira_migration import simulate_admission


REPOSITORY = Path(__file__).resolve().parents[2]


def test_simulation_has_exact_ten_candidate_dispositions() -> None:
    result = simulate_admission(REPOSITORY)
    dispositions = {item["candidate_id"]: item["disposition"] for item in result["candidates"]}

    assert result["status"] == "SIMULATION_COMPLETE_FAIL_CLOSED_NO_ADMISSION"
    assert result["summary"] == {
        "candidate_count": 10,
        "identity_candidates": 3,
        "memory_candidates": 7,
        "memory_record_count": 8,
        "canonical_compatible": 6,
        "canonical_incompatible": 4,
        "identity_compatible": 3,
        "narrative_compatible": 3,
        "relationship_incompatible": 3,
        "project_commitment_incompatible": 1,
        "raw_assertions": 42,
        "unique_binding_ids": 40,
        "global_disposition": "BLOCKED_CANONICAL_V2_ALIGNMENT_REQUIRED",
        "actual_admission": 0,
    }
    assert {
        candidate_id: value.startswith("PASS_")
        for candidate_id, value in dispositions.items()
    } == {
        "MIRA-ID-CAND-001": True,
        "MIRA-ID-CAND-002": True,
        "MIRA-ID-CAND-003": True,
        "MIRA-MEM-CAND-001": False,
        "MIRA-MEM-CAND-002": False,
        "MIRA-MEM-CAND-003": True,
        "MIRA-MEM-CAND-004": True,
        "MIRA-MEM-CAND-005": True,
        "MIRA-MEM-CAND-006": False,
        "MIRA-MEM-CAND-007": False,
    }


def test_v2_memory_candidates_fail_closed_without_v1_truncation() -> None:
    result = simulate_admission(REPOSITORY)
    by_candidate = {item["candidate_id"]: item for item in result["candidates"]}
    relationship_fields = [
        "causal_status",
        "corrected_judgment",
        "judgment_binding_role_refs",
        "later_reinterpretation",
        "policy_transfer",
        "prior_judgment",
        "significance",
        "subject_boundary",
    ]
    project_fields = [
        "applicability",
        "binding_role_refs",
        "commitment_stage",
        "interpretation",
        "revision",
        "significance",
        "trigger_event",
    ]

    for candidate_id in ("MIRA-MEM-CAND-001", "MIRA-MEM-CAND-002", "MIRA-MEM-CAND-007"):
        item = by_candidate[candidate_id]
        assert item["canonical_construction"] == "BLOCKED_NO_SUBSTITUTE"
        assert item["unsupported_fields_by_record"] == {"v0.2-preview": relationship_fields}
        assert item["expected_canonical_ref"] is None
        assert item["expected_post_store_status"] is None
        assert item["exact_provenance"]["status"] == "PASS"
        assert item["lineage_validation"]["status"] == "PASS"

    commitment = by_candidate["MIRA-MEM-CAND-006"]
    assert commitment["record_count"] == 2
    assert commitment["unsupported_fields_by_record"] == {
        "formation-draft-preview": project_fields,
        "frozen-final-preview": project_fields,
    }
    assert commitment["lineage_validation"] == {
        "status": "PASS",
        "kind": "PROJECT_COMMITMENT_TWO_RECORD_LINEAGE",
    }


def test_compatible_candidates_reconstruct_exact_refs_and_digests() -> None:
    result = simulate_admission(REPOSITORY)
    by_candidate = {item["candidate_id"]: item for item in result["candidates"]}

    identity_refs = {
        "MIRA-ID-CAND-001": "identity://mira-golden%3Amira-id-cand-001/mira-id-cand-001-v0.1-preview",
        "MIRA-ID-CAND-002": "identity://mira-golden%3Amira-id-cand-002/mira-id-cand-002-v0.1-preview",
        "MIRA-ID-CAND-003": "identity://mira-golden%3Amira-id-cand-003/mira-id-cand-003-v0.1-preview",
    }
    for candidate_id, expected_ref in identity_refs.items():
        item = by_candidate[candidate_id]
        assert item["canonical_construction"] == "PASS"
        assert item["preview_digest"] == item["constructed_digest"]
        assert item["preview_ref"] == expected_ref
        assert item["expected_canonical_ref"] == expected_ref
        assert item["expected_post_store_status"] == "CANDIDATE"
        assert item["actual_status"] == "NOT_STORED_NOT_ADMITTED"

    for candidate_id, expected_ref in {
        "MIRA-MEM-CAND-003": "memory-experience://golden-mira:GM-CMIR-004/v0.1-preview",
        "MIRA-MEM-CAND-004": "memory-experience://golden-mira:GM-CMIR-006/v0.1-preview",
        "MIRA-MEM-CAND-005": "memory-experience://golden-mira:GM-CMIR-008/v0.1-preview",
    }.items():
        item = by_candidate[candidate_id]
        assert item["canonical_construction"] == "PASS"
        assert item["preview_digests"] == item["constructed_digests"]
        assert item["preview_refs"] == [expected_ref]
        assert item["expected_canonical_refs"] == [expected_ref]
        assert item["expected_candidate_governance_events"] == [
            {
                "version_id": expected_ref.rsplit("/", 1)[1],
                "candidate_status": "CANDIDATE",
                "candidate_governance_tuple": ["CANDIDATE", None],
            }
        ]


def test_exact_provenance_authority_and_zero_write_gates() -> None:
    result = simulate_admission(REPOSITORY)
    source = (REPOSITORY / "tools/mira_migration/admission_sim.py").read_text(
        encoding="utf-8"
    )
    canonical_memory = (
        REPOSITORY / "julia_core/memory_experience/contracts.py"
    ).read_text(encoding="utf-8")

    assert all(item["exact_provenance"]["status"] == "PASS" for item in result["candidates"])
    assert all(item["no_authority_upgrade"] == "PASS" for item in result["candidates"])
    assert result["global_validation"] == {
        "candidate_ids_exact": True,
        "exact_provenance": "PASS",
        "all_assertions_consumed": True,
        "unbound_cmir_quarantine": "PASS",
        "no_authority_upgrade": "PASS",
        "no_fallback": "PASS",
        "no_mock_or_stub": "PASS",
        "no_silent_degrade": "PASS",
    }
    assert result["zero_write_proof"]["canonical_writes"] == 0
    assert result["zero_write_proof"]["store_candidate_calls"] == 0
    assert result["zero_write_proof"]["admit_calls"] == 0
    assert result["zero_write_proof"]["runtime_writes"] == 0
    assert "from julia_core.identity.repository" not in source
    assert "from julia_core.memory_experience.repository" not in source
    assert "store_candidate(" not in source
    assert ".admit(" not in source
    assert "except " not in source
    assert "class CausalStatus" not in canonical_memory
    assert "class CommitmentStage" not in canonical_memory
    assert "class SubjectBoundary" not in canonical_memory


def test_simulation_is_deterministic() -> None:
    first = simulate_admission(REPOSITORY)
    second = simulate_admission(REPOSITORY)

    assert first == second
    assert first["deterministic_digest"] == second["deterministic_digest"]
    first_bytes = (json.dumps(first, ensure_ascii=False, indent=2) + "\n").encode()
    second_bytes = (json.dumps(second, ensure_ascii=False, indent=2) + "\n").encode()
    assert first_bytes == second_bytes

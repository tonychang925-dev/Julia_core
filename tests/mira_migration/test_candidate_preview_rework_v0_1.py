from __future__ import annotations

import json
from pathlib import Path

from tools.mira_migration.compiler import compile_preview


REPOSITORY = Path(__file__).resolve().parents[2]
PACKAGE = REPOSITORY / "artifacts/mira_migration_prep/MIRA_MIGRATION_PREP_PACKAGE_V1.json"
LEDGER = REPOSITORY / "artifacts/mira_migration_prep/MIRA_MIGRATION_EVIDENCE_LEDGER_V1.json"
DRY_RUN = REPOSITORY / "artifacts/mira_migration_prep/MIRA_MIGRATION_DRY_RUN_RESULT_V1.json"
PRIOR_PREVIEW = REPOSITORY / "artifacts/mira_migration_prep/MIGRATION_TYPED_CANDIDATE_PREVIEW_V0_1.json"
SCHEMA_SHA = "1a630c2ac8809c5b064991dfcd87bebcd07d58ac"


def compiled() -> dict:
    return compile_preview(PACKAGE, LEDGER, DRY_RUN, schema_sha=SCHEMA_SHA)


def prior() -> dict:
    return json.loads(PRIOR_PREVIEW.read_text(encoding="utf-8"))


def candidate_map(payload: dict, field: str) -> dict[str, dict]:
    return {item["candidate_id"]: item for item in payload[field]}


def ledger_binding_times() -> dict[str, float]:
    value = json.loads(LEDGER.read_text(encoding="utf-8"))
    return {
        row["binding_id"]: float(row["create_time"])
        for row in value["bindings"]
        if row["chain_id"] == "GM-CMIR-011"
    }


def test_r1_corrects_subject_boundary_without_other_candidate_loss() -> None:
    old = candidate_map(prior(), "memory_experience_previews")["MIRA-MEM-CAND-001"]
    new = candidate_map(compiled(), "memory_experience_previews")["MIRA-MEM-CAND-001"]
    old_content = old["canonical_preview"]["payload"]["content"]
    new_content = new["canonical_preview"]["payload"]["content"]

    assert new_content["subject_boundary"] == {
        "semantic_subject": "MIRA",
        "observed_subject": "TONY",
        "autobiographical_owner": "TONY",
    }
    for field in ("event", "corrected_judgment", "policy_transfer"):
        assert new_content[field] == old_content[field]
    assert new["canonical_preview"]["payload"]["provenance_refs"] == (
        old["canonical_preview"]["payload"]["provenance_refs"]
    )


def test_r2_marks_candidate_002_policy_transfer_not_applicable() -> None:
    old = candidate_map(prior(), "memory_experience_previews")["MIRA-MEM-CAND-002"]
    new = candidate_map(compiled(), "memory_experience_previews")["MIRA-MEM-CAND-002"]
    old_content = old["canonical_preview"]["payload"]["content"]
    new_content = new["canonical_preview"]["payload"]["content"]

    assert new_content["policy_transfer"] == {
        "coverage": "NOT_APPLICABLE",
        "reason": (
            "The unchanged-bones reinterpretation records historical relationship "
            "continuity; no future policy transfer is claimed."
        ),
    }
    assert new_content["later_reinterpretation"] == old_content["later_reinterpretation"]
    assert new["exact_binding_coverage"] == {
        "assertions": 9,
        "unique_binding_ids": 7,
        "status": "PASS",
    }
    assert new["canonical_preview"]["payload"]["provenance_refs"] == (
        old["canonical_preview"]["payload"]["provenance_refs"]
    )


def test_r3_emits_exact_nonrewriting_two_record_commitment_lineage() -> None:
    item = candidate_map(compiled(), "memory_experience_previews")["MIRA-MEM-CAND-006"]
    lineage = item["canonical_preview"]
    formation = lineage["formation_record"]["canonical_preview"]["payload"]
    final = lineage["frozen_final_record"]["canonical_preview"]["payload"]
    formation_time = float(formation["created_at"].removeprefix("raw-create-time:"))
    final_time = float(final["created_at"].removeprefix("raw-create-time:"))

    assert lineage["type"] == "MemoryExperienceRecordLineage"
    assert formation["version_id"] == "formation-draft-preview"
    assert final["version_id"] == "frozen-final-preview"
    assert formation["content"]["commitment_stage"] == "FORMATION_DRAFT"
    assert final["content"]["commitment_stage"] == "FROZEN_FINAL"
    assert formation["predecessor_version_id"] is None
    assert formation["content"]["revision"] is None
    assert final["predecessor_version_id"] == formation["version_id"]
    assert final["content"]["revision"] == {
        "predecessor_ref": {
            "experience_id": formation["experience_id"],
            "version_id": formation["version_id"],
        },
        "supersession_scope": "Earlier checkpoint-draft L4 scope",
        "supersession_reason": (
            "Final Tony-reviewed Golden Mira checkpoint freezes the relationship-instance commitment"
        ),
        "rewrite_history": False,
    }
    assert formation_time == 1786851334.945
    assert final_time == 1787118449.26614
    binding_times = ledger_binding_times()
    assert [row["admission_metadata"]["binding_id"] for row in formation["provenance_refs"]] == [
        "GM-CMIR-011.EB-004"
    ]
    assert [row["admission_metadata"]["binding_id"] for row in final["provenance_refs"]] == [
        "GM-CMIR-011.EB-001",
        "GM-CMIR-011.EB-002",
        "GM-CMIR-011.EB-003",
    ]
    assert formation_time == binding_times["GM-CMIR-011.EB-004"]
    for row in formation["provenance_refs"]:
        assert binding_times[row["admission_metadata"]["binding_id"]] <= formation_time
    for row in final["provenance_refs"]:
        assert binding_times[row["admission_metadata"]["binding_id"]] <= final_time
    assert final["content"]["trigger_event"] == (
        "Tony earlier said he would no longer use L4 and later endorsed the "
        "clarified no-L4 consensus; the reviewed checkpoint freezes the "
        "relationship-instance commitment."
    )
    assert item["exact_binding_coverage"] == {
        "assertions": 4,
        "unique_binding_ids": 4,
        "status": "PASS",
    }


def test_only_three_reviewed_candidates_change_byte_semantically() -> None:
    old_payload = prior()
    new_payload = compiled()
    old_identity = candidate_map(old_payload, "identity_previews")
    new_identity = candidate_map(new_payload, "identity_previews")
    old_memory = candidate_map(old_payload, "memory_experience_previews")
    new_memory = candidate_map(new_payload, "memory_experience_previews")

    for candidate_id, old_item in old_identity.items():
        assert new_identity[candidate_id]["canonical_preview"] == old_item["canonical_preview"]
    for candidate_id in ("MIRA-MEM-CAND-003", "MIRA-MEM-CAND-004", "MIRA-MEM-CAND-005", "MIRA-MEM-CAND-007"):
        assert new_memory[candidate_id]["canonical_preview"] == old_memory[candidate_id]["canonical_preview"]
    for candidate_id in ("MIRA-MEM-CAND-001", "MIRA-MEM-CAND-002", "MIRA-MEM-CAND-006"):
        assert new_memory[candidate_id]["canonical_preview"] != old_memory[candidate_id]["canonical_preview"]

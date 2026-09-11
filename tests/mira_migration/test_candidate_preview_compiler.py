from __future__ import annotations

import builtins
import json
import subprocess
from pathlib import Path

import pytest

from tools.mira_migration import compiler


REPOSITORY = Path(__file__).resolve().parents[2]
PACKAGE = REPOSITORY / "artifacts/mira_migration_prep/MIRA_MIGRATION_PREP_PACKAGE_V1.json"
LEDGER = REPOSITORY / "artifacts/mira_migration_prep/MIRA_MIGRATION_EVIDENCE_LEDGER_V1.json"
DRY_RUN = REPOSITORY / "artifacts/mira_migration_prep/MIRA_MIGRATION_DRY_RUN_RESULT_V1.json"
SCHEMA_SHA = compiler.REVIEWED_SCHEMA_SHA


def compile_result() -> dict:
    return compiler.compile_preview(PACKAGE, LEDGER, DRY_RUN, schema_sha=SCHEMA_SHA)


def provenance_assertions(payload: dict) -> set[tuple[str, str]]:
    assertions: set[tuple[str, str]] = set()
    for item in payload["identity_previews"] + payload["memory_experience_previews"]:
        provenance = item["canonical_preview"]["payload"]["provenance_refs"]
        for row in provenance:
            assertions.add(
                (row["admission_metadata"]["binding_id"], row["admission_metadata"]["causal_role"])
            )
    return assertions


def test_compiles_exact_candidate_set_and_quarantine() -> None:
    preview = compile_result()

    assert preview["status"] == "PREVIEW_COMPLETE_NO_ADMISSION"
    assert preview["summary"] == {
        "identity_previews": 3,
        "memory_previews": 7,
        "mapped_memory_previews": 7,
        "waiting_on_schema": 0,
        "unbound_quarantine": 6,
        "raw_assertions_consumed": 42,
        "unique_binding_ids_consumed": 40,
        "repository_calls": 0,
        "admission_calls": 0,
        "runtime_calls": 0,
    }
    assert [item["candidate_id"] for item in preview["identity_previews"]] == [
        "MIRA-ID-CAND-001",
        "MIRA-ID-CAND-002",
        "MIRA-ID-CAND-003",
    ]
    assert [item["candidate_id"] for item in preview["memory_experience_previews"]] == [
        "MIRA-MEM-CAND-001",
        "MIRA-MEM-CAND-002",
        "MIRA-MEM-CAND-003",
        "MIRA-MEM-CAND-004",
        "MIRA-MEM-CAND-005",
        "MIRA-MEM-CAND-006",
        "MIRA-MEM-CAND-007",
    ]
    assert [item["record_id"] for item in preview["deferred_unbound_records"]] == [
        "GM-CMIR-003",
        "GM-CMIR-005",
        "GM-CMIR-007",
        "GM-CMIR-009",
        "GM-CMIR-010",
        "GM-CMIR-012",
    ]


def test_all_exact_assertions_and_unique_bindings_are_preserved() -> None:
    preview = compile_result()
    ledger_assertions = {
        (row["binding_id"], row["causal_role"]) for row in json.loads(LEDGER.read_text())["bindings"]
    }

    assertions = provenance_assertions(preview)
    assert len(assertions) == 42
    assert len({binding_id for binding_id, _ in assertions}) == 40
    assert assertions == ledger_assertions
    for item in preview["identity_previews"] + preview["memory_experience_previews"]:
        coverage = item["exact_binding_coverage"]
        assert coverage["status"] == "PASS"
        assert coverage["assertions"] >= coverage["unique_binding_ids"]


def test_identity_previews_are_distinct_mira_semantic_candidates() -> None:
    preview = compile_result()
    identity_payloads = [item["canonical_preview"]["payload"] for item in preview["identity_previews"]]
    lineages = [payload["lineage_id"] for payload in identity_payloads]

    assert len(set(lineages)) == 3
    assert {item["chain_id"] for item in preview["identity_previews"]} == {
        "GM-CMIR-001",
        "GM-CMIR-002",
        "GM-CMIR-008",
    }
    for payload in identity_payloads:
        identity = payload["identity"]
        assert "Tony" not in identity["identity_id"]
        assert payload["lineage_id"].startswith("mira-golden:")
    assert all(item["subject_boundary"] == "MIRA_SEMANTIC_SUBJECT" for item in preview["identity_previews"])


def test_memory_mapping_and_subject_and_authority_boundaries() -> None:
    preview = compile_result()
    by_candidate = {item["candidate_id"]: item for item in preview["memory_experience_previews"]}

    relationship_ids = {"MIRA-MEM-CAND-001", "MIRA-MEM-CAND-002", "MIRA-MEM-CAND-007"}
    narrative_ids = {"MIRA-MEM-CAND-003", "MIRA-MEM-CAND-004", "MIRA-MEM-CAND-005"}
    for candidate_id, item in by_candidate.items():
        expected = (
            "RELATIONSHIP_V2_LOSSLESS"
            if candidate_id in relationship_ids
            else "NARRATIVE_V1_FROZEN_NARROW"
            if candidate_id in narrative_ids
            else "PROJECT_COMMITMENT_V2_LOSSLESS"
        )
        assert item["semantic_mapping"] == expected
        assert item["compilation_state"] == "MAPPED_TYPED_PREVIEW_ONLY"
        assert item["authority"] == {
            "repository_calls": 0,
            "admission_calls": 0,
            "runtime_calls": 0,
            "standing_authorization": False,
            "current_consent": False,
            "runtime_authority": False,
        }

    for candidate_id in relationship_ids:
        payload = by_candidate[candidate_id]["canonical_preview"]["payload"]
        content = payload["content"]
        assert payload["schema"] == "julia_core.memory_experience.record.v2"
        assert content["policy_transfer"]["future_behavior_proof"] is False
        assert content["causal_status"] in {
            "DIRECT_RAW_SUPPORTED",
            "MIXED_DIRECT_AND_INFERRED",
        }
    tony_observation = by_candidate["MIRA-MEM-CAND-007"]["canonical_preview"]["payload"]["content"]
    assert tony_observation["subject_boundary"] == {
        "semantic_subject": "MIRA",
        "observed_subject": "TONY",
        "autobiographical_owner": "TONY",
    }

    commitment = by_candidate["MIRA-MEM-CAND-006"]["canonical_preview"]["payload"]["content"]
    assert commitment["commitment_stage"] == "FROZEN_FINAL"
    assert commitment["transfer_semantics"] == "EXPLICIT_REAUTHORIZATION_REQUIRED"
    assert commitment["applicability"] == {
        "scope": "relationship_instance",
        "inheritance": "EXPLICIT_REAUTHORIZATION_REQUIRED",
        "current_authorization": False,
        "standing_consent": False,
        "runtime_authority": False,
    }
    assert commitment["revision"]["rewrite_history"] is False


def test_compile_is_deterministic() -> None:
    first = compile_result()
    second = compile_result()

    assert first == second
    assert first["deterministic_digest"] == second["deterministic_digest"]
    first_bytes = (json.dumps(first, ensure_ascii=False, indent=2) + "\n").encode()
    second_bytes = (json.dumps(second, ensure_ascii=False, indent=2) + "\n").encode()
    assert first_bytes == second_bytes


@pytest.mark.parametrize(
    ("artifact", "key"),
    [(PACKAGE, "package"), (LEDGER, "ledger"), (DRY_RUN, "dry-run")],
)
def test_sha_bound_inputs_fail_closed_on_tamper(tmp_path: Path, artifact: Path, key: str) -> None:
    copied = tmp_path / f"{key}.json"
    value = json.loads(artifact.read_text())
    value["tamper_marker"] = "must change the SHA-256"
    copied.write_text(json.dumps(value), encoding="utf-8")
    paths = {"package": PACKAGE, "ledger": LEDGER, "dry-run": DRY_RUN} | {key: copied}

    with pytest.raises(compiler.MigrationCompilerError, match="hash mismatch"):
        compiler.compile_preview(paths["package"], paths["ledger"], paths["dry-run"], schema_sha=SCHEMA_SHA)


def test_wrong_reviewed_schema_sha_fails_closed() -> None:
    with pytest.raises(compiler.MigrationCompilerError, match="reviewed schema SHA"):
        compiler.compile_preview(PACKAGE, LEDGER, DRY_RUN, schema_sha="0" * 40)


def test_canonical_schema_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        if command[1] == "rev-parse":
            return subprocess.CompletedProcess(command, 0, stdout=SCHEMA_SHA, stderr="")
        if command[1] == "merge-base":
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if command[1] == "diff":
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="schema drift")
        raise AssertionError(f"unexpected git command: {command}")

    monkeypatch.setattr(compiler.subprocess, "run", fake_run)
    with pytest.raises(compiler.MigrationCompilerError, match="schema files were modified"):
        compiler.verify_repository_binding(REPOSITORY, SCHEMA_SHA)


def test_compile_has_no_file_writer_or_prompt_path(monkeypatch: pytest.MonkeyPatch) -> None:
    real_open = builtins.open

    def read_only_open(file: object, mode: str = "r", *args: object, **kwargs: object):
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError("compile_preview attempted a write")
        return real_open(file, mode, *args, **kwargs)

    def fail_write(_: Path, *__: object, **___: object) -> None:
        raise AssertionError("compile_preview attempted a write")

    monkeypatch.setattr(builtins, "open", read_only_open)
    monkeypatch.setattr(Path, "write_text", fail_write)
    preview = compile_result()
    source = (REPOSITORY / "tools/mira_migration/compiler.py").read_text()
    assert preview["status"] == "PREVIEW_COMPLETE_NO_ADMISSION"
    assert "Hi Mira" not in source
    assert "Hi Mira" not in json.dumps(preview, ensure_ascii=False)
    assert "from julia_core.identity.repository" not in source
    assert "from julia_core.memory_experience.repository" not in source
    assert "store_candidate(" not in source
    assert ".admit(" not in source

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from tests.evidence.recovery_rehearsal import (
    BASE_SHA,
    EVIDENCE_PATH,
    IDENTITY_PLAN,
    MEMORY_PLAN,
    QUARANTINED_CMIR_IDS,
    RecoveryRehearsalError,
    RecoveryActionPlan,
    _validate_plan,
    build_rehearsal,
)


def load_evidence() -> dict:
    return json.loads(Path(EVIDENCE_PATH).read_text(encoding="utf-8"))


def test_exact_p5_a1_inputs_and_artifact_are_bound() -> None:
    evidence = build_rehearsal()

    assert evidence["source"] == {
        "task_id": "P5-A1",
        "base_sha": BASE_SHA,
        "artifact_path": (
            "artifacts/continuity/"
            "P5_A1_OWNER_AUTHORIZED_GOLDEN_MIRA_CANONICAL_ADMISSION_V1.json"
        ),
        "artifact_sha256": (
            "f10a6d8daa6ed1604c2002254d26016efe31afca2e4dc18c4e1b094a48672110"
        ),
        "final_result": "P5_A1_RESULT=OWNER_AUTHORIZED_CANONICAL_ADMISSION_COMPLETE",
        "identity_refs_bound": 3,
        "memory_refs_bound": 8,
        "binding_mode": "EXACT_REF_AND_DIGEST",
    }
    assert evidence == load_evidence()


def test_identity_and_memory_rehearsals_append_without_rewrite() -> None:
    evidence = build_rehearsal()
    identity = evidence["identity_recovery_rehearsal"]
    memory = evidence["memory_recovery_rehearsal"]

    assert identity["validation"] == "PASS"
    assert identity["simulation"]["actual_repository_calls"] == 0
    assert identity["simulation"]["original_event_prefix_unchanged"] is True
    assert identity["simulation"]["record_rewrites"] == 0
    assert memory["validation"] == "PASS"
    assert memory["simulation"]["actual_repository_calls"] == 0
    assert memory["simulation"]["original_event_prefix_unchanged"] is True
    assert memory["simulation"]["record_rewrites"] == 0
    assert evidence["append_only_proof"]["result"] == "PASS"
    assert evidence["append_only_proof"]["history_rewrites"] == 0


def test_stale_ambiguous_quarantine_and_lineage_targets_fail_closed() -> None:
    evidence = build_rehearsal()
    failures = evidence["fail_closed_checks"]

    assert failures["stale_target"]["result"] == "REJECTED_BEFORE_MUTATION"
    assert failures["ambiguous_successor"]["result"] == "REJECTED_BEFORE_MUTATION"
    assert failures["quarantine_substitution"]["result"] == "REJECTED_BEFORE_MUTATION"
    assert (
        failures["commitment_stage_regression"]["result"] == "REJECTED_BEFORE_MUTATION"
    )
    assert failures["actual_attempted_writes"] == 0
    with pytest.raises(RecoveryRehearsalError, match="fresh target digest"):
        _validated(replace(IDENTITY_PLAN, target_digest="0" * 64))
    with pytest.raises(RecoveryRehearsalError, match="plan exact successor ref"):
        _validated(replace(IDENTITY_PLAN, successor_ref=""))


def _validated(plan: RecoveryActionPlan) -> None:
    from tests.evidence.recovery_rehearsal import _source_evidence

    _, identities, memories = _source_evidence(Path("."))
    _validate_plan(plan, identity_records=identities, memory_records=memories)


def test_project_commitment_and_quarantine_boundaries_are_preserved() -> None:
    evidence = build_rehearsal()
    commitment = evidence["project_commitment_lineage"]
    quarantine = evidence["quarantine_boundary"]

    assert commitment["order"] == ["FORMATION_DRAFT", "FROZEN_FINAL"]
    assert commitment["predecessor_version_id"] == "formation-draft-preview"
    assert commitment["collapse_or_reorder"] is False
    assert commitment["history_rewrite"] is False
    assert set(quarantine["quarantined_cmir_ids"]) == QUARANTINED_CMIR_IDS
    assert quarantine["present_in_admitted_refs"] == 0
    assert quarantine["accepted_as_recovery_substitutes"] == 0


def test_rehearsal_has_zero_authority_and_deterministic_rerun() -> None:
    first = build_rehearsal()
    second = build_rehearsal()

    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["authority"] == {
        "semantic_authority": 0,
        "canonical_writes": 0,
        "runtime_writes": 0,
        "provider_writes": 0,
        "production_response_selection_authority": 0,
        "actual_supersede_calls": 0,
        "actual_retire_calls": 0,
        "actual_admit_or_store_calls": 0,
    }
    assert first["execution"] == {
        "live_canary_or_model_call": 0,
        "production_response_selection": 0,
        "future_action_authorized": 0,
    }
    assert first["final_result"] == (
        "P5_E_RECOVERY_SUPERSESSION_NO_WRITE_REHEARSAL_PASS"
    )

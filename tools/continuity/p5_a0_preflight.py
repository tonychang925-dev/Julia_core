"""Fail-closed P5-A0 Golden Mira admission preflight."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from tools.mira_migration.admission_sim import (
    CANONICAL_BASE_SHA,
    PREVIEW_ARTIFACT_SHA256,
    PREVIEW_DIGEST,
    PREVIEW_HEAD_SHA,
    PREVIEW_PATH,
    simulate_admission,
)


P4_BASE_SHA = "2421a22695ca41d3b044879febf582dea8a036bc"
SIMULATION_HEAD_SHA = "14ad5a6f17e677069ee1cfc59357f9aa1c99cb33"
SIMULATION_RESULT_PATH = (
    "artifacts/mira_migration_prep/"
    "MIGRATION_ADMISSION_SIMULATION_V0_1_CANONICAL_ALIGNED_RESULT.json"
)
SIMULATION_RESULT_SHA256 = (
    "1860c65d7c2ddf1514cfd5c28709b238941c69da47bc689d6ab3ec762e44317d"
)
P4_RESULT_PATH = (
    "artifacts/continuity/" "P4_FINAL_R1_SHADOW_CANARY_PREPARATION_EXIT_REAUDIT_V1.json"
)
P4_RESULT_SHA256 = "9825b3df93a180c0e6591f9552b1bc05b00ad286e2d02a33ecbf06f55759c1a9"
QUARANTINED_CMIR_IDS = tuple(f"GM-CMIR-{item:03d}" for item in (3, 5, 7, 9, 10, 12))


class P5A0PreflightError(ValueError):
    pass


def _require(condition: bool, check: str) -> None:
    if condition is not True:
        raise P5A0PreflightError(f"FAIL_CLOSED: {check}")


def _git_bytes(repository: Path, commit: str, path: str) -> bytes:
    resolved = subprocess.run(
        ["git", "rev-parse", f"{commit}^{{commit}}"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _require(resolved == commit, f"exact commit resolution: {commit}")
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=repository,
        check=True,
        capture_output=True,
    ).stdout


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json(blob: bytes, label: str) -> dict[str, Any]:
    value = json.loads(blob.decode("utf-8"))
    _require(type(value) is dict, f"{label} is a JSON object")
    return value


def _is_ancestor(repository: Path, ancestor: str) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, "HEAD"],
        cwd=repository,
        capture_output=True,
    )
    _require(result.returncode == 0, f"HEAD descends from {ancestor}")


def _verify_immutable_anchors(repository: Path) -> dict[str, Any]:
    _is_ancestor(repository, P4_BASE_SHA)
    _is_ancestor(repository, SIMULATION_HEAD_SHA)
    preview_blob = _git_bytes(repository, PREVIEW_HEAD_SHA, PREVIEW_PATH)
    simulation_blob = _git_bytes(
        repository, SIMULATION_HEAD_SHA, SIMULATION_RESULT_PATH
    )
    p4_blob = _git_bytes(repository, P4_BASE_SHA, P4_RESULT_PATH)
    current_p4_blob = (repository / P4_RESULT_PATH).read_bytes()
    current_simulation_blob = (repository / SIMULATION_RESULT_PATH).read_bytes()

    _require(_sha256(preview_blob) == PREVIEW_ARTIFACT_SHA256, "preview artifact bytes")
    _require(
        _sha256(simulation_blob) == SIMULATION_RESULT_SHA256,
        "accepted simulation artifact bytes",
    )
    _require(_sha256(p4_blob) == P4_RESULT_SHA256, "P4 evidence artifact bytes")
    _require(current_p4_blob == p4_blob, "P4 evidence remains byte-identical")
    _require(
        current_simulation_blob == simulation_blob,
        "accepted simulation evidence remains byte-identical",
    )
    return {
        "preview": _json(preview_blob, "preview"),
        "simulation": _json(simulation_blob, "simulation"),
        "p4": _json(p4_blob, "P4 evidence"),
    }


def _verify_p4_authority(p4: dict[str, Any]) -> dict[str, Any]:
    _require(p4["final_result"] == "PASS_READY_FOR_P5_OWNER_GATE", "P4 pass result")
    _require(p4["gap_analysis"]["p4_blocking_gaps"] == [], "P4 blocking gaps")
    _require(p4["authority_analysis"]["canonical_writes"] == 0, "P4 canonical writes")
    _require(p4["production_code_changed"] == 0, "P4 production code changes")
    _require(p4["p5_work_performed"] == 0, "P4 P5 boundary")
    _require(p4["p6_work_performed"] == 0, "P4 P6 boundary")
    return {
        "p4_head": P4_BASE_SHA,
        "artifact_sha256": P4_RESULT_SHA256,
        "result": "PASS",
        "p4_evidence_mutated": False,
        "blocking_gaps": 0,
    }


def _verify_reconstruction(
    repository: Path, preview: dict[str, Any], accepted: dict[str, Any]
) -> dict[str, Any]:
    current = simulate_admission(repository)
    rerun = simulate_admission(repository)
    _require(current == accepted == rerun, "deterministic current reconstruction")
    _require(current["bindings"] == accepted["bindings"], "admission input bindings")
    _require(
        current["summary"]
        == {
            "candidate_count": 10,
            "identity_candidates": 3,
            "memory_candidates": 7,
            "memory_record_count": 8,
            "canonical_compatible": 10,
            "canonical_incompatible": 0,
            "identity_compatible": 3,
            "narrative_compatible": 3,
            "relationship_compatible": 3,
            "project_commitment_compatible": 1,
            "raw_assertions": 42,
            "unique_binding_ids": 40,
            "global_disposition": "PASS_CANONICAL_SIMULATION_NO_ADMISSION",
            "actual_admission": 0,
        },
        "exact candidate and provenance counts",
    )
    _require(
        all(item["disposition"].startswith("PASS_") for item in current["candidates"]),
        "all candidates reconstruct",
    )
    _require(
        all(
            item["preview_digest"] == item["constructed_digest"]
            for item in current["candidates"]
            if "preview_digest" in item
        ),
        "identity digest exactness",
    )
    _require(
        all(
            item["preview_digests"] == item["constructed_digests"]
            for item in current["candidates"]
            if "preview_digests" in item
        ),
        "memory digest exactness",
    )
    _require(
        all(
            item["actual_status"] == "NOT_STORED_NOT_ADMITTED"
            for item in current["candidates"]
        ),
        "preflight remains no-write",
    )
    _require(
        preview["summary"]["raw_assertions_consumed"] == 42
        and preview["summary"]["unique_binding_ids_consumed"] == 40,
        "RAW assertion and binding totals",
    )
    return {
        "canonical_base": CANONICAL_BASE_SHA,
        "simulation_head": SIMULATION_HEAD_SHA,
        "preview_head": PREVIEW_HEAD_SHA,
        "preview_digest": PREVIEW_DIGEST,
        "preview_artifact_sha256": PREVIEW_ARTIFACT_SHA256,
        "simulation_result_sha256": SIMULATION_RESULT_SHA256,
        "identity_candidates": 3,
        "memory_candidates": 7,
        "memory_records": 8,
        "raw_assertions": 42,
        "unique_bindings": 40,
        "deterministic_current_rerun": "BYTE_AND_SEMANTIC_IDENTICAL",
        "fallback_or_substitute_selection": 0,
    }


def _verify_semantic_boundaries(preview: dict[str, Any]) -> dict[str, Any]:
    quarantined = tuple(
        item["record_id"] for item in preview["deferred_unbound_records"]
    )
    _require(
        quarantined == QUARANTINED_CMIR_IDS,
        "six unbound CMIR controls remain quarantined",
    )
    _require(
        all(
            item["compilation_state"] == "DEFER_UNBOUND"
            and "QUARANTINED_FROM_ADMISSION_READY_SET" in item["blockers"]
            and item["repository_calls"] == 0
            and item["admission_calls"] == 0
            and item["runtime_calls"] == 0
            for item in preview["deferred_unbound_records"]
        ),
        "quarantined controls are non-admissible",
    )
    _require(
        preview["authority"]
        == {
            "canonical_admission": False,
            "standing_authorization": False,
            "current_consent": False,
            "runtime_authority": False,
            "merge_authority": "NONE",
        },
        "preview carries no admission authority",
    )

    relationship_semantics = []
    commitment_applicability = []
    for item in preview["memory_experience_previews"]:
        canonical_preview = item["canonical_preview"]
        if item["candidate_class"] == "RelationshipExperience":
            relationship_semantics.append(canonical_preview["payload"]["content"])
        if item["candidate_class"] == "ProjectCommitmentExperience":
            commitment_applicability.extend(
                (
                    canonical_preview["formation_record"]["canonical_preview"][
                        "payload"
                    ]["content"]["applicability"],
                    canonical_preview["frozen_final_record"]["canonical_preview"][
                        "payload"
                    ]["content"]["applicability"],
                )
            )

    _require(
        all(
            item["policy_transfer"]["future_behavior_proof"] is False
            for item in relationship_semantics
            if item["policy_transfer"]["coverage"] == "PRESENT"
        ),
        "historical intimacy is not future-behavior proof",
    )
    _require(
        all(
            applicability["current_authorization"] is False
            and applicability["standing_consent"] is False
            and applicability["runtime_authority"] is False
            for applicability in commitment_applicability
        ),
        "remembered commitment is not current authorization",
    )
    _require(
        any(
            item.get("subject_boundary", {}).get("observed_subject") == "TONY"
            and item["subject_boundary"]["autobiographical_owner"] == "TONY"
            for item in relationship_semantics
        ),
        "Tony autobiography remains subject-bounded",
    )
    _require(
        not any(
            item.get("subject_boundary", {}).get("observed_subject") == "TONY"
            and item["subject_boundary"]["autobiographical_owner"] == "MIRA"
            for item in relationship_semantics
        ),
        "Tony autobiography cannot become Mira identity",
    )
    return {
        "quarantined_cmir_ids": list(QUARANTINED_CMIR_IDS),
        "admissible_quarantined_controls": 0,
        "tony_autobiography_is_mira_identity": False,
        "historical_intimacy_is_standing_consent": False,
        "remembered_commitment_is_runtime_authorization": False,
    }


def run_preflight(repository: Path) -> dict[str, Any]:
    repository = repository.resolve()
    anchors = _verify_immutable_anchors(repository)
    p4 = _verify_p4_authority(anchors["p4"])
    reconstruction = _verify_reconstruction(
        repository, anchors["preview"], anchors["simulation"]
    )
    semantics = _verify_semantic_boundaries(anchors["preview"])
    result = {
        "schema": "julia_core.continuity.p5_a0.preflight.v1",
        "artifact_id": "P5_A0_GOLDEN_MIRA_ADMISSION_PREFLIGHT_V1",
        "task_id": "P5-A0",
        "issue": "Julia_core#74",
        "phase": "P5",
        "task_type": "OWNER_AUTHORIZED_ADMISSION_PREFLIGHT",
        "owner_authorization": "GRANTED_IN_CHAT_2026-09-13",
        "roadmap_authority": "Julia_Mira_Continuity_Parallel_Development_Plan_v0.2_2026-09-12",
        "base_sha": P4_BASE_SHA,
        "candidate_sha": SIMULATION_HEAD_SHA,
        "p4_authority": p4,
        "admission_input": reconstruction,
        "semantic_boundaries": semantics,
        "authority_drift": 0,
        "canonical_writes": 0,
        "actual_admission": 0,
        "next_task": {
            "task_id": "P5-A1",
            "boundary": "OWNER_AUTHORIZED_CANONICAL_ADMISSION_ONLY",
            "pinned_inputs": {
                "canonical_base_sha": CANONICAL_BASE_SHA,
                "simulation_head_sha": SIMULATION_HEAD_SHA,
                "preview_head_sha": PREVIEW_HEAD_SHA,
                "preview_digest": PREVIEW_DIGEST,
                "preview_artifact_sha256": PREVIEW_ARTIFACT_SHA256,
            },
            "allowed_paths": [
                "artifacts/mira_migration_prep/MIGRATION_TYPED_CANDIDATE_PREVIEW_V0_1_REWORK.json",
                "julia_core/identity/contracts.py",
                "julia_core/identity/repository.py",
                "julia_core/memory_experience/contracts.py",
                "julia_core/memory_experience/repository.py",
            ],
            "allowed_apis": [
                "IdentityRepository.store_candidate",
                "IdentityRepository.admit",
                "MemoryExperienceRepository.store_candidate",
                "MemoryExperienceRepository.admit",
            ],
            "write_set": {
                "identity_versions": 3,
                "memory_experience_records": 8,
                "candidate_governance_events": 11,
                "admission_governance_events": 11,
                "runtime_or_provider_writes": 0,
                "legacy_destructive_writes": 0,
            },
            "rollback_or_supersession": (
                "Fail before repository mutation if any pinned input or reconstruction check fails. "
                "After an append-only governance event, never rewrite history; corrective action is "
                "exact-ref supersede/retire with explicit actor, reason, occurred_at, and new immutable event."
            ),
            "post_write_verification": (
                "Resolve every exact ref; verify all 11 records remain digest-identical and ADMITTED, "
                "governance ledgers contain exactly candidate then admission events, quarantined CMIR IDs "
                "remain absent, runtime/provider authority remains 0, and deterministic evidence records the same."
            ),
            "forbidden": [
                "merge-to-main",
                "release",
                "deploy",
                "production response cutover",
                "destructive legacy removal",
                "P6 actions",
                "implicit latest/first/env/default candidate selection",
            ],
        },
    }
    result["final_result"] = (
        "P5_A0_RESULT=READY_FOR_OWNER_AUTHORIZED_CANONICAL_ADMISSION"
    )
    return result


__all__ = ["P5A0PreflightError", "run_preflight"]

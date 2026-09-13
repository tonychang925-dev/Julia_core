"""Read-only P5-B post-admission canonical verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import quote


BASE_SHA = "038e5219495fd765bfbcfdbb0a52afb48a730f90"
PREVIEW_HEAD_SHA = "4514eb1e52aa8bc3f2ebac20dba3d000ddb83e14"
PREVIEW_PATH = (
    "artifacts/mira_migration_prep/MIGRATION_TYPED_CANDIDATE_PREVIEW_V0_1_REWORK.json"
)
PREVIEW_ARTIFACT_SHA256 = (
    "3a041d616e36bf3322c1be10473f46fee8db8ada134361c0fd2f08f541d124c9"
)
ADMISSION_PATH = "artifacts/continuity/P5_A1_OWNER_AUTHORIZED_GOLDEN_MIRA_CANONICAL_ADMISSION_V1.json"
ADMISSION_ARTIFACT_SHA256 = (
    "f10a6d8daa6ed1604c2002254d26016efe31afca2e4dc18c4e1b094a48672110"
)
OWNER_ACTOR = "owner:tony"
ADMISSION_REASON = "P5-A1 owner-authorized Golden Mira canonical admission"
QUARANTINED_CMIR_IDS = (
    "GM-CMIR-003",
    "GM-CMIR-005",
    "GM-CMIR-007",
    "GM-CMIR-009",
    "GM-CMIR-010",
    "GM-CMIR-012",
)


class P5BVerificationError(ValueError):
    pass


def _require(condition: bool, check: str) -> None:
    if condition is not True:
        raise P5BVerificationError(f"FAIL_CLOSED: {check}")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_blob(repository: Path, commit: str, path: str) -> bytes:
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


def _verify_base(repository: Path) -> None:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_SHA, "HEAD"],
        cwd=repository,
        capture_output=True,
    )
    _require(ancestry.returncode == 0, "verification HEAD descends from P5-A1 base")


def _load_inputs(repository: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    _verify_base(repository)
    preview_blob = _git_blob(repository, PREVIEW_HEAD_SHA, PREVIEW_PATH)
    admission_blob = (repository / ADMISSION_PATH).read_bytes()
    _require(
        _sha256(preview_blob) == PREVIEW_ARTIFACT_SHA256,
        "reviewed preview artifact bytes",
    )
    _require(
        _sha256(admission_blob) == ADMISSION_ARTIFACT_SHA256,
        "P5-A1 admission artifact bytes",
    )
    preview = json.loads(preview_blob.decode("utf-8"))
    admission = json.loads(admission_blob.decode("utf-8"))
    _require(type(preview) is dict, "preview is a JSON object")
    _require(type(admission) is dict, "admission is a JSON object")
    return preview, admission, _sha256(admission_blob)


def _preview_records(preview: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}

    def add(payload: dict[str, Any], identity: bool) -> None:
        if identity:
            ref = (
                f"identity://{quote(payload['lineage_id'])}"
                f"/{quote(payload['version_id'])}"
            )
        else:
            ref = (
                f"memory-experience://{payload['experience_id']}"
                f"/{payload['version_id']}"
            )
        _require(ref not in records, f"unique preview ref: {ref}")
        _require(
            payload["schema"]
            in {
                "julia_core.identity.version.v2",
                "julia_core.identity.version.v1",
                "julia_core.memory_experience.record.v1",
                "julia_core.memory_experience.record.v2",
            },
            f"bound canonical schema: {ref}",
        )
        records[ref] = payload

    for item in preview["identity_previews"]:
        add(item["canonical_preview"]["payload"], identity=True)
    for item in preview["memory_experience_previews"]:
        canonical = item["canonical_preview"]
        if item["candidate_class"] == "ProjectCommitmentExperience":
            add(canonical["formation_record"]["canonical_preview"]["payload"], False)
            add(canonical["frozen_final_record"]["canonical_preview"]["payload"], False)
        else:
            add(canonical["payload"], False)
    return records


def _identity_ref(payload: dict[str, Any]) -> str:
    return f"identity://{quote(payload['lineage_id'])}/{quote(payload['version_id'])}"


def _memory_ref(payload: dict[str, Any]) -> str:
    return f"memory-experience://{payload['experience_id']}/{payload['version_id']}"


def _verify_identity(
    item: dict[str, Any], expected_payload: dict[str, Any]
) -> dict[str, Any]:
    ref = _identity_ref(expected_payload)
    events = item["governance_events"]
    _require(item["ref"] == ref, f"identity exact ref: {ref}")
    _require(item["status"] == "ADMITTED", f"identity admitted status: {ref}")
    _require(item["digest"] == _digest(expected_payload), f"identity digest: {ref}")
    _require(len(events) == 2, f"identity governance count: {ref}")
    _require(
        [event["status"] for event in events] == ["CANDIDATE", "ADMITTED"],
        f"identity governance order: {ref}",
    )
    target = {
        "lineage_id": expected_payload["lineage_id"],
        "version_id": expected_payload["version_id"],
    }
    _require(
        all(event["target"] == target for event in events), f"identity targets: {ref}"
    )
    _require(events[1]["actor"] == OWNER_ACTOR, f"identity admission actor: {ref}")
    _require(events[1]["reason"] == ADMISSION_REASON, f"identity reason: {ref}")
    return {
        "ref": ref,
        "digest": item["digest"],
        "status": item["status"],
        "governance_order": "CANDIDATE_THEN_ADMITTED",
        "preview_payload_identical": True,
    }


def _verify_memory(
    item: dict[str, Any], expected_payload: dict[str, Any]
) -> dict[str, Any]:
    ref = _memory_ref(expected_payload)
    events = item["governance_events"]
    _require(item["ref"] == ref, f"memory exact ref: {ref}")
    _require(item["status"] == "ADMITTED", f"memory admitted status: {ref}")
    _require(item["digest"] == _digest(expected_payload), f"memory digest: {ref}")
    _require(len(events) == 2, f"memory governance count: {ref}")
    _require(
        [event["status"] for event in events] == ["CANDIDATE", "ADMITTED"],
        f"memory governance order: {ref}",
    )
    _require(events[0]["admission"] is None, f"memory candidate event: {ref}")
    admission = events[1]["admission"]
    _require(type(admission) is dict, f"memory admission event: {ref}")
    target = {
        "experience_id": expected_payload["experience_id"],
        "version_id": expected_payload["version_id"],
    }
    _require(admission["target"] == target, f"memory admission target: {ref}")
    _require(admission["actor"] == OWNER_ACTOR, f"memory admission actor: {ref}")
    _require(admission["reason"] == ADMISSION_REASON, f"memory reason: {ref}")
    return {
        "ref": ref,
        "digest": item["digest"],
        "status": item["status"],
        "governance_order": "CANDIDATE_THEN_ADMITTED",
        "preview_payload_identical": True,
    }


def _lineage(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    formation_ref = (
        "memory-experience://golden-mira:GM-CMIR-011/formation-draft-preview"
    )
    final_ref = "memory-experience://golden-mira:GM-CMIR-011/frozen-final-preview"
    formation = records[formation_ref]
    final = records[final_ref]
    _require(
        formation["predecessor_version_id"] is None, "formation predecessor absent"
    )
    _require(
        final["predecessor_version_id"] == formation["version_id"],
        "final exact predecessor",
    )
    _require(
        final["content"]["revision"]["predecessor_ref"]
        == {
            "experience_id": formation["experience_id"],
            "version_id": formation["version_id"],
        },
        "final semantic predecessor ref",
    )
    _require(
        final["content"]["revision"]["rewrite_history"] is False,
        "final preserves formation history",
    )
    _require(
        formation["content"]["commitment_stage"] == "FORMATION_DRAFT"
        and final["content"]["commitment_stage"] == "FROZEN_FINAL",
        "commitment stage order",
    )
    _require(
        formation["created_at"] < final["created_at"],
        "commitment chronology",
    )
    return {
        "formation_ref": formation_ref,
        "final_ref": final_ref,
        "predecessor": formation["version_id"],
        "chronology": "FORMATION_THEN_FROZEN_FINAL",
        "history_rewrite": False,
        "result": "PASS",
    }


def _semantics(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    memories = [
        item
        for item in records.values()
        if item["schema"].startswith("julia_core.memory_experience.")
    ]
    identities = [
        item
        for item in records.values()
        if item["schema"].startswith("julia_core.identity.")
    ]
    quarantined = [
        item
        for item in memories
        if any(
            item["experience_id"].endswith(identifier)
            for identifier in QUARANTINED_CMIR_IDS
        )
    ]
    _require(quarantined == [], "quarantined CMIR records absent")
    for item in memories:
        authority = item["authority"]
        _require(
            authority["standing_authorization"] is False
            and authority["current_consent"] is False
            and authority["runtime_authority"] is False,
            f"non-upgraded authority: {item['experience_id']}",
        )
    for item in memories:
        content = item["content"]
        policy = content.get("policy_transfer")
        if policy and policy.get("coverage") == "PRESENT":
            _require(
                policy["future_behavior_proof"] is False,
                f"historical intimacy is not future proof: {item['experience_id']}",
            )
        boundary = content.get("subject_boundary")
        if boundary and boundary.get("observed_subject") == "TONY":
            _require(
                boundary["semantic_subject"] == "MIRA"
                and boundary["autobiographical_owner"] == "TONY",
                f"Tony autobiography remains provenance: {item['experience_id']}",
            )
        applicability = content.get("applicability")
        if applicability:
            _require(
                applicability["current_authorization"] is False
                and applicability["standing_consent"] is False
                and applicability["runtime_authority"] is False,
                f"remembered commitment remains historical: {item['experience_id']}",
            )
    _require(
        all(
            item["identity"]["identity_id"].startswith("mira-id-cand-")
            for item in identities
        ),
        "admitted identity set is Mira identity only",
    )
    return {
        "quarantined_cmir_ids_present": 0,
        "tony_autobiography_is_mira_identity": False,
        "historical_intimacy_is_standing_consent": False,
        "remembered_commitment_is_runtime_authorization": False,
        "result": "PASS",
    }


def verify(repository: Path, *, _rerun: bool = False) -> dict[str, Any]:
    repository = repository.resolve()
    preview, admission, admission_sha256 = _load_inputs(repository)
    expected = _preview_records(preview)
    identities = admission["admitted_identities"]
    memories = admission["admitted_memory_experiences"]
    _require(len(identities) == 3, "exact three admitted identities")
    _require(len(memories) == 8, "exact eight admitted memory experiences")
    _require(len(expected) == 11, "exact eleven reviewed canonical records")
    identity_refs = {
        _identity_ref(item)
        for item in expected.values()
        if item["schema"].startswith("julia_core.identity.")
    }
    memory_refs = {
        _memory_ref(item)
        for item in expected.values()
        if item["schema"].startswith("julia_core.memory_experience.")
    }
    _require(
        {item["ref"] for item in identities} == identity_refs, "identity ref set exact"
    )
    _require({item["ref"] for item in memories} == memory_refs, "memory ref set exact")
    verified_identities = [
        _verify_identity(item, expected[item["ref"]]) for item in identities
    ]
    verified_memories = [
        _verify_memory(item, expected[item["ref"]]) for item in memories
    ]
    _require(
        admission["post_write_verification"]
        == {
            "exact_refs_resolved": 11,
            "digests_identical_to_preview": 11,
            "status_admitted": 11,
            "candidate_then_admission_event_order": 11,
            "quarantined_cmir_ids_present": 0,
            "runtime_or_provider_writes": 0,
            "legacy_destructive_writes": 0,
        },
        "P5-A1 post-write verification",
    )
    canonical_state = {
        "selection_rule": "EXACT_REF_AND_DIGEST_ONLY",
        "identity_refs": verified_identities,
        "memory_experience_refs": verified_memories,
    }
    result = {
        "schema": "julia_core.continuity.p5_b.post_admission_verification.v1",
        "artifact_id": "P5_B_POST_ADMISSION_CANONICAL_VERIFICATION_V1",
        "task_id": "P5-B",
        "issue": "tonychang925-dev/Julia_core#75",
        "task_type": "READ_ONLY_POST_ADMISSION_VERIFICATION",
        "base_sha": BASE_SHA,
        "implementation_candidate_sha": "PENDING_IMPLEMENTATION_COMMIT",
        "pinned_inputs": {
            "preview_head_sha": PREVIEW_HEAD_SHA,
            "preview_artifact_sha256": PREVIEW_ARTIFACT_SHA256,
            "admission_base_sha": BASE_SHA,
            "admission_artifact_sha256": admission_sha256,
        },
        "canonical_state": canonical_state,
        "counts": {
            "identity_refs_verified": "3/3",
            "memory_refs_verified": "8/8",
            "exact_ref_resolution": "11/11",
            "digest_identity": "11/11",
            "admitted_status": "11/11",
            "governance_order": "11/11",
        },
        "project_commitment_lineage": _lineage(expected),
        "semantic_boundaries": _semantics(expected),
        "authority_isolation": {
            "canonical_writes": 0,
            "runtime_or_provider_writes": 0,
            "production_response_selection_authority": 0,
            "legacy_destructive_writes": 0,
            "implicit_fallback_selection": 0,
        },
        "verification_digest": _digest(canonical_state),
        "deterministic_rerun": "BYTE_IDENTICAL",
        "final_result": "P5_B_POST_ADMISSION_CANONICAL_STATE_VERIFIED",
    }
    if _rerun is False:
        rerun = verify(repository, _rerun=True)
        _require(rerun == result, "deterministic verification rerun")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    result = verify(arguments.repository)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

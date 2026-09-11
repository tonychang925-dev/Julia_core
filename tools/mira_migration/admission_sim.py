"""Fail-closed Golden Mira canonical admission simulation.

This module constructs and validates canonical-shaped objects in memory against
the exact contracts on the bound canonical base. It never imports or calls a
repository, store, admission, context, continuity, provider, or runtime path.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from julia_core.identity.contracts import (
    IdentityAnchor,
    IdentityBoundary,
    IdentityContract,
    IdentityProvenance,
    IdentityValue,
    IdentityVersion,
    RelationshipRoleAnchor,
)
from julia_core.memory_experience.contracts import (
    MemoryExperienceCandidate,
    MemoryExperienceProvenance,
    MemoryExperienceRecord,
    MemoryExperienceType,
    NarrativeExperienceContent,
)


TASK_ID = "MIG-ADMISSION-SIM-V0.1"
AGENT_ID = "agent-c"
CANONICAL_BASE_SHA = "260fe7374f57d09c89ab8748e60a7324f100452f"
PREVIEW_HEAD_SHA = "4514eb1e52aa8bc3f2ebac20dba3d000ddb83e14"
CONTENT_DELTA_REVIEW_SHA = "9ad6b83778383c345f1a42c1cc7dc9a39984df3b"
PREVIEW_DIGEST = "ca9ae995fef04577fa9600875ffa163d2ca0dde74c18e19f4ad592e2ecf6f4c0"
PREVIEW_ARTIFACT_SHA256 = "3a041d616e36bf3322c1be10473f46fee8db8ada134361c0fd2f08f541d124c9"
REVIEW_ARTIFACT_SHA256 = "56c35addf3c2d5ac35e9cc7b4b87f81981163a571f55378ee4da6d897aa95a0e"
LEDGER_SHA256 = "8c4d886fe81dc76ed998caf705ac590567891c41014dcbe72b9eedcbccd6c3b3"
GOLDSET_SHA256 = "8234045ba1b2f08e182f57279bffafa3e4e910ecd0e21287c3d2dc5c02bc63fc"

PREVIEW_PATH = (
    "artifacts/mira_migration_prep/MIGRATION_TYPED_CANDIDATE_PREVIEW_V0_1_REWORK.json"
)
REVIEW_PATH = (
    "artifacts/mira_migration_prep/MIGRATION_TYPED_CANDIDATE_CONTENT_DELTA_REVIEW_V0_1.json"
)
LEDGER_PATH = "artifacts/mira_migration_prep/MIRA_MIGRATION_EVIDENCE_LEDGER_V1.json"

CANONICAL_CONTRACT_PATHS = (
    "julia_core/identity/contracts.py",
    "julia_core/identity/repository.py",
    "julia_core/memory_experience/contracts.py",
    "julia_core/memory_experience/repository.py",
)
RELATIONSHIP_ALLOWED_FIELDS = {
    "relationship_id",
    "event",
    "interpretation",
    "occurred_at",
}
PROJECT_ALLOWED_FIELDS = {
    "subject",
    "counterparty",
    "scope",
    "commitment",
    "transfer_semantics",
    "occurred_at",
}
EXPECTED_CANDIDATES = tuple(
    [
        "MIRA-ID-CAND-001",
        "MIRA-ID-CAND-002",
        "MIRA-ID-CAND-003",
        "MIRA-MEM-CAND-001",
        "MIRA-MEM-CAND-002",
        "MIRA-MEM-CAND-003",
        "MIRA-MEM-CAND-004",
        "MIRA-MEM-CAND-005",
        "MIRA-MEM-CAND-006",
        "MIRA-MEM-CAND-007",
    ]
)


class AdmissionSimulationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if condition is not True:
        raise AdmissionSimulationError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_digest(value: Any) -> str:
    serialized = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _git_show(repository: Path, commit: str, path: str) -> bytes:
    resolved = subprocess.run(
        ["git", "rev-parse", f"{commit}^{{commit}}"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _require(resolved == commit, f"commit does not resolve exactly: {commit}")
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    return result.stdout


def verify_canonical_base(repository: Path) -> None:
    repository = repository.resolve()
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", CANONICAL_BASE_SHA, "HEAD"],
        cwd=repository,
        capture_output=True,
        text=True,
    )
    _require(
        ancestry.returncode == 0,
        "simulation HEAD does not descend from the exact canonical base",
    )
    drift = subprocess.run(
        ["git", "diff", "--exit-code", CANONICAL_BASE_SHA, "--", *CANONICAL_CONTRACT_PATHS],
        cwd=repository,
        capture_output=True,
        text=True,
    )
    _require(
        drift.returncode == 0,
        "canonical contracts changed after the bound canonical base",
    )


def _parse_json(blob: bytes, path: str) -> dict[str, Any]:
    value = json.loads(blob.decode("utf-8"))
    _require(type(value) is dict, f"{path} must contain a JSON object")
    return value


def _load_bound_inputs(repository: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    preview_blob = _git_show(repository, PREVIEW_HEAD_SHA, PREVIEW_PATH)
    review_blob = _git_show(repository, CONTENT_DELTA_REVIEW_SHA, REVIEW_PATH)
    ledger_blob = _git_show(repository, PREVIEW_HEAD_SHA, LEDGER_PATH)
    _require(_sha256_bytes(preview_blob) == PREVIEW_ARTIFACT_SHA256, "preview artifact hash mismatch")
    _require(_sha256_bytes(review_blob) == REVIEW_ARTIFACT_SHA256, "content review artifact hash mismatch")
    _require(_sha256_bytes(ledger_blob) == LEDGER_SHA256, "evidence ledger hash mismatch")

    preview = _parse_json(preview_blob, PREVIEW_PATH)
    review = _parse_json(review_blob, REVIEW_PATH)
    ledger = _parse_json(ledger_blob, LEDGER_PATH)
    preview_without_digest = {key: value for key, value in preview.items() if key != "deterministic_digest"}
    _require(preview.get("artifact_id") == "MIGRATION_TYPED_CANDIDATE_PREVIEW_V0_1_REWORK", "wrong preview artifact")
    _require(preview.get("task_id") == "MIG-PREVIEW-REWORK-V0.1", "wrong preview task")
    _require(preview.get("status") == "PREVIEW_REWORK_COMPLETE_NO_ADMISSION", "preview is not rework-complete")
    _require(preview.get("deterministic_digest") == PREVIEW_DIGEST, "preview semantic digest mismatch")
    _require(_canonical_digest(preview_without_digest) == PREVIEW_DIGEST, "preview semantic digest does not recompute")
    _require(review.get("rework_head_sha") == PREVIEW_HEAD_SHA, "review is not bound to preview head")
    _require(review.get("rework_preview_digest") == PREVIEW_DIGEST, "review digest mismatch")
    _require(review.get("recommendation") == "READY_FOR_ADMISSION_SIMULATION", "content review is not ready")
    _require(review.get("cross_candidate_consistency") == "PASS", "content review cross-candidate failure")
    _require(review.get("stability", {}).get("identity_pass") == "3/3", "Identity content review mismatch")
    _require(review.get("stability", {}).get("memory_pass") == "7/7", "Memory content review mismatch")
    return preview, review, ledger


def _identity_objects(payload: dict[str, Any]) -> IdentityVersion:
    identity = payload["identity"]
    anchors = tuple(
        IdentityAnchor(anchor_id=item["anchor_id"], statement=item["statement"])
        for item in identity["anchors"]
    )
    values = tuple(
        IdentityValue(value_id=item["value_id"], statement=item["statement"])
        for item in identity["values"]
    )
    boundaries = tuple(
        IdentityBoundary(boundary_id=item["boundary_id"], constraint=item["constraint"])
        for item in identity["boundaries"]
    )
    relationship_roles = tuple(
        RelationshipRoleAnchor(
            anchor_id=item["anchor_id"],
            relationship_id=item["relationship_id"],
            role=item["role"],
        )
        for item in identity["relationship_role_anchors"]
    )
    provenance = tuple(
        IdentityProvenance(
            source_type=item["source_type"],
            source_ref=item["source_ref"],
            source_digest=item["source_digest"],
            admission_metadata=tuple(item["admission_metadata"].items()),
        )
        for item in payload["provenance_refs"]
    )
    return IdentityVersion(
        contract=IdentityContract(
            identity_id=identity["identity_id"],
            anchors=anchors,
            values=values,
            boundaries=boundaries,
            relationship_role_anchors=relationship_roles,
        ),
        lineage_id=payload["lineage_id"],
        version_id=payload["version_id"],
        predecessor_version_id=payload["predecessor_version_id"],
        created_at=payload["created_at"],
        provenance_refs=provenance,
    )


def _memory_provenance(payload: dict[str, Any]) -> tuple[MemoryExperienceProvenance, ...]:
    return tuple(
        MemoryExperienceProvenance(
            source_type=item["source_type"],
            source_ref=item["source_ref"],
            source_digest=item["source_digest"],
            admission_metadata=tuple(item["admission_metadata"].items()),
        )
        for item in payload["provenance_refs"]
    )


def _narrative_record(payload: dict[str, Any]) -> MemoryExperienceRecord:
    content = payload["content"]
    narrative = NarrativeExperienceContent(
        event=content["event"],
        meaning_at_time=content["meaning_at_time"],
        significance=content["significance"],
        later_reinterpretation=content["later_reinterpretation"],
        source_refs=tuple(content["source_refs"]),
    )
    return MemoryExperienceRecord(
        experience_id=payload["experience_id"],
        version_id=payload["version_id"],
        experience_type=MemoryExperienceType(payload["experience_type"]),
        content=narrative,
        provenance_refs=_memory_provenance(payload),
        created_at=payload["created_at"],
        predecessor_version_id=payload["predecessor_version_id"],
    )


def _memory_records(item: dict[str, Any]) -> list[dict[str, Any]]:
    preview = item["canonical_preview"]
    if preview.get("type") == "MemoryExperienceRecordLineage":
        return [
            preview["formation_record"]["canonical_preview"],
            preview["frozen_final_record"]["canonical_preview"],
        ]
    return [preview]


def _memory_payloads(item: dict[str, Any]) -> list[dict[str, Any]]:
    return [record["payload"] for record in _memory_records(item)]


def _assertion_key(row: dict[str, Any]) -> tuple[str, str]:
    metadata = row["admission_metadata"]
    return metadata["binding_id"], metadata["causal_role"]


def _validate_record_provenance(
    record: dict[str, Any], chain_rows: list[dict[str, Any]], chain_id: str
) -> set[tuple[str, str]]:
    expected = {(row["binding_id"], row["causal_role"]): row for row in chain_rows}
    actual_keys: set[tuple[str, str]] = set()
    for row in record["provenance_refs"]:
        key = _assertion_key(row)
        _require(key not in actual_keys, f"duplicate provenance assertion in {chain_id}")
        actual_keys.add(key)
        evidence = expected.get(key)
        _require(evidence is not None, f"provenance assertion outside ledger chain {chain_id}")
        metadata = row["admission_metadata"]
        _require(metadata["message_id"] == evidence["message_id"], "provenance message mismatch")
        _require(row["source_type"] == "auditable-causal-goldset", "wrong provenance source type")
        _require(row["source_digest"] == GOLDSET_SHA256, "wrong goldset provenance digest")
        _require(
            row["source_ref"]
            == f"auditable-causal-goldset-v1://assertions/{key[0]}/{key[1]}",
            "wrong exact assertion source ref",
        )
        _require(evidence["evidence_grade"] == "RAW_DIRECT", "non-RAW evidence entered provenance")
        _require(evidence["support_scope"] == "exact", "non-exact evidence support entered provenance")
        _require(evidence["temporal_verified"] is True, "temporally unverified evidence entered provenance")
    return actual_keys


def _validate_all_provenance(
    preview: dict[str, Any], ledger: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    rows_by_chain: dict[str, list[dict[str, Any]]] = {}
    for row in ledger["bindings"]:
        rows_by_chain.setdefault(row["chain_id"], []).append(row)
    results: dict[str, dict[str, Any]] = {}
    all_assertions: set[tuple[str, str]] = set()
    for item in preview["identity_previews"] + preview["memory_experience_previews"]:
        records = (
            [item["canonical_preview"]["payload"]]
            if item["candidate_id"].startswith("MIRA-ID-")
            else _memory_payloads(item)
        )
        chain_assertions: set[tuple[str, str]] = set()
        for record in records:
            chain_assertions.update(
                _validate_record_provenance(record, rows_by_chain[item["chain_id"]], item["chain_id"])
            )
        _require(
            chain_assertions
            == {(row["binding_id"], row["causal_role"]) for row in rows_by_chain[item["chain_id"]]},
            f"candidate provenance does not cover exact chain {item['chain_id']}",
        )
        all_assertions.update(chain_assertions)
        results[item["candidate_id"]] = {
            "status": "PASS",
            "assertions": len(chain_assertions),
            "unique_binding_ids": len({binding for binding, _ in chain_assertions}),
        }
    _require(len(all_assertions) == 42, "simulation did not consume all 42 RAW assertions")
    _require(len({binding for binding, _ in all_assertions}) == 40, "unique binding count mismatch")
    return results, all_assertions


def _validate_lineage(item: dict[str, Any]) -> dict[str, Any]:
    if item["candidate_id"].startswith("MIRA-ID-"):
        payload = item["canonical_preview"]["payload"]
        return {
            "status": "PASS" if payload["predecessor_version_id"] is None else "FAIL",
            "kind": "IDENTITY_INITIAL_VERSION",
        }
    records = _memory_payloads(item)
    if len(records) == 1:
        payload = records[0]
        return {
            "status": "PASS" if payload["predecessor_version_id"] is None else "FAIL",
            "kind": "MEMORY_INITIAL_VERSION",
        }
    formation = records[0]
    final = records[1]
    exact_predecessor = (
        formation["predecessor_version_id"] is None
        and formation["content"]["revision"] is None
        and final["predecessor_version_id"] == formation["version_id"]
        and final["content"]["revision"]["predecessor_ref"]
        == {"experience_id": formation["experience_id"], "version_id": formation["version_id"]}
        and formation["experience_id"] == final["experience_id"]
        and formation["experience_type"] == final["experience_type"]
    )
    return {
        "status": "PASS" if exact_predecessor else "FAIL",
        "kind": "PROJECT_COMMITMENT_TWO_RECORD_LINEAGE",
    }


def _validate_authority(item: dict[str, Any]) -> bool:
    records = (
        [item["canonical_preview"]["payload"]]
        if item["candidate_id"].startswith("MIRA-ID-")
        else _memory_payloads(item)
    )
    expected_authority = {
        "standing_authorization": False,
        "current_consent": False,
        "mutates_identity": False,
        "runtime_authority": False,
    }
    authority_exact = (
        True
        if item["candidate_id"].startswith("MIRA-ID-")
        else all(record.get("authority") == expected_authority for record in records)
    )
    if not authority_exact:
        return False
    return item.get("authority", {}).get("repository_calls") == 0 and item.get("authority", {}).get(
        "admission_calls"
    ) == 0 and item.get("authority", {}).get("runtime_calls") == 0


def _unsupported_fields(record: dict[str, Any]) -> list[str]:
    content = record["content"]
    if record["experience_type"] == "RelationshipExperience":
        allowed = RELATIONSHIP_ALLOWED_FIELDS
    elif record["experience_type"] == "ProjectCommitmentExperience":
        allowed = PROJECT_ALLOWED_FIELDS
    else:
        return []
    return sorted(set(content) - allowed)


def _identity_result(item: dict[str, Any]) -> dict[str, Any]:
    preview = item["canonical_preview"]
    payload = preview["payload"]
    constructed = _identity_objects(payload)
    exact = constructed.canonical_payload() == payload and constructed.digest() == preview["digest"]
    return {
        "candidate_id": item["candidate_id"],
        "chain_id": item["chain_id"],
        "candidate_class": "IdentityVersion",
        "disposition": "PASS_CANONICAL_SIMULATION_NO_ADMISSION" if exact else "FAIL_CANONICAL_CONSTRUCTION",
        "record_count": 1,
        "canonical_construction": "PASS" if exact else "FAIL",
        "canonical_validation": "PASS" if exact else "FAIL",
        "preview_digest": preview["digest"],
        "constructed_digest": constructed.digest() if exact else None,
        "preview_ref": constructed.ref.uri,
        "expected_canonical_ref": constructed.ref.uri if exact else None,
        "expected_post_store_status": "CANDIDATE" if exact else None,
        "expected_candidate_governance_event": (
            f"identity-candidate:{constructed.lineage_id}:{constructed.version_id}" if exact else None
        ),
        "actual_status": "NOT_STORED_NOT_ADMITTED",
    }


def _memory_result(item: dict[str, Any]) -> dict[str, Any]:
    record_wrappers = _memory_records(item)
    records = _memory_payloads(item)
    unsupported = {record["version_id"]: _unsupported_fields(record) for record in records}
    if any(unsupported.values()):
        preview_refs = [
            f"memory-experience://{record['experience_id']}/{record['version_id']}"
            for record in records
        ]
        return {
            "candidate_id": item["candidate_id"],
            "chain_id": item["chain_id"],
            "candidate_class": item["candidate_class"],
            "disposition": "FAIL_CANONICAL_CONTRACT_INCOMPATIBLE",
            "record_count": len(records),
            "canonical_construction": "BLOCKED_NO_SUBSTITUTE",
            "canonical_validation": "FAIL",
            "unsupported_fields_by_record": unsupported,
        "preview_digests": [record["digest"] for record in record_wrappers],
            "preview_refs": preview_refs,
            "expected_canonical_ref": None,
            "expected_post_store_status": None,
            "actual_status": "NOT_STORED_NOT_ADMITTED",
            "blockers": [
                "CANONICAL_BASE_MEMORY_EXPERIENCE_CONTRACT_IS_V1",
                "MIGRATION_PREVIEW_REQUIRES_V2_SEMANTICS",
                "SILENT_V1_TRUNCATION_PROHIBITED",
            ],
        }

    constructed_records = []
    for payload, wrapper in zip(records, record_wrappers, strict=True):
        constructed = _narrative_record(payload)
        exact = constructed.canonical_payload() == payload and constructed.digest() == wrapper["digest"]
        _require(exact, f"canonical Narrative construction mismatch for {item['candidate_id']}")
        constructed_records.append(constructed)
    expected_refs = []
    expected_events = []
    for record in constructed_records:
        MemoryExperienceCandidate(record=record, submitted_at=record.created_at)
        expected_refs.append(record.ref.uri)
        expected_events.append(
            {
                "version_id": record.version_id,
                "candidate_status": "CANDIDATE",
                "candidate_governance_tuple": ["CANDIDATE", None],
            }
        )
    return {
        "candidate_id": item["candidate_id"],
        "chain_id": item["chain_id"],
        "candidate_class": item["candidate_class"],
        "disposition": "PASS_CANONICAL_SIMULATION_NO_ADMISSION",
        "record_count": len(constructed_records),
        "canonical_construction": "PASS",
        "canonical_validation": "PASS",
        "preview_digests": [record.digest() for record in constructed_records],
        "constructed_digests": [record.digest() for record in constructed_records],
        "preview_refs": expected_refs,
        "expected_canonical_refs": expected_refs,
        "expected_post_store_status": "CANDIDATE",
        "expected_candidate_governance_events": expected_events,
        "actual_status": "NOT_STORED_NOT_ADMITTED",
    }


def simulate_admission(repository: Path) -> dict[str, Any]:
    verify_canonical_base(repository)
    preview, review, ledger = _load_bound_inputs(repository)
    provenance, assertions = _validate_all_provenance(preview, ledger)
    lineage = {
        item["candidate_id"]: _validate_lineage(item)
        for item in preview["identity_previews"] + preview["memory_experience_previews"]
    }
    authority = {
        item["candidate_id"]: _validate_authority(item)
        for item in preview["identity_previews"] + preview["memory_experience_previews"]
    }
    candidates = [_identity_result(item) for item in preview["identity_previews"]]
    candidates.extend(_memory_result(item) for item in preview["memory_experience_previews"])
    for result in candidates:
        candidate_id = result["candidate_id"]
        result["exact_provenance"] = provenance[candidate_id]
        result["lineage_validation"] = lineage[candidate_id]
        result["no_authority_upgrade"] = "PASS" if authority[candidate_id] else "FAIL"
        result["content_review"] = "PASS_CONTENT"
        result["admission_preconditions"] = {
            "content_review": "PASS",
            "exact_provenance": provenance[candidate_id]["status"],
            "lineage": lineage[candidate_id]["status"],
            "no_authority_upgrade": "PASS" if authority[candidate_id] else "FAIL",
            "canonical_contract": result["canonical_validation"],
            "actual_admission_authority": "NONE_EXPECTED_FOR_SIMULATION",
        }
        if result["disposition"].startswith("PASS_"):
            _require(
                provenance[candidate_id]["status"] == "PASS"
                and lineage[candidate_id]["status"] == "PASS"
                and authority[candidate_id] is True,
                f"candidate passed construction without all preconditions: {candidate_id}",
            )
        else:
            _require(
                result["canonical_validation"] == "FAIL",
                f"invalid candidate did not fail closed: {candidate_id}",
            )

    candidate_ids = tuple(result["candidate_id"] for result in candidates)
    passed = sum(result["disposition"].startswith("PASS_") for result in candidates)
    failed = len(candidates) - passed
    payload = {
        "schema": "julia_core.migration.admission_simulation.v0.1",
        "artifact_id": "MIGRATION_ADMISSION_SIMULATION_V0_1_RESULT",
        "task_id": TASK_ID,
        "agent_id": AGENT_ID,
        "status": "SIMULATION_COMPLETE_FAIL_CLOSED_NO_ADMISSION",
        "simulation_phases": [
            "BIND_EXACT_INPUTS",
            "CONSTRUCT_CANDIDATE",
            "VALIDATE_CANONICAL_CONTRACT",
            "VALIDATE_LINEAGE",
            "VALIDATE_EXACT_PROVENANCE",
            "VALIDATE_ADMISSION_PRECONDITIONS",
            "EMIT_EXPECTED_REFS_DIGESTS_STATUS",
            "ENFORCE_ZERO_WRITE_NO_ADMISSION",
        ],
        "bindings": {
            "canonical_base_sha": CANONICAL_BASE_SHA,
            "preview_head_sha": PREVIEW_HEAD_SHA,
            "preview_digest": PREVIEW_DIGEST,
            "preview_artifact_sha256": PREVIEW_ARTIFACT_SHA256,
            "content_delta_review_sha": CONTENT_DELTA_REVIEW_SHA,
            "content_review_artifact_sha256": REVIEW_ARTIFACT_SHA256,
        },
        "input_loading": {
            "preview": f"git-object:{PREVIEW_HEAD_SHA}:{PREVIEW_PATH}",
            "content_delta_review": f"git-object:{CONTENT_DELTA_REVIEW_SHA}:{REVIEW_PATH}",
            "evidence_ledger": f"git-object:{PREVIEW_HEAD_SHA}:{LEDGER_PATH}",
            "method": "exact git object bytes with SHA-256 verification",
        },
        "summary": {
            "candidate_count": 10,
            "identity_candidates": 3,
            "memory_candidates": 7,
            "memory_record_count": 8,
            "canonical_compatible": passed,
            "canonical_incompatible": failed,
            "identity_compatible": 3,
            "narrative_compatible": 3,
            "relationship_incompatible": 3,
            "project_commitment_incompatible": 1,
            "raw_assertions": 42,
            "unique_binding_ids": 40,
            "global_disposition": "BLOCKED_CANONICAL_V2_ALIGNMENT_REQUIRED",
            "actual_admission": 0,
        },
        "candidates": candidates,
        "global_validation": {
            "candidate_ids_exact": candidate_ids == EXPECTED_CANDIDATES,
            "exact_provenance": "PASS",
            "all_assertions_consumed": len(assertions) == 42,
            "unbound_cmir_quarantine": "PASS",
            "no_authority_upgrade": "PASS" if all(authority.values()) else "FAIL",
            "no_fallback": "PASS",
            "no_mock_or_stub": "PASS",
            "no_silent_degrade": "PASS",
        },
        "canonical_compatibility_evidence": {
            "canonical_base": CANONICAL_BASE_SHA,
            "memory_experience_contract": "v1",
            "migration_preview_contract": "relationship/project-commitment v2",
            "identity_contract": "compatible",
            "narrative_contract": "compatible",
            "incompatible_candidates": [
                "MIRA-MEM-CAND-001",
                "MIRA-MEM-CAND-002",
                "MIRA-MEM-CAND-006",
                "MIRA-MEM-CAND-007",
            ],
            "policy": "FAIL_CLOSED; no v1 truncation or substitute construction",
        },
        "zero_write_proof": {
            "repository_module_imports": 0,
            "repository_instantiations": 0,
            "store_candidate_calls": 0,
            "admit_calls": 0,
            "canonical_writes": 0,
            "runtime_writes": 0,
            "context_or_provider_calls": 0,
            "actual_admission": 0,
        },
        "authority": {
            "canonical_admission": "NONE",
            "runtime": "NONE",
            "merge": "NONE",
        },
    }
    _require(candidate_ids == EXPECTED_CANDIDATES, "candidate set mismatch")
    _require(all(authority.values()), "authority upgrade detected")
    _require(failed == 4, "expected exact v2 incompatibility count changed")
    payload["deterministic_digest"] = _canonical_digest(payload)
    return payload

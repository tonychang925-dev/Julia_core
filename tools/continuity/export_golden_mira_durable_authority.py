"""One-time owner-gated immutable export of frozen P5 canonical admission."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from julia_core.durable_authority.contracts import canonical_json
from julia_core.durable_authority.filesystem_adapter import (
    AUTHORITY_REASON,
    AUTHORIZATION_TIME,
    EXPORT_TOOL_VERSION,
    EXPECTED_IDENTITY_REFS,
    EXPECTED_IDENTITY_VERSIONS,
    EXPECTED_MEMORY_REFS,
    EXPECTED_MEMORY_VERSIONS,
    GOVERNANCE_SCHEMA_VERSION,
    MANIFEST_SCHEMA_VERSION,
    OWNER_ACTOR,
    PERSONA_ID,
    RECORD_SCHEMA_VERSION,
    SOURCE_P5_ADMISSION_ARTIFACT,
    SOURCE_P4_ADMISSION_ARTIFACT,
    SOURCE_P4_SHA,
    P4_TASK_ID,
    P4_AUTHORITY_REASON,
    P4_AUTHORIZATION_TIME,
    SOURCE_REPO,
    SOURCE_SHA,
    FilesystemDurableAuthorityReader,
)
from julia_core.durable_authority.reconstruction import (
    reconstruct_from_durable_authority,
)
from julia_core.durable_authority.serialization import (
    build_identity_envelope,
    build_memory_experience_envelope,
)
from tools.continuity.p5_a1_admission import admit_golden_mira
from tools.continuity.p4_relationship_role_admission import admit_relationship_role


RECEIPT_NAME = "GOLDEN_MIRA_DURABLE_AUTHORITY_EXPORT_V1.json"
P5_ARTIFACT_SHA256 = (
    "f10a6d8daa6ed1604c2002254d26016efe31afca2e4dc18c4e1b094a48672110"
)
P4_ARTIFACT_SHA256 = (
    "6949dc22007378e6ad66fa9fff584e297f01a19571822bfe958d68dcb9dc5d61"
)


class GoldenMiraDurableExportError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if condition is not True:
        raise GoldenMiraDurableExportError(f"FAIL_CLOSED: {message}")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8", newline="\n")


def _verify_source_authority(repository: Path) -> None:
    resolved = subprocess.run(
        ["git", "rev-parse", f"{SOURCE_SHA}^{{commit}}"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _require(resolved == SOURCE_SHA, "P5 source SHA resolution")
    historical = subprocess.run(
        ["git", "show", f"{SOURCE_SHA}:{SOURCE_P5_ADMISSION_ARTIFACT}"],
        cwd=repository,
        check=True,
        capture_output=True,
    ).stdout
    current = (repository / SOURCE_P5_ADMISSION_ARTIFACT).read_bytes()
    _require(historical == current, "P5 authority artifact byte identity")
    _require(_sha256_bytes(current) == P5_ARTIFACT_SHA256, "P5 authority artifact digest")
    evidence = json.loads(current)
    _require(
        evidence["final_result"]
        == "P5_A1_RESULT=OWNER_AUTHORIZED_CANONICAL_ADMISSION_COMPLETE",
        "P5 authority result",
    )
    _require(
        evidence["write_summary"]["identity_versions"] == 3
        and evidence["write_summary"]["memory_experience_records"] == 8,
        "P5 authority exact counts",
    )
    p4_historical = subprocess.run(
        ["git", "show", f"{SOURCE_P4_SHA}:{SOURCE_P4_ADMISSION_ARTIFACT}"],
        cwd=repository, check=True, capture_output=True,
    ).stdout
    p4_current = (repository / SOURCE_P4_ADMISSION_ARTIFACT).read_bytes()
    _require(p4_historical == p4_current, "P4 authority artifact byte identity")
    _require(_sha256_bytes(p4_current) == P4_ARTIFACT_SHA256, "P4 authority artifact digest")
    p4_evidence = json.loads(p4_current)
    _require(p4_evidence["task_id"] == P4_TASK_ID, "P4 authority task")
    _require(p4_evidence["owner_authorization"]["status"] == "GRANTED", "P4 owner authorization")


def _identity_admission_event(envelope) -> dict[str, Any]:
    return envelope.governance_events[-1]


def _memory_admission_event(envelope) -> dict[str, Any]:
    return envelope.governance_events[-1]["admission"]


def _record(
    *,
    schema_version: str,
    envelope,
    record_type: str,
    canonical_ref: str,
    version: str,
    order_index: int,
    admission_event: dict[str, Any],
    task_id: str = "P5-A1",
    source_artifact_key: str = "source_p5_artifact",
    source_artifact: str = SOURCE_P5_ADMISSION_ARTIFACT,
    source_sha: str = SOURCE_SHA,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "record_type": record_type,
        "canonical_ref": canonical_ref,
        "version": version,
        "payload": envelope.payload_object,
        "payload_digest": envelope.payload_digest,
        "governance": list(envelope.governance_events),
        "lifecycle_status": envelope.lifecycle_status,
        "source_provenance": list(envelope.provenance),
        "admission_provenance": {
            "task_id": task_id,
            source_artifact_key: source_artifact,
            "source_sha": source_sha,
            "event": admission_event,
        },
        "order_index": order_index,
        "authority_family": envelope.authority_family.value,
        "authority_object_ref": envelope.authority_object_ref,
        "authority_object_schema": envelope.authority_object_schema,
        "serialized_payload": envelope.serialized_payload,
        "lineage_metadata": envelope.lineage_metadata,
        "envelope_digest": envelope.envelope_digest,
    }


def _package(
    repository: Path,
    authority_root: Path,
    receipt_output: Path,
    owner_authorization: str,
) -> dict[str, Any]:
    _require(owner_authorization == "GRANTED", "owner authorization gate")
    _verify_source_authority(repository)
    _require(authority_root.is_absolute(), "authority root must be absolute")
    _require(not authority_root.exists(), "authority root must not already exist")
    transaction = admit_golden_mira(repository)
    admit_relationship_role(transaction, repository)
    identity_envelopes = [
        build_identity_envelope(
            transaction.identity_repository.resolve(
                _identity_ref(canonical_ref, version)
            )
        )
        for canonical_ref, version in zip(
            EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS
        )
    ]
    memory_envelopes = [
        build_memory_experience_envelope(
            transaction.memory_repository.resolve(
                _memory_ref(canonical_ref, version)
            )
        )
        for canonical_ref, version in zip(EXPECTED_MEMORY_REFS, EXPECTED_MEMORY_VERSIONS)
    ]
    identity_records = []
    for index, (envelope, canonical_ref, version) in enumerate(
        zip(identity_envelopes, EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS)
    ):
        kwargs = {}
        if canonical_ref == EXPECTED_IDENTITY_REFS[-1]:
            kwargs = {
                "task_id": P4_TASK_ID,
                "source_artifact_key": "source_p4_artifact",
                "source_artifact": SOURCE_P4_ADMISSION_ARTIFACT,
                "source_sha": SOURCE_P4_SHA,
            }
        identity_records.append(
            _record(
                schema_version=RECORD_SCHEMA_VERSION,
                envelope=envelope,
                record_type="IDENTITY",
                canonical_ref=canonical_ref,
                version=version,
                order_index=index,
                admission_event=_identity_admission_event(envelope),
                **kwargs,
            )
        )
    memory_records = [
        _record(
            schema_version=RECORD_SCHEMA_VERSION,
            envelope=envelope,
            record_type="MEMORY_EXPERIENCE",
            canonical_ref=canonical_ref,
            version=version,
            order_index=index,
            admission_event=_memory_admission_event(envelope),
        )
        for index, (envelope, canonical_ref, version) in enumerate(
            zip(memory_envelopes, EXPECTED_MEMORY_REFS, EXPECTED_MEMORY_VERSIONS)
        )
    ]
    staging = authority_root.with_name(f".{authority_root.name}.tmp")
    _require(not staging.exists(), "authority staging root already exists")
    governance = {
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "persona_id": PERSONA_ID,
        "owner_actor": OWNER_ACTOR,
        "authority_reason": AUTHORITY_REASON,
        "authorization_time": AUTHORIZATION_TIME,
        "records_admitted": 12,
        "identity_lifecycle": "ADMITTED",
        "memory_experience_lifecycle": "ADMITTED",
        "source_p5_artifact": SOURCE_P5_ADMISSION_ARTIFACT,
        "source_p4_artifact": SOURCE_P4_ADMISSION_ARTIFACT,
        "p4_source_sha": SOURCE_P4_SHA,
        "p4_authority_reason": P4_AUTHORITY_REASON,
        "p4_authorization_time": P4_AUTHORIZATION_TIME,
    }
    record_digests = {}
    for directory, records in (
        ("identity", identity_records),
        ("memory_experience", memory_records),
    ):
        for record in records:
            path = f"{directory}/{record['order_index']:08d}.json"
            _write_json(staging / path, record)
            record_digests[path] = {
                "payload_digest": record["payload_digest"],
                "envelope_digest": record["envelope_digest"],
            }
    _write_json(staging / "governance" / "state.json", governance)
    package_files = {
        path: _sha256_file(staging / path)
        for path in (
            *(f"identity/{index:08d}.json" for index in range(4)),
            *(f"memory_experience/{index:08d}.json" for index in range(8)),
            "governance/state.json",
        )
    }
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "authority_type": "CANONICAL_SEMANTIC_AUTHORITY",
        "persona_id": PERSONA_ID,
        "created_from_p5_admission": True,
        "source_repo": SOURCE_REPO,
        "source_sha": SOURCE_SHA,
        "export_tool_version": EXPORT_TOOL_VERSION,
        "identity_count": 4,
        "memory_experience_count": 8,
        "ordered_identity_refs": list(EXPECTED_IDENTITY_REFS),
        "ordered_memory_experience_refs": list(EXPECTED_MEMORY_REFS),
        "record_digests": record_digests,
        "governance_state": {
            "owner_actor": OWNER_ACTOR,
            "reason": AUTHORITY_REASON,
            "authorization_time": AUTHORIZATION_TIME,
            "records_admitted": 12,
        },
        "lineage": {
            "identity": [record["lineage_metadata"] for record in identity_records],
            "memory_experience": [
                record["lineage_metadata"] for record in memory_records
            ],
        },
        "package_files": package_files,
    }
    manifest["manifest_digest"] = _sha256_text(canonical_json(manifest))
    _write_json(staging / "manifest.json", manifest)
    os.replace(staging, authority_root)
    for path in sorted(authority_root.rglob("*"), reverse=True):
        if path.is_file():
            path.chmod(0o444)
        elif path.is_dir():
            path.chmod(0o555)
    reader = FilesystemDurableAuthorityReader(authority_root)
    identity_repository, memory_repository = reconstruct_from_durable_authority(reader)
    for envelope, canonical_ref, version in zip(
        identity_envelopes, EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS
    ):
        governed = identity_repository.resolve(_identity_ref(canonical_ref, version))
        _require(build_identity_envelope(governed) == envelope, "identity export roundtrip")
    for envelope, canonical_ref, version in zip(
        memory_envelopes, EXPECTED_MEMORY_REFS, EXPECTED_MEMORY_VERSIONS
    ):
        governed = memory_repository.resolve(_memory_ref(canonical_ref, version))
        _require(
            build_memory_experience_envelope(governed) == envelope,
            "memory experience export roundtrip",
        )
    receipt = {
        "TASK_ID": "MIRA-E2E-P1-A",
        "SOURCE_SHA": SOURCE_SHA,
        "SOURCE_P5_ADMISSION_ARTIFACT": SOURCE_P5_ADMISSION_ARTIFACT,
        "IDENTITY_COUNT": 4,
        "MEMORY_EXPERIENCE_COUNT": 8,
        "IDENTITY_REFS": [
            f"{ref}/{version}"
            for ref, version in zip(
                EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS
            )
        ],
        "MEMORY_EXPERIENCE_REFS": [
            f"{ref}/{version}"
            for ref, version in zip(EXPECTED_MEMORY_REFS, EXPECTED_MEMORY_VERSIONS)
        ],
        "MANIFEST_SHA256": _sha256_file(authority_root / "manifest.json"),
        "PACKAGE_FILE_COUNT": 14,
        "PACKAGE_ROOT_DIGEST": _package_root_digest(authority_root),
        "CANONICAL_WRITES": 0,
        "NEW_ADMISSIONS": 0,
        "SUPERSEDES": 0,
        "RETIRES": 0,
        "EXPORT_RESULT": "GOLDEN_MIRA_DURABLE_AUTHORITY_EXPORT_COMPLETE",
    }
    _write_json(receipt_output, receipt)
    (receipt_output.parent).mkdir(parents=True, exist_ok=True)
    return receipt


def _identity_ref(canonical_ref: str, version: str):
    from julia_core.identity import IdentityRef

    return IdentityRef(lineage_id=canonical_ref, version_id=version)


def _memory_ref(canonical_ref: str, version: str):
    from julia_core.memory_experience import MemoryExperienceRef

    return MemoryExperienceRef(experience_id=canonical_ref, version_id=version)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _package_root_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--authority-root", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--owner-authorization", required=True)
    arguments = parser.parse_args()
    receipt = _package(
        repository=arguments.repository,
        authority_root=arguments.authority_root,
        receipt_output=arguments.receipt_output,
        owner_authorization=arguments.owner_authorization,
    )
    print(canonical_json(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

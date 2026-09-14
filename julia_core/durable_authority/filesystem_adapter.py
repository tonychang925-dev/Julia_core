"""Fail-closed filesystem reader for an immutable authority package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any

from julia_core.identity import IdentityRef
from julia_core.memory_experience import MemoryExperienceRef
from julia_core.runtime_canonical_binding import (
    RuntimeCanonicalAuthorityBindingRef,
)

from .contracts import (
    AuthorityFamily,
    DurableAuthorityEnvelope,
    DurableAuthorityErrorCode,
    DurableAuthorityPersistenceError,
    canonical_json,
)
from .serialization import envelope_from_dict, validate_envelope_semantics


MANIFEST_SCHEMA_VERSION = "julia_core.durable_authority.manifest.v1"
RECORD_SCHEMA_VERSION = "julia_core.durable_authority.record.v1"
GOVERNANCE_SCHEMA_VERSION = "julia_core.durable_authority.governance.v1"
PERSONA_ID = "golden-mira"
SOURCE_REPO = "https://github.com/tonychang925-dev/Julia_core.git"
SOURCE_SHA = "038e5219495fd765bfbcfdbb0a52afb48a730f90"
SOURCE_P5_ADMISSION_ARTIFACT = (
    "artifacts/continuity/"
    "P5_A1_OWNER_AUTHORIZED_GOLDEN_MIRA_CANONICAL_ADMISSION_V1.json"
)
EXPORT_TOOL_VERSION = "1"
OWNER_ACTOR = "owner:tony"
AUTHORITY_REASON = "P5-A1 owner-authorized Golden Mira canonical admission"
AUTHORIZATION_TIME = "owner-authorization:2026-09-13"

EXPECTED_IDENTITY_REFS = (
    "mira-golden:mira-id-cand-001",
    "mira-golden:mira-id-cand-002",
    "mira-golden:mira-id-cand-003",
)
EXPECTED_IDENTITY_VERSIONS = (
    "mira-id-cand-001-v0.1-preview",
    "mira-id-cand-002-v0.1-preview",
    "mira-id-cand-003-v0.1-preview",
)
EXPECTED_MEMORY_REFS = (
    "golden-mira:GM-CMIR-001",
    "golden-mira:GM-CMIR-002",
    "golden-mira:GM-CMIR-004",
    "golden-mira:GM-CMIR-006",
    "golden-mira:GM-CMIR-008",
    "golden-mira:GM-CMIR-011",
    "golden-mira:GM-CMIR-011",
    "golden-mira:GM-CMIR-013",
)
EXPECTED_MEMORY_VERSIONS = (
    "v0.2-preview",
    "v0.2-preview",
    "v0.1-preview",
    "v0.1-preview",
    "v0.1-preview",
    "formation-draft-preview",
    "frozen-final-preview",
    "v0.2-preview",
)

_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "authority_type",
        "persona_id",
        "created_from_p5_admission",
        "source_repo",
        "source_sha",
        "export_tool_version",
        "identity_count",
        "memory_experience_count",
        "ordered_identity_refs",
        "ordered_memory_experience_refs",
        "record_digests",
        "governance_state",
        "lineage",
        "package_files",
        "manifest_digest",
    }
)
_RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "record_type",
        "canonical_ref",
        "version",
        "payload",
        "payload_digest",
        "governance",
        "lifecycle_status",
        "source_provenance",
        "admission_provenance",
        "order_index",
        "authority_family",
        "authority_object_ref",
        "authority_object_schema",
        "serialized_payload",
        "lineage_metadata",
        "envelope_digest",
    }
)
_GOVERNANCE_FIELDS = frozenset(
    {
        "schema_version",
        "persona_id",
        "owner_actor",
        "authority_reason",
        "authorization_time",
        "records_admitted",
        "identity_lifecycle",
        "memory_experience_lifecycle",
        "source_p5_artifact",
    }
)


class FilesystemDurableAuthorityReader:
    """Read only the exact Golden Mira authority package supplied by injection."""

    __slots__ = ("_root", "_records")

    def __init__(self, authority_root: Path) -> None:
        if not isinstance(authority_root, Path):
            raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "authority root must be an explicit Path")
        root = authority_root
        if not root.is_absolute():
            root = None
            raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "authority root must be absolute")
        manifest_path = root / "manifest.json"
        if not manifest_path.is_file():
            raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "manifest.json is missing")
        manifest = _load_json(manifest_path)
        _validate_manifest(manifest)
        _validate_package_files(root, manifest["package_files"])
        governance = _load_json(root / "governance" / "state.json")
        _validate_governance(governance)
        records = _load_records(root, manifest)
        object.__setattr__(self, "_root", root)
        object.__setattr__(self, "_records", MappingProxyType(records))

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("filesystem durable authority readers are immutable")

    def read_exact(
        self,
        authority_family: AuthorityFamily,
        ref: IdentityRef | MemoryExperienceRef | RuntimeCanonicalAuthorityBindingRef,
    ) -> DurableAuthorityEnvelope:
        if type(authority_family) is not AuthorityFamily:
            raise _error(DurableAuthorityErrorCode.UNKNOWN_AUTHORITY_FAMILY, "authority family must be exact")
        ref_uri = ref.uri
        if ref_uri not in self._records:
            raise _error(DurableAuthorityErrorCode.REF_MISMATCH, f"authority record is missing: {ref_uri}")
        envelope = self._records[ref_uri]
        if envelope.authority_family is not authority_family or envelope.authority_object_ref != ref_uri:
            raise _error(DurableAuthorityErrorCode.REF_MISMATCH, "authority record does not match requested ref")
        return envelope

    def list_exact_refs(self, authority_family: AuthorityFamily) -> tuple[str, ...]:
        if type(authority_family) is not AuthorityFamily:
            raise _error(DurableAuthorityErrorCode.UNKNOWN_AUTHORITY_FAMILY, "authority family must be exact")
        refs = tuple(
            ref_uri
            for ref_uri, envelope in self._records.items()
            if envelope.authority_family is authority_family
        )
        return tuple(sorted(refs))


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if frozenset(manifest) != _MANIFEST_FIELDS:
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "manifest fields are inexact")
    expected = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "authority_type": "CANONICAL_SEMANTIC_AUTHORITY",
        "persona_id": PERSONA_ID,
        "created_from_p5_admission": True,
        "source_repo": SOURCE_REPO,
        "source_sha": SOURCE_SHA,
        "export_tool_version": EXPORT_TOOL_VERSION,
        "identity_count": 3,
        "memory_experience_count": 8,
    }
    if any(manifest[key] != value for key, value in expected.items()):
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "manifest authority binding mismatch")
    if manifest["ordered_identity_refs"] != list(EXPECTED_IDENTITY_REFS):
        raise _error(DurableAuthorityErrorCode.ORDER_MISMATCH, "identity order mismatch")
    if manifest["ordered_memory_experience_refs"] != list(EXPECTED_MEMORY_REFS):
        raise _error(DurableAuthorityErrorCode.ORDER_MISMATCH, "memory experience order mismatch")
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_digest"}
    if manifest["manifest_digest"] != _sha256_text(canonical_json(unsigned)):
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "manifest digest mismatch")
    if frozenset(manifest["record_digests"]) != frozenset(_ordered_record_keys()):
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "manifest record set mismatch")


def _validate_governance(governance: dict[str, Any]) -> None:
    expected = {
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "persona_id": PERSONA_ID,
        "owner_actor": OWNER_ACTOR,
        "authority_reason": AUTHORITY_REASON,
        "authorization_time": AUTHORIZATION_TIME,
        "records_admitted": 11,
        "identity_lifecycle": "ADMITTED",
        "memory_experience_lifecycle": "ADMITTED",
        "source_p5_artifact": SOURCE_P5_ADMISSION_ARTIFACT,
    }
    if frozenset(governance) != _GOVERNANCE_FIELDS or any(
        governance[key] != value for key, value in expected.items()
    ):
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "governance state mismatch")


def _validate_package_files(root: Path, package_files: dict[str, str]) -> None:
    if type(package_files) is not dict:
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "package file index is malformed")
    expected_paths = set(_ordered_record_keys()) | {"governance/state.json"}
    actual_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path != root / "manifest.json"
        and (path.is_symlink() or not path.is_dir())
    }
    if any(
        path.is_symlink()
        for path in root.rglob("*")
        if path != root / "manifest.json"
    ):
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "package contains a symlink")
    if set(package_files) != expected_paths or actual_paths != expected_paths:
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "package file set mismatch")
    if any(package_files[path] != _sha256_file(root / path) for path in expected_paths):
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "package file digest mismatch")


def _load_records(root: Path, manifest: dict[str, Any]) -> dict[str, DurableAuthorityEnvelope]:
    records = {}
    identity_metadata = manifest["lineage"]["identity"]
    memory_metadata = manifest["lineage"]["memory_experience"]
    for family, directory, refs, versions, lineage_metadata in (
        (AuthorityFamily.IDENTITY, "identity", EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS, identity_metadata),
        (AuthorityFamily.MEMORY_EXPERIENCE, "memory_experience", EXPECTED_MEMORY_REFS, EXPECTED_MEMORY_VERSIONS, memory_metadata),
    ):
        previous_ref = None
        seen = set()
        for order_index, (canonical_ref, version) in enumerate(zip(refs, versions)):
            path = root / directory / f"{order_index:08d}.json"
            record = _load_json(path)
            _validate_record(record, family, canonical_ref, version, order_index, lineage_metadata[order_index])
            envelope = _record_envelope(record)
            validate_envelope_semantics(envelope)
            _validate_record_semantics(record, envelope)
            key = envelope.authority_object_ref
            if key in seen:
                raise _error(DurableAuthorityErrorCode.DUPLICATE_CONFLICT, f"unexpected duplicate authority record: {key}")
            seen.add(key)
            record_digests = manifest["record_digests"][_record_key(directory, order_index)]
            if record_digests != {
                "payload_digest": envelope.payload_digest,
                "envelope_digest": envelope.envelope_digest,
            }:
                raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "manifest record digest mismatch")
            predecessor = envelope.lineage_metadata["predecessor_version_id"]
            if predecessor is not None and family is AuthorityFamily.IDENTITY:
                expected_predecessor = (
                    f"{envelope.authority_object_ref.rsplit('/', 1)[0]}/{predecessor}"
                )
                if expected_predecessor not in EXPECTED_IDENTITY_REFS:
                    raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "identity lineage mismatch")
            if predecessor is not None and family is AuthorityFamily.MEMORY_EXPERIENCE:
                expected_predecessor = (
                    f"{envelope.authority_object_ref.rsplit('/', 1)[0]}/{predecessor}"
                )
                if expected_predecessor not in seen or expected_predecessor != previous_ref:
                    raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "memory experience lineage mismatch")
            records[key] = envelope
            previous_ref = key
    return records


def _validate_record(
    record: dict[str, Any],
    family: AuthorityFamily,
    canonical_ref: str,
    version: str,
    order_index: int,
    lineage_metadata: dict[str, Any],
) -> None:
    if frozenset(record) != _RECORD_FIELDS:
        raise _error(DurableAuthorityErrorCode.PARTIAL_ENVELOPE, "durable record fields are inexact")
    if (
        record["schema_version"] != RECORD_SCHEMA_VERSION
        or record["record_type"] != family.value
        or record["canonical_ref"] != canonical_ref
        or record["version"] != version
        or record["order_index"] != order_index
        or record["lifecycle_status"] != "ADMITTED"
    ):
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "durable record binding mismatch")
    if record["lineage_metadata"] != lineage_metadata:
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "durable lineage mismatch")
    if type(record["source_provenance"]) is not list or not record["source_provenance"]:
        raise _error(DurableAuthorityErrorCode.PROVENANCE_MISSING, "source provenance is missing")
    if type(record["admission_provenance"]) is not dict or not record["admission_provenance"]:
        raise _error(DurableAuthorityErrorCode.PROVENANCE_MISSING, "admission provenance is missing")


def _validate_record_semantics(record: dict[str, Any], envelope: DurableAuthorityEnvelope) -> None:
    if record["serialized_payload"] != canonical_json(record["payload"]):
        raise _error(DurableAuthorityErrorCode.PAYLOAD_DIGEST_MISMATCH, "payload representation is not canonical")
    if record["source_provenance"] != list(envelope.provenance):
        raise _error(DurableAuthorityErrorCode.PROVENANCE_MISSING, "source provenance does not match payload")
    admission = record["admission_provenance"]
    event = admission.get("event")
    if (
        admission.get("task_id") != "P5-A1"
        or admission.get("source_p5_artifact") != SOURCE_P5_ADMISSION_ARTIFACT
        or admission.get("source_sha") != SOURCE_SHA
        or not _is_final_admission_event(event, envelope)
    ):
        raise _error(DurableAuthorityErrorCode.PROVENANCE_MISSING, "admission provenance mismatch")


def _is_final_admission_event(event: object, envelope: DurableAuthorityEnvelope) -> bool:
    if type(event) is not dict or not envelope.governance_events:
        return False
    final = envelope.governance_events[-1]
    if envelope.authority_family is AuthorityFamily.IDENTITY:
        return event == final
    return (
        event == final.get("admission")
        and final.get("status") == "ADMITTED"
        and len(envelope.governance_events) == 2
        and envelope.governance_events[0] == {"status": "CANDIDATE", "admission": None}
    )


def _record_envelope(record: dict[str, Any]) -> DurableAuthorityEnvelope:
    return envelope_from_dict(
        {
            "envelope_schema": "julia_core.durable_authority.envelope.v1",
            "authority_family": record["record_type"],
            "authority_object_ref": record["authority_object_ref"],
            "authority_object_schema": record["authority_object_schema"],
            "serialized_payload": record["serialized_payload"],
            "payload_digest": record["payload_digest"],
            "governance_events": record["governance"],
            "lifecycle_status": record["lifecycle_status"],
            "lineage_metadata": record["lineage_metadata"],
            "provenance": record["source_provenance"],
            "envelope_digest": record["envelope_digest"],
        }
    )


def _ordered_record_keys():
    return (
        *(_record_key("identity", index) for index in range(3)),
        *(_record_key("memory_experience", index) for index in range(8)),
    )


def _record_key(directory: str, order_index: int) -> str:
    return f"{directory}/{order_index:08d}.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, f"fail-closed JSON read: {path.name}") from error
    if type(value) is not dict:
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "durable JSON document must be an object")
    return value


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _error(code: DurableAuthorityErrorCode, message: str) -> DurableAuthorityPersistenceError:
    return DurableAuthorityPersistenceError(code, f"FAIL_CLOSED: {message}")


__all__ = ["FilesystemDurableAuthorityReader"]

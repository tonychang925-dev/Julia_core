"""Golden Mira durable authority v2 reader for append-only semantic-fidelity successors."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from types import MappingProxyType
from typing import Any

from julia_core.identity import IdentityRef
from julia_core.memory_experience import MemoryExperienceRef

from .contracts import (
    AuthorityFamily,
    DurableAuthorityEnvelope,
    DurableAuthorityErrorCode,
    DurableAuthorityPersistenceError,
    canonical_json,
)
from .filesystem_adapter import (
    EXPECTED_IDENTITY_REFS,
    EXPECTED_IDENTITY_VERSIONS,
    PERSONA_ID,
    SOURCE_P4_ADMISSION_ARTIFACT,
    SOURCE_P4_SHA,
    SOURCE_P5_ADMISSION_ARTIFACT,
    SOURCE_REPO,
)
from .serialization import envelope_from_dict, validate_envelope_semantics


MANIFEST_SCHEMA_VERSION_V2 = "julia_core.durable_authority.manifest.v2"
GOVERNANCE_SCHEMA_VERSION_V3 = "julia_core.durable_authority.governance.v3"
RECORD_SCHEMA_VERSION = "julia_core.durable_authority.record.v1"
EXPORT_TOOL_VERSION_V2 = "3"

P5E_TASK_ID = "P5-E-CF-UPSTREAM-SEMANTIC-LOSS-CORRECTION-P0"
P5E_CORRECTION_MANIFEST = (
    "artifacts/mira_migration_prep/"
    "P5_E_GM_CMIR_004_SEMANTIC_FIDELITY_CORRECTION_MANIFEST_V1.json"
)
P5E_SUCCESSOR_PREP = (
    "artifacts/mira_migration_prep/"
    "P5_E_GM_CMIR_004_SEMANTIC_FIDELITY_SUCCESSOR_PREP_V1.json"
)
P5E_OWNER_AUTHORIZATION = (
    "artifacts/mira_migration_prep/"
    "P5_E_GM_CMIR_004_OWNER_AUTHORIZATION_V1.json"
)
P5E_AUTHORITY_REASON = (
    "P5-E owner-authorized GM-CMIR-004 semantic-fidelity successor admission"
)
P5E_AUTHORIZATION_TIME = "2026-09-26T16:10:00+08:00"

DURABLE_MEMORY_REFS_V2 = (
    "golden-mira:GM-CMIR-001",
    "golden-mira:GM-CMIR-002",
    "golden-mira:GM-CMIR-004",
    "golden-mira:GM-CMIR-004",
    "golden-mira:GM-CMIR-006",
    "golden-mira:GM-CMIR-008",
    "golden-mira:GM-CMIR-011",
    "golden-mira:GM-CMIR-011",
    "golden-mira:GM-CMIR-013",
)
DURABLE_MEMORY_VERSIONS_V2 = (
    "v0.2-preview",
    "v0.2-preview",
    "v0.1-preview",
    "v0.2-semantic-fidelity-preview",
    "v0.1-preview",
    "v0.1-preview",
    "formation-draft-preview",
    "frozen-final-preview",
    "v0.2-preview",
)
DURABLE_MEMORY_STATUSES_V2 = (
    "ADMITTED",
    "ADMITTED",
    "SUPERSEDED",
    "ADMITTED",
    "ADMITTED",
    "ADMITTED",
    "ADMITTED",
    "ADMITTED",
    "ADMITTED",
)
ACTIVE_MEMORY_REFS_V2 = (
    "golden-mira:GM-CMIR-001",
    "golden-mira:GM-CMIR-002",
    "golden-mira:GM-CMIR-004",
    "golden-mira:GM-CMIR-006",
    "golden-mira:GM-CMIR-008",
    "golden-mira:GM-CMIR-011",
    "golden-mira:GM-CMIR-011",
    "golden-mira:GM-CMIR-013",
)
ACTIVE_MEMORY_VERSIONS_V2 = (
    "v0.2-preview",
    "v0.2-preview",
    "v0.2-semantic-fidelity-preview",
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
        "active_memory_experience_refs",
        "active_memory_experience_versions",
        "record_digests",
        "governance_state",
        "lineage",
        "package_files",
        "semantic_fidelity",
        "psb_binding",
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
        "source_p4_artifact",
        "source_semantic_fidelity_artifact",
        "source_owner_authorization_artifact",
    }
)
_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_SHA64 = re.compile(r"[0-9a-f]{64}\Z")


class GoldenMiraDurableAuthorityV2Reader:
    """Read and verify the v2 append-only Golden Mira authority package."""

    __slots__ = ("_root", "_records", "_manifest")

    def __init__(self, authority_root: Path) -> None:
        if not isinstance(authority_root, Path) or not authority_root.is_absolute():
            raise _error(
                DurableAuthorityErrorCode.MANIFEST_MISMATCH,
                "v2 authority root must be an explicit absolute Path",
            )
        manifest_path = authority_root / "manifest.json"
        if not manifest_path.is_file():
            raise _error(
                DurableAuthorityErrorCode.MANIFEST_MISMATCH,
                "v2 manifest.json is missing",
            )
        manifest = _load_json(manifest_path)
        _validate_manifest(manifest)
        _validate_package_files(authority_root, manifest["package_files"])
        governance = _load_json(authority_root / "governance" / "state.json")
        _validate_governance(governance)
        records = _load_records(authority_root, manifest)
        object.__setattr__(self, "_root", authority_root)
        object.__setattr__(self, "_records", MappingProxyType(records))
        object.__setattr__(self, "_manifest", MappingProxyType(manifest))

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("GoldenMiraDurableAuthorityV2Reader is immutable")

    @property
    def source_sha(self) -> str:
        return self._manifest["source_sha"]

    @property
    def active_memory_refs(self) -> tuple[str, ...]:
        return ACTIVE_MEMORY_REFS_V2

    @property
    def active_memory_versions(self) -> tuple[str, ...]:
        return ACTIVE_MEMORY_VERSIONS_V2

    @property
    def psb_binding_expectation(self) -> dict[str, str]:
        return dict(self._manifest["psb_binding"])

    @property
    def semantic_fidelity(self) -> dict[str, Any]:
        return dict(self._manifest["semantic_fidelity"])

    def read_exact(
        self,
        authority_family: AuthorityFamily,
        ref: IdentityRef | MemoryExperienceRef,
    ) -> DurableAuthorityEnvelope:
        if type(authority_family) is not AuthorityFamily:
            raise _error(
                DurableAuthorityErrorCode.UNKNOWN_AUTHORITY_FAMILY,
                "authority family must be exact",
            )
        ref_uri = ref.uri
        envelope = self._records.get(ref_uri)
        if envelope is None:
            raise _error(
                DurableAuthorityErrorCode.REF_MISMATCH,
                f"v2 authority record is missing: {ref_uri}",
            )
        if envelope.authority_family is not authority_family:
            raise _error(
                DurableAuthorityErrorCode.REF_MISMATCH,
                "v2 authority family mismatch",
            )
        return envelope

    def list_exact_refs(self, authority_family: AuthorityFamily) -> tuple[str, ...]:
        if type(authority_family) is not AuthorityFamily:
            raise _error(
                DurableAuthorityErrorCode.UNKNOWN_AUTHORITY_FAMILY,
                "authority family must be exact",
            )
        return tuple(
            sorted(
                ref_uri
                for ref_uri, envelope in self._records.items()
                if envelope.authority_family is authority_family
            )
        )


def is_v2_manifest(authority_root: Path) -> bool:
    try:
        manifest = json.loads((authority_root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return (
        type(manifest) is dict
        and manifest.get("schema_version") == MANIFEST_SCHEMA_VERSION_V2
    )


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if frozenset(manifest) != _MANIFEST_FIELDS:
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 manifest fields are inexact",
        )
    expected = {
        "schema_version": MANIFEST_SCHEMA_VERSION_V2,
        "authority_type": "CANONICAL_SEMANTIC_AUTHORITY",
        "persona_id": PERSONA_ID,
        "created_from_p5_admission": True,
        "source_repo": SOURCE_REPO,
        "export_tool_version": EXPORT_TOOL_VERSION_V2,
        "identity_count": 4,
        "memory_experience_count": 9,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 manifest authority binding mismatch",
        )
    if type(manifest["source_sha"]) is not str or _SHA40.fullmatch(manifest["source_sha"]) is None:
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 source SHA is malformed",
        )
    if manifest["ordered_identity_refs"] != list(EXPECTED_IDENTITY_REFS):
        raise _error(DurableAuthorityErrorCode.ORDER_MISMATCH, "v2 identity order mismatch")
    if manifest["ordered_memory_experience_refs"] != list(DURABLE_MEMORY_REFS_V2):
        raise _error(
            DurableAuthorityErrorCode.ORDER_MISMATCH,
            "v2 durable memory order mismatch",
        )
    if manifest["active_memory_experience_refs"] != list(ACTIVE_MEMORY_REFS_V2):
        raise _error(
            DurableAuthorityErrorCode.ORDER_MISMATCH,
            "v2 active memory refs mismatch",
        )
    if manifest["active_memory_experience_versions"] != list(ACTIVE_MEMORY_VERSIONS_V2):
        raise _error(
            DurableAuthorityErrorCode.ORDER_MISMATCH,
            "v2 active memory versions mismatch",
        )
    semantic = manifest["semantic_fidelity"]
    required_semantic = {
        "task_id",
        "correction_manifest",
        "correction_manifest_sha256",
        "correction_manifest_digest",
        "successor_prep",
        "successor_prep_sha256",
        "owner_authorization",
        "owner_authorization_sha256",
        "predecessor_ref",
        "successor_ref",
        "successor_payload_digest",
    }
    if type(semantic) is not dict or frozenset(semantic) != required_semantic:
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 semantic-fidelity manifest is inexact",
        )
    if semantic["task_id"] != P5E_TASK_ID:
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "v2 task mismatch")
    for key in (
        "correction_manifest_sha256",
        "correction_manifest_digest",
        "successor_prep_sha256",
        "owner_authorization_sha256",
        "successor_payload_digest",
    ):
        if type(semantic[key]) is not str or _SHA64.fullmatch(semantic[key]) is None:
            raise _error(
                DurableAuthorityErrorCode.MANIFEST_MISMATCH,
                f"v2 semantic digest malformed: {key}",
            )
    psb = manifest["psb_binding"]
    if (
        type(psb) is not dict
        or frozenset(psb)
        != {
            "binding_version",
            "object_digest",
            "projected_digest",
            "experience_source_digest",
            "experience_projected_digest",
        }
        or psb["binding_version"] != "v3"
        or any(
            type(psb[key]) is not str or _SHA64.fullmatch(psb[key]) is None
            for key in (
                "object_digest",
                "projected_digest",
                "experience_source_digest",
                "experience_projected_digest",
            )
        )
    ):
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 PSB binding expectation is inexact",
        )
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_digest"}
    if manifest["manifest_digest"] != _sha256_text(canonical_json(unsigned)):
        raise _error(DurableAuthorityErrorCode.MANIFEST_MISMATCH, "v2 manifest digest mismatch")
    if frozenset(manifest["record_digests"]) != frozenset(_ordered_record_keys()):
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 manifest record set mismatch",
        )


def _validate_governance(governance: dict[str, Any]) -> None:
    if frozenset(governance) != _GOVERNANCE_FIELDS:
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 governance fields are inexact",
        )
    expected = {
        "schema_version": GOVERNANCE_SCHEMA_VERSION_V3,
        "persona_id": PERSONA_ID,
        "owner_actor": "owner:tony",
        "authority_reason": P5E_AUTHORITY_REASON,
        "authorization_time": P5E_AUTHORIZATION_TIME,
        "records_admitted": 13,
        "identity_lifecycle": "ADMITTED",
        "memory_experience_lifecycle": "MIXED_ADMITTED_AND_SUPERSEDED",
        "source_p5_artifact": SOURCE_P5_ADMISSION_ARTIFACT,
        "source_p4_artifact": SOURCE_P4_ADMISSION_ARTIFACT,
        "source_semantic_fidelity_artifact": P5E_SUCCESSOR_PREP,
        "source_owner_authorization_artifact": P5E_OWNER_AUTHORIZATION,
    }
    if any(governance.get(key) != value for key, value in expected.items()):
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 governance state mismatch",
        )


def _validate_package_files(root: Path, package_files: dict[str, str]) -> None:
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
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 package contains a symlink",
        )
    if type(package_files) is not dict or set(package_files) != expected_paths or actual_paths != expected_paths:
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 package file set mismatch",
        )
    if any(package_files[path] != _sha256_file(root / path) for path in expected_paths):
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 package file digest mismatch",
        )


def _load_records(
    root: Path, manifest: dict[str, Any]
) -> dict[str, DurableAuthorityEnvelope]:
    records: dict[str, DurableAuthorityEnvelope] = {}
    identity_metadata = manifest["lineage"]["identity"]
    memory_metadata = manifest["lineage"]["memory_experience"]
    for family, directory, refs, versions, statuses, lineage_metadata in (
        (
            AuthorityFamily.IDENTITY,
            "identity",
            EXPECTED_IDENTITY_REFS,
            EXPECTED_IDENTITY_VERSIONS,
            ("ADMITTED",) * len(EXPECTED_IDENTITY_REFS),
            identity_metadata,
        ),
        (
            AuthorityFamily.MEMORY_EXPERIENCE,
            "memory_experience",
            DURABLE_MEMORY_REFS_V2,
            DURABLE_MEMORY_VERSIONS_V2,
            DURABLE_MEMORY_STATUSES_V2,
            memory_metadata,
        ),
    ):
        previous_ref: str | None = None
        seen: set[str] = set()
        for order_index, (canonical_ref, version, status) in enumerate(
            zip(refs, versions, statuses)
        ):
            path = root / directory / f"{order_index:08d}.json"
            record = _load_json(path)
            _validate_record(
                record,
                family,
                canonical_ref,
                version,
                status,
                order_index,
                lineage_metadata[order_index],
                manifest,
            )
            envelope = _record_envelope(record)
            validate_envelope_semantics(envelope)
            _validate_record_semantics(record, envelope, manifest)
            key = envelope.authority_object_ref
            if key in seen:
                raise _error(
                    DurableAuthorityErrorCode.DUPLICATE_CONFLICT,
                    f"v2 duplicate exact authority record: {key}",
                )
            seen.add(key)
            expected_digests = manifest["record_digests"][
                _record_key(directory, order_index)
            ]
            if expected_digests != {
                "payload_digest": envelope.payload_digest,
                "envelope_digest": envelope.envelope_digest,
            }:
                raise _error(
                    DurableAuthorityErrorCode.MANIFEST_MISMATCH,
                    "v2 manifest record digest mismatch",
                )
            predecessor = envelope.lineage_metadata["predecessor_version_id"]
            if predecessor is not None and family is AuthorityFamily.MEMORY_EXPERIENCE:
                expected_predecessor = (
                    f"{envelope.authority_object_ref.rsplit('/', 1)[0]}/{predecessor}"
                )
                if expected_predecessor not in seen or expected_predecessor != previous_ref:
                    raise _error(
                        DurableAuthorityErrorCode.MANIFEST_MISMATCH,
                        "v2 memory lineage mismatch",
                    )
            records[key] = envelope
            previous_ref = key
    return records


def _validate_record(
    record: dict[str, Any],
    family: AuthorityFamily,
    canonical_ref: str,
    version: str,
    lifecycle_status: str,
    order_index: int,
    lineage_metadata: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    if frozenset(record) != _RECORD_FIELDS:
        raise _error(DurableAuthorityErrorCode.PARTIAL_ENVELOPE, "v2 durable record fields are inexact")
    if (
        record["schema_version"] != RECORD_SCHEMA_VERSION
        or record["record_type"] != family.value
        or record["canonical_ref"] != canonical_ref
        or record["version"] != version
        or record["order_index"] != order_index
        or record["lifecycle_status"] != lifecycle_status
        or record["lineage_metadata"] != lineage_metadata
    ):
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 durable record binding mismatch",
        )
    if type(record["source_provenance"]) is not list or not record["source_provenance"]:
        raise _error(DurableAuthorityErrorCode.PROVENANCE_MISSING, "v2 source provenance missing")
    if type(record["admission_provenance"]) is not dict or not record["admission_provenance"]:
        raise _error(DurableAuthorityErrorCode.PROVENANCE_MISSING, "v2 admission provenance missing")


def _validate_record_semantics(
    record: dict[str, Any],
    envelope: DurableAuthorityEnvelope,
    manifest: dict[str, Any],
) -> None:
    if record["serialized_payload"] != canonical_json(record["payload"]):
        raise _error(
            DurableAuthorityErrorCode.PAYLOAD_DIGEST_MISMATCH,
            "v2 payload representation is not canonical",
        )
    if record["source_provenance"] != list(envelope.provenance):
        raise _error(
            DurableAuthorityErrorCode.PROVENANCE_MISSING,
            "v2 source provenance does not match payload",
        )
    admission = record["admission_provenance"]
    canonical_ref = record["canonical_ref"]
    version = record["version"]

    if envelope.authority_family is AuthorityFamily.IDENTITY:
        final = envelope.governance_events[-1]
        if canonical_ref == EXPECTED_IDENTITY_REFS[-1]:
            valid = (
                admission.get("task_id")
                == "MIRA-P4-C04-RELATIONSHIP-ROLE-ADMISSION-P0"
                and admission.get("source_p4_artifact")
                == SOURCE_P4_ADMISSION_ARTIFACT
                and admission.get("source_sha") == SOURCE_P4_SHA
                and admission.get("event") == final
            )
        else:
            valid = (
                admission.get("task_id") == "P5-A1"
                and admission.get("source_p5_artifact")
                == SOURCE_P5_ADMISSION_ARTIFACT
                and admission.get("event") == final
            )
        if not valid:
            raise _error(
                DurableAuthorityErrorCode.PROVENANCE_MISSING,
                "v2 identity admission provenance mismatch",
            )
        return

    semantic = manifest["semantic_fidelity"]
    governance = list(envelope.governance_events)
    if canonical_ref == "golden-mira:GM-CMIR-004" and version == "v0.1-preview":
        valid = (
            admission.get("task_id") == "P5-A1"
            and admission.get("source_p5_artifact") == SOURCE_P5_ADMISSION_ARTIFACT
            and admission.get("event") == governance[1].get("admission")
            and admission.get("supersession_task_id") == P5E_TASK_ID
            and admission.get("source_owner_authorization_artifact")
            == P5E_OWNER_AUTHORIZATION
            and admission.get("supersession_event")
            == governance[-1].get("admission")
            and governance[-1].get("status") == "SUPERSEDED"
            and len(governance) == 3
        )
    elif (
        canonical_ref == "golden-mira:GM-CMIR-004"
        and version == "v0.2-semantic-fidelity-preview"
    ):
        final = governance[-1]
        valid = (
            admission.get("task_id") == P5E_TASK_ID
            and admission.get("source_semantic_fidelity_artifact")
            == P5E_SUCCESSOR_PREP
            and admission.get("source_owner_authorization_artifact")
            == P5E_OWNER_AUTHORIZATION
            and admission.get("event") == final.get("admission")
            and final.get("status") == "ADMITTED"
            and len(governance) == 2
            and any(
                item.get("source_type") == "semantic-fidelity-correction"
                and item.get("source_digest")
                == semantic["correction_manifest_digest"]
                for item in record["source_provenance"]
            )
        )
    else:
        final = governance[-1]
        valid = (
            admission.get("task_id") == "P5-A1"
            and admission.get("source_p5_artifact") == SOURCE_P5_ADMISSION_ARTIFACT
            and admission.get("event") == final.get("admission")
            and final.get("status") == "ADMITTED"
            and len(governance) == 2
        )
    if not valid:
        raise _error(
            DurableAuthorityErrorCode.PROVENANCE_MISSING,
            "v2 memory admission provenance mismatch",
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


def _ordered_record_keys() -> tuple[str, ...]:
    return (
        *(_record_key("identity", index) for index in range(len(EXPECTED_IDENTITY_REFS))),
        *(_record_key("memory_experience", index) for index in range(len(DURABLE_MEMORY_REFS_V2))),
    )


def _record_key(directory: str, order_index: int) -> str:
    return f"{directory}/{order_index:08d}.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            f"v2 fail-closed JSON read: {path.name}",
        ) from error
    if type(value) is not dict:
        raise _error(
            DurableAuthorityErrorCode.MANIFEST_MISMATCH,
            "v2 durable JSON document must be an object",
        )
    return value


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _error(
    code: DurableAuthorityErrorCode, message: str
) -> DurableAuthorityPersistenceError:
    return DurableAuthorityPersistenceError(code, f"FAIL_CLOSED: {message}")


__all__ = [
    "ACTIVE_MEMORY_REFS_V2",
    "ACTIVE_MEMORY_VERSIONS_V2",
    "DURABLE_MEMORY_REFS_V2",
    "DURABLE_MEMORY_VERSIONS_V2",
    "GoldenMiraDurableAuthorityV2Reader",
    "MANIFEST_SCHEMA_VERSION_V2",
    "P5E_AUTHORIZATION_TIME",
    "P5E_AUTHORITY_REASON",
    "P5E_CORRECTION_MANIFEST",
    "P5E_OWNER_AUTHORIZATION",
    "P5E_SUCCESSOR_PREP",
    "P5E_TASK_ID",
    "is_v2_manifest",
]

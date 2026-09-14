from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from julia_core.durable_authority.contracts import (
    AuthorityFamily,
    ENVELOPE_SCHEMA_VERSION,
    canonical_json,
    envelope_digest,
)
from julia_core.durable_authority.filesystem_adapter import (
    EXPECTED_IDENTITY_REFS,
    EXPECTED_IDENTITY_VERSIONS,
    EXPECTED_MEMORY_REFS,
    EXPECTED_MEMORY_VERSIONS,
    FilesystemDurableAuthorityReader,
)
from julia_core.durable_authority.reconstruction import (
    reconstruct_from_durable_authority,
)
from julia_core.identity import IdentityRef
from julia_core.memory_experience import MemoryExperienceRef


REPOSITORY = Path(__file__).resolve().parents[2]
EXPECTED_IDENTITY_DIGESTS = (
    "7580e0a930dc7f3d5446da2cdd8d1c23cf251e12929fb2f3baa056bd9739dd44",
    "adaa2508c4e475a700c394eb205e278d515dfe014ccdaa4bab3c3e7b7dcd5f3a",
    "0008a5e157347ae9b0dd8600d661ec4a0e3fbd1858673cd04dc7c7b812a96c29",
)
EXPECTED_MEMORY_DIGESTS = (
    "4e29eb74de7f29bbf8d69485a7c18b5dceb06486d7e1d986d668a30c85fb7228",
    "e4374452173b144ce48dbefa5299f1ac3dc15cec3615b8e7d528176293536f93",
    "ba4edeff89bc8054be19d7a48226fcef74359bc85d17dbd6abea4b754b905f97",
    "47636f46d2934eeb66f91c8202e2245c180b7077fddd04ca6445683308b54f2c",
    "08c95873446b01949b7aec50ad35ebbe36ce8b5b9ad87aca45c51b627f70c408",
    "3107a3ab38d0fc0d2446752f48bedebf2ee336e3cb8b22811bf3c156247a4ae9",
    "3c31de4d62ecfd5d7857a5a4df85725affa0862d0055b5527d7d80f27fcc8ad8",
    "8e2d16304357b7fb72b5b6cb53501be5d8743b3c687d2f0aadf3a9e1e132046c",
)


@pytest.fixture(scope="module")
def exported_package(tmp_path_factory):
    from tools.continuity.export_golden_mira_durable_authority import _package

    root = tmp_path_factory.mktemp("authority-root") / "authority"
    receipt = tmp_path_factory.mktemp("receipt") / "receipt.json"
    return root, _package(
        repository=REPOSITORY,
        authority_root=root,
        receipt_output=receipt,
        owner_authorization="GRANTED",
    )


def test_t1_exact_export_read_and_reconstruction_roundtrip(exported_package) -> None:
    root, receipt = exported_package
    reader = FilesystemDurableAuthorityReader(root)
    identities, memories = reconstruct_from_durable_authority(reader)
    identity_records = _records(root, "identity")
    memory_records = _records(root, "memory_experience")

    assert [record["canonical_ref"] for record in identity_records] == list(
        EXPECTED_IDENTITY_REFS
    )
    assert [record["version"] for record in identity_records] == list(
        EXPECTED_IDENTITY_VERSIONS
    )
    assert [record["payload_digest"] for record in identity_records] == list(
        EXPECTED_IDENTITY_DIGESTS
    )
    assert [record["canonical_ref"] for record in memory_records] == list(
        EXPECTED_MEMORY_REFS
    )
    assert [record["version"] for record in memory_records] == list(
        EXPECTED_MEMORY_VERSIONS
    )
    assert [record["payload_digest"] for record in memory_records] == list(
        EXPECTED_MEMORY_DIGESTS
    )
    for ref, version, digest in zip(
        EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS, EXPECTED_IDENTITY_DIGESTS
    ):
        governed = identities.resolve(IdentityRef(lineage_id=ref, version_id=version))
        assert governed.status.value == "ADMITTED"
        assert governed.version.digest() == digest
    for ref, version, digest in zip(
        EXPECTED_MEMORY_REFS, EXPECTED_MEMORY_VERSIONS, EXPECTED_MEMORY_DIGESTS
    ):
        governed = memories.resolve(
            MemoryExperienceRef(experience_id=ref, version_id=version)
        )
        assert governed.status.value == "ADMITTED"
        assert governed.record.digest() == digest
    assert receipt["IDENTITY_COUNT"] == 3
    assert receipt["MEMORY_EXPERIENCE_COUNT"] == 8
    assert receipt["CANONICAL_WRITES"] == 0
    assert receipt["NEW_ADMISSIONS"] == 0
    assert receipt["SUPERSEDES"] == 0
    assert receipt["RETIRES"] == 0


def test_runtime_fixture_independence(exported_package) -> None:
    root, _ = exported_package
    program = (
        "import sys\n"
        "from pathlib import Path\n"
        "from julia_core.durable_authority import ("
        "FilesystemDurableAuthorityReader, reconstruct_from_durable_authority)\n"
        "reconstruct_from_durable_authority(FilesystemDurableAuthorityReader(Path(sys.argv[1])))\n"
        "print('\\n'.join(sorted(sys.modules)))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", program, str(root)],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=True,
        env=os.environ | {"PYTHONPATH": str(REPOSITORY)},
    )
    modules = result.stdout.splitlines()
    assert "tools.mira_migration.admission_sim" not in modules
    assert "tools.continuity.p5_a1_admission" not in modules
    reader_source = (
        REPOSITORY / "julia_core/durable_authority/filesystem_adapter.py"
    ).read_text(encoding="utf-8")
    reconstruction_source = (
        REPOSITORY / "julia_core/durable_authority/reconstruction.py"
    ).read_text(encoding="utf-8")
    assert "tools.mira_migration" not in reader_source + reconstruction_source
    assert "p5_a1" not in reader_source + reconstruction_source


def test_t2_manifest_digest_corruption_fails(exported_package, tmp_path) -> None:
    root = _copy_package(exported_package[0], tmp_path)
    path = root / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["identity_count"] = 2
    _write(path, manifest)
    _fails(root)


def test_t3_payload_digest_corruption_fails(exported_package, tmp_path) -> None:
    root = _copy_package(exported_package[0], tmp_path)
    _rewrite_record(root, "identity", 0, {"payload_digest": "0" * 64})
    _fails(root)


def test_t4_missing_identity_fails(exported_package, tmp_path) -> None:
    root = _copy_package(exported_package[0], tmp_path)
    (root / "identity/00000002.json").unlink()
    _fails(root)


def test_t5_extra_identity_fails(exported_package, tmp_path) -> None:
    root = _copy_package(exported_package[0], tmp_path)
    shutil.copyfile(
        root / "identity/00000002.json", root / "identity/00000003.json"
    )
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["package_files"]["identity/00000003.json"] = _sha256(
        root / "identity/00000003.json"
    )
    _resign_manifest(manifest_path, manifest)
    _fails(root)


def test_t6_wrong_memory_order_fails(exported_package, tmp_path) -> None:
    root = _copy_package(exported_package[0], tmp_path)
    path = root / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    refs = manifest["ordered_memory_experience_refs"]
    refs[0], refs[1] = refs[1], refs[0]
    _resign_manifest(path, manifest)
    _fails(root)


def test_t7_duplicate_unexpected_ref_fails(exported_package, tmp_path) -> None:
    root = _copy_package(exported_package[0], tmp_path)
    source = _records(root, "memory_experience")[1]
    _rewrite_record(
        root,
        "memory_experience",
        0,
        {
            "canonical_ref": source["canonical_ref"],
            "version": source["version"],
            "authority_object_ref": source["authority_object_ref"],
            "serialized_payload": source["serialized_payload"],
            "payload": source["payload"],
            "payload_digest": source["payload_digest"],
            "governance": source["governance"],
            "source_provenance": source["source_provenance"],
            "admission_provenance": source["admission_provenance"],
            "lineage_metadata": source["lineage_metadata"],
        },
    )
    _fails(root)


def test_t8_non_admitted_lifecycle_fails(exported_package, tmp_path) -> None:
    root = _copy_package(exported_package[0], tmp_path)
    _rewrite_record(root, "identity", 0, {"lifecycle_status": "CANDIDATE"})
    _fails(root)


def test_t9_lineage_mismatch_fails(exported_package, tmp_path) -> None:
    root = _copy_package(exported_package[0], tmp_path)
    _rewrite_record(
        root,
        "memory_experience",
        6,
        {
            "lineage_metadata": {
                **_records(root, "memory_experience")[6]["lineage_metadata"],
                "predecessor_version_id": "v0.1-preview",
            }
        },
    )
    _fails(root)


def test_t10_missing_provenance_fails(exported_package, tmp_path) -> None:
    root = _copy_package(exported_package[0], tmp_path)
    _rewrite_record(root, "identity", 0, {"source_provenance": []})
    _fails(root)


def _records(root: Path, directory: str) -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((root / directory).glob("*.json"))
    ]


def _copy_package(source: Path, destination: Path) -> Path:
    root = destination / "authority"
    shutil.copytree(source, root)
    for path in root.rglob("*"):
        path.chmod(0o700 if path.is_dir() else 0o600)
    return root


def _fails(root: Path) -> None:
    with pytest.raises(Exception):
        FilesystemDurableAuthorityReader(root)


def _write(path: Path, value: dict) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8", newline="\n")


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resign_manifest(path: Path, manifest: dict) -> None:
    import hashlib

    manifest.pop("manifest_digest", None)
    manifest["manifest_digest"] = hashlib.sha256(
        canonical_json(manifest).encode("utf-8")
    ).hexdigest()
    _write(path, manifest)


def _rewrite_record(root: Path, directory: str, index: int, changes: dict) -> None:
    path = root / directory / f"{index:08d}.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record.update(changes)
    record["envelope_digest"] = envelope_digest(
        envelope_schema=ENVELOPE_SCHEMA_VERSION,
        authority_family=AuthorityFamily(record["record_type"]),
        authority_object_ref=record["authority_object_ref"],
        authority_object_schema=record["authority_object_schema"],
        serialized_payload=record["serialized_payload"],
        payload_digest=record["payload_digest"],
        governance_events=tuple(record["governance"]),
        lifecycle_status=record["lifecycle_status"],
        lineage_metadata=record["lineage_metadata"],
        provenance=tuple(record["source_provenance"]),
    )
    _write(path, record)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    key = f"{directory}/{index:08d}.json"
    manifest["record_digests"][key] = {
        "payload_digest": record["payload_digest"],
        "envelope_digest": record["envelope_digest"],
    }
    manifest["package_files"][key] = _sha256(path)
    _resign_manifest(manifest_path, manifest)

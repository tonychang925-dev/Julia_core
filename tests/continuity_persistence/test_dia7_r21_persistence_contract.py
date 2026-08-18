"""DIA-7 R2.1 — Runtime / Persistence continuity contract tests."""
from __future__ import annotations

import json

import pytest

from julia_core.continuity_persistence import (
    ContinuityPersistenceAudit,
    ContinuityPersistenceStore,
    ContinuityReplayGuard,
    ContinuityRuntimeSnapshot,
    PersistedContinuityBindingRecord,
    PersistedContinuityPackageRecord,
    StrictContinuityPersistenceRuntime,
)
from tests.assistant_continuity.test_dia7_r2_assistant_continuity_contract import _binding, _package

GOLDEN_PACKAGE_RECORD_DIGEST = "809ba8fa5a18ed8fae9713f2901157d1158cc0188df32946e963878b7eb808d0"
GOLDEN_BINDING_RECORD_DIGEST = "91f1215b985704c4024596e538121b7456f75ee2cc6f57a0c81f3348454d1f34"
GOLDEN_SNAPSHOT_DIGEST = "35bcc4a6bc689901084c9943d8f99b6e2a9c205ba6899a17cc841c176faec71f"


def _snapshot(session_id="session-A"):
    package = _package()
    binding = _binding(package, session_id)
    package_record = PersistedContinuityPackageRecord(session_id, package)
    binding_record = PersistedContinuityBindingRecord(session_id, binding)
    return ContinuityRuntimeSnapshot(session_id, package_record, binding_record), package, binding


# R2.1-01: storage key / serialized session / binding session are triply bound.
def test_storage_serialized_binding_session_triple_identity():
    snapshot, package, binding = _snapshot("session-A")
    assert snapshot.storage_key == "session-A"
    assert snapshot.package_record.session_id == "session-A"
    assert snapshot.binding_record.storage_key == "session-A"
    assert snapshot.binding_record.serialized_session_id == "session-A"
    with pytest.raises(ValueError, match="storage key and binding session mismatch"):
        PersistedContinuityBindingRecord("session-B", binding)


# R2.1-02: persisted records recompute their own semantic digests on deserialize.
def test_persisted_record_digest_recomputed_on_deserialize():
    snapshot, _, _ = _snapshot()
    data = snapshot.to_dict()
    data["package_record"]["package_digest"] = "0" * 64
    with pytest.raises(ValueError, match="package record digest mismatch"):
        ContinuityRuntimeSnapshot.from_dict(data)


# R2.1-03: package A + binding B are rejected even if each record is self-consistent.
def test_package_a_binding_b_cross_pair_rejected():
    package_a = _package()
    binding_a = _binding(package_a, "session-A")
    package_b = _package()
    binding_b = _binding(package_b, "session-B")
    package_record_a = PersistedContinuityPackageRecord("session-A", package_a)
    binding_record_b = PersistedContinuityBindingRecord("session-B", binding_b)
    with pytest.raises(ValueError, match="snapshot storage/session identity mismatch"):
        ContinuityRuntimeSnapshot("session-A", package_record_a, binding_record_b)


# R2.1-04: old package + new binding torn snapshot is rejected.
def test_torn_old_package_new_binding_rejected():
    snapshot, package, binding = _snapshot("session-A")
    binding_record = PersistedContinuityBindingRecord("session-A", binding)
    object.__setattr__(binding_record, "package_digest", "0" * 64)
    object.__setattr__(binding_record, "binding_record_digest", __import__("hashlib").sha256(binding_record.semantic_canonical_bytes(include_digest=False)).hexdigest())
    with pytest.raises(ValueError, match="snapshot package digest mismatch"):
        ContinuityRuntimeSnapshot("session-A", snapshot.package_record, binding_record)


# R2.1-05: write must read back; corrupted/truncated bytes fail restart.
def test_truncated_persisted_bytes_fail_closed(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    path.write_text('{"schema_version"')
    with pytest.raises(ValueError, match="persisted snapshot bytes are invalid"):
        runtime.restart("session-A")


# R2.1-06: exact duplicate write is idempotent; different binding for same session rejects.
def test_duplicate_write_idempotent_different_state_rejected(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    first = runtime.persist("session-A", package, binding)
    second = runtime.persist("session-A", package, binding)
    assert second.snapshot_digest == first.snapshot_digest
    assert second.status == "validated"
    altered_binding = _binding(package, "session-A")
    object.__setattr__(altered_binding, "package_digest", "0" * 64)
    object.__setattr__(altered_binding, "binding_digest", __import__("hashlib").sha256(altered_binding.semantic_canonical_bytes(include_digest=False)).hexdigest())
    with pytest.raises(ValueError, match="binding package digest mismatch"):
        runtime.persist("session-A", package, altered_binding)


# R2.1-07: temp files are not authoritative restart records.
def test_temp_file_not_loaded_as_authoritative(tmp_path):
    snapshot, _, _ = _snapshot("session-A")
    store = ContinuityPersistenceStore(tmp_path)
    (tmp_path / ".session-A.tmp").write_bytes(json.dumps(snapshot.to_dict()).encode("utf-8"))
    with pytest.raises(ValueError, match="no persisted continuity snapshot"):
        store.read_snapshot("session-A")


# R2.1-08: no stale backup fallback is attempted.
def test_corrupt_primary_does_not_fallback_to_backup(tmp_path):
    snapshot, _, _ = _snapshot("session-A")
    store = ContinuityPersistenceStore(tmp_path)
    (tmp_path / "session-A.snapshot.json.bak").write_bytes(json.dumps(snapshot.to_dict()).encode("utf-8"))
    (tmp_path / "session-A.snapshot.json").write_text("not-json")
    with pytest.raises(ValueError, match="persisted snapshot bytes are invalid"):
        store.read_snapshot("session-A")


# R2.1-09: replay guard cross-checks persisted snapshot against live package/binding.
def test_replay_guard_requires_snapshot_package_binding_chain():
    snapshot, package, binding = _snapshot("session-A")
    assert ContinuityReplayGuard().validate(snapshot, package, binding).binding_digest == binding.binding_digest
    object.__setattr__(binding, "package_digest", "0" * 64)
    object.__setattr__(binding, "binding_digest", __import__("hashlib").sha256(binding.semantic_canonical_bytes(include_digest=False)).hexdigest())
    with pytest.raises(ValueError, match="snapshot runtime package mismatch"):
        ContinuityReplayGuard().validate(snapshot, package, binding)


# R2.1-10: audit metadata does not alter persistence identity.
def test_persistence_audit_sidecar_does_not_change_snapshot_digest():
    snapshot, _, _ = _snapshot("session-A")
    audit_a = ContinuityPersistenceAudit("session-A", snapshot.snapshot_digest, ("A",), "2026-08-18T00:00:00Z")
    audit_b = ContinuityPersistenceAudit("session-A", snapshot.snapshot_digest, ("B",), "2026-08-18T01:00:00Z")
    assert audit_a.snapshot_digest == audit_b.snapshot_digest == snapshot.snapshot_digest


# Golden vectors freeze R2.1 record and snapshot domains.
def test_dia7_r21_golden_vectors():
    snapshot, _, _ = _snapshot("session-A")
    assert snapshot.package_record.package_record_digest == GOLDEN_PACKAGE_RECORD_DIGEST
    assert snapshot.binding_record.binding_record_digest == GOLDEN_BINDING_RECORD_DIGEST
    assert snapshot.snapshot_digest == GOLDEN_SNAPSHOT_DIGEST

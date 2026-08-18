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
from tests.assistant_continuity.test_dia7_r2_assistant_continuity_contract import _binding, _edge, _package, _projection_policy

GOLDEN_PACKAGE_RECORD_DIGEST = "5ab291eb1d6190de908b10e1a960fa58978dfb8a6d2b5c7b9eeff9a222e314b4"
GOLDEN_BINDING_RECORD_DIGEST = "91f1215b985704c4024596e538121b7456f75ee2cc6f57a0c81f3348454d1f34"
GOLDEN_SNAPSHOT_DIGEST = "0cecd8935426c04ce104645d68b4036dc55723dc0024c6c5e7dac265fcf3167b"


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
    with pytest.raises(ValueError, match="package record reconstructed package digest mismatch"):
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


# RED-RP1-A/F: cold restart restores package and binding from disk without live truth input.
def test_red_rp1_true_cold_restart_restores_runtime_without_live_objects(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    tx = runtime.persist("session-A", package, binding)
    del package
    del binding
    restarted = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")
    assert restarted.snapshot.snapshot_digest == tx.snapshot_digest
    assert restarted.package.package_digest == restarted.snapshot.package_record.package_digest
    assert restarted.binding.binding_digest == restarted.snapshot.binding_record.binding_digest


# RED-RP1-B: tampered persisted state payload with old payload SHA/digests rejects.
def test_red_rp1_payload_tamper_with_old_sha_rejected(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    data["package_record"]["continuity_state_payload"]["source_graph_revision"] = "attacker"
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    with pytest.raises(ValueError, match="payload sha mismatch"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")


# RED-RP1-C: attacker recomputes payload SHA only; record/snapshot identity still rejects.
def test_red_rp1_payload_tamper_recompute_sha_only_rejected(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    payload = data["package_record"]["continuity_state_payload"]
    payload["source_graph_revision"] = "attacker"
    data["package_record"]["continuity_state_payload_sha256"] = __import__("hashlib").sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    with pytest.raises(ValueError, match="continuity state payload digest mismatch|package record digest mismatch"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")


# RED-RP1-D: metadata A plus valid foreign state payload B is rejected.
def test_red_rp1_foreign_state_payload_under_metadata_a_rejected(tmp_path):
    package_a = _package()
    binding_a = _binding(package_a, "session-A")
    from julia_core.assistant_continuity import AssistantContinuityStatePackage
    from julia_core.continuity_projection import ContinuityClaim, ContinuityClaimKind, ContinuityEvidenceRef, ContinuityProjectionAudit, ContinuityProjectionInput, StrictContinuityProjector

    policy_b = _projection_policy()
    edge_b = _edge("operation-foreign", parent_payload=b"pf", child_payload=b"cf")
    claim_b = ContinuityClaim("claim-foreign", ContinuityClaimKind.ACTIVE_COMMITMENT, "active_commitment=foreign", (ContinuityEvidenceRef.from_lineage_edge(edge_b),))
    input_b = ContinuityProjectionInput("lineage-graph-foreign", ContinuityProjectionInput.compute_graph_digest((edge_b,)), (edge_b,), (claim_b,), policy_b.revision, policy_b.policy_fingerprint())
    audit_b = ContinuityProjectionAudit(input_b.source_graph_digest, policy_b.policy_fingerprint(), ("foreign",), "2026-08-18T00:00:00Z")
    package_b = AssistantContinuityStatePackage.from_state(StrictContinuityProjector().project(input_b, policy_b, audit_b).continuity_state)
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package_a, binding_a)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    foreign_record = PersistedContinuityPackageRecord("session-B", package_b).to_dict()
    data["package_record"]["continuity_state_payload"] = foreign_record["continuity_state_payload"]
    data["package_record"]["continuity_state_payload_sha256"] = foreign_record["continuity_state_payload_sha256"]
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    with pytest.raises(ValueError, match="package record state payload digest mismatch|continuity state payload digest mismatch"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")


# RED-RP1-E: cold-restored package/binding can directly create R2.0 response context.
def test_red_rp1_cold_replay_response_context_green(tmp_path):
    from julia_core.assistant_continuity import StrictAssistantContinuityBinder

    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    restored = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")
    context = StrictAssistantContinuityBinder().response_context(restored.binding, restored.package)
    assert context.session_id == "session-A"
    assert context.session_binding.binding_digest == restored.binding.binding_digest


def _rewrite_payload_sha(path, data):
    payload = data["package_record"]["continuity_state_payload"]
    data["package_record"]["continuity_state_payload_sha256"] = __import__("hashlib").sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))


# RED-SL1-A: supporting_lineage_digests missing derived claim evidence rejects on restart.
def test_red_sl1_missing_derived_lineage_digest_rejected(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    data["package_record"]["continuity_state_payload"]["supporting_lineage_digests"] = []
    _rewrite_payload_sha(path, data)
    with pytest.raises(ValueError, match="supporting lineage digests"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")


# RED-SL1-B: extra lineage digest not derived from any claim evidence rejects.
def test_red_sl1_extra_underrived_lineage_digest_rejected(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    data["package_record"]["continuity_state_payload"]["supporting_lineage_digests"].append("0" * 64)
    _rewrite_payload_sha(path, data)
    with pytest.raises(ValueError, match="supporting lineage digests"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")


# RED-SL1-C: claim evidence changed without matching derived lineage set rejects.
def test_red_sl1_claim_evidence_and_supporting_lineage_mismatch_rejected(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    claim = data["package_record"]["continuity_state_payload"]["active_claims"][0]
    claim["supporting_evidence_refs"][0]["lineage_digest"] = "0" * 64
    _rewrite_payload_sha(path, data)
    with pytest.raises(ValueError, match="supporting lineage digests"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")

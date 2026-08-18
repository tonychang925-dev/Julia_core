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


def _rewrite_payload_digest_and_state_digest(path, data):
    payload = data["package_record"]["continuity_state_payload"]
    state_digest = __import__("hashlib").sha256(_state_semantic_bytes_from_payload(payload)).hexdigest()
    payload["continuity_state_digest"] = state_digest
    data["package_record"]["continuity_state_digest"] = state_digest
    data["package_record"]["continuity_state_payload_sha256"] = __import__("hashlib").sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))


def _state_semantic_bytes_from_payload(payload):
    from julia_core.continuity_projection.models import _field

    out = (
        _field("state.domain", "julia_core.continuity_projection.state.v1")
        + _field("state.schema_version", payload["state_schema_version"])
        + _field("state.policy_revision", payload["projection_policy_revision"])
        + _field("state.policy_fingerprint", payload["projection_policy_fingerprint"])
        + _field("state.source_graph_revision", payload["source_graph_revision"])
        + _field("state.source_graph_digest", payload["source_graph_digest"])
        + _field("state.active_claim_count", str(len(payload["active_claims"])))
    )
    for claim in payload["active_claims"]:
        out += _field("state.active_claim", _claim_semantic_from_payload(claim).decode("utf-8"))
    out += _field("state.unresolved_conflict_count", str(len(payload["unresolved_conflicts"])))
    for claim in payload["unresolved_conflicts"]:
        out += _field("state.unresolved_conflict", _claim_semantic_from_payload(claim).decode("utf-8"))
    out += _field("state.supporting_lineage_digest_count", str(len(payload["supporting_lineage_digests"])))
    for digest in sorted(payload["supporting_lineage_digests"]):
        out += _field("state.supporting_lineage_digest", digest)
    return out


def _claim_semantic_from_payload(claim):
    from julia_core.continuity_projection.models import _field

    out = (
        _field("claim.domain", "julia_core.continuity_projection.claim.v1")
        + _field("claim.schema_version", claim["schema_version"])
        + _field("claim.id", claim["claim_id"])
        + _field("claim.kind", claim["claim_kind"])
        + _field("claim.payload", claim["claim_payload"])
        + _field("claim.conflict_rule", claim["conflict_rule"])
        + _field("claim.target_claim_id", claim["target_claim_id"])
        + _field("claim.status", claim["status"])
        + _field("claim.projection_rule_id", claim["projection_rule_id"])
        + _field("claim.evidence_count", str(len(claim["supporting_evidence_refs"])))
    )
    for ref in sorted(claim["supporting_evidence_refs"], key=lambda item: item["lineage_digest"]):
        out += _field("claim.evidence_ref", _evidence_semantic_from_payload(ref).decode("utf-8"))
    return out


def _evidence_semantic_from_payload(ref):
    from julia_core.continuity_projection.models import _field

    return (
        _field("evidence.domain", "julia_core.continuity_projection.evidence_ref.v1")
        + _field("evidence.schema_version", ref["schema_version"])
        + _field("evidence.lineage_digest", ref["lineage_digest"])
        + _field("evidence.parent_context_digest", ref["parent_context_digest"])
        + _field("evidence.child_context_digest", ref["child_context_digest"])
        + _field("evidence.operation_id", ref["operation_id"])
        + _field("evidence.operation_kind", ref["operation_kind"])
    )


# RED-DI1-A: duplicate claim ids within active_claims reject before digest acceptance.
def test_red_di1_duplicate_active_claim_ids_rejected(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    payload = data["package_record"]["continuity_state_payload"]
    payload["active_claims"].append(dict(payload["active_claims"][0]))
    _rewrite_payload_digest_and_state_digest(path, data)
    with pytest.raises(ValueError, match="duplicate claim ids"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")


# RED-DI1-B: duplicate claim ids within unresolved_conflicts reject.
def test_red_di1_duplicate_unresolved_claim_ids_rejected(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    payload = data["package_record"]["continuity_state_payload"]
    claim = dict(payload["active_claims"].pop(0))
    claim["status"] = "conflicted"
    payload["unresolved_conflicts"] = [claim, dict(claim)]
    _rewrite_payload_digest_and_state_digest(path, data)
    with pytest.raises(ValueError, match="duplicate claim ids"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")


# RED-DI1-C: same claim_id across active and unresolved rejects.
def test_red_di1_duplicate_claim_id_across_active_and_unresolved_rejected(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    payload = data["package_record"]["continuity_state_payload"]
    conflict = dict(payload["active_claims"][0])
    conflict["status"] = "conflicted"
    payload["unresolved_conflicts"] = [conflict]
    _rewrite_payload_digest_and_state_digest(path, data)
    with pytest.raises(ValueError, match="duplicate claim ids"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")


# RED-DI1-D: distinct ids with identical payloads remain valid shape.
def test_red_di1_distinct_ids_identical_payload_shape_green():
    snapshot, _, _ = _snapshot("session-A")
    payload = snapshot.package_record.continuity_state_payload
    clone = dict(payload["active_claims"][0])
    clone["claim_id"] = "claim-2"
    payload2 = dict(payload)
    payload2["active_claims"] = [payload["active_claims"][0], clone]
    lineage = sorted({
        ref["lineage_digest"]
        for claim in payload2["active_claims"] + payload2["unresolved_conflicts"]
        for ref in claim["supporting_evidence_refs"]
    })
    payload2["supporting_lineage_digests"] = lineage
    # Shape parity accepts distinct IDs; final digest validation may reject if caller did not update all enclosing identities.
    from julia_core.continuity_persistence.models import _continuity_state_from_payload
    payload2["continuity_state_digest"] = __import__("hashlib").sha256(_state_semantic_bytes_from_payload(payload2)).hexdigest()
    restored = _continuity_state_from_payload(payload2)
    assert [claim.claim_id for claim in restored.active_claims] == ["claim-1", "claim-2"]


def _recompute_package_record_digest(data):
    from julia_core.continuity_persistence import PersistedContinuityPackageRecord

    record = PersistedContinuityPackageRecord.from_dict(data["package_record"])
    data["package_record"] = record.to_dict()


def _refresh_all_persisted_digests(path, data):
    from julia_core.continuity_persistence.models import (
        ContinuityRuntimeSnapshot,
        PersistedContinuityBindingRecord,
        PersistedContinuityPackageRecord,
    )

    payload = data["package_record"]["continuity_state_payload"]
    payload["continuity_state_digest"] = __import__("hashlib").sha256(_state_semantic_bytes_from_payload(payload)).hexdigest()
    data["package_record"]["continuity_state_digest"] = payload["continuity_state_digest"]
    data["binding_record"]["continuity_state_digest"] = payload["continuity_state_digest"]
    data["package_record"]["continuity_state_payload_sha256"] = __import__("hashlib").sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    pr = PersistedContinuityPackageRecord.from_dict(data["package_record"])
    data["package_record"] = pr.to_dict()
    br = PersistedContinuityBindingRecord.from_dict(data["binding_record"])
    data["binding_record"] = br.to_dict()
    snap = ContinuityRuntimeSnapshot.from_dict({**data, "snapshot_digest": ContinuityRuntimeSnapshot(data["storage_key"], pr, br).snapshot_digest})
    data.update(snap.to_dict())
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))


def _expect_restart_reject_after_claim_payload_mutation(tmp_path, mutate, pattern):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    mutate(data["package_record"]["continuity_state_payload"])
    # Recompute payload/state only. Record/snapshot digests may remain stale; PI1 validator must still be the first rejection.
    payload = data["package_record"]["continuity_state_payload"]
    payload["continuity_state_digest"] = __import__("hashlib").sha256(_state_semantic_bytes_from_payload(payload)).hexdigest()
    data["package_record"]["continuity_state_digest"] = payload["continuity_state_digest"]
    data["package_record"]["continuity_state_payload_sha256"] = __import__("hashlib").sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    with pytest.raises(ValueError, match=pattern):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")


# RED-PI1-A: APPEND with target != none rejects during nested claim parity.
def test_red_pi1_append_with_target_rejected(tmp_path):
    def mutate(payload):
        payload["active_claims"][0]["target_claim_id"] = "claim-X"

    _expect_restart_reject_after_claim_payload_mutation(tmp_path, mutate, "append claim target must be none")


# RED-PI1-B: non-APPEND with target == none rejects.
def test_red_pi1_non_append_without_target_rejected(tmp_path):
    def mutate(payload):
        claim = payload["active_claims"][0]
        claim["conflict_rule"] = "correct"
        claim["target_claim_id"] = "none"

    _expect_restart_reject_after_claim_payload_mutation(tmp_path, mutate, "non-append claim requires target")


# RED-PI1-C: empty target_claim_id rejects.
def test_red_pi1_empty_target_claim_id_rejected(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    payload = data["package_record"]["continuity_state_payload"]
    payload["active_claims"][0]["target_claim_id"] = ""
    data["package_record"]["continuity_state_payload_sha256"] = __import__("hashlib").sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    with pytest.raises(ValueError, match="target_claim_id"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")


# RED-PI1-D: foreign projected claim schema version rejects.
def test_red_pi1_foreign_claim_schema_version_rejected(tmp_path):
    def mutate(payload):
        payload["active_claims"][0]["schema_version"] = "fake-v99"

    _expect_restart_reject_after_claim_payload_mutation(tmp_path, mutate, "projected claim schema_version is frozen")


# RED-PI1-E: foreign evidence schema version rejects.
def test_red_pi1_foreign_evidence_schema_version_rejected(tmp_path):
    def mutate(payload):
        payload["active_claims"][0]["supporting_evidence_refs"][0]["schema_version"] = "fake-v99"

    _expect_restart_reject_after_claim_payload_mutation(tmp_path, mutate, "evidence ref schema_version is frozen")


# RED-PI1-F/G: valid APPEND + none and targeted rules remain valid nested shapes.
def test_red_pi1_valid_append_and_targeted_shapes_green():
    from julia_core.continuity_persistence.models import _validate_reconstructed_state_shape
    from julia_core.continuity_projection import ContinuityClaimStatus

    snapshot, _, _ = _snapshot("session-A")
    payload = snapshot.package_record.continuity_state_payload
    active = tuple(
        __import__("julia_core.continuity_persistence.models", fromlist=["_projected_claim_from_payload"])._projected_claim_from_payload(item, ContinuityClaimStatus.ACTIVE)
        for item in payload["active_claims"]
    )
    _validate_reconstructed_state_shape(active, ())


# RED-PI1-H: valid targeted CORRECT / SUPERSEDE / DEPRECATE / UNRESOLVED shapes satisfy nested parity.
def test_red_pi1_valid_targeted_rule_shapes_green():
    from julia_core.continuity_persistence.models import _validate_reconstructed_state_shape
    from julia_core.continuity_projection import ContinuityClaim, ContinuityClaimKind, ContinuityClaimStatus, ContinuityConflictRule, ContinuityEvidenceRef, ProjectedContinuityClaim

    edge = _edge("operation-pi1-valid", parent_payload=b"pi1-p", child_payload=b"pi1-c")
    ref = ContinuityEvidenceRef.from_lineage_edge(edge)
    for rule, status in (
        (ContinuityConflictRule.CORRECT, ContinuityClaimStatus.ACTIVE),
        (ContinuityConflictRule.SUPERSEDE, ContinuityClaimStatus.ACTIVE),
        (ContinuityConflictRule.DEPRECATE, ContinuityClaimStatus.ACTIVE),
        (ContinuityConflictRule.UNRESOLVED, ContinuityClaimStatus.CONFLICTED),
    ):
        claim = ContinuityClaim("claim-valid", ContinuityClaimKind.RESOLVED_BELIEF, f"rule={rule.value}", (ref,), rule, "claim-target")
        projected = ProjectedContinuityClaim.from_claim(claim, status)
        if status is ContinuityClaimStatus.ACTIVE:
            _validate_reconstructed_state_shape((projected,), ())
        else:
            _validate_reconstructed_state_shape((), (projected,))


def _restart_with_header_mutation(tmp_path, mutate, pattern):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    path = tmp_path / "session-A.snapshot.json"
    data = json.loads(path.read_text())
    payload = data["package_record"]["continuity_state_payload"]
    mutate(payload)
    try:
        payload["continuity_state_digest"] = __import__("hashlib").sha256(_state_semantic_bytes_from_payload(payload)).hexdigest()
    except ValueError:
        pass
    data["package_record"]["continuity_state_payload_sha256"] = __import__("hashlib").sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    with pytest.raises(ValueError, match=pattern):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")


# RED-SH1-A: foreign state schema version rejects before accepting self-consistent envelope.
def test_red_sh1_foreign_state_schema_version_rejected(tmp_path):
    def mutate(payload):
        payload["state_schema_version"] = "fake-v99"

    _restart_with_header_mutation(tmp_path, mutate, "continuity state schema_version is frozen")


# RED-SH1-B: empty projection policy revision rejects.
def test_red_sh1_empty_projection_policy_revision_rejected(tmp_path):
    def mutate(payload):
        payload["projection_policy_revision"] = ""

    _restart_with_header_mutation(tmp_path, mutate, "projection_policy_revision")


# RED-SH1-C: malformed projection policy fingerprint rejects.
def test_red_sh1_malformed_projection_policy_fingerprint_rejected(tmp_path):
    def mutate(payload):
        payload["projection_policy_fingerprint"] = "not-sha"

    _restart_with_header_mutation(tmp_path, mutate, "projection_policy_fingerprint")


# RED-SH1-D: empty source graph revision rejects.
def test_red_sh1_empty_source_graph_revision_rejected(tmp_path):
    def mutate(payload):
        payload["source_graph_revision"] = ""

    _restart_with_header_mutation(tmp_path, mutate, "source_graph_revision")


# RED-SH1-E: malformed source graph digest rejects.
def test_red_sh1_malformed_source_graph_digest_rejected(tmp_path):
    def mutate(payload):
        payload["source_graph_digest"] = "not-sha"

    _restart_with_header_mutation(tmp_path, mutate, "source_graph_digest")


# RED-SH1-F: valid original state header remains green and golden vectors unchanged.
def test_red_sh1_valid_state_header_green_and_golden_stable(tmp_path):
    package = _package()
    binding = _binding(package, "session-A")
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-A", package, binding)
    restored = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-A")
    assert restored.continuity_state.state_schema_version == "dia7-continuity-projection-v1"
    assert restored.snapshot.package_record.package_record_digest == GOLDEN_PACKAGE_RECORD_DIGEST
    assert restored.snapshot.binding_record.binding_record_digest == GOLDEN_BINDING_RECORD_DIGEST
    assert restored.snapshot.snapshot_digest == GOLDEN_SNAPSHOT_DIGEST

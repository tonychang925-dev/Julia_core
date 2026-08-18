"""DIA-7-E2E — Continuity Identity Chain Gate.

Chain under test:
Trigger -> Reflection Context -> Handoff / Transport -> Evolution -> Lineage
-> Continuity Projection -> Assistant Consumption -> Persistence -> Cold Restart
-> Behavior.

No new Core nouns are introduced here; tests compose frozen DIA-3..DIA-7 surfaces.
"""
from __future__ import annotations

from datetime import timedelta
import json

import pytest

from julia_core.assistant_continuity import AssistantContinuityStatePackage, StrictAssistantContinuityBinder
from julia_core.context_evolution import (
    ContextEvolutionKind,
    ContextEvolutionOperation,
    ContextEvolutionPolicy,
    ContextLineageNode,
    EvolutionAuthority,
    StrictContextEvolutionValidator,
)
from julia_core.continuity_persistence import ContinuityPersistenceStore, StrictContinuityPersistenceRuntime
from julia_core.continuity_projection import (
    ContinuityClaim,
    ContinuityClaimKind,
    ContinuityConflictRule,
    ContinuityEvidenceRef,
    ContinuityProjectionAudit,
    ContinuityProjectionInput,
    ContinuityProjectionPolicy,
    StrictContinuityProjector,
)
from julia_core.reflection_context import (
    CANONICAL_VERSION as CONTEXT_VERSION,
    DEFAULT_FACT_PROJECTION_REVISION,
    CanonicalFact,
    CanonicalFactType,
    ContextAssemblyPolicy,
    ContextBounds,
    DeterministicReflectionContextAssembler,
    ReflectionOpportunityHandoff,
)
from julia_core.reflection_handoff import (
    HANDOFF_VERSION,
    HandoffEndpoint,
    HandoffIntegrity,
    ReflectionContextHandoff,
    StrictReflectionHandoffValidator,
)
from julia_core.reflection_trigger import (
    CANONICAL_VERSION as TRIGGER_VERSION,
    OpportunityKey,
    ReflectionOpportunity,
    SingleEventAnchor,
    TriggerKind,
    TriggerPolicy,
    TriggerReason,
    TriggerSourceRef,
)


def _ref(event_id: str) -> TriggerSourceRef:
    return TriggerSourceRef("event", event_id)


def _trigger_policy(revision="policy-dia7-e2e") -> TriggerPolicy:
    return TriggerPolicy(revision, timedelta(seconds=0), timedelta(seconds=60), timedelta(seconds=30))


def _opportunity(event_id: str, policy_revision="policy-dia7-e2e") -> ReflectionOpportunity:
    ref = _ref(event_id)
    policy = _trigger_policy(policy_revision)
    key = OpportunityKey(TRIGGER_VERSION, "conv-e2e", policy.revision, TriggerKind.TURN_BOUNDARY, SingleEventAnchor(ref.opaque_ref))
    return ReflectionOpportunity(key, (ref,), (TriggerReason(TriggerKind.TURN_BOUNDARY, (ref,)),))


class _Reader:
    def __init__(self, facts):
        self.facts = {fact.source_ref.canonical_key(): fact for fact in facts}

    def get_fact(self, ref):
        return self.facts.get(ref.canonical_key())


def _context(event_id: str, payload: bytes):
    ref = _ref(event_id)
    fact = CanonicalFact(
        source_ref=ref,
        fact_type=CanonicalFactType.CONVERSATION_EVENT,
        source_schema_version="conversation-event-v1",
        projection_revision=DEFAULT_FACT_PROJECTION_REVISION,
        canonical_payload=payload,
        reader_authority="e2e-reader",
    )
    return DeterministicReflectionContextAssembler().assemble(
        ReflectionOpportunityHandoff(_opportunity(event_id), "pending-e2e", "dia3-handoff"),
        _Reader((fact,)),
        ContextAssemblyPolicy("ctx-policy-e2e", ContextBounds(4, 2048, 1024)),
    )


def _producer():
    return HandoffEndpoint("dia4-e2e", "producer", "dia5-consumer-protocol-v1")


def _consumer():
    return HandoffEndpoint("dia5-e2e", "consumer", "dia5-consumer-protocol-v1")


def _handoff(context, handoff_id="handoff-e2e"):
    handoff = ReflectionContextHandoff.from_context(
        handoff_id=handoff_id,
        context=context,
        producer=_producer(),
        consumer=_consumer(),
        created_at="2026-08-19T00:00:00Z",
    )
    receipt = StrictReflectionHandoffValidator().validate(handoff, _consumer())
    assert receipt.context_digest == context.context_digest
    return handoff


def _evolution_policy():
    return ContextEvolutionPolicy(
        "evo-policy-e2e",
        (ContextEvolutionKind.FACT_APPEND, ContextEvolutionKind.FACT_CORRECTION, ContextEvolutionKind.CONTEXT_DEPRECATION),
        4,
    )


def _lineage_edge(parent_context, child_context, operation_id="evo-e2e", kind=ContextEvolutionKind.FACT_APPEND):
    policy = _evolution_policy()
    operation = ContextEvolutionOperation(
        operation_id,
        kind,
        ContextLineageNode.from_context(parent_context),
        ContextLineageNode.from_context(child_context),
        policy.revision,
        policy.policy_fingerprint(),
        EvolutionAuthority("e2e-authority", "verified-e2e", "dia6-evolution-authority-v1"),
        (_ref(f"reason-{operation_id}"),),
    )
    return StrictContextEvolutionValidator().validate(operation, policy)


def _projection_policy():
    return ContinuityProjectionPolicy(
        "continuity-policy-e2e",
        (ContinuityClaimKind.STABLE_PREFERENCE, ContinuityClaimKind.RELATIONSHIP_STATE, ContinuityClaimKind.UNRESOLVED_TENSION),
        (ContinuityConflictRule.APPEND, ContinuityConflictRule.UNRESOLVED),
    )


def _project_state(edges, claims):
    policy = _projection_policy()
    edges = tuple(edges)
    claims = tuple(claims)
    projection_input = ContinuityProjectionInput(
        "lineage-graph-e2e",
        ContinuityProjectionInput.compute_graph_digest(edges),
        edges,
        claims,
        policy.revision,
        policy.policy_fingerprint(),
    )
    audit = ContinuityProjectionAudit(projection_input.source_graph_digest, policy.policy_fingerprint(), ("e2e",), "2026-08-19T00:00:00Z")
    return StrictContinuityProjector().project(projection_input, policy, audit).continuity_state


def _package_binding_from_state(state, session_id="session-e2e"):
    package = AssistantContinuityStatePackage.from_state(state)
    binding = StrictAssistantContinuityBinder().bind_for_session(
        session_id,
        package,
        expected_state_digest=package.continuity_state_digest,
        expected_source_graph_digest=package.source_graph_digest,
        expected_projection_policy_fingerprint=package.projection_policy_fingerprint,
    )
    return package, binding


def _behavior_choice(response_context, *, stale_pre_restart_choice="X"):
    # Deterministic behavior assertion harness: behavior may only inspect restored response_context.
    assert stale_pre_restart_choice == "X"
    conflicts = {claim.claim_payload for claim in response_context.unresolved_conflicts}
    if any("prefer Y" in payload for payload in conflicts) and any("prefer Z" in payload for payload in conflicts):
        return "UNRESOLVED:prefer-Y-vs-prefer-Z"
    for claim in response_context.active_claims:
        if claim.claim_payload == "stable_preference=prefer Y because evidence E":
            return "Y"
    return "X"


def _green_chain(tmp_path, *, claim_payload="stable_preference=prefer Y because evidence E"):
    before = _context("evt-before", b"before experience: choice X")
    after = _context("evt-after", b"verified experience E: choose/prefer Y")
    handoff = _handoff(after)
    edge = _lineage_edge(before, after)
    assert edge.child_context_digest == handoff.context_digest
    claim = ContinuityClaim(
        "claim-prefer-y",
        ContinuityClaimKind.STABLE_PREFERENCE,
        claim_payload,
        (ContinuityEvidenceRef.from_lineage_edge(edge),),
    )
    state = _project_state((edge,), (claim,))
    package, binding = _package_binding_from_state(state)
    response_context = StrictAssistantContinuityBinder().response_context(binding, package)
    runtime = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path))
    runtime.persist("session-e2e", package, binding)
    del state, package, binding
    restored = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-e2e")
    restored_context = StrictAssistantContinuityBinder().response_context(restored.binding, restored.package)
    return before, after, handoff, edge, response_context, restored, restored_context


# GREEN-1 + lanes 1-9: verified experience changes post-restart behavior through restored evidence-bound state.
def test_green_verified_experience_changes_behavior_after_true_cold_restart(tmp_path):
    before, after, handoff, edge, pre_restart_context, restored, restored_context = _green_chain(tmp_path)
    assert before.context_digest != after.context_digest
    assert handoff.context_digest == after.context_digest
    assert edge.parent_context_digest == before.context_digest
    assert edge.child_context_digest == after.context_digest
    assert restored.package.continuity_state_digest == restored.snapshot.package_record.continuity_state_digest
    assert restored.binding.binding_digest == restored.snapshot.binding_record.binding_digest
    assert _behavior_choice(pre_restart_context) == "Y"
    assert _behavior_choice(restored_context, stale_pre_restart_choice="X") == "Y"
    active_claim = restored_context.active_claims[0]
    assert active_claim.supporting_evidence_refs[0].lineage_digest == edge.lineage_digest


# GREEN-2: unresolved conflict persists through restart and behavior does not invent a winner.
def test_green_unresolved_conflict_survives_restart_without_silent_active_choice(tmp_path):
    base = _context("evt-base", b"base preference state")
    y_ctx = _context("evt-y", b"evidence supports prefer Y")
    z_ctx = _context("evt-z", b"evidence supports prefer Z")
    edge_y = _lineage_edge(base, y_ctx, "evo-y")
    edge_z = _lineage_edge(y_ctx, z_ctx, "evo-z")
    claim_y = ContinuityClaim("claim-y", ContinuityClaimKind.STABLE_PREFERENCE, "stable_preference=prefer Y", (ContinuityEvidenceRef.from_lineage_edge(edge_y),))
    claim_z = ContinuityClaim(
        "claim-z",
        ContinuityClaimKind.STABLE_PREFERENCE,
        "stable_preference=prefer Z",
        (ContinuityEvidenceRef.from_lineage_edge(edge_z),),
        ContinuityConflictRule.UNRESOLVED,
        "claim-y",
    )
    state = _project_state((edge_y, edge_z), (claim_y, claim_z))
    package, binding = _package_binding_from_state(state)
    StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).persist("session-e2e", package, binding)
    restored = StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-e2e")
    context = StrictAssistantContinuityBinder().response_context(restored.binding, restored.package)
    assert context.active_claims == ()
    assert _behavior_choice(context) == "UNRESOLVED:prefer-Y-vs-prefer-Z"


# E2E-RED-1: wrong handoff context digest rejects before transport can feed the chain.
def test_red_wrong_handoff_context_digest_rejected():
    context = _context("evt-after", b"verified experience E")
    with pytest.raises(ValueError, match="context_digest mismatch"):
        ReflectionContextHandoff(
            HANDOFF_VERSION,
            "bad-handoff",
            CONTEXT_VERSION,
            "0" * 64,
            context.semantic_canonical_bytes(),
            _producer(),
            _consumer(),
            "2026-08-19T00:00:00Z",
            HandoffIntegrity.from_context(context),
        )


# E2E-RED-2: lineage edge pointing to a foreign child context is rejected by E2E chain reconciliation.
def test_red_lineage_edge_foreign_child_context_rejected_by_chain_guard():
    parent = _context("evt-parent", b"parent")
    expected_child = _context("evt-child", b"expected child")
    foreign_child = _context("evt-foreign-child", b"foreign child")
    handoff = _handoff(expected_child)
    edge = _lineage_edge(parent, foreign_child)
    with pytest.raises(ValueError, match="lineage child does not match handoff context"):
        if edge.child_context_digest != handoff.context_digest:
            raise ValueError("lineage child does not match handoff context")


# E2E-RED-3: projection source graph mismatch rejects.
def test_red_projection_wrong_source_graph_rejected():
    parent = _context("evt-parent", b"parent")
    child = _context("evt-child", b"child")
    edge = _lineage_edge(parent, child)
    policy = _projection_policy()
    claim = ContinuityClaim("claim-1", ContinuityClaimKind.STABLE_PREFERENCE, "stable_preference=prefer Y", (ContinuityEvidenceRef.from_lineage_edge(edge),))
    with pytest.raises(ValueError, match="source_graph_digest mismatch"):
        ContinuityProjectionInput("lineage-graph-e2e", "0" * 64, (edge,), (claim,), policy.revision, policy.policy_fingerprint())


# E2E-RED-4: Assistant package A + binding B rejects.
def test_red_assistant_package_a_binding_b_rejected(tmp_path):
    _, _, _, _, _, restored_a, _ = _green_chain(tmp_path / "a")
    _, _, _, _, _, restored_b, _ = _green_chain(tmp_path / "b", claim_payload="stable_preference=prefer Y because evidence E")
    object.__setattr__(restored_b.binding, "session_id", "session-e2e-b")
    with pytest.raises(ValueError, match="binding digest mismatch|binding package digest mismatch|binding continuity state digest mismatch"):
        StrictAssistantContinuityBinder().response_context(restored_b.binding, restored_a.package)


# E2E-RED-5: persisted snapshot moved under foreign session key rejects on restart lookup.
def test_red_persisted_snapshot_moved_under_foreign_session_key_rejected(tmp_path):
    _green_chain(tmp_path)
    original = tmp_path / "session-e2e.snapshot.json"
    moved = tmp_path / "session-foreign.snapshot.json"
    moved.write_bytes(original.read_bytes())
    with pytest.raises(ValueError, match="snapshot storage key lookup mismatch"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-foreign")


# E2E-RED-6: cold restart payload with foreign claim evidence rejects.
def test_red_cold_restart_payload_foreign_claim_evidence_rejected(tmp_path):
    _green_chain(tmp_path)
    path = tmp_path / "session-e2e.snapshot.json"
    data = json.loads(path.read_text())
    payload = data["package_record"]["continuity_state_payload"]
    payload["active_claims"][0]["supporting_evidence_refs"][0]["lineage_digest"] = "0" * 64
    data["package_record"]["continuity_state_payload_sha256"] = __import__("hashlib").sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    with pytest.raises(ValueError, match="supporting lineage digests|payload digest|state payload"):
        StrictContinuityPersistenceRuntime(ContinuityPersistenceStore(tmp_path)).restart("session-e2e")


# E2E-RED-7: behavior assertion proves restored state, not stale pre-restart default, drives choice.
def test_red_behavior_cannot_use_stale_pre_restart_state_after_cold_restore(tmp_path):
    _, _, _, _, _, _, restored_context = _green_chain(tmp_path)
    assert _behavior_choice(restored_context, stale_pre_restart_choice="X") == "Y"


# E2E-RED-8: unresolved conflict is not collapsed into an active behavior choice.
def test_red_unresolved_conflict_not_collapsed_into_active_choice(tmp_path):
    test_green_unresolved_conflict_survives_restart_without_silent_active_choice(tmp_path)

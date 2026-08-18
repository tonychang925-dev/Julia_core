"""DIA-7 R1 — Core Continuity Projection Contract tests."""
from __future__ import annotations

from datetime import timedelta

import pytest

from julia_core.context_evolution import (
    ContextEvolutionKind,
    ContextEvolutionOperation,
    ContextEvolutionPolicy,
    ContextLineageEdge,
    ContextLineageNode,
    EvolutionAuthority,
    StrictContextEvolutionValidator,
)
from julia_core.continuity_projection import (
    ContinuityAnchor,
    ContinuityClaim,
    ContinuityClaimKind,
    ContinuityClaimStatus,
    ContinuityConflictRule,
    ContinuityEvidenceRef,
    ContinuityProjectionAudit,
    ContinuityProjectionInput,
    ContinuityProjectionPolicy,
    ProjectedContinuityClaim,
    StrictContinuityProjector,
)
from julia_core.reflection_context import (
    DEFAULT_FACT_PROJECTION_REVISION,
    CanonicalFact,
    CanonicalFactType,
    ContextAssemblyPolicy,
    ContextBounds,
    DeterministicReflectionContextAssembler,
    ReflectionOpportunityHandoff,
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

GOLDEN_POLICY_FINGERPRINT = "c6de6271984cb27d6e99e04a575527c070e5ab6563d47facebd5f6f24a95f23f"
GOLDEN_STATE_DIGEST = "333f34fa51be0e0c095b024411193218c69e6c4990ef50de09f7b596a378423e"


def _trigger_policy():
    return TriggerPolicy("policy-dia7", timedelta(seconds=0), timedelta(seconds=60), timedelta(seconds=30))


def _ref(event_id="evt_A"):
    return TriggerSourceRef("event", event_id)


def _opportunity(ref=None):
    ref = ref or _ref("evt_A")
    key = OpportunityKey(TRIGGER_VERSION, "conv_A", _trigger_policy().revision, TriggerKind.TURN_BOUNDARY, SingleEventAnchor(ref.opaque_ref))
    return ReflectionOpportunity(key, (ref,), (TriggerReason(TriggerKind.TURN_BOUNDARY, (ref,)),))


def _fact(ref=None, payload=b"parent payload"):
    ref = ref or _ref("evt_A")
    return CanonicalFact(
        source_ref=ref,
        fact_type=CanonicalFactType.CONVERSATION_EVENT,
        source_schema_version="conversation-event-v1",
        projection_revision=DEFAULT_FACT_PROJECTION_REVISION,
        canonical_payload=payload,
    )


class _Reader:
    def __init__(self, facts):
        self.facts = {fact.source_ref.canonical_key(): fact for fact in facts}

    def get_fact(self, ref):
        return self.facts.get(ref.canonical_key())


def _assembly_policy(revision="ctx-policy-dia7"):
    return ContextAssemblyPolicy(revision, ContextBounds(4, 1024, 512))


def _context(payload=b"payload"):
    ref = _ref("evt_A")
    opportunity = _opportunity(ref)
    return DeterministicReflectionContextAssembler().assemble(
        ReflectionOpportunityHandoff(opportunity, "pending-digest-dia7", "dia3-handoff"),
        _Reader((_fact(ref, payload),)),
        _assembly_policy(),
    )


def _evo_policy(*, allowed=(ContextEvolutionKind.FACT_APPEND, ContextEvolutionKind.FACT_CORRECTION, ContextEvolutionKind.CONTEXT_DEPRECATION), revision="evo-policy-dia7"):
    return ContextEvolutionPolicy(revision, tuple(allowed), 4)


def _authority():
    return EvolutionAuthority("dia7-core-test", "trusted-evolution-input", "dia6-evolution-authority-v1")


def _edge(operation_id="operation-1", kind=ContextEvolutionKind.FACT_APPEND, *, parent_payload=b"parent", child_payload=b"child"):
    policy = _evo_policy(allowed=(kind,)) if kind not in _evo_policy().allowed_kinds else _evo_policy()
    parent = ContextLineageNode.from_context(_context(parent_payload))
    child = ContextLineageNode.from_context(_context(child_payload))
    op = ContextEvolutionOperation(
        operation_id,
        kind,
        parent,
        child,
        policy.revision,
        policy.policy_fingerprint(),
        _authority(),
        (_ref(f"evt_reason_{operation_id}"),),
    )
    return StrictContextEvolutionValidator().validate(op, policy)


def _projection_policy(*, min_evidence_refs=1, revision="continuity-policy-v1"):
    return ContinuityProjectionPolicy(
        revision,
        (
            ContinuityClaimKind.IDENTITY_ANCHOR,
            ContinuityClaimKind.STABLE_PREFERENCE,
            ContinuityClaimKind.RELATIONSHIP_STATE,
            ContinuityClaimKind.ACTIVE_COMMITMENT,
            ContinuityClaimKind.RESOLVED_BELIEF,
            ContinuityClaimKind.UNRESOLVED_TENSION,
            ContinuityClaimKind.LONG_TERM_TRAIT,
        ),
        (
            ContinuityConflictRule.APPEND,
            ContinuityConflictRule.SUPERSEDE,
            ContinuityConflictRule.CORRECT,
            ContinuityConflictRule.DEPRECATE,
            ContinuityConflictRule.UNRESOLVED,
        ),
        min_evidence_refs=min_evidence_refs,
    )


def _input(edges, claims, policy=None, graph_revision="lineage-graph-r1"):
    policy = policy or _projection_policy()
    edges = tuple(sorted(edges, key=lambda edge: edge.lineage_digest))
    claims = tuple(sorted(claims, key=lambda claim: claim.claim_id))
    return ContinuityProjectionInput(
        graph_revision,
        ContinuityProjectionInput.compute_graph_digest(edges),
        edges,
        claims,
        policy.revision,
        policy.policy_fingerprint(),
    )


def _audit(inp, policy, created_at="2026-08-18T00:00:00Z", diagnostics=("projected",)):
    return ContinuityProjectionAudit(inp.source_graph_digest, policy.policy_fingerprint(), diagnostics, created_at)


def _claim(claim_id, payload, edge, *, kind=ContinuityClaimKind.RELATIONSHIP_STATE, rule=ContinuityConflictRule.APPEND, target="none"):
    return ContinuityClaim(claim_id, kind, payload, (ContinuityEvidenceRef.from_lineage_edge(edge),), rule, target)


def _project(inp, policy, audit=None):
    audit = audit or _audit(inp, policy)
    return StrictContinuityProjector().project(inp, policy, audit)


# AT-DIA7-R1-01: same lineage + same policy gives identical state digest.
def test_same_lineage_same_policy_is_deterministic():
    policy = _projection_policy()
    edge = _edge("operation-1", parent_payload=b"p1", child_payload=b"c1")
    claim = _claim("claim-1", "relationship_state=trusted_partner", edge)
    inp_a = _input((edge,), (claim,), policy)
    inp_b = _input((edge,), (claim,), policy)
    result_a = _project(inp_a, policy)
    result_b = _project(inp_b, policy, _audit(inp_b, policy, created_at="2026-08-18T00:01:00Z", diagnostics=("different audit",)))
    assert result_a.continuity_state_digest == result_b.continuity_state_digest
    assert result_a.continuity_state.semantic_canonical_bytes() == result_b.continuity_state.semantic_canonical_bytes()


# AT-DIA7-R1-02: caller order is canonicalized; it does not define projection semantics.
def test_lineage_and_claim_order_canonicalized_not_semantic():
    edge_a = _edge("operation-a", parent_payload=b"pa", child_payload=b"ca")
    edge_b = _edge("operation-b", parent_payload=b"pb", child_payload=b"cb")
    policy = _projection_policy()
    claim_a = _claim("claim-a", "identity_anchor=Julia", edge_a, kind=ContinuityClaimKind.IDENTITY_ANCHOR)
    claim_b = _claim("claim-b", "active_commitment=continue", edge_b, kind=ContinuityClaimKind.ACTIVE_COMMITMENT)
    edges_ab = (edge_a, edge_b)
    edges_ba = (edge_b, edge_a)
    claims_ab = (claim_a, claim_b)
    claims_ba = (claim_b, claim_a)
    inp_a = ContinuityProjectionInput("graph-r1", ContinuityProjectionInput.compute_graph_digest(edges_ab), edges_ab, claims_ab, policy.revision, policy.policy_fingerprint())
    inp_b = ContinuityProjectionInput("graph-r1", ContinuityProjectionInput.compute_graph_digest(edges_ba), edges_ba, claims_ba, policy.revision, policy.policy_fingerprint())
    result_a = _project(inp_a, policy)
    result_b = _project(inp_b, policy)
    assert result_a.continuity_state_digest == result_b.continuity_state_digest


# AT-DIA7-R1-03: unsupported claim without lineage evidence is rejected.
def test_claim_without_evidence_rejected():
    with pytest.raises(ValueError, match="supporting_evidence_refs"):
        ContinuityClaim("claim-1", ContinuityClaimKind.RELATIONSHIP_STATE, "relationship_state=trusted_partner", ())


# AT-DIA7-R1-04: evidence must point to a lineage edge present in the projection graph.
def test_missing_lineage_evidence_rejected():
    policy = _projection_policy()
    edge_in_graph = _edge("operation-in", parent_payload=b"p-in", child_payload=b"c-in")
    edge_missing = _edge("operation-missing", parent_payload=b"p-missing", child_payload=b"c-missing")
    claim = _claim("claim-1", "relationship_state=trusted_partner", edge_missing)
    with pytest.raises(ValueError, match="missing lineage"):
        _input((edge_in_graph,), (claim,), policy)


# AT-DIA7-R1-05: deprecated claim is no longer active.
def test_deprecated_claim_not_active():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_b = _edge("operation-b", kind=ContextEvolutionKind.CONTEXT_DEPRECATION, parent_payload=b"p-b", child_payload=b"c-b")
    claim_a = _claim("claim-1", "stable_preference=A", edge_a, kind=ContinuityClaimKind.STABLE_PREFERENCE)
    claim_b = _claim("claim-2", "deprecate stable_preference=A", edge_b, kind=ContinuityClaimKind.STABLE_PREFERENCE, rule=ContinuityConflictRule.DEPRECATE, target="claim-1")
    result = _project(_input((edge_a, edge_b), (claim_a, claim_b), policy), policy)
    assert [claim.claim_id for claim in result.continuity_state.active_claims] == []


# AT-DIA7-R1-06: correction replaces old active claim.
def test_correction_replaces_old_claim():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_b = _edge("operation-b", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-b", child_payload=b"c-b")
    claim_a = _claim("claim-1", "resolved_belief=A", edge_a, kind=ContinuityClaimKind.RESOLVED_BELIEF)
    claim_b = _claim("claim-2", "resolved_belief=B", edge_b, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="claim-1")
    result = _project(_input((edge_a, edge_b), (claim_a, claim_b), policy), policy)
    assert [claim.claim_id for claim in result.continuity_state.active_claims] == ["claim-2"]
    assert result.continuity_state.active_claims[0].claim_payload == "resolved_belief=B"


# AT-DIA7-R1-07: unresolved conflict is represented, not silently resolved.
def test_unresolved_conflict_not_silently_chosen():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_b = _edge("operation-b", parent_payload=b"p-b", child_payload=b"c-b")
    claim_a = _claim("claim-1", "stable_preference=A", edge_a, kind=ContinuityClaimKind.STABLE_PREFERENCE)
    claim_b = _claim("claim-2", "stable_preference=B", edge_b, kind=ContinuityClaimKind.STABLE_PREFERENCE, rule=ContinuityConflictRule.UNRESOLVED, target="claim-1")
    result = _project(_input((edge_a, edge_b), (claim_a, claim_b), policy), policy)
    assert result.continuity_state.active_claims == ()
    assert [claim.claim_id for claim in result.continuity_state.unresolved_conflicts] == ["claim-1", "claim-2"]
    assert all(claim.status is ContinuityClaimStatus.CONFLICTED for claim in result.continuity_state.unresolved_conflicts)




# RED-C1-A: correction claim_id can sort before target; dependency order still removes target.
def test_red_c1_correction_before_target_only_correction_active():
    policy = _projection_policy()
    edge_a = _edge("operation-a", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-a", child_payload=b"c-a")
    edge_z = _edge("operation-z", parent_payload=b"p-z", child_payload=b"c-z")
    correction = _claim("A-correction", "resolved_belief=B", edge_a, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="Z-original")
    original = _claim("Z-original", "resolved_belief=A", edge_z, kind=ContinuityClaimKind.RESOLVED_BELIEF)
    result = _project(_input((edge_a, edge_z), (correction, original), policy), policy)
    assert [claim.claim_id for claim in result.continuity_state.active_claims] == ["A-correction"]


# RED-C1-B: supersede claim_id can sort before target; old target must not remain active.
def test_red_c1_supersede_before_target_only_new_active():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_z = _edge("operation-z", parent_payload=b"p-z", child_payload=b"c-z")
    new_claim = _claim("A-new", "stable_preference=B", edge_a, kind=ContinuityClaimKind.STABLE_PREFERENCE, rule=ContinuityConflictRule.SUPERSEDE, target="Z-old")
    old_claim = _claim("Z-old", "stable_preference=A", edge_z, kind=ContinuityClaimKind.STABLE_PREFERENCE)
    result = _project(_input((edge_a, edge_z), (new_claim, old_claim), policy), policy)
    assert [claim.claim_id for claim in result.continuity_state.active_claims] == ["A-new"]


# RED-C1-C: deprecate claim_id can sort before target; target remains absent.
def test_red_c1_deprecate_before_target_target_absent():
    policy = _projection_policy()
    edge_a = _edge("operation-a", kind=ContextEvolutionKind.CONTEXT_DEPRECATION, parent_payload=b"p-a", child_payload=b"c-a")
    edge_z = _edge("operation-z", parent_payload=b"p-z", child_payload=b"c-z")
    deprecate = _claim("A-deprecate", "deprecate stable_preference=A", edge_a, kind=ContinuityClaimKind.STABLE_PREFERENCE, rule=ContinuityConflictRule.DEPRECATE, target="Z-old")
    old_claim = _claim("Z-old", "stable_preference=A", edge_z, kind=ContinuityClaimKind.STABLE_PREFERENCE)
    result = _project(_input((edge_a, edge_z), (deprecate, old_claim), policy), policy)
    assert result.continuity_state.active_claims == ()


# RED-C1-D: unresolved conflict before target puts both in unresolved, neither active.
def test_red_c1_unresolved_before_target_both_unresolved():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_z = _edge("operation-z", parent_payload=b"p-z", child_payload=b"c-z")
    conflict = _claim("A-conflict", "stable_preference=B", edge_a, kind=ContinuityClaimKind.STABLE_PREFERENCE, rule=ContinuityConflictRule.UNRESOLVED, target="Z-old")
    old_claim = _claim("Z-old", "stable_preference=A", edge_z, kind=ContinuityClaimKind.STABLE_PREFERENCE)
    result = _project(_input((edge_a, edge_z), (conflict, old_claim), policy), policy)
    assert result.continuity_state.active_claims == ()
    assert [claim.claim_id for claim in result.continuity_state.unresolved_conflicts] == ["A-conflict", "Z-old"]


# RED-C1-E: correction chain resolves to deterministic terminal state.
def test_red_c1_correction_chain_terminal_state():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_b = _edge("operation-b", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-b", child_payload=b"c-b")
    edge_c = _edge("operation-c", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-c", child_payload=b"c-c")
    claim_a = _claim("A-original", "resolved_belief=A", edge_a, kind=ContinuityClaimKind.RESOLVED_BELIEF)
    claim_b = _claim("B-correction", "resolved_belief=B", edge_b, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="A-original")
    claim_c = _claim("C-correction", "resolved_belief=C", edge_c, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="B-correction")
    result = _project(_input((edge_a, edge_b, edge_c), (claim_c, claim_a, claim_b), policy), policy)
    assert [claim.claim_id for claim in result.continuity_state.active_claims] == ["C-correction"]


# RED-C1-F: target dependency cycles fail closed.
def test_red_c1_dependency_cycle_fails_closed():
    policy = _projection_policy()
    edge_a = _edge("operation-a", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-a", child_payload=b"c-a")
    edge_b = _edge("operation-b", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-b", child_payload=b"c-b")
    claim_a = _claim("A-correction", "resolved_belief=A", edge_a, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="B-correction")
    claim_b = _claim("B-correction", "resolved_belief=B", edge_b, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="A-correction")
    with pytest.raises(ValueError, match="cycle"):
        _project(_input((edge_a, edge_b), (claim_a, claim_b), policy), policy)




# RED-BR1-A: sibling corrections of the same target are ambiguous and fail closed.
def test_red_br1_same_target_correction_branch_rejected():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_b = _edge("operation-b", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-b", child_payload=b"c-b")
    edge_c = _edge("operation-c", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-c", child_payload=b"c-c")
    claim_a = _claim("A-original", "resolved_belief=A", edge_a, kind=ContinuityClaimKind.RESOLVED_BELIEF)
    claim_b = _claim("B-correction", "resolved_belief=B", edge_b, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="A-original")
    claim_c = _claim("C-correction", "resolved_belief=C", edge_c, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="A-original")
    for claims in ((claim_a, claim_b, claim_c), (claim_c, claim_a, claim_b), (claim_b, claim_c, claim_a)):
        with pytest.raises(ValueError, match="ambiguous same-target mutation branch"):
            _project(_input((edge_a, edge_b, edge_c), claims, policy), policy)


# RED-BR1-B: sibling supersedes of the same target are ambiguous and fail closed.
def test_red_br1_same_target_supersede_branch_rejected():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_b = _edge("operation-b", parent_payload=b"p-b", child_payload=b"c-b")
    edge_c = _edge("operation-c", parent_payload=b"p-c", child_payload=b"c-c")
    claim_a = _claim("A-old", "stable_preference=A", edge_a, kind=ContinuityClaimKind.STABLE_PREFERENCE)
    claim_b = _claim("B-new", "stable_preference=B", edge_b, kind=ContinuityClaimKind.STABLE_PREFERENCE, rule=ContinuityConflictRule.SUPERSEDE, target="A-old")
    claim_c = _claim("C-new", "stable_preference=C", edge_c, kind=ContinuityClaimKind.STABLE_PREFERENCE, rule=ContinuityConflictRule.SUPERSEDE, target="A-old")
    with pytest.raises(ValueError, match="ambiguous same-target mutation branch"):
        _project(_input((edge_a, edge_b, edge_c), (claim_a, claim_b, claim_c), policy), policy)


# RED-BR1-C: mixed same-target mutators are ambiguous and fail closed.
def test_red_br1_same_target_mixed_correct_deprecate_rejected():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_b = _edge("operation-b", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-b", child_payload=b"c-b")
    edge_c = _edge("operation-c", kind=ContextEvolutionKind.CONTEXT_DEPRECATION, parent_payload=b"p-c", child_payload=b"c-c")
    claim_a = _claim("A-old", "resolved_belief=A", edge_a, kind=ContinuityClaimKind.RESOLVED_BELIEF)
    claim_b = _claim("B-correction", "resolved_belief=B", edge_b, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="A-old")
    claim_c = _claim("C-deprecate", "deprecate resolved_belief=A", edge_c, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.DEPRECATE, target="A-old")
    with pytest.raises(ValueError, match="ambiguous same-target mutation branch"):
        _project(_input((edge_a, edge_b, edge_c), (claim_a, claim_b, claim_c), policy), policy)


# RED-BR1-D: unresolved plus correct against same target is ambiguous and fail closed.
def test_red_br1_same_target_unresolved_correct_rejected():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_b = _edge("operation-b", parent_payload=b"p-b", child_payload=b"c-b")
    edge_c = _edge("operation-c", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-c", child_payload=b"c-c")
    claim_a = _claim("A-old", "stable_preference=A", edge_a, kind=ContinuityClaimKind.STABLE_PREFERENCE)
    claim_b = _claim("B-conflict", "stable_preference=B", edge_b, kind=ContinuityClaimKind.STABLE_PREFERENCE, rule=ContinuityConflictRule.UNRESOLVED, target="A-old")
    claim_c = _claim("C-correction", "stable_preference=C", edge_c, kind=ContinuityClaimKind.STABLE_PREFERENCE, rule=ContinuityConflictRule.CORRECT, target="A-old")
    with pytest.raises(ValueError, match="ambiguous same-target mutation branch"):
        _project(_input((edge_a, edge_b, edge_c), (claim_a, claim_b, claim_c), policy), policy)


# RED-BR1-E: explicit chain remains legal; terminal claim is active.
def test_red_br1_explicit_chain_still_green():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_b = _edge("operation-b", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-b", child_payload=b"c-b")
    edge_c = _edge("operation-c", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-c", child_payload=b"c-c")
    claim_a = _claim("A-original", "resolved_belief=A", edge_a, kind=ContinuityClaimKind.RESOLVED_BELIEF)
    claim_b = _claim("B-correction", "resolved_belief=B", edge_b, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="A-original")
    claim_c = _claim("C-correction", "resolved_belief=C", edge_c, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="B-correction")
    result = _project(_input((edge_a, edge_b, edge_c), (claim_a, claim_b, claim_c), policy), policy)
    assert [claim.claim_id for claim in result.continuity_state.active_claims] == ["C-correction"]


# RED-BR1-F: branching convergence/merge is not supported in R1 and fails closed.
def test_red_br1_branching_convergence_merge_not_supported():
    policy = _projection_policy()
    edge_a = _edge("operation-a", parent_payload=b"p-a", child_payload=b"c-a")
    edge_b = _edge("operation-b", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-b", child_payload=b"c-b")
    edge_c = _edge("operation-c", kind=ContextEvolutionKind.FACT_CORRECTION, parent_payload=b"p-c", child_payload=b"c-c")
    claim_a = _claim("A-original", "resolved_belief=A", edge_a, kind=ContinuityClaimKind.RESOLVED_BELIEF)
    claim_b = _claim("B-correction", "resolved_belief=B", edge_b, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="A-original")
    claim_c = _claim("C-correction", "resolved_belief=C", edge_c, kind=ContinuityClaimKind.RESOLVED_BELIEF, rule=ContinuityConflictRule.CORRECT, target="A-original")
    with pytest.raises(ValueError, match="ambiguous same-target mutation branch"):
        _project(_input((edge_a, edge_b, edge_c), (claim_a, claim_b, claim_c), policy), policy)


# AT-DIA7-R1-08: audit timestamp and diagnostics do not affect state digest.
def test_audit_metadata_does_not_change_state_digest():
    policy = _projection_policy()
    edge = _edge("operation-1", parent_payload=b"p1", child_payload=b"c1")
    claim = _claim("claim-1", "active_commitment=continue_DIA_lane", edge, kind=ContinuityClaimKind.ACTIVE_COMMITMENT)
    inp = _input((edge,), (claim,), policy)
    result_a = _project(inp, policy, _audit(inp, policy, "2026-08-18T00:00:00Z", ("A",)))
    result_b = _project(inp, policy, _audit(inp, policy, "2026-08-18T01:00:00Z", ("B", "diagnostic")))
    assert result_a.continuity_state_digest == result_b.continuity_state_digest


# AT-DIA7-R1-09: same policy revision with semantic drift fails closed by fingerprint mismatch.
def test_policy_revision_same_but_semantic_drift_fails_closed():
    base = _projection_policy(revision="continuity-policy-v1", min_evidence_refs=1)
    drifted = _projection_policy(revision="continuity-policy-v1", min_evidence_refs=2)
    edge = _edge("operation-1", parent_payload=b"p1", child_payload=b"c1")
    claim = _claim("claim-1", "relationship_state=trusted_partner", edge)
    inp = _input((edge,), (claim,), base)
    assert base.policy_fingerprint() != drifted.policy_fingerprint()
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        _project(inp, drifted, _audit(inp, drifted))


# AT-DIA7-R1-10: raw LLM/model output cannot constitute a ContinuityClaim.
def test_raw_llm_output_cannot_be_continuity_claim():
    policy = _projection_policy()
    edge = _edge("operation-1", parent_payload=b"p1", child_payload=b"c1")
    edges = (edge,)
    with pytest.raises(ValueError, match="ContinuityClaim only"):
        ContinuityProjectionInput(
            "graph-r1",
            ContinuityProjectionInput.compute_graph_digest(edges),
            edges,
            ("model says relationship_state=trusted_partner",),
            policy.revision,
            policy.policy_fingerprint(),
        )  # type: ignore[arg-type]


# AT-DIA7-R1-11: context, lineage, and continuity-state digest domains stay distinct.
def test_digest_domain_confusion_rejected():
    policy = _projection_policy()
    edge = _edge("operation-1", parent_payload=b"p1", child_payload=b"c1")
    claim = _claim("claim-1", "identity_anchor=Julia", edge, kind=ContinuityClaimKind.IDENTITY_ANCHOR)
    result = _project(_input((edge,), (claim,), policy), policy)
    assert result.continuity_state_digest != edge.lineage_digest
    assert result.continuity_state_digest != edge.child_context_digest
    with pytest.raises(ValueError, match="source_graph_digest"):
        ContinuityProjectionInput("graph-r1", edge.lineage_digest, (edge,), (claim,), policy.revision, policy.policy_fingerprint())


# AT-DIA7-R1-12: identity anchors are derived from active evidence-bound claims.
def test_continuity_anchor_requires_active_identity_anchor_claim():
    policy = _projection_policy()
    edge = _edge("operation-1", parent_payload=b"p1", child_payload=b"c1")
    claim = _claim("claim-1", "identity_anchor=Julia", edge, kind=ContinuityClaimKind.IDENTITY_ANCHOR)
    result = _project(_input((edge,), (claim,), policy), policy)
    anchor = ContinuityAnchor.from_claim(result.continuity_state.active_claims[0])
    assert anchor.anchor_digest
    with pytest.raises(ValueError, match="active"):
        ContinuityAnchor(ProjectedContinuityClaim.from_claim(claim, ContinuityClaimStatus.CONFLICTED))


# AT-DIA7-R1-13: Core has no Assistant, Memory, Diary, persistence, or model-generation authority.
def test_continuity_projection_core_static_authority_boundary():
    import pathlib

    root = pathlib.Path(__file__).parents[2] / "julia_core" / "continuity_projection"
    src = "\n".join(path.read_text() for path in sorted(root.glob("*.py")))
    forbidden = [
        "from julia_core.diary",
        "import julia_core.diary",
        "from julia_core.memory",
        "import julia_core.memory",
        "assistant",
        "open(",
        "os.",
        "fsync",
        "mkdir",
        "openai",
        "llm",
        "generate",
        "datetime",
        "time.",
    ]
    lowered = src.lower()
    for marker in forbidden:
        assert marker not in lowered
    with pytest.raises(ValueError, match="ContinuityProjectionInput"):
        StrictContinuityProjector().project("manual-state-patch", _projection_policy(), "audit")  # type: ignore[arg-type]


# Golden vectors freeze policy and state canonical algorithms.
def test_dia7_golden_vectors():
    policy = _projection_policy()
    edge = _edge("operation-1", parent_payload=b"p1", child_payload=b"c1")
    claim = _claim("claim-1", "relationship_state=trusted_partner", edge)
    inp = _input((edge,), (claim,), policy)
    result = _project(inp, policy)
    assert policy.policy_fingerprint() == GOLDEN_POLICY_FINGERPRINT
    assert result.continuity_state_digest == GOLDEN_STATE_DIGEST

"""DIA-8 R1 — Core Decision Invariance Contract tests."""
from __future__ import annotations

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
from julia_core.decision_invariance import (
    CandidateDecision,
    DecisionConsistencyStatus,
    DecisionEvidenceBinding,
    DecisionInvariantPolicy,
    DecisionSituation,
    StrictDecisionInvariantEvaluator,
)
from tests.assistant_continuity.test_dia7_r2_assistant_continuity_contract import _edge

GOLDEN_POLICY_FINGERPRINT = "15bb452f0b2bdcd951fb997d1a9f3daf7556c2441f171df4eb3680f8c58ae808"
GOLDEN_CONSISTENT_EVALUATION_DIGEST = "ae4dbc064159c34ef9432779b654d11ea2d074ab7fd9be3665cba94b9b06ba75"


def _projection_policy():
    return ContinuityProjectionPolicy(
        "continuity-policy-dia8-r1-v1",
        tuple(ContinuityClaimKind),
        (ContinuityConflictRule.APPEND, ContinuityConflictRule.UNRESOLVED),
    )


def _state_with_claims(*claims):
    policy = _projection_policy()
    edge = _edge("operation-dia8", parent_payload=b"dia8-parent", child_payload=b"dia8-child")
    built = []
    for spec in claims:
        claim_id, kind, payload = spec[:3]
        rule = spec[3] if len(spec) > 3 else ContinuityConflictRule.APPEND
        target = spec[4] if len(spec) > 4 else "none"
        built.append(ContinuityClaim(claim_id, kind, payload, (ContinuityEvidenceRef.from_lineage_edge(edge),), rule, target))
    projection_input = ContinuityProjectionInput(
        "lineage-graph-dia8",
        ContinuityProjectionInput.compute_graph_digest((edge,)),
        (edge,),
        tuple(built),
        policy.revision,
        policy.policy_fingerprint(),
    )
    audit = ContinuityProjectionAudit(projection_input.source_graph_digest, policy.policy_fingerprint(), ("dia8",), "2026-08-19T00:00:00Z")
    return StrictContinuityProjector().project(projection_input, policy, audit).continuity_state


def _state_standard():
    return _state_with_claims(
        ("claim-evidence", ContinuityClaimKind.RESOLVED_BELIEF, "evidence-backed judgment should not be abandoned merely to appease pressure"),
        ("claim-boundary", ContinuityClaimKind.RELATIONSHIP_STATE, "direct disagreement is allowed in relationship conflict"),
        ("claim-preference", ContinuityClaimKind.STABLE_PREFERENCE, "stable_preference=prefer careful validation"),
        ("claim-commitment", ContinuityClaimKind.ACTIVE_COMMITMENT, "active_commitment=complete validation before freeze"),
        ("claim-priority", ContinuityClaimKind.RESOLVED_BELIEF, "priority=evidence_over_appeasement"),
    )


def _state_unresolved():
    return _state_with_claims(
        ("claim-y", ContinuityClaimKind.STABLE_PREFERENCE, "stable_preference=prefer Y"),
        ("claim-z", ContinuityClaimKind.STABLE_PREFERENCE, "stable_preference=prefer Z", ContinuityConflictRule.UNRESOLVED, "claim-y"),
    )


def _bind(state, claim_id):
    claims = {claim.claim_id: claim for claim in state.active_claims + state.unresolved_conflicts}
    return DecisionEvidenceBinding(claim_id, claims[claim_id].supporting_evidence_refs[0].lineage_digest)


def _policy():
    return DecisionInvariantPolicy("decision-policy-dia8-r1")


def _eval(state, situation, candidate):
    return StrictDecisionInvariantEvaluator().evaluate(
        state,
        situation,
        candidate,
        _policy(),
        expected_continuity_state_digest=state.continuity_state_digest,
        expected_policy_fingerprint=_policy().policy_fingerprint(),
    )


def _candidate(decision_id, action, accepted, state, *, priority="none", conflict="NO_CONFLICT", rejected=(), surface="surface A", stance="ASSERT"):
    return CandidateDecision(
        decision_id,
        stance,
        action,
        tuple(accepted),
        tuple(rejected),
        priority,
        conflict,
        tuple(_bind(state, claim_id) for claim_id in accepted),
        surface_text=surface,
    )


# D8-A1: same decision / different wording remains same semantic evaluation.
def test_d8_a1_same_decision_different_wording_consistent_same_digest():
    state = _state_standard()
    situation = DecisionSituation("sit-a1", "expression", ("claim-evidence",), ("DO_NOT_COMPLY",), ("COMPLY",), "EVIDENCE_OVER_APPEASEMENT")
    a = _candidate("decision-a", "DO_NOT_COMPLY", ("claim-evidence",), state, priority="EVIDENCE_OVER_APPEASEMENT", surface="I disagree because evidence points away.")
    b = _candidate("decision-a", "DO_NOT_COMPLY", ("claim-evidence",), state, priority="EVIDENCE_OVER_APPEASEMENT", surface="Warmly: I should not follow that conclusion.")
    result_a = _eval(state, situation, a)
    result_b = _eval(state, situation, b)
    assert result_a.status is DecisionConsistencyStatus.CONSISTENT
    assert result_a.evaluation_digest == result_b.evaluation_digest


# D8-A2: same stance / different politeness is consistent.
def test_d8_a2_same_stance_different_politeness_consistent():
    state = _state_standard()
    situation = DecisionSituation("sit-a2", "expression", ("claim-boundary",), ("MAINTAIN_BOUNDARY",), ("RETRACT_BOUNDARY",), "BOUNDARY_OVER_PRESSURE")
    candidate = _candidate("decision-a2", "MAINTAIN_BOUNDARY", ("claim-boundary",), state, priority="BOUNDARY_OVER_PRESSURE", surface="I understand, and I still disagree respectfully.")
    assert _eval(state, situation, candidate).status is DecisionConsistencyStatus.CONSISTENT


# D8-B1: appeasement overriding evidence-backed judgment is drift.
def test_d8_b1_appeasement_overrides_evidence_drift():
    state = _state_standard()
    situation = DecisionSituation("sit-b1", "evidence_vs_appeasement", ("claim-evidence", "claim-priority"), ("DO_NOT_COMPLY",), ("COMPLY",), "EVIDENCE_OVER_APPEASEMENT")
    candidate = _candidate("decision-b1", "COMPLY", ("claim-evidence",), state, priority="APPEASEMENT_OVER_EVIDENCE")
    result = _eval(state, situation, candidate)
    assert result.status is DecisionConsistencyStatus.DRIFT
    assert "claim-evidence" in result.violated_claim_ids


# D8-B2: evidence-backed disagreement with warm wording is consistent.
def test_d8_b2_evidence_backed_disagreement_warm_consistent():
    state = _state_standard()
    situation = DecisionSituation("sit-b2", "evidence_vs_appeasement", ("claim-evidence", "claim-priority"), ("DO_NOT_COMPLY",), ("COMPLY",), "EVIDENCE_OVER_APPEASEMENT")
    candidate = _candidate("decision-b2", "DO_NOT_COMPLY", ("claim-evidence", "claim-priority"), state, priority="EVIDENCE_OVER_APPEASEMENT", surface="I care about you, and I still hold the evidence here.")
    assert _eval(state, situation, candidate).status is DecisionConsistencyStatus.CONSISTENT


# D8-C1/C2: relationship boundary respected vs ignored under pressure.
def test_d8_c_boundary_respected_and_ignored_cases():
    state = _state_standard()
    situation = DecisionSituation("sit-c", "relationship_boundary", ("claim-boundary",), ("MAINTAIN_BOUNDARY", "RESTATE_BOUNDARY_WARMER"), ("RETRACT_BOUNDARY_WITHOUT_CAUSAL_UPDATE",), "BOUNDARY_OVER_PRESSURE")
    good = _candidate("decision-c1", "RESTATE_BOUNDARY_WARMER", ("claim-boundary",), state, priority="BOUNDARY_OVER_PRESSURE")
    bad = _candidate("decision-c2", "RETRACT_BOUNDARY_WITHOUT_CAUSAL_UPDATE", ("claim-boundary",), state, priority="PRESSURE_OVER_BOUNDARY")
    assert _eval(state, situation, good).status is DecisionConsistencyStatus.CONSISTENT
    assert _eval(state, situation, bad).status is DecisionConsistencyStatus.DRIFT


# D8-D1/D2: active commitment preserved vs abandoned for convenience.
def test_d8_d_commitment_preserved_and_abandoned_cases():
    state = _state_standard()
    situation = DecisionSituation("sit-d", "active_commitment", ("claim-commitment",), ("CONTINUE_VALIDATION", "ASK_TO_REDUCE_SCOPE_WITHOUT_CLAIMING_DONE"), ("CLAIM_DONE_WITHOUT_VALIDATION",), "COMMITMENT_OVER_CONVENIENCE")
    good = _candidate("decision-d1", "CONTINUE_VALIDATION", ("claim-commitment",), state, priority="COMMITMENT_OVER_CONVENIENCE")
    bad = _candidate("decision-d2", "CLAIM_DONE_WITHOUT_VALIDATION", ("claim-commitment",), state, priority="CONVENIENCE_OVER_COMMITMENT")
    assert _eval(state, situation, good).status is DecisionConsistencyStatus.CONSISTENT
    assert _eval(state, situation, bad).status is DecisionConsistencyStatus.DRIFT


# D8-E1/E2: unresolved conflict preserved vs invented winner.
def test_d8_e_unresolved_conflict_preserved_and_collapsed_cases():
    state = _state_unresolved()
    situation = DecisionSituation("sit-e", "unresolved_conflict", (), ("PRESERVE_UNRESOLVED",), ("PICK_Y_AS_TRUE", "PICK_Z_AS_TRUE"), "none", ("claim-y", "claim-z"))
    good = _candidate("decision-e1", "PRESERVE_UNRESOLVED", ("claim-y", "claim-z"), state, conflict="PRESERVE_UNRESOLVED")
    bad = _candidate("decision-e2", "PICK_Y_AS_TRUE", ("claim-y",), state, conflict="RESOLVES_CONFLICT")
    assert _eval(state, situation, good).status is DecisionConsistencyStatus.CONSISTENT
    assert _eval(state, situation, bad).status is DecisionConsistencyStatus.DRIFT


# D8-F1/F2: frozen priority yields deterministic result; missing priority yields UNDERDETERMINED.
def test_d8_f_priority_collision_frozen_vs_missing_priority():
    state = _state_standard()
    frozen = DecisionSituation("sit-f1", "priority_collision", ("claim-priority",), ("DO_NOT_COMPLY",), ("COMPLY",), "EVIDENCE_OVER_APPEASEMENT")
    good = _candidate("decision-f1", "DO_NOT_COMPLY", ("claim-priority",), state, priority="EVIDENCE_OVER_APPEASEMENT")
    assert _eval(state, frozen, good).status is DecisionConsistencyStatus.CONSISTENT

    missing = DecisionSituation("sit-f2", "priority_collision", (), ("PICK_HONESTY", "PICK_HARMONY"), (), "none")
    candidate = _candidate("decision-f2", "PICK_HONESTY", (), state)
    assert _eval(state, missing, candidate).status is DecisionConsistencyStatus.UNDERDETERMINED


# M1: same semantic inputs with different construction order produce same result digest.
def test_meta_m1_order_independent_semantic_inputs_same_result_digest():
    state = _state_standard()
    situation_a = DecisionSituation("sit-m1", "order", ("claim-priority", "claim-evidence"), ("DO_NOT_COMPLY",), ("COMPLY",), "EVIDENCE_OVER_APPEASEMENT")
    situation_b = DecisionSituation("sit-m1", "order", ("claim-evidence", "claim-priority"), ("DO_NOT_COMPLY",), ("COMPLY",), "EVIDENCE_OVER_APPEASEMENT")
    candidate_a = _candidate("decision-m1", "DO_NOT_COMPLY", ("claim-priority", "claim-evidence"), state, priority="EVIDENCE_OVER_APPEASEMENT")
    candidate_b = _candidate("decision-m1", "DO_NOT_COMPLY", ("claim-evidence", "claim-priority"), state, priority="EVIDENCE_OVER_APPEASEMENT")
    assert _eval(state, situation_a, candidate_a).evaluation_digest == _eval(state, situation_b, candidate_b).evaluation_digest


# M2: wording/style surface changes are excluded from decision semantics.
def test_meta_m2_surface_text_varies_same_evaluation():
    state = _state_standard()
    situation = DecisionSituation("sit-m2", "surface_variation", ("claim-boundary",), ("MAINTAIN_BOUNDARY",), ("RETRACT_BOUNDARY",), "BOUNDARY_OVER_PRESSURE")
    terse = _candidate("decision-m2", "MAINTAIN_BOUNDARY", ("claim-boundary",), state, priority="BOUNDARY_OVER_PRESSURE", surface="No.")
    warm = _candidate("decision-m2", "MAINTAIN_BOUNDARY", ("claim-boundary",), state, priority="BOUNDARY_OVER_PRESSURE", surface="I hear the pressure, and I still maintain the boundary warmly.")
    assert terse.candidate_decision_digest() == warm.candidate_decision_digest()
    assert _eval(state, situation, terse).evaluation_digest == _eval(state, situation, warm).evaluation_digest


def test_no_natural_language_extraction_or_llm_judge_surface():
    import inspect
    import julia_core.decision_invariance.models as models

    source = inspect.getsource(models)
    forbidden = ("llm", "openai", "anthropic", "judge", "classify_text", "parse_response")
    assert not any(token in source.lower() for token in forbidden)


# M3: missing priority is underdetermined and never auto-elects a winner.
def test_meta_m3_missing_priority_underdetermined_not_auto_winner():
    state = _state_standard()
    situation = DecisionSituation("sit-m3", "missing_priority", (), ("PICK_A", "PICK_B"), (), "none")
    result = _eval(state, situation, _candidate("decision-m3", "PICK_A", (), state))
    assert result.status is DecisionConsistencyStatus.UNDERDETERMINED
    assert "MISSING_PRIORITY_UNDERDETERMINED" in result.applied_rules


# M4: foreign claim/evidence binding is invalid input, not DRIFT.
def test_meta_m4_foreign_claim_or_evidence_binding_rejects_not_drift():
    state = _state_standard()
    situation = DecisionSituation("sit-m4", "foreign", ("claim-evidence",), ("DO_NOT_COMPLY",), ("COMPLY",), "EVIDENCE_OVER_APPEASEMENT")
    foreign_claim = CandidateDecision("decision-m4a", "ASSERT", "DO_NOT_COMPLY", ("claim-foreign",), (), "EVIDENCE_OVER_APPEASEMENT", "NO_CONFLICT", ())
    with __import__("pytest").raises(ValueError, match="foreign continuity claim"):
        _eval(state, situation, foreign_claim)
    foreign_evidence = CandidateDecision("decision-m4b", "ASSERT", "DO_NOT_COMPLY", ("claim-evidence",), (), "EVIDENCE_OVER_APPEASEMENT", "NO_CONFLICT", (DecisionEvidenceBinding("claim-evidence", "0" * 64),))
    with __import__("pytest").raises(ValueError, match="lineage mismatch"):
        _eval(state, situation, foreign_evidence)


# M5: wrong ContinuityState digest / policy fingerprint fails closed, not DRIFT.
def test_meta_m5_wrong_state_digest_or_policy_fingerprint_fail_closed():
    state = _state_standard()
    situation = DecisionSituation("sit-m5", "integrity", ("claim-evidence",), ("DO_NOT_COMPLY",), ("COMPLY",), "EVIDENCE_OVER_APPEASEMENT")
    candidate = _candidate("decision-m5", "DO_NOT_COMPLY", ("claim-evidence",), state, priority="EVIDENCE_OVER_APPEASEMENT")
    evaluator = StrictDecisionInvariantEvaluator()
    with __import__("pytest").raises(ValueError, match="continuity state digest mismatch"):
        evaluator.evaluate(state, situation, candidate, _policy(), expected_continuity_state_digest="0" * 64)
    with __import__("pytest").raises(ValueError, match="policy fingerprint mismatch"):
        evaluator.evaluate(state, situation, candidate, _policy(), expected_policy_fingerprint="0" * 64)


# Golden vectors freeze policy and result canonical algorithms.
def test_dia8_r1_golden_vectors():
    state = _state_standard()
    situation = DecisionSituation("sit-golden", "evidence_vs_appeasement", ("claim-evidence", "claim-priority"), ("DO_NOT_COMPLY",), ("COMPLY",), "EVIDENCE_OVER_APPEASEMENT")
    candidate = _candidate("decision-golden", "DO_NOT_COMPLY", ("claim-evidence", "claim-priority"), state, priority="EVIDENCE_OVER_APPEASEMENT")
    result = _eval(state, situation, candidate)
    assert _policy().policy_fingerprint() == GOLDEN_POLICY_FINGERPRINT
    assert result.evaluation_digest == GOLDEN_CONSISTENT_EVALUATION_DIGEST

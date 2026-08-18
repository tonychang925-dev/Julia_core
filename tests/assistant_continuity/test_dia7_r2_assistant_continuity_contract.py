"""DIA-7 R2.0 — Assistant Continuity Integration Contract tests."""
from __future__ import annotations

from datetime import timedelta

import pytest

from julia_core.assistant_continuity import (
    AssistantContinuityResponseContext,
    AssistantContinuitySessionBinding,
    AssistantContinuityStatePackage,
    ContinuityConsumptionAudit,
    ContinuityStateBindingStore,
    StrictAssistantContinuityBinder,
)
from julia_core.context_evolution import (
    ContextEvolutionKind,
    ContextEvolutionOperation,
    ContextEvolutionPolicy,
    ContextLineageNode,
    EvolutionAuthority,
    StrictContextEvolutionValidator,
)
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

GOLDEN_PACKAGE_DIGEST = "4a13179e7ee38c90df1f728a550b3a49bc0decc80cd27392a23574d433bb1734"
GOLDEN_BINDING_DIGEST = "6a6df4c91a8efb0650774ec0b59deb1ff5916efb9a391c27b7286c879ca95c08"
GOLDEN_RESPONSE_CONTEXT_DIGEST = "8270998a600109ab4dd4f65cde6ff48233837d3b7a2e4ebaf9ea6df4ad387b9f"


def _trigger_policy():
    return TriggerPolicy("policy-dia7-r2", timedelta(seconds=0), timedelta(seconds=60), timedelta(seconds=30))


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


def _context(payload=b"payload"):
    ref = _ref("evt_A")
    opportunity = _opportunity(ref)
    return DeterministicReflectionContextAssembler().assemble(
        ReflectionOpportunityHandoff(opportunity, "pending-digest-dia7-r2", "dia3-handoff"),
        _Reader((_fact(ref, payload),)),
        ContextAssemblyPolicy("ctx-policy-dia7-r2", ContextBounds(4, 1024, 512)),
    )


def _edge(operation_id="operation-1", kind=ContextEvolutionKind.FACT_APPEND, *, parent_payload=b"parent", child_payload=b"child"):
    evo_policy = ContextEvolutionPolicy("evo-policy-dia7-r2", (ContextEvolutionKind.FACT_APPEND, ContextEvolutionKind.FACT_CORRECTION, ContextEvolutionKind.CONTEXT_DEPRECATION), 4)
    parent = ContextLineageNode.from_context(_context(parent_payload))
    child = ContextLineageNode.from_context(_context(child_payload))
    op = ContextEvolutionOperation(
        operation_id,
        kind,
        parent,
        child,
        evo_policy.revision,
        evo_policy.policy_fingerprint(),
        EvolutionAuthority("dia7-r2-test", "trusted-evolution-input", "dia6-evolution-authority-v1"),
        (_ref(f"evt_reason_{operation_id}"),),
    )
    return StrictContextEvolutionValidator().validate(op, evo_policy)


def _projection_policy():
    return ContinuityProjectionPolicy(
        "continuity-policy-r2-v1",
        (ContinuityClaimKind.IDENTITY_ANCHOR, ContinuityClaimKind.RELATIONSHIP_STATE, ContinuityClaimKind.ACTIVE_COMMITMENT),
        (ContinuityConflictRule.APPEND, ContinuityConflictRule.UNRESOLVED),
    )


def _state():
    policy = _projection_policy()
    edge = _edge("operation-1", parent_payload=b"p1", child_payload=b"c1")
    claim = ContinuityClaim(
        "claim-1",
        ContinuityClaimKind.RELATIONSHIP_STATE,
        "relationship_state=trusted_partner",
        (ContinuityEvidenceRef.from_lineage_edge(edge),),
    )
    edges = (edge,)
    claims = (claim,)
    projection_input = ContinuityProjectionInput(
        "lineage-graph-r2",
        ContinuityProjectionInput.compute_graph_digest(edges),
        edges,
        claims,
        policy.revision,
        policy.policy_fingerprint(),
    )
    audit = ContinuityProjectionAudit(projection_input.source_graph_digest, policy.policy_fingerprint(), ("projected",), "2026-08-18T00:00:00Z")
    return StrictContinuityProjector().project(projection_input, policy, audit).continuity_state


def _package():
    return AssistantContinuityStatePackage.from_state(_state())


def _binding(package=None, session_id="session-A"):
    package = package or _package()
    return StrictAssistantContinuityBinder().bind_for_session(
        session_id,
        package,
        expected_state_digest=package.continuity_state_digest,
        expected_source_graph_digest=package.source_graph_digest,
        expected_projection_policy_fingerprint=package.projection_policy_fingerprint,
    )


# R2-01: Assistant package consumes exact ContinuityState and exposes claims read-only.
def test_package_requires_exact_continuity_state_and_exposes_claims():
    package = _package()
    assert package.active_claims == package.continuity_state.active_claims
    assert package.unresolved_conflicts == package.continuity_state.unresolved_conflicts
    with pytest.raises(ValueError, match="ContinuityState"):
        AssistantContinuityStatePackage("model generated state")  # type: ignore[arg-type]


# R2-02: session/state/source graph/policy cross-binding is exact.
def test_session_state_graph_policy_cross_binding():
    package = _package()
    binding = _binding(package, "session-A")
    assert binding.session_id == "session-A"
    assert binding.continuity_state_digest == package.continuity_state_digest
    assert binding.source_graph_digest == package.source_graph_digest
    assert binding.projection_policy_fingerprint == package.projection_policy_fingerprint
    assert binding.package_digest == package.package_digest


# R2-03/04/05: wrong digest, graph, or policy fails closed.
def test_wrong_cross_binding_fields_fail_closed():
    package = _package()
    binder = StrictAssistantContinuityBinder()
    with pytest.raises(ValueError, match="state digest mismatch"):
        binder.bind_for_session("session-A", package, expected_state_digest="0" * 64, expected_source_graph_digest=package.source_graph_digest, expected_projection_policy_fingerprint=package.projection_policy_fingerprint)
    with pytest.raises(ValueError, match="source graph digest mismatch"):
        binder.bind_for_session("session-A", package, expected_state_digest=package.continuity_state_digest, expected_source_graph_digest="0" * 64, expected_projection_policy_fingerprint=package.projection_policy_fingerprint)
    with pytest.raises(ValueError, match="policy fingerprint mismatch"):
        binder.bind_for_session("session-A", package, expected_state_digest=package.continuity_state_digest, expected_source_graph_digest=package.source_graph_digest, expected_projection_policy_fingerprint="0" * 64)


# R2-06: stale or corrupted state digest cannot be packaged.
def test_stale_or_corrupted_state_digest_rejected():
    state = _state()
    object.__setattr__(state, "continuity_state_digest", "0" * 64)
    with pytest.raises(ValueError, match="digest mismatch"):
        AssistantContinuityStatePackage.from_state(state)


# R2-07: restart/replay binding validates the exact same package.
def test_restart_replay_binding_store_validates_exact_package():
    package = _package()
    binding = _binding(package, "session-A")
    store = ContinuityStateBindingStore()
    store.save(binding)
    replay = store.replay_validate("session-A", package)
    assert replay.binding_digest == binding.binding_digest
    with pytest.raises(ValueError, match="no continuity binding"):
        store.replay_validate("wrong-session", package)


# R2-08: rebinding same session to different continuity state fails closed.
def test_same_session_different_state_rebind_rejected():
    package_a = _package()
    package_b = AssistantContinuityStatePackage.from_state(_state())
    object.__setattr__(package_b, "package_digest", "0" * 64)
    binding_a = _binding(package_a, "session-A")
    binding_b = AssistantContinuitySessionBinding.bind("session-A", package_b)
    store = ContinuityStateBindingStore()
    store.save(binding_a)
    with pytest.raises(ValueError, match="different continuity state"):
        store.save(binding_b)


# R2-09: Assistant response context is bound to the exact consumed state package.
def test_response_context_bound_to_exact_consumed_state():
    package = _package()
    binding = _binding(package, "session-A")
    context = StrictAssistantContinuityBinder().response_context(binding, package)
    assert context.session_binding.binding_digest == binding.binding_digest
    assert context.active_claims == package.active_claims
    with pytest.raises(ValueError, match="package digest mismatch"):
        altered = AssistantContinuityStatePackage.from_state(_state())
        object.__setattr__(altered, "package_digest", "0" * 64)
        AssistantContinuityResponseContext(binding, altered)


# R2-10: audit metadata is sidecar and does not affect package/binding/context digest.
def test_consumption_audit_does_not_affect_binding_identity():
    package = _package()
    binding = _binding(package, "session-A")
    context = StrictAssistantContinuityBinder().response_context(binding, package)
    audit_a = ContinuityConsumptionAudit("session-A", binding.binding_digest, package.continuity_state_digest, ("A",), "2026-08-18T00:00:00Z")
    audit_b = ContinuityConsumptionAudit("session-A", binding.binding_digest, package.continuity_state_digest, ("B", "diagnostic"), "2026-08-18T01:00:00Z")
    assert audit_a.binding_digest == audit_b.binding_digest == binding.binding_digest
    assert context.response_context_digest == StrictAssistantContinuityBinder().response_context(binding, package).response_context_digest


# R2-11: raw model output/manual patches cannot create binding or response context.
def test_model_output_and_manual_patch_rejected():
    package = _package()
    binder = StrictAssistantContinuityBinder()
    with pytest.raises(ValueError, match="AssistantContinuityStatePackage"):
        binder.bind_for_session("session-A", "model says current identity", expected_state_digest=package.continuity_state_digest, expected_source_graph_digest=package.source_graph_digest, expected_projection_policy_fingerprint=package.projection_policy_fingerprint)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="AssistantContinuitySessionBinding"):
        binder.response_context("manual-binding", package)  # type: ignore[arg-type]


# R2-12: Core authority boundary excludes projection mutation, persistence, model generation.
def test_assistant_continuity_static_authority_boundary():
    import pathlib

    root = pathlib.Path(__file__).parents[2] / "julia_core" / "assistant_continuity"
    src = "\n".join(path.read_text() for path in sorted(root.glob("*.py")))
    forbidden = [
        "from julia_core.diary",
        "import julia_core.diary",
        "from julia_core.memory",
        "import julia_core.memory",
        "from julia_core.context_os",
        "import julia_core.context_os",
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


# Golden vectors freeze R2 package, binding, and response-context algorithms.
def test_dia7_r2_golden_vectors():
    package = _package()
    binding = _binding(package, "session-A")
    context = StrictAssistantContinuityBinder().response_context(binding, package)
    assert package.package_digest == GOLDEN_PACKAGE_DIGEST
    assert binding.binding_digest == GOLDEN_BINDING_DIGEST
    assert context.response_context_digest == GOLDEN_RESPONSE_CONTEXT_DIGEST

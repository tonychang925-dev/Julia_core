"""DIA-6 R1 — Context Evolution Core Contract tests."""
from __future__ import annotations

from datetime import timedelta
from hashlib import sha256

import pytest

from julia_core.context_evolution import (
    CHILD_VALIDATION_REVISION,
    LINEAGE_DIGEST_ALGORITHM_REVISION,
    PARENT_VERIFICATION_REVISION,
    ContextEvolutionAudit,
    ContextEvolutionKind,
    ContextEvolutionOperation,
    ContextEvolutionPolicy,
    ContextLineageEdge,
    ContextLineageNode,
    EvolutionAuthority,
    StrictContextEvolutionValidator,
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

GOLDEN_POLICY_FINGERPRINT = "01bf15b7f121c57bbc982b48ab4f59d099d8ba3d9b2ceaa4473e20ece3272ac4"
GOLDEN_LINEAGE_DIGEST = "c2b704a320bf25669228295d141327973acbdbbbc4ae76a764935dbbb9131f6f"


def _trigger_policy():
    return TriggerPolicy("policy-dia6", timedelta(seconds=0), timedelta(seconds=60), timedelta(seconds=30))


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


def _assembly_policy(revision="ctx-policy-dia6"):
    return ContextAssemblyPolicy(revision, ContextBounds(4, 1024, 512))


def _context(payload=b"parent payload"):
    ref = _ref("evt_A")
    opportunity = _opportunity(ref)
    return DeterministicReflectionContextAssembler().assemble(
        ReflectionOpportunityHandoff(opportunity, "pending-digest-dia6", "dia3-handoff"),
        _Reader((_fact(ref, payload),)),
        _assembly_policy(),
    )


def _policy(*, allowed=(ContextEvolutionKind.FACT_APPEND, ContextEvolutionKind.FACT_CORRECTION, ContextEvolutionKind.CONTEXT_DEPRECATION), max_reason_refs=4, revision="evo-policy-v1"):
    return ContextEvolutionPolicy(revision, tuple(allowed), max_reason_refs)


def _authority():
    return EvolutionAuthority("dia6-core-test", "trusted-evolution-input", "dia6-evolution-authority-v1")


def _operation(kind=ContextEvolutionKind.FACT_APPEND, *, parent_payload=b"parent payload", child_payload=b"child payload", policy=None, reason_refs=None):
    policy = policy or _policy()
    parent = ContextLineageNode.from_context(_context(parent_payload))
    child = ContextLineageNode.from_context(_context(child_payload))
    return ContextEvolutionOperation(
        "operation-1",
        kind,
        parent,
        child,
        policy.revision,
        policy.policy_fingerprint(),
        _authority(),
        reason_refs or (_ref("evt_reason"),),
    )


# AT-DIA6-R0-01/03: evolution produces a child identity and never mutates parent bytes.
def test_evolution_is_new_child_identity_not_parent_mutation():
    parent_context = _context(b"parent payload")
    parent_bytes_before = parent_context.semantic_canonical_bytes()
    op = _operation(parent_payload=b"parent payload", child_payload=b"child payload")
    edge = StrictContextEvolutionValidator().validate(op, _policy())
    assert op.parent_context.context_digest != op.child_context.context_digest
    assert edge.parent_context_digest == op.parent_context.context_digest
    assert parent_context.semantic_canonical_bytes() == parent_bytes_before


# AT-DIA6-R0-02: same context digest with different semantic bytes hash is corruption.
def test_same_context_digest_with_different_semantic_hash_rejected():
    parent = ContextLineageNode.from_context(_context(b"parent"))
    corrupt_child = ContextLineageNode(
        parent.context_digest,
        parent.context_version,
        parent.assembly_policy_revision,
        parent.assembly_policy_fingerprint,
        sha256(b"different bytes").hexdigest(),
    )
    policy = _policy()
    with pytest.raises(ValueError, match="same context digest"):
        ContextEvolutionOperation("op-corrupt", ContextEvolutionKind.FACT_APPEND, parent, corrupt_child, policy.revision, policy.policy_fingerprint(), _authority(), (_ref("evt_reason"),))


# AT-DIA6-R0-04/05: lineage digest binds parent and child identities.
def test_lineage_digest_binds_parent_and_child():
    policy = _policy()
    edge_a = StrictContextEvolutionValidator().validate(_operation(parent_payload=b"parent-A", child_payload=b"child", policy=policy), policy)
    edge_b = StrictContextEvolutionValidator().validate(_operation(parent_payload=b"parent-B", child_payload=b"child", policy=policy), policy)
    edge_c = StrictContextEvolutionValidator().validate(_operation(parent_payload=b"parent-A", child_payload=b"child-C", policy=policy), policy)
    assert edge_a.lineage_digest != edge_b.lineage_digest
    assert edge_a.lineage_digest != edge_c.lineage_digest


# AT-DIA6-R0-06: exact operation type is required at validation boundary.
def test_arbitrary_operation_object_not_accepted_by_validator():
    class OperationSubclass(ContextEvolutionOperation):
        pass

    policy = _policy()
    op = _operation(policy=policy)
    spoof = OperationSubclass(op.operation_id, op.operation_kind, op.parent_context, op.child_context, op.evolution_policy_revision, op.evolution_policy_fingerprint, op.authority, op.reason_refs)
    with pytest.raises(ValueError, match="exact ContextEvolutionOperation"):
        StrictContextEvolutionValidator().validate(spoof, policy)


# AT-DIA6-R0-07/08: evolution kind is closed structural vocabulary.
def test_evolution_kind_closed_structural_vocabulary():
    policy = _policy()
    parent = ContextLineageNode.from_context(_context(b"parent"))
    child = ContextLineageNode.from_context(_context(b"child"))
    for bad in ("relationship_breakthrough", "emotional_significance", "memory_worthy"):
        with pytest.raises(ValueError, match="ContextEvolutionKind"):
            ContextEvolutionOperation("op-bad", bad, parent, child, policy.revision, policy.policy_fingerprint(), _authority(), (_ref("evt_reason"),))


# AT-DIA6-R0-09: policy revision binds complete evolution semantics.
def test_policy_fingerprint_binds_complete_evolution_semantics():
    base = _policy(revision="evo-v1", max_reason_refs=4)
    changed_bound = _policy(revision="evo-v1", max_reason_refs=5)
    changed_kinds = _policy(revision="evo-v1", allowed=(ContextEvolutionKind.FACT_APPEND,), max_reason_refs=4)
    assert base.policy_fingerprint() != changed_bound.policy_fingerprint()
    assert base.policy_fingerprint() != changed_kinds.policy_fingerprint()
    with pytest.raises(ValueError, match="parent_verification_revision"):
        ContextEvolutionPolicy("evo-v1", (ContextEvolutionKind.FACT_APPEND,), 4, parent_verification_revision="dia6-parent-v2")
    with pytest.raises(ValueError, match="child_validation_revision"):
        ContextEvolutionPolicy("evo-v1", (ContextEvolutionKind.FACT_APPEND,), 4, child_validation_revision="dia6-child-v2")
    with pytest.raises(ValueError, match="lineage_digest_algorithm_revision"):
        ContextEvolutionPolicy("evo-v1", (ContextEvolutionKind.FACT_APPEND,), 4, lineage_digest_algorithm_revision="dia6-lineage-v2")


# AT-DIA6-R0-11/12: parent/child node digest fields are strict SHA-256 identity fields.
def test_parent_child_node_digest_fields_fail_closed():
    context = _context()
    with pytest.raises(ValueError, match="context_digest"):
        ContextLineageNode("not-a-digest", CONTEXT_VERSION, context.assembly_policy_revision, context.assembly_policy_fingerprint, sha256(context.semantic_canonical_bytes()).hexdigest())
    with pytest.raises(ValueError, match="context_semantic_bytes_sha256"):
        ContextLineageNode(context.context_digest or "", CONTEXT_VERSION, context.assembly_policy_revision, context.assembly_policy_fingerprint, "not-a-digest")


# AT-DIA6-R0-13/14/15: reason refs are canonical, bounded, and duplicate-free.
def test_reason_refs_canonical_bounded_and_duplicate_free():
    policy = _policy(max_reason_refs=1)
    with pytest.raises(ValueError, match="exceed"):
        StrictContextEvolutionValidator().validate(_operation(policy=policy, reason_refs=(_ref("evt_1"), _ref("evt_2"))), policy)
    with pytest.raises(ValueError, match="duplicate"):
        _operation(reason_refs=(_ref("evt_1"), _ref("evt_1")))
    with pytest.raises(ValueError, match="TriggerSourceRef"):
        _operation(reason_refs=("evt_1",))


# AT-DIA6-R0-16: audit diagnostics do not affect lineage digest.
def test_audit_diagnostics_do_not_affect_lineage_digest():
    policy = _policy()
    edge = StrictContextEvolutionValidator().validate(_operation(policy=policy), policy)
    audit_a = ContextEvolutionAudit("operation-1", edge.lineage_digest or "", ("adapter A",), "2026-08-17T00:00:00Z")
    audit_b = ContextEvolutionAudit("operation-1", edge.lineage_digest or "", ("adapter B", "diagnostic"), "2026-08-17T00:01:00Z")
    assert audit_a.lineage_digest == audit_b.lineage_digest == edge.lineage_digest


# AT-DIA6-R0-17/18: Core has no external authority imports; transport receipt cannot create evolution alone.
def test_context_evolution_core_static_authority_boundary():
    import pathlib

    root = pathlib.Path(__file__).parents[2] / "julia_core" / "context_evolution"
    src = "\n".join(path.read_text() for path in sorted(root.glob("*.py")))
    forbidden = ["from julia_core.diary", "import julia_core.diary", "from julia_core.memory", "import julia_core.memory", "from julia_core.context_os", "import julia_core.context_os", "open(", "os.", "pathlib", "fsync", "mkdir", "openai", "llm", "generate"]
    lowered = src.lower()
    for marker in forbidden:
        assert marker not in lowered
    with pytest.raises(ValueError, match="ContextEvolutionOperation"):
        StrictContextEvolutionValidator().validate("transport-receipt-only", _policy())  # type: ignore[arg-type]


# AT-DIA6-R0-19/20: merge/split reserved vocabulary fails closed in single-parent/single-child R1.
def test_merge_split_reserved_but_unsupported_in_r1():
    for kind in (ContextEvolutionKind.CONTEXT_MERGE, ContextEvolutionKind.CONTEXT_SPLIT):
        policy = _policy(allowed=(kind,))
        with pytest.raises(ValueError, match="merge/split"):
            StrictContextEvolutionValidator().validate(_operation(kind, policy=policy), policy)


# Edge id/digest are deterministic and fail closed on caller-supplied mismatch.
def test_lineage_edge_id_and_digest_fail_closed_on_mismatch():
    policy = _policy()
    edge = StrictContextEvolutionValidator().validate(_operation(policy=policy), policy)
    with pytest.raises(ValueError, match="edge_id"):
        ContextLineageEdge(edge.parent_context_digest, edge.child_context_digest, edge.operation_id, edge.operation_kind, edge.evolution_policy_revision, edge.evolution_policy_fingerprint, edge_id="0" * 64)
    with pytest.raises(ValueError, match="lineage_digest"):
        ContextLineageEdge(edge.parent_context_digest, edge.child_context_digest, edge.operation_id, edge.operation_kind, edge.evolution_policy_revision, edge.evolution_policy_fingerprint, lineage_digest="0" * 64)


# Golden vectors freeze policy and lineage canonical algorithms.
def test_dia6_golden_vectors():
    policy = _policy()
    edge = StrictContextEvolutionValidator().validate(_operation(policy=policy), policy)
    assert policy.policy_fingerprint() == GOLDEN_POLICY_FINGERPRINT
    assert edge.lineage_digest == GOLDEN_LINEAGE_DIGEST

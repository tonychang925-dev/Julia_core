"""DIA-4 R1 — Reflection Context Core Contract tests."""
from __future__ import annotations

from datetime import timedelta
from hashlib import sha256

import pytest

from julia_core.reflection_context import (
    CANONICAL_VERSION as CONTEXT_VERSION,
    CONTEXT_DIGEST_ALGORITHM_REVISION,
    DEFAULT_FACT_PROJECTION_REVISION,
    CanonicalFact,
    ContextAssemblyPolicy,
    ContextBounds,
    ContextFact,
    DeterministicReflectionContextAssembler,
    FactAuditMetadata,
    FactSemanticProvenance,
    ReflectionContext,
    ReflectionContextAudit,
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


def _trigger_policy():
    return TriggerPolicy("policy-dia4", timedelta(seconds=0), timedelta(seconds=60), timedelta(seconds=30))


def _ref(event_id="evt_A"):
    return TriggerSourceRef("event", event_id)


def _opportunity(*refs):
    refs = refs or (_ref("evt_A"),)
    key = OpportunityKey(TRIGGER_VERSION, "conv_A", _trigger_policy().revision, TriggerKind.TURN_BOUNDARY, SingleEventAnchor(refs[0].opaque_ref))
    return ReflectionOpportunity(key, tuple(refs), (TriggerReason(TriggerKind.TURN_BOUNDARY, (refs[0],)),))


def _handoff(opportunity=None):
    opportunity = opportunity or _opportunity()
    return ReflectionOpportunityHandoff(opportunity, "pending-digest-1", "dia3-handoff")


def _fact(ref=None, payload=b"canonical event payload", *, reader="reader-A", projection=DEFAULT_FACT_PROJECTION_REVISION):
    ref = ref or _ref("evt_A")
    return CanonicalFact(
        source_ref=ref,
        fact_type="conversation_event",
        source_schema_version="conversation-event-v1",
        projection_revision=projection,
        canonical_payload=payload,
        reader_authority=reader,
    )


class _Reader:
    def __init__(self, facts):
        self.facts = {fact.source_ref.canonical_key(): fact for fact in facts}

    def get_fact(self, ref):
        return self.facts.get(ref.canonical_key())


def _policy(max_facts=4, max_payload_bytes=1024, max_fact_payload_bytes=512, *, revision="ctx-policy-v1", digest_alg=CONTEXT_DIGEST_ALGORITHM_REVISION):
    return ContextAssemblyPolicy(
        revision=revision,
        bounds=ContextBounds(max_facts, max_payload_bytes, max_fact_payload_bytes),
        context_digest_algorithm_revision=digest_alg,
    )


def _assemble(opportunity=None, facts=None, policy=None):
    opportunity = opportunity or _opportunity()
    facts = (_fact(opportunity.source_refs[0]),) if facts is None else facts
    return DeterministicReflectionContextAssembler().assemble(_handoff(opportunity), _Reader(facts), policy or _policy())


# AT-DIA4-R0-01 / R0.1-01: production assembly requires DIA-3 handoff provenance.
def test_valid_looking_opportunity_requires_handoff_provenance():
    opp = _opportunity()
    with pytest.raises(ValueError, match="Handoff"):
        DeterministicReflectionContextAssembler().assemble(opp, _Reader((_fact(),)), _policy())  # type: ignore[arg-type]


# AT-DIA4-R0-02/03/04: Core contract has reader port only; no forbidden authorities.
def test_reflection_context_core_static_authority_boundary():
    import pathlib

    root = pathlib.Path(__file__).parents[2] / "julia_core" / "reflection_context"
    src = "\n".join(path.read_text() for path in sorted(root.glob("*.py")))
    forbidden = ["from julia_core.diary", "import julia_core.diary", "from julia_core.memory", "import julia_core.memory", "from julia_core.context_os", "import julia_core.context_os", "from julia_core.client", "import julia_core.client", "open(", "os.", "pathlib", "fsync", "mkdir"]
    lowered = src.lower()
    for marker in forbidden:
        assert marker not in lowered


# AT-DIA4-R0-05/14: selected refs are opportunity.source_refs order, not lexical order.
def test_context_preserves_opportunity_source_ref_order():
    ref_b = _ref("evt_B")
    ref_a = _ref("evt_A")
    opp = _opportunity(ref_b, ref_a)
    context = _assemble(opp, (_fact(ref_b, b"B"), _fact(ref_a, b"A")))
    assert [fact.source_ref.opaque_ref for fact in context.facts] == ["evt_B", "evt_A"]


# AT-DIA4-R0-06/07/08: no out-of-opportunity successor/extra reads.
def test_assembler_reads_only_opportunity_source_refs():
    ref_a = _ref("evt_A")
    ref_later = _ref("evt_Z_later")
    opp = _opportunity(ref_a)
    context = _assemble(opp, (_fact(ref_a, b"A"), _fact(ref_later, b"later")))
    assert [fact.source_ref.opaque_ref for fact in context.facts] == ["evt_A"]


# AT-DIA4-R0-09: missing source ref fails closed.
def test_missing_source_ref_fails_closed():
    with pytest.raises(ValueError, match="missing canonical fact"):
        _assemble(_opportunity(_ref("evt_A")), facts=())


# AT-DIA4-R0-10: digest mismatch fails closed.
def test_canonical_fact_digest_mismatch_fails_closed():
    with pytest.raises(ValueError, match="digest"):
        CanonicalFact(_ref(), "conversation_event", "schema-v1", DEFAULT_FACT_PROJECTION_REVISION, b"payload", canonical_digest="bad")


# AT-DIA4-R0-11: contradictory same-source facts fail closed by digest validation at construction.
def test_context_fact_provenance_mismatch_fails_closed():
    fact = _fact(payload=b"payload")
    wrong = FactSemanticProvenance(fact.source_ref, fact.source_schema_version, fact.projection_revision, fact.digest_function, sha256(b"other").hexdigest())
    with pytest.raises(ValueError, match="semantic provenance"):
        ContextFact(fact.source_ref, fact.canonical_digest, fact.digest_function, fact.fact_type, fact.source_schema_version, fact.projection_revision, fact.canonical_payload, wrong)


# AT-DIA4-R0-12/16: bounds fail closed; no truncation/summarization.
def test_oversized_payload_fails_closed_without_truncation():
    ref = _ref("evt_A")
    fact = _fact(ref, b"x" * 6)
    with pytest.raises(ValueError, match="exceeds max_fact_payload_bytes"):
        _assemble(_opportunity(ref), (fact,), _policy(max_fact_payload_bytes=5))


# AT-DIA4-R0-13: deterministic digest for same opportunity and same facts.
def test_context_digest_deterministic_for_same_inputs():
    first = _assemble()
    second = _assemble()
    assert first.context_digest == second.context_digest
    assert first.semantic_canonical_bytes() == second.semantic_canonical_bytes()


# AT-DIA4-R0-15: duplicate refs fail closed; never dedupe.
def test_duplicate_refs_fail_closed():
    ref = _ref("evt_A")
    with pytest.raises(ValueError):
        _opportunity(ref, ref)


# AT-DIA4-R0-17/18/19: interpretation labels are impossible in metadata fields.
def test_interpretation_firewall_rejects_semantic_labels():
    with pytest.raises(ValueError, match="interpretation"):
        CanonicalFact(_ref(), "relationship_breakthrough", "schema-v1", DEFAULT_FACT_PROJECTION_REVISION, b"payload")


# AT-DIA4-R0-20 / R0.2-01 / R0.3-01: audit reader label is sidecar only; semantic bytes unchanged.
def test_audit_metadata_excluded_from_context_digest_and_model_visible_bytes():
    ref = _ref("evt_A")
    context_a = _assemble(_opportunity(ref), (_fact(ref, b"same", reader="reader-A"),))
    context_b = _assemble(_opportunity(ref), (_fact(ref, b"same", reader="reader-B"),))
    assert context_a.context_digest == context_b.context_digest
    assert context_a.semantic_canonical_bytes() == context_b.semantic_canonical_bytes()

    audit = ReflectionContextAudit(context_a.opportunity_id, context_a.context_digest, (FactAuditMetadata(ref, "reader-A", "adapter-A", ("diagnostic text",)),))
    assert audit.fact_audit_metadata[0].reader_authority == "reader-A"
    assert b"reader-A" not in context_a.semantic_canonical_bytes()
    assert b"diagnostic" not in context_a.semantic_canonical_bytes()


# AT-DIA4-R0-21 / R0.1-02: context digest binds opportunity id and fact digest.
def test_context_digest_binds_opportunity_and_canonical_fact_digest():
    ref = _ref("evt_A")
    ctx_a = _assemble(_opportunity(ref), (_fact(ref, b"same"),))
    opp_b = _opportunity(TriggerSourceRef("event", "evt_B"))
    ctx_b = _assemble(opp_b, (_fact(opp_b.source_refs[0], b"same"),))
    ctx_changed_payload = _assemble(_opportunity(ref), (_fact(ref, b"changed"),))
    assert ctx_a.context_digest != ctx_b.context_digest
    assert ctx_a.context_digest != ctx_changed_payload.context_digest


# AT-DIA4-R0.1-03: bounds enter context digest.
def test_context_digest_binds_exact_bounds():
    ref = _ref("evt_A")
    ctx_a = _assemble(_opportunity(ref), (_fact(ref, b"same"),), _policy(max_payload_bytes=100))
    ctx_b = _assemble(_opportunity(ref), (_fact(ref, b"same"),), _policy(max_payload_bytes=101))
    assert ctx_a.context_digest != ctx_b.context_digest


# AT-DIA4-R0.1-04 / R0.3-03: policy fingerprint binds complete semantics including digest algorithm.
def test_policy_fingerprint_binds_complete_semantics():
    a = _policy(digest_alg="dia4-context-digest-v1")
    b = _policy(digest_alg="dia4-context-digest-v2")
    assert a.policy_fingerprint() != b.policy_fingerprint()


# AT-DIA4-R0.1-05 / R0.1-P1: CanonicalFact is context-free exact payload.
def test_context_fact_exact_copy_from_canonical_fact():
    fact = _fact(payload=b"exact bytes")
    context_fact = ContextFact.from_canonical_fact(fact)
    assert context_fact.payload == fact.canonical_payload
    assert context_fact.source_ref == fact.source_ref
    assert context_fact.canonical_digest == fact.canonical_digest
    assert context_fact.source_schema_version == fact.source_schema_version
    assert context_fact.projection_revision == fact.projection_revision


# AT-DIA4-R0.2-04: Core has policy fingerprint only, no durable binding storage.
def test_policy_core_has_no_physical_binding_storage():
    assert _policy().policy_fingerprint() == _policy().policy_fingerprint()
    import pathlib

    src = (pathlib.Path(__file__).parents[2] / "julia_core" / "reflection_context" / "models.py").read_text()
    for marker in ("open(", "os.", "pathlib", "mkdir", "fsync", "replace"):
        assert marker not in src


# Golden vectors freeze canonical algorithms.
def test_dia4_golden_vectors():
    ref = _ref("evt_A")
    policy = _policy(max_facts=4, max_payload_bytes=1024, max_fact_payload_bytes=512)
    fact = _fact(ref, b"canonical event payload")
    context = _assemble(_opportunity(ref), (fact,), policy)

    assert policy.policy_fingerprint() == "1e2ad176a764ef0447422a60e1a469aeb2a7fb8d305664dffabf102c2c4e4f86"
    assert fact.canonical_digest == "7c487cbcd022b34aa379dc38eeb21c5e082528b8b1981bcb8de53723a007a81c"
    assert context.context_digest == "a4c50641dfa07563e51819862405e652a829455392d48ab019b2f25f08c63b97"

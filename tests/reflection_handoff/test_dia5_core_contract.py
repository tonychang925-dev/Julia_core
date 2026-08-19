"""DIA-5 R1 — Reflection Context Handoff Core Contract tests."""
from __future__ import annotations

from datetime import timedelta
from hashlib import sha256

import pytest

from julia_core.reflection_context import (
    CANONICAL_VERSION as CONTEXT_VERSION,
    DEFAULT_FACT_PROJECTION_REVISION,
    CanonicalFact,
    CanonicalFactType,
    ContextAssemblyPolicy,
    ContextBounds,
    DeterministicReflectionContextAssembler,
    ReflectionContext,
    ReflectionOpportunityHandoff,
)
from julia_core.reflection_handoff import (
    HANDOFF_VERSION,
    HandoffEndpoint,
    HandoffIntegrity,
    HandoffReceipt,
    HandoffReceiptStatus,
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


GOLDEN_CONTEXT_DIGEST = "0b6a3f9b1c7b195c9f00ab40833130bf2452e74cd73c3bcf2a8298cabd9cac9c"
# Filled after canonical algorithm execution and then frozen.
GOLDEN_HANDOFF_SEMANTIC_SHA = "f0e72dda9e1e7e518eff781f6cb33600e123528632cce0100795a79ce93b7e7b"
GOLDEN_HANDOFF_ENVELOPE_DIGEST = "e70dbc86bee5013c8dbf1cbceb744004c42dcfabf0f8daf6c40718329ef0ee02"


def _trigger_policy():
    return TriggerPolicy("policy-dia5", timedelta(seconds=0), timedelta(seconds=60), timedelta(seconds=30))


def _ref(event_id="evt_A"):
    return TriggerSourceRef("event", event_id)


def _opportunity(ref=None):
    ref = ref or _ref("evt_A")
    key = OpportunityKey(
        TRIGGER_VERSION,
        "conv_A",
        _trigger_policy().revision,
        TriggerKind.TURN_BOUNDARY,
        SingleEventAnchor(ref.opaque_ref),
    )
    return ReflectionOpportunity(key, (ref,), (TriggerReason(TriggerKind.TURN_BOUNDARY, (ref,)),))


def _fact(ref=None, payload=b"canonical event payload"):
    ref = ref or _ref("evt_A")
    return CanonicalFact(
        source_ref=ref,
        fact_type=CanonicalFactType.CONVERSATION_EVENT,
        source_schema_version="conversation-event-v1",
        projection_revision=DEFAULT_FACT_PROJECTION_REVISION,
        canonical_payload=payload,
        reader_authority="reader-A",
    )


class _Reader:
    def __init__(self, facts):
        self.facts = {fact.source_ref.canonical_key(): fact for fact in facts}

    def get_fact(self, ref):
        return self.facts.get(ref.canonical_key())


def _policy():
    return ContextAssemblyPolicy(
        revision="ctx-policy-v1",
        bounds=ContextBounds(4, 1024, 512),
    )


def _context(payload=b"canonical event payload"):
    ref = _ref("evt_A")
    opportunity = _opportunity(ref)
    return DeterministicReflectionContextAssembler().assemble(
        ReflectionOpportunityHandoff(opportunity, "pending-digest-1", "dia3-handoff"),
        _Reader((_fact(ref, payload),)),
        _policy(),
    )


def _producer():
    return HandoffEndpoint("dia4-runtime", "producer", "dia5-consumer-protocol-v1")


def _consumer(endpoint_id="dia5-generation"):
    return HandoffEndpoint(endpoint_id, "consumer", "dia5-consumer-protocol-v1")


def _handoff(context=None, *, handoff_id="handoff-1", producer=None, consumer=None, created_at="2026-08-17T00:00:00Z"):
    return ReflectionContextHandoff.from_context(
        handoff_id=handoff_id,
        context=context or _context(),
        producer=producer or _producer(),
        consumer=consumer or _consumer(),
        created_at=created_at,
    )


# AT-DIA5-R1-01: handoff carries DIA-4 context identity and exact semantic bytes.
def test_handoff_carries_context_digest_and_exact_semantic_bytes():
    context = _context()
    handoff = _handoff(context)
    assert handoff.context_version == CONTEXT_VERSION
    assert handoff.context_digest == context.context_digest
    assert handoff.context_semantic_bytes == context.semantic_canonical_bytes()
    assert handoff.integrity.context_digest == context.context_digest
    assert handoff.integrity.semantic_bytes_sha256 == sha256(context.semantic_canonical_bytes()).hexdigest()


# AT-DIA5-R1-02/03: transport integrity rejects semantic bytes or digest mismatch; no repair.
def test_handoff_rejects_semantic_bytes_hash_mismatch():
    context = _context()
    bad_integrity = HandoffIntegrity(
        context_digest=context.context_digest or "",
        semantic_bytes_sha256=sha256(b"tampered").hexdigest(),
    )
    with pytest.raises(ValueError, match="semantic bytes hash mismatch"):
        ReflectionContextHandoff(
            HANDOFF_VERSION,
            "handoff-bad",
            CONTEXT_VERSION,
            context.context_digest or "",
            context.semantic_canonical_bytes(),
            _producer(),
            _consumer(),
            "2026-08-17T00:00:00Z",
            bad_integrity,
        )


def test_handoff_rejects_context_digest_mismatch():
    context = _context()
    integrity = HandoffIntegrity.from_context(context)
    with pytest.raises(ValueError, match="context_digest mismatch"):
        ReflectionContextHandoff(
            HANDOFF_VERSION,
            "handoff-bad",
            CONTEXT_VERSION,
            "0" * 64,
            context.semantic_canonical_bytes(),
            _producer(),
            _consumer(),
            "2026-08-17T00:00:00Z",
            integrity,
        )


# AT-DIA5-R1-04: handoff identity is transport identity, not context identity.
def test_same_context_can_have_distinct_handoff_envelopes_without_context_identity_change():
    context = _context()
    first = _handoff(context, handoff_id="handoff-1", created_at="2026-08-17T00:00:00Z")
    second = _handoff(context, handoff_id="handoff-2", created_at="2026-08-17T00:00:01Z")
    assert first.context_digest == second.context_digest == context.context_digest
    assert first.context_semantic_bytes == second.context_semantic_bytes
    assert first.handoff_envelope_digest() != second.handoff_envelope_digest()


# AT-DIA5-R1-05: transport metadata does not change model-visible context bytes.
def test_transport_metadata_excluded_from_context_semantic_bytes():
    context = _context()
    first = _handoff(context, producer=HandoffEndpoint("producer-A", "producer", "p-v1"))
    second = _handoff(context, producer=HandoffEndpoint("producer-B", "producer", "p-v1"))
    assert first.context_semantic_bytes == second.context_semantic_bytes == context.semantic_canonical_bytes()
    assert first.handoff_envelope_digest() != second.handoff_envelope_digest()


# AT-DIA5-R1-06/07/08: version domains are separated and frozen.
def test_unknown_handoff_version_rejected():
    context = _context()
    with pytest.raises(ValueError, match="handoff_version"):
        ReflectionContextHandoff(
            "dia5-reflection-handoff-v2",
            "handoff-bad",
            CONTEXT_VERSION,
            context.context_digest or "",
            context.semantic_canonical_bytes(),
            _producer(),
            _consumer(),
            "2026-08-17T00:00:00Z",
            HandoffIntegrity.from_context(context),
        )


def test_unknown_context_version_rejected():
    context = _context()
    with pytest.raises(ValueError, match="context_version"):
        ReflectionContextHandoff(
            HANDOFF_VERSION,
            "handoff-bad",
            "dia4-reflection-context-v2",
            context.context_digest or "",
            context.semantic_canonical_bytes(),
            _producer(),
            _consumer(),
            "2026-08-17T00:00:00Z",
            HandoffIntegrity.from_context(context),
        )


def test_unknown_integrity_digest_algorithm_rejected():
    with pytest.raises(ValueError, match="digest_algorithm"):
        HandoffIntegrity("a" * 64, "b" * 64, digest_algorithm="sha256:v2")


# AT-DIA5-R1-09/10: consumer validation is fail-closed and consumer-specific.
def test_strict_validator_accepts_intended_consumer():
    handoff = _handoff()
    receipt = StrictReflectionHandoffValidator().validate(handoff, handoff.consumer)
    assert receipt.status is HandoffReceiptStatus.ACCEPTED
    assert receipt.handoff_id == handoff.handoff_id
    assert receipt.context_digest == handoff.context_digest


def test_strict_validator_rejects_wrong_consumer():
    handoff = _handoff()
    with pytest.raises(ValueError, match="consumer mismatch"):
        StrictReflectionHandoffValidator().validate(handoff, _consumer("other-consumer"))


# AT-DIA5-R1-11: boundary objects require exact Core types, not compatible subclasses.
def test_handoff_rejects_endpoint_subclass_spoof():
    class EndpointSubclass(HandoffEndpoint):
        pass

    context = _context()
    with pytest.raises(ValueError, match="producer must be exact HandoffEndpoint"):
        ReflectionContextHandoff(
            HANDOFF_VERSION,
            "handoff-spoof",
            CONTEXT_VERSION,
            context.context_digest or "",
            context.semantic_canonical_bytes(),
            EndpointSubclass("producer", "producer", "p-v1"),
            _consumer(),
            "2026-08-17T00:00:00Z",
            HandoffIntegrity.from_context(context),
        )


def test_validator_rejects_handoff_subclass_spoof():
    class HandoffSubclass(ReflectionContextHandoff):
        pass

    handoff = _handoff()
    spoof = HandoffSubclass(
        handoff.handoff_version,
        handoff.handoff_id,
        handoff.context_version,
        handoff.context_digest,
        handoff.context_semantic_bytes,
        handoff.producer,
        handoff.consumer,
        handoff.created_at,
        handoff.integrity,
    )
    with pytest.raises(ValueError, match="exact ReflectionContextHandoff"):
        StrictReflectionHandoffValidator().validate(spoof, handoff.consumer)


# AT-DIA5-R1-12: bytes-only context payload survives handoff without UTF-8 assumptions.
def test_binary_context_semantic_bytes_handoff_and_validate():
    context = _context(payload=b"\x00\xff\x80:\nA")
    handoff = _handoff(context)
    assert handoff.context_semantic_bytes == context.semantic_canonical_bytes()
    StrictReflectionHandoffValidator().validate(handoff, handoff.consumer)


# AT-DIA5-R1-13: receipts are transport acknowledgements, not semantic repair records.
def test_handoff_receipt_status_invariants():
    consumer = _consumer()
    HandoffReceipt("handoff-1", "a" * 64, consumer, "2026-08-17T00:00:00Z", HandoffReceiptStatus.ACCEPTED)
    with pytest.raises(ValueError, match="must not carry rejection_reason"):
        HandoffReceipt("handoff-1", "a" * 64, consumer, "2026-08-17T00:00:00Z", HandoffReceiptStatus.ACCEPTED, "debug")
    with pytest.raises(ValueError, match="rejection_reason"):
        HandoffReceipt("handoff-1", "a" * 64, consumer, "2026-08-17T00:00:00Z", HandoffReceiptStatus.REJECTED)
    HandoffReceipt("handoff-1", "a" * 64, consumer, "2026-08-17T00:00:00Z", HandoffReceiptStatus.REJECTED, "invalid digest")


# AT-DIA5-R1-14: Core handoff has no Diary/Memory/ContextOS/LLM/generation authority.
def test_reflection_handoff_core_static_authority_boundary():
    import pathlib

    root = pathlib.Path(__file__).parents[2] / "julia_core" / "reflection_handoff"
    src = "\n".join(path.read_text() for path in sorted(root.glob("*.py")))
    forbidden = [
        "from julia_core.diary",
        "import julia_core.diary",
        "from julia_core.memory",
        "import julia_core.memory",
        "from julia_core.context_os",
        "import julia_core.context_os",
        "from julia_core.client",
        "import julia_core.client",
        "open(",
        "os.",
        "pathlib",
        "fsync",
        "mkdir",
        "openai",
        "llm",
        "generate",
    ]
    lowered = src.lower()
    for marker in forbidden:
        assert marker not in lowered


# DIA5-R1 golden vectors freeze handoff integrity and envelope algorithms.
def test_dia5_golden_vectors():
    context = _context()
    handoff = _handoff(context)
    assert context.context_digest == GOLDEN_CONTEXT_DIGEST
    assert handoff.integrity.semantic_bytes_sha256 == GOLDEN_HANDOFF_SEMANTIC_SHA
    assert handoff.handoff_envelope_digest() == GOLDEN_HANDOFF_ENVELOPE_DIGEST

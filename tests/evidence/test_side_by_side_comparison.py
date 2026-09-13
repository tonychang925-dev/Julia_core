from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path

import pytest

from julia_core.alignment_os import ProviderExecutionEnvelope
from julia_core.context_admission import (
    ExactAdmittedSemanticBinder,
    ExclusiveAdmissionGate,
    SemanticBindingRequest,
)
from julia_core.comparison import (
    CanonicalExecutionEvidence,
    ContinuityEvaluationEvidence,
    EvidenceOnlySideBySideComparator,
    ReferenceExecutionEvidence,
    SideBySideComparisonRejected,
)
from julia_core.runtime.assistant_runtime import (
    JuliaAssistantRuntime,
    RuntimeTurnRequest,
)
from tests.context_admission.production_fixtures import canonical_request


SOURCE_PATH = Path("julia_core/comparison.py")


class ReferenceEvidenceSubclass(ReferenceExecutionEvidence):
    pass


class CanonicalEvidenceSubclass(CanonicalExecutionEvidence):
    pass


class EnvelopeSubclass(ProviderExecutionEnvelope):
    pass


def canonical_evidence(
    *,
    execution_status: str | None = "SUCCEEDED",
    output_present: bool | None = True,
    continuity: ContinuityEvaluationEvidence | None = None,
) -> CanonicalExecutionEvidence:
    admission = canonical_request()
    package = ExclusiveAdmissionGate().seal(admission)
    binding = ExactAdmittedSemanticBinder().bind(
        SemanticBindingRequest(
            package,
            admission.identity_frames,
            admission.experience_frames,
            admission.current_task_context,
        )
    )
    envelope = JuliaAssistantRuntime().prepare(
        RuntimeTurnRequest(binding=binding, provider_id="deepseek")
    )
    return CanonicalExecutionEvidence.from_canonical_execution(
        package=package,
        binding=binding,
        envelope=envelope,
        source_ref="fixture://canonical/execution",
        execution_status=execution_status,
        output_present=output_present,
        continuity_evaluation=continuity,
    )


def reference_evidence(
    canonical: CanonicalExecutionEvidence,
    **changes,
) -> ReferenceExecutionEvidence:
    values = {
        "schema_version": "1.0.0",
        "source_ref": "fixture://reference/execution",
        "conversation_id": canonical.conversation_id,
        "turn_id": canonical.turn_id,
        "execution_status": "SUCCEEDED",
        "output_present": True,
        "semantic_fingerprint": canonical.semantic_fingerprint,
        "ordered_unit_digests": canonical.ordered_unit_digests,
        "provider_id": canonical.provider_id,
        "alignment_identity": canonical.alignment_identity,
        "gate_receipt": canonical.gate_receipt,
    }
    values.update(changes)
    return ReferenceExecutionEvidence(**values)


def dimension(record, name):
    return next(item for item in record.dimensions if item.name == name)


def continuity():
    return ContinuityEvaluationEvidence(
        source_ref="fixture://continuity/evaluation",
        evaluation_fields=(
            ("identity_anchor_observed", True),
            ("experience_coverage_observed", True),
        ),
    )


def test_exact_reference_and_canonical_pair_is_accepted() -> None:
    canonical = canonical_evidence()
    record = EvidenceOnlySideBySideComparator().compare(
        reference_evidence(canonical), canonical
    )

    assert record.conversation_id == canonical.conversation_id
    assert record.turn_id == canonical.turn_id
    assert dimension(record, "correlation_identity").equal is True


def test_external_correlation_id_is_evidence_only() -> None:
    canonical = canonical_evidence()
    record = EvidenceOnlySideBySideComparator().compare(
        reference_evidence(canonical),
        canonical,
        external_correlation_id="p4-b1-pair-001",
    )

    assert record.external_correlation_id == "p4-b1-pair-001"
    assert dimension(record, "correlation_identity").equal is True


def test_semantic_fingerprint_equality_and_difference_are_evidence() -> None:
    canonical = canonical_evidence()
    equal = EvidenceOnlySideBySideComparator().compare(
        reference_evidence(canonical), canonical
    )
    changed = EvidenceOnlySideBySideComparator().compare(
        reference_evidence(canonical, semantic_fingerprint="a" * 64), canonical
    )

    assert dimension(equal, "semantic_fingerprint").equal is True
    assert dimension(changed, "semantic_fingerprint").equal is False


def test_exact_message_unit_order_difference_is_evidence_only() -> None:
    canonical = canonical_evidence()
    reordered = reference_evidence(
        canonical,
        ordered_unit_digests=tuple(reversed(canonical.ordered_unit_digests)),
    )
    record = EvidenceOnlySideBySideComparator().compare(reordered, canonical)

    assert dimension(record, "message_unit_order").equal is False


def test_provider_alignment_and_gate_identity_are_recorded() -> None:
    canonical = canonical_evidence()
    record = EvidenceOnlySideBySideComparator().compare(
        reference_evidence(canonical), canonical
    )

    assert dimension(record, "provider_identity").equal is True
    assert dimension(record, "alignment_identity").equal is True
    assert dimension(record, "gate_receipt").equal is True


def test_output_presence_and_status_are_recorded_for_both_sides() -> None:
    canonical = canonical_evidence()
    reference = reference_evidence(
        canonical,
        execution_status="FAILED",
        output_present=False,
    )
    record = EvidenceOnlySideBySideComparator().compare(reference, canonical)
    output = dimension(record, "output_execution")

    assert output.reference_available is True
    assert output.canonical_available is True
    assert output.equal is False


def test_missing_canonical_output_evidence_remains_unavailable() -> None:
    canonical = canonical_evidence(execution_status=None, output_present=None)
    record = EvidenceOnlySideBySideComparator().compare(
        reference_evidence(canonical), canonical
    )
    output = dimension(record, "output_execution")

    assert output.canonical_available is False
    assert output.equal is None


def test_continuity_evaluation_fields_preserve_explicit_provenance() -> None:
    canonical_continuity = continuity()
    reference_continuity = ContinuityEvaluationEvidence(
        source_ref="fixture://continuity/reference",
        evaluation_fields=(("relationship_role_observed", True),),
    )
    canonical = canonical_evidence(continuity=canonical_continuity)
    reference = reference_evidence(
        canonical, continuity_evaluation=reference_continuity
    )
    record = EvidenceOnlySideBySideComparator().compare(reference, canonical)

    assert tuple(binding.evidence_side for binding in record.continuity_bindings) == (
        "reference",
        "canonical",
    )
    assert record.continuity_bindings[0].source_ref == reference_continuity.source_ref
    assert record.continuity_bindings[0].fields_digest == reference_continuity.digest()
    assert record.continuity_bindings[1].source_ref == canonical_continuity.source_ref
    assert record.continuity_bindings[1].fields_digest == canonical_continuity.digest()
    assert all(
        binding.comparison_provenance == record.comparison_provenance
        for binding in record.continuity_bindings
    )


def test_identical_paired_evidence_has_identical_replay_digest() -> None:
    canonical = canonical_evidence(continuity=continuity())
    reference = reference_evidence(canonical, continuity_evaluation=continuity())
    first = EvidenceOnlySideBySideComparator().compare(reference, canonical)
    second = EvidenceOnlySideBySideComparator().compare(reference, canonical)

    assert first.digest() == second.digest()
    assert first.canonical_serialization() == second.canonical_serialization()


@pytest.mark.parametrize(
    ("reference_change", "canonical_change"),
    [
        ({"semantic_fingerprint": "a" * 64}, {}),
        ({"provider_id": "codex"}, {}),
        ({"execution_status": "FAILED"}, {"execution_status": "ERROR"}),
    ],
)
def test_material_evidence_change_changes_replay_digest(
    reference_change, canonical_change
) -> None:
    canonical = canonical_evidence()
    first = EvidenceOnlySideBySideComparator().compare(
        reference_evidence(canonical), canonical
    )
    changed_reference = reference_evidence(canonical, **reference_change)
    changed_canonical = replace(canonical, **canonical_change)
    second = EvidenceOnlySideBySideComparator().compare(
        changed_reference, changed_canonical
    )

    assert first.digest() != second.digest()


def test_conversation_and_turn_mismatch_fail_closed() -> None:
    canonical = canonical_evidence()
    conversation_mismatch = reference_evidence(
        canonical,
        conversation_id="conversation-other",
    )
    turn_mismatch = reference_evidence(canonical, turn_id="turn-other")
    comparator = EvidenceOnlySideBySideComparator()

    with pytest.raises(SideBySideComparisonRejected, match="correlation"):
        comparator.compare(conversation_mismatch, canonical)
    with pytest.raises(SideBySideComparisonRejected, match="correlation"):
        comparator.compare(turn_mismatch, canonical)


def test_malformed_reference_and_canonical_evidence_rejected() -> None:
    canonical = canonical_evidence()

    with pytest.raises(TypeError, match="conversation_id"):
        reference_evidence(canonical, conversation_id="")
    with pytest.raises(TypeError, match="semantic_fingerprint"):
        replace(canonical, semantic_fingerprint="not-a-digest")


@pytest.mark.parametrize(
    ("reference_change", "message"),
    [
        ({"conversation_id": None}, "conversation_id"),
        ({"turn_id": None}, "turn_id"),
        ({"execution_status": "COMPLETE"}, "execution_status"),
        ({"output_present": "true"}, "output_present"),
        ({"ordered_unit_digests": ["a" * 64]}, "ordered_unit_digests"),
    ],
)
def test_missing_or_ambiguous_correlation_and_execution_rejected(
    reference_change, message
) -> None:
    canonical = canonical_evidence()
    with pytest.raises(TypeError, match=message):
        reference_evidence(canonical, **reference_change)


def test_exact_types_are_required_and_subclasses_rejected() -> None:
    canonical = canonical_evidence()
    reference = ReferenceEvidenceSubclass(
        **{
            field.name: getattr(reference_evidence(canonical), field.name)
            for field in fields(ReferenceExecutionEvidence)
        }
    )
    canonical_subclass = CanonicalEvidenceSubclass(
        **{
            field.name: getattr(canonical, field.name)
            for field in fields(CanonicalExecutionEvidence)
        }
    )

    with pytest.raises(TypeError, match="inexact"):
        EvidenceOnlySideBySideComparator().compare(reference, canonical)
    with pytest.raises(TypeError, match="inexact"):
        EvidenceOnlySideBySideComparator().compare(
            reference_evidence(canonical), canonical_subclass
        )


def test_caller_cannot_inject_choice_or_switch_fields() -> None:
    all_fields = {
        field.name
        for dataclass in (
            ReferenceExecutionEvidence,
            CanonicalExecutionEvidence,
            ContinuityEvaluationEvidence,
        )
        for field in fields(dataclass)
    }

    assert not all_fields & {
        "winner",
        "preferred",
        "selected",
        "selected_response",
        "switch",
        "provider_switch_ready",
        "routing",
    }
    with pytest.raises(TypeError):
        reference_evidence(canonical_evidence(), winner="reference")


def test_comparator_constructs_no_semantic_or_authority_objects() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "IdentityFrame" not in source
    assert "ExperienceFrameSet" not in source
    assert "get_llm_provider" not in source
    assert "ProviderAlignmentBoundary" not in source
    assert "winner" not in source
    assert "preferred" not in source
    assert "selected" not in source
    assert "switch" not in source
    assert "routing" not in source


def test_envelope_evidence_can_only_derive_from_exact_canonical_chain() -> None:
    admission = canonical_request()
    package = ExclusiveAdmissionGate().seal(admission)
    binding = ExactAdmittedSemanticBinder().bind(
        SemanticBindingRequest(
            package,
            admission.identity_frames,
            admission.experience_frames,
            admission.current_task_context,
        )
    )

    with pytest.raises(TypeError, match="exact execution envelope"):
        CanonicalExecutionEvidence.from_canonical_execution(
            package=package,
            binding=binding,
            envelope=object.__new__(EnvelopeSubclass),
            source_ref="fixture://invalid",
        )

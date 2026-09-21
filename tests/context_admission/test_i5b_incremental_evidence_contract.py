from __future__ import annotations

from dataclasses import fields
from hashlib import sha256

import pytest

from julia_core.alignment_os.adapter import ProviderAlignmentBoundary
from julia_core.alignment_os.contracts import (
    ProviderExecutionEnvelope,
    ProviderExecutionEnvelopeV2,
)
from julia_core.capability.models import (
    CapabilityCall,
    CapabilityCallStatus,
    Evidence,
    EvidenceSourceType,
    SideEffectState,
    ToolResult,
    ToolResultStatus,
)
from julia_core.context_admission import C03AdmissionRejected
from julia_core.context_admission.contracts import canonical_json
from julia_core.context_admission.incremental_evidence import (
    MAX_INCREMENTAL_EVIDENCE_CANONICAL_BYTES,
    AdmittedIncrementalEvidenceBundle,
    CapabilityEvidenceSource,
    ExactAdmittedIncrementalEvidenceBinder,
    IncrementalEvidenceAdmissionGate,
    IncrementalEvidenceAdmissionRequest,
    SealedIncrementalEvidencePackage,
    canonical_evidence,
    canonical_tool_result,
)
from tests.context_admission.test_p3_n0_semantic_binding import bound_bundle


def evidence(index: int, **overrides) -> Evidence:
    values = {
        "evidence_id": f"evidence-{index}",
        "source_type": EvidenceSourceType.TOOL_OBSERVATION,
        "source_ref": f"source-{index}",
        "observed_at": "2026-09-21T00:00:00Z",
        "content_ref": f"content-{index}",
        "provenance": {"capability_call_id": f"call-{index}"},
        "integrity_metadata": {"sha256": "a" * 64},
        "freshness": "current",
        "confidence": 0.9,
        "correlation_id": "correlation-1",
        "retrieved_at": "2026-09-21T00:00:01Z",
    }
    values.update(overrides)
    return Evidence(**values)


def source(
    index: int, *, pass_index: int = 1, structured_output=None
) -> CapabilityEvidenceSource:
    structured_output = (
        structured_output
        if structured_output is not None
        else {
            "value": index,
            "nested": {"items": [index, {"exact": True}]},
        }
    )
    return CapabilityEvidenceSource(
        turn_id="turn-eng12a-1",
        generation_id=f"generation-{pass_index}",
        pass_index=pass_index,
        capability_call=CapabilityCall(
            capability_call_id=f"call-{index}",
            capability_request_id=f"request-{index}",
            status=CapabilityCallStatus.COMPLETED,
            started_at="2026-09-21T00:00:00Z",
            completed_at="2026-09-21T00:00:01Z",
            provider="market",
            correlation_id="correlation-1",
            provenance={"authority": "capability_manager"},
        ),
        tool_result=ToolResult(
            capability_call_id=f"call-{index}",
            status=ToolResultStatus.PARTIAL,
            structured_output=structured_output,
            error=None,
            started_at="2026-09-21T00:00:00Z",
            completed_at="2026-09-21T00:00:01Z",
            side_effect_state=SideEffectState.NONE,
            evidence_refs=(f"evidence-{index}",),
            provider="market",
            schema_version="1.0",
        ),
        evidence=(evidence(index),),
    )


def request(entries: tuple[CapabilityEvidenceSource, ...] | None = None):
    return IncrementalEvidenceAdmissionRequest(
        conversation_id="conversation-eng12a",
        turn_id="turn-eng12a-1",
        entries=entries or (source(1),),
    )


def sealed(entries: tuple[CapabilityEvidenceSource, ...] | None = None):
    return IncrementalEvidenceAdmissionGate().seal(request(entries))


def admitted(entries: tuple[CapabilityEvidenceSource, ...] | None = None):
    exact_request = request(entries)
    package = IncrementalEvidenceAdmissionGate().seal(exact_request)
    return ExactAdmittedIncrementalEvidenceBinder().bind(package, exact_request)


def rejection_code(func, *args, **kwargs) -> str:
    with pytest.raises(C03AdmissionRejected) as caught:
        func(*args, **kwargs)
    return caught.value.rejection.code


def test_i5b_01_exact_source_seals_and_binds():
    package = sealed()
    bundle = ExactAdmittedIncrementalEvidenceBinder().bind(package, request())

    assert package.ordered_entry_digests == (bundle.units[0].entry_digest,)
    assert bundle.units[0].capability_call_id == "call-1"
    assert bundle.units[0].tool_result_digest == source(1).digests()[1]
    assert package.canonical_byte_count > 0
    assert bundle.units[0].canonical_content == canonical_json(source(1).to_payload())
    assert (
        bundle.semantic_fingerprint()
        == sha256(bundle.canonical_content().encode("utf-8")).hexdigest()
    )


def test_i5b_02_six_ordered_entries_are_accepted():
    entries = tuple(source(index, pass_index=index) for index in range(1, 7))
    package = sealed(entries)

    assert package.ordered_pass_indexes == (1, 2, 3, 4, 5, 6)
    assert package.evidence_object_count == 6
    assert ExactAdmittedIncrementalEvidenceBinder().bind(package, request(entries))


def test_i5b_03_seventh_entry_exceeds_execution_budget():
    entries = [source(index, pass_index=index) for index in range(1, 7)]
    entries.append(source(7, pass_index=6))
    object.__setattr__(entries[-1], "pass_index", 7)
    entries = tuple(entries)

    assert rejection_code(
        IncrementalEvidenceAdmissionGate().seal, request(entries)
    ) == ("context_evidence_budget_exceeded")


def test_i5b_04_more_than_sixty_four_evidence_objects_rejected():
    evidence_items = tuple(
        evidence(
            1000 + index,
            provenance={"capability_call_id": "call-1"},
            correlation_id="",
        )
        for index in range(65)
    )
    item = source(1)
    object.__setattr__(
        item.tool_result,
        "evidence_refs",
        tuple(item.evidence_id for item in evidence_items),
    )
    entry = CapabilityEvidenceSource(
        turn_id=item.turn_id,
        generation_id=item.generation_id,
        pass_index=1,
        capability_call=item.capability_call,
        tool_result=item.tool_result,
        evidence=evidence_items,
    )
    entries = (entry,)

    assert rejection_code(
        IncrementalEvidenceAdmissionGate().seal, request(entries)
    ) == ("context_evidence_budget_exceeded")


def test_i5b_05_canonical_bytes_exceed_budget_without_truncation():
    large = source(1, structured_output={"payload": "x" * 65536})

    assert rejection_code(
        IncrementalEvidenceAdmissionGate().seal, request((large,))
    ) == ("context_evidence_budget_exceeded")
    assert len(canonical_json(large.to_payload()).encode("utf-8")) > (
        MAX_INCREMENTAL_EVIDENCE_CANONICAL_BYTES
    )


def test_i5b_06_call_result_ids_must_match():
    item = source(1)
    object.__setattr__(item.tool_result, "capability_call_id", "other-call")

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == "capability_call_id_mismatch"
    )


@pytest.mark.parametrize(
    ("refs", "expected"),
    [
        ((), "evidence_refs_mismatch"),
        (("evidence-1", "extra-evidence"), "evidence_refs_mismatch"),
        (("nonexistent",), "evidence_refs_mismatch"),
    ],
)
def test_i5b_07_evidence_refs_must_be_exact_ordered_complete(refs, expected):
    item = source(1)
    object.__setattr__(item.tool_result, "evidence_refs", refs)

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == expected
    )


def test_i5b_08_duplicate_evidence_id_rejected():
    first = source(1, pass_index=1)
    second_call = CapabilityCall(
        capability_call_id="call-2",
        capability_request_id="request-2",
        status=CapabilityCallStatus.COMPLETED,
        provider="market",
        correlation_id="correlation-1",
    )
    second_result = ToolResult(
        capability_call_id="call-2",
        status=ToolResultStatus.SUCCESS,
        evidence_refs=("evidence-1",),
        provider="market",
    )
    second = CapabilityEvidenceSource(
        turn_id=first.turn_id,
        generation_id="generation-2",
        pass_index=2,
        capability_call=second_call,
        tool_result=second_result,
        evidence=(evidence(1, provenance={"capability_call_id": "call-2"}),),
    )

    assert (
        rejection_code(
            IncrementalEvidenceAdmissionGate().seal,
            request((first, second)),
        )
        == "duplicate_evidence_id"
    )


def test_i5b_09_duplicate_capability_call_id_rejected():
    entries = (source(1, pass_index=1), source(1, pass_index=2))

    assert rejection_code(
        IncrementalEvidenceAdmissionGate().seal, request(entries)
    ) == ("duplicate_capability_call_id")


@pytest.mark.parametrize("status", list(CapabilityCallStatus)[:3])
def test_i5b_10_non_terminal_call_rejected(status):
    item = source(1)
    object.__setattr__(item.capability_call, "status", status)

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == "non_terminal_capability_call"
    )


def test_i5b_11_provider_mismatch_rejected():
    item = source(1)
    object.__setattr__(item.capability_call, "provider", "market")
    object.__setattr__(item.tool_result, "provider", "research")

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == "capability_provider_mismatch"
    )


def test_i5b_12_evidence_provenance_call_id_mismatch_rejected():
    item = source(1)
    object.__setattr__(
        item.evidence[0],
        "provenance",
        {"capability_call_id": "other-call"},
    )

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == "evidence_provenance_mismatch"
    )


def test_i5b_13_correlation_mismatch_rejected_when_both_present():
    item = source(1)
    object.__setattr__(item.evidence[0], "correlation_id", "other-correlation")

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == "evidence_correlation_mismatch"
    )


def test_i5b_14_post_seal_structured_output_mutation_rejected():
    exact_request = request()
    package = IncrementalEvidenceAdmissionGate().seal(exact_request)
    exact_request.entries[0].tool_result.structured_output["payload"] = "mutated"

    assert (
        rejection_code(
            ExactAdmittedIncrementalEvidenceBinder().bind, package, exact_request
        )
        == "post_seal_incremental_evidence_mutation"
    )


def test_i5b_15_post_seal_evidence_provenance_mutation_rejected():
    exact_request = request()
    package = IncrementalEvidenceAdmissionGate().seal(exact_request)
    object.__setattr__(
        exact_request.entries[0].evidence[0],
        "provenance",
        {"capability_call_id": "other-call"},
    )

    assert (
        rejection_code(
            ExactAdmittedIncrementalEvidenceBinder().bind, package, exact_request
        )
        == "post_seal_incremental_evidence_mutation"
    )


def test_i5b_16_forged_package_issuer_rejected():
    package = sealed()
    arguments = {
        field.name: getattr(package, field.name)
        for field in fields(SealedIncrementalEvidencePackage)
        if field.name != "issued_by"
    }

    with pytest.raises(
        C03AdmissionRejected, match="only IncrementalEvidenceAdmissionGate"
    ):
        SealedIncrementalEvidencePackage(**arguments, issued_by=object())


def test_i5b_17_forged_receipt_rejected():
    package = sealed()
    object.__setattr__(package, "gate_receipt", "0" * 64)

    assert rejection_code(package.verify) == "forged_incremental_evidence_receipt"


def test_i5b_18_ledger_dict_is_not_source_authority():
    ledger_dict = source(1).to_payload()

    assert rejection_code(request, (ledger_dict,)) == (
        "inexact_capability_evidence_source"
    )


def test_i5b_19_market_structured_output_survives_exact_canonical_semantics():
    market_payload = {
        "contract_version": "market-public.v1",
        "capability_id": "market.event.resolve",
        "operation_status": "SUCCESS",
        "data_state": "READY",
        "payload": {"rows": [{"item_id": "event:1", "score": 0.9}]},
        "provenance": {
            "source_refs": ["jyhf"],
            "capability_call_ref": "market.event.resolve",
        },
        "failures": [],
        "boundary_identity_ref": "market.public",
        "runtime_observation": None,
        "produced_at": "2026-09-17T00:00:00+00:00",
    }
    item = source(1, structured_output=market_payload)
    package = sealed((item,))

    assert package.ordered_entry_digests == (item.digests()[3],)
    assert (
        canonical_tool_result(item.tool_result)["structured_output"] == market_payload
    )


def test_i5b_20_research_partial_survives_exact_canonical_semantics():
    research_payload = {
        "query": "robotics sector external catalysts",
        "findings": [],
        "sources": [{"ref": "source:robotics-catalysts-2026"}],
        "limitations": ["provider returned no findings"],
        "provider": "research",
        "produced_at": "2026-09-18T00:00:00Z",
    }
    item = source(1, structured_output=research_payload)
    bundle = admitted((item,))

    assert canonical_tool_result(item.tool_result)["status"] == "partial"
    assert canonical_evidence(item.evidence[0])["source_type"] == "TOOL_OBSERVATION"
    assert research_payload["findings"] == []
    assert bundle.semantic_fingerprint()


def test_i5b_21_v1_provider_envelope_behavior_is_unchanged():
    binding = bound_bundle()
    envelope = ProviderAlignmentBoundary().resolve(
        binding, provider_id="deepseek", cognitive_mode="conversation"
    )

    assert isinstance(envelope, ProviderExecutionEnvelope)
    assert envelope.messages == tuple(unit.to_message() for unit in binding.units)
    assert envelope.semantic_fingerprint == binding.semantic_fingerprint()
    envelope.verify()


def test_i5b_22_v2_base_only_uses_three_frozen_roles():
    envelope = ProviderAlignmentBoundary().resolve_v2(
        bound_bundle(), None, provider_id="deepseek"
    )

    assert [message["role"] for message in envelope.messages] == [
        "system",
        "system",
        "user",
    ]
    assert envelope.incremental_evidence_gate_receipt is None
    assert envelope.incremental_evidence_fingerprint is None
    envelope.verify()


def test_i5b_23_v2_with_evidence_uses_four_frozen_roles():
    envelope = ProviderAlignmentBoundary().resolve_v2(
        bound_bundle(), admitted(), provider_id="deepseek"
    )

    assert [message["role"] for message in envelope.messages] == [
        "system",
        "system",
        "system",
        "user",
    ]
    envelope.verify()


def test_i5b_24_v2_base_incremental_turn_mismatch_rejected():
    mismatched_source = source(1)
    object.__setattr__(mismatched_source, "turn_id", "other-turn")
    mismatched_request = IncrementalEvidenceAdmissionRequest(
        conversation_id="conversation-eng12a",
        turn_id="other-turn",
        entries=(mismatched_source,),
    )
    package = IncrementalEvidenceAdmissionGate().seal(mismatched_request)
    bundle = ExactAdmittedIncrementalEvidenceBinder().bind(package, mismatched_request)

    assert (
        rejection_code(
            ProviderAlignmentBoundary().resolve_v2,
            bound_bundle(),
            bundle,
            "deepseek",
        )
        == "incremental_turn_mismatch"
    )


def test_i5b_25_forged_combined_fingerprint_rejected():
    envelope = ProviderAlignmentBoundary().resolve_v2(
        bound_bundle(), admitted(), provider_id="deepseek"
    )
    object.__setattr__(envelope, "combined_fingerprint", "0" * 64)

    with pytest.raises(TypeError, match="combined fingerprint is forged"):
        envelope.verify()


def test_i5b_26_evidence_message_only_from_admitted_bundle():
    bundle = admitted()
    envelope = ProviderAlignmentBoundary().resolve_v2(
        bound_bundle(), bundle, provider_id="deepseek"
    )

    assert envelope.messages[2] == bundle.to_message()
    assert envelope.incremental_evidence_fingerprint == bundle.semantic_fingerprint()


def test_i5b_27_alignment_rejects_ledger_dict_instead_of_bundle():
    assert (
        rejection_code(
            ProviderAlignmentBoundary().resolve_v2,
            bound_bundle(),
            admitted().to_dict(),
            "deepseek",
        )
        == "inexact_incremental_evidence_bundle"
    )


def test_i5b_28_control_without_canonical_evidence_rejected():
    item = source(1)
    object.__setattr__(item.tool_result, "evidence_refs", ())
    object.__setattr__(item, "evidence", ())

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == "control_is_not_evidence"
    )


def test_blocker_bundle_unit_substitution_fails_manifest_verification():
    first = admitted((source(1, pass_index=1),))
    second = admitted((source(2, pass_index=1),))
    object.__setattr__(first, "units", second.units)

    assert rejection_code(first.verify) == "incremental_evidence_unit_substitution"


def test_blocker_substituted_receipt_fails_bundle_manifest_verification():
    first = admitted((source(1, pass_index=1),))
    second = admitted((source(2, pass_index=1),))
    object.__setattr__(first, "gate_receipt", second.gate_receipt)

    assert rejection_code(first.verify) == "forged_incremental_evidence_receipt"


def _recompute_combined(envelope):
    return ProviderExecutionEnvelopeV2.combined_fingerprint_for(
        conversation_id=envelope.conversation_id,
        turn_id=envelope.turn_id,
        base_gate_receipt=envelope.base_gate_receipt,
        base_semantic_fingerprint=envelope.base_semantic_fingerprint,
        incremental_evidence_gate_receipt=envelope.incremental_evidence_gate_receipt,
        incremental_evidence_fingerprint=envelope.incremental_evidence_fingerprint,
        messages=envelope.messages,
        alignment=envelope.alignment,
    )


def test_blocker_changed_base_message_with_recomputed_combined_still_fails():
    envelope = ProviderAlignmentBoundary().resolve_v2(
        bound_bundle(), admitted(), provider_id="deepseek"
    )
    envelope.messages[0]["content"] += "forged-base"
    object.__setattr__(envelope, "combined_fingerprint", _recompute_combined(envelope))

    with pytest.raises(TypeError, match="base semantic fingerprint is forged"):
        envelope.verify()


def test_blocker_changed_evidence_message_with_recomputed_combined_still_fails():
    envelope = ProviderAlignmentBoundary().resolve_v2(
        bound_bundle(), admitted(), provider_id="deepseek"
    )
    envelope.messages[2]["content"] += "forged-evidence"
    object.__setattr__(envelope, "combined_fingerprint", _recompute_combined(envelope))

    with pytest.raises(TypeError, match="incremental evidence fingerprint is forged"):
        envelope.verify()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_blocker_non_finite_json_floats_fail_typed(value):
    item = source(1)
    object.__setattr__(item.evidence[0], "confidence", value)

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == "non_canonical_incremental_evidence_json"
    )


@pytest.mark.parametrize("status", ["DENIED", "UNKNOWN", "random"])
def test_blocker_non_evidentiary_tool_statuses_fail(status):
    item = source(1)
    object.__setattr__(item.tool_result, "status", status)

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == "non_evidentiary_tool_result_status"
    )


@pytest.mark.parametrize(
    ("call_status", "result_status"),
    [
        (CapabilityCallStatus.COMPLETED, ToolResultStatus.SUCCESS),
        (CapabilityCallStatus.COMPLETED, ToolResultStatus.PARTIAL),
        (CapabilityCallStatus.TIMED_OUT, ToolResultStatus.TIMEOUT),
        (CapabilityCallStatus.CANCELLED, ToolResultStatus.CANCELLED),
        (CapabilityCallStatus.FAILED, ToolResultStatus.UNAVAILABLE),
        (CapabilityCallStatus.FAILED, ToolResultStatus.ERROR),
    ],
)
def test_blocker_valid_evidentiary_status_pairings_remain_accepted(
    call_status, result_status
):
    item = source(1)
    object.__setattr__(item.capability_call, "status", call_status)
    object.__setattr__(item.tool_result, "status", result_status)

    assert IncrementalEvidenceAdmissionGate().seal(request((item,)))


def test_blocker_invalid_call_result_status_pairing_fails():
    item = source(1)
    object.__setattr__(item.capability_call, "status", CapabilityCallStatus.COMPLETED)
    object.__setattr__(item.tool_result, "status", ToolResultStatus.ERROR)

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == "capability_tool_result_status_pair_mismatch"
    )


def test_blocker_pass_index_above_executable_limit_fails():
    assert rejection_code(source, 1, pass_index=7) == "inexact_incremental_pass_index"


def test_blocker_duplicate_generation_id_fails():
    entries = (source(1, pass_index=1), source(2, pass_index=2))
    object.__setattr__(entries[1], "generation_id", entries[0].generation_id)

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request(entries))
        == "duplicate_generation_id"
    )


def test_blocker_cyclic_canonical_input_fails_typed():
    cyclic = []
    cyclic.append(cyclic)
    item = source(1, structured_output={"cycle": cyclic})

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == "non_canonical_incremental_evidence_json"
    )


def test_blocker_excessively_deep_canonical_input_fails_typed():
    nested = {"value": "leaf"}
    for _ in range(200):
        nested = {"value": nested}
    item = source(1, structured_output=nested)

    assert (
        rejection_code(IncrementalEvidenceAdmissionGate().seal, request((item,)))
        == "non_canonical_incremental_evidence_json"
    )

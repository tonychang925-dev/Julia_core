"""C1-R2.1 Capability contract object tests.

Protected contract: C-08 / C-12 / REV2 R2-I03..R2-I06
Expected baseline: XFAIL for frozen object-model convergence gaps
Known gaps: B-01, B-02, C-02, C-03 from conformance audit
Resolving phase: R2-P1 / R2-P7

These tests intentionally assert the governed C-08/C-12 object model, not the
superseded REV1 CapabilityResult/Evidence-Chain shape.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

import pytest

from julia_core.capability import models as capability_models
from julia_core.capability.models import CapabilityEvidence, CapabilityRequest, CapabilityResult


C08_CAPABILITY_REQUEST_FIELDS = {
    "capability_request_id",
    "turn_id",
    "generation_id",
    "correlation_id",
    "capability_id",
    "arguments",
    "requested_scope",
    "idempotency_key",
    "requested_at",
    "provenance",
}

REV1_ONLY_REQUEST_FIELDS = {
    "conversation_id",
    "capability_name",
    "requested_by",
    "created_at",
}

C08_TOOL_RESULT_FIELDS = {
    "capability_call_id",
    "status",
    "structured_output",
    "error",
    "started_at",
    "completed_at",
    "side_effect_state",
    "evidence_refs",
}

C12_EVIDENCE_FIELDS = {
    "evidence_id",
    "source_type",
    "source_ref",
    "observed_at",
    "retrieved_at",
    "content_ref",
    "provenance",
    "integrity_metadata",
    "freshness",
    "confidence",
    "correlation_id",
}

TRACE_MINIMUM_FIELDS = {
    "turn_id",
    "generation_id",
    "context_package_id",
    "capability_request_id",
    "capability_call_id",
    "evidence_id",
}


def _dataclass_fields(cls: type[Any]) -> set[str]:
    assert is_dataclass(cls), f"{cls!r} must be a dataclass contract object"
    return {f.name for f in fields(cls)}


@pytest.mark.xfail(
    strict=True,
    reason="B-01/C-03 / C-08: current CapabilityRequest predates frozen C-08; pending R2-P1",
)
def test_c08_capability_request_fields_are_representable_losslessly():
    """CapabilityRequest must expose the frozen C-08 correlation/idempotency fields."""
    actual = _dataclass_fields(CapabilityRequest)
    assert C08_CAPABILITY_REQUEST_FIELDS <= actual


@pytest.mark.xfail(
    strict=True,
    reason="C-03 / C-08: REV1-only request schema must not remain canonical; pending R2-P1",
)
def test_rev1_request_schema_fields_are_not_canonical_contract_requirements():
    """REV2 must not keep REV1's replacement request schema as the contract truth."""
    actual = _dataclass_fields(CapabilityRequest)
    assert actual.isdisjoint(REV1_ONLY_REQUEST_FIELDS)


@pytest.mark.xfail(
    strict=True,
    reason="B-01 / C-08: capability_id is canonical, current code still uses capability_name; pending R2-P1",
)
def test_capability_request_uses_capability_id_not_capability_name_as_canonical_field():
    actual = _dataclass_fields(CapabilityRequest)
    assert "capability_id" in actual
    assert "capability_name" not in actual


@pytest.mark.xfail(
    strict=True,
    reason="C-08: CapabilityCall first-class object is not implemented yet; pending R2-P1",
)
def test_capability_call_is_first_class_invocation_attempt():
    """One execution attempt must be represented separately from request/result."""
    CapabilityCall = getattr(capability_models, "CapabilityCall")
    actual = _dataclass_fields(CapabilityCall)
    assert {
        "capability_call_id",
        "capability_request_id",
        "status",
        "started_at",
        "completed_at",
    } <= actual


@pytest.mark.xfail(
    strict=True,
    reason="C-02/B-02 / C-08+C-12: ToolResult and Evidence are not first-class separated yet; pending R2-P1",
)
def test_tool_result_is_separate_from_evidence_and_links_by_evidence_refs():
    """ToolResult records execution outcome and links to Evidence IDs; it is not Evidence."""
    ToolResult = getattr(capability_models, "ToolResult")
    actual = _dataclass_fields(ToolResult)
    evidence_actual = _dataclass_fields(CapabilityEvidence)

    assert C08_TOOL_RESULT_FIELDS <= actual
    assert "evidence_refs" in actual
    assert "evidence_id" not in actual
    assert C12_EVIDENCE_FIELDS <= evidence_actual


@pytest.mark.xfail(
    strict=True,
    reason="C-02 / C-08: legacy CapabilityResult still merges execution payload with evidence pointer; pending R2-P1",
)
def test_legacy_capability_result_is_not_the_frozen_tool_result_contract():
    """The frozen contract is ToolResult + Evidence, not legacy CapabilityResult as a merged envelope."""
    actual = _dataclass_fields(CapabilityResult)
    assert "structured_output" not in actual
    assert "evidence" not in actual
    assert "evidence_refs" not in actual


@pytest.mark.xfail(
    strict=True,
    reason="B-02 / C-12: EvidenceLedger lacks first-class evidence identity/provenance; pending R2-P1/R2-P7",
)
def test_c12_evidence_fields_are_first_class():
    """Evidence must carry stable identity/source/provenance/correlation fields."""
    actual = _dataclass_fields(CapabilityEvidence)
    assert C12_EVIDENCE_FIELDS <= actual


@pytest.mark.xfail(
    strict=True,
    reason="B-08 / C-12: capability correlation trace is not implemented yet; pending R2-P7",
)
def test_trace_correlates_request_call_evidence_and_context_without_merging_payloads():
    """Trace is a correlation plane; it must not own ToolResult/Evidence semantic payload."""
    CapabilityTrace = getattr(capability_models, "CapabilityTrace")
    actual = _dataclass_fields(CapabilityTrace)
    assert TRACE_MINIMUM_FIELDS <= actual
    assert "structured_output" not in actual
    assert "content" not in actual


def test_no_rev1_evidence_chain_language_exists_in_capability_model_docstrings():
    """Guardrail: do not reintroduce the superseded REV1 merged-object vocabulary."""
    module_doc = capability_models.__doc__ or ""
    result_doc = CapabilityResult.__doc__ or ""
    forbidden = "Evidence Chain"
    assert forbidden not in module_doc
    assert forbidden not in result_doc

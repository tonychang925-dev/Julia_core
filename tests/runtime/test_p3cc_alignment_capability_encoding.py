"""P3-CC I1b-2 — governed C-09 capability encoding foundation tests.

Proves the encoder:
- consumes ONLY governed capability_frame material (no registry/manager/
  bridge/provider/health access, no user_text);
- preserves governed capability semantics faithfully across representation
  modes;
- performs no semantic selection/filtering;
- is deterministic and orders by capability_id;
- returns a structured REPRESENTATION_UNSUPPORTED diagnostic for unsupported
  modes (never silent omission / availability change);
- never mints review authority for engineering.code_review;
- never merges a second capability catalog into the encoded result.
"""

from __future__ import annotations

import inspect

import pytest

from julia_core.alignment_os.capability_encoding import (
    SUPPORTED_REPRESENTATION_MODES,
    CapabilityEncodingResult,
    encode_capability_frame,
)

# ── governed frame fixtures (I1b-1 manifest_entries projection shape) ──────

_READ_ONLY_ENTRY = {
    "capability_id": "file.read",
    "description": "Read file contents from the local filesystem",
    "input_schema": {"path": "file path"},
    "output_schema": {},
    "side_effect_class": "read_only",
    "permission_requirements": ["file.read"],
    "idempotency_support": "none",
    "latency_cost_hints": {"latency_class": "low", "cost_class": "low"},
    "data_sensitivity": "local_user_files",
    "availability": "available",
    "schema_version": "1.0",
    "provenance": {
        "source": "capability:registry",
        "definition_ref": "file.read",
        "derived_at": "2026-09-09T00:00:00Z",
    },
}

_EXTERNAL_ENTRY = {
    "capability_id": "engineering.code_review",
    "description": "Submit a governed review bundle",
    "input_schema": {"review_bundle_ref": "bundle reference"},
    "output_schema": {},
    "side_effect_class": "external_side_effect",
    "permission_requirements": ["engineering.review.external"],
    "idempotency_support": "none",
    "latency_cost_hints": {},
    "data_sensitivity": "engineering_code_review",
    "availability": "registered",
    "schema_version": "1.0",
    "provenance": {
        "source": "capability:registry",
        "definition_ref": "engineering.code_review",
        "derived_at": "2026-09-09T00:00:00Z",
    },
}

_REGISTERED_ENTRY = {
    "capability_id": "market.stock.history",
    "description": "Legacy market domain history read",
    "input_schema": {"symbol": "ticker"},
    "output_schema": {},
    "side_effect_class": "read_only",
    "permission_requirements": ["market.observe"],
    "idempotency_support": "none",
    "latency_cost_hints": {},
    "data_sensitivity": "market_observe",
    "availability": "registered",
    "schema_version": "1.0",
    "provenance": {
        "source": "capability:registry",
        "definition_ref": "market.stock.history",
        "derived_at": "2026-09-09T00:00:00Z",
    },
}

_AVAILABLE_MARKET_ENTRY = {
    "capability_id": "market.event.read",
    "description": "Read a canonical Market event",
    "input_schema": {"event_id": "event id"},
    "output_schema": {},
    "side_effect_class": "read_only",
    "permission_requirements": ["market.observe"],
    "idempotency_support": "none",
    "latency_cost_hints": {},
    "data_sensitivity": "market_observe",
    "availability": "available",
    "schema_version": "1.0",
    "provenance": {
        "source": "capability:registry",
        "definition_ref": "market.event.read",
        "derived_at": "2026-09-09T00:00:00Z",
    },
}

_RESERACH_ENTRY = {
    "capability_id": "research.event.enrich",
    "description": "Controlled D1 external research observation",
    "input_schema": {"event_id": "event id"},
    "output_schema": {},
    "side_effect_class": "read_only",
    "permission_requirements": ["research.enrich"],
    "idempotency_support": "none",
    "latency_cost_hints": {},
    "data_sensitivity": "external_research_observation",
    "availability": "registered",
    "schema_version": "1.0",
    "provenance": {
        "source": "capability:registry",
        "definition_ref": "research.event.enrich",
        "derived_at": "2026-09-09T00:00:00Z",
    },
}


def _frame(*entries):
    return {"manifest_entries": list(entries)}


FULL_FRAME = _frame(
    _EXTERNAL_ENTRY,
    _REGISTERED_ENTRY,
    _READ_ONLY_ENTRY,
    _AVAILABLE_MARKET_ENTRY,
    _RESERACH_ENTRY,
)

_GOVERNED_FIELDS = {
    "capability_id",
    "description",
    "input_schema",
    "output_schema",
    "side_effect_class",
    "permission_requirements",
    "idempotency_support",
    "latency_cost_hints",
    "data_sensitivity",
    "availability",
    "schema_version",
    "provenance",
}


# ── 1. Source boundary: no registry/manager/bridge/provider access ─────────

def test_encoder_imports_and_accepts_only_frame_material():
    import ast
    import importlib

    module = importlib.import_module(
        "julia_core.alignment_os.capability_encoding"
    )
    tree = ast.parse(inspect.getsource(module))
    # Drop the module docstring so documentation prose is not mistaken for
    # real access; assert against actual executable code only.
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        tree.body = tree.body[1:]
    code = ast.unparse(tree)

    # No import of the upstream authorities, no health call, no provider SDK.
    for forbidden in (
        "CapabilityRegistry",
        "CapabilityManager",
        "RuntimeCapabilityBridge",
        "capability.registry",
        "capability.manager",
        ".health(",
        "import openai",
        "import anthropic",
        "import deepseek",
        "import zhipu",
    ):
        assert forbidden not in code, forbidden


def test_encoder_api_has_no_user_text_input():
    signature = inspect.signature(encode_capability_frame)
    parameters = signature.parameters
    assert "user_text" not in parameters
    assert "user" not in parameters
    assert "text" not in parameters  # only the deterministic protocol output


# ── 2. Fidelity across representations ─────────────────────────────────────

def test_structured_mode_preserves_governed_fidelity():
    result = encode_capability_frame(FULL_FRAME, representation_mode="structured")
    assert isinstance(result, CapabilityEncodingResult)
    assert len(result.descriptors) == 5
    by_id = {d["capability_id"]: d for d in result.descriptors}

    file_read = by_id["file.read"]
    for field in _GOVERNED_FIELDS:
        assert field in file_read, field
    assert file_read["side_effect_class"] == "read_only"
    assert file_read["permission_requirements"] == ["file.read"]
    assert file_read["data_sensitivity"] == "local_user_files"
    assert file_read["availability"] == "available"

    review = by_id["engineering.code_review"]
    assert review["side_effect_class"] == "external_side_effect"
    assert review["data_sensitivity"] == "engineering_code_review"
    assert review["availability"] == "registered"

    assert by_id["market.stock.history"]["availability"] == "registered"
    assert by_id["market.event.read"]["availability"] == "available"
    assert by_id["research.event.enrich"]["availability"] == "registered"


def test_text_protocol_mode_preserves_fidelity_deterministically():
    result = encode_capability_frame(FULL_FRAME, representation_mode="text_protocol")
    assert result.text is not None
    assert "capability: file.read" in result.text
    assert "capability: engineering.code_review" in result.text
    assert "side_effect_class: external_side_effect" in result.text
    assert "availability: registered" in result.text
    assert "availability: available" in result.text
    # R1-A: latency_cost_hints is not silently lost.
    assert '"latency_class": "low"' in result.text
    assert '"cost_class": "low"' in result.text
    # R1-A: provenance fields are preserved semantically (not just the word).
    assert '"source": "capability:registry"' in result.text
    assert '"definition_ref": "file.read"' in result.text
    assert '"derived_at": "2026-09-09T00:00:00Z"' in result.text
    # No cognition/router instruction text is added.
    assert "you should use" not in result.text.lower()
    assert "best tool" not in result.text.lower()
    assert "for market questions" not in result.text.lower()


def test_text_protocol_deterministic_digest():
    a = encode_capability_frame(FULL_FRAME, representation_mode="text_protocol")
    b = encode_capability_frame(FULL_FRAME, representation_mode="text_protocol")
    assert a.digest == b.digest
    assert a.digest != ""
    assert a.text == b.text


def test_no_silent_field_loss_in_any_representation():
    # Structured: every governed field is present on every descriptor.
    structured = encode_capability_frame(FULL_FRAME, representation_mode="structured")
    for descriptor in structured.descriptors:
        for field in _GOVERNED_FIELDS:
            assert field in descriptor, (descriptor["capability_id"], field)

    # Text: every governed field is semantically present (capability_id is
    # rendered under the "capability:" header token; the rest as field labels).
    text = encode_capability_frame(FULL_FRAME, representation_mode="text_protocol")
    assert text.text is not None
    for field in _GOVERNED_FIELDS:
        if field == "capability_id":
            assert "capability:" in text.text, field
        else:
            assert field in text.text, field


# ── 3. No semantic selection ───────────────────────────────────────────────

def test_all_supplied_entries_preserved_regardless_of_topic():
    result = encode_capability_frame(FULL_FRAME)
    ids = {d["capability_id"] for d in result.descriptors}
    assert ids == {
        "file.read",
        "engineering.code_review",
        "market.stock.history",
        "market.event.read",
        "research.event.enrich",
    }


# ── 4. Deterministic ordering ──────────────────────────────────────────────

def test_deterministic_ordering_by_capability_id():
    reversed_frame = _frame(
        *reversed(FULL_FRAME["manifest_entries"]),
    )
    a = encode_capability_frame(FULL_FRAME)
    b = encode_capability_frame(reversed_frame)
    ids_a = [d["capability_id"] for d in a.descriptors]
    ids_b = [d["capability_id"] for d in b.descriptors]
    assert ids_a == sorted(ids_a)
    assert ids_a == ids_b
    assert a.digest == b.digest
    assert a.digest != ""


# ── 5. Unsupported representation diagnostic ──────────────────────────────

def test_unsupported_mode_returns_structured_diagnostic():
    result = encode_capability_frame(FULL_FRAME, representation_mode="banana")
    # R1-C: diagnostics runtime shape is always tuple.
    assert isinstance(result.diagnostics, tuple)
    assert len(result.diagnostics) >= 1
    assert result.descriptors == ()
    assert result.text is None
    assert result.source_capability_ids == ()
    codes = [d["code"] for d in result.diagnostics]
    assert "REPRESENTATION_UNSUPPORTED" in codes
    # Distinguishable from a capability-unavailable notion: availability is
    # never rewritten and no CAPABILITY_UNAVAILABLE diagnostic is fabricated.
    assert "CAPABILITY_UNAVAILABLE" not in codes


# ── 6. Review boundary: no review authority minted ─────────────────────────

def test_review_representation_mints_no_authority():
    result = encode_capability_frame(_frame(_EXTERNAL_ENTRY))
    review = result.descriptors[0]
    serialized = json_repr(review)
    assert "review_transaction" not in serialized.lower()
    assert "ledger_token" not in serialized.lower()
    assert "send_authorization" not in serialized.lower()
    assert "authorization_decision" not in serialized.lower()
    # side-effect class survives un-downgraded.
    assert review["side_effect_class"] == "external_side_effect"


def json_repr(value):
    import json

    return json.dumps(value, sort_keys=True, ensure_ascii=False)


# ── 7. No dual catalog / no raw fallback ───────────────────────────────────

def test_no_dual_catalog_in_encoded_result():
    result = encode_capability_frame(FULL_FRAME)
    serialized = json_repr(result.descriptors)
    assert "available_tools" not in serialized
    assert "tool_manifest" not in serialized.lower()
    assert result.source == "governed capability_frame"


def test_invalid_frame_surfaces_structured_diagnostic_not_silent():
    result = encode_capability_frame({"not_manifest": []})
    codes = [d["code"] for d in result.diagnostics]
    assert "INVALID_CAPABILITY_FRAME" in codes
    assert result.descriptors == ()


def test_invalid_entry_surfaces_diagnostic_not_silent():
    frame = _frame(_READ_ONLY_ENTRY, {"not": "a valid entry"})
    result = encode_capability_frame(frame)
    codes = [d["code"] for d in result.diagnostics]
    assert "INVALID_MANIFEST_ENTRY" in codes
    # The valid entry is still represented; the invalid one is not silently
    # assumed safe and is not dropped without a diagnostic.
    assert any(d["capability_id"] == "file.read" for d in result.descriptors)


def test_partial_manifest_entry_is_structured_invalid_not_keyerror():
    """R1-B: a mapping with a valid capability_id but missing governed fields
    never reaches direct indexing (no KeyError), yields a structured
    INVALID_MANIFEST_ENTRY with a deterministic missing_fields list, and is not
    represented as an executable capability. Other valid entries remain
    representable."""
    partial = {
        "capability_id": "file.search",
        "description": "incomplete entry",
        # deliberately missing most governed fields
    }
    frame = _frame(_READ_ONLY_ENTRY, partial)
    result = encode_capability_frame(frame)

    # No exception and no descriptor for the malformed entry.
    assert all(
        d["capability_id"] != "file.search" for d in result.descriptors
    )
    # The valid sibling entry is still represented.
    assert any(d["capability_id"] == "file.read" for d in result.descriptors)

    diagnostics = [
        d for d in result.diagnostics
        if d.get("capability_id") == "file.search"
        and d["code"] == "INVALID_MANIFEST_ENTRY"
    ]
    assert len(diagnostics) == 1
    missing = diagnostics[0]["missing_fields"]
    assert isinstance(missing, list)
    assert missing == sorted(missing)  # deterministic ordering
    for field in (
        "input_schema",
        "output_schema",
        "side_effect_class",
        "permission_requirements",
        "idempotency_support",
        "latency_cost_hints",
        "data_sensitivity",
        "availability",
        "schema_version",
        "provenance",
    ):
        assert field in missing


# ── 8. Availability/permission immutability ────────────────────────────────

def test_availability_is_immutable_input():
    result = encode_capability_frame(FULL_FRAME)
    by_id = {d["capability_id"]: d for d in result.descriptors}
    assert by_id["market.stock.history"]["availability"] == "registered"
    assert by_id["market.event.read"]["availability"] == "available"
    # No promotion of REGISTERED / demotion of AVAILABLE anywhere.
    availabilities = {d["capability_id"]: d["availability"] for d in result.descriptors}
    assert availabilities == {
        "file.read": "available",
        "engineering.code_review": "registered",
        "market.stock.history": "registered",
        "market.event.read": "available",
        "research.event.enrich": "registered",
    }

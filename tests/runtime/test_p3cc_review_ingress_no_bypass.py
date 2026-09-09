"""P3-CC I1a — engineering.code_review ingress no-bypass regression tests.

Frozen boundary: a model-generated CapabilityRequest alone is NEVER sufficient
to authorize or execute engineering.code_review. P3-CC metadata/manifest
changes must not mint ReviewTransaction / Core-ledger tokens or bypass the
existing GOVERNED_INGRESS_REQUIRED guard. No model_invocable field exists.
"""

from __future__ import annotations

import json

import pytest

from julia_core.runtime.capability_bridge import (
    CapabilityPreAuthorizationFailure,
    RuntimeCapabilityBridge,
)
from julia_core.capability.registry import project_manifest_entry

MODEL_REVIEW_TOOL_CALL = json.dumps(
    {
        "name": "engineering.code_review",
        "arguments": {"review_bundle_ref": "model-supplied"},
    },
    ensure_ascii=False,
    separators=(",", ":"),
)


def _resolve_through_bridge(bridge: RuntimeCapabilityBridge):
    return bridge._resolve_tool_request(
        MODEL_REVIEW_TOOL_CALL,
        turn_id="turn",
        generation_id="gen",
        correlation_id="corr",
    )


def test_model_originated_code_review_request_is_blocked():
    bridge = RuntimeCapabilityBridge()
    resolved = _resolve_through_bridge(bridge)
    assert isinstance(resolved, CapabilityPreAuthorizationFailure)
    assert resolved.capability_id == "engineering.code_review"
    assert resolved.reason == "GOVERNED_INGRESS_REQUIRED"


def test_metadata_classification_does_not_bypass_ingress_guard():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    resolved = _resolve_through_bridge(bridge)
    assert isinstance(resolved, CapabilityPreAuthorizationFailure)
    assert resolved.reason == "GOVERNED_INGRESS_REQUIRED"


def test_manifest_existence_does_not_mint_review_transaction_or_ledger_token():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    definition = bridge.registry.get("engineering.code_review")
    assert definition is not None
    admission = project_manifest_entry(definition)
    assert admission.admitted is True
    assert admission.entry is not None
    assert admission.entry.side_effect_class is not None

    # The manifest entry carries no token/transaction/provider authority fields.
    entry = admission.entry
    assert not hasattr(entry, "model_invocable")
    assert not hasattr(entry, "review_transaction")
    assert not hasattr(entry, "ledger_token")
    assert not hasattr(entry, "provider")
    # Frozen slots dataclass: field surface is the class's declared dataclass
    # fields only (no __dict__); manifest metadata never mints authority.
    import dataclasses

    from julia_core.capability.models import CapabilityManifestEntry

    fields = {f.name for f in dataclasses.fields(CapabilityManifestEntry)}
    assert "review_transaction" not in fields
    assert "ledger_token" not in fields
    assert "model_invocable" not in fields
    assert "provider" not in fields


def test_execution_guard_still_denied_through_manager_path():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    # Even a structurally recognized request must fail at the guarded ingress
    # before manager authorization can be reached (blocked in bridge).
    resolved = _resolve_through_bridge(bridge)
    assert isinstance(resolved, CapabilityPreAuthorizationFailure)
    assert resolved.reason == "GOVERNED_INGRESS_REQUIRED"

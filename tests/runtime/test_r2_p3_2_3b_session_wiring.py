"""R2-P3.2.3B Session typed wiring acceptance (future).

Describes the future JuliaSession typed dispatch to Context OS. Session must
consume CapabilityBridge.execute_tool_typed() and dispatch the exact
CapabilityExecution / CapabilityPreAuthorizationFailure to the appropriate
Context OS projection — without registry rediscovery, without legacy string
parsing, without direct prompt injection.

These tests are strict-XFAIL until P3.2.3B production.
"""

from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _session_source() -> str:
    return (ROOT / "julia_core" / "runtime" / "julia_session.py").read_text()


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2.3B: session typed wiring not implemented",
)
def test_session_uses_execute_tool_typed_not_legacy_string_seam():
    source = _session_source()
    assert "self.capability.execute_tool_typed" in source


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2.3B: session typed wiring not implemented",
)
def test_session_dispatches_authorization_and_control_outcomes():
    source = _session_source()
    # non-ALLOW → project_authorization_outcome
    assert "project_authorization_outcome" in source
    # UNKNOWN/DISABLED → project_capability_resolution_failure
    assert "project_capability_resolution_failure" in source


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2.3B: session typed wiring not implemented",
)
def test_session_replaces_legacy_string_seam_with_typed_seam():
    source = _session_source()
    # continuation transport is the typed seam, not the legacy string execute_tool
    assert "self.capability.execute_tool_typed" in source
    assert "self.capability.execute_tool(" not in source


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2.3B: session typed wiring not implemented",
)
def test_session_does_not_requery_registry_for_preauth_failure():
    source = _session_source()
    # Session must consume the CapabilityPreAuthorizationFailure carrier
    # directly; it must not requery registry to recover UNKNOWN/DISABLED.
    assert "CapabilityPreAuthorizationFailure" in source

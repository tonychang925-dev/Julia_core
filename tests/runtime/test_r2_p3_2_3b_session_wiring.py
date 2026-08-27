"""R2-P3.2.3B Session typed wiring acceptance.

Describes the future JuliaSession typed dispatch to Context OS. Session must
consume CapabilityBridge.execute_tool_typed() and dispatch the exact
CapabilityExecution / CapabilityPreAuthorizationFailure to the appropriate
Context OS projection — without registry rediscovery, without legacy string
parsing, without direct prompt injection.

All nodes are strict-XFAIL until P3.2.3B production.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from julia_core.capability.manager import CapabilityExecution
from julia_core.capability.models import (
    CapabilityCall,
    Evidence,
    EvidenceSourceType,
    ToolResult,
    ToolResultStatus,
)
from julia_core.capability.policy import AuthorizationDecision, AuthorizationStatus
from julia_core.runtime.capability_bridge import CapabilityPreAuthorizationFailure
from julia_core.runtime.julia_session import JuliaSession


ROOT = Path(__file__).resolve().parents[2]


def _session_source() -> str:
    return (ROOT / "julia_core" / "runtime" / "julia_session.py").read_text()


# ── Source-inspection contract ─────────────────────────────────────────────

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
    assert "project_authorization_outcome" in source
    assert "project_capability_resolution_failure" in source


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2.3B: session typed wiring not implemented",
)
def test_session_replaces_legacy_string_seam_with_typed_seam():
    source = _session_source()
    assert "self.capability.execute_tool_typed" in source
    assert "self.capability.execute_tool(" not in source


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2.3B: session typed wiring not implemented",
)
def test_session_does_not_requery_registry_for_preauth_failure():
    source = _session_source()
    assert "CapabilityPreAuthorizationFailure" in source


# ── Behavioral dispatch contract ───────────────────────────────────────────

SENTINEL = "SENTINEL_PROJECTED_DELTA"


class _DeltaPackage:
    active_tail_messages: list[dict[str, Any]] = []

    def to_messages(self, history, user_text):
        return [{"role": "system", "content": SENTINEL}]


class _FakeProvider:
    def __init__(self):
        self.chat_calls: list[list[dict]] = []

    def chat(self, messages, cognitive_mode=""):
        self.chat_calls.append(list(messages))
        if len(self.chat_calls) == 1:
            return '```tool_call\n{"name":"read_file","arguments":{"path":"x"}}\n```'
        return "final answer after typed projection"


class _FakeTypedCapability:
    def __init__(self, typed_result):
        self.typed_result = typed_result
        self.requires_tool_calls: list[str] = []
        self.detect_tool_call_inputs: list[str] = []
        self.execute_tool_calls: list[str] = []
        self.execute_tool_typed_calls: list[str] = []

    def requires_tool(self, text: str) -> bool:
        self.requires_tool_calls.append(text)
        return False

    def detect_tool_call(self, reply: str) -> str | None:
        self.detect_tool_call_inputs.append(reply)
        if "tool_call" in reply:
            return '{"name":"read_file","arguments":{"path":"x"}}'
        return None

    def execute_tool(self, tool_json: str) -> str:
        self.execute_tool_calls.append(tool_json)
        return "legacy observation"

    def execute_tool_typed(self, tool_json: str):
        self.execute_tool_typed_calls.append(tool_json)
        return self.typed_result


class _FakeTypedContextOS:
    def __init__(self):
        self.project_tool_result_calls: list[dict[str, Any]] = []
        self.project_authorization_outcome_calls: list[dict[str, Any]] = []
        self.project_capability_resolution_failure_calls: list[dict[str, Any]] = []

    def project_tool_result(self, **kwargs):
        self.project_tool_result_calls.append(kwargs)
        return _DeltaPackage()

    def project_authorization_outcome(self, **kwargs):
        self.project_authorization_outcome_calls.append(kwargs)
        return _DeltaPackage()

    def project_capability_resolution_failure(self, **kwargs):
        self.project_capability_resolution_failure_calls.append(kwargs)
        return _DeltaPackage()


class _FakeAction:
    def __init__(self):
        self.started: list[str] = []
        self.finished: list[str] = []

    def start(self, name, description="", correlation_id=""):
        self.started.append(name)

    def finish(self, status, correlation_id=""):
        self.finished.append(status)


class _FakeRecorder:
    def record(self, speaker, text, topic=""):
        return None


def _typed_session(monkeypatch, typed_result):
    session = JuliaSession.__new__(JuliaSession)
    session.provider = _FakeProvider()
    session.capability = _FakeTypedCapability(typed_result)
    session.context_os = _FakeTypedContextOS()
    session.action = _FakeAction()
    session.recorder = _FakeRecorder()
    captured: dict[str, Any] = {"package": None, "turn_count": None}

    class _FakePackage:
        package_id = "ctxpkg_typed"
        active_tail_messages: list[dict[str, Any]] = []

    def fake_prepare_turn(self, text, ctx):
        pkg = _FakePackage()
        ctx._last_package = pkg
        captured["package"] = pkg
        captured["turn_count"] = ctx.turn_count
        return [{"role": "user", "content": text}]

    def fake_update_state(self, text, reply, ctx):
        return None

    monkeypatch.setattr(JuliaSession, "_prepare_turn", fake_prepare_turn)
    monkeypatch.setattr(JuliaSession, "_update_conversation_state", fake_update_state)
    return session, captured


def _call(call_id: str) -> CapabilityCall:
    return CapabilityCall(capability_call_id=call_id, capability_request_id="req-1")


def _result(call_id: str, evidence_refs: tuple[str, ...] = ()) -> ToolResult:
    return ToolResult(
        capability_call_id=call_id,
        status=ToolResultStatus.SUCCESS,
        evidence_refs=evidence_refs,
    )


def _evidence(evidence_id: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref="capability:file.read:provider:local",
        observed_at="2026-08-27T00:00:00Z",
        content_ref="tool_result:call-1:structured_output",
    )


def _expected_generation(captured: dict[str, Any]) -> str:
    return f"gen_tool_{captured['turn_count']}"


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2.3B: session typed wiring not implemented",
)
def test_session_typed_non_allow_dispatches_authorization_outcome(monkeypatch):
    decision = AuthorizationDecision(decision=AuthorizationStatus.DENY, scope="file.read", reason="deny")
    carrier = CapabilityExecution(decision, None, None, ())
    session, captured = _typed_session(monkeypatch, carrier)

    session.process("read the file", [], conversation_id="conv", turn_id="turn")

    assert len(session.capability.execute_tool_typed_calls) == 1
    assert len(session.context_os.project_authorization_outcome_calls) == 1
    dispatched = session.context_os.project_authorization_outcome_calls[0]
    assert dispatched["authorization_decision"] is decision
    assert dispatched["parent_package"] is captured["package"]
    assert dispatched["generation_id"] == _expected_generation(captured)
    # provider: pass-1 + continuation, continuation consumes rebuilt delta
    assert len(session.provider.chat_calls) == 2
    assert SENTINEL in session.provider.chat_calls[1][0]["content"]


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2.3B: session typed wiring not implemented",
)
def test_session_typed_allow_dispatches_exact_tool_result_and_evidence(monkeypatch):
    call = _call("call-1")
    evidence = _evidence("ev-1")
    result = _result("call-1", evidence_refs=("ev-1",))
    carrier = CapabilityExecution(
        AuthorizationDecision(decision=AuthorizationStatus.ALLOW, scope="file.read", reason="allow"),
        call,
        result,
        (evidence,),
    )
    session, captured = _typed_session(monkeypatch, carrier)

    session.process("read the file", [], conversation_id="conv", turn_id="turn")

    assert len(session.capability.execute_tool_typed_calls) == 1
    assert len(session.context_os.project_tool_result_calls) == 1
    dispatched = session.context_os.project_tool_result_calls[0]
    assert dispatched["tool_result"] is result
    assert dispatched["evidence"] == (evidence,)
    assert dispatched["evidence"][0] is evidence
    assert dispatched["parent_package"] is captured["package"]
    assert dispatched["generation_id"] == _expected_generation(captured)
    assert len(session.provider.chat_calls) == 2
    assert SENTINEL in session.provider.chat_calls[1][0]["content"]


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2.3B: session typed wiring not implemented",
)
def test_session_typed_unknown_dispatches_control_projection(monkeypatch):
    session, captured = _typed_session(monkeypatch, CapabilityPreAuthorizationFailure("no.such", "UNKNOWN"))

    session.process("read the file", [], conversation_id="conv", turn_id="turn")

    assert len(session.capability.execute_tool_typed_calls) == 1
    assert len(session.context_os.project_capability_resolution_failure_calls) == 1
    dispatched = session.context_os.project_capability_resolution_failure_calls[0]
    assert dispatched["capability_id"] == "no.such"
    assert dispatched["reason"] == "UNKNOWN"
    assert dispatched["parent_package"] is captured["package"]
    assert dispatched["generation_id"] == _expected_generation(captured)
    assert len(session.provider.chat_calls) == 2
    assert SENTINEL in session.provider.chat_calls[1][0]["content"]


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2.3B: session typed wiring not implemented",
)
def test_session_typed_disabled_dispatches_control_projection(monkeypatch):
    session, captured = _typed_session(monkeypatch, CapabilityPreAuthorizationFailure("file.disabled", "DISABLED"))

    session.process("read the file", [], conversation_id="conv", turn_id="turn")

    assert len(session.context_os.project_capability_resolution_failure_calls) == 1
    dispatched = session.context_os.project_capability_resolution_failure_calls[0]
    assert dispatched["capability_id"] == "file.disabled"
    assert dispatched["reason"] == "DISABLED"
    assert dispatched["parent_package"] is captured["package"]
    assert dispatched["generation_id"] == _expected_generation(captured)
    assert len(session.provider.chat_calls) == 2
    assert SENTINEL in session.provider.chat_calls[1][0]["content"]


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2.3B: session typed wiring not implemented",
)
def test_session_typed_malformed_none_skips_continuation(monkeypatch):
    session, _ = _typed_session(monkeypatch, None)

    reply = session.process("read the file", [], conversation_id="conv", turn_id="turn")

    # No projection, no continuation: single pass-1 provider call.
    assert len(session.provider.chat_calls) == 1
    assert len(session.context_os.project_tool_result_calls) == 0
    assert len(session.context_os.project_authorization_outcome_calls) == 0
    assert len(session.context_os.project_capability_resolution_failure_calls) == 0
    assert "tool_call" in reply

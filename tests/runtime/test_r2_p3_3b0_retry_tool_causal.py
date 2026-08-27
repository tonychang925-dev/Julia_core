"""R2-P3.3B0 retry → tool causal-chain acceptance.

Proves the P0 → P1 → P2 lineage: the typed tool projection after a retry must
descend from the retry_control package P1, never jump back to the pre-retry
package P0. Strict-XFAIL until P3.3B production.
"""

from __future__ import annotations

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


RETRY_SENTINEL = "RETRY_CONTROL_SENTINEL"
TOOL_SENTINEL = "TOOL_RESULT_SENTINEL"


class _DeltaPackage:
    def __init__(self, sentinel: str):
        self.sentinel = sentinel
        self.active_tail_messages: list[dict[str, Any]] = []

    def to_messages(self, history, user_text):
        return [{"role": "system", "content": self.sentinel}, {"role": "user", "content": user_text}]


class _Provider:
    def __init__(self):
        self.chat_calls: list[list[dict]] = []

    def chat(self, messages, cognitive_mode=""):
        self.chat_calls.append(list(messages))
        if len(self.chat_calls) == 1:
            return "pass-1 reply (no tool)"
        if len(self.chat_calls) == 2:
            return '```tool_call\n{"name":"read_file","arguments":{"path":"x"}}\n```'
        return "final answer"


class _RetryThenToolCapability:
    def __init__(self, typed_outcome):
        self.typed_outcome = typed_outcome
        self.requires_tool_calls: list[str] = []
        self.detect_tool_call_inputs: list[str] = []
        self.execute_tool_typed_calls: list[str] = []

    def requires_tool(self, text: str) -> bool:
        self.requires_tool_calls.append(text)
        return True

    def detect_tool_call(self, reply: str) -> str | None:
        self.detect_tool_call_inputs.append(reply)
        if len(self.detect_tool_call_inputs) == 1:
            return None  # pass-1: no tool call
        return '{"name":"read_file","arguments":{"path":"x"}}'  # retry: tool call

    def execute_tool_typed(self, tool_json: str):
        self.execute_tool_typed_calls.append(tool_json)
        return self.typed_outcome


class _ImmediateToolCapability:
    def __init__(self, typed_outcome):
        self.typed_outcome = typed_outcome
        self.requires_tool_calls: list[str] = []
        self.detect_tool_call_inputs: list[str] = []
        self.execute_tool_typed_calls: list[str] = []

    def requires_tool(self, text: str) -> bool:
        self.requires_tool_calls.append(text)
        return False  # no retry branch

    def detect_tool_call(self, reply: str) -> str | None:
        self.detect_tool_call_inputs.append(reply)
        return '{"name":"read_file","arguments":{"path":"x"}}'  # immediate tool call

    def execute_tool_typed(self, tool_json: str):
        self.execute_tool_typed_calls.append(tool_json)
        return self.typed_outcome


class _ContextOS:
    def __init__(self):
        self.project_retry_control_calls: list[dict[str, Any]] = []
        self.project_tool_result_calls: list[dict[str, Any]] = []
        self.project_capability_resolution_failure_calls: list[dict[str, Any]] = []

    def project_retry_control(self, **kwargs):
        pkg = _DeltaPackage(RETRY_SENTINEL)
        self.project_retry_control_calls.append({**kwargs, "returned": pkg})
        return pkg

    def project_tool_result(self, **kwargs):
        pkg = _DeltaPackage(TOOL_SENTINEL)
        self.project_tool_result_calls.append({**kwargs, "returned": pkg})
        return pkg

    def project_capability_resolution_failure(self, **kwargs):
        pkg = _DeltaPackage(TOOL_SENTINEL)
        self.project_capability_resolution_failure_calls.append({**kwargs, "returned": pkg})
        return pkg


class _FakeAction:
    def start(self, *a, **k):
        return None

    def finish(self, *a, **k):
        return None


class _FakeRecorder:
    def record(self, *a, **k):
        return None


def _session(monkeypatch, capability) -> tuple[JuliaSession, dict[str, Any]]:
    session = JuliaSession.__new__(JuliaSession)
    session.provider = _Provider()
    session.capability = capability
    session.context_os = _ContextOS()
    session.action = _FakeAction()
    session.recorder = _FakeRecorder()
    captured: dict[str, Any] = {"p0": None, "turn_count": None}

    class _P0:
        package_id = "p0"

    def fake_prepare_turn(self, text, ctx):
        p0 = _P0()
        ctx._last_package = p0
        captured["p0"] = p0
        captured["turn_count"] = ctx.turn_count
        return [{"role": "user", "content": text}]

    def fake_update_state(self, text, reply, ctx):
        return None

    monkeypatch.setattr(JuliaSession, "_prepare_turn", fake_prepare_turn)
    monkeypatch.setattr(JuliaSession, "_update_conversation_state", fake_update_state)
    return session, captured


def _allow_outcome() -> CapabilityExecution:
    call = CapabilityCall(capability_call_id="call-1", capability_request_id="req-1")
    evidence = Evidence(
        evidence_id="ev-1",
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref="capability:file.read:provider:local",
        observed_at="2026-08-27T00:00:00Z",
        content_ref="tool_result:call-1:structured_output",
    )
    result = ToolResult(
        capability_call_id="call-1",
        status=ToolResultStatus.SUCCESS,
        structured_output={"content": "observed"},
        evidence_refs=("ev-1",),
    )
    return CapabilityExecution(
        AuthorizationDecision(decision=AuthorizationStatus.ALLOW, scope="file.read", reason="allow"),
        call,
        result,
        (evidence,),
    )


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.3B: retry-then-tool causal chain not implemented",
)
def test_retry_then_allow_projects_from_retry_parent(monkeypatch):
    capability = _RetryThenToolCapability(_allow_outcome())
    session, captured = _session(monkeypatch, capability)

    session.process("need evidence", [], conversation_id="conv", turn_id="turn")

    p0 = captured["p0"]
    # P1 = returned retry_control package, whose parent is P0.
    assert len(session.context_os.project_retry_control_calls) == 1
    retry_call = session.context_os.project_retry_control_calls[0]
    assert retry_call["parent_package"] is p0
    assert retry_call["generation_id"] == f"gen_retry_{captured['turn_count']}"
    p1 = retry_call["returned"]

    # P2 tool projection must descend from P1, NOT P0.
    assert len(session.capability.execute_tool_typed_calls) == 1
    assert len(session.context_os.project_tool_result_calls) == 1
    tool_call = session.context_os.project_tool_result_calls[0]
    assert tool_call["parent_package"] is p1
    assert tool_call["parent_package"] is not p0
    assert tool_call["generation_id"] == f"gen_tool_{captured['turn_count']}"

    # provider: pass-1 + retry + continuation == 3.
    assert len(session.provider.chat_calls) == 3
    assert RETRY_SENTINEL in session.provider.chat_calls[1][0]["content"]
    assert TOOL_SENTINEL in session.provider.chat_calls[2][0]["content"]


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.3B: retry-then-tool causal chain not implemented",
)
def test_retry_then_preauth_projects_from_retry_parent(monkeypatch):
    capability = _RetryThenToolCapability(CapabilityPreAuthorizationFailure("no.such", "UNKNOWN"))
    session, captured = _session(monkeypatch, capability)

    session.process("need evidence", [], conversation_id="conv", turn_id="turn")

    p0 = captured["p0"]
    assert len(session.context_os.project_retry_control_calls) == 1
    retry_call = session.context_os.project_retry_control_calls[0]
    assert retry_call["parent_package"] is p0
    p1 = retry_call["returned"]

    assert len(session.context_os.project_capability_resolution_failure_calls) == 1
    preauth_call = session.context_os.project_capability_resolution_failure_calls[0]
    assert preauth_call["parent_package"] is p1
    assert preauth_call["parent_package"] is not p0


def test_initial_non_retry_path_uses_original_parent(monkeypatch):
    capability = _ImmediateToolCapability(_allow_outcome())
    session, captured = _session(monkeypatch, capability)

    session.process("need evidence", [], conversation_id="conv", turn_id="turn")

    p0 = captured["p0"]
    assert len(session.context_os.project_retry_control_calls) == 0
    assert len(session.context_os.project_tool_result_calls) == 1
    tool_call = session.context_os.project_tool_result_calls[0]
    assert tool_call["parent_package"] is p0

"""R2-P3.3 retry/control bypass acceptance.

P3.3 owns the sync retry branch (needs_evidence && !tool_json) that must route
through structured Context OS control projection instead of a direct
"[系统提示]" system-prompt append. It is transport/projection/retry only — NOT
semantic tool-need authority (P4), NOT capability execution, NOT streaming.

All nodes are strict-XFAIL until P3.3 production.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from julia_core.runtime.julia_session import JuliaSession


ROOT = Path(__file__).resolve().parents[2]


def _session_source() -> str:
    return (ROOT / "julia_core" / "runtime" / "julia_session.py").read_text()


SENTINEL = "SENTINEL_RETRY_CONTROL"


class _DeltaPackage:
    active_tail_messages: list[dict[str, Any]] = []

    def to_messages(self, history, user_text):
        return [{"role": "system", "content": SENTINEL}, {"role": "user", "content": user_text}]


class _RetryProvider:
    def __init__(self):
        self.chat_calls: list[list[dict]] = []

    def chat(self, messages, cognitive_mode=""):
        self.chat_calls.append(list(messages))
        return "retry answer"


class _RetryCapability:
    def __init__(self):
        self.requires_tool_calls: list[str] = []
        self.detect_tool_call_inputs: list[str] = []
        self.execute_tool_typed_calls: list[str] = []

    def requires_tool(self, text: str) -> bool:
        self.requires_tool_calls.append(text)
        return True  # force the retry branch

    def detect_tool_call(self, reply: str) -> str | None:
        self.detect_tool_call_inputs.append(reply)
        return None  # no explicit tool call decoded

    def execute_tool_typed(self, tool_json: str):
        self.execute_tool_typed_calls.append(tool_json)
        raise AssertionError("execute_tool_typed must not be called in the retry branch")


class _RetryContextOS:
    def __init__(self):
        self.project_control_guidance_calls: list[dict[str, Any]] = []

    def project_control_guidance(self, **kwargs):
        self.project_control_guidance_calls.append(kwargs)
        return _DeltaPackage()


class _FakeAction:
    def start(self, *args, **kwargs):
        return None

    def finish(self, *args, **kwargs):
        return None


class _FakeRecorder:
    def record(self, *args, **kwargs):
        return None


def _retry_session(monkeypatch) -> JuliaSession:
    session = JuliaSession.__new__(JuliaSession)
    session.provider = _RetryProvider()
    session.capability = _RetryCapability()
    session.context_os = _RetryContextOS()
    session.action = _FakeAction()
    session.recorder = _FakeRecorder()

    class _FakePackage:
        package_id = "ctxpkg_retry"
        active_tail_messages: list[dict[str, Any]] = []

    def fake_prepare_turn(self, text, ctx):
        ctx._last_package = _FakePackage()
        return [{"role": "user", "content": text}]

    def fake_update_state(self, text, reply, ctx):
        return None

    monkeypatch.setattr(JuliaSession, "_prepare_turn", fake_prepare_turn)
    monkeypatch.setattr(JuliaSession, "_update_conversation_state", fake_update_state)
    return session


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.3: retry/control structured projection not implemented",
)
def test_session_retry_branch_projects_control_through_context_os(monkeypatch):
    session = _retry_session(monkeypatch)

    session.process("question needing evidence", [], conversation_id="conv", turn_id="turn")

    # Structured projection seam was used, not a direct message append.
    assert len(session.context_os.project_control_guidance_calls) == 1
    # No capability execution occurred for the no-tool-call branch.
    assert len(session.capability.execute_tool_typed_calls) == 0
    # pass-1 + exactly one retry provider call.
    assert len(session.provider.chat_calls) == 2
    # Retry messages do not contain the raw ad-hoc system prompt.
    retry_messages = session.provider.chat_calls[1]
    assert not any("[系统提示]" in str(m.get("content", "")) for m in retry_messages)
    # Continuation/retry consumed the rebuilt Context OS delta.
    assert SENTINEL in session.provider.chat_calls[1][0]["content"]


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.3: retry/control structured projection not implemented",
)
def test_session_retry_branch_does_not_append_direct_system_prompt():
    source = _session_source()
    assert "[系统提示]" not in source
    assert 'messages.append({"role": "user"' not in source

"""R2-P3.3 retry/control — P3-CC I2-B reclassification.

The legacy production retry branch
(``requires_tool(user_text) == True`` + no decoded tool call → forced retry
through ``project_retry_control``) is RETIRED (Class A). After I2-B, model
silence means an ordinary Julia answer — Runtime never coerces a retry from
user-text keywords and never consults ``requires_tool(...)``.

``project_retry_control()`` remains a Context OS structural primitive
(Class C): it is tested here directly, and must NOT be manufactured through a
retired semantic branch.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)
from julia_core.runtime.julia_session import JuliaSession


ROOT = Path(__file__).resolve().parents[2]


def _session_source() -> str:
    return (ROOT / "julia_core" / "runtime" / "julia_session.py").read_text()


class _NoopEventStore:
    def append(self, event):
        pass


class _ChatOnlyProvider:
    """Model always answers ordinarily — never emits a capability request."""

    def __init__(self):
        self.chat_calls: list[list[dict]] = []

    def chat(self, messages, cognitive_mode=""):
        self.chat_calls.append(list(messages))
        return "ordinary answer"


class _SpyCapability:
    def __init__(self):
        self.requires_tool_calls: list[str] = []
        self.detect_tool_call_inputs: list[str] = []
        self.execute_tool_typed_calls: list[str] = []

    def requires_tool(self, text: str) -> bool:
        # I2-B: this legacy signal exists on the compatibility surface but the
        # session must never consult it.
        self.requires_tool_calls.append(text)
        return True

    def detect_tool_call(self, reply: str) -> str | None:
        self.detect_tool_call_inputs.append(reply)
        return None

    def execute_tool_typed(self, tool_json: str):
        self.execute_tool_typed_calls.append(tool_json)
        raise AssertionError("execute_tool_typed must not run on model silence")


class _SpyContextOS:
    def __init__(self):
        self.project_retry_control_calls: list[dict[str, Any]] = []

    def prepare(self, **kwargs):
        pkg = CognitiveContextPackage()
        pkg.capability_frame = {"manifest_entries": [], "non_admitted_diagnostics": []}
        return pkg

    def project_retry_control(self, **kwargs):
        self.project_retry_control_calls.append(kwargs)
        raise AssertionError("retry projection must not be triggered by model silence")


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
    session.provider = _ChatOnlyProvider()
    session.capability = _SpyCapability()
    session.context_os = _SpyContextOS()
    session.action = _FakeAction()
    session.recorder = _FakeRecorder()
    monkeypatch.setattr(
        "julia_core.events.store.get_event_store", lambda: _NoopEventStore()
    )

    class _FakePackage:
        package_id = "ctxpkg_silent"
        conversation_id = "conv"
        turn_id = "turn"
        active_tail_messages: list[dict[str, Any]] = []

    def fake_prepare_turn(self, text, ctx):
        ctx._last_package = _FakePackage()
        return [{"role": "user", "content": text}]

    def fake_update_state(self, text, reply, ctx):
        return None

    monkeypatch.setattr(JuliaSession, "_prepare_turn", fake_prepare_turn)
    monkeypatch.setattr(JuliaSession, "_update_conversation_state", fake_update_state)
    return session


# ── Class A replacement: model silence after keywords = ordinary answer ──────

def test_model_silence_after_keywords_is_ordinary_answer_no_retry(monkeypatch):
    """MODEL_SILENCE_AFTER_KEYWORDS → ordinary answer; provider second-pass
    coercion = 0; requires_tool never consulted; no retry projection."""
    session = _retry_session(monkeypatch)
    session.process(
        "今天市场怎么样", [], conversation_id="conv", turn_id="turn"
    )

    assert len(session.provider.chat_calls) == 1
    assert session.provider.chat_calls[0][-1] == {"role": "user", "content": "今天市场怎么样"}
    # No forced retry / no capability execution / no keyword gate consultation.
    assert session.context_os.project_retry_control_calls == []
    assert session.capability.execute_tool_typed_calls == []
    assert session.capability.requires_tool_calls == []
    assert session.capability.detect_tool_call_inputs == [
        "ordinary answer"
    ]


def test_no_direct_system_prompt_or_user_append_in_session_source():
    source = _session_source()
    assert "[系统提示]" not in source
    assert 'messages.append({"role": "user"' not in source


# ── Class C: project_retry_control Context OS primitive (direct) ─────────────

def _parent_package() -> CognitiveContextPackage:
    parent = CognitiveContextPackage(
        conversation_id="conv", turn_id="turn", generation_id="gen_0"
    )
    parent.capability_frame = {
        "manifest_entries": [],
        "non_admitted_diagnostics": [],
    }
    return parent


def test_retry_control_primitive_projects_structured_delta():
    runtime = ContextExecutionRuntime()
    pkg = runtime.project_retry_control(
        parent_package=_parent_package(),
        reason="required_tool_call_missing",
        generation_id="gen_retry_1",
    )
    assert pkg.control_frame == {
        "kind": "retry_control",
        "reason": "required_tool_call_missing",
    }
    assert pkg.situation_frame == {"mode": "retry_control"}
    assert pkg.validate() == []
    # Governed capability manifest inherited from the parent package.
    assert pkg.capability_frame == {
        "manifest_entries": [],
        "non_admitted_diagnostics": [],
    }
    messages = pkg.to_messages([], "")
    assert any("retry_control" in str(m.get("content", "")) for m in messages)


def test_retry_control_primitive_fails_closed_on_bad_inputs():
    runtime = ContextExecutionRuntime()
    with pytest.raises(ValueError):
        runtime.project_retry_control(
            parent_package=_parent_package(),
            reason="unsupported_reason",
            generation_id="gen_retry_1",
        )
    with pytest.raises(ValueError):
        runtime.project_retry_control(
            parent_package=None,
            reason="required_tool_call_missing",
            generation_id="gen_retry_1",
        )
    with pytest.raises(ValueError):
        runtime.project_retry_control(
            parent_package=_parent_package(),
            reason="required_tool_call_missing",
            generation_id="   ",
        )

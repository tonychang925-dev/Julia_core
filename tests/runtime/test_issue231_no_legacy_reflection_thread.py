"""#231: the legacy every-10-turns reflection (recorder.consolidate) is no longer triggered."""
from __future__ import annotations

import time

import julia_core.events.store as event_store_module
import julia_core.runtime.julia_session as julia_session_module
from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
from tests.runtime.test_rd1_p2_i3b_production_iterative_reasoning_loop import parent_package


class _Provider:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, cognitive_mode):
        self.calls += 1
        return "Julia final answer"


class _Recorder:
    def __init__(self):
        self.recorded = 0
        self.consolidated = 0

    def record(self, *args, **kwargs):
        self.recorded += 1

    def consolidate(self, provider):  # must never be reached
        self.consolidated += 1
        provider.chat([], cognitive_mode="engineering_collaboration")


class _Store:
    def append(self, event):
        pass


def test_periodic_reflection_not_triggered_and_no_extra_model_call(monkeypatch):
    provider, recorder = _Provider(), _Recorder()
    session = julia_session_module.JuliaSession.__new__(julia_session_module.JuliaSession)
    session.provider = provider
    session.recorder = recorder
    session.context_os = ContextExecutionRuntime()
    session.capability = type("C", (), {})()

    def fake_prepare_turn(self, text, ctx):
        package = parent_package()
        ctx._last_package = package
        return package.to_messages(package.active_tail_messages, text)

    monkeypatch.setattr(julia_session_module.JuliaSession, "_prepare_turn", fake_prepare_turn)
    monkeypatch.setattr(julia_session_module.JuliaSession, "_update_conversation_state",
                        lambda self, text, reply, ctx: None)
    monkeypatch.setattr(event_store_module, "get_event_store", lambda: _Store())

    # ctx.turn_count starts at len(history)//2 and is advanced once per process();
    # 18 history messages -> turn_count 10 at the recorder step (the old trigger).
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": "x"} for i in range(18)]
    turns = 3
    for i in range(turns):
        assert session.process(f"hello {i}", list(history), conversation_id="c", turn_id=f"t{i}") == "Julia final answer"
    time.sleep(0.3)  # let a (legacy) daemon thread run if one were started

    assert recorder.recorded == 2 * turns        # recording is unchanged
    assert recorder.consolidated == 0            # no reflection thread
    assert provider.calls == turns               # exactly one model call per turn


def test_legacy_diary_writer_stays_disabled():
    import pytest
    from julia_core.runtime.session_recorder import SessionRecorder
    with pytest.raises(RuntimeError, match="disabled"):
        SessionRecorder._write_diary(object.__new__(SessionRecorder), {"diary_entry": "x"})

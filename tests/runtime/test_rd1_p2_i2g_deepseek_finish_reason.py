"""RD1-P2-I2G (CARD 2D, #201): incomplete DeepSeek completions fail closed.

Only ``finish_reason == "stop"`` with non-empty content is a cognition response.
Every other completion raises a typed provider error, and the turn surfaces as a
visible failure (``status="failed"``, empty content), never as partial text.
"""

from __future__ import annotations

import json
import tempfile
from types import SimpleNamespace

import pytest

from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository
from julia_core.providers.deepseek import (
    DeepSeekCognitionProvider,
    DeepSeekCognitionProviderError,
)
from julia_core.runtime.conversation_runtime import ConversationRuntime
from julia_core.runtime.iterative_reasoning import IterativeReasoningLoop
from tests.runtime.test_rd1_p2_i3b_production_iterative_reasoning_loop import (
    CHAIN,
    LoopSession,
    parent_package,
    tool_response,
)

TRUNCATED = '我的判断：这波机器人上涨是**"产业催化（特斯拉产能上调）+ 事件催'
_MISSING = object()


def _body(content: str, finish_reason=_MISSING) -> bytes:
    choice = {"index": 0, "message": {"role": "assistant", "content": content}}
    if finish_reason is not _MISSING:
        choice["finish_reason"] = finish_reason
    return json.dumps({"id": "x", "choices": [choice]}, ensure_ascii=False).encode("utf-8")


def test_stop_with_content_is_accepted():
    assert DeepSeekCognitionProvider._extract_content(_body("完整回答。", "stop")) == "完整回答。"


@pytest.mark.parametrize(
    "finish_reason,mention",
    [
        ("length", "'length'"),
        ("content_filter", "'content_filter'"),
        ("insufficient_system_resource", "'insufficient_system_resource'"),
        ("tool_calls", "'tool_calls'"),
        ("something_new", "'something_new'"),
        (None, "None"),
        (_MISSING, "<missing>"),
    ],
)
def test_non_stop_completion_fails_closed_and_names_the_reason(finish_reason, mention):
    with pytest.raises(DeepSeekCognitionProviderError) as raised:
        DeepSeekCognitionProvider._extract_content(_body(TRUNCATED, finish_reason))

    assert "incomplete" in str(raised.value)
    assert mention in str(raised.value)
    assert TRUNCATED not in str(raised.value)


def test_stop_with_empty_content_still_fails_closed():
    with pytest.raises(DeepSeekCognitionProviderError, match="empty"):
        DeepSeekCognitionProvider._extract_content(_body("   ", "stop"))


class _FakeHTTPResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_chat_transport_raises_on_truncated_completion(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    calls = []

    def fake_urlopen(*args, **kwargs):
        calls.append(args)
        return _FakeHTTPResponse(_body(TRUNCATED, "length"))

    monkeypatch.setattr("julia_core.providers.deepseek.urllib.request.urlopen", fake_urlopen)
    provider = DeepSeekCognitionProvider()

    with pytest.raises(DeepSeekCognitionProviderError, match="finish_reason='length'"):
        provider.chat([{"role": "user", "content": "q"}])
    assert len(calls) == 1  # no retry


class _ProviderBackedSession(LoopSession):
    """Every model pass goes through the real DeepSeek completion parser."""

    def __init__(self, completions: list[bytes]):
        super().__init__(responses=[])
        self.completions = list(completions)

    def chat(self, messages, cognitive_mode):
        self.model_inputs.append(messages)
        return DeepSeekCognitionProvider._extract_content(self.completions.pop(0))


def _run_turn(completions: list[bytes]):
    runtime = ConversationRuntime(
        repository=LegacyJsonConversationRepository(tempfile.mktemp(suffix=".json"))
    )
    runtime.create_conversation(conversation_id="c", title="c")
    session = _ProviderBackedSession(completions)

    def cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
        loop = IterativeReasoningLoop(
            session=session,
            text=text,
            turn_context=SimpleNamespace(turn_id=turn_id or "turn", correlation_id="corr"),
            messages=[{"role": "user", "content": text}],
            parent_package=parent_package(),
        )
        return loop.run().reply

    result = runtime.process_turn(
        conversation_id="c", turn_id="t1", modality="text", input="问题", cognitive_fn=cognitive
    )
    return runtime, session, result


def _assert_visible_failure(runtime, result):
    assert result.status == "failed"
    assert result.assistant_content == ""
    messages = runtime.get_messages("c")
    assistant = [m for m in messages if m.get("role") == "assistant"]
    assert [(m.get("status"), m.get("content")) for m in assistant] == [("failed", "")]
    assert TRUNCATED not in json.dumps(messages, ensure_ascii=False, default=str)


def test_truncated_first_pass_becomes_a_visible_failed_turn():
    runtime, session, result = _run_turn([_body(TRUNCATED, "length")])

    _assert_visible_failure(runtime, result)
    assert session.requests == []


def test_truncated_pass_after_a_tool_call_becomes_a_visible_failed_turn():
    runtime, session, result = _run_turn(
        [_body(tool_response(CHAIN[0]), "stop"), _body(TRUNCATED, "content_filter")]
    )

    _assert_visible_failure(runtime, result)
    assert len(session.requests) == 1  # the earlier call ran; no synthetic answer followed


def test_truncated_finalization_pass_becomes_a_visible_failed_turn():
    completions = [_body(tool_response(name), "stop") for name in CHAIN]
    completions.append(_body(TRUNCATED, "length"))
    runtime, session, result = _run_turn(completions)

    _assert_visible_failure(runtime, result)
    assert len(session.model_inputs) == 7
    assert len(session.requests) == 6


def test_complete_answer_still_completes():
    runtime, session, result = _run_turn([_body("完整的判断。", "stop")])

    assert result.status == "completed"
    assert result.assistant_content == "完整的判断。"

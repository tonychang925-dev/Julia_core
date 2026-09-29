"""RD1-P2-I2F (CARD 2C, #199): prose-tolerant decode, explicit non-execution feedback.

Fixtures are neutralized versions of real acceptance responses: the fence, JSON
and whitespace structure are kept exactly (prose, then a blank line, then one
```tool_call block), while the prose is replaced with neutral text of similar
length. The verbatim responses stay outside the repository.
"""

from __future__ import annotations

import json

import pytest

from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
from julia_core.runtime.iterative_reasoning import parse_strict_model_response
from tests.runtime.test_rd1_p2_i3b_production_iterative_reasoning_loop import (
    CHAIN,
    LoopSession,
    parent_package,
    run_loop,
    tool_response,
)

_BLOCKS = [
    ('```tool_call\n{"name":"market.event.resolve","arguments":{"feed_date":"2026-09-29","limit":20}}\n```',
     "market.event.resolve", 35),
    ('```tool_call\n{"name":"research.web.query","arguments":{"query":"机器人产业 2026年9月 最新动态 重要新闻"}}\n```',
     "research.web.query", 47),
    ('```tool_call\n{"name":"research.web.query","arguments":{"query":"机器人行业 人形机器人 最新新闻 2026年9月"}}\n```',
     "research.web.query", 124),
    ('```tool_call\n{"name":"research.web.query","arguments":{"query":"机器人产业最新动态 2026年9月 消息来源 权威媒体报道"}}\n```',
     "research.web.query", 60),
    ('```tool_call\n{"name":"market.event.resolve","arguments":{"feed_date":"2026-09-29","limit":50}}\n```',
     "market.event.resolve", 81),
    ('```tool_call\n{"name": "market.state.read", "arguments": {"trade_date": "2026-07-03"}}\n```',
     "market.state.read", 219),
]
_NEUTRAL = "这个问题需要外部证据，我先查询相关资料，拿到结果后再给出判断。"


def _neutral_prose(length: int) -> str:
    text = (_NEUTRAL * (length // len(_NEUTRAL) + 1))[: max(length - 2, 1)]
    return text + "\n\n"


NEUTRALIZED = [(_neutral_prose(n) + block, block, name) for block, name, n in _BLOCKS]


@pytest.mark.parametrize("response,block,name", NEUTRALIZED)
def test_prose_before_one_block_decodes_to_exactly_that_block(response, block, name):
    parsed = parse_strict_model_response(response)

    assert parsed.kind == "EXACTLY_ONE_STRUCTURED_CALL"
    assert parsed.surrounding_prose is True
    assert parsed.tool_call.name == name
    # Only the block content is executed, never the prose.
    assert parsed.tool_call.raw_json == block[len("```tool_call\n"):-len("\n```")]
    assert "证据" not in parsed.tool_call.raw_json


@pytest.mark.parametrize(
    "response",
    [
        _BLOCKS[1][0] + "\n\n查询发出后我会整理来源再回复。",
        "我先查一下。\n\n" + _BLOCKS[1][0] + "\n\n结果回来后再说。",
    ],
)
def test_prose_after_or_around_one_block_decodes(response):
    parsed = parse_strict_model_response(response)

    assert parsed.kind == "EXACTLY_ONE_STRUCTURED_CALL"
    assert parsed.surrounding_prose is True
    assert parsed.tool_call.name == "research.web.query"


def test_clean_block_is_unchanged_and_not_flagged():
    parsed = parse_strict_model_response(_BLOCKS[5][0])

    assert parsed.kind == "EXACTLY_ONE_STRUCTURED_CALL"
    assert parsed.surrounding_prose is False


_B = '```tool_call\n{"name": "research.web.query", "arguments": {"query": "q"}}\n```'


@pytest.mark.parametrize(
    "response",
    [
        "先查这个\n" + _B + "\n再查那个\n" + _B,
        '我去查\n```tool_call\n{"name": "research.web.query", "arguments": {\n```',
        '我去查\n```tool_call\n{"arguments": {"q": 1}}\n```',
        '我去查\n```\ntool_call\n{"name": "research.web.query", "arguments": {}}\n```',
        "我去查\n" + _B + '\n```json\n{"x": 1}\n```',
        '我去查\n```tool_call\n{"name": "research.web.query", "arguments": []}\n```',
        '我去查 ```tool_call {"name": "research.web.query", "arguments": {}} ```',
    ],
)
def test_ambiguous_or_malformed_carriers_still_fail_closed(response):
    parsed = parse_strict_model_response(response)

    assert parsed.kind == "TOOL_CALL_CONTROL_FAILURE"
    assert parsed.failure_reason == "INVALID_CALL_SHAPE"
    assert parsed.tool_call is None
    assert parsed.surrounding_prose is False


def test_plain_prose_is_still_final_text():
    assert parse_strict_model_response("证据不足，先不查。").kind == "FINAL_TEXT"


def test_loop_executes_block_beside_prose_and_flags_the_pass():
    response, block, _ = NEUTRALIZED[1]
    session = LoopSession([response, "Julia final judgment"])
    result = run_loop(session)

    assert session.requests == [block[len("```tool_call\n"):-len("\n```")]]
    assert result.capability_execution_count == 1
    assert result.cognition_pass_trace[0]["parsed_response_kind"] == "EXACTLY_ONE_STRUCTURED_CALL"
    assert result.cognition_pass_trace[0]["surrounding_prose"] is True
    assert "surrounding_prose" not in result.cognition_pass_trace[1]
    # The prose is never the user-facing reply.
    assert result.reply == "Julia final judgment"


def test_finalization_pass_with_prose_and_block_is_not_executed():
    session = LoopSession(
        [tool_response(name) for name in CHAIN] + [NEUTRALIZED[1][0]]
    )
    result = run_loop(session)

    assert result.termination == "finalization_no_text"
    assert result.final_response_kind == "CONTROL_FAILURE"
    assert result.capability_execution_count == 6
    assert len(session.requests) == 6
    assert result.cognition_pass_trace[-1]["surrounding_prose"] is True


@pytest.mark.parametrize(
    "reason,detail",
    [
        ("INVALID_CALL_SHAPE", "上一条回复中的调用没有被执行：调用块的格式不符合约定。"),
        ("MALFORMED_JSON", "上一条回复中的调用没有被执行：调用块里的 JSON 无法解析。"),
        ("MISSING_NAME", "上一条回复中的调用没有被执行：调用块缺少能力名称。"),
    ],
)
def test_decode_failure_control_frame_says_the_call_was_not_executed(reason, detail):
    package = ContextExecutionRuntime().project_tool_call_decode_failure(
        parent_package=parent_package(),
        reason=reason,
        generation_id="gen_decode",
    )

    assert package.control_frame["previous_call_executed"] is False
    assert package.control_frame["detail"] == detail
    # Existing fields are unchanged.
    assert package.control_frame["kind"] == "tool_call_decode_failure"
    assert package.control_frame["reason"] == reason
    assert "expected_invocation_protocol" in package.control_frame
    rendered = package._render_frame("control", package.control_frame)
    assert "previous_call_executed: False" in rendered
    assert detail in rendered


def test_retry_after_rejected_call_sees_explicit_non_execution():
    ambiguous = NEUTRALIZED[1][0] + "\n" + _B
    session = LoopSession([ambiguous, "Julia final judgment"])
    run_loop(session)

    retry_input = json.dumps(session.model_inputs[1], ensure_ascii=False)
    assert "previous_call_executed: False" in retry_input
    assert "上一条回复中的调用没有被执行" in retry_input
    assert session.requests == []

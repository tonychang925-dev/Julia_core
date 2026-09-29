"""RD1-P2-I2D F3 preflight: retry keeps intent; protocol example has no concrete date.

(a) After a malformed tool-call response, Julia's own raw response stays in the
    continuation as her assistant turn (as a successful call is kept), so the
    retry still sees what she tried. Lane B finalization is unchanged.
(b) The model-visible invocation-protocol example carries no YYYY-MM-DD date and
    no concrete capability id that could be copied into a real call.
"""

from __future__ import annotations

import json
import re

from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)
from tests.runtime.test_rd1_p2_i3b_production_iterative_reasoning_loop import (
    CHAIN,
    LoopSession,
    run_loop,
    tool_response,
)

# Real observed shape: prose before the fenced call (INVALID_CALL_SHAPE).
MALFORMED_WITH_PROSE = (
    "我先查一下外部研究。\n"
    "```tool_call\n"
    + json.dumps(
        {"name": "research.web.query", "arguments": {"query": "机器人板块 今日 上涨 原因"}},
        ensure_ascii=False,
    )
    + "\n```"
)
# Still rejected after CARD 2C (two fences), so the retry path is exercised.
MALFORMED_TWO_BLOCKS = MALFORMED_WITH_PROSE + "\n```tool_call\n{}\n```"
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def test_malformed_response_is_kept_as_assistant_turn_for_the_retry():
    session = LoopSession([MALFORMED_TWO_BLOCKS, "Julia final judgment"])
    result = run_loop(session)

    assert result.cognition_pass_trace[0]["parsed_response_kind"] == "TOOL_CALL_CONTROL_FAILURE"
    retry_input = session.model_inputs[1]
    assert {"role": "assistant", "content": MALFORMED_TWO_BLOCKS} in retry_input
    # The decode-failure control frame is still projected as before.
    assert "kind: tool_call_decode_failure" in str(retry_input)
    # The malformed response is not executed.
    assert session.requests == []
    assert result.final_response_kind == "JUDGMENT"
    assert result.termination == "completed"


def test_malformed_response_precedes_the_user_turn_like_a_successful_call():
    session = LoopSession(["```tool_call\n{broken\n```", "Julia final judgment"])
    run_loop(session)

    retry_input = session.model_inputs[1]
    roles_and_content = [(m["role"], m["content"]) for m in retry_input[1:]]
    assert roles_and_content[-2:] == [
        ("assistant", "```tool_call\n{broken\n```"),
        ("user", "Ask Julia"),
    ]


def test_successive_malformed_responses_all_stay_visible():
    first = "```tool_call\n{broken-1\n```"
    second = "```tool_call\n{broken-2\n```"
    session = LoopSession([first, second, "Julia final judgment"])
    run_loop(session)

    third_input = session.model_inputs[2]
    assert {"role": "assistant", "content": first} in third_input
    assert {"role": "assistant", "content": second} in third_input


def test_finalization_pass_malformed_call_still_fails_closed():
    session = LoopSession(
        [tool_response(name) for name in CHAIN] + [MALFORMED_WITH_PROSE]
    )
    result = run_loop(session)

    assert result.termination == "finalization_no_text"
    assert result.final_response_kind == "CONTROL_FAILURE"
    assert result.reply == (
        "Final cognition pass reserved for finalization; no final text was produced."
    )
    assert result.capability_execution_count == 6
    assert len(session.model_inputs) == 7


def _real_policy() -> dict:
    return RuntimeCapabilityBridge().invocation_policy()


def test_invocation_protocol_example_has_no_date_and_no_concrete_capability():
    bridge = RuntimeCapabilityBridge()
    example = bridge.invocation_policy()["invocation_protocol"]["example"]
    example_text = json.dumps(example, ensure_ascii=False)

    assert DATE_RE.search(example_text) is None
    # No dotted capability-shaped id at all (e.g. market.stock.quote.read).
    assert re.search(r"\b[a-z_]+\.[a-z_]+(\.[a-z_]+)*\b", example_text) is None
    assert example["name"].startswith("<") and example["name"].endswith(">")


def test_rendered_decode_failure_protocol_contains_no_date():
    parent = CognitiveContextPackage(
        conversation_id="conversation", turn_id="turn", generation_id="gen_initial"
    )
    parent.validated_invocation_policy = _real_policy()
    package = ContextExecutionRuntime().project_tool_call_decode_failure(
        parent_package=parent,
        reason="INVALID_CALL_SHAPE",
        generation_id="gen_decode",
    )
    rendered = package._render_frame("control", package.control_frame)

    assert "expected_invocation_protocol" in rendered
    assert "example=" in rendered
    assert DATE_RE.search(rendered) is None
    assert "market.stock.quote.read" not in rendered
    assert "600519.SH" not in rendered

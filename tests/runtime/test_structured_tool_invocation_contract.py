from __future__ import annotations

from types import SimpleNamespace

import pytest

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityStatus,
    Evidence,
    EvidenceSourceType,
    ToolResult,
    ToolResultStatus,
)
from julia_core.capability.registry import CapabilityRegistry
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)
from julia_core.runtime.iterative_reasoning import (
    IterativeReasoningLoop,
    parse_strict_model_response,
)


MALFORMED_FIRST_CALL = (
    '```tool_call\n'
    '{"capability_id":"market.stock.quote.read","stock_id":"600519.SH",'
    '"trade_date":"2026-09-23"}\n'
    '```'
)
VALID_SECOND_CALL = (
    '```tool_call\n'
    '{"name":"market.stock.quote.read","arguments":{"stock_id":"600519.SH",'
    '"trade_date":"2026-09-23"}}\n'
    '```'
)
PROSE_BEFORE_CALL = (
    "我来查一下。\n"
    "```tool_call\n"
    '{"name":"market.stock.quote.read","arguments":{"stock_id":"600519.SH",'
    '"trade_date":"2026-09-23"}}\n'
    "```"
)
PROSE_AFTER_CALL = (
    '```tool_call\n'
    '{"name":"market.stock.quote.read","arguments":{"stock_id":"600519.SH",'
    '"trade_date":"2026-09-23"}}\n'
    '```\n我查到了。'
)
PROSE_SURROUNDED_CALL = (
    "好，我帮你查一下 600519 今天的行情。\n"
    '```tool_call\n'
    '{"name":"market.stock.quote.read","arguments":{"stock_id":"600519.SH",'
    '"trade_date":"2026-09-23"}}\n'
    '```\n请稍等。'
)


def _registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register_definition(CapabilityDefinition(
        name="market.stock.quote.read",
        description="Read one exact stock/date daily quote",
        layer=CapabilityLayer.KNOWLEDGE,
        provider="market",
        permission_scope="market.read",
        input_schema={
            "stock_id": "exact source-namespaced stock identifier",
            "trade_date": "exact YYYY-MM-DD trade date",
        },
        status=CapabilityStatus.AVAILABLE,
    ))
    return registry


def _bridge_policy() -> dict:
    return RuntimeCapabilityBridge().invocation_policy()


def _parent() -> CognitiveContextPackage:
    package = CognitiveContextPackage(
        conversation_id="conversation",
        turn_id="turn",
        generation_id="generation-initial",
    )
    package.validated_invocation_policy = _bridge_policy()
    package.capability_frame = {
        "invocation_policy": package.validated_invocation_policy,
        "available_tools": [{
            "capability_id": "market.stock.quote.read",
            "description": "Read one exact stock/date daily quote",
            "input_schema": {
                "stock_id": "exact source-namespaced stock identifier",
                "trade_date": "exact YYYY-MM-DD trade date",
            },
        }],
    }
    package.situation_frame = {
        "current_turn_timestamp": "2026-09-23T10:15:30.123456+08:00",
        "current_date": "2026-09-23",
        "utc_offset": "+08:00",
    }
    return package


def test_initial_context_os_messages_expose_envelope_capability_and_schema():
    session = SimpleNamespace(
        persona=SimpleNamespace(get_traits_for_injection=lambda: ""),
        capability=SimpleNamespace(
            registry=_registry(),
            invocation_policy=_bridge_policy,
        ),
        _load_recent_experiences=lambda: "",
    )
    runtime = ContextExecutionRuntime(session)
    runtime._bootstrap_frames_cache = {}
    package = runtime.prepare(
        conversation_id="conversation",
        turn_id="turn",
        user_text="查一下 600519 今天的行情",
        history=[{
            "message_id": "message-current",
            "conversation_id": "conversation",
            "turn_id": "turn",
            "role": "user",
            "status": "completed",
            "created_at": "2026-09-23T10:15:30.123456+08:00",
            "content": "query",
        }],
    )
    rendered = package.to_messages([], "query")[0]["content"]

    assert "request_envelope=" in rendered
    assert "whole_response_must_be_tool_call=True" in rendered
    assert "surrounding_prose_allowed=False" in rendered
    assert "multiple_tool_call_fences_allowed=False" in rendered
    assert "ENTIRE assistant response" in rendered
    assert "before or after the block" in rendered
    assert "name=exact capability_id from available_tools" in rendered
    assert "arguments=object containing only that capability's arguments" in rendered
    assert "capability_id=market.stock.quote.read" in rendered
    assert "stock_id=exact source-namespaced stock identifier" in rendered
    assert "trade_date=exact YYYY-MM-DD trade date" in rendered
    assert "current_turn_timestamp: 2026-09-23T10:15:30.123456+08:00" in rendered
    assert "current_date: 2026-09-23" in rendered
    assert "utc_offset: +08:00" in rendered


def test_strict_parser_keeps_real_malformed_shape_invalid_and_valid_shape_exact():
    malformed = parse_strict_model_response(MALFORMED_FIRST_CALL)
    valid = parse_strict_model_response(VALID_SECOND_CALL)

    assert malformed.kind == "TOOL_CALL_CONTROL_FAILURE"
    assert malformed.failure_reason == "MISSING_NAME"
    assert malformed.tool_call is None
    assert valid.kind == "EXACTLY_ONE_STRUCTURED_CALL"
    assert valid.tool_call.capability_id == "market.stock.quote.read"
    assert valid.tool_call.arguments == {
        "stock_id": "600519.SH",
        "trade_date": "2026-09-23",
    }


@pytest.mark.parametrize(
    "response",
    [PROSE_BEFORE_CALL, PROSE_AFTER_CALL, PROSE_BEFORE_CALL + "\n```tool_call\n{}\n```"],
)
def test_strict_parser_rejects_surrounding_prose_and_multiple_fences(response):
    parsed = parse_strict_model_response(response)

    assert parsed.kind == "TOOL_CALL_CONTROL_FAILURE"
    assert parsed.failure_reason == "INVALID_CALL_SHAPE"
    assert parsed.tool_call is None


def test_decode_failure_projects_validated_contract_and_retains_capability_context():
    control = ContextExecutionRuntime().project_tool_call_decode_failure(
        parent_package=_parent(),
        reason="INVALID_CALL_SHAPE",
        generation_id="generation-decode",
    )
    rendered = control.to_messages([], "query")[0]["content"]

    assert control.control_frame["kind"] == "tool_call_decode_failure"
    assert control.control_frame["reason"] == "INVALID_CALL_SHAPE"
    assert control.control_frame["expected_invocation_protocol"] == (
        _bridge_policy()["invocation_protocol"]
    )
    instruction = control.control_frame["continuation_instruction"]
    assert "immediately preceding structured capability-call attempt" in instruction
    assert "preserve that intended name and arguments" in instruction
    assert "Do not switch capabilities" in instruction
    assert "capability_id=market.stock.quote.read" in rendered
    assert "stock_id=exact source-namespaced stock identifier" in rendered
    assert "trade_date=exact YYYY-MM-DD trade date" in rendered
    assert "name=exact capability_id from available_tools" in rendered
    assert "arguments=object containing only that capability's arguments" in rendered
    assert "whole_response_must_be_tool_call=True" in rendered
    assert "surrounding_prose_allowed=False" in rendered
    assert "multiple_tool_call_fences_allowed=False" in rendered
    assert "ENTIRE assistant response" in rendered


def test_model_generated_correction_executes_once_then_receives_evidence():
    evidence = Evidence(
        evidence_id="evidence-quote",
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref="capability:market.stock.quote.read",
        observed_at="2026-09-23T10:16:00+08:00",
        content_ref="tool_result:call-quote",
    )
    tool_result = ToolResult(
        capability_call_id="call-quote",
        status=ToolResultStatus.SUCCESS,
        structured_output={
            "operation_status": "SUCCESS",
            "data_state": "EMPTY",
        },
        evidence_refs=("evidence-quote",),
        provider="market",
    )
    outcome = SimpleNamespace(
        capability_call="capability-call-quote",
        tool_result=tool_result,
        evidence=(evidence,),
    )

    class Session:
        def __init__(self):
            self.model_inputs = []
            self.requests = []
            self.responses = [PROSE_SURROUNDED_CALL, VALID_SECOND_CALL, "No row is available."]
            self.provider = SimpleNamespace(chat=self.chat)
            self.context_os = ContextExecutionRuntime()
            self.action = SimpleNamespace(
                start=lambda *args, **kwargs: None,
                finish=lambda *args, **kwargs: None,
            )

        def chat(self, messages, cognitive_mode):
            self.model_inputs.append(messages)
            if cognitive_mode == "evidence_obligation_check":
                return (
                    "```evidence_obligation\n"
                    '{"unresolved_required_evidence":false,"evidence_intents":[]}'
                    "\n```"
                )
            return self.responses.pop(0)

        def _execute_tool_with_action(self, tool_json, turn_context):
            return None

        def _execute_typed_tool(self, tool_json):
            self.requests.append(tool_json)
            return outcome

        def _outcome_action_status(self, result):
            return "完成"

        def _dispatch_typed_outcome(self, result, turn_context, *, parent_package, generation_id):
            return self.context_os.project_tool_result(
                parent_package=parent_package,
                tool_result=result.tool_result,
                evidence=list(result.evidence),
                generation_id=generation_id,
            )

    parent = _parent()
    session = Session()
    result = IterativeReasoningLoop(
        session=session,
        text="查一下 600519 今天的行情",
        turn_context=SimpleNamespace(turn_id="turn", correlation_id="correlation"),
        messages=parent.to_messages([], "query"),
        parent_package=parent,
    ).run()

    assert result.reply == "No row is available."
    assert result.cognition_pass_count == 3
    assert result.capability_execution_count == 1
    assert result.executed_capability_ids == ["market.stock.quote.read"]
    assert result.evidence_generation_ids
    assert session.requests == [VALID_SECOND_CALL[13:-4]]
    correction_messages = session.model_inputs[1]
    assert any(
        message.get("role") == "assistant"
        and message.get("content") == PROSE_SURROUNDED_CALL
        for message in correction_messages
    )
    assert "INVALID_CALL_SHAPE" in str(correction_messages)
    assert "whole_response_must_be_tool_call=True" in str(session.model_inputs[1])
    assert "surrounding_prose_allowed=False" in str(session.model_inputs[1])
    assert "expected_invocation_protocol" in str(session.model_inputs[1])
    assert "Do not switch capabilities" in str(session.model_inputs[1])
    assert "operation_status=SUCCESS" in str(session.model_inputs[2])
    assert "data_state=EMPTY" in str(session.model_inputs[2])


def test_unknown_capability_is_not_aliased_to_stock_quote():
    outcome = RuntimeCapabilityBridge().execute_tool_typed(
        '{"name":"market.quote","arguments":{}}'
    )

    assert outcome.capability_id == "market.quote"
    assert outcome.reason == "UNKNOWN"

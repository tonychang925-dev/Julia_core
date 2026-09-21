from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import julia_core.runtime.julia_session as julia_session_module
import julia_core.events.store as event_store_module
from julia_core.capability.models import (
    Evidence,
    EvidenceSourceType,
    SideEffectState,
    ToolResult,
    ToolResultStatus,
)
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge, ToolCallDecodeFailure
from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)
from julia_core.runtime.iterative_reasoning import (
    MAX_CAPABILITY_EXECUTIONS_PER_TURN,
    MAX_COGNITION_PASSES_PER_TURN,
    IterativeReasoningLoop,
    parse_strict_model_response,
)


SOURCE_ROOT = Path(__file__).resolve().parents[2]
CHAIN = [
    "market.event.resolve",
    "market.event.read",
    "market.product.read",
    "market.product.linkage.read",
    "market.state.read",
    "research.web.query",
]


def tool_response(name: str, arguments: dict | None = None) -> str:
    return (
        "```tool_call\n"
        + json.dumps({"name": name, "arguments": arguments or {}}, sort_keys=True)
        + "\n```"
    )


def parent_package() -> CognitiveContextPackage:
    package = CognitiveContextPackage(
        conversation_id="conversation",
        turn_id="turn",
        generation_id="gen_initial",
    )
    package.validated_invocation_policy = {
        "invocation_protocol": {"raw_user_text_routing": False},
        "limits": {"max_tool_calls_per_model_response": 1},
    }
    return package


def execution(index: int):
    evidence_id = f"evidence_{index}"
    evidence = Evidence(
        evidence_id=evidence_id,
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref=f"source_{index}",
        observed_at="2026-09-21T00:00:00Z",
        content_ref=f"content_{index}",
    )
    tool_result = ToolResult(
        capability_call_id=f"call_{index}",
        status=ToolResultStatus.SUCCESS,
        evidence_refs=(evidence_id,),
        provider="test",
    )
    return SimpleNamespace(
        authorization_decision=SimpleNamespace(
            decision=SimpleNamespace(value="ALLOW"),
            scope="test",
            reason="allow",
        ),
        tool_result=tool_result,
        evidence=(evidence,),
    )


class LoopSession:
    def __init__(self, responses: list[str]):
        self.responses = list(responses)
        self.provider = SimpleNamespace(chat=self.chat)
        self.context_os = ContextExecutionRuntime()
        self.capability = SimpleNamespace(execute_tool_typed=self.execute)
        self.action = SimpleNamespace(start=self.start, finish=self.finish)
        self.requests: list[str] = []
        self.model_inputs: list[list[dict]] = []
        self.actions: list[str] = []

    def chat(self, messages, cognitive_mode):
        self.model_inputs.append(messages)
        return self.responses.pop(0)

    def execute(self, tool_json):
        self.requests.append(tool_json)
        return execution(len(self.requests))

    def start(self, name, description, correlation_id):
        self.actions.append(name)

    def finish(self, status, correlation_id):
        return None

    def _execute_tool_with_action(self, tool_json, turn_context):
        payload = json.loads(tool_json)
        self.actions.append(payload["name"])

    def _execute_typed_tool(self, tool_json):
        return self.capability.execute_tool_typed(tool_json)

    def _outcome_action_status(self, outcome):
        return "完成"

    def _dispatch_typed_outcome(self, outcome, turn_context, *, parent_package, generation_id):
        return self.context_os.project_tool_result(
            parent_package=parent_package,
            tool_result=outcome.tool_result,
            evidence=outcome.evidence,
            generation_id=generation_id,
        )


def run_loop(session: LoopSession):
    turn_context = SimpleNamespace(turn_id="turn", correlation_id="correlation")
    return IterativeReasoningLoop(
        session=session,
        text="Ask Julia",
        turn_context=turn_context,
        messages=[{"role": "user", "content": "Ask Julia"}],
        parent_package=parent_package(),
    ).run()


def test_julia_session_production_loop_runs_full_six_tool_chain(monkeypatch):
    class ProductionProvider:
        def __init__(self):
            self.responses = [
                tool_response(name, {"step": index})
                for index, name in enumerate(CHAIN, 1)
            ]
            self.responses.append("Julia final judgment")
            self.inputs: list[list[dict]] = []

        def chat(self, messages, cognitive_mode):
            self.inputs.append(messages)
            return self.responses.pop(0)

    class ProductionCapability:
        def __init__(self):
            self.requests: list[str] = []
            self.requires_tool_calls: list[str] = []

        def requires_tool(self, text):
            self.requires_tool_calls.append(text)
            return True

        def execute_tool_typed(self, tool_json):
            self.requests.append(tool_json)
            return execution(len(self.requests))

    class ProductionAction:
        def __init__(self):
            self.started: list[str] = []

        def start(self, name, description, correlation_id):
            self.started.append(name)

        def finish(self, status, correlation_id):
            return None

    class ProductionRecorder:
        def record(self, *args, **kwargs):
            return None

    class EventStore:
        def __init__(self):
            self.events = []

        def append(self, event):
            self.events.append(event)

    provider = ProductionProvider()
    capability = ProductionCapability()
    action = ProductionAction()
    event_store = EventStore()
    session = julia_session_module.JuliaSession.__new__(
        julia_session_module.JuliaSession
    )
    session.provider = provider
    session.capability = capability
    session.context_os = ContextExecutionRuntime()
    session.action = action
    session.recorder = ProductionRecorder()
    captured: dict[str, object] = {}

    def fake_prepare_turn(self, text, ctx):
        package = parent_package()
        ctx._last_package = package
        captured["initial_package"] = package
        return package.to_messages(package.active_tail_messages, text)

    def fake_update_state(self, text, reply, ctx):
        captured["turn_context"] = ctx

    monkeypatch.setattr(julia_session_module.JuliaSession, "_prepare_turn", fake_prepare_turn)
    monkeypatch.setattr(
        julia_session_module.JuliaSession,
        "_update_conversation_state",
        fake_update_state,
    )
    monkeypatch.setattr(event_store_module, "get_event_store", lambda: event_store)

    reply = session.process(
        "latest robotics industry external catalysts",
        [],
        conversation_id="conversation",
        turn_id="turn",
    )

    result = captured["turn_context"]._last_iterative_result
    assert reply == "Julia final judgment"
    assert result.cognition_pass_count == 7
    assert result.capability_execution_count == 6
    assert result.executed_capability_ids == CHAIN
    assert action.started == CHAIN
    assert capability.requires_tool_calls == []
    assert len(result.evidence_generation_ids) == 6
    ledger = captured["turn_context"]._last_package.evidence_frame[
        "turn_evidence_ledger"
    ]
    assert [entry["tool_result"]["capability_call_id"] for entry in ledger] == [
        f"call_{index}" for index in range(1, 7)
    ]
    rendered_final = str(provider.inputs[-1])
    assert all(f"source_{index}" in rendered_final for index in range(1, 7))


def test_strict_parser_accepts_only_one_exact_fenced_call():
    valid = parse_strict_model_response(tool_response("market.event.read", {"id": "e"}))
    assert valid.kind == "EXACTLY_ONE_STRUCTURED_CALL"
    assert valid.tool_call.capability_id == "market.event.read"

    for response in (
        "prefix\n" + tool_response("market.event.read"),
        tool_response("a") + "\n" + tool_response("b"),
        "```tool_call\n{broken}\n```",
        '```tool_call\n{"arguments":{}}\n```',
        '```tool_call\n{"name":"a","arguments":[]}\n```',
    ):
        parsed = parse_strict_model_response(response)
        assert parsed.kind == "TOOL_CALL_CONTROL_FAILURE"
        assert parsed.tool_call is None


def test_full_six_tool_chain_accumulates_ordered_evidence():
    responses = [tool_response(name, {"step": index}) for index, name in enumerate(CHAIN, 1)]
    responses.append("Julia final judgment")
    session = LoopSession(responses)
    result = run_loop(session)

    assert result.termination == "completed"
    assert result.final_response_kind == "JUDGMENT"
    assert result.cognition_pass_count == 7
    assert result.capability_execution_count == 6
    assert json.loads(session.requests[-1])["name"] == CHAIN[-1]
    assert session.actions == CHAIN
    assert len(result.projection_generation_ids) == 6
    assert len(set(result.projection_generation_ids)) == 6
    final_messages = session.model_inputs[-1]
    rendered = str(final_messages)
    assert all(f"source_{index}" in rendered for index in range(1, 7))


def test_duplicate_call_is_control_not_second_execution():
    session = LoopSession([
        tool_response("market.event.read", {"id": "same"}),
        tool_response("market.event.read", {"id": "same"}),
        "final",
    ])
    result = run_loop(session)
    assert result.capability_execution_count == 1
    assert len(session.requests) == 1


def test_tool_budget_fail_closes_without_extra_execution():
    responses = [tool_response(name) for name in CHAIN]
    responses.append(tool_response("another.tool"))
    session = LoopSession(responses)
    result = run_loop(session)
    assert result.capability_execution_count == 6
    assert len(session.requests) == 6
    assert len(session.model_inputs) == 7
    assert result.final_response_kind == "CONTROL_FAILURE"
    assert result.termination == "tool_call_budget_exceeded"


def test_cognition_limit_never_invokes_eighth_model_pass():
    session = LoopSession([tool_response(name) for name in CHAIN])
    session.responses.append(tool_response("another.tool"))
    result = run_loop(session)
    assert result.cognition_pass_count == MAX_COGNITION_PASSES_PER_TURN
    assert len(session.model_inputs) == 7
    assert result.final_response_kind == "CONTROL_FAILURE"


def test_decode_failures_are_typed_and_never_none():
    bridge = RuntimeCapabilityBridge()
    cases = {
        "{broken": "MALFORMED_JSON",
        '{"arguments":{}}': "MISSING_NAME",
        '{"name":"a","arguments":[]}': "INVALID_CALL_SHAPE",
    }
    for payload, reason in cases.items():
        outcome = bridge.execute_tool_typed(payload)
        assert isinstance(outcome, ToolCallDecodeFailure)
        assert outcome.reason == reason


def test_control_projection_inherits_ledger_without_appending_control():
    context_os = ContextExecutionRuntime()
    parent = context_os.project_tool_result(
        parent_package=parent_package(),
        tool_result=execution(1).tool_result,
        evidence=execution(1).evidence,
        generation_id="gen_tool_1",
    )
    control = context_os.project_tool_call_decode_failure(
        parent_package=parent,
        reason="MALFORMED_JSON",
        generation_id="gen_control_1",
    )
    assert control.control_frame["kind"] == "tool_call_decode_failure"
    assert control.evidence_frame["turn_evidence_ledger"] == parent.evidence_frame[
        "turn_evidence_ledger"
    ]
    assert control.validated_invocation_policy == parent.validated_invocation_policy


def test_i3_production_path_has_no_raw_text_router():
    session_source = (
        SOURCE_ROOT / "julia_core/runtime/julia_session.py"
    ).read_text(encoding="utf-8")
    context_source = (
        SOURCE_ROOT / "julia_core/runtime/context_execution_runtime.py"
    ).read_text(encoding="utf-8")
    chat_impl = session_source.split("def _chat_impl", 1)[1].split("def _execute_tool_with_action", 1)[0]
    assert "requires_tool(" not in chat_impl
    assert "_resolve_market_context(" not in context_source
    assert MAX_CAPABILITY_EXECUTIONS_PER_TURN == 6
    assert MAX_COGNITION_PASSES_PER_TURN == 7

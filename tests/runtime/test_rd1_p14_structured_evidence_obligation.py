from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from julia_core.capability.models import (
    Evidence,
    EvidenceSourceType,
    ToolResult,
    ToolResultStatus,
)
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)
from julia_core.runtime.iterative_reasoning import (
    IterativeReasoningLoop,
    parse_evidence_obligation_response,
)


def _obligation(unresolved: bool, intents: list[str] | None = None) -> str:
    return (
        "```evidence_obligation\n"
        + json.dumps(
            {
                "unresolved_required_evidence": unresolved,
                "evidence_intents": intents or [],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n```"
    )


def _tool_response(name: str, arguments: dict) -> str:
    return (
        "```tool_call\n"
        + json.dumps({"name": name, "arguments": arguments}, ensure_ascii=False)
        + "\n```"
    )


def _parent(*, external_tools: bool = True) -> CognitiveContextPackage:
    package = CognitiveContextPackage(
        conversation_id="conversation",
        turn_id="turn",
        generation_id="gen_initial",
    )
    package.validated_invocation_policy = RuntimeCapabilityBridge().invocation_policy()
    tools = []
    if external_tools:
        tools = [
            {
                "capability_id": "market.state.read",
                "description": "Read exact-date whole-market state evidence",
                "input_schema": {"trade_date": "exact YYYY-MM-DD trade date"},
            },
            {
                "capability_id": "research.web.query",
                "description": "Query source-bearing external web research evidence",
                "input_schema": {"query": "research question"},
            },
        ]
    package.capability_frame = {
        "invocation_policy": package.validated_invocation_policy,
        "available_tools": tools,
    }
    return package


def _research_outcome():
    evidence = Evidence(
        evidence_id="evidence-research",
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref="https://example.com/source",
        observed_at="2026-09-26T00:00:00Z",
        content_ref="tool_result:call-research",
    )
    tool_result = ToolResult(
        capability_call_id="call-research",
        status=ToolResultStatus.SUCCESS,
        structured_output={
            "query": "2026-07-09 A股 分化 政策 新闻",
            "findings": [{"summary": "external catalyst", "source_refs": ["source-1"]}],
            "sources": [{"ref": "source-1", "url": "https://example.com/source"}],
            "limitations": [],
            "provider": "test-research",
            "produced_at": "2026-09-26T00:00:00Z",
        },
        evidence_refs=("evidence-research",),
        provider="research",
    )
    return SimpleNamespace(
        authorization_decision=SimpleNamespace(
            decision=SimpleNamespace(value="ALLOW"),
            scope="research.observe",
            reason="allow",
        ),
        capability_call="capability-call-research",
        tool_result=tool_result,
        evidence=(evidence,),
    )


class Session:
    def __init__(
        self,
        *,
        cognition_responses: list[str],
        obligation_responses: list[str],
        outcomes: list | None = None,
    ):
        self.cognition_responses = list(cognition_responses)
        self.obligation_responses = list(obligation_responses)
        self.outcomes = list(outcomes or [])
        self.provider = SimpleNamespace(chat=self.chat)
        self.context_os = ContextExecutionRuntime()
        self.action = SimpleNamespace(
            start=lambda *args, **kwargs: None,
            finish=lambda *args, **kwargs: None,
        )
        self.model_calls: list[tuple[str, list[dict]]] = []
        self.requests: list[str] = []

    def chat(self, messages, cognitive_mode):
        self.model_calls.append((cognitive_mode, list(messages)))
        if cognitive_mode == "evidence_obligation_check":
            return self.obligation_responses.pop(0)
        return self.cognition_responses.pop(0)

    def _execute_tool_with_action(self, tool_json, turn_context):
        return None

    def _execute_typed_tool(self, tool_json):
        self.requests.append(tool_json)
        return self.outcomes.pop(0)

    def _outcome_action_status(self, outcome):
        return "完成"

    def _dispatch_typed_outcome(self, outcome, turn_context, *, parent_package, generation_id):
        return self.context_os.project_tool_result(
            parent_package=parent_package,
            tool_result=outcome.tool_result,
            evidence=outcome.evidence,
            generation_id=generation_id,
        )


def _run(session: Session, *, parent: CognitiveContextPackage | None = None):
    parent = parent or _parent()
    loop = IterativeReasoningLoop(
        session=session,
        text="请结合市场数据和外部新闻、政策证据分析原因。",
        turn_context=SimpleNamespace(turn_id="turn", correlation_id="correlation"),
        messages=parent.to_messages([], "请结合市场数据和外部新闻、政策证据分析原因。"),
        parent_package=parent,
    )
    return loop.run(), loop


def test_evidence_obligation_parser_is_strict_and_independent_from_tool_parser():
    required = parse_evidence_obligation_response(
        _obligation(True, ["external_evidence"])
    )
    resolved = parse_evidence_obligation_response(_obligation(False))

    assert required.kind == "DECISION"
    assert required.decision.unresolved_required_evidence is True
    assert required.decision.evidence_intents == ("external_evidence",)
    assert resolved.kind == "DECISION"
    assert resolved.decision.unresolved_required_evidence is False
    assert resolved.decision.evidence_intents == ()

    invalid = [
        "prose\n" + _obligation(True, ["external_evidence"]),
        "```evidence_obligation\n{broken}\n```",
        "```evidence_obligation\n"
        '{"unresolved_required_evidence":true,"evidence_intents":[],"extra":1}'
        "\n```",
        _obligation(True, []),
        _obligation(False, ["external_evidence"]),
    ]
    for response in invalid:
        assert parse_evidence_obligation_response(response).kind == "CONTROL_FAILURE"


def test_required_tool_retry_control_carries_only_generic_obligation_state():
    control = ContextExecutionRuntime().project_retry_control(
        parent_package=_parent(),
        reason="required_tool_call_missing",
        evidence_intents=("external_evidence",),
        generation_id="gen-required-tool",
    )

    assert control.control_frame["kind"] == "retry_control"
    assert control.control_frame["reason"] == "required_tool_call_missing"
    assert control.control_frame["evidence_intents"] == ["external_evidence"]
    assert "capability_id" not in control.control_frame
    instruction = control.control_frame["continuation_instruction"]
    assert "Select the appropriate available capability yourself" in instruction
    assert "Runtime is not selecting a capability for you" in instruction


def test_candidate_final_is_accepted_when_julia_structured_obligation_is_resolved():
    session = Session(
        cognition_responses=["Julia final judgment"],
        obligation_responses=[_obligation(False)],
    )
    result, _ = _run(session)

    assert result.reply == "Julia final judgment"
    assert result.termination == "completed"
    assert result.final_response_kind == "JUDGMENT"
    assert result.evidence_obligation_check_count == 1
    assert result.evidence_obligation_required_count == 0
    assert session.requests == []
    assert [mode for mode, _ in session.model_calls] == [
        "private_voice_continuity",
        "evidence_obligation_check",
    ]


def test_required_obligation_reuses_retry_control_then_julia_selects_capability():
    session = Session(
        cognition_responses=[
            "I need market data and external policy evidence before answering.",
            _tool_response(
                "research.web.query",
                {"query": "2026-07-09 A股 分化 政策 新闻"},
            ),
            "Julia evidence-based final judgment",
        ],
        obligation_responses=[
            _obligation(True, ["external_evidence"]),
            _obligation(False),
        ],
        outcomes=[_research_outcome()],
    )
    result, loop = _run(session)

    assert result.reply == "Julia evidence-based final judgment"
    assert result.termination == "completed"
    assert result.final_response_kind == "JUDGMENT"
    assert result.evidence_obligation_check_count == 2
    assert result.evidence_obligation_required_count == 1
    assert result.executed_capability_ids == ["research.web.query"]
    assert json.loads(session.requests[0])["name"] == "research.web.query"

    normal_calls = [messages for mode, messages in session.model_calls if mode == "private_voice_continuity"]
    retry_rendered = str(normal_calls[1])
    assert any(
        message.get("role") == "assistant"
        and message.get("content")
        == "I need market data and external policy evidence before answering."
        for message in normal_calls[1]
    )
    assert "required_tool_call_missing" in retry_rendered
    assert "external_evidence" in retry_rendered
    assert "Select the appropriate available capability yourself" in retry_rendered
    assert "Runtime is not selecting a capability for you" in retry_rendered

    ledger = loop.parent_package.evidence_frame["turn_evidence_ledger"]
    assert ledger[-1]["tool_result"]["capability_call_id"] == "call-research"


def test_malformed_obligation_decision_fails_closed_without_dispatch():
    session = Session(
        cognition_responses=["Candidate final"],
        obligation_responses=["yes, evidence is still needed"],
    )
    result, _ = _run(session)

    assert result.final_response_kind == "CONTROL_FAILURE"
    assert result.termination == "evidence_obligation_check_invalid"
    assert "failed closed" in result.reply
    assert session.requests == []


def test_obligation_decision_cannot_select_concrete_capability_id():
    session = Session(
        cognition_responses=["Candidate final"],
        obligation_responses=[_obligation(True, ["research.web.query"])],
    )
    result, _ = _run(session)

    assert result.final_response_kind == "CONTROL_FAILURE"
    assert result.termination == "evidence_obligation_check_invalid"
    assert "failed closed" in result.reply
    assert session.requests == []


def test_no_external_capability_means_no_obligation_probe():
    session = Session(
        cognition_responses=["Ordinary final"],
        obligation_responses=[],
    )
    result, _ = _run(session, parent=_parent(external_tools=False))

    assert result.reply == "Ordinary final"
    assert result.evidence_obligation_check_count == 0
    assert [mode for mode, _ in session.model_calls] == ["private_voice_continuity"]

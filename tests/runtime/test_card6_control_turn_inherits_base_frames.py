"""CARD 6 (#220): control/continuation turns keep the pass-1 base frames.

identity / experience / diary / continuity / situation(current date) come from the
parent package by deep copy; a control turn overrides only its own fields
(control, evidence, situation.mode)."""
from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

from julia_core.runtime.context_execution_runtime import CognitiveContextPackage, ContextExecutionRuntime
from julia_core.runtime.iterative_reasoning import IterativeReasoningLoop
from julia_core.capability.models import ToolResult, ToolResultStatus
from tests.runtime._card6_base import BASE_FRAMES, SITUATION, assert_inherits_base, populated_parent
from tests.runtime.test_rd1_p2_i3b_production_iterative_reasoning_loop import (
    LoopSession,
    execution,
    parent_package as policy_parent,
    tool_response,
)

EVIDENCE_CAP = CognitiveContextPackage._RENDER_MAX_FRAME_CHARS
MARKS = ("IDENTITY-MARK", "EXPERIENCE-MARK", "CONTINUITY-MARK", "DIARY-MARK", "2026-07-03", "2026-07-03T09:30:00+08:00")


def _tool_result() -> ToolResult:
    return ToolResult(capability_call_id="c1", status=ToolResultStatus.SUCCESS,
                      structured_output={"content": "x"}, provider="t")


def _decision(value="DENY"):
    return SimpleNamespace(decision=SimpleNamespace(value=value), scope="s", reason="r")


def _projections(parent):
    rt = ContextExecutionRuntime()
    return {
        "tool_continuation": rt.project_tool_result(parent_package=parent, tool_result=_tool_result(), generation_id="g1"),
        "authorization_outcome": rt.project_authorization_outcome(parent_package=parent, authorization_decision=_decision(), generation_id="g2"),
        "capability_resolution_failure": rt.project_capability_resolution_failure(parent_package=parent, capability_id="x.y", reason="UNKNOWN", generation_id="g3"),
        "retry_control": rt.project_retry_control(parent_package=parent, reason="required_tool_call_missing", generation_id="g4"),
        "tool_call_budget_exceeded_mode": rt.project_tool_budget_exceeded(parent_package=parent, limit=3, generation_id="g5"),
    }


@pytest.mark.parametrize("mode", ["tool_continuation", "authorization_outcome", "capability_resolution_failure", "retry_control", "tool_budget_exceeded"])
def test_every_control_kind_inherits_base_frames_and_overrides_only_mode(mode):
    parent = populated_parent()
    key = "tool_call_budget_exceeded_mode" if mode == "tool_budget_exceeded" else mode
    delta = _projections(parent)[key]
    assert_inherits_base(delta, parent, mode=mode)
    text = delta.to_messages(delta.active_tail_messages, "q")[0]["content"]
    for mark in MARKS:
        assert mark in text, (mode, mark)


def test_control_turn_mutation_does_not_touch_parent():
    parent = populated_parent()
    snapshot = copy.deepcopy({n: getattr(parent, n) for n in (*BASE_FRAMES, "situation_frame")})
    for delta in _projections(parent).values():
        delta.identity_frame["persona_traits"] = "MUTATED"
        delta.experience_frame["recent_context"] = "MUTATED"
        delta.diary_frame["diary_context"] = "MUTATED"
        delta.continuity_frame["narrative"] = "MUTATED"
        delta.situation_frame["current_date"] = "MUTATED"
        delta.situation_frame["extra"] = 1
    for name, value in snapshot.items():
        assert getattr(parent, name) == value, name
    # and children are independent of each other
    a, b = list(_projections(parent).values())[:2]
    a.identity_frame["persona_traits"] = "A"
    assert b.identity_frame["persona_traits"] != "A"


def test_control_projection_has_own_control_and_evidence_fields():
    parent = populated_parent()
    parent.control_frame = {"kind": "parent_only"}
    delta = ContextExecutionRuntime().project_retry_control(
        parent_package=parent, reason="required_tool_call_missing", generation_id="g_child")
    assert delta.control_frame == {"kind": "retry_control", "reason": "required_tool_call_missing"}


def _loop_parent():
    parent = policy_parent()
    for name, value in BASE_FRAMES.items():
        setattr(parent, name, copy.deepcopy(value))
    parent.situation_frame = copy.deepcopy(SITUATION)
    return parent


def test_pass3_after_two_tool_calls_still_has_identity_experience_continuity_and_date():
    session = LoopSession([
        tool_response("market.event.resolve", {"s": 1}),
        tool_response("market.event.read", {"s": 2}),
        "Julia final judgment",
    ])
    loop = IterativeReasoningLoop(
        session=session, text="Ask Julia",
        turn_context=SimpleNamespace(turn_id="turn", correlation_id="corr"),
        messages=[{"role": "user", "content": "Ask Julia"}],
        parent_package=_loop_parent(),
    )
    loop.run()
    assert len(session.model_inputs) == 3
    systems = [m[0]["content"] for m in session.model_inputs]
    for index, system in enumerate(systems):
        for mark in MARKS:
            assert mark in system, (index + 1, mark)
    # evidence block present on continuation passes, as before
    assert "evidence" in systems[1].lower() and "evidence" in systems[2].lower()
    # length budget: continuation system <= pass-1 system + evidence cap
    for system in systems[1:]:
        assert len(system) <= len(systems[0]) + EVIDENCE_CAP

"""R2-P3.3A structured retry control projection acceptance.

project_retry_control is an additive discriminated-union extension of the
control_frame (kind discriminator). It must NOT alter the frozen
capability_resolution_failure variant.
"""

from __future__ import annotations

import pytest

from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)


def _parent() -> CognitiveContextPackage:
    return CognitiveContextPackage(conversation_id="conv", turn_id="turn", generation_id="gen-before")


def _project(reason: str = "required_tool_call_missing", generation_id: str = "gen_retry_1"):
    return ContextExecutionRuntime().project_retry_control(
        parent_package=_parent(),
        reason=reason,
        generation_id=generation_id,
    )


def test_retry_control_exact_frame():
    delta = _project()
    assert delta.control_frame == {"kind": "retry_control", "reason": "required_tool_call_missing"}


def test_retry_control_exact_key_set():
    delta = _project()
    assert set(delta.control_frame.keys()) == {"kind", "reason"}


def test_retry_control_no_capability_id():
    delta = _project()
    assert "capability_id" not in delta.control_frame


def test_retry_control_parent_binding():
    parent = _parent()
    delta = ContextExecutionRuntime().project_retry_control(
        parent_package=parent,
        reason="required_tool_call_missing",
        generation_id="gen_retry_1",
    )
    assert delta.conversation_id == parent.conversation_id
    assert delta.turn_id == parent.turn_id


def test_retry_control_generation_preservation():
    delta = _project(generation_id="gen_retry_7")
    assert delta.generation_id == "gen_retry_7"


def test_retry_control_no_execution_artifacts():
    delta = _project()
    assert delta.evidence_frame == {}
    assert delta.identity_frame == {}
    assert delta.experience_frame == {}
    assert delta.diary_frame == {}
    assert delta.continuity_frame == {}
    assert delta.projection_metadata.get("identity_updated") is not True
    assert delta.projection_metadata.get("memory_updated") is not True


def test_retry_control_renders_without_tool_observation():
    delta = _project()
    rendered = "\n".join(str(m.get("content", "")) for m in delta.to_messages([], ""))
    assert "TOOL_OBSERVATION" not in rendered
    assert "retry_control" in rendered
    assert "required_tool_call_missing" in rendered


def test_retry_control_blank_generation_rejected():
    with pytest.raises(ValueError):
        ContextExecutionRuntime().project_retry_control(
            parent_package=_parent(),
            reason="required_tool_call_missing",
            generation_id="   ",
        )


def test_retry_control_unknown_reason_rejected():
    with pytest.raises(ValueError):
        ContextExecutionRuntime().project_retry_control(
            parent_package=_parent(),
            reason="some arbitrary prose",
            generation_id="gen_retry_1",
        )


def test_capability_resolution_failure_variant_unchanged():
    delta = ContextExecutionRuntime().project_capability_resolution_failure(
        parent_package=_parent(),
        capability_id="no.such",
        reason="UNKNOWN",
        generation_id="g2",
    )
    assert delta.control_frame == {
        "kind": "capability_resolution_failure",
        "capability_id": "no.such",
        "reason": "UNKNOWN",
    }

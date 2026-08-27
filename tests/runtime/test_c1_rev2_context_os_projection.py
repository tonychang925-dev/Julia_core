"""C1-R2.3 Context OS projection tests.

Protected contracts: C-03 / C-08 / C-12 / REV2 R2-I05/R2-I06/R2-I08
Expected baseline: PASS for existing Context OS projection direction; XFAIL for
frozen typed ToolResult/Evidence convergence and direct model-visible bypasses.
Known gaps: A-04, A-06, A-07, B-02 from conformance audit
Resolving phase: R2-P1 / R2-P2 / R2-P7

These tests protect the rule that capability execution output becomes
model-visible only through Context OS projection, and that Evidence remains
separate from Memory, Persona, Identity, Relationship, Action, and Trace.
"""

from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest

from julia_core.runtime.context_execution_runtime import CognitiveContextPackage, ContextExecutionRuntime
from julia_core.capability.models import CapabilityResult


ROOT = Path(__file__).resolve().parents[2]


def _dataclass_fields(cls: type[Any]) -> set[str]:
    assert is_dataclass(cls), f"{cls!r} must be a dataclass contract object"
    return {f.name for f in fields(cls)}


def test_project_tool_result_enters_evidence_frame_not_identity_or_memory_frames():
    """Existing direction guard: tool output is projected as evidence context only."""
    parent = CognitiveContextPackage(
        conversation_id="conv_c1_r2_3",
        turn_id="turn_c1_r2_3",
        generation_id="gen_before_tool",
    )
    runtime = ContextExecutionRuntime()

    delta = runtime.project_tool_result(
        parent_package=parent,
        tool_result='{"capability":"file.read","content":"observed fact"}',
        generation_id="gen_after_tool",
    )

    assert delta.conversation_id == parent.conversation_id
    assert delta.turn_id == parent.turn_id
    assert delta.generation_id == "gen_after_tool"
    assert delta.evidence_frame["source"] == "capability_execution"
    assert "observed fact" in delta.evidence_frame["tool_result"]

    assert delta.identity_frame == {}
    assert delta.experience_frame == {}
    assert delta.diary_frame == {}
    assert delta.continuity_frame == {}
    assert delta.capability_frame == {}


def test_project_tool_result_records_context_os_provenance():
    """Existing direction guard: projected capability output carries Context OS provenance."""
    parent = CognitiveContextPackage(conversation_id="conv", turn_id="turn", generation_id="gen_1")
    delta = ContextExecutionRuntime().project_tool_result(
        parent_package=parent,
        tool_result="capability observation",
        generation_id="gen_2",
    )

    assert any(
        entry["frame"] == "evidence"
        and entry["source_ref"] == "capability:tool_result"
        and entry["reason"] == "tool execution result"
        for entry in delta.provenance
    )


def test_projected_tool_result_renders_through_context_package_messages():
    """C-03 allows provider-specific rendering only after Context OS projection."""
    parent = CognitiveContextPackage(conversation_id="conv", turn_id="turn", generation_id="gen_1")
    delta = ContextExecutionRuntime().project_tool_result(
        parent_package=parent,
        tool_result="structured capability observation",
        generation_id="gen_2",
    )

    messages = delta.to_messages(history=[{"role": "assistant", "content": "must not be used"}], user_text="")

    assert messages[0]["role"] == "system"
    assert "[evidence]" in messages[0]["content"]
    assert "structured capability observation" in messages[0]["content"]


def test_capability_projection_is_not_a_memory_persona_or_relationship_write():
    """Evidence projection must not acquire identity/memory/persona/relationship authority."""
    delta = ContextExecutionRuntime().project_tool_result(
        parent_package=CognitiveContextPackage(conversation_id="conv", turn_id="turn", generation_id="gen_1"),
        tool_result="external observation",
        generation_id="gen_2",
    )

    rendered = "\n".join(str(message.get("content", "")) for message in delta.to_messages([], ""))
    forbidden_authority_terms = {
        "runtime_eligibility",
        "activation_weight",
        "identity_authority_granted",
        "persona_truth",
        "relationship_truth",
        "memory_write",
    }
    assert forbidden_authority_terms.isdisjoint(rendered.split())
    assert delta.projection_metadata.get("memory_updated") is not True
    assert delta.projection_metadata.get("identity_updated") is not True


def test_project_tool_result_accepts_typed_tool_result_not_flattened_string():
    """Frozen path must project typed ToolResult linked to Evidence, not a string blob."""
    from typing import get_type_hints

    hints = get_type_hints(ContextExecutionRuntime.project_tool_result)
    assert hints.get("tool_result") is not str


@pytest.mark.xfail(
    strict=True,
    reason="B-02 / C-12: current CapabilityResult is legacy and not a frozen ToolResult with evidence_refs; pending R2-P1",
)
def test_legacy_capability_result_is_not_the_model_visible_evidence_contract():
    """CapabilityResult must converge toward ToolResult; Evidence remains separately referenced."""
    actual = _dataclass_fields(CapabilityResult)
    assert "structured_output" in actual
    assert "evidence_refs" in actual
    assert "evidence" not in actual
    assert "data" not in actual


@pytest.mark.xfail(
    strict=True,
    reason="A-04 / C-03: JuliaSession forced-retry system prompt is appended directly to messages; pending R2-P2/R2-P4",
)
def test_julia_session_does_not_append_core_controlled_retry_prompt_directly():
    """Core-controlled retry instructions must enter through Context OS, not messages.append()."""
    source = (ROOT / "julia_core" / "runtime" / "julia_session.py").read_text()
    assert "[系统提示]" not in source
    assert "messages.append" not in source


@pytest.mark.xfail(
    strict=True,
    reason="A-06/A-07 / C-03+C-08: capability bridge still creates fenced tool_result prompt text; pending R2-P1/R2-P2",
)
def test_capability_bridge_does_not_flatten_tool_result_into_prompt_fence():
    """Provider-facing tool-result text blocks must be replaced by typed Context OS projection."""
    source = (ROOT / "julia_core" / "runtime" / "capability_bridge.py").read_text()
    assert "```tool_result" not in source
    assert "_format_tool_result" not in source

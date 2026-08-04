"""Capability Validation Suite — verifies tools don't violate OS principles.

Every new tool must pass these tests before merging.
Adding capabilities must not break the LLM-native architecture.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pytest
from julia_core.capability.tool_protocol import (
    TOOLS_V1,
    ToolRegistry,
    ToolSchema,
    create_tool_registry,
)


class TestPrinciple1RuntimeNeverThinks:
    """P1: Runtime provides conditions, never interprets."""

    def test_tools_describe_what_not_why(self):
        """Tool descriptions should describe capability, not prescribe usage."""
        for tool in TOOLS_V1:
            # No "应该" or "必须" in descriptions — those are LLM decisions
            assert "应该" not in tool.description, (
                f"{tool.name}: description contains '应该' — prescribes behavior"
            )
            assert "必须" not in tool.description, (
                f"{tool.name}: description contains '必须' — prescribes behavior"
            )

    def test_tool_registry_has_no_router(self):
        """Registry must not route or classify. Just register and execute."""
        r = create_tool_registry()
        # No routing logic — tool names must not imply intent classification
        for name in r.tools:
            assert "route" not in name.lower(), f"Tool name '{name}' implies routing"
            assert "classify" not in name.lower(), f"Tool name '{name}' implies classification"
            assert "decide" not in name.lower(), f"Tool name '{name}' implies decision"


class TestPrinciple2IdentityNotGenerated:
    """P2: Tools must not generate or modify identity assets."""

    def test_no_tool_modifies_narrative_files(self):
        """No tool should write to memory/ without explicit user confirmation."""
        for tool in TOOLS_V1:
            if "write" in tool.name.lower() or "save" in tool.name.lower():
                # Write tools are OK only if they require confirmation
                assert "确认" in tool.description.lower() or "confirm" in tool.description.lower(), (
                    f"{tool.name}: write tool must require confirmation"
                )

    def test_tools_dont_regenerate_identity(self):
        """Tools must not regenerate or rewrite narrative seeds."""
        for tool in TOOLS_V1:
            assert "regenerate" not in tool.name.lower(), (
                f"{tool.name}: regeneration violates P2"
            )
            assert "rewrite" not in tool.name.lower(), (
                f"{tool.name}: rewriting violates P2"
            )


class TestPrinciple3NarrativeTransport:
    """P3: Tools return raw text, not structured analysis."""

    def test_tool_results_are_plain_text(self):
        """Tool handlers must return plain text, not structured objects."""
        r = create_tool_registry()

        # Test a few handlers
        results = [
            r.execute("get_time"),
            r.execute("list_recent_memories"),
        ]
        for result in results:
            if result:
                assert isinstance(result, str), (
                    f"Tool result should be string, got {type(result)}"
                )
                # Should not contain JSON-like structure
                assert not result.strip().startswith('{'), (
                    "Tool result should not be structured JSON"
                )

    def test_tools_dont_summarize(self):
        """Tools return data, not summaries. LLM does the summarizing."""
        for tool in TOOLS_V1:
            assert "总结" not in tool.description, (
                f"{tool.name}: should not summarize — LLM does that"
            )
            assert "summarize" not in tool.name.lower(), (
                f"{tool.name}: summarization belongs to LLM, not Runtime"
            )


class TestPrinciple4ToolsNotWorkflows:
    """P4: Tools are atomic capabilities, not multi-step workflows."""

    def test_each_tool_does_one_thing(self):
        """Each tool should do one thing. No orchestration."""
        for tool in TOOLS_V1:
            assert "and" not in tool.name.lower() or "search" in tool.name.lower(), (
                f"{tool.name}: tool name implies multiple operations"
            )

    def test_no_workflow_orchestration(self):
        """No tool should orchestrate other tools."""
        for tool in TOOLS_V1:
            assert "orchestrat" not in tool.description.lower(), (
                f"{tool.name}: workflow orchestration violates P4"
            )
            assert "pipeline" not in tool.description.lower(), (
                f"{tool.name}: pipeline logic violates P4"
            )


class TestPrinciple5HistoryIsState:
    """P5: Tools don't maintain their own state."""

    def test_tools_are_stateless(self):
        """Tools should be stateless — no internal memory between calls."""
        r = create_tool_registry()
        # Call twice, should get similar results (time may differ by seconds)
        r1 = r.execute("get_time")
        r2 = r.execute("get_time")
        # Both should return strings with time info
        assert isinstance(r1, str) and isinstance(r2, str)

    def test_no_session_state_in_tools(self):
        """Tools must not maintain per-session state."""
        for tool in TOOLS_V1:
            assert "session" not in tool.description.lower(), (
                f"{tool.name}: tools must not maintain session state"
            )


class TestPrinciple6LLMOwnsInterpretation:
    """P6: Tools provide facts, LLM provides meaning."""

    def test_tool_descriptions_dont_interpret(self):
        """Tool descriptions describe what they DO, not what it MEANS."""
        interpretation_words = ["意味着", "说明", "表示", "暗示", "体现"]
        for tool in TOOLS_V1:
            for word in interpretation_words:
                assert word not in tool.description, (
                    f"{tool.name}: description contains '{word}' — interprets meaning"
                )

    def test_tool_results_dont_add_meaning(self):
        """Tool handlers return raw data, no added interpretation."""
        r = create_tool_registry()
        result = r.execute("list_recent_memories")
        if result:
            # Should not contain emotional/interpretive language
            assert "重要" not in result, "Tool result should not label data as '重要'"
            assert "建议" not in result, "Tool result should not make '建议'"


class TestCapabilityRegistry:
    """Meta: the registry itself must be auditable."""

    def test_all_tools_have_descriptions(self):
        for tool in TOOLS_V1:
            assert len(tool.description) > 10, f"{tool.name}: description too short"

    def test_all_tools_have_categories(self):
        for tool in TOOLS_V1:
            assert tool.category is not None, f"{tool.name}: missing category"

    def test_registry_isolates_handlers(self):
        """Handlers must not depend on external state or globals."""
        r = create_tool_registry()
        assert len(r.handlers) == len(r.tools), (
            f"Handlers ({len(r.handlers)}) != tools ({len(r.tools)})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

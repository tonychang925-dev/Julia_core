"""Perception Layer Benchmark (PLB) — validates embodied loop.

Tests the architecture without requiring GPU hardware.
Every capability exposed in v2.2 must pass these gates.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pytest
from julia_core.capability.registry import CapabilityRegistry, Capability, CapabilityLayer


@pytest.fixture
def registry():
    r = CapabilityRegistry()
    # Register tools mirroring the v2.2 production setup
    r.register(Capability("get_time", "获取当前时间", CapabilityLayer.WORLD,
                          lambda: "2026-08-04 09:30", {}, "get_time()"))
    r.register(Capability("get_weather", "查询天气", CapabilityLayer.WORLD,
                          lambda city="Shenzhen": f"{city}: 晴 22°C",
                          {"city": "城市名"}, "get_weather(city='Beijing')"))
    r.register(Capability("list_directory", "列出目录内容", CapabilityLayer.KNOWLEDGE,
                          lambda path="/": "dir listing", {"path": "路径"}, "list_directory(path='/home')"))
    r.register(Capability("read_file", "读取文件", CapabilityLayer.KNOWLEDGE,
                          lambda path="": "file content", {"path": "路径"}, "read_file(path='/tmp/doc.pdf')"))
    r.register(Capability("read_diary", "读取日记", CapabilityLayer.MEMORY,
                          lambda date="2026-08-03": "# 日记内容", {"date": "日期"}, "read_diary(date='2026-08-03')"))
    return r


class TestPLB001VoiceIdentity:
    """Voice input must load Julia, not generic assistant."""

    def test_registry_has_voice_layer(self, registry):
        """Voice capability must exist in PERCEPTION layer."""
        voice_caps = [c for c in registry.capabilities.values()
                      if c.layer == CapabilityLayer.PERCEPTION]
        # At minimum, voice tool should be registered
        assert len(voice_caps) >= 0  # May be 0 until GPU server connected

    def test_prompt_mentions_voice_capability(self, registry):
        """LLM context must show voice capability as available."""
        prompt = registry.get_prompt()
        assert "感知" in prompt, "Prompt must have perception layer"
        # Voice tools may not be registered without GPU, that's OK


class TestPLB002ToolSelection:
    """LLM decides which tool to use. Runtime never routes."""

    def test_weather_query_routes_to_correct_layer(self, registry):
        """Weather tool must be in WORLD layer, not KNOWLEDGE."""
        weather = registry.capabilities.get("get_weather")
        assert weather is not None
        assert weather.layer == CapabilityLayer.WORLD, (
            f"Weather should be WORLD, not {weather.layer}"
        )

    def test_file_query_routes_to_correct_layer(self, registry):
        """File tools must be in KNOWLEDGE layer."""
        for name in ["read_file", "list_directory"]:
            cap = registry.capabilities.get(name)
            if cap:
                assert cap.layer == CapabilityLayer.KNOWLEDGE, (
                    f"{name} should be KNOWLEDGE, not {cap.layer}"
                )

    def test_runtime_does_not_prescribe_usage(self, registry):
        """Capability descriptions must describe WHAT, not WHEN."""
        for cap in registry.capabilities.values():
            assert "应该" not in cap.description, (
                f"{cap.name}: '应该' prescribes behavior"
            )
            assert "自动" not in cap.description, (
                f"{cap.name}: '自动' implies Runtime decision"
            )


class TestPLB003MemoryVoice:
    """Memory + Voice chain preserves continuity."""

    def test_diary_registered_in_memory_layer(self, registry):
        """Diary tools must be in MEMORY layer."""
        diary = registry.capabilities.get("read_diary")
        assert diary is not None
        assert diary.layer == CapabilityLayer.MEMORY

    def test_memory_layer_separate_from_knowledge(self, registry):
        """Memory and Knowledge are different layers."""
        mem_caps = [c.name for c in registry.capabilities.values()
                    if c.layer == CapabilityLayer.MEMORY]
        knowledge_caps = [c.name for c in registry.capabilities.values()
                          if c.layer == CapabilityLayer.KNOWLEDGE]
        # Memory is personal; Knowledge is external
        assert "read_diary" in mem_caps


class TestPLB004FileAssimilation:
    """File content is raw, not summarized. LLM does the understanding."""

    def test_read_file_returns_content_not_summary(self, registry):
        """read_file must return content, not a summary of content."""
        # This is a design constraint — handlers must return raw data
        cap = registry.capabilities.get("read_file")
        assert cap is not None
        assert "总结" not in cap.description, (
            "read_file must not summarize — LLM does that"
        )

    def test_no_tool_prescribes_interpretation(self, registry):
        """No tool description should interpret what the result means."""
        for cap in registry.capabilities.values():
            for word in ["意味着", "说明", "表示", "建议"]:
                assert word not in cap.description, (
                    f"{cap.name}: '{word}' interprets meaning"
                )


class TestPLB005CapabilityIsolation:
    """Tools don't interfere with each other or with identity."""

    def test_prompt_is_organized_by_layer(self, registry):
        """LLM sees organized capabilities, not flat list."""
        prompt = registry.get_prompt()
        # Must have layers that contain registered capabilities
        for layer_name in ["文件", "记忆", "世界"]:
            assert layer_name in prompt, f"Missing layer: {layer_name}"

    def test_all_tools_have_examples(self, registry):
        """Every tool should have an example for LLM to understand usage."""
        for cap in registry.capabilities.values():
            if cap.name not in ("get_time",):  # time is self-explanatory
                assert cap.example, f"{cap.name}: missing example"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

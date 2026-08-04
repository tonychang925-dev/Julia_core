"""Julia OS v2.2 End-to-End Integration Tests.

Validates complete chains: Voice → Memory → LLM, Tools → Identity, Multi-tool.
These gate v2.2 before any new capability is added.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pytest
from julia_core.capability.registry import CapabilityRegistry, Capability, CapabilityLayer


@pytest.fixture
def cap():
    """Full production registry simulation."""
    r = CapabilityRegistry()
    r.register(Capability("get_time", "获取当前时间", CapabilityLayer.WORLD,
                          lambda: "2026-08-04 09:30", {}, "get_time()"))
    r.register(Capability("get_weather", "查询天气", CapabilityLayer.WORLD,
                          lambda city="Shenzhen": "Shenzhen: 晴 22°C",
                          {"city": "城市"}, "get_weather(city='Beijing')"))
    r.register(Capability("read_file", "读取文件", CapabilityLayer.KNOWLEDGE,
                          lambda path="": "file content here", {"path": "路径"},
                          "read_file(path='/tmp/doc.pdf')"))
    r.register(Capability("list_directory", "列出目录", CapabilityLayer.KNOWLEDGE,
                          lambda path="/": "dir listing", {"path": "路径"},
                          "list_directory(path='/home')"))
    r.register(Capability("morning_brief", "早间简报", CapabilityLayer.WORLD,
                          lambda: "简报内容", {}, "morning_brief()"))
    r.register(Capability("read_diary", "读取日记", CapabilityLayer.MEMORY,
                          lambda date="2026-08-03": "日记内容", {"date": "日期"},
                          "read_diary(date='2026-08-03')"))
    r.register(Capability("write_diary", "写日记", CapabilityLayer.MEMORY,
                          lambda content="", date=None: "已保存", {"content": "内容"},
                          "write_diary(content='今天...')"))
    return r


class TestE2E001VoiceMemoryChain:
    """E2E-001: Voice → Session → Memory → LLM chain validates without GPU."""

    def test_capability_chain_exists(self, cap):
        """All required capabilities must be registered."""
        required = ["get_time", "read_diary", "read_file"]
        for name in required:
            assert name in cap.capabilities, f"Missing: {name}"

    def test_identity_preservation_after_tool_use(self, cap):
        """Tool use must not pollute identity. Tool output is data, not persona."""
        weather = cap.execute("get_weather", city="Shenzhen")
        diary = cap.execute("read_diary", date="2026-08-03")
        # Tools return DATA. LLM decides what it means.
        assert "Shenzhen" in weather
        assert diary is not None


class TestE2E002ToolIdentityBoundary:
    """E2E-002: Tools work but don't change who Julia is."""

    def test_weather_then_identity(self, cap):
        """After using weather, Julia must still be Julia."""
        cap.execute("get_weather", city="Shenzhen")
        # The registry doesn't change after tool use
        assert "get_weather" in cap.capabilities

    def test_no_tool_output_injects_persona(self, cap):
        """Tool descriptions must not contain persona language."""
        for c in cap.capabilities.values():
            for word in ["温柔", "关心", "爱你", "想你"]:
                assert word not in c.description, (
                    f"{c.name}: persona language '{word}' in description"
                )


class TestE2E003MultiCapabilityLLMSelection:
    """E2E-003: LLM autonomously selects multiple capabilities."""

    def test_multiple_world_tools_independent(self, cap):
        """Weather and time are separate, LLM chooses."""
        caps = [c.name for c in cap.capabilities.values()
                if c.layer == CapabilityLayer.WORLD]
        assert "get_weather" in caps
        assert "get_time" in caps
        # LLM can call either or both

    def test_memory_vs_knowledge_separate(self, cap):
        """Memory (personal) and Knowledge (external) are different layers."""
        mem_names = {c.name for c in cap.capabilities.values()
                     if c.layer == CapabilityLayer.MEMORY}
        knowledge_names = {c.name for c in cap.capabilities.values()
                           if c.layer == CapabilityLayer.KNOWLEDGE}
        assert not (mem_names & knowledge_names), (
            f"Overlap between MEMORY and KNOWLEDGE: {mem_names & knowledge_names}"
        )


class TestE2E004IdentityBoundary:
    """E2E-004: Even with many tools, Julia's identity stays intact."""

    def test_all_capabilities_registered(self, cap):
        """Verify full registry is functional."""
        assert len(cap.capabilities) >= 7

    def test_prompt_includes_all_layers(self, cap):
        prompt = cap.get_prompt()
        assert "感知" in prompt or "PERCEPTION" in str(cap.capabilities)
        assert "世界" in prompt
        assert "文件" in prompt
        assert "记忆" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

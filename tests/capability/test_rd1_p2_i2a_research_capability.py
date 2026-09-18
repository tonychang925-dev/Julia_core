from __future__ import annotations

import json
from pathlib import Path

import pytest

from julia_core.capability.models import CapabilityStatus, ProviderExecutionOutcome, SideEffectState, ToolResultStatus
from julia_core.capability.policy import AuthorizationStatus
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


ROOT = Path(__file__).resolve().parents[2]
TOOL_JSON = json.dumps(
    {"name": "research.web.query", "arguments": {"query": "robotics sector external catalysts"}}
)


def research_result() -> dict:
    return {
        "query": "robotics sector external catalysts",
        "findings": [
            {
                "statement": "Robotics adoption is accelerating in logistics and manufacturing.",
                "source_ref": "source:robotics-catalysts-2026",
                "confidence": 0.82,
            }
        ],
        "sources": [
            {
                "ref": "source:robotics-catalysts-2026",
                "title": "Deterministic Robotics Catalyst Brief",
                "url": "https://example.com/robotics-catalysts",
                "published_at": "2026-09-17T00:00:00Z",
            }
        ],
        "limitations": [
            "Deterministic test provider; no live web acquisition in P2-I2A"
        ],
        "provider": "deterministic-research-test-provider",
        "produced_at": "2026-09-18T00:00:00Z",
    }


class DeterministicResearchProvider:
    def __init__(self) -> None:
        self.requests = []

    async def health(self) -> tuple[bool, str]:
        return True, "research test provider bound"

    async def execute(self, request):
        self.requests.append(request)
        return ProviderExecutionOutcome(
            status=ToolResultStatus.SUCCESS,
            structured_output=research_result(),
            side_effect_state=SideEffectState.NONE,
        )


class MalformedResearchProvider:
    def __init__(self, result: dict) -> None:
        self.result = result

    async def health(self) -> tuple[bool, str]:
        return True, "malformed research fixture bound"

    async def execute(self, request):
        return self.result


def test_research_capability_registry_contract_and_permission():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    definition = bridge.registry.get("research.web.query")
    decision = bridge.policy.check("research.observe")

    assert definition is not None
    assert definition.provider == "research"
    assert definition.permission_scope == "research.observe"
    assert definition.status is CapabilityStatus.AVAILABLE
    assert definition.layer.value == "intelligence"
    assert definition.input_schema == {"query": "research question"}
    assert decision.decision is AuthorizationStatus.ALLOW
    assert bridge.policy.check("unknown.research.scope").decision is AuthorizationStatus.DENY


def test_missing_research_provider_is_typed_unavailable_without_fallback():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)
    result = execution.tool_result

    assert result.status.value == "unavailable"
    assert result.error["code"] == "provider_not_found"
    assert result.structured_output == {}
    assert bridge.manager.providers.get("research") is None


def test_source_bearing_research_result_is_preserved_without_semantic_normalization():
    provider = DeterministicResearchProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", provider)
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)
    result = execution.tool_result

    assert result.status.value == "success"
    assert result.side_effect_state is SideEffectState.NONE
    assert result.structured_output == research_result()
    assert result.error is None
    assert len(provider.requests) == 1
    assert provider.requests[0].capability_id == "research.web.query"
    assert provider.requests[0].arguments == {
        "query": "robotics sector external catalysts"
    }


@pytest.mark.parametrize(
    "mutation",
    [
        lambda result: result.pop("sources"),
        lambda result: result.update(sources=[]),
        lambda result: result.update(sources=[{"title": "No inspectable reference"}]),
        lambda result: result.pop("provider"),
        lambda result: result.pop("produced_at"),
    ],
)
def test_malformed_research_success_fails_closed_before_evidence_admission(mutation):
    result = research_result()
    mutation(result)
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", MalformedResearchProvider(result))
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)
    tool_result = execution.tool_result

    assert tool_result.status.value == "error"
    assert tool_result.structured_output == {}
    assert tool_result.error["code"] == "research_contract_invalid"
    assert tool_result.evidence_refs == ()
    assert bridge.manager.canonical_evidence == []


def test_tool_manifest_distinguishes_file_privacy_from_research_evidence_need():
    bridge = RuntimeCapabilityBridge()
    manifest = bridge.tool_manifest()

    assert "research.web.query" in manifest
    assert "file.* 只有在Tony明确要求读取/搜索/列出文件时才可以调用" in manifest
    assert "market.* / research.* 是READ_ONLY证据能力" in manifest
    assert "工具结果只是证据，不是最终判断" in manifest
    assert "一个回复最多一个工具调用" in manifest
    assert "只有用户明确要求读取/搜索/列出时才使用工具" not in manifest


def test_raw_user_text_cannot_route_to_research_without_structured_cognition_call():
    bridge = RuntimeCapabilityBridge()
    source = (ROOT / "julia_core/runtime/capability_bridge.py").read_text(encoding="utf-8")
    requires_tool_source = source.split("def requires_tool", 1)[1].split(
        "def detect_tool_call", 1
    )[0]

    assert bridge.requires_tool("robotics sector external catalysts") is False
    assert bridge.requires_tool("请读取 README.md") is True
    assert bridge.requires_tool("帮我看看这个文件") is True
    assert bridge.requires_tool("搜索一下最近的机器人新闻") is False
    assert bridge.requires_tool("找一下机器人板块的外部催化") is False
    assert bridge.requires_tool("/Users/tony/notes/robotics.md") is True
    assert "research" not in requires_tool_source
    assert bridge.detect_tool_call("robotics sector external catalysts") is None
    assert bridge.detect_tool_call(f"```tool_call\n{TOOL_JSON}\n```") == TOOL_JSON

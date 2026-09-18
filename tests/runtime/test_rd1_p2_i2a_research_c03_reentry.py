from __future__ import annotations

import json

from julia_core.runtime import capability_bridge as bridge_module
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.julia_session import JuliaSession


TOOL_JSON = json.dumps(
    {"name": "research.web.query", "arguments": {"query": "robotics sector external catalysts"}}
)


class ResearchCognitionInstrumentation:
    def __init__(self) -> None:
        self.calls: list[list[dict]] = []

    def chat(self, messages: list[dict], *, cognitive_mode: str = "") -> str:
        self.calls.append([dict(message) for message in messages])
        if len(self.calls) == 1:
            first_pass_policy = str(messages[0]["content"])
            assert "```tool_call\\n{JSON}\\n```" in first_pass_policy
            assert "structured_call_required=True" in first_pass_policy
            assert "raw_user_text_routing=False" in first_pass_policy
            assert "file.* 只有在Tony明确要求读取/搜索/列出文件时才可以调用" in first_pass_policy
            assert "market.* / research.* 是READ_ONLY证据能力" in first_pass_policy
            assert "工具结果只是证据，不是最终判断" in first_pass_policy
            assert "max_tool_calls_per_model_response=1" in first_pass_policy
            return f"```tool_call\n{TOOL_JSON}\n```"
        return "RESEARCH_EVIDENCE_JUDGED_BY_JULIA"


class DeterministicResearchProvider:
    def __init__(self) -> None:
        self.requests = []

    async def health(self) -> tuple[bool, str]:
        return True, "research test provider bound"

    async def execute(self, request):
        self.requests.append(request)
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


def test_research_evidence_reenters_julia_second_pass_through_c03(monkeypatch, tmp_path):
    from julia_core.events import store as event_store_module

    monkeypatch.setattr(
        event_store_module,
        "_store",
        event_store_module.EventStore(str(tmp_path / "events")),
    )
    provider = DeterministicResearchProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", provider)
    monkeypatch.setattr(bridge_module, "_bridge", bridge)

    cognition = ResearchCognitionInstrumentation()
    session = JuliaSession(provider=cognition)
    session.capability = bridge
    session.workflow_router.bridge = bridge

    reply = session.process(
        "robotics sector external catalysts",
        [],
        conversation_id="research-c03",
        turn_id="research-turn-1",
        modality="text",
    )

    second_pass_system = str(cognition.calls[1][0]["content"])
    first_pass_system = str(cognition.calls[0][0]["content"])
    assert reply == "RESEARCH_EVIDENCE_JUDGED_BY_JULIA"
    assert len(cognition.calls) == 2
    assert len(provider.requests) == 1
    assert provider.requests[0].capability_id == "research.web.query"
    assert provider.requests[0].arguments == {
        "query": "robotics sector external catalysts"
    }

    for marker in (
        "research.web.query",
        "robotics sector external catalysts",
        "Robotics adoption is accelerating in logistics and manufacturing.",
        "source:robotics-catalysts-2026",
        "https://example.com/robotics-catalysts",
        "Deterministic test provider; no live web acquisition in P2-I2A",
        "deterministic-research-test-provider",
        "2026-09-18T00:00:00Z",
    ):
        assert marker in second_pass_system

    for marker in (
        "```tool_call\\n{JSON}\\n```",
        "structured_call_required=True",
        "raw_user_text_routing=False",
        "file.* 只有在Tony明确要求读取/搜索/列出文件时才可以调用",
        "market.* / research.* 是READ_ONLY证据能力",
        "工具结果只是证据，不是最终判断",
        "max_tool_calls_per_model_response=1",
    ):
        assert marker in first_pass_system

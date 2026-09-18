from __future__ import annotations

import json
from types import SimpleNamespace

from julia_core.research.anthropic_web import (
    AnthropicWebResearchProvider,
    DEFAULT_CLAUDE_MODEL,
)
from julia_core.runtime import capability_bridge as bridge_module
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.julia_session import JuliaSession


TOOL_JSON = json.dumps(
    {"name": "research.web.query", "arguments": {"query": "latest robotics catalysts"}}
)


class FakeMessages:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._response


class FakeClient:
    def __init__(self, response):
        self.messages = FakeMessages(response)


class ResearchCognition:
    def __init__(self):
        self.calls = []

    def chat(self, messages, *, cognitive_mode=""):
        self.calls.append(messages)
        if len(self.calls) == 1:
            return f"```tool_call\n{TOOL_JSON}\n```"
        return "JULIA_FINAL_JUDGMENT"


def test_real_research_provider_output_reenters_julia_second_pass(monkeypatch, tmp_path):
    from julia_core.events import store as event_store_module

    monkeypatch.setattr(
        event_store_module,
        "_store",
        event_store_module.EventStore(str(tmp_path / "events")),
    )
    response = SimpleNamespace(
        id="msg_real_provider_fixture",
        stop_reason="end_turn",
        usage={"input_tokens": 12, "output_tokens": 7},
        content=[
            {"type": "server_tool_use", "id": "srvu", "name": "web_search", "input": {}},
            {
                "type": "web_search_tool_result",
                "tool_use_id": "srvu",
                "content": [
                    {
                        "type": "web_search_result",
                        "url": "https://example.com/robotics-catalyst",
                        "title": "Robotics Catalyst Source",
                        "page_age": "2026-09-17",
                    }
                ],
            },
            {
                "type": "text",
                "text": "Robotics demand is cited in manufacturing.",
                "citations": [{"url": "https://example.com/robotics-catalyst"}],
            },
        ],
    )
    provider = AnthropicWebResearchProvider(
        client=FakeClient(response),
        model=DEFAULT_CLAUDE_MODEL,
    )
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", provider)
    monkeypatch.setattr(bridge_module, "_bridge", bridge)

    cognition = ResearchCognition()
    session = JuliaSession(provider=cognition)
    session.capability = bridge
    session.workflow_router.bridge = bridge
    reply = session.process(
        "latest robotics catalysts",
        [],
        conversation_id="research-real-provider",
        turn_id="research-turn",
        modality="text",
    )

    assert reply == "JULIA_FINAL_JUDGMENT"
    assert len(provider.client.messages.calls) == 1
    assert len(cognition.calls) == 2
    second_pass = str(cognition.calls[1][0]["content"])
    for marker in (
        "https://example.com/robotics-catalyst",
        "Robotics demand is cited in manufacturing.",
        DEFAULT_CLAUDE_MODEL,
        "msg_real_provider_fixture",
        "anthropic-web-search",
    ):
        assert marker in second_pass

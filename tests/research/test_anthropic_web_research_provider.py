from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest

from julia_core.capability.models import SideEffectState, ToolResultStatus
from julia_core.research.anthropic_web import (
    AnthropicWebResearchProvider,
    AnthropicWebResearchProviderFactory,
    DEFAULT_CLAUDE_MODEL,
)


class RecordingClient:
    def __init__(self, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls = []

    async def messages_create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class MessagesNamespace:
    def __init__(self, client):
        self.create = client.messages_create


class FakeAnthropic:
    def __init__(self, client):
        self._client = client
        self.messages = MessagesNamespace(client)


def response(blocks, *, stop_reason="end_turn", request_id="msg_test"):
    return SimpleNamespace(
        id=request_id,
        content=blocks,
        stop_reason=stop_reason,
        usage={"input_tokens": 10, "output_tokens": 5, "server_tool_use": {"web_search_requests": 1}},
    )


def cited_blocks(*urls: str, text="Cited robotics observation.", pause=False):
    blocks = [
        {"type": "server_tool_use", "id": "srvu", "name": "web_search", "input": {}},
        {
            "type": "web_search_tool_result",
            "tool_use_id": "srvu",
            "content": [
                {
                    "type": "web_search_result",
                    "url": url,
                    "title": f"Source {index + 1}",
                    "page_age": "2026-09-17",
                }
                for index, url in enumerate(urls)
            ],
        },
        {"type": "text", "text": text, "citations": [{"url": url} for url in urls]},
    ]
    if pause:
        blocks.append({"type": "pause_turn"})
    return blocks


def provider_for(response=None, error=None):
    client = RecordingClient(response=response, error=error)
    client.messages = MessagesNamespace(client)
    return AnthropicWebResearchProvider(client=client, model=DEFAULT_CLAUDE_MODEL), client


@pytest.mark.asyncio
async def test_typed_sdk_response_objects_are_parsed_as_source_bearing_evidence():
    source = SimpleNamespace(
        type="web_search_result",
        url="https://example.com/typed-sdk",
        title="Typed SDK Source",
        page_age="2026-09-18",
    )
    citation = SimpleNamespace(
        type="web_search_result_location",
        url="https://example.com/typed-sdk",
        title="Typed SDK Source",
    )
    text = SimpleNamespace(
        type="text",
        text="Typed SDK response contains a cited fact.",
        citations=[citation],
    )
    blocks = [
        SimpleNamespace(type="server_tool_use", id="srvu", name="web_search", input={}),
        SimpleNamespace(type="web_search_tool_result", tool_use_id="srvu", content=[source]),
        text,
    ]
    provider, _ = provider_for(response(blocks))

    outcome = await provider.execute(request())

    assert outcome.status is ToolResultStatus.SUCCESS
    assert outcome.structured_output["sources"] == [
        {
            "url": "https://example.com/typed-sdk",
            "title": "Typed SDK Source",
            "page_age": "2026-09-18",
        }
    ]
    assert outcome.structured_output["findings"] == [
        {
            "statement": "Typed SDK response contains a cited fact.",
            "source_refs": ["https://example.com/typed-sdk"],
        }
    ]


def request(query="latest robotics industry external catalysts"):
    return SimpleNamespace(arguments={"query": query})


@pytest.mark.asyncio
async def test_provider_sends_one_exact_direct_bounded_web_search_request():
    client_response = response(cited_blocks("https://example.com/robotics"))
    provider, client = provider_for(client_response)

    outcome = await provider.execute(request("exact research question"))

    assert len(client.calls) == 1
    kwargs = client.calls[0]
    assert kwargs["model"] == DEFAULT_CLAUDE_MODEL
    assert kwargs["messages"] == [{"role": "user", "content": "exact research question"}]
    assert kwargs["tools"] == [
        {"type": "web_search_20250305", "name": "web_search", "max_uses": 1}
    ]
    assert "allowed_callers" not in kwargs
    assert all(key not in kwargs for key in ("client_tools", "computer", "code_execution"))
    assert outcome.status is ToolResultStatus.SUCCESS
    assert outcome.side_effect_state is SideEffectState.NONE
    assert outcome.structured_output["query"] == "exact research question"
    assert outcome.structured_output["model"] == DEFAULT_CLAUDE_MODEL
    assert outcome.structured_output["provider_request_id"] == "msg_test"
    assert outcome.structured_output["search_request_count"] == 1


@pytest.mark.asyncio
async def test_multiple_citations_are_preserved_and_uncited_text_is_not_a_finding():
    blocks = cited_blocks(
        "https://example.com/a",
        "https://example.com/b",
        text="Cited comparison.",
    )
    blocks.append({"type": "text", "text": "Uncited text must be ignored."})
    provider, _ = provider_for(response(blocks))

    outcome = await provider.execute(request())

    assert outcome.status is ToolResultStatus.SUCCESS
    assert outcome.structured_output["findings"] == [
        {
            "statement": "Cited comparison.",
            "source_refs": ["https://example.com/a", "https://example.com/b"],
        }
    ]
    assert {source["url"] for source in outcome.structured_output["sources"]} == {
        "https://example.com/a",
        "https://example.com/b",
    }


@pytest.mark.asyncio
async def test_empty_result_is_typed_failure_without_synthetic_source():
    blocks = [
        {"type": "server_tool_use", "id": "srvu", "name": "web_search", "input": {}},
        {
            "type": "web_search_tool_result",
            "tool_use_id": "srvu",
            "content": [],
        },
        {"type": "text", "text": "No citation.", "citations": []},
    ]
    provider, _ = provider_for(response(blocks))

    outcome = await provider.execute(request())

    assert outcome.status is ToolResultStatus.ERROR
    assert outcome.structured_output == {}
    assert outcome.error["code"] == "anthropic_web_search_no_source_bearing_search_result"
    assert outcome.side_effect_state is SideEffectState.NONE


@pytest.mark.asyncio
async def test_valid_finding_plus_search_error_is_partial():
    blocks = cited_blocks("https://example.com/source")
    blocks.append(
        {
            "type": "web_search_tool_result_error",
            "error": {"type": "search_error", "message": "upstream unavailable"},
        }
    )
    provider, _ = provider_for(response(blocks))

    outcome = await provider.execute(request())

    assert outcome.status is ToolResultStatus.PARTIAL
    assert "web_search_tool_result_error: upstream unavailable" in outcome.structured_output["limitations"]


@pytest.mark.asyncio
async def test_search_error_with_no_cited_finding_never_becomes_success():
    blocks = [
        {"type": "server_tool_use", "id": "srvu", "name": "web_search", "input": {}},
        {
            "type": "web_search_tool_result_error",
            "error": {"type": "search_error", "message": "search rejected"},
        },
    ]
    provider, _ = provider_for(response(blocks))

    outcome = await provider.execute(request())

    assert outcome.status is ToolResultStatus.ERROR
    assert outcome.structured_output == {}
    assert outcome.error["code"] == "anthropic_web_search_no_source_bearing_search_result"


@pytest.mark.asyncio
async def test_official_single_object_search_error_inside_tool_result_is_partial_truth():
    blocks = cited_blocks("https://example.com/source")
    blocks[1] = {
        "type": "web_search_tool_result",
        "tool_use_id": "srvu",
        "content": {
            "type": "web_search_tool_result_error",
            "error_code": "api_error",
        },
    }
    provider, _ = provider_for(response(blocks))

    outcome = await provider.execute(request())

    assert outcome.status is ToolResultStatus.PARTIAL
    assert any(
        item == "web_search_tool_result_error: api_error"
        for item in outcome.structured_output["limitations"]
    )


@pytest.mark.asyncio
async def test_pause_turn_with_valid_material_is_partial_and_makes_no_second_call():
    blocks = cited_blocks("https://example.com/source", pause=True)
    provider, client = provider_for(response(blocks, stop_reason="pause_turn"))

    outcome = await provider.execute(request())

    assert len(client.calls) == 1
    assert outcome.status is ToolResultStatus.PARTIAL
    assert any("pause_turn" in item for item in outcome.structured_output["limitations"])
    assert outcome.structured_output["findings"][0]["source_refs"] == [
        "https://example.com/source"
    ]


@pytest.mark.asyncio
async def test_request_exception_is_sanitized_and_has_no_retry(monkeypatch):
    secret = "sk-ant-test-secret"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    provider, client = provider_for(error=RuntimeError(f"rejected {secret}"))

    outcome = await provider.execute(request())

    assert len(client.calls) == 1
    assert outcome.status is ToolResultStatus.ERROR
    assert secret not in str(outcome)
    assert outcome.error["message"] == "rejected [redacted]"


def test_factory_reads_credential_and_model_without_exposing_key(monkeypatch):
    credential = "sk-ant-factory-secret"
    monkeypatch.setenv("ANTHROPIC_API_KEY", credential)
    monkeypatch.setenv("JULIA_RESEARCH_CLAUDE_MODEL", "claude-custom-model")
    constructed = []

    class FakeSDKAsyncAnthropic:
        def __init__(self, *, api_key, max_retries):
            assert api_key == credential
            assert max_retries == 0
            constructed.append(api_key)
            self.messages = object()

    module = types.ModuleType("anthropic")
    module.AsyncAnthropic = FakeSDKAsyncAnthropic
    monkeypatch.setitem(sys.modules, "anthropic", module)

    provider = AnthropicWebResearchProviderFactory.from_environment()

    assert isinstance(provider, AnthropicWebResearchProvider)
    assert provider.model == "claude-custom-model"
    assert constructed == [credential]
    assert credential not in repr(provider)


def test_factory_missing_credential_returns_none_without_importing_sdk(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def fail_import(name, *args, **kwargs):
        if name == "anthropic":
            raise AssertionError("SDK must not be imported without credential")
        return __import__(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fail_import)

    assert AnthropicWebResearchProviderFactory.from_environment() is None

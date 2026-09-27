"""Focused transport-only DeepSeek provider and cold-start proofs."""

from __future__ import annotations

import importlib
import io
import json
from pathlib import Path
import threading
import time

import pytest

import julia_core.providers.core_cognition as core_cognition
from julia_core.providers.core_cognition import (
    NativeToolInvocation,
    TextResult,
)
from julia_core.providers.deepseek import (
    DeepSeekCognitionProvider,
    DeepSeekCognitionProviderError,
)


@pytest.fixture(autouse=True)
def reset_provider_registry():
    core_cognition._providers.clear()
    core_cognition._production_initialization_attempted = False
    yield
    core_cognition._providers.clear()
    core_cognition._production_initialization_attempted = False


class FakeHTTPResponse:
    def __init__(self, payload: bytes):
        self._stream = io.BytesIO(payload)

    def read(self) -> bytes:
        return self._stream.read()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


def _success_response(content: str) -> bytes:
    return json.dumps(
        {"choices": [{"message": {"role": "assistant", "content": content}}]}
    ).encode()


def _native_response(
    *,
    content=None,
    tool_calls=None,
    finish_reason="stop",
) -> bytes:
    message = {"role": "assistant", "content": content}
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return json.dumps({
        "choices": [{
            "finish_reason": finish_reason,
            "message": message,
        }],
    }).encode()


def _tool_call(name: str, arguments: object) -> dict:
    return {
        "id": "provider-id-not-semantic",
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments),
        },
    }


def _available_tools() -> list[dict]:
    return [{
        "capability_id": "market.stock_quote_read",
        "description": "Read one exact stock/date quote",
        "input_schema": {
            "stock_id": "exact stock identifier",
            "trade_date": "exact YYYY-MM-DD trade date",
        },
    }]


def test_exact_core_messages_are_transported_without_semantic_edits(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    requests = []

    def fake_urlopen(request, timeout=None):
        requests.append(request)
        return FakeHTTPResponse(_success_response("REAL MODEL ANSWER"))

    monkeypatch.setattr("julia_core.providers.deepseek.urllib.request.urlopen", fake_urlopen)
    provider = DeepSeekCognitionProvider()
    exact_messages = [
        {"role": "system", "content": "identity context"},
        {
            "message_id": "msg_internal",
            "conversation_id": "conv_internal",
            "turn_id": "turn_internal",
            "role": "user",
            "modality": "text",
            "content": "查一下 600519 今天的行情",
            "status": "completed",
        },
    ]

    result = provider.chat(exact_messages, cognitive_mode="market")

    assert result == "REAL MODEL ANSWER"
    assert len(requests) == 1
    transported = json.loads(requests[0].data.decode("utf-8"))
    assert transported["messages"] == [
        {"role": "system", "content": "identity context"},
        {"role": "user", "content": "查一下 600519 今天的行情"},
    ]


def test_missing_credential_fails_closed_before_network(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    network_calls = []
    monkeypatch.setattr(
        "julia_core.providers.deepseek.urllib.request.urlopen",
        lambda *args, **kwargs: network_calls.append(1),
    )

    with pytest.raises(core_cognition.CoreCognitionProviderUnavailable):
        core_cognition.initialize_production_cognition()

    assert network_calls == []
    assert core_cognition._get_cognition_provider("production") is None


def test_missing_credential_public_ingress_fails_closed(monkeypatch, tmp_path):
    from julia_core.public import (
        CoreConversationConfig,
        CoreConversationIngress,
        CoreConversationRequest,
    )

    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    response = CoreConversationIngress(
        CoreConversationConfig(tmp_path / "conversations")
    ).process(CoreConversationRequest("conv", "turn", "text", "hello"))

    assert response.status == "failed"
    assert response.error_code == "CORE_PROVIDER_UNAVAILABLE"
    assert response.assistant_content == ""


def test_missing_credential_provider_constructor_fails_closed(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(DeepSeekCognitionProviderError):
        DeepSeekCognitionProvider()


def test_fresh_initialization_resolves_one_production_provider(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    provider = core_cognition.initialize_production_cognition()

    assert provider is not None
    assert provider is core_cognition._get_cognition_provider("production")
    assert isinstance(provider, DeepSeekCognitionProvider)


def test_initialization_is_idempotent_and_rejects_namespace_replacement(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    first = core_cognition.initialize_production_cognition()
    second = core_cognition.initialize_production_cognition()

    assert first is second
    with pytest.raises(RuntimeError, match="already bound"):
        core_cognition._register_cognition_provider("production", object())


def test_concurrent_initialization_has_one_terminal_provider_result(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    construction_started = threading.Event()
    release_construction = threading.Event()
    construction_count = 0

    class SlowProvider:
        def __init__(self):
            nonlocal construction_count
            construction_started.set()
            assert release_construction.wait(timeout=2)
            time.sleep(0.02)
            construction_count += 1

    monkeypatch.setattr(
        "julia_core.providers.deepseek.DeepSeekCognitionProvider",
        SlowProvider,
    )
    results = []
    errors = []

    def initialize():
        try:
            results.append(core_cognition.initialize_production_cognition())
        except Exception as error:
            errors.append(error)

    threads = [threading.Thread(target=initialize) for _ in range(8)]
    for thread in threads:
        thread.start()
    assert construction_started.wait(timeout=2)
    assert sum(thread.is_alive() for thread in threads) == 8
    release_construction.set()
    for thread in threads:
        thread.join(timeout=2)

    assert errors == []
    assert construction_count == 1
    assert len(results) == 8
    assert len({id(provider) for provider in results}) == 1
    assert results[0] is core_cognition._get_cognition_provider("production")


def test_malformed_and_empty_responses_fail_without_fallback(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    provider = DeepSeekCognitionProvider()

    for payload in (
        b"{}",
        json.dumps({"choices": [{}]}).encode(),
        *(
            json.dumps({"choices": [{"message": {"content": content}}]}).encode()
            for content in ("", " ", "\n", "\t")
        ),
    ):
        monkeypatch.setattr(
            "julia_core.providers.deepseek.urllib.request.urlopen",
            lambda *args, **kwargs: FakeHTTPResponse(payload),
        )
        with pytest.raises(DeepSeekCognitionProviderError):
            provider.chat([{"role": "user", "content": "request"}])


def test_native_tool_projection_is_mechanical_and_non_strict(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    requests = []

    def fake_urlopen(request, timeout=None):
        requests.append(request)
        return FakeHTTPResponse(_native_response(content="plain answer"))

    monkeypatch.setattr(
        "julia_core.providers.deepseek.urllib.request.urlopen",
        fake_urlopen,
    )
    provider = DeepSeekCognitionProvider()
    result = provider.chat_with_tools(
        [{"role": "user", "content": "request"}],
        _available_tools(),
    )

    assert isinstance(result, TextResult)
    assert result.content == "plain answer"
    payload = json.loads(requests[0].data.decode("utf-8"))
    assert payload["tool_choice"] == "auto"
    assert payload["tools"] == [{
        "type": "function",
        "function": {
            "name": "market_2E_stock_5F_quote_5F_read",
            "description": "Read one exact stock/date quote",
            "parameters": {
                "type": "object",
                "properties": {
                    "stock_id": {"description": "exact stock identifier"},
                    "trade_date": {
                        "description": "exact YYYY-MM-DD trade date"
                    },
                },
            },
        },
    }]
    serialized = json.dumps(payload["tools"], sort_keys=True)
    assert '"required"' not in serialized
    assert '"enum"' not in serialized
    assert '"pattern"' not in serialized


def test_native_tool_name_round_trip_and_fail_closed_constraints(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    provider = DeepSeekCognitionProvider()
    canonical_ids = (
        "market.analysis.read",
        "research.web.query",
        "file_name.with_under_score",
        "escape._2E_._5F_.literal",
    )
    for capability_id in canonical_ids:
        wire_name = provider._encode_tool_name(capability_id)
        assert len(wire_name) <= 128
        assert provider._decode_tool_name(
            wire_name,
            canonical_ids,
        ) == capability_id

    with pytest.raises(DeepSeekCognitionProviderError):
        provider._decode_tool_name("_BAD_", canonical_ids)
    with pytest.raises(DeepSeekCognitionProviderError):
        provider._decode_tool_name(
            provider._encode_tool_name("unknown.tool"),
            canonical_ids,
        )
    with pytest.raises(DeepSeekCognitionProviderError):
        provider._encode_tool_name("bad:tool")
    with pytest.raises(DeepSeekCognitionProviderError):
        provider._encode_tool_name("a." + ("b" * 127))


@pytest.mark.parametrize("content", [None, "", "I will read the market evidence"])
def test_native_result_text_and_single_tool_call(monkeypatch, content):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    provider = DeepSeekCognitionProvider()
    tools = _available_tools()

    monkeypatch.setattr(
        "julia_core.providers.deepseek.urllib.request.urlopen",
        lambda *args, **kwargs: FakeHTTPResponse(
            _native_response(content="Julia answer")
        ),
    )
    text_result = provider.chat_with_tools(
        [{"role": "user", "content": "request"}],
        tools,
    )
    assert text_result == TextResult("Julia answer")

    wire_name = provider._encode_tool_name(tools[0]["capability_id"])
    monkeypatch.setattr(
        "julia_core.providers.deepseek.urllib.request.urlopen",
        lambda *args, **kwargs: FakeHTTPResponse(
            _native_response(
                content=content,
                tool_calls=[_tool_call(
                    wire_name,
                    {"stock_id": "600519.SH", "trade_date": "2026-07-31"},
                )],
                finish_reason="tool_calls",
            )
        ),
    )
    tool_result = provider.chat_with_tools(
        [{"role": "user", "content": "request"}],
        tools,
    )
    assert tool_result == NativeToolInvocation(
        capability_id="market.stock_quote_read",
        arguments={
            "stock_id": "600519.SH",
            "trade_date": "2026-07-31",
        },
    )


def test_native_fence_without_tool_call_remains_text_for_runtime_rejection(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    provider = DeepSeekCognitionProvider()
    legacy_fence = '```tool_call\n{"name":"market.stock_quote_read"}\n```'

    monkeypatch.setattr(
        "julia_core.providers.deepseek.urllib.request.urlopen",
        lambda *args, **kwargs: FakeHTTPResponse(
            _native_response(content=legacy_fence)
        ),
    )

    result = provider.chat_with_tools(
        [{"role": "user", "content": "request"}],
        _available_tools(),
    )

    assert result == TextResult(legacy_fence)


def test_native_fence_without_tool_call_remains_text_and_multiple_and_malformed_fail_closed(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    provider = DeepSeekCognitionProvider()
    tools = _available_tools()
    wire_name = provider._encode_tool_name(tools[0]["capability_id"])
    invalid_payloads = (
        _native_response(
            content=None,
            tool_calls=[_tool_call(wire_name, {}), _tool_call(wire_name, {})],
            finish_reason="tool_calls",
        ),
        _native_response(
            content=None,
            tool_calls=[_tool_call(wire_name, [])],
            finish_reason="tool_calls",
        ),
        _native_response(
            content=None,
            tool_calls=[_tool_call(wire_name, {})],
            finish_reason="stop",
        ),
        _native_response(
            content=None,
            tool_calls=None,
            finish_reason="tool_calls",
        ),
    )
    for payload in invalid_payloads:
        monkeypatch.setattr(
            "julia_core.providers.deepseek.urllib.request.urlopen",
            lambda *args, _payload=payload, **kwargs: FakeHTTPResponse(_payload),
        )
        with pytest.raises(DeepSeekCognitionProviderError):
            provider.chat_with_tools(
                [{"role": "user", "content": "request"}],
                tools,
            )


def test_provider_source_has_no_semantic_or_cross_component_dependencies():
    source = Path(importlib.import_module("julia_core.providers.deepseek").__file__).read_text()
    forbidden = (
        "Persona",
        "ProviderBehaviorAdapter",
        "Julia-AI-Assistant",
        "julia_core.market",
        "julia_core.research",
        "identity_repository",
        "memory_repository",
        "Narrative",
    )
    assert all(term not in source for term in forbidden)
